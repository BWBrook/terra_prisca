"""Figure 2: perfect control breaks down when the climate responds slowly.

    uv run python -m terra_prisca.haze_world.paper_figures fig2
    uv run python -m terra_prisca.haze_world.paper_figures.fig2 --refresh

Fixed products, f = 0, reference state (loss 1e-3 per h, supply 0.30).
(a, b) kicked trajectories (0.1% acetogen kick) at tau = 1 and 10 yr; (c) leading
real part of the eigenvalues against tau for the exact reference state and one
graded state (dial D2, d = 1e-4 per yr, sigma = 0.03 K).

The default run replots the CSVs in models/haze_world/paper/figures/data/
(fig2_trajectories.csv, fig2_spectra.csv, fig2_checks.csv). --refresh
regenerates them: the two 30,000-year B2 runs with
dynamic_transients.integrate (about 2 min, one process) and the spectra (about
15 s). The graded state is read from figures/graded_dials/states.json.
Traces stop at the first crossing below one cell. Panels (a, b) show 0-2,000 yr
and 28,000-30,000 yr of the 30,000-yr runs.
"""

import csv
import json
import sys
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import eigvals
from scipy.optimize import brentq

from terra_prisca.haze_world import dynamic_core as dc
from terra_prisca.haze_world import dynamic_realisation as dr
from terra_prisca.haze_world import dynamic_transients as dt

from . import style
from .fig1 import write_csv

ROOT = style.ROOT
FIG_DIR = ROOT / "models/haze_world/figures"
TAUS = (1.0, 10.0)
WINDOWS = ((0.0, 2000.0), (28000.0, 30000.0))
GRADED = ("D2_d0.0001", 0.03)


def trajectory(tau):
    case = next(c for c in dt.design() if c.case_id == f"B2_f0_tau{tau:g}")
    y0, t0 = dt.initial(case)
    start = perf_counter()
    result = dt.integrate(y0, dt.parameters(case), case.years, case.tau_yr, t0)
    wall = perf_counter() - start
    conversion = result["global_log_cell_conversion"]
    t, temperature = result["t"], result["temperature_k"]
    logs = (result["log_biomass"] + conversion) / np.log(10.0)
    crossing = [c for c in result["first_below_cell_yr"] if c is not None]
    stop = min(crossing) if crossing else None
    rows = []
    for j, time in enumerate(t):
        if stop is not None and time > stop:
            break
        if stop is None and not any(a <= time <= b for a, b in WINDOWS):
            continue
        if stop is not None and not WINDOWS[0][0] <= time <= WINDOWS[0][1]:
            continue
        rows.append(dict(tau_yr=tau, time_yr=float(time), temperature_k=float(temperature[j]),
                         log10_acetogen_cells=float(logs[0, j]), log10_methanogen_cells=float(logs[1, j])))
    if stop is not None:
        k = max(i for i, r in enumerate(rows) if r["time_yr"] <= stop)
        a, b = rows[k], rows[k + 1] if k + 1 < len(rows) else None
        last = rows[-1]
        i_stop = int(np.argmax(t > stop))
        w = (stop - t[i_stop - 1]) / (t[i_stop] - t[i_stop - 1])
        rows.append(dict(tau_yr=tau, time_yr=float(stop),
                         temperature_k=float((1 - w) * temperature[i_stop - 1] + w * temperature[i_stop]),
                         log10_acetogen_cells=float((1 - w) * logs[0, i_stop - 1] + w * logs[0, i_stop]),
                         log10_methanogen_cells=float((1 - w) * logs[1, i_stop - 1] + w * logs[1, i_stop])))
    late = t >= 0.8 * t[-1]
    summary = dict(
        tau_yr=tau, wall_seconds=wall, first_acetogen_below_cell_yr=result["first_below_cell_yr"][0],
        first_methanogen_below_cell_yr=result["first_below_cell_yr"][1],
        acetogen_log10_min_cells=float((result["min_log_biomass"][0] + conversion) / np.log(10.0)),
        methanogen_log10_min_cells=float((result["min_log_biomass"][1] + conversion) / np.log(10.0)),
        final_window_temperature_span_k=float(np.ptp(temperature[late])),
        peak_temperature_k=result["temperature_range_k"][1], minimum_temperature_k=result["temperature_range_k"][0])
    return rows, summary


def archived_summary(tau):
    manifest = json.loads((FIG_DIR / "dynamic_realisation/transient_manifest.json").read_text())
    return next(r for r in manifest["rows"] if r["case_id"] == f"B2_f0_tau{tau:g}")


def leading(matrix):
    return float(eigvals(matrix, check_finite=True).real.max())


