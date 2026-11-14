"""Figure 3. Durability costs a little precision.

(a) Critical response time against local sensitivity: exact states (strip),
on/off and resolved-habitat graded states, and the four dial branches.
(b) Finite responses of temperature to supply for habitat spreads of 0-8 K
(weak mixing, f = 0.5), from the Issue 1 pressure-test branches.
Sources are archived outputs only; every plotted number is exported to
models/haze_world/paper/figures/data/fig3_*.csv.
"""

import csv
import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

from . import style

FIG = style.ROOT / "models" / "haze_world" / "figures"
CENSOR = 1e4
TAU_STAR = 30.0
YMIN, YMAX = 0.02, 9e4
BRIDGE_Y = 0.026

BRANCHES = {
    "D1_f0": dict(label="acetate dial, f = 0", color=style.ACETOGEN, marker="o", ls="-"),
    "D1_f0.5": dict(label="acetate dial, f = 0.5", color=style.ACETOGEN, marker="o", ls=(0, (4, 2))),
    "D2_d0.0001": dict(label="habitat spread, d = 10$^{-4}$ yr$^{-1}$", color=style.THIRD, marker="^", ls="-"),
    "D2_d0.001": dict(label="habitat spread, d = 10$^{-3}$ yr$^{-1}$", color=style.THIRD, marker="^", ls=(0, (4, 2))),
}


