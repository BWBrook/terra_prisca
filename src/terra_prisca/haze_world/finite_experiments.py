"""Constant-protocol finite-census invasions and product-activity comparisons.

uv run python -m terra_prisca.haze_world.finite_experiments --stage main --workers 8

Workers write only their own fingerprinted raw record and completion receipt.
The collector writes public tables only after every requested case completes.
"""

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from dataclasses import asdict, dataclass, replace
from functools import lru_cache
import gzip
from hashlib import sha256
import importlib.metadata
import io
import itertools
import json
from pathlib import Path

import numpy as np

from .finite_populations import CellProcess, integrate_finite
from .population_coupling import (HOURS_PER_YEAR, equilibrium_states, fluxes,
                                  reference, rhs)
from .methane_budget import temperature_k
from .two_guilds import BASE, HENRY_30C_MOL_L_PA

ROOT = BASE.parents[1]
OUTPUT = BASE / "figures/finite_populations"
RAW = ROOT / "local/haze/finite_populations"
FRACTIONS = (0., .5, .9)
FLOORS = (1., 1e6, 1e12)
IMMIGRATION = (0., .1, 1., 100.)
OCCUPANCY = {0: "empty", 1: "acetogen_only", 2: "methanogen_only", 3: "both"}


@dataclass(frozen=True)
class Case:
    case_id: str
    activity: str
    fraction: float
    minimum_cells: float
    relative_immigration_yr: float
    direction: str
    census_yr: float = 10.
    years: float = 100000.


def design(stage="main", years=100000.):
    if stage == "main":
        combinations = itertools.product(("fixed", "products"), FRACTIONS, FLOORS, IMMIGRATION,
                                         ("A_into_M", "M_into_A"))
        return [Case(f"main_{i:04d}_t{years:g}", *values, years=years)
                for i, values in enumerate(combinations)]
    if stage == "census":
        boundaries = (("fixed", .5, 1e6, 1., "A_into_M"),
                      ("products", .5, 1e6, 1., "A_into_M"),
                      ("fixed", .9, 1., 0., "M_into_A"))
        return [Case(f"census_{i:04d}_t{years:g}", *values, census_yr=census, years=years)
                for i, (values, census) in enumerate(itertools.product(boundaries, (1., 10., 30.)))]
    if stage == "pilot":
        values = (("fixed", .5, 1., 0., "A_into_M"),
                  ("fixed", .9, 1., 1., "M_into_A"),
                  ("products", .5, 1., 1., "A_into_M"),
                  ("products", .5, 1., 100., "M_into_A"))
        return [Case(f"pilot_{i:04d}_t1000", *row, years=1000.) for i, row in enumerate(values)]
    raise ValueError("Unknown finite-census stage")


def parameters(case):
    p = replace(reference(.3), acetate_fraction=case.fraction, activity_feedback=case.activity)
    rate = case.relative_immigration_yr * case.minimum_cells
    process = CellProcess(minimum_cells=case.minimum_cells, census_yr=case.census_yr,
                          immigration_cells_yr=(rate, rate))
    return p, process


@lru_cache(maxsize=None)
def resident(activity, fraction, direction):
    p = replace(reference(.3), acetate_fraction=fraction, activity_feedback=activity)
    enabled = (False, True) if direction == "A_into_M" else (True, False)
    kind = "methanogen" if direction == "A_into_M" else "acetogen"
    choices = [e for e in equilibrium_states(replace(p, enabled=enabled))
               if e["kind"] == kind and e["stable"]]
    if len(choices) != 1:
        raise RuntimeError(f"Expected one conditional {kind} equilibrium; found {len(choices)}")
    return choices[0]


def initial_state(case):
    state = resident(case.activity, case.fraction, case.direction)["y"].copy()
    state[1 if case.direction == "A_into_M" else 2] = 1e-12
    return state


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, np.ndarray)):
        return [clean(v) for v in value]
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, complex):
        return [clean(value.real), clean(value.imag)]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def dumps(value):
    return json.dumps(clean(value), sort_keys=True, allow_nan=False)


def source_hashes():
    files = [Path(__file__), *[Path(__file__).with_name(name) for name in (
        "finite_populations.py", "population_coupling.py", "two_guilds.py", "hydrogen_uptake.py",
        "woodii1998.py", "methane_budget.py", "darwinian.py")],
        ROOT / "src/terra_prisca/haze_response/arney2016.py",
        ROOT / "models/haze_response/arney2016/figure4.csv",
        ROOT / "models/haze_response/arney2016/cases.csv",
        BASE / "evidence/kotsyurbenko2001_table2.csv", BASE / "evidence/peters1998_chemostat.csv"]
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in files}


