"""Bounded switch-location experiments for the positive-outlet H2 model.

    uv run python -m terra_prisca.haze_world.competition_switches

Source-window paths and named low-temperature continuations are separate.
Crossings of intrinsic R* are distinguished from exchanges of living winners.
"""

import argparse
from collections import Counter
import csv
from dataclasses import asdict, replace
import gzip
from hashlib import sha256
import io
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from .two_guilds import (BASE, Competition, FIRST_ORDER_LIMIT_MOL_L,
                         HENRY_30C_MOL_L_PA, MSB, MSP, delivery, equilibrium,
                         parameter_grid)

SUPPLY = 1e-6
SOURCE_WINDOW_K = (277.15, 290.)
EXTENDED_WINDOW_K = (273., 290.)
K_CUTS = {"reference": (1., 1.), "both_div3": (1 / 3, 1 / 3),
          "both_div7": (1 / 7, 1 / 7), "acetogen_div3": (1 / 3, 1.),
          "acetogen_div7": (1 / 7, 1.)}
LABELS = ("acetogen", "methanogen", "lifeless", "outside_first_order_domain", "tie")


def temperature_grid(lower, upper, step=.1):
    if not 273 <= lower < upper <= 303.15 or not np.isfinite(step) or step <= 0:
        raise ValueError("Use an ordered 273–303.15 K interval and positive step")
    knots = (273., 277.15, 283.15, 288.15, 293.15, 298.15, 303.15)
    values = np.r_[np.arange(lower, upper, step), lower, upper,
                   [t for t in knots if lower <= t <= upper]]
    return np.unique(np.round(values, 10))


def _orientation(left, right):
    if not np.isfinite(left) or not np.isfinite(right):
        return "boundary_or_undefined"
    if left < 0 < right:
        return "acetogen_cold_methanogen_warm"
    if left > 0 > right:
        return "methanogen_cold_acetogen_warm"
    return "contact_without_exchange"


def finite_crossings(temperatures, values, evaluate):
    """Locate each sampled sign change, never bridge an undefined sample.

    A finite sampling grid cannot exclude two unseen crossings inside one cell.
    Consecutive zero samples are retained as a tie bracket, not many switches.
    """
    ts, ys = np.asarray(temperatures), np.asarray(values)
    if ts.ndim != 1 or ys.shape != ts.shape or len(ts) < 2 or np.any(np.diff(ts) <= 0):
        raise ValueError("Provide matching ordered samples")
    candidates = []
    zero = np.isfinite(ys) & (ys == 0)
    starts = np.flatnonzero(zero & np.r_[True, ~zero[:-1]])
    for first in starts:
        last = first
        while last + 1 < len(ts) and zero[last + 1]:
            last += 1
        candidates.append((float(ts[first]), float(ts[last]), "sampled_tie_interval" if last > first else "root"))
    for i in range(len(ts) - 1):
        if not np.isfinite(ys[i:i + 2]).all() or zero[i:i + 2].any() or np.signbit(ys[i]) == np.signbit(ys[i + 1]):
            continue
        try:
            root = brentq(evaluate, ts[i], ts[i + 1], xtol=1e-9)
        except ValueError:
            candidates.append((float(ts[i]), float(ts[i + 1]), "unresolved_bracket"))
        else:
            candidates.append((float(root), float(root), "root"))
    result = []
    for lo, hi, kind in sorted(candidates):
        delta = min(1e-4, float(np.min(np.diff(ts))) / 10)
        left = evaluate(lo - delta) if lo - delta >= ts[0] else np.nan
        right = evaluate(hi + delta) if hi + delta <= ts[-1] else np.nan
        result.append(dict(lower_k=lo, upper_k=hi, kind=kind,
                           orientation=_orientation(left, right)))
    return result


def _difference(temperature_k, config):
    e = equilibrium(temperature_k - 273.15, config, SUPPLY)
    a, m = e["rstar_a_pa"], e["rstar_m_pa"]
    return a - m if np.isfinite(a) and np.isfinite(m) else np.nan


