"""Graphical abstract for the plain-language brief.

    uv run python -m terra_prisca.haze_world.paper_figures.graphical_abstract

Reads committed exports only (paper/figures/data/, the buffered-refuge
selection, the case-B climate vertices and the acetate-fate review record) and
never rewrites them. Writes graphical_abstract.{pdf,svg,png} and
graphical_abstract_checks.csv, which lists every number shown and its source,
to models/haze_world/paper/products/figures/.

(1) schematic; (2) steady temperature against supply, fig1c data; (3) critical
response time against sensitivity, exact states apart from graded ones, fig3
data; (4) bulk temperature after invasion with and without refuges, fig4 data.
"""

import csv
import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from . import style

OUT = style.ROOT / "models" / "haze_world" / "paper" / "products" / "figures"
REFUGE_SELECTION = style.ROOT / "models" / "haze_world" / "figures" / "buffered_refuges" / "selected_main.csv"
CLIMATE_VERTICES = style.ROOT / "models" / "haze_response" / "arney2016" / "figure4.csv"
ACETATE_FATE = style.ROOT / "models" / "haze_world" / "review" / "issue4_acetate_fate.json"
W, H = 170 * style.MM, 100 * style.MM
FS = 6.5
GRADED = style.THIRD
NO_REFUGE = style.MUTED
CHECKS = []


def read(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def shown(quantity, text, raw, source, selection, claim=""):
    CHECKS.append(dict(quantity=quantity, shown=text, value=raw, source=source, selection=selection, claim=claim))
    return text


def rel(path):
    return str(path.relative_to(style.ROOT))


def box(ax, x0, y0, x1, y1, text, edge=style.INK_2, ls="-"):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=2",
                                fc="white", ec=edge, lw=1.0, ls=ls, zorder=2))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, text, ha="center", va="center", fontsize=FS, color=style.INK,
            zorder=3, linespacing=1.1)


def arrow(ax, a, b, color=style.INK_2, ls="-", lw=0.9, rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=6, color=color, lw=lw, ls=ls,
                                 shrinkA=0, shrinkB=0, zorder=1, connectionstyle=f"arc3,rad={rad}"))


def panel_schematic(ax):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    lx0, lx1, rx0, rx1 = 6, 46, 54, 94
    lc, rc = (lx0 + lx1) / 2, (rx0 + rx1) / 2
    h = 5.5
    box(ax, 20, 92 - h, 80, 92 + h, "Hydrogen supply")
    box(ax, lx0, 74 - h, lx1, 74 + h, "Methanogens", style.METHANOGEN, "--")
    box(ax, rx0, 74 - h, rx1, 74 + h, "Acetogens", style.ACETOGEN)
    box(ax, lx0, 50 - h, lx1, 50 + h, "Methane")
    box(ax, rx0, 50 - h, rx1, 50 + h, "Acetate")
    box(ax, lx0, 31 - h, lx1, 31 + h, "Organic haze")
    box(ax, rx0, 31 - 7.5, rx1, 31 + 7.5, "Lasting sink:\noxidation,\nexport, burial")
    box(ax, 14, 9 - h, 86, 9 + h, "Surface temperature")
    arrow(ax, (38, 92 - h), (lc, 74 + h), color=style.METHANOGEN, ls="--")
    arrow(ax, (62, 92 - h), (rc, 74 + h), color=style.ACETOGEN)
    arrow(ax, (lc, 74 - h), (lc, 50 + h), color=style.METHANOGEN, ls="--")
    arrow(ax, (rc, 74 - h), (rc, 50 + h), color=style.ACETOGEN)
    arrow(ax, (lc, 50 - h), (lc, 31 + h))
    arrow(ax, (rc, 50 - h), (rc, 31 + 7.5))
    arrow(ax, (rx0, 50), (lx1, 50))
    ax.text(50, 61.5, "some recycled", fontsize=FS, color=style.INK_2, ha="center", va="center")
    arrow(ax, (lc, 31 - h), (lc, 9 + h))
    ax.text(lc + 2, 19.5, "cools", fontsize=FS, color=style.INK_2, ha="left", va="center")
    dash = (0, (3, 1.5))
    for x_edge, x_side, x_box in ((14, 0.6, lx0), (86, 99.4, rx1)):
        ax.plot([x_edge, x_side, x_side], [9, 9, 74], color=style.INK, ls=dash, lw=0.9, zorder=1)
        arrow(ax, (x_side, 74), (x_box, 74), color=style.INK, ls=dash)
    ax.text(0, -1.5, "Temperature tips the contest.\nNear the switch temperature T*,\non the haze-cooling branch:\n"
            "below T*, acetogens win and the\nplanet warms; above T*,\nmethanogens win and it cools",
            fontsize=FS, color=style.INK, ha="left", va="top", linespacing=1.15)


