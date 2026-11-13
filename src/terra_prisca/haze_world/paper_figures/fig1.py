"""Figure 1: how microbes can set a planet's temperature.

    uv run python -m terra_prisca.haze_world.paper_figures fig1

Everything is recomputed from the model (about 40 s) and written to
models/haze_world/paper/figures/data/fig1_*.csv before plotting.

(a) schematic; (b) hydrogen requirement R*_i(T), equation (2.3), at the
reference settings (loss 1e-3 per h, capacity ratio 0.74, constant-shape
continuation below 277.15 K); (c) steady surface temperature against hydrogen
supply with fixed products, f = 0.5 and tau = 0, for methanogens alone and for
the two-group system (its stable state), with an inset of the Arney et al.
(2016) case B response.
"""

import csv
from dataclasses import replace

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from terra_prisca.haze_world import population_coupling as core

from . import style

T_MIN, T_MAX, T_COLD = 273.0, 303.15, 277.15
REFERENCE_POTENTIAL = 0.3
J_REFERENCE = 1e-6


def write_csv(name, rows):
    style.DATA.mkdir(parents=True, exist_ok=True)
    path = style.DATA / name
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def requirement_rows():
    biology = core.reference().biology
    grid = np.unique(np.r_[np.round(np.arange(T_MIN, T_MAX, 0.05), 2), T_COLD, T_MAX])
    rows = []
    for t in grid:
        a, m = [g.rstar(biology.loss_h) for g in core.guilds(float(t) - 273.15, biology)]
        rows.append(dict(temperature_k=float(t), rstar_acetogen_pa=a, rstar_methanogen_pa=m,
                         region="continuation" if t < T_COLD else "measured"))
    return rows, core.switch_temperatures(biology)[0]


def stable_states(p, enabled):
    q = replace(p, enabled=enabled)
    return [e for e in core.equilibrium_states(q) if e["kind"] != "lifeless" and e["stable"]]


def steady_rows():
    rows = []
    potentials = np.round(np.arange(0.10, 0.70 + 1e-9, 0.005), 4)
    for potential in potentials:
        p = core.reference(float(potential))
        supply = core.supply_h2(p) / J_REFERENCE
        for system, enabled in (("methanogens_alone", (False, True)), ("both_groups", (True, True))):
            for e in stable_states(p, enabled):
                rows.append(dict(potential=float(potential), supply_j_1e6_mol_l_h=supply, system=system,
                                 state=e["kind"], temperature_k=e["t_k"], ch4_co2_ratio=e["r"]))
    return rows


def coexistence_limits():
    """Bisect the supply range where the stable two-group state is the mixture."""
    def mixed(potential):
        return any(e["kind"] == "mixed" for e in stable_states(core.reference(potential), (True, True)))

    limits = []
    for lo, hi in ((0.20, 0.30), (0.40, 0.50)):
        rising = not mixed(lo)
        for _ in range(30):
            mid = (lo + hi) / 2
            if mixed(mid) == rising:
                hi = mid
            else:
                lo = mid
        limits.append((lo + hi) / 2)
    return limits


def inset_rows():
    q = core.reference().climate
    curve = core.response(q.case)
    grid = np.unique(np.r_[np.linspace(0, 0.30, 301), curve.ratios])
    t = core.temperature_k(grid, q)
    peak, trough = np.argmax(curve.temperatures_k), np.argmin(curve.temperatures_k)
    r_peak, r_trough = curve.ratios[peak], curve.ratios[trough]
    rows = []
    for r, temp in zip(grid, t):
        domain = "bridge" if r < curve.ratios[0] else "arney"
        rows.append(dict(ch4_co2_ratio=float(r), temperature_k=float(temp), domain=domain,
                         haze_cooling_branch=bool(r_peak <= r <= r_trough)))
    return rows, (r_peak, curve.temperatures_k[peak], r_trough, curve.temperatures_k[trough])