def scan_path(config, *, lower=277.15, upper=290., step=.1):
    if config.exchange_mol_l_h_pa <= 0:
        raise ValueError("Switch experiments require a positive resource outlet")
    ts = temperature_grid(lower, upper, step)
    rows = []
    for t in ts:
        e = equilibrium(t - 273.15, config, SUPPLY)
        rows.append(dict(temperature_k=float(t), status=e["status"], winner=e["winner"],
                         pressure_pa=e["pressure_pa"], rstar_a_pa=e["rstar_a_pa"],
                         rstar_m_pa=e["rstar_m_pa"], capture_fraction=e["capture_fraction"],
                         biomass_a_g_l=float(e["biomass_g_l"][0]),
                         biomass_m_g_l=float(e["biomass_g_l"][1])))
    diff = [r["rstar_a_pa"] - r["rstar_m_pa"] if
            np.isfinite((r["rstar_a_pa"], r["rstar_m_pa"])).all() else np.nan for r in rows]
    events = finite_crossings(ts, diff, lambda t: _difference(t, config))
    for event in events:
        t = (event["lower_k"] + event["upper_k"]) / 2
        e = equilibrium(t - 273.15, config, SUPPLY)
        root_pressure = e["rstar_a_pa"]
        in_domain = config.kinetics != "first_order" or root_pressure * HENRY_30C_MOL_L_PA <= FIRST_ORDER_LIMIT_MOL_L
        reachable = np.isfinite(root_pressure) and root_pressure < e["lifeless_pressure_pa"] and in_domain
        event.update(pressure_pa=root_pressure, reachable=bool(reachable), actual_exchange=False)
        if event["kind"] == "root" and reachable and event["orientation"] in (
                "acetogen_cold_methanogen_warm", "methanogen_cold_acetogen_warm"):
            delta = 1e-4
            if lower <= t - delta and t + delta <= upper:
                before = equilibrium(t - delta - 273.15, config, SUPPLY)["winner"]
                after = equilibrium(t + delta - 273.15, config, SUPPLY)["winner"]
                event["actual_exchange"] = {before, after} == {"acetogen", "methanogen"}
    transitions = [dict(lower_k=a["temperature_k"], upper_k=b["temperature_k"],
                        before=a["winner"], after=b["winner"])
                   for a, b in zip(rows[:-1], rows[1:]) if a["winner"] != b["winner"]]
    return rows, events, transitions


def cases():
    """Controlled cuts plus a separate 243-set base-grid audit, not their product."""
    for strain, form, (cut, scales), ea, em, p0, variant in itertools.product(
            (MSB, MSP), ("saturating", "first_order"), K_CUTS.items(),
            (-20000., -24000., -28000.), (-24000., -28000., -32000.),
            (30., 300., 3000.), ("none", "constant_shape", "arrhenius_continuation")):
        c = Competition(methanogen=strain, kinetics=form, threshold_shape="fixed_energy",
                        km_scale_a=scales[0], km_scale_m=scales[1],
                        cessation_energy_a_j=ea, cessation_energy_m_j=em,
                        exchange_mol_l_h_pa=SUPPLY / p0, low_temperature_variant=variant)
        yield "controlled", cut, p0, c
    for strain, form in itertools.product((MSB, MSP), ("saturating", "first_order")):
        for c in parameter_grid(strain):
            yield "base_grid", "reference", 300., replace(c, kinetics=form, threshold_shape="fixed_energy",
                                                          exchange_mol_l_h_pa=SUPPLY / 300.)


def _write_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _delivery_sensitivity():
    rows = []
    for strain, form, p0, t, assimilation in itertools.product((MSB, MSP), ("saturating", "first_order"),
                                                              (30., 300., 3000.), (4., 10., 15., 16.85, 20., 30.), (0., .0824)):
        c = Competition(methanogen=strain, kinetics=form, threshold_shape="fixed_energy",
                        exchange_mol_l_h_pa=SUPPLY / p0, assimilation_m=assimilation)
        e = equilibrium(t, c, SUPPLY)
        methane = delivery(e["pressure_pa"], e["biomass_g_l"], t, c)["methane_mol_l_h"] if e["status"] == "living" else np.nan
        rows.append(dict(methanogen=strain, kinetics=form, lifeless_pressure_pa=p0,
                         temperature_c=t, assimilation_m_mol_h2_g=assimilation,
                         winner=e["winner"], rstar_a_pa=e["rstar_a_pa"], rstar_m_pa=e["rstar_m_pa"],
                         capture_fraction=e["capture_fraction"], methane_mol_l_h=methane))
    return rows