def panel_plateau(ax, steady, checks1):
    t_star = checks1["t_star_k"]
    lo, hi = checks1["coexistence_start_supply_j_1e6"], checks1["coexistence_end_supply_j_1e6"]
    ax.axvspan(lo, hi, color=style.GRID, lw=0, zorder=0)
    r_last = max(float(v["ch4_co2_ratio"]) for v in read(CLIMATE_VERTICES) if v["case"] == "B")
    assert abs(r_last - 0.2333365) < 1e-7
    both = [r for r in steady if r["system"] == "both_groups" and float(r["ch4_co2_ratio"]) <= r_last]
    alone = [r for r in steady if r["system"] == "methanogens_alone" and float(r["ch4_co2_ratio"]) <= r_last]
    ends = {k: max(float(r["supply_j_1e6_mol_l_h"]) for r in v) for k, v in (("both", both), ("alone", alone))}
    assert abs(ends["both"] - 1.85) < 1e-9 and abs(ends["alone"] - 1.05) < 1e-9, ends
    shown("lines_end_last_extracted_climate_ratio", "line ends (no number)", r_last, rel(CLIMATE_VERTICES),
          "max ch4_co2_ratio, case B; steady states above it (assumed flat 274.002 K climate) not drawn; "
          f"last drawn supply {ends['both']:.4g} (both groups), {ends['alone']:.4g} (methanogens alone)")
    peak = max(alone, key=lambda r: float(r["temperature_k"]))
    x0 = float(peak["supply_j_1e6_mol_l_h"])
    shown("supply_axis_start_haze_peak", "axis start (no number)", x0, rel(style.DATA / "fig1c_steady_state.csv"),
          "supply at the methanogens-alone temperature peak; lower supplies (assumed low-methane bridge) not drawn")
    ax.plot([float(r["supply_j_1e6_mol_l_h"]) for r in both], [float(r["temperature_k"]) for r in both],
            color=style.INK, lw=1.6, zorder=3)
    ax.plot([float(r["supply_j_1e6_mol_l_h"]) for r in alone], [float(r["temperature_k"]) for r in alone],
            color=style.METHANOGEN, ls="--", lw=1.2, zorder=4)
    ax.set_xlim(x0, 1.95)
    ax.set_ylim(270, 300)
    ax.set_xticks([1, 1.5, 2])
    ax.set_xticklabels(["1", "1.5", "2"])
    ax.set_xlabel("Hydrogen supply\n(× reference)", linespacing=1.1)
    ax.set_ylabel("Steady surface temperature (K)")
    ts = shown("T*_switch_temperature_K", f"{t_star:.2f} K", t_star, rel(style.DATA / "fig1_checks.csv"),
               "quantity == t_star_k", "C05/C06")
    ax.text(1.27, t_star + 0.8, f"both groups\nheld at T* =\n{ts}", fontsize=FS, color=style.INK,
            ha="center", va="bottom", linespacing=1.1)
    ax.text(0.86, 271.7, "methanogens\nalone", fontsize=FS, color=style.METHANOGEN, ha="left", va="center", linespacing=1.1)
    ratio = hi / lo
    assert abs(ratio - 1.99551) < 1e-5
    rt = shown("coexistence_supply_range_factor", f"{ratio:.1f}-fold", ratio, rel(style.DATA / "fig1_checks.csv"),
               "coexistence_end_supply_j_1e6 / coexistence_start_supply_j_1e6 (half acetate recycled, biomass exported)",
               "C06/C67")
    ax.text(1.2, 299.3, f"held over a\n{rt} range\nof supply", fontsize=FS, color=style.INK_2,
            ha="center", va="top", linespacing=1.1)
    return ts