def read(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def write(name, rows):
    style.DATA.mkdir(parents=True, exist_ok=True)
    with open(style.DATA / name, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def tau_of(r):
    s = r["critical_lag_status"]
    if s == "finite_crossing":
        return float(r["critical_lag_yr"]), "finite_crossing"
    if s.startswith("not_detected"):
        return CENSOR, "censored_at_1e4"
    return 0.0, s


def load_states():
    rows = []
    for fname, stage in (("c0_local_gain.csv", "C0"), ("c1_resolved.csv", "C1")):
        for r in read(FIG / "continuum_habitats" / fname):
            if r["gain_status"] != "defined":
                continue
            tau, status = tau_of(r)
            rows.append(dict(
                stage=stage, chemistry=r["chemistry"], fraction=float(r["fraction"]),
                loss_h=r.get("loss_h") or "", nominal_potential=float(r["nominal_potential"]),
                sigma_k=float(r["sigma_k"]), dispersal_yr=r.get("dispersal_yr") or "",
                Sc=float(r["Sc"]), S0=float(r["S0"]), abs_S=abs(float(r["Sc"])),
                tau_status=status, tau_c_yr=tau))
    return rows


def classify(rows):
    exact = [r for r in rows if r["abs_S"] < 1e-6]
    graded = [r for r in rows if r["abs_S"] >= 1e-6]
    excluded = [r for r in graded if r["S0"] > 0]
    ordinary = [r for r in graded if r["S0"] < 0]
    for r in exact:
        r["group"] = "exact_cooling" if r["tau_status"] == "finite_crossing" else "exact_bridge_unstable"
    for r in ordinary:
        r["group"] = "graded_C0_onoff" if r["stage"] == "C0" else "graded_C1_resolved"
    for r in excluded:
        r["group"] = "excluded_bridge_S0_positive"
    return exact, ordinary, excluded


def load_branches():
    pts = {}
    for fname, kind in (("dials.csv", "grid"), ("threshold_refinement/dials.csv", "refinement")):
        for r in read(FIG / "graded_dials" / fname):
            if abs(float(r["Sc"])) < 1e-6:
                continue
            tau, status = tau_of(r)
            pts.setdefault(r["branch_id"], []).append(dict(
                branch_id=r["branch_id"], source=kind, dial=float(r["dial"]),
                temperature_k=float(r["temperature_k"]), Sc=float(r["Sc"]),
                abs_S=abs(float(r["Sc"])), tau_status=status, tau_c_yr=tau))
    out = []
    for b in BRANCHES:
        seq = sorted(pts[b], key=lambda p: p["dial"])
        out.extend(seq)
    return out


def main():
    style.apply()
    states = load_states()
    exact, ordinary, excluded = classify(states)
    cooling = [r for r in exact if r["group"] == "exact_cooling"]
    bridge = [r for r in exact if r["group"] == "exact_bridge_unstable"]
    cens = [r for r in ordinary if r["tau_status"] == "censored_at_1e4"]
    c1_fin = [r for r in ordinary if r["group"] == "graded_C1_resolved" and r["tau_status"] == "finite_crossing"]
    checks = dict(
        exact_states=(len(exact), 42), exact_cooling=(len(cooling), 36), exact_bridge=(len(bridge), 6),
        graded_ordinary=(len(ordinary), 122), graded_censored=(len(cens), 113),
        graded_finite_C1=(len(c1_fin), 9), excluded_bridge=(len(excluded), 6))
    for k, (got, want) in checks.items():
        assert got == want, (k, got, want)
    assert min(r["abs_S"] for r in ordinary) > 0.589 and min(r["abs_S"] for r in ordinary) < 0.590
    assert 331 < min(r["tau_c_yr"] for r in ordinary) < 332
    assert 0.057 < min(r["tau_c_yr"] for r in cooling) < 0.058
    assert 7.07 < max(r["tau_c_yr"] for r in cooling) < 7.09

    branches = load_branches()
    thr = {b["branch_id"]: b for b in json.load(open(FIG / "graded_dials" / "threshold_refinement" / "thresholds.json"))["branches"]}
    brackets = {"D1_f0": (0.2776, 0.2788), "D1_f0.5": (0.3142, 0.3155), "D2_d0.0001": (0.0702, 0.0714), "D2_d0.001": (0.1619, 0.1635)}
    for b, (lo, hi) in brackets.items():
        assert round(thr[b]["price_low"], 4) == lo and round(thr[b]["price_high"], 4) == hi, b

    fig = plt.figure(figsize=(style.DOUBLE, 82 * style.MM))
    gs = GridSpec(1, 2, figure=fig, width_ratios=[0.1, 0.9], wspace=0.0,
                  left=0.075, right=0.65, bottom=0.14, top=0.97)
    gs_b = GridSpec(1, 1, figure=fig, left=0.735, right=0.995, bottom=0.14, top=0.97)
    ax0 = fig.add_subplot(gs[0, 0])
    ax = fig.add_subplot(gs[0, 1], sharey=ax0)
    axb = fig.add_subplot(gs_b[0, 0])

    # strip: exact states
    rng_x = lambda i: ((i * 0.6180339887) % 1.0 - 0.5) * 0.7
    ordered = sorted(cooling, key=lambda r: r["tau_c_yr"])
    strip_rows = []
    for i, r in enumerate(ordered):
        x = rng_x(i)
        r["x_plotted"] = x
        ax0.plot(x, r["tau_c_yr"], marker="D", ms=3.2, mfc=style.INK, mec=style.INK, ls="none", mew=0.4)
    for i, r in enumerate(bridge):
        x = rng_x(i + 40)
        r["x_plotted"] = x
        ax0.plot(x, BRIDGE_Y, marker="D", ms=3.2, mfc="white", mec=style.INK, ls="none", mew=0.8, clip_on=False, zorder=5)
    ax0.set_xlim(-0.6, 0.6)
    ax0.set_xticks([0])
    ax0.set_xticklabels(["0"])
    ax0.set_xlabel("$S$ = 0", labelpad=2)
    ax0.set_yscale("log")
    ax0.set_ylim(YMIN, YMAX)
    ax0.set_ylabel("Critical response time $\\tau_c$ (yr)")
    ax0.spines["right"].set_visible(False)
    ax0.axhline(TAU_STAR, color=style.INK_2, lw=0.6)
    # main: price band and 30-yr line
    ax.set_xscale("log")
    lo = min(v[0] for v in brackets.values())
    hi = max(v[1] for v in brackets.values())
    ax.axvspan(lo, hi, color=style.GRID, zorder=0, lw=0)
    ax.axhline(TAU_STAR, color=style.INK_2, lw=0.6, zorder=1)
    ax.axhline(CENSOR, color=style.GRID, lw=0.6, zorder=0)
    ax.text(2.2e-4, TAU_STAR * 1.15, "30 yr", fontsize=6.5, color=style.INK_2, va="bottom")
    ax.text(np.sqrt(lo * hi), 6e4, "price of 30 yr: 0.07–0.32 K per e-fold", fontsize=6, color=style.INK_2,
            ha="center", va="center", zorder=6)
    ax.text(2.2e-4, CENSOR * 1.25, "10$^4$ yr ceiling:\narrows = lower bounds", fontsize=6, color=style.INK_2, va="bottom")

    arrow = r"$\uparrow$"
    for grp, col in (("graded_C0_onoff", style.MECHANISM["onoff"]["color"]), ("graded_C1_resolved", style.THIRD)):
        sel = [r for r in ordinary if r["group"] == grp]
        c = [r for r in sel if r["tau_status"] == "censored_at_1e4"]
        f = [r for r in sel if r["tau_status"] == "finite_crossing"]
        colour = "#8a8883" if grp == "graded_C0_onoff" else style.THIRD
        ax.plot([r["abs_S"] for r in c], [CENSOR] * len(c), ls="none", marker=arrow, ms=5.5, mec=colour, mfc=colour, mew=0.3, alpha=0.85, zorder=3)
        ax.plot([r["abs_S"] for r in f], [r["tau_c_yr"] for r in f], ls="none", marker="^", ms=4.2, mfc="white", mec=colour, mew=0.9, zorder=4)
        for r in sel:
            r["y_plotted"] = r["tau_c_yr"]

    # dial branches
    tag_pos = {"D1_f0": (0.55, 0.62), "D1_f0.5": (0.55, 1.5), "D2_d0.0001": (2.0, 0.42), "D2_d0.001": (1.2, 0.17)}
    for b, sty in BRANCHES.items():
        seq = [p for p in branches if p["branch_id"] == b]
        fin = [p for p in seq if p["tau_status"] == "finite_crossing"]
        cen = [p for p in seq if p["tau_status"] == "censored_at_1e4"]
        ax.plot([p["abs_S"] for p in fin], [p["tau_c_yr"] for p in fin], color=sty["color"], ls=sty["ls"], lw=1.0,
                marker=sty["marker"], ms=2.6, mfc=sty["color"], mec=sty["color"], zorder=5)
        ax.plot([p["abs_S"] for p in cen], [CENSOR] * len(cen), ls="none", marker=arrow, ms=6.5, mec=sty["color"],
                mfc=sty["color"], mew=0.4, zorder=5, clip_on=False)
        for p in seq:
            p["y_plotted"] = p["tau_c_yr"]
        t = thr[b]
        mid = 0.5 * (t["price_low"] + t["price_high"])
        ax.plot([mid], [TAU_STAR], marker="o", ms=5, mfc="none", mec=style.INK, mew=0.7, zorder=7)
    ax.set_xlim(2e-4, 250)
    ax.set_ylim(YMIN, YMAX)
    ax.set_xlabel("Local sensitivity $|S|$ (K per e-fold of supply)")
    ax.tick_params(labelleft=False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", which="both", left=False)
    handles = [
        Line2D([], [], marker="D", ls="none", mfc=style.INK, mec=style.INK, ms=3.2, label="exact, cooling branch (36)"),
        Line2D([], [], marker="D", ls="none", mfc="white", mec=style.INK, ms=3.2, label="exact, unstable at τ = 0 (6)"),
        Line2D([], [], marker=arrow, ls="none", mfc="#8a8883", mec="#8a8883", ms=6, label="on/off graded, lower bound (42)"),
        Line2D([], [], marker=arrow, ls="none", mfc=style.THIRD, mec=style.THIRD, ms=6, label="resolved habitats, lower bound (71)"),
        Line2D([], [], marker="^", ls="none", mfc="white", mec=style.THIRD, ms=4.2, label="resolved habitats, finite (9)"),
    ]
    leg = ax.legend(handles=handles, loc="lower right", bbox_to_anchor=(1.0, 0.02), fontsize=6, handletextpad=0.3, labelspacing=0.25, borderaxespad=0.2)
    leg.set_zorder(9)
    ax.add_artist(leg)
    lh = [Line2D([], [], color=v["color"], ls=v["ls"], marker=v["marker"], ms=2.6, lw=1.0, label=v["label"]) for v in BRANCHES.values()]
    leg2 = ax.legend(handles=lh, loc="upper left", bbox_to_anchor=(0.0, 0.80), fontsize=6, handlelength=2.6, handletextpad=0.4, labelspacing=0.25, borderaxespad=0.2)
    leg2.set_zorder(9)
    style.panel_label(ax0, "a", x=-0.9, y=0.985)

    # (b) finite responses across habitat spread
    probe = json.load(open(style.ROOT / "models" / "haze_world" / "review" / "issue1_spread_response.json"))
    meta = probe["meta"]
    p_lo, p_hi, t_star = meta["P_lo"], meta["P_hi"], meta["T_star_K"]
    assert abs(t_star - 281.5348) < 1e-3 and meta["f"] == 0.5 and meta["d_per_yr"] == 1e-4
    axb.axvspan(p_lo, p_hi, color=style.GRID, lw=0, zorder=0)
    axb.axhline(t_star, color=style.INK_2, lw=0.5, ls=":", zorder=1)
    ramp = {0.0: style.INK, 1.0: "#8fd3b8", 3.0: "#4cbd92", 6.0: style.THIRD, 8.0: "#0d6b48"}
    fin = []
    for sg, col in ramp.items():
        kind = "hom" if sg == 0.0 else None
        seq = [r for r in probe["rows"] if r["status"] == "accepted" and r["sigma_K"] == sg
               and (r["direction"] == "hom" if kind else r["direction"] in ("up", "down", "ref"))]
        seq.sort(key=lambda r: r["P"])
        P = np.array([r["P"] for r in seq])
        T = np.array([r["T_K"] for r in seq])
        axb.plot(P, T, color=col, lw=1.2 if sg else 1.0, zorder=4)
        if sg:
            axb.plot(P[[0, -1]], T[[0, -1]], ls="none", marker="o", ms=2.8, mfc="white", mec=col, mew=0.8, zorder=5)
            span = float(np.interp(p_lo, P, T) - np.interp(p_hi, P, T)) if P[0] <= p_lo and P[-1] >= p_hi else None
            if sg == 1.0:
                assert abs(span - 1.91115) < 1e-4
            if sg == 3.0:
                assert abs(span - 5.40874) < 1e-4
        for r in seq:
            fin.append(dict(sigma_K=sg, P=r["P"], direction=r["direction"], T_K=r["T_K"],
                            S_K_per_efold=r.get("S_K_per_efold"), branch_end=bool(sg) and r["P"] in (P[0], P[-1])))
    lab = {0.0: ("uniform, σ = 0", 0.47, t_star + 0.3, "right"), 1.0: ("1 K", 0.468, 280.0, "left"),
           3.0: ("3 K", 0.478, 277.9, "left"), 6.0: ("6 K", 0.364, 278.3, "left"), 8.0: ("σ = 8 K", 0.222, 289.6, "left")}
    for sg, (txt, x, y, ha) in lab.items():
        axb.text(x, y, txt, fontsize=6.3, color=ramp[sg], ha=ha, va="center")
    axb.set_xscale("log")
    axb.set_xlim(0.19, 0.52)
    axb.set_xticks([0.2, 0.3, 0.4, 0.5])
    axb.set_xticklabels(["0.2", "0.3", "0.4", "0.5"])
    axb.minorticks_off()
    axb.set_ylim(272.5, 291)
    axb.set_xlabel("Hydrogen supply potential $P$")
    axb.set_ylabel("Surface temperature $T$ (K)")
    axb.text(0.5 * (p_lo + p_hi) ** 1, 290.4, "uniform coexistence", fontsize=5.8, color=style.INK_2, ha="center", va="top")
    axb.text(0.02, 0.03, "(a): 30 yr at σ = 0.02–0.06 K", transform=axb.transAxes, fontsize=5.8, color=style.INK_2, ha="left", va="bottom")
    style.panel_label(axb, "b", x=-0.25, y=0.985)

    # exports
    export_states = [r for r in states]
    for r in export_states:
        r.setdefault("group", "")
        r.setdefault("x_plotted", "")
        if "y_plotted" not in r:
            r["y_plotted"] = BRIDGE_Y if r["group"] == "exact_bridge_unstable" else r["tau_c_yr"]
        r["tau_c_yr"] = r["tau_c_yr"] if r["tau_status"] != "already_unstable" else ""
    keep = [r for r in export_states if r["group"] != "excluded_bridge_S0_positive"]
    cols_ = ["group", "stage", "chemistry", "fraction", "loss_h", "nominal_potential", "sigma_k", "dispersal_yr",
             "Sc", "S0", "abs_S", "tau_status", "tau_c_yr", "x_plotted", "y_plotted"]
    write("fig3_states.csv", [{k: r[k] for k in cols_} for r in keep])
    write("fig3_branches.csv", [dict(p, line_joined=p["tau_status"] == "finite_crossing", y_plotted=p["y_plotted"]) for p in branches])
    write("fig3_thresholds.csv", [dict(branch_id=b, price_low_K=thr[b]["price_low"], price_high_K=thr[b]["price_high"],
                                       price_midpoint_K=0.5 * (thr[b]["price_low"] + thr[b]["price_high"]),
                                       dial_low=thr[b]["low_dial"], dial_high=thr[b]["high_dial"],
                                       tau_low_yr=thr[b]["low_tau"], tau_high_yr=thr[b]["high_tau"], tau_target_yr=TAU_STAR)
                                  for b in BRANCHES])
    write("fig3_finite_responses.csv", fin)
    write("fig3_checks.csv", [dict(quantity=k, reproduced=v[0], expected=v[1]) for k, v in checks.items()] + [
        dict(quantity="graded_min_abs_S_K", reproduced=min(r["abs_S"] for r in ordinary), expected=0.59),
        dict(quantity="graded_min_tau_c_yr", reproduced=min(r["tau_c_yr"] for r in ordinary), expected=331),
        dict(quantity="exact_cooling_tau_c_min_yr", reproduced=min(r["tau_c_yr"] for r in cooling), expected=0.057),
        dict(quantity="exact_cooling_tau_c_max_yr", reproduced=max(r["tau_c_yr"] for r in cooling), expected=7.08)])
    return style.save(fig, "fig3")


if __name__ == "__main__":
    print(main())