def spectra():
    from terra_prisca.haze_world import continuum_core as weighted
    from terra_prisca.haze_world import graded_dials as gd

    p = dr.parameters("fixed", 0.0, 0.001, 0.30)
    exact = next(e for e in dc.equilibrium_states(p) if e["kind"] == "mixed" and e["status"] == "accepted")
    build = dr.thermal_builder(exact["y"], p)
    states = json.loads((FIG_DIR / "graded_dials/states.json").read_text())
    record = next(r for r in states if r["branch_id"] == GRADED[0] and r["dial"] == GRADED[1])
    p2, y2 = gd.reconstruct(record), np.asarray(record["y"])
    blocks = gd.blocks(y2, p2, "D2")

    def graded(tau):
        scale = weighted.operator_scales(y2, p2, blocks, tau)
        return leading(weighted.dense_matrix(y2, p2, tau, blocks=blocks) * scale[None, :] / scale[:, None])

    series = {"exact": lambda tau: leading(build(tau)), "graded": graded}
    grid = np.unique(np.r_[np.geomspace(1e-3, 1e4, 281), 0.1492, 38.5])
    rows, firsts = [], {}
    for name, function in series.items():
        values = [function(float(t)) for t in grid]
        for t, v in zip(grid, values):
            rows.append(dict(state=name, tau_yr=float(t), leading_real_yr=v))
        flips = [i for i in range(len(grid) - 1) if values[i] < 0 <= values[i + 1]]
        first = flips[0]
        firsts[name] = brentq(function, grid[first], grid[first + 1], xtol=1e-10)
    for name, first in firsts.items():
        rows.append(dict(state=name + "_first_loss", tau_yr=first, leading_real_yr=0.0))
    return rows, firsts, record["lag"]["tau_c"], exact["t_k"]


def refresh():
    rows, summaries = [], []
    for tau in TAUS:
        r, s = trajectory(tau)
        rows += r
        summaries.append(s)
    write_csv("fig2_trajectories.csv", rows)
    s_rows, firsts, recorded, _ = spectra()
    write_csv("fig2_spectra.csv", s_rows)
    checks = []
    for s in summaries:
        arch = archived_summary(s["tau_yr"])
        for key in ("first_acetogen_below_cell_yr", "first_methanogen_below_cell_yr",
                    "acetogen_log10_min_cells", "methanogen_log10_min_cells",
                    "final_window_temperature_span_k", "peak_temperature_k", "minimum_temperature_k"):
            checks.append(dict(quantity=f"tau{s['tau_yr']:g}_{key}", regenerated=s[key], archived=arch[key]))
        checks.append(dict(quantity=f"tau{s['tau_yr']:g}_wall_seconds", regenerated=s["wall_seconds"], archived=""))
    checks.append(dict(quantity="exact_first_loss_tau_yr", regenerated=firsts["exact"], archived=0.14921426039312066))
    checks.append(dict(quantity="graded_first_loss_tau_yr", regenerated=firsts["graded"], archived=recorded))
    write_csv("fig2_checks.csv", checks)


def read(name):
    with (style.DATA / name).open() as handle:
        return [{k: (float(v) if v not in ("", "None") else None) if k != "state" and k != "quantity" else v
                 for k, v in row.items()} for row in csv.DictReader(handle)]


def break_marks(left, right):
    kw = dict(color=style.INK_2, lw=0.6, clip_on=False, transform=None)
    d = 0.02
    for ax, x in ((left, 1.0), (right, 0.0)):
        for y in (0.0,):
            ax.plot([x - 0.025, x + 0.025], [y - 0.03, y + 0.03], transform=ax.transAxes, color=style.INK_2,
                    lw=0.6, clip_on=False)