def identity(case):
    p, process = parameters(case)
    record = dict(case=asdict(case), parameters=asdict(p), cell_process=asdict(process),
                  source_sha256=source_hashes(),
                  packages={name: importlib.metadata.version(name) for name in ("numpy", "scipy")},
                  initial_protocol="Conditional no-immigration pure resident; missing guild seeded at1e-12gDW/L; f held fixed; mean immigration starts att0")
    return sha256(dumps(record).encode()).hexdigest(), record


def summarize(case, p, process, result):
    analysis_year = result.metadata["last_census_yr"]
    indices = np.flatnonzero(result.t <= analysis_year + 1e-8)
    end = indices[-1]
    y = result.y[:, end]
    volume = result.metadata["total_habitat_l"]
    conversion = volume / process.cell_mass_gdw
    cells = y[1:3] * conversion
    mask = int(result.census_activity[-1])
    start = max(0., analysis_year - 20000.)
    late = indices[result.t[indices] >= start]
    sample = result.y[:, late]
    floor_density = process.minimum_cells / conversion
    scales = np.maximum(np.mean(abs(sample), axis=1), [1., floor_density, floor_density, 1e-9, .001])
    spans = np.ptp(sample, axis=1) / scales
    temperatures = np.asarray(temperature_k(sample[4], p.climate))
    flags = result.census_activity[np.arange(len(result.census_activity)) * process.census_yr >= start]
    changes = int(np.sum(flags[1:] != flags[:-1]))
    f = fluxes(y, p)
    derivative = rhs(y, p)
    derivative[1:3] += result.metadata["immigration_gdw_l_yr"]
    hydraulic_yr = HENRY_30C_MOL_L_PA / (p.biology.exchange_mol_l_h_pa * HOURS_PER_YEAR)
    rates = [abs(derivative[0]) * hydraulic_yr / max(y[0], 1.),
             abs(derivative[3]) * p.acetate_lifetime_yr / max(y[3], 1e-9),
             abs(derivative[4]) * p.loss.lifetime_yr / max(y[4], .001)]
    for i in range(2):
        if mask & (1 << i):
            rates.append(abs(derivative[i + 1]) / max(y[i + 1], floor_density) / (p.biology.loss_h * HOURS_PER_YEAR))
    stationary = (case.years >= 100000 and max(spans) < 1e-3 and np.ptp(temperatures) < .01
                  and max(rates) < 1e-3 and changes == 0)
    culls = Counter(e["guild"] for e in result.extinction_events)
    arrivals = Counter(e["guild"] for e in result.arrival_events)
    late_culls = sum(start <= e["time_yr"] <= analysis_year for e in result.extinction_events)
    row = dict(**asdict(case), analysis_year=float(analysis_year), occupancy=OCCUPANCY[mask],
               settling_status="census_stationary" if stationary else "unsettled" if case.years >= 100000 else "pilot_only",
               phase_category=OCCUPANCY[mask] if stationary else "unsettled",
               temperature_k=f["temperature_k"], climate_domain=f["climate_domain"], methane_ratio=y[4],
               pressure_pa=y[0], acetate_mol_l=y[3], cells_a=cells[0], cells_m=cells[1],
               net_growth_a_yr=f["net_growth_yr"][0], net_growth_m_yr=f["net_growth_yr"][1],
               immigration_replacement_a_yr=process.immigration_cells_yr[0] / cells[0] if cells[0] else None,
               immigration_replacement_m_yr=process.immigration_cells_yr[1] / cells[1] if cells[1] else None,
               culls_a=culls["acetogen"], culls_m=culls["methanogen"],
               retained_returns_a=arrivals["acetogen"], retained_returns_m=arrivals["methanogen"],
               first_cull_a_yr=result.first_extinction_by_guild_yr[0], first_cull_m_yr=result.first_extinction_by_guild_yr[1],
               late_culls=late_culls, late_occupancy_changes=changes,
               max_late_relative_span=float(max(spans)), late_temperature_span_k=float(np.ptp(temperatures)),
               max_scaled_derivative=float(max(rates)), methane_tendency_ratio_yr=derivative[4],
               endpoint_status="after_last_scheduled_census", minimum_scope=result.metadata["minimum_scope"],
               min_pre_census_cells_a=result.min_cells[0], min_pre_census_cells_m=result.min_cells[1],
               solver_nfev=result.metadata["nfev"], solver_resets=result.metadata["solver_resets"],
               wall_seconds=result.metadata["wall_seconds"])
    for key, values in result.ledger.items():
        row[key + "_a"], row[key + "_m"] = values
    return clean(row)