def box(ax, x0, y0, x1, y1, text, entity=None, fontsize=6.5):
    if entity:
        spec = style.ENTITY[entity]
        edge, ls = spec["color"], spec["linestyle"]
    else:
        edge, ls = style.INK_2, "-"
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=0.8",
                                fc="white", ec=edge, lw=1.0, ls=ls, zorder=2))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, text, ha="center", va="center", fontsize=fontsize,
            color=style.INK, zorder=3, linespacing=1.15)


def arrow(ax, start, end, color=style.INK_2, ls="-", both=False, lw=0.9, rad=0.0):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="<|-|>" if both else "-|>", mutation_scale=6,
                                 color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0, zorder=1,
                                 connectionstyle=f"arc3,rad={rad}"))


def schematic(ax):
    ax.set_xlim(-1, 100)
    ax.set_ylim(1, 43)
    ax.axis("off")
    mid, top, low = 24, 38, 9
    h = 4.2
    box(ax, 0, mid - h, 12, mid + h, "Hydrogen\nsupply")
    box(ax, 17, mid - h, 30, mid + h, "Hydrogen in\nthe habitat")
    box(ax, 15, 1.5, 32, 7.5, "Atmospheric\nH$_2$ reservoir")
    box(ax, 38, top - h, 52, top + h, "Acetogens", "acetogen")
    box(ax, 38, low - h, 52, low + h, "Methanogens", "methanogen")
    box(ax, 59, top - h, 70, top + h, "Acetate")
    box(ax, 59, low - h, 70, low + h, "Methane")
    box(ax, 76, low - h, 88, low + h, "Organic\nhaze")
    box(ax, 77, mid - h, 99, mid + h, "Surface temperature\nT")

    arrow(ax, (12, mid), (17, mid))
    arrow(ax, (23.5, mid - h), (23.5, 7.5), both=True)
    ax.text(25, 15.2, "exchange", fontsize=6, color=style.INK_2, va="center")
    arrow(ax, (30, mid + 1.5), (38, top - 1), color=style.ACETOGEN)
    arrow(ax, (30, mid - 1.5), (38, low + 1), color=style.METHANOGEN, ls="--")
    arrow(ax, (52, top), (59, top), color=style.ACETOGEN)
    arrow(ax, (52, low), (59, low), color=style.METHANOGEN, ls="--")
    arrow(ax, (70, low), (76, low))
    arrow(ax, (82, low + h), (82, mid - h))
    ax.text(83.2, 15.6, "cools", fontsize=6, color=style.INK_2, va="center")
    arrow(ax, (70, top), (84, top))
    ax.text(77, top + 2.8, "lost, 1 − f", fontsize=6, color=style.INK_2, ha="center", va="center")
    arrow(ax, (64.5, top - h), (64.5, low + h))
    ax.text(66, 31.3, "recycled\nfraction f", fontsize=6, color=style.INK_2, va="center", linespacing=1.1)
    ax.plot([77, 45], [mid, mid], color=style.INK, ls=(0, (4, 2)), lw=1.0, zorder=1)
    arrow(ax, (45, mid), (45, top - h), color=style.INK, ls=(0, (4, 2)), lw=1.0)
    arrow(ax, (45, mid), (45, low + h), color=style.INK, ls=(0, (4, 2)), lw=1.0)
    ax.text(61, 26.3, "temperature sets\nwhich group wins", fontsize=6, color=style.INK, ha="right",
            va="bottom", linespacing=1.1)
    ax.text(88.5, 31.3, "responds over\ntime τ", fontsize=6, color=style.INK_2, ha="center",
            va="center", linespacing=1.1)