def _plot_maps(output, config_rows, points):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from matplotlib.patches import Patch
    colors = ("#dc8f38", "#4679b4", "#ededed", "#8a647a", "#6fa776")
    cmap = ListedColormap(colors)
    lookup = {name: i for i, name in enumerate(LABELS)}
    for variant in ("none", "constant_shape", "arrhenius_continuation"):
        fig, axes = plt.subplots(4, 3, figsize=(12, 9), sharex=True, sharey=True, layout="constrained")
        for row, (strain, form) in enumerate(itertools.product((MSB, MSP), ("saturating", "first_order"))):
            for col, p0 in enumerate((30., 300., 3000.)):
                ax = axes[row, col]
                selected = [c for c in config_rows if c["group"] == "controlled" and c["methanogen"] == strain
                            and c["kinetics"] == form and c["lifeless_pressure_pa"] == p0
                            and c["low_temperature_variant"] == variant
                            and c["cessation_energy_a_j"] == -24000. and c["cessation_energy_m_j"] == -28000.]
                matrix = []
                ts = None
                for name in K_CUTS:
                    case = next(c for c in selected if c["k_cut"] == name)
                    path = points[case["path_id"]]
                    ts = np.array([p["temperature_k"] for p in path])
                    matrix.append([lookup[p["winner"]] for p in path])
                ax.pcolormesh(ts, np.arange(len(K_CUTS)), np.asarray(matrix), cmap=cmap,
                              norm=BoundaryNorm(np.arange(6) - .5, 5), shading="nearest")
                if variant != "none":
                    ax.axvspan(273., 277.15, facecolor="none", edgecolor="#444444", hatch="///", linewidth=0.)
                if row == 0:
                    ax.set_title(f"Lifeless pressure {p0:g} Pa")
                if col == 0:
                    ax.set_yticks(np.arange(len(K_CUTS)),
                                  ("reference", "both ÷3", "both ÷7", "A only ÷3", "A only ÷7"), fontsize=8)
                    ax.set_ylabel(f"{strain.split()[-1]}\n{'saturating A' if form == 'saturating' else 'first-order A'}", fontsize=9)
                if row == 3:
                    ax.set_xlabel("Temperature (K)")
                ax.set_xlim(ts[0], ts[-1])
        fig.legend(handles=[Patch(color=c, label=n.replace("_", " ")) for c, n in zip(colors, LABELS)],
                   loc="outside lower center", ncol=3, frameon=False)
        fig.suptitle("Within measured uptake-temperature range" if variant == "none" else f"Named continuation: {variant.replace('_', ' ')}")
        fig.savefig(output / f"winner_map_{variant}.png", dpi=145)
        plt.close(fig)


def _plot_switches(output, configurations, events):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    by_id = {c["path_id"]: c for c in configurations}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True, layout="constrained")
    for ax, group in zip(axes, ("controlled", "base_grid")):
        for event in events:
            c = by_id[event["path_id"]]
            if c["group"] != group or c["low_temperature_variant"] != "none" or c["lifeless_pressure_pa"] != 300. or event["kind"] != "root":
                continue
            color = "#4679b4" if c["methanogen"] == MSB else "#dc8f38"
            marker = "v" if event["orientation"] == "methanogen_cold_acetogen_warm" else "^"
            ax.scatter(event["lower_k"], event["pressure_pa"], s=25, marker=marker,
                       edgecolor=color, facecolor=color if event["actual_exchange"] else "none", alpha=.65)
        ax.axhline(300., color="#555555", ls="--", lw=1)
        ax.set(yscale="log", xlabel="Intrinsic crossing temperature (K)",
               title="Controlled K and energy cuts" if group == "controlled" else "243-set base grid, two strains and uptake forms")
        ax.set_xlim(277.15, 290.)
    axes[0].set_ylabel("Shared R* at crossing (Pa)")
    fig.legend(handles=[Line2D([], [], color="#4679b4", marker="o", ls="", label="MSB"),
                        Line2D([], [], color="#dc8f38", marker="o", ls="", label="MSP"),
                        Line2D([], [], color="#555555", marker="^", ls="", label="A cold → M warm"),
                        Line2D([], [], color="#555555", marker="v", ls="", label="M cold → A warm"),
                        Line2D([], [], color="#555555", marker="o", markerfacecolor="none", ls="", label="Not an exchange of living winners")],
               loc="outside lower center", ncol=3, frameon=False)
    fig.savefig(output / "switch_pressures.png", dpi=145)
    plt.close(fig)


