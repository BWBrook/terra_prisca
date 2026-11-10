"""Uncensored trajectories for the specified refuge bottleneck experiment."""

import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from . import buffered_experiments as e
from . import habitat_equilibria as equilibria
from .habitat_integration import Census, integrate_finite

RAW = e.ROOT / "local/haze/bottleneck"
OUTPUT = e.ROOT / "models/haze_world/figures/bottleneck"


def planned():
    cases = []
    for stage in ("main", "controls", "sensitivity"):
        with (e.OUTPUT / f"selected_{stage}.csv").open() as stream:
            for row in csv.DictReader(stream):
                receipt = e.RAW / row["raw_file"].replace(".json.gz", ".receipt.json")
                record = json.loads(receipt.read_text())
                if sha256((e.RAW / record["raw_file"]).read_bytes()).hexdigest() != record["raw_sha256"]:
                    raise RuntimeError("Changed census baseline")
                cases.append((e.Case(**record["protocol"]["case"]), row, record))
    return cases


def continuation():
    cases = []
    for f in (0., .5):
        for w in (.005, .02):
            for d in np.logspace(-9, -3, 49):
                cases.append(e.Case(f"exchange_{len(cases):04d}", f, "warm", float(d), "A_into_M",
                                    refuge_fraction=w, years=6000., census_yr=1.))
    return cases


def source_hashes():
    return e.source_hashes() | {str(Path(__file__).relative_to(e.ROOT)): sha256(Path(__file__).read_bytes()).hexdigest()}


def paths(protocol):
    fingerprint = sha256(e.dumps(protocol).encode()).hexdigest()
    stem = f"{protocol['case']['case_id']}_t{protocol['years']:g}-{fingerprint[:16]}"
    return fingerprint, RAW / f"{stem}.npz", RAW / f"{stem}.receipt.json"


def run(case, years, baseline=None, expected_sources=None):
    _, environment = e.identity(case)
    protocol = dict(case=asdict(case), years=years, census=asdict(Census(minimum_cells=0., census_yr=1.)),
                    source_sha256=source_hashes(), baseline_fingerprint=None if baseline is None else baseline["fingerprint"],
                    python=environment["python"], packages=environment["packages"],
                    scope="Uncensored physical trajectory; one-year sampling; no stochastic feedback")
    if expected_sources is not None and protocol["source_sha256"] != expected_sources:
        raise RuntimeError("Source changed during frozen trajectory batch")
    fingerprint, data, receipt = paths(protocol)
    if receipt.exists():
        r = json.loads(receipt.read_text())
        if r["fingerprint"] != fingerprint or sha256(data.read_bytes()).hexdigest() != r["raw_sha256"]:
            raise RuntimeError("Invalid uncensored receipt")
        return r
    p = e.parameters(case)
    if baseline is not None:
        initial = np.asarray(_baseline_initial(baseline))
        start = dict(baseline_fingerprint=baseline["fingerprint"])
    else:
        resident = 1 if case.direction == "A_into_M" else 0
        candidates = equilibria.conditional_states(p, resident)
        qualifying = [s for s in candidates if s["stability"] == "stable"
                      and all(s["y"][4*j+1+resident] > 0 for j, w in enumerate(p.weights) if w)]
        if not qualifying:
            raise RuntimeError("No supported conditional start")
        selected = max(qualifying, key=lambda x: x["r"])
        initial = e.seed_state(selected["y"], p, case.direction)
        start = dict(selected=selected, qualifying=len(qualifying))
    result = integrate_finite(initial, p, years, Census(minimum_cells=0., census_yr=1.), sample_every_censuses=1)
    if result.status != "completed" or result.extinction_events:
        raise RuntimeError(f"Uncensored integration failed: {result.status}")
    if np.any(~np.isfinite(result.y)) or np.any(result.y < 0):
        raise RuntimeError("Invalid accepted physical stocks")
    RAW.mkdir(parents=True, exist_ok=True)
    temporary = data.with_suffix(".tmp")
    with temporary.open("wb") as stream:
        np.savez_compressed(stream, t=result.t, y=result.y, log_biomass=result.log_biomass,
            temperatures_k=result.temperatures_k, initial=initial,
            min_log_biomass=result.global_continuous_min_log_biomass,
            min_times=result.global_continuous_min_times_yr,
            metadata=e.dumps(result.metadata))
    temporary.replace(data)
    if source_hashes() != protocol["source_sha256"]:
        raise RuntimeError("Source changed while integrating")
    record = dict(fingerprint=fingerprint, execution_status="complete", protocol=protocol, start=start,
                  raw_file=data.name, raw_sha256=sha256(data.read_bytes()).hexdigest())
    temporary = receipt.with_suffix(".tmp")
    temporary.write_text(e.dumps(record)+"\n"); temporary.replace(receipt)
    return record


def _baseline_initial(record):
    import gzip
    with gzip.open(e.RAW / record["raw_file"], "rt") as stream:
        return json.load(stream)["initial"]


def _worker(task):
    case, years, baseline, sources = task
    return run(case, years, baseline, sources)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("planned", "exchange"), default="planned")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--years", type=float)
    args = parser.parse_args()
    sources = source_hashes()
    if args.stage == "planned":
        tasks = [(c, args.years or 30000., r, sources) for c, row, r in planned()
                 if any(int(row[f"culls_{patch}_{g}"]) for patch in ("bulk", "warm", "cold") for g in e.GUILDS)]
    else:
        tasks = [(c, args.years or 6000., None, sources) for c in continuation()]
    if args.case_id:
        tasks = [t for t in tasks if t[0].case_id in args.case_id or t[0].case_id.rsplit("_t", 1)[0] in args.case_id]
        if len(tasks) != len(args.case_id):
            raise ValueError("Unknown or duplicate case selection")
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i, r in enumerate(pool.map(_worker, tasks), 1):
            print(i, len(tasks), r["protocol"]["case"]["case_id"], flush=True)


if __name__ == "__main__":
    main()