def panel_b(ax, rows, t_switch):
    t = np.array([r["temperature_k"] for r in rows])
    a = np.array([r["rstar_acetogen_pa"] for r in rows])
    m = np.array([r["rstar_methanogen_pa"] for r in rows])
    ax.axvspan(T_MIN, T_COLD, color=style.GRID, zorder=0, lw=0)
    ax.text(275.1, 42, "continuation", ha="center", va="center", fontsize=6,
            color=style.INK_2, rotation=90)
    ax.plot(t, a, color=style.ACETOGEN, ls="-", label="Acetogens", zorder=3)
    ax.plot(t, m, color=style.METHANOGEN, ls="--", label="Methanogens", zorder=3)
    ax.axvline(t_switch, color=style.INK_2, lw=0.7, ls=":", zorder=1)
    ax.plot([t_switch], [np.interp(t_switch, t, a)], marker="D", color=style.INK, ms=3.5, zorder=4, ls="")
    ax.text(t_switch + 0.7, 45, f"$T^*$ = {t_switch:.2f} K", fontsize=6.5, color=style.INK,
            ha="left", va="center")
    ax.set_yscale("log")
    ax.set_xlim(T_MIN, T_MAX)
    ax.set_ylim(12, 115)
    ax.set_yticks([15, 20, 30, 50, 70, 100])
    ax.set_yticklabels(["15", "20", "30", "50", "70", "100"])
    ax.yaxis.set_minor_locator(plt.NullLocator())
    ax.set_xlabel("Temperature (K)")
    ax.set_ylabel("Hydrogen requirement $R^*$ (Pa)")
    ax.legend(loc="upper right", handlelength=2.2, borderaxespad=0.2)
    style.panel_label(ax, "b", x=-0.2)


def panel_c(ax, rows, limits, inset, inset_rows_, branch):
    both = [r for r in rows if r["system"] == "both_groups"]
    alone = [r for r in rows if r["system"] == "methanogens_alone"]
    lo, hi = [p / REFERENCE_POTENTIAL for p in limits]
    ax.axvspan(lo, hi, color=style.GRID, zorder=0, lw=0)
    ax.axvline(1.0, color=style.MUTED, lw=0.6, ls=":", zorder=1)
    x = [r["supply_j_1e6_mol_l_h"] for r in both]
    ax.plot(x, [r["temperature_k"] for r in both], color=style.INK, lw=1.5, zorder=3,
            label="Both groups")
    x = [r["supply_j_1e6_mol_l_h"] for r in alone]
    ax.plot(x, [r["temperature_k"] for r in alone], color=style.METHANOGEN, ls="--", lw=1.2, zorder=4,
            label="Methanogens alone")
    ax.axhline(inset["t_star"], color=style.INK_2, lw=0.5, ls=":", zorder=1)
    ax.text(1.27, 279.2, "coexistence", fontsize=6, color=style.INK_2, ha="center", va="center")
    ax.text(1.02, 299.3, "reference", fontsize=6, color=style.INK_2, ha="left", va="top")
    ax.text(2.28, 282.2, "$T^*$", fontsize=6.5, color=style.INK, ha="right", va="bottom")
    ax.set_xlim(0.3, 2.3)
    ax.set_ylim(270, 300)
    ax.set_xlabel("Hydrogen supply $J$ ($10^{-6}$ mol H$_2$ L$^{-1}$ h$^{-1}$)")
    ax.set_ylabel("Steady surface temperature (K)")
    ax.legend(loc="lower left", handlelength=2.2, borderaxespad=0.2, bbox_to_anchor=(0.0, 0.0))
    style.panel_label(ax, "c", x=-0.14)

    ins = ax.inset_axes([0.60, 0.57, 0.38, 0.41])
    r = np.array([q["ch4_co2_ratio"] for q in inset_rows_])
    t = np.array([q["temperature_k"] for q in inset_rows_])
    on = np.array([q["haze_cooling_branch"] for q in inset_rows_])
    ins.plot(r, t, color=style.INK_2, lw=0.8)
    ins.plot(r[on], t[on], color=style.INK, lw=2.0, solid_capstyle="butt")
    ins.plot([inset["r_mixed"]], [inset["t_star"]], marker="D", color=style.INK, ms=3, ls="", zorder=4)
    ins.plot([inset["r_alone"]], [inset["t_alone"]], marker="s", color=style.METHANOGEN, ms=3, ls="",
             zorder=4)
    ins.text(0.235, 285, "haze\ncooling", fontsize=5.5, color=style.INK, ha="left", va="center",
             linespacing=1.05)
    ins.set_xlim(0, 0.3)
    ins.set_ylim(268, 302)
    ins.set_xticks([0, 0.1, 0.2, 0.3])
    ins.set_yticks([270, 280, 290, 300])
    ins.tick_params(labelsize=5.5, length=2, pad=1.5)
    ins.set_xlabel("CH$_4$/CO$_2$ ratio $r$", fontsize=6, labelpad=1)
    ins.set_ylabel("Climate target (K)", fontsize=6, labelpad=1)
    ins.patch.set_alpha(0.0)


