"""Bounded cycle checks requested by the turnover/dormancy review.

Earlier physical and numerical producers remain frozen. A reduced physical
LSODA control is used only while both guilds remain macroscopic; it rejects
negative accepted stocks, unsupported climates and any census removal.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.integrate import LSODA
from scipy.signal import find_peaks

from . import dormancy as model
from . import dormancy_experiments as experiments
from . import dormancy_face_integration as face
from . import dormancy_radau_integration as radau
from . import dormancy_starts
from . import turnover


ROOT = experiments.e.ROOT
RAW = ROOT/"local/haze/dormancy_cycle_closure"
REVIEW = ROOT/"models/haze_world/review"


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def sources():
    return experiments.sources() | {
        str(Path(module.__file__).relative_to(ROOT)): digest(module.__file__)
        for module in (face, radau, turnover)
    } | {str(Path(__file__).relative_to(ROOT)): digest(__file__)}


def cycle_case(key):
    return next(case for case in experiments.design() if case.case_id == f"dormancy_{key}")


def mixed_root():
    path = REVIEW/"dormancy126_cycle_0024.json"
    record = json.loads(path.read_text())
    y = np.array(record["mixed_equilibrium"]["y"])
    p = experiments.parameters(cycle_case("0024"))
    y[p.dormant_indices] = 0.
    return y, p, dict(path=str(path.relative_to(ROOT)), sha256=digest(path),
                      maximum_absolute_rhs=float(max(abs(model.rhs(y, p)))))


def perturb(y, p, guild, fraction):
    if guild not in (0, 1) or not -1 < fraction < 1 or fraction == 0:
        raise ValueError("Choose one guild and a nonzero fractional perturbation")
    out = np.array(y, dtype=float, copy=True)
    out[p.biomass_indices[:, guild]] *= 1+fraction
    return out


def macro_integrate(initial, p, years, *, rtol=2e-9, max_step=2., cadence=10.):
    """A maintained-solver control, restricted to macroscopic populations."""
    initial = np.asarray(initial, dtype=float)
    if initial.shape != (p.state_size,) or np.any(initial < 0):
        raise ValueError("Expected finite nonnegative physical stocks")
    active = np.flatnonzero(p.weights > 0)
    indices = np.r_[np.concatenate([np.arange(6*j, 6*j+6) for j in active]), p.state_size-1]
    scales = np.r_[np.tile([100., 1e-3, 1e-3, 1e-3, 1e-3, 1e-3], len(active)), .2]
    atol = np.r_[np.tile([1e-10, 1e-24, 1e-24, 1e-13, 1e-15, 1e-15], len(active)), 1e-12]

    def decode(z):
        out = np.zeros(p.state_size)
        out[indices] = z*scales
        return out

    def rhs(time, z):
        return model.rhs(decode(z), p, trial_extension=True)[indices]/scales

    solver = LSODA(rhs, 0., initial[indices]/scales, years, rtol=rtol,
                   atol=atol, max_step=max_step)
    times, values = [0.], [initial.copy()]
    next_sample, pieces = cadence, 0
    conversion = p.coupled.habitat_l_cm2*face.Census().surface_cm2/face.Census().cell_mass_gdw
    smallest_cells = np.inf
    while solver.status == "running":
        message = solver.step()
        if solver.status == "failed":
            raise ArithmeticError("Macro LSODA failed: "+str(message))
        pieces += 1
        endpoints = [solver.y]
        dense = solver.dense_output()
        endpoints.append(dense((solver.t_old+solver.t)/2))
        for z in endpoints:
            y = decode(z)
            if np.any(~np.isfinite(y)) or np.any(y < 0):
                raise ArithmeticError(f"Negative/nonfinite macro stock at {solver.t:.17g}")
            if "unsupported" in model.temperature_flags(y, p):
                raise ArithmeticError("Macro control left the supported climate/physiology domain")
            counts = p.weights@(y[p.biomass_indices]+y[p.dormant_indices])*conversion
            smallest_cells = min(smallest_cells, float(min(counts)))
            if min(counts) < 1e16:
                raise ArithmeticError("Macro control reached the rare-population range")
        while next_sample <= solver.t+1e-10:
            if next_sample > years:
                break
            y = decode(dense(next_sample))
            if np.any(y < 0) or np.any(~np.isfinite(y)):
                raise ArithmeticError("Invalid sampled macro stock")
            local = (y[p.biomass_indices]+y[p.dormant_indices])
            local *= (p.weights*conversion)[:, None]
            if np.any(local[active] < 1.):
                raise ArithmeticError("Macro control would require a census removal")
            times.append(next_sample); values.append(y)
            next_sample += cadence
    if times[-1] != years:
        times.append(float(years)); values.append(decode(solver.y))
    return dict(t=np.array(times), y=np.column_stack(values),
        work=dict(rhs=solver.nfev, jacobians=solver.njev, accepted_steps=pieces,
                  minimum_global_cells=smallest_cells),
        scope="Reduced physical LSODA; accepted endpoints, midpoints and observations checked. No rare-lineage or whole-piece positivity certificate.")


def envelopes(data, p, years):
    time = data["t"]
    temperature = np.asarray(model.core.temperature_k(data["y"][-1], p.coupled.climate))
    width = min(5000., years/3)
    records = []
    for right in np.arange(width, years+width/2, width):
        use = (time >= max(0., right-width)) & (time <= min(years, right))
        t, v = time[use], temperature[use]
        if len(t) < 3:
            continue
        peaks = find_peaks(v, prominence=max(1e-10, np.ptp(v)*.02))[0]
        period = float(np.polyfit(np.arange(len(peaks)), t[peaks], 1)[0]) if len(peaks)>2 else None
        records.append(dict(left_yr=float(t[0]), right_yr=float(t[-1]),
            span_k=float(np.ptp(v)), mean_k=float(np.mean(v)), period_yr=period))
    return records


def run_amplitude(guild, fraction, years, backend="macro", max_step=2.):
    root, p, proof = mixed_root()
    initial = perturb(root, p, guild, fraction)
    protocol = dict(kind="amplitude", guild=guild, fraction=fraction, years=years,
        backend=backend, max_step_yr=max_step, rtol=2e-9, source_sha256=sources(),
        mixed_root=proof, initial=initial.tolist(), dormant_initial="exact zero",
        census="One cell per habitat per10yr; macro branch rejects any required removal")
    fingerprint = sha256(experiments.e.dumps(protocol).encode()).hexdigest()
    RAW.mkdir(parents=True, exist_ok=True)
    receipt = RAW/f"amplitude_{guild}_{fraction:g}_{fingerprint[:12]}.json"
    if receipt.exists():
        old = json.loads(receipt.read_text())
        if old["status"] == "completed" and digest(ROOT/old["raw_file"]) == old["raw_sha256"]:
            return old
        raise RuntimeError("Preserve prior unsuccessful trial")
    started = perf_counter()
    row = dict(protocol=protocol, fingerprint=fingerprint)
    try:
        if backend == "macro":
            data = macro_integrate(initial, p, years, max_step=max_step)
        else:
            helper = radau if backend == "radau" else face
            result = helper.integrate_finite(initial, p, years, sample_every_censuses=1,
                                             rtol=2e-9, max_step=max_step)
            if result.status != "completed":
                raise ArithmeticError("Incomplete frozen-producer flow")
            data = dict(t=result.t, y=result.y, work=result.metadata,
                        scope="Frozen positive-coordinate producer")
        raw = receipt.with_suffix(".npz")
        np.savez_compressed(raw, t=data["t"], y=data["y"], initial=initial)
        row.update(status="completed", raw_file=str(raw.relative_to(ROOT)), raw_sha256=digest(raw),
                   work=data["work"], scope=data["scope"], envelopes=envelopes(data, p, years),
                   final_temperature_k=float(model.core.temperature_k(data["y"][-1, -1], p.coupled.climate)))
    except Exception as error:
        row.update(status="failed", error=repr(error))
    row.update(wall_seconds=perf_counter()-started, sources_unchanged=sources()==protocol["source_sha256"])
    receipt.write_text(experiments.e.dumps(row)+"\n")
    return row


def linear_initial(key):
    case = replace(cycle_case(key), ramp="linear")
    p = experiments.parameters(case)
    roots = dormancy_starts.conditional_states(p, 1)
    candidates = [r for r in roots["candidates"] if r["max_scaled_residual"] <= 1e-8
                  and all(r["y"][6*j+2] > 0 for j, w in enumerate(p.weights) if w)]
    if not candidates:
        raise ArithmeticError("No residual-qualified linear resident")
    root = max(candidates, key=lambda r: r["r"])
    initial = np.array(root["y"], copy=True)
    for j, weight in enumerate(p.weights):
        if weight:
            initial[6*j+1] = 1e-12
            initial[6*j+4] = 0.
    proof = {k:v for k,v in root.items() if k != "y"}
    proof["scope"] = "Highest-r residual-qualified linear M resident; nonsmooth conditional stability remains unqualified. Original active A invasion dose retained."
    return case, p, initial, proof


def run_linear(key, years, backend="macro", max_step=2.):
    case, p, initial, proof = linear_initial(key)
    case = replace(case, years=years)
    protocol = dict(kind="linear_original_start", case=vars(case), initial=initial.tolist(),
        resident=proof, backend=backend, max_step_yr=max_step, rtol=2e-9,
        source_sha256=sources(), census="One cell per habitat every10years")
    fingerprint = sha256(experiments.e.dumps(protocol).encode()).hexdigest()
    RAW.mkdir(parents=True, exist_ok=True)
    receipt = RAW/f"linear_{key}_{fingerprint[:12]}.json"
    if receipt.exists():
        old = json.loads(receipt.read_text())
        if old["status"] == "completed" and digest(ROOT/old["raw_file"]) == old["raw_sha256"]:
            return old
        raise RuntimeError("Preserve prior unsuccessful trial")
    started = perf_counter()
    row = dict(protocol=protocol, fingerprint=fingerprint)
    try:
        if backend == "macro":
            data = macro_integrate(initial, p, years, max_step=max_step)
            events = []
        else:
            helper = radau if backend == "radau" else face
            result = helper.integrate_finite(initial, p, years, sample_every_censuses=1,
                                             rtol=2e-9, max_step=max_step)
            if result.status != "completed":
                raise ArithmeticError("Incomplete frozen-producer flow")
            data = dict(t=result.t, y=result.y, work=result.metadata,
                        scope="Frozen positive-coordinate producer with linear physical switching law")
            events = result.extinction_events
        raw = receipt.with_suffix(".npz")
        np.savez_compressed(raw, t=data["t"], y=data["y"], initial=initial)
        row.update(status="completed", raw_file=str(raw.relative_to(ROOT)), raw_sha256=digest(raw),
                   work=data["work"], scope=data["scope"], envelopes=envelopes(data, p, years),
                   extinction_events=events, final=experiments.summarize(case, p, result) if backend != "macro" else None,
                   final_temperature_k=float(model.core.temperature_k(data["y"][-1,-1], p.coupled.climate)))
    except Exception as error:
        row.update(status="failed", error=repr(error))
    row.update(wall_seconds=perf_counter()-started, sources_unchanged=sources()==protocol["source_sha256"])
    receipt.write_text(experiments.e.dumps(row)+"\n")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=float, default=1000.)
    parser.add_argument("--guild", type=int, choices=(0,1), default=0)
    parser.add_argument("--fraction", type=float, default=.001)
    parser.add_argument("--backend", choices=("macro","face","radau"), default="macro")
    parser.add_argument("--max-step", type=float, default=2.)
    parser.add_argument("--linear-case", choices=("0024","0032","0126","0012","0068"))
    args = parser.parse_args()
    row = (run_linear(args.linear_case, args.years, args.backend, args.max_step)
           if args.linear_case else run_amplitude(args.guild, args.fraction, args.years, args.backend, args.max_step))
    print(experiments.e.dumps({k:v for k,v in row.items() if k not in ("protocol","work")}), flush=True)


if __name__ == "__main__":
    main()