def tick_text(v):
    return f"{v:g}"


def panel_margins(ax0, ax, states, branches, thresholds):
    cooling = [r for r in states if r["group"] == "exact_cooling"]
    bridge = [r for r in states if r["group"] == "exact_bridge_unstable"]
    graded = [r for r in states if r["group"] in ("graded_C0_onoff", "graded_C1_resolved")]
    assert len(cooling) == 36 and len(bridge) == 6 and len(graded) == 122
    taus = sorted(float(r["tau_c_yr"]) for r in cooling)
    assert 0.057 < taus[0] < 0.058 and 7.07 < taus[-1] < 7.09
    target = float(thresholds[0]["tau_target_yr"])
    assert all(float(t["tau_target_yr"]) == target for t in thresholds) and target == 30.0
    mids = [float(t["price_midpoint_K"]) for t in thresholds]
    assert round(min(mids), 2) == 0.07 and round(max(mids), 2) == 0.31
    censor = {float(r["tau_c_yr"]) for r in graded if r["tau_status"] == "censored_at_1e4"}
    assert censor == {1e4}
    ceiling = censor.pop()
    ymin, ymax = 0.01, 3e5

    for i, r in enumerate(sorted(cooling, key=lambda r: float(r["tau_c_yr"]))):
        x = ((i * 0.6180339887) % 1.0 - 0.5) * 0.7
        ax0.plot(x, float(r["tau_c_yr"]), marker="D", ms=2.8, mfc=style.INK, mec=style.INK, ls="none", mew=0.3)
    ax0.set_xlim(-0.6, 0.6)
    ax0.set_xticks([0])
    ax0.set_xticklabels(["exact"])
    for a in (ax0, ax):
        a.set_yscale("log")
        a.set_ylim(ymin, ymax)
        a.axhline(target, color=style.INK_2, lw=0.6, zorder=1)
    ax0.set_yticks([0.1, 1, 10, 100, 1000, 10000])
    ax0.set_yticklabels(["0.1", "1", "10", "100", "1000", "10000"])
    ax0.yaxis.set_minor_locator(plt.NullLocator())
    ax0.set_ylabel("Slowest climate response\nbefore stability is lost (yr)", linespacing=1.1)

    ax.set_xscale("log")
    ax.set_xlim(1e-4, 1000)
    ax.set_xticks([1e-3, 1e-1, 10])
    ax.set_xticklabels(["0.001", "0.1", "10"])
    ax.xaxis.set_minor_locator(plt.NullLocator())
    ax.tick_params(axis="y", which="both", left=False, labelleft=False)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Local temperature sensitivity\n(K per e-fold of supply)", linespacing=1.1)

    arrow_m = r"$\uparrow$"
    fin = [r for r in graded if r["tau_status"] == "finite_crossing"]
    cen = [r for r in graded if r["tau_status"] == "censored_at_1e4"]
    ax.plot([float(r["abs_S"]) for r in cen], [ceiling] * len(cen), ls="none", marker=arrow_m, ms=5, mec=GRADED,
            mfc=GRADED, mew=0.3, alpha=0.8, zorder=3, clip_on=False)
    ax.plot([float(r["abs_S"]) for r in fin], [float(r["tau_c_yr"]) for r in fin], ls="none", marker="^", ms=3.2,
            mfc="white", mec=GRADED, mew=0.8, zorder=4)
    for b in sorted({p["branch_id"] for p in branches}):
        seq = sorted((p for p in branches if p["branch_id"] == b), key=lambda p: float(p["abs_S"]))
        j = [p for p in seq if p["line_joined"] == "True"]
        c = [p for p in seq if p["tau_status"] == "censored_at_1e4"]
        ax.plot([float(p["abs_S"]) for p in j], [float(p["tau_c_yr"]) for p in j], color=GRADED, lw=0.9,
                marker="o", ms=1.6, zorder=5)
        ax.plot([float(p["abs_S"]) for p in c], [ceiling] * len(c), ls="none", marker=arrow_m, ms=5, mec=GRADED,
                mfc=GRADED, mew=0.3, zorder=5, clip_on=False)
    ax.plot(mids, [target] * len(mids), ls="none", marker="o", ms=4.2, mfc="none", mec=style.INK, mew=0.7, zorder=7)

    n = shown("exact_states_cooling_branch_count", str(len(cooling)), len(cooling), rel(style.DATA / "fig3_states.csv"),
              "group == exact_cooling", "C54")
    tmax = shown("exact_states_max_critical_response_yr", f"{taus[-1]:.1f} yr", taus[-1],
                 rel(style.DATA / "fig3_states.csv"), "max tau_c_yr where group == exact_cooling", "C54")
    shown("exact_states_bridge_not_shown_count", str(len(bridge)), len(bridge), rel(style.DATA / "fig3_states.csv"),
          "group == exact_bridge_unstable (named in the note below the panel, not plotted)", "C54")
    tt = shown("response_time_line_yr", f"{target:g} yr", target, rel(style.DATA / "fig3_thresholds.csv"),
               "tau_target_yr (all four branches)", "C57")
    p_lo = shown("graded_price_30yr_low_K", f"{min(mids):.2f}", min(mids), rel(style.DATA / "fig3_thresholds.csv"),
                 "min price_midpoint_K over branches", "C57")
    p_hi = shown("graded_price_30yr_high_K", f"{max(mids):.2f}", max(mids), rel(style.DATA / "fig3_thresholds.csv"),
                 "max price_midpoint_K over branches", "C57")
    ceil_t = shown("search_ceiling_yr", f"{ceiling:,.0f} yr", ceiling, rel(style.DATA / "fig3_states.csv"),
                   "tau_c_yr where tau_status == censored_at_1e4", "C54")
    ax.text(1.3e-4, ymin * 1.15, f"{n} original exact states:\nall lose stability by\na {tmax.replace(' yr', '-yr')} response",
            fontsize=FS, color=style.INK, ha="left", va="bottom", linespacing=1.1)
    ax.text(1.3e-4, target * 1.2, tt, fontsize=FS, color=style.INK_2, ha="left", va="bottom")
    ax.text(0.5, target / 1.7, f"graded control\ntolerates a\n{target:g}-yr response\nat {p_lo}–{p_hi} K\nper e-fold\n(rings)",
            fontsize=FS, color=GRADED, ha="left", va="top", linespacing=1.1)
    ax.text(1.3e-4, ceiling * 1.3, f"looser control (arrows):\nstill stable at the\n{ceil_t.replace(' yr', '-yr')} search limit",
            fontsize=FS, color=GRADED, ha="left", va="bottom", linespacing=1.1)
    return n, tmax, tt, p_lo, p_hi, ceil_t, len(bridge)


