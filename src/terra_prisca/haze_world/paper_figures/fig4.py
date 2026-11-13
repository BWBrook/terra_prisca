"""Figure 4. Arrival order decides the survivor.

(a) Global cell counts during one invasion in each direction (fixed products,
f = 0.5, tau = 3 yr). (b) Outcome of all 24 invasion runs, with the settings
whose reference mixed state is locally stable. Exports: data/fig4_*.csv.
"""

import csv

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

from . import style

DYN = style.ROOT / "models" / "haze_world" / "figures" / "dynamic_realisation"
TMAX = 40.0
DIRS = ("A_into_M", "M_into_A")
DIR_TEXT = {"A_into_M": "acetogens invade methanogens", "M_into_A": "methanogens invade acetogens"}
RESIDENT = {"A_into_M": "methanogen", "M_into_A": "acetogen"}
SURVIVOR = {"acetogen_only": "acetogen", "methanogen_only": "methanogen"}


def read(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def write(name, rows):
    style.DATA.mkdir(parents=True, exist_ok=True)
    with open(style.DATA / name, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def mixed_stability():
    """Reference mixed state (one habitat, loss 1e-3, potential 0.3): leading real part of the
    linearisation at tau = 0, 3, 30 yr, from stability_gain.csv."""
    out = {}
    for r in read(DYN / "stability_gain.csv"):
        if (r["status"] == "accepted" and r["kind"] == "mixed" and r["sigma_k"] == "0.0" and r["n_habitats"] == "1"
                and r["nominal_potential"] == "0.3" and r["loss_h"] == "0.001" and r["branch"] == "0"
                and r["two_layer"] == "False" and r["slope_multiplier"] == "1.0" and r["lifetime_yr"] == "10000.0"
                and r["chemistry"] in ("fixed", "products")):
            for tau in ("0", "3", "30"):
                out[(r["chemistry"], float(r["fraction"]), float(tau))] = float(r[f"lambda_real_tau_{tau}"])
    assert len(out) == 12, len(out)
    return out


def main():
    style.apply()
    inv = read(DYN / "invasions.csv")
    assert len(inv) == 24
    lam = mixed_stability()
    outcomes = []
    for r in inv:
        key = (r["chemistry"], float(r["fraction"]), float(r["tau_yr"]))
        l = lam[key]
        outcomes.append(dict(case_id=r["case_id"], chemistry=r["chemistry"], fraction=float(r["fraction"]),
                             tau_yr=float(r["tau_yr"]), direction=r["direction"],
                             census_endpoint=r["census_endpoint"], survivor=SURVIVOR[r["census_endpoint"]],
                             first_resident_below_one_cell_yr=float(r["first_%s_below_cell_yr" % RESIDENT[r["direction"]]]),
                             mixed_state_leading_real_part_per_yr=l, mixed_state_locally_stable=l < 0))
    n_a = sum(o["survivor"] == "acetogen" for o in outcomes if o["direction"] == "A_into_M")
    n_m = sum(o["survivor"] == "methanogen" for o in outcomes if o["direction"] == "M_into_A")
    assert (n_a, n_m) == (12, 12)
    assert all(o["first_resident_below_one_cell_yr"] > 0 for o in outcomes)
    write("fig4_outcomes.csv", outcomes)

    fig = plt.figure(figsize=(style.DOUBLE, 80 * style.MM))
    gs = GridSpec(1, 2, figure=fig, width_ratios=[1.0, 0.82], wspace=0.34, left=0.07, right=0.995, bottom=0.14, top=0.97)
    sub = gs[0, 0].subgridspec(1, 2, wspace=0.08)
    axa = [fig.add_subplot(sub[0, 0])]
    axa.append(fig.add_subplot(sub[0, 1], sharey=axa[0]))
    axb = fig.add_subplot(gs[0, 1])

    traj_rows = []
    for ax, d in zip(axa, DIRS):
        rows = read(DYN / f"transient_B3_fixed_f0.5_tau3_{d}.csv")
        rows = [r for r in rows if r["sample_kind"] == "original_1yr_sample" and float(r["time_yr"]) <= TMAX]
        t = np.array([float(r["time_yr"]) for r in rows])
        y = {"acetogen": np.array([float(r["log10_acetogen_cells"]) for r in rows]),
             "methanogen": np.array([float(r["log10_methanogen_cells"]) for r in rows])}
        t_cross = next(float(o["first_resident_below_one_cell_yr"]) for o in outcomes
                       if o["case_id"] == f"B3_fixed_f0.5_tau3_{d}")
        res = RESIDENT[d]
        for g in ("acetogen", "methanogen"):
            e = style.ENTITY[g]
            stop = t_cross if g == res else np.inf
            solid = t <= stop
            ax.plot(t[solid], y[g][solid], color=e["color"], ls="-", lw=1.2, marker=e["marker"], ms=2.6,
                    markevery=4, mfc=e["color"], mec=e["color"], zorder=4)
            if g == res:
                dash = t >= np.floor(stop)
                ax.plot(t[dash], y[g][dash], color=e["color"], alpha=0.4, ls=(0, (3, 2)), lw=1.0, zorder=3)
            for tt, v in zip(t, y[g]):
                traj_rows.append(dict(case_id=f"B3_fixed_f0.5_tau3_{d}", direction=d, guild=g, time_yr=tt,
                                      log10_cells=v, trace="physical" if tt <= stop else "mathematical_diagnostic"))
        style.one_cell_line(ax)
        ax.plot([t_cross], [0], marker="x", color=style.INK, ms=4.5, mew=0.9, zorder=6)
        ax.annotate(f"first crossing\n{t_cross:.1f} yr", (t_cross, 0), xytext=(t_cross + 5, 14), fontsize=6, color=style.INK_2,
                    arrowprops=dict(arrowstyle="-", lw=0.4, color=style.INK_2), va="center")
        mn = next(float(r[f"{res}_log10_min_cells"]) for r in inv if r["case_id"] == f"B3_fixed_f0.5_tau3_{d}")
        left = d == "A_into_M"
        ax.text(0.03 if left else 0.97, 0.42, f"continuous solution reaches\n10$^{{{mn:.0f}}}$ cells later", transform=ax.transAxes,
                fontsize=5.8, color=style.INK_2, ha="left" if left else "right", va="top")
        ax.text(0.03, 0.03, DIR_TEXT[d], transform=ax.transAxes, fontsize=6.3, color=style.INK, ha="left", va="bottom") if False else None
        ax.text(0.5, 1.0, DIR_TEXT[d], transform=ax.transAxes, fontsize=6.3, color=style.INK_2, ha="center", va="top")
        ax.set_xlim(0, TMAX)
        ax.set_xlabel("Time after invasion (yr)")
    axa[0].set_ylim(-42, 32)
    axa[0].set_ylabel("Global cell count, log$_{10}$ (cells)")
    axa[1].tick_params(labelleft=False)
    axa[1].spines["left"].set_visible(False)
    axa[1].tick_params(axis="y", left=False)
    handles = [
        Line2D([], [], color=style.ACETOGEN, marker="o", ms=2.6, lw=1.2, label="acetogens"),
        Line2D([], [], color=style.METHANOGEN, marker="s", ms=2.6, lw=1.2, label="methanogens"),
        Line2D([], [], color=style.INK_2, ls=(0, (3, 2)), alpha=0.5, lw=1.0, label="diagnostic after crossing"),
        Line2D([], [], color=style.INK_2, ls=":", lw=0.7, label="one cell"),
    ]
    axa[0].legend(handles=handles, loc="lower left", bbox_to_anchor=(0.0, 0.0), fontsize=5.8, labelspacing=0.3, handlelength=2.2)
    style.panel_label(axa[0], "a", x=-0.28, y=0.985)

    # (b) outcome grid
    settings = [(c, f, tau) for c in ("fixed", "products") for f in (0.0, 0.5) for tau in (0.0, 3.0, 30.0)]
    cols = {"A_into_M": 0, "M_into_A": 1, "mix": 2.25}
    n = len(settings)
    byk = {(o["chemistry"], o["fraction"], o["tau_yr"], o["direction"]): o for o in outcomes}
    rows_out = []
    for i, (c, f, tau) in enumerate(settings):
        y = n - 1 - i - (0.6 if c == "products" else 0)
        for d in DIRS:
            o = byk[(c, f, tau, d)]
            e = style.ENTITY[o["survivor"]]
            axb.plot(cols[d], y, marker=e["marker"], ms=5.2, color=e["color"], ls="none", mec=e["color"])
            rows_out.append(dict(setting=f"{c}, f={f:g}, tau={tau:g}", direction=d, survivor=o["survivor"], x=cols[d], y=y))
        stable = lam[(c, f, tau)] < 0
        if stable:
            axb.plot(cols["mix"], y, marker="D", ms=4.6, color=style.INK, ls="none")
        else:
            axb.plot(cols["mix"], y, marker="_", ms=5, color=style.MUTED, ls="none", mew=1.0)
        rows_out.append(dict(setting=f"{c}, f={f:g}, tau={tau:g}", direction="mixed_state_locally_stable",
                             survivor="stable" if stable else "unstable", x=cols["mix"], y=y))
    ylabels, yt = [], []
    for i, (c, f, tau) in enumerate(settings):
        yt.append(n - 1 - i - (0.6 if c == "products" else 0))
        ylabels.append(f"f = {f:g}, τ = {tau:g}")
    axb.set_yticks(yt)
    axb.set_yticklabels(ylabels, fontsize=6)
    axb.set_xticks([0, 1, 2.25])
    axb.set_xticklabels(["acetogens\ninvade", "methanogens\ninvade", "mixture\nlocally stable"], fontsize=6.3)
    axb.set_xlim(-0.55, 2.8)
    axb.set_ylabel("")
    axb.set_ylim(-0.8, n - 0.2 + 0.2)
    axb.spines["left"].set_visible(False)
    axb.tick_params(axis="y", length=0)
    axb.tick_params(axis="x", length=0)
    axb.xaxis.set_ticks_position("top")
    axb.xaxis.set_label_position("top")
    for c, ytxt in (("fixed products", 11.55), ("products from both", 5.15)):
        pass
    axb.text(-0.55, n - 0.15, "", fontsize=1)
    axb.spines["bottom"].set_visible(False)
    axb.text(-0.30, 0.75, "fixed products", transform=axb.transAxes, fontsize=6.3, color=style.INK, ha="center", va="center", rotation=90)
    axb.text(-0.30, 0.25, "feedback from both products", transform=axb.transAxes, fontsize=6.3, color=style.INK, ha="center", va="center", rotation=90)
    axb.axhline(5.7 - 0.2, color=style.GRID, lw=0.6, xmin=0, xmax=1)
    axb.text(0.5, -0.75, "12/12 acetogen-only   |   12/12 methanogen-only", fontsize=6, color=style.INK_2, ha="center", va="top", transform=axb.transData) if False else None
    hb = [
        Line2D([], [], marker="o", color=style.ACETOGEN, ls="none", ms=5, label="acetogen only"),
        Line2D([], [], marker="s", color=style.METHANOGEN, ls="none", ms=5, label="methanogen only"),
        Line2D([], [], marker="D", color=style.INK, ls="none", ms=4.6, label="mixture stable"),
        Line2D([], [], marker="_", color=style.MUTED, ls="none", ms=5, mew=1.0, label="mixture unstable"),
    ]
    axb.legend(handles=hb, loc="upper center", bbox_to_anchor=(0.42, -0.04), ncol=2, fontsize=6, columnspacing=1.0, handletextpad=0.3)
    style.panel_label(axb, "b", x=-0.34, y=1.1)
    write("fig4_trajectories.csv", traj_rows)
    write("fig4_grid.csv", rows_out)
    stable_n = sum(lam[(c, f, tau)] < 0 for c, f, tau in settings)
    write("fig4_checks.csv", [dict(quantity="acetogen_invasions_ending_acetogen_only", reproduced=n_a, expected=12),
                              dict(quantity="methanogen_invasions_ending_methanogen_only", reproduced=n_m, expected=12),
                              dict(quantity="settings_with_locally_stable_mixture", reproduced=stable_n, expected="recorded, no prior count")])
    return style.save(fig, "fig4")


if __name__ == "__main__":
    print(main())
