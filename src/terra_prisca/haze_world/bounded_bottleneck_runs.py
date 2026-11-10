"""E1 numerical protocol: cap accepted-step attempts at ten years.

The frozen E2 runner remains unchanged. This E1 protocol avoids logarithmic
acetate overflow in inadmissible large Newton trials, without changing stocks,
equations, or accepted-state positivity rules.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from . import bottleneck_runs as r
from . import buffered_experiments as e
from . import bottleneck_integration as numerical
from .bottleneck_integration import Census, integrate_finite


def sources():
    paths = (Path(__file__), Path(numerical.__file__))
    return r.source_hashes() | {str(path.relative_to(e.ROOT)): sha256(path.read_bytes()).hexdigest() for path in paths}


def run(task):
    case, baseline, years, expected = task
    _, environment = e.identity(case)
    protocol = dict(case=asdict(case), years=years, census=asdict(Census(minimum_cells=0., census_yr=1.)),
        max_step_yr=10., solver="accepted_state_trial_retry_v1", source_sha256=sources(), baseline_fingerprint=baseline["fingerprint"],
        python=environment["python"], packages=environment["packages"],
        scope="Uncensored E1 physical trajectory with bounded solver trials; one-year sampling")
    if protocol["source_sha256"] != expected:
        raise RuntimeError("Bounded-run source changed")
    fingerprint, data, receipt = r.paths(protocol)
    if receipt.exists():
        record = json.loads(receipt.read_text())
        if sha256(data.read_bytes()).hexdigest() != record["raw_sha256"]:
            raise RuntimeError("Changed bounded-run payload")
        return record
    initial = np.asarray(r._baseline_initial(baseline)); p = e.parameters(case)
    result = integrate_finite(initial, p, years, Census(minimum_cells=0., census_yr=1.),
                              sample_every_censuses=1, max_step=10.)
    if result.status != "completed" or result.extinction_events or np.any(~np.isfinite(result.y)) or np.any(result.y < 0):
        raise RuntimeError(f"Invalid bounded uncensored run: {case.case_id}")
    if sources() != expected:
        raise RuntimeError("Source changed while integrating")
    r.RAW.mkdir(parents=True, exist_ok=True)
    temporary = data.with_suffix(".tmp")
    with temporary.open("wb") as stream:
        np.savez_compressed(stream, t=result.t, y=result.y, log_biomass=result.log_biomass,
            temperatures_k=result.temperatures_k, initial=initial,
            min_log_biomass=result.global_continuous_min_log_biomass,
            min_times=result.global_continuous_min_times_yr, metadata=e.dumps(result.metadata))
    temporary.replace(data)
    record = dict(fingerprint=fingerprint, execution_status="complete", protocol=protocol,
        start=dict(baseline_fingerprint=baseline["fingerprint"]), raw_file=data.name,
        raw_sha256=sha256(data.read_bytes()).hexdigest())
    temporary = receipt.with_suffix(".tmp"); temporary.write_text(e.dumps(record)+"\n"); temporary.replace(receipt)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--years", type=float, default=30000.)
    args = parser.parse_args(); frozen = sources()
    tasks = [(c, record, args.years, frozen) for c, row, record in r.planned()
        if any(int(row[f"culls_{patch}_{g}"]) for patch in ("bulk", "warm", "cold") for g in e.GUILDS)]
    if args.case_id:
        tasks = [t for t in tasks if t[0].case_id in args.case_id or t[0].case_id.rsplit("_t", 1)[0] in args.case_id]
        if len(tasks) != len(args.case_id): raise ValueError("Unknown case selection")
    pool = ProcessPoolExecutor(max_workers=args.workers)
    try:
        futures = {pool.submit(run, t): t[0].case_id for t in tasks}
        for i, future in enumerate(as_completed(futures), 1):
            try: record = future.result()
            except Exception as error: raise RuntimeError(f"Failed {futures[future]}") from error
            print(i, len(tasks), record["protocol"]["case"]["case_id"], flush=True)
    finally:
        pool.shutdown(wait=True, cancel_futures=True)


if __name__ == "__main__": main()