def run_case(case, raw_dir):
    fingerprint, protocol = identity(case)
    prefix = f"{case.case_id}-{fingerprint[:16]}"
    receipt = raw_dir / (prefix + ".receipt.json")
    data = raw_dir / (prefix + ".json.gz")
    if receipt.exists():
        record = json.loads(receipt.read_text())
        if record["fingerprint"] != fingerprint or sha256(data.read_bytes()).hexdigest() != record["raw_sha256"]:
            raise RuntimeError(f"Receipt/data mismatch: {case.case_id}")
        return record
    p, process = parameters(case)
    y0 = initial_state(case)
    result = integrate_finite(y0, p, case.years, process, sample_every_censuses=1)
    summary = summarize(case, p, process, result)
    raw_dir.mkdir(parents=True, exist_ok=True)
    temporary = data.with_suffix(".tmp")
    with temporary.open("wb") as binary, gzip.GzipFile(filename="", mode="wb", fileobj=binary, mtime=0) as compressed, io.TextIOWrapper(compressed) as handle:
        handle.write(dumps(dict(protocol=protocol, initial_y=y0, summary=summary, result=asdict(result))))
    temporary.replace(data)
    record = dict(status="complete", fingerprint=fingerprint, protocol=protocol, summary=summary,
                  raw_file=data.name, raw_sha256=sha256(data.read_bytes()).hexdigest())
    temp_receipt = receipt.with_suffix(".tmp")
    temp_receipt.write_text(dumps(record) + "\n")
    temp_receipt.replace(receipt)
    return record


def write_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: format(v, ".10g") if isinstance(v, float) else v for k, v in row.items()})