def _resolution_audit(configurations, summaries, events, step):
    by_id = {r["path_id"]: r for r in summaries}
    rows = []
    for index, conf in enumerate(configurations):
        selected = ((conf["group"] == "controlled" and conf["lifeless_pressure_pa"] == 300.
                     and conf["cessation_energy_a_j"] == -24000. and conf["cessation_energy_m_j"] == -28000.)
                    or by_id[conf["path_id"]]["finite_rstar_crossings"] > 1
                    or conf["group"] == "base_grid" and index % 17 == 0)
        if not selected:
            continue
        config = Competition(**{name: conf[name] for name in Competition.__dataclass_fields__})
        old = [e for e in events if e["path_id"] == conf["path_id"] and e["kind"] == "root"]
        lower = SOURCE_WINDOW_K[0] if config.low_temperature_variant == "none" else EXTENDED_WINDOW_K[0]
        _, fine, _ = scan_path(config, lower=lower, step=step / 2)
        fine = [e for e in fine if e["kind"] == "root"]
        same_count = len(old) == len(fine)
        error = max((abs(a["lower_k"] - b["lower_k"]) for a, b in zip(old, fine)), default=0.) if same_count else np.nan
        same_types = same_count and [(e["orientation"], e["actual_exchange"]) for e in old] == [(e["orientation"], e["actual_exchange"]) for e in fine]
        rows.append(dict(path_id=conf["path_id"], coarse_step_k=step, fine_step_k=step / 2,
                         coarse_roots=len(old), fine_roots=len(fine), matching_types=same_types,
                         max_temperature_difference_k=error))
    return rows


