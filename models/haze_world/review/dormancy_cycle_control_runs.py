"""Run the bounded linear switching controls without changing frozen producers."""

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from terra_prisca.haze_world import dormancy_cycle_closure as closure


def run(key, years=20000.):
    start = closure.run_linear(key, 2000., backend="face", max_step=10.)
    if start["status"] != "completed":
        return {"status": "failed_startup", "startup": start}
    case, p, _, _ = closure.linear_initial(key)
    case = replace(case, years=years)
    with np.load(closure.ROOT/start["raw_file"]) as source:
        t0, y0 = source["t"], source["y"]
    protocol = dict(kind="linear_two_segment_original_start", case=vars(case),
        startup_fingerprint=start["fingerprint"], startup_raw_sha256=start["raw_sha256"],
        startup_years=2000., continuation_years=years-2000., continuation_backend="macro",
        continuation_max_step_yr=2., continuation_rtol=2e-9,
        source_sha256=closure.sources(), controller_sha256=closure.digest(__file__),
        scope="Original linear invasion with positive-coordinate startup; autonomous physical RHS restarted at accepted census time2000yr. Macro continuation rejects negative stocks, rare guilds or required census removal.")
    fingerprint = sha256(closure.experiments.e.dumps(protocol).encode()).hexdigest()
    receipt = closure.RAW/f"linear_segments_{key}_{fingerprint[:12]}.json"
    if receipt.exists():
        old = json.loads(receipt.read_text())
        if old["status"] == "completed" and closure.digest(closure.ROOT/old["raw_file"]) == old["raw_sha256"]:
            return old
        raise RuntimeError("Preserve prior unsuccessful continuation")
    record = dict(protocol=protocol, fingerprint=fingerprint)
    started = perf_counter()
    try:
        flow = closure.macro_integrate(y0[:, -1], p, years-2000.)
        t = np.r_[t0, flow["t"][1:]+2000.]
        y = np.column_stack([y0, flow["y"][:, 1:]])
        raw = receipt.with_suffix(".npz")
        np.savez_compressed(raw, t=t, y=y, initial=y0[:, 0])
        record.update(status="completed", actual_horizon_yr=float(t[-1]),
            raw_file=str(raw.relative_to(closure.ROOT)), raw_sha256=closure.digest(raw),
            startup_receipt=str((closure.RAW/f"linear_{key}_{start['fingerprint'][:12]}.json").relative_to(closure.ROOT)),
            startup_work=start["work"], continuation_work=flow["work"],
            startup_extinction_events=start.get("extinction_events", []),
            envelopes=closure.envelopes(dict(t=t, y=y), p, years),
            final_temperature_k=float(closure.model.core.temperature_k(y[-1, -1], p.coupled.climate)))
    except Exception as error:
        record.update(status="failed_continuation", error=repr(error),
            actual_horizon_yr=2000., startup_raw_file=start["raw_file"],
            startup_raw_sha256=start["raw_sha256"])
    record.update(wall_seconds=perf_counter()-started,
        sources_unchanged=closure.sources()==protocol["source_sha256"] and closure.digest(__file__)==protocol["controller_sha256"])
    receipt.write_text(closure.experiments.e.dumps(record)+"\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("0024", "0032", "0126", "0012", "0068"))
    args = parser.parse_args()
    record = run(args.case)
    print(json.dumps({k: v for k, v in record.items() if k not in ("protocol", "startup_work", "continuation_work")}), flush=True)