def plot_maps(rows, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Patch
    labels = ("acetogen_only", "methanogen_only", "both", "empty", "unsettled")
    colors = ("#dc8f38", "#4679b4", "#3f8b60", "#dedede", "#8b7499")
    lookup = {name: i for i, name in enumerate(labels)}
    for direction in ("A_into_M", "M_into_A"):
        fig, axes = plt.subplots(2, 3, figsize=(10, 5), layout="constrained", sharex=True, sharey=True)
        for i, activity in enumerate(("fixed", "products")):
            for j, fraction in enumerate(FRACTIONS):
                ax = axes[i, j]
                selected = [r for r in rows if r["direction"] == direction and r["activity"] == activity and r["fraction"] == fraction]
                matrix = [[lookup[next(r for r in selected if r["minimum_cells"] == n and r["relative_immigration_yr"] == rate)["phase_category"]]
                           for rate in IMMIGRATION] for n in FLOORS]
                ax.imshow(matrix, origin="lower", aspect="auto", cmap=ListedColormap(colors),
                          norm=BoundaryNorm(np.arange(6) - .5, 5))
                ax.set_xticks(range(4), ("0", "0.1", "1", "100"))
                ax.set_yticks(range(3), ("1", "10⁶", "10¹²"))
                ax.set_title(f"{activity} activities; f={fraction:g}", fontsize=10)
                if i == 1:
                    ax.set_xlabel("Mean immigration / removal floor (yr⁻¹)")
                if j == 0:
                    ax.set_ylabel("Removal floor (global cells)")
        fig.suptitle("Acetogens introduced into methanogens" if direction == "A_into_M" else "Methanogens introduced into acetogens")
        fig.legend(handles=[Patch(color=c, label=l.replace("_", " ")) for c, l in zip(colors, labels)],
                   loc="outside lower center", ncol=3, frameon=False)
        fig.savefig(output / f"endpoints_{direction}.png", dpi=145)
        plt.close(fig)


def collect(cases, raw_dir, output, stage):
    receipts = []
    for case in cases:
        fingerprint, _ = identity(case)
        path = raw_dir / f"{case.case_id}-{fingerprint[:16]}.receipt.json"
        if not path.exists():
            raise RuntimeError(f"No matching complete receipt for {case.case_id}")
        record = json.loads(path.read_text())
        if record["status"] != "complete" or record["fingerprint"] != fingerprint:
            raise RuntimeError(f"Invalid completion receipt: {case.case_id}")
        if sha256((raw_dir / record["raw_file"]).read_bytes()).hexdigest() != record["raw_sha256"]:
            raise RuntimeError(f"Raw hash mismatch: {case.case_id}")
        receipts.append(record)
    output.mkdir(parents=True, exist_ok=True)
    rows = [r["summary"] for r in receipts]
    write_csv(output / f"{stage}_summary.csv", rows)
    manifest = dict(stage=stage, cases=len(cases), sources=source_hashes(),
                    phase_counts=dict(Counter(r["phase_category"] for r in rows)),
                    receipts=[dict(case_id=r["summary"]["case_id"], fingerprint=r["fingerprint"],
                                   raw_file=r["raw_file"], raw_sha256=r["raw_sha256"]) for r in receipts],
                    settling_rule="After-last-census samples; last20kyr span<0.001, temperature span<0.01K, scaled derivative<0.001, unchanged occupancy; duration>=100kyr",
                    census_population_model="Deterministic continuous densities, scheduled removal and mean immigration; not integer stochastic arrival probabilities",
                    extrema_scope="Pre-census samples only, not continuous extrema")
    (output / f"{stage}_manifest.json").write_text(dumps(manifest) + "\n")
    if stage == "main" and len(cases) == 144:
        plot_maps(rows, output)
    if any(p.stat().st_size >= 1_000_000 for p in output.iterdir()):
        raise RuntimeError("Public output exceeds1MB; retain detailed data only in raw storage")
    return manifest


def run_equilibria(output):
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    schemes = [("supply", a, f, 1., "constant", potential) for a, f, potential in
               itertools.product(("fixed", "products"), FRACTIONS, (.12, .2, .24, .3, .4, .5, .6))]
    schemes += [("pool_stress", a, f, lag, recycling, .3) for a, f, lag, recycling in
                itertools.product(("fixed", "products"), (.5, .9, 1.), (1., 100., 10000.), ("constant", "cold_limited"))]
    for group, activity, fraction, lag, recycling, potential in schemes:
        p = replace(reference(potential), activity_feedback=activity, acetate_fraction=fraction,
                    acetate_lifetime_yr=lag, recycling_variant=recycling)
        for e in equilibrium_states(p):
            rows.append(clean(dict(group=group, activity=activity, fraction=fraction, lag_yr=lag,
                                   recycling=recycling, potential=potential, kind=e["kind"],
                                   stability=e["stability"], temperature_k=e["t_k"], methane_ratio=e["r"],
                                   pressure_pa=e["y"][0], acetate_mol_l=e["y"][3],
                                   climate_domain=e["domain"], max_real_yr=e["max_real_yr"],
                                   scaled_redox_residual=e["redox_residual"] / fluxes(e["y"], p)["supply_h2_mol_l_yr"])))
    write_csv(output / "continuum_equilibria.csv", rows)
    starts = []
    for activity, fraction, direction in itertools.product(("fixed", "products"), FRACTIONS, ("A_into_M", "M_into_A")):
        case = Case("initial", activity, fraction, 1., 0., direction)
        p, process = parameters(case)
        y = initial_state(case)
        f = fluxes(y, p)
        starts.append(dict(activity=activity, fraction=fraction, direction=direction,
                           temperature_k=f["temperature_k"], pressure_pa=y[0], acetate_mol_l=y[3],
                           net_growth_a_yr=f["net_growth_yr"][0], net_growth_m_yr=f["net_growth_yr"][1],
                           seed_g_l=1e-12, seed_global_cells=1e-12 * p.habitat_l_cm2 * process.surface_cm2 / process.cell_mass_gdw))
    write_csv(output / "initial_states.csv", starts)
    (output / "equilibria_manifest.json").write_text(dumps(dict(sources=source_hashes(), configurations=len(schemes),
        state_records=len(rows), activity_variant="Normalized product quarter powers; fixed CO2/pH and transferred base thresholds remain assumptions")) + "\n")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("main", "census", "pilot", "equilibria", "all"), default="all")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--years", type=float, default=100000.)
    parser.add_argument("--raw-dir", type=Path, default=RAW)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--list-cases", action="store_true")
    args = parser.parse_args()
    if args.workers < 1 or args.years <= 0 or not np.isfinite(args.years):
        parser.error("Use positive worker count and duration")
    stages = ("main", "census") if args.stage == "all" else (() if args.stage == "equilibria" else (args.stage,))
    if args.stage in ("equilibria", "all") and not args.list_cases:
        run_equilibria(args.output)
    for stage in stages:
        cases = design(stage, args.years)
        if args.case_id:
            selected = set(args.case_id)
            cases = [c for c in cases if c.case_id in selected]
            if not cases:
                parser.error("No requested case IDs occur in the selected stage")
        if args.list_cases:
            print(dumps([asdict(c) for c in cases]))
            continue
        if not args.collect_only:
            if args.workers == 1:
                for case in cases:
                    run_case(case, args.raw_dir)
            else:
                with ProcessPoolExecutor(max_workers=args.workers) as executor:
                    futures = {executor.submit(run_case, case, args.raw_dir): case.case_id for case in cases}
                    for future in as_completed(futures):
                        future.result()
        print(dumps(collect(cases, args.raw_dir, args.output, stage)))


if __name__ == "__main__":
    main()