def full_recycling_margins():
    d = json.load(open(ACETATE_FATE))
    taus = [r["tau_c"] for r in d["sweep"] if r["chemistry"] == "fixed" and r["f"] == 1.0]
    assert len(taus) == 5 and all(r["lag_status"] == "finite_crossing" for r in d["sweep"]
                                  if r["chemistry"] == "fixed" and r["f"] == 1.0)
    (win,) = [w for w in d["windows"] if w["f"] == 1.0 and w["biomass_recycled"] == 0.0]
    assert abs(min(taus) - 21.2725) < 1e-3 and abs(max(taus) - 30.6566) < 1e-3 and abs(win["ratio"] - 1.04682) < 1e-5
    src, sel = rel(ACETATE_FATE), "sweep, chemistry fixed, f 1.0 (biomass exported), window positions 0.05-0.95"
    lo = shown("full_recycling_exact_tau_c_min_yr", f"{min(taus):.0f}", min(taus), src, sel, "C67")
    hi = shown("full_recycling_exact_tau_c_max_yr", f"{max(taus):.0f} yr", max(taus), src, sel, "C67")
    wp = shown("full_recycling_window_width_percent", f"{100 * (win['ratio'] - 1):.0f}%", win["ratio"], src,
               "windows, f 1.0, biomass_recycled 0.0: ratio high/low supply", "C67")
    return lo, hi, wp