def main():
    style.apply()
    req, t_switch = requirement_rows()
    write_csv("fig1b_hydrogen_requirement.csv", req)
    steady = steady_rows()
    write_csv("fig1c_steady_state.csv", steady)
    limits = coexistence_limits()
    ins_rows, (r_peak, t_peak, r_trough, t_trough) = inset_rows()
    write_csv("fig1c_arney_case_b.csv", ins_rows)

    ref = [r for r in steady if abs(r["potential"] - REFERENCE_POTENTIAL) < 1e-9]
    mixed = next(r for r in ref if r["state"] == "mixed")
    alone = next(r for r in ref if r["system"] == "methanogens_alone")
    inset = dict(t_star=mixed["temperature_k"], r_mixed=mixed["ch4_co2_ratio"],
                 t_alone=alone["temperature_k"], r_alone=alone["ch4_co2_ratio"])

    t = np.array([r["temperature_k"] for r in req])
    a = np.array([r["rstar_acetogen_pa"] for r in req])
    m = np.array([r["rstar_methanogen_pa"] for r in req])
    checks = [
        ("t_star_k", t_switch, 281.53),
        ("rstar_acetogen_278k_pa", np.interp(278.0, t, a), 27.61),
        ("rstar_methanogen_278k_pa", np.interp(278.0, t, m), 47.11),
        ("rstar_acetogen_283k_pa", np.interp(283.0, t, a), 21.45),
        ("rstar_methanogen_283k_pa", np.interp(283.0, t, m), 19.57),
        ("mixed_temperature_reference_k", mixed["temperature_k"], 281.53),
        ("methanogens_alone_temperature_reference_k", alone["temperature_k"], 273.52),
        ("coexistence_start_potential", limits[0], None),
        ("coexistence_end_potential", limits[1], None),
        ("coexistence_start_supply_j_1e6", limits[0] / REFERENCE_POTENTIAL, None),
        ("coexistence_end_supply_j_1e6", limits[1] / REFERENCE_POTENTIAL, None),
        ("arney_peak_ratio", r_peak, None), ("arney_peak_k", t_peak, None),
        ("arney_trough_ratio", r_trough, None), ("arney_trough_k", t_trough, None),
    ]
    write_csv("fig1_checks.csv", [dict(quantity=k, value=v, draft_value="" if d is None else d)
                                  for k, v, d in checks])

    fig = plt.figure(figsize=(style.DOUBLE, 4.9))
    grid = fig.add_gridspec(2, 2, height_ratios=[0.72, 1.15], hspace=0.38, wspace=0.28,
                            left=0.07, right=0.99, top=0.98, bottom=0.09)
    ax_a = fig.add_subplot(grid[0, :])
    schematic(ax_a)
    ax_a.text(0.0, 1.0, "(a)", transform=ax_a.transAxes, fontsize=8, fontstyle="italic",
              ha="left", va="top")
    panel_b(fig.add_subplot(grid[1, 0]), req, t_switch)
    panel_c(fig.add_subplot(grid[1, 1]), steady, limits, inset, ins_rows, None)
    return style.save(fig, "fig1")


if __name__ == "__main__":
    print(main())
