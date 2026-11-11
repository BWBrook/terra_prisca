"""Bounded X12 archive checks; writes only the explicitly supplied output JSON."""

import argparse
from collections import Counter
from dataclasses import asdict
import gzip
from hashlib import sha256
import json
from pathlib import Path
import platform

import numpy as np

from terra_prisca.haze_world import buffered_experiments as buffered
from terra_prisca.haze_world import habitat_integration as habitat
from terra_prisca.haze_world import refuge_experiments as refuge
from terra_prisca.haze_world import refuge_integration
from terra_prisca.haze_world import bottleneck_integration
from terra_prisca.haze_world import dormancy_experiments
from terra_prisca.haze_world import dormancy_jacobian_integration as dormancy_solver

ROOT = Path.cwd()


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def legacy_roots(poly, lo, hi):
    return [float(v.real) for v in poly.roots() if abs(v.imag) < 1e-8 and lo <= v.real <= hi]


def boundary_inventory():
    folder = ROOT / "local/haze/refuge_coupling"
    manifest = json.loads((ROOT / "models/haze_world/figures/refuge_coupling/raw_manifest.json").read_text())
    rows = []
    for entry in manifest["files"]:
        path = folder / Path(entry["path"]).name
        if path.suffix != ".gz":
            continue
        if digest(path) != entry["sha256"]:
            raise RuntimeError(f"Changed archived payload: {path}")
        record = json.load(gzip.open(path, "rt"))
        result = record.get("result")
        if not result or not result.get("domain_exit"):
            continue
        exit_ = result["domain_exit"]
        ratio = result["y"][-1][-1]
        residual = min(abs(ratio - b) for b in exit_["ratio_interval"] if b is not None)
        rows.append(dict(path=str(path.relative_to(ROOT)), sha256=entry["sha256"],
                         case_id=record["protocol"]["case"]["case_id"],
                         time_yr=exit_["time_yr"], ratio=ratio, residual=residual,
                         host=record["protocol"].get("operating_system", "not recorded")))
    return rows


def compare_minimum_function(module, name, root_module):
    original = getattr(module, name)
    new_roots = root_module._real_roots
    report = dict(calls=0, max_log_minimum_difference=0., finite_mask_changes=0)

    def checked(*args, **kwargs):
        result = original(*args, **kwargs)
        root_module._real_roots = legacy_roots
        try:
            control = original(*args, **kwargs)
        finally:
            root_module._real_roots = new_roots
        report["calls"] += 1
        # Both helpers return local minima first; dormancy adds global minima
        # in its third return slot. Times are not a separate stock estimand.
        indices = (0, 2) if len(result) == 4 else (0,)
        for index in indices:
            a, b = np.asarray(result[index]), np.asarray(control[index])
            report["finite_mask_changes"] += int(np.count_nonzero(np.isfinite(a) != np.isfinite(b)))
            mask = np.isfinite(a) & np.isfinite(b)
            if np.any(mask):
                report["max_log_minimum_difference"] = max(report["max_log_minimum_difference"], float(np.max(abs(a[mask] - b[mask]))))
        return result

    setattr(module, name, checked)
    return original, report


def replay_headline_minimum():
    import csv
    table = ROOT / "models/haze_world/figures/bottleneck/survival.csv"
    row = next(r for r in csv.DictReader(table.open()) if r["configuration"] == "warm"
               and float(r["fraction"]) == 0 and float(r["dispersal_yr"]) == 1e-6)
    path = ROOT / "local/haze/bottleneck" / row["source_raw_file"]
    if digest(path) != row["source_raw_sha256"]:
        raise RuntimeError("Changed headline trajectory")
    receipt = json.loads(path.with_suffix(".receipt.json").read_text())
    saved = np.load(path)
    case = buffered.Case(**receipt["protocol"]["case"])
    parameters = buffered.parameters(case)
    local_original, local_report = compare_minimum_function(habitat, "_dense_minima", habitat)
    global_original, global_report = compare_minimum_function(habitat, "_dense_global_minima", habitat)
    try:
        result = bottleneck_integration.integrate_finite(saved["initial"], parameters, 2000.,
            habitat.Census(minimum_cells=0., census_yr=1.), sample_every_censuses=1)
    finally:
        habitat._dense_minima = local_original
        habitat._dense_global_minima = global_original
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path),
                host=receipt["protocol"].get("operating_system", "not recorded"),
                status=result.status, replay_end_yr=float(result.t[-1]),
                archived_minimum_times_yr=saved["min_times"].tolist(),
                archived_minimum_log_biomass=saved["min_log_biomass"].tolist(),
                repaired_minimum_times_yr=result.global_continuous_min_times_yr.tolist(),
                repaired_minimum_log_biomass=result.global_continuous_min_log_biomass.tolist(),
                minimum_function_controls=dict(local=local_report, global_=global_report))