def panel_refuges(ax, refuge_rows, selection):
    t_star = None
    finals = {}
    for sel in selection:
        pts = [d for d in refuge_rows if d["case_id"] == sel["case_id"] and float(d["time_yr"]) > 0]
        t = np.array([float(d["time_yr"]) for d in pts])
        temp = np.array([float(d["bulk_temperature_k"]) for d in pts])
        invader = "acetogen" if sel["direction"] == "A_into_M" else "methanogen"
        e = style.ENTITY[invader]
        both = sel["configuration"] == "both"
        ax.plot(t, temp, color=e["color"] if both else NO_REFUGE, ls="-" if both else e["linestyle"],
                lw=1.3 if both else 1.0, zorder=4 if both else 3)
        ax.plot(t[-1], temp[-1], marker=e["marker"], ms=3.6, color=e["color"] if both else NO_REFUGE, ls="none",
                zorder=5, clip_on=False)
        finals[(sel["configuration"], sel["direction"])] = (temp[-1], t[-1])
    t_both = [finals[("both", d)][0] for d in ("A_into_M", "M_into_A")]
    assert all(abs(v - 281.534823) < 1e-5 for v in t_both)
    assert abs(finals[("none", "A_into_M")][0] - 294.40263) < 1e-4
    assert abs(finals[("none", "M_into_A")][0] - 273.516845) < 1e-4
    t_end = finals[("both", "A_into_M")][1]
    src = rel(style.DATA / "fig4_refuges.csv")
    hot = shown("no_refuge_acetogens_invade_final_K", f"{finals[('none', 'A_into_M')][0]:.1f} K",
                finals[("none", "A_into_M")][0], src,
                "last row, configuration none, direction A_into_M (matched no-refuge control)", "C09")
    cold = shown("no_refuge_methanogens_invade_final_K", f"{finals[('none', 'M_into_A')][0]:.1f} K",
                 finals[("none", "M_into_A")][0], src,
                 "last row, configuration none, direction M_into_A (matched no-refuge control)", "C09")
    shown("refuge_both_final_K", "T* (no number)", float(np.mean(t_both)), src,
          "last rows, configuration both, both directions", "C09")
    both_sel = [s for s in selection if s["configuration"] == "both"]
    area = {float(s["refuge_fraction"]) for s in both_sel}
    cold_k = {float(s["cold_k"]) for s in both_sel}
    warm_k = {float(s["warm_k"]) for s in both_sel}
    assert len(area) == len(cold_k) == len(warm_k) == 1
    a, ck, wk = area.pop(), cold_k.pop(), warm_k.pop()
    srel = rel(REFUGE_SELECTION)
    at = shown("refuge_area_percent_each", f"{100 * a:g}%", a, srel, "refuge_fraction, configuration both", "C09")
    ct = shown("refuge_cold_K", f"{ck:g}", ck, srel, "cold_k, configuration both", "C09")
    wt = shown("refuge_warm_K", f"{wk:g} K", wk, srel, "warm_k, configuration both", "C09")
    ax.axhline(t_both[0], color=style.INK_2, ls=":", lw=0.7, zorder=1)
    ax.set_xscale("log")
    ax.set_xlim(100, t_end)
    ax.set_xticks([100, 1000, 10000, 100000])
    ax.set_xticklabels(["100", "1000", "10,000", "100,000"])
    ax.xaxis.set_minor_locator(plt.NullLocator())
    ax.set_ylim(266, 300)
    ax.set_xlabel("Years after invasion")
    ax.set_ylabel("Surface temperature (K)")
    ax.text(t_end, 292.8, f"no refuge:\nacetogens\nalone,\n{hot}", fontsize=FS,
            color=style.INK_2, ha="right", va="top", linespacing=1.1)
    ax.text(t_end, 272.3, f"no refuge:\nmethanogens\nalone, {cold}", fontsize=FS,
            color=style.INK_2, ha="right", va="top", linespacing=1.1)
    ax.text(120, 299.8, "methanogens invade", fontsize=FS, color=style.METHANOGEN, ha="left", va="top")
    ax.text(120, 272.6, "acetogens\ninvade", fontsize=FS, color=style.ACETOGEN, ha="left", va="top",
            linespacing=1.1)
    ax.text(120, 289.5, "refuges:\nboth groups\nreach T*", fontsize=FS, color=style.INK,
            ha="left", va="top", linespacing=1.1)
    return at, ct, wt