def run(output, raw_output, *, step=.1):
    output.mkdir(parents=True, exist_ok=True)
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    configurations, summaries, events, transitions = [], [], [], []
    selected_points = {}
    with raw_output.open("wb") as binary, gzip.GzipFile(filename="", mode="wb", fileobj=binary, mtime=0) as compressed, io.TextIOWrapper(compressed, newline="") as handle:
        writer = None
        for number, (group, cut, p0, c) in enumerate(cases()):
            path_id = f"path_{number:04d}"
            lower = SOURCE_WINDOW_K[0] if c.low_temperature_variant == "none" else EXTENDED_WINDOW_K[0]
            points, roots, changes = scan_path(c, lower=lower, step=step)
            conf = dict(path_id=path_id, group=group, k_cut=cut, lifeless_pressure_pa=p0, **asdict(c))
            configurations.append(conf)
            counts = Counter(p["winner"] for p in points)
            warm = [equilibrium(t, c, SUPPLY)["winner"] == "methanogen" for t in (20., 30.)]
            summaries.append(dict(path_id=path_id, group=group, lower_k=lower, upper_k=290.,
                                  first_winner=points[0]["winner"], last_winner=points[-1]["winner"],
                                  finite_rstar_crossings=sum(e["kind"] == "root" for e in roots),
                                  actual_winner_exchanges=sum(e["actual_exchange"] for e in roots),
                                  status_transitions=len(changes), conditional_m_wins_20_and_30=all(warm),
                                  **{f"samples_{name}": counts[name] for name in LABELS}))
            events.extend(dict(path_id=path_id, **e) for e in roots)
            transitions.extend(dict(path_id=path_id, **e) for e in changes)
            for point in points:
                row = dict(path_id=path_id, **point)
                if writer is None:
                    writer = csv.DictWriter(handle, fieldnames=list(row), lineterminator="\n")
                    writer.writeheader()
                writer.writerow(row)
            if group == "controlled" and c.cessation_energy_a_j == -24000. and c.cessation_energy_m_j == -28000.:
                selected_points[path_id] = points
    _write_csv(output / "configurations.csv", configurations)
    _write_csv(output / "path_summary.csv", summaries)
    _write_csv(output / "switch_locations.csv", events)
    _write_csv(output / "status_transitions.csv", transitions)
    _write_csv(output / "assimilation_delivery.csv", _delivery_sensitivity())
    resolution = _resolution_audit(configurations, summaries, events, step)
    _write_csv(output / "resolution_audit.csv", resolution)
    sources = [Path(__file__), Path(__file__).with_name("two_guilds.py"),
               Path(__file__).with_name("hydrogen_uptake.py"), Path(__file__).with_name("woodii1998.py"),
               BASE / "evidence/kotsyurbenko2001_table2.csv", BASE / "evidence/peters1998_chemostat.csv"]
    groups = {}
    by_id = {c["path_id"]: c for c in configurations}
    for group, variant in sorted({(c["group"], c["low_temperature_variant"]) for c in configurations}):
        subset = [r for r in summaries if r["group"] == group and by_id[r["path_id"]]["low_temperature_variant"] == variant]
        ids = {r["path_id"] for r in subset}
        event_subset = [e for e in events if e["path_id"] in ids]
        groups[f"{group}:{variant}"] = dict(paths=len(subset),
            paths_with_crossing=sum(r["finite_rstar_crossings"] > 0 for r in subset),
            paths_with_actual_exchange=sum(r["actual_winner_exchanges"] > 0 for r in subset),
            paths_with_multiple_crossings=sum(r["finite_rstar_crossings"] > 1 for r in subset),
            actual_exchange_orientations=dict(Counter(e["orientation"] for e in event_subset if e["actual_exchange"])),
            warm_condition_retained=sum(r["conditional_m_wins_20_and_30"] for r in subset),
            end_winners=dict(Counter(r["last_winner"] for r in subset)))
    manifest = dict(supply_mol_l_h=SUPPLY, atmosphere_pa=0., step_k=step,
                    source_window_k=SOURCE_WINDOW_K, extended_window_k=EXTENDED_WINDOW_K,
                    controlled_cuts="central biology;five K cuts;nine cessation-energy pairs;three positive outlets;two strains;two uptake forms;three temperature-window choices",
                    broad_grid="243 base sets;two strains;two uptake forms;fixed-energy central threshold law;p0=300Pa;source window only",
                    groups=groups, configuration_rows=len(configurations),
                    resolution_audit=dict(paths=len(resolution),
                        type_or_count_mismatches=sum(not r["matching_types"] for r in resolution),
                        max_temperature_difference_k=max(r["max_temperature_difference_k"] for r in resolution)),
                    raw_points_sha256=sha256(raw_output.read_bytes()).hexdigest(),
                    raw_points_file="local/haze/competition_switches/raw_points.csv.gz",
                    input_sha256={p.name: sha256(p.read_bytes()).hexdigest() for p in sources},
                    caveats=["Grid counts are not probabilities or a calibration.",
                             "No assertion excludes two unresolved crossings inside one sampling cell.",
                             "Low-temperature continuations are scenarios, not recovered measurements.",
                             "A guild exchange alone establishes neither climate feedback nor bistability.",
                             "Exact ties have no selected biomass partition and are not routed as zero methane."])
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    _plot_maps(output, configurations, selected_points)
    _plot_switches(output, configurations, events)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BASE / "figures/competition_switches")
    parser.add_argument("--raw", type=Path, default=BASE.parents[1] / "local/haze/competition_switches/raw_points.csv.gz")
    parser.add_argument("--step", type=float, default=.1)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.raw, step=args.step)["groups"], indent=2))


if __name__ == "__main__":
    main()