def replay_linux_minimum():
    folder = ROOT / "local/haze/dormancy_linux_pilot"
    receipt_path = next(folder.glob("*.receipt.json"))
    receipt = json.loads(receipt_path.read_text())
    path = folder / receipt["raw_file"]
    if digest(path) != receipt["raw_sha256"]:
        raise RuntimeError("Changed Linux pilot payload")
    saved = np.load(path)
    case = dormancy_experiments.Case(**receipt["protocol"]["case"])
    parameters = dormancy_experiments.parameters(case)
    if asdict(parameters) != receipt["protocol"]["parameters"]:
        # Dataclass tuples serialize as lists; compare in the serialized form.
        if json.loads(json.dumps(asdict(parameters))) != receipt["protocol"]["parameters"]:
            raise RuntimeError("Linux pilot physics differs from current replay")
    original, report = compare_minimum_function(dormancy_solver, "_dense_minima", habitat)
    try:
        result = dormancy_solver.integrate_finite(saved["initial"], parameters, 1500.,
            habitat.Census(**receipt["protocol"]["census"]), rtol=case.rtol,
            max_step=case.max_step_yr, sample_every_censuses=1)
    finally:
        dormancy_solver._dense_minima = original
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path),
                host=receipt["protocol"]["operating_system"],
                status=result.status, replay_end_yr=float(result.t[-1]),
                archived_minimum_times_yr=saved["min_times"].tolist(),
                archived_minimum_log_biomass=[float(v) if np.isfinite(v) else None for v in saved["min_log_biomass"]],
                repaired_minimum_times_yr=result.global_continuous_min_times_yr.tolist(),
                repaired_minimum_log_biomass=[float(v) if np.isfinite(v) else None for v in result.global_continuous_min_log_biomass],
                minimum_function_control=report)


def replay_exit_tail(row):
    path = ROOT / row["path"]
    record = json.load(gzip.open(path, "rt"))
    saved = record["result"]
    # A last stored physical state is sufficient only if every present lineage
    # still has a representable physical stock; do not turn underflow into loss.
    k = len(saved["t"]) - 2
    state = np.asarray(saved["y"])[:, k]
    logs = np.asarray(saved["log_biomass"], dtype=float)[:, :, k]
    for patch in range(2):
        for guild in range(2):
            if np.isfinite(logs[patch, guild]) and state[4*patch+1+guild] == 0:
                raise RuntimeError("Tail replay would lose a subrepresentable lineage")
    case = refuge.Case(**record["protocol"]["case"])
    parameters = refuge.parameters(case)
    span = saved["t"][-1] - saved["t"][k]
    result = refuge_integration.integrate(state, parameters, span + 1., rtol=1e-10, max_step=.1)
    return dict(path=row["path"], restart_time_yr=saved["t"][k],
                archived_exit_time_yr=saved["t"][-1],
                repaired_exit_time_yr=saved["t"][k] + float(result.t[-1]),
                repaired_status=result.status,
                repaired_boundary_residual=min(abs(result.y[-1,-1]-b) for b in saved["domain_exit"]["ratio_interval"] if b is not None))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    boundaries = boundary_inventory()
    report = dict(scope="Boundary checks and bounded selected replays; not archive-wide dense-polynomial certification",
                  machine=dict(system=platform.system(), architecture=platform.machine()),
                  source_sha256={str(p.relative_to(ROOT)): digest(p) for p in [
                      Path(__file__), *(ROOT / "src/terra_prisca/haze_world" / n for n in (
                          "dense_roots.py", "habitat_integration.py", "refuge_integration.py", "methane_budget.py"))]},
                  domain_exits=boundaries,
                  counts=dict(exits=len(boundaries), boundary_residual_over_1e_8=sum(r["residual"] > 1e-8 for r in boundaries)),
                  provenance=dict(Counter(r["host"] for r in boundaries)))
    report["exit_tail_replays"] = [replay_exit_tail(row) for row in (boundaries[0], boundaries[-1])]
    report["headline_minimum_replay"] = replay_headline_minimum()
    report["linux_minimum_replay"] = replay_linux_minimum()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "domain_exits"}, indent=2))


if __name__ == "__main__":
    main()