def main():
    style.apply()
    CHECKS.clear()
    checks1 = {r["quantity"]: float(r["value"]) for r in read(style.DATA / "fig1_checks.csv")}
    assert abs(checks1["t_star_k"] - 281.53482) < 1e-4
    steady = read(style.DATA / "fig1c_steady_state.csv")
    mixed = [float(r["temperature_k"]) for r in steady if r["state"] == "mixed"]
    assert mixed and max(abs(t - checks1["t_star_k"]) for t in mixed) < 1e-6
    states = read(style.DATA / "fig3_states.csv")
    branches = read(style.DATA / "fig3_branches.csv")
    thresholds = read(style.DATA / "fig3_thresholds.csv")
    refuges = read(style.DATA / "fig4_refuges.csv")
    selection = sorted((r for r in read(REFUGE_SELECTION) if r["fraction"] == "0.5" and r["dispersal_yr"] == "1e-06"
                        and r["configuration"] in ("both", "none")), key=lambda r: (r["configuration"], r["direction"]))
    assert len(selection) == 4 and {r["case_id"] for r in selection} == {r["case_id"] for r in refuges}

    fig = plt.figure(figsize=(W, H))
    headline = "Competing microbes can hold a hazy planet's temperature, but exact control is fragile to a slow climate"
    fig.text(0.006, 0.985, headline, fontsize=9.5, fontweight="bold", color=style.INK, ha="left", va="top")
    fig.text(0.006, 0.928, "All results are in the model",
             fontsize=FS, color=style.INK_2, ha="left", va="top")
    top, bottom = 0.765, 0.26
    ax1 = fig.add_axes([0.004, 0.20, 0.226, top - 0.20])
    ax2 = fig.add_axes([0.29, bottom, 0.14, top - bottom])
    ax3s = fig.add_axes([0.512, bottom, 0.02, top - bottom])
    ax3 = fig.add_axes([0.552, bottom, 0.183, top - bottom])
    ax4 = fig.add_axes([0.80, bottom, 0.172, top - bottom])

    panel_schematic(ax1)
    panel_plateau(ax2, steady, checks1)
    n_bridge = panel_margins(ax3s, ax3, states, branches, thresholds)[-1]
    at, ct, wt = panel_refuges(ax4, refuges, selection)

    ty = 0.86
    for x, text in ((0.006, "1  How it works"), (0.245, "2  Exact control"),
                    (0.452, "3  Exact is fragile,\n    graded lasts"), (0.745, "4  Two refuges let both\n    groups persist")):
        fig.text(x, ty, text, fontsize=7.5, fontweight="bold", color=style.INK, ha="left", va="top", linespacing=1.1)
    fig.text(0.245, 0.012, "Lines stop where methane\nleaves the extracted climate\ncurve; beyond it the climate\n"
             "is assumed flat.", fontsize=FS, color=style.INK_2, ha="left", va="bottom", linespacing=1.1)
    f_lo, f_hi, f_win = full_recycling_margins()
    fig.text(0.452, 0.012, f"Not shown: {n_bridge} exact states unstable even\nwith an instant climate response. With all\n"
             f"acetate recycled and biomass exported, exact\nstates in a {f_win} window at lower supply\ntolerate a "
             f"{f_lo}–{f_hi.replace(' yr', '-yr')} response.",
             fontsize=FS, color=style.INK_2, ha="left", va="bottom", linespacing=1.1)
    shown("other_route_immigration", "named (no number)", "", "models/haze_world/synthesis/claims.csv",
          "immigration assembles a material mixture near T* at f = 0 and 0.5", "C66")
    fig.text(0.745, 0.012, f"Refuges: two habitats, {at} of area each,\nheld at {ct} and {wt}; instant thermal\n"
             "response. Without refuges the invader\nends alone (grey). Refuges keep the\n"
             "losing group alive while methane\nadjusts. Immigration is another route.", fontsize=FS, color=style.INK_2,
             ha="left", va="bottom", linespacing=1.1)
    return save(fig)


def save(fig):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "graphical_abstract.pdf", metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(OUT / "graphical_abstract.svg", metadata={"Date": None})
    fig.savefig(OUT / "graphical_abstract.png", dpi=300)
    plt.close(fig)
    with open(OUT / "graphical_abstract_checks.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(CHECKS[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(CHECKS)
    return OUT / "graphical_abstract.pdf"


if __name__ == "__main__":
    print(main())