def main(do_refresh=False):
    style.apply()
    if do_refresh or not (style.DATA / "fig2_trajectories.csv").exists():
        refresh()
    traj = read("fig2_trajectories.csv")
    spec = read("fig2_spectra.csv")
    by_tau = {tau: [r for r in traj if r["tau_yr"] == tau] for tau in TAUS}

    fig = plt.figure(figsize=(style.DOUBLE, 3.3))
    outer = fig.add_gridspec(1, 2, width_ratios=[2.0, 1.0], wspace=0.26, left=0.075, right=0.985,
                             top=0.97, bottom=0.14)
    left = outer[0].subgridspec(2, 2, wspace=0.05, hspace=0.14)
    a1 = fig.add_subplot(left[0, 0])
    a2 = fig.add_subplot(left[0, 1], sharey=a1)
    b1 = fig.add_subplot(left[1, 0], sharex=a1)
    b2 = fig.add_subplot(left[1, 1], sharex=a2, sharey=b1)
    c = fig.add_subplot(outer[1])

    ink_styles = {1.0: dict(color=style.INK, lw=0.7, ls="-"), 10.0: dict(color=style.INK, lw=1.2, ls=(0, (4, 1.5)))}
    width = {1.0: 0.8, 10.0: 1.5}
    for tau in TAUS:
        rows = by_tau[tau]
        t = np.array([r["time_yr"] for r in rows])
        for ax_t, ax_n, (lo, hi) in ((a1, b1, WINDOWS[0]), (a2, b2, WINDOWS[1])):
            m = (t >= lo) & (t <= hi)
            if not m.any():
                continue
            ax_t.plot(t[m], [r["temperature_k"] for r, k in zip(rows, m) if k], **ink_styles[tau])
            for key, ent in (("log10_acetogen_cells", "acetogen"), ("log10_methanogen_cells", "methanogen")):
                ax_n.plot(t[m], [r[key] for r, k in zip(rows, m) if k], color=style.ENTITY[ent]["color"],
                          ls=style.ENTITY[ent]["linestyle"], lw=width[tau])
    stop = by_tau[10.0][-1]
    a1.plot([stop["time_yr"]], [stop["temperature_k"]], marker="x", color=style.INK, ms=3.5, mew=0.9, zorder=5)
    b1.plot([stop["time_yr"]], [stop["log10_acetogen_cells"]], marker="x", color=style.INK, ms=3.5, mew=0.9,
            zorder=5)
    style.one_cell_line(b1)
    style.one_cell_line(b2)

    a1.set_xlim(*WINDOWS[0])
    a2.set_xlim(*WINDOWS[1])
    a1.set_ylim(280.6, 283.2)
    b1.set_ylim(-2, 29)
    for ax in (a2, b2):
        ax.spines["left"].set_visible(False)
        ax.tick_params(left=False, labelleft=False)
    for ax in (a1, a2):
        ax.tick_params(labelbottom=False)
    a1.set_xticks([0, 500, 1000, 1500])
    a2.set_xticks([28000, 29000, 30000])
    a2.set_xticklabels(["28000", "29000", "30000"])
    a1.set_ylabel("Surface temperature (K)")
    b1.set_ylabel("Cells, $\\log_{10}$ (global count)")
    fig.text(0.075 + (0.985 - 0.075) * 0.44 * 0.5 + 0.02, 0.01, "Time (yr)", ha="center", va="bottom", fontsize=7.5)
    for ax in (a1, a2, b1, b2):
        pass
    style.panel_label(a1, "a", x=-0.2)
    style.panel_label(b1, "b", x=-0.2)
    a1.text(1.0, 0.05, "", transform=a1.transAxes)

    a1.annotate("first cell lost\nat %.0f yr" % stop["time_yr"], (stop["time_yr"], stop["temperature_k"]),
                xytext=(1100, 283.15), fontsize=6.5, ha="center", va="top", color=style.INK,
                arrowprops=dict(arrowstyle="-", lw=0.5, color=style.INK_2, shrinkA=1, shrinkB=2))
    a1.plot([], [], **ink_styles[1.0], label="$\\tau$ = 1 yr")
    a1.plot([], [], **ink_styles[10.0], label="$\\tau$ = 10 yr")
    a1.legend(loc="upper left", handlelength=2.6, borderaxespad=0.1)
    b1.plot([], [], color=style.ACETOGEN, ls="-", label="Acetogens")
    b1.plot([], [], color=style.METHANOGEN, ls="--", label="Methanogens")
    b1.plot([], [], color=style.INK, lw=1.5, label="$\\tau$ = 10 yr (thick)")
    b1.plot([], [], color=style.INK, lw=0.8, label="$\\tau$ = 1 yr (thin)")
    b1.legend(loc="center left", bbox_to_anchor=(0.0, 0.5), handlelength=2.2, borderaxespad=0.1)
    b2.text(29000, 0.8, "one cell", fontsize=6, ha="center", va="bottom", color=style.INK_2)
    break_marks(a1, a2)
    break_marks(b1, b2)

    thresh = 1e-4
    for name, spec_ in (("exact", style.MECHANISM["exact"]), ("graded", style.MECHANISM["spread"])):
        rows = [r for r in spec if r["state"] == name]
        c.plot([r["tau_yr"] for r in rows], [r["leading_real_yr"] for r in rows], color=spec_["color"],
               ls="-" if name == "exact" else "--", lw=1.2)
        first = next(r for r in spec if r["state"] == name + "_first_loss")
        c.plot([first["tau_yr"]], [0], marker=spec_["marker"], color=spec_["color"], ms=5, ls="", zorder=5,
               mec="white", mew=0.5)
        c.annotate(f"{first['tau_yr']:.4g} yr", (first["tau_yr"], 0), xytext=(5, -11),
                   textcoords="offset points", fontsize=6, color=style.INK)
    c.text(1.5e-3, 1.5e-2, "exact reference", fontsize=6.5, color=style.INK, ha="left", va="center")
    c.text(60, 2.2e-4, "graded state", fontsize=6.5, color=style.MECHANISM["spread"]["color"],
           ha="left", va="center")
    c.text(1.2e-3, 3e-3, "unstable", fontsize=6, color=style.INK_2, va="center")
    c.text(1.2e-3, -3.1e-4, "stable", fontsize=6, color=style.INK_2, va="center")
    c.axhline(0, color=style.INK_2, lw=0.6)
    c.set_xscale("log")
    c.set_yscale("symlog", linthresh=thresh, linscale=0.6)
    c.set_xlim(1e-3, 1e4)
    c.set_ylim(-4.5e-4, 3e-2)
    c.set_xlabel("Climate response time $\\tau$ (yr)")
    c.set_ylabel("Leading real part of eigenvalue (yr$^{-1}$)")
    style.panel_label(c, "c", x=-0.3)
    return style.save(fig, "fig2")


if __name__ == "__main__":
    print(main("--refresh" in sys.argv))
