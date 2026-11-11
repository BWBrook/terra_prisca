"""Physical directional tests of the nonsmooth case0024 linear-ramp root."""

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from time import perf_counter

import numpy as np

from terra_prisca.haze_world import dormancy_cycle_closure as closure


def run(guild, fraction, backend="macro", years=20000.):
    root, old, proof = closure.mixed_root()
    p = replace(old, ramp="linear")
    initial = closure.perturb(root, p, guild, fraction)
    protocol = dict(kind="linear_root_direction", guild=guild, fraction=fraction,
        years=years, backend=backend, max_step_yr=10. if backend=="radau" else 2.,
        rtol=2e-9, initial=initial.tolist(), root_source=proof,
        linear_root_max_absolute_rhs=float(max(abs(closure.model.rhs(root, p)))),
        source_sha256=closure.sources(), controller_sha256=closure.digest(__file__),
        stability_scope="Physical directional restoration test; nonsmooth local stability remains unqualified. No single-Jacobian certificate.")
    fingerprint = sha256(closure.experiments.e.dumps(protocol).encode()).hexdigest()
    receipt = closure.RAW/f"linear_root_{guild}_{fraction:g}_{backend}_{fingerprint[:12]}.json"
    if receipt.exists():
        old = json.loads(receipt.read_text())
        if old["status"] == "completed" and closure.digest(closure.ROOT/old["raw_file"]) == old["raw_sha256"]:
            return old
        raise RuntimeError("Preserve unsuccessful directional trial")
    record = dict(protocol=protocol, fingerprint=fingerprint)
    started = perf_counter()
    try:
        if backend == "macro":
            data = closure.macro_integrate(initial, p, years)
            events = []
        else:
            result = closure.radau.integrate_finite(initial, p, years,
                sample_every_censuses=1, rtol=2e-9, max_step=10.)
            if result.status != "completed":
                raise ArithmeticError("Incomplete frozen Radau directional flow")
            data = dict(t=result.t, y=result.y, work=result.metadata)
            events = result.extinction_events
        raw = receipt.with_suffix(".npz")
        np.savez_compressed(raw, t=data["t"], y=data["y"], initial=initial)
        record.update(status="completed", actual_horizon_yr=float(data["t"][-1]),
            raw_file=str(raw.relative_to(closure.ROOT)), raw_sha256=closure.digest(raw),
            work=data["work"], extinction_events=events,
            envelopes=closure.envelopes(data, p, years))
    except Exception as error:
        record.update(status="failed", error=repr(error))
    record.update(wall_seconds=perf_counter()-started,
        sources_unchanged=closure.sources()==protocol["source_sha256"] and closure.digest(__file__)==protocol["controller_sha256"])
    receipt.write_text(closure.experiments.e.dumps(record)+"\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("guild", type=int, choices=(0, 1))
    parser.add_argument("fraction", type=float)
    parser.add_argument("--backend", choices=("macro", "radau"), default="macro")
    args = parser.parse_args()
    record = run(args.guild, args.fraction, args.backend)
    print(json.dumps({k:v for k,v in record.items() if k not in ("protocol", "work")}), flush=True)
