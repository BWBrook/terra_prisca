"""Score the GLW (2006) readings against the printed Figs 2 and 3 and the text.

    uv run python -m terra_prisca.goldblatt_lenton_watson.fidelity_glw2006 [outdir]

Reads the vector geometry in glw2006_vectors.csv (written by vectors.py from the
article PDF) and writes, to models/goldblatt_lenton_watson/fidelity/:

  glw2006_fig2.csv     each Fig. 2 curve against each reading and null, as
                       two-way RMS distances in printed points
  glw2006_folds.csv    fold positions, printed and modelled
  glw2006_fig3.csv     each Fig. 3 trace against each reading, beta and methane
                       axis convention
  glw2006_claims.csv   the stated numbers, recomputed
  glw2006_overlay.png  model curves drawn over the printed vertices

Distances are measured on the printed page: data units are converted to points
with each panel's own scale, so a score of 0.1 pt means the model line lies a
tenth of a printed point from the published one.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree

from . import glw2006 as g
from . import vectors as V

OUT = Path("models/goldblatt_lenton_watson/fidelity")

# Points per data unit, from the frames (vectors.py): Fig. 2 frames are 216.30 x
# 89.95 pt over 8 x 11 decades; Fig. 3 main frames 124.25 x 41.54 pt over
# 0.5 Gyr x 6 decades (a, c) or 12e11 mol/yr (b, d); zoom frames 43.86 pt wide over 1 Myr.
SCALE2 = (216.30 / 8, 89.95 / 11)
SCALE3 = {"a": (124.25 / 0.5, 41.545 / 6), "c": (124.25 / 0.5, 41.50 / 6),
          "b": (124.684 / 0.5, 40.276 / 12), "d": (124.684 / 0.5, 40.12 / 12),
          "a_zoom": (43.86 / 0.001, 41.545 / 6), "c_zoom": (44.77 / 0.001, 41.50 / 6),
          "b_zoom": (44.54 / 0.001, 40.51 / 12), "d_zoom": (44.54 / 0.001, 40.34 / 12)}

FIG2_CASES = {  # (panel, curve): (fixed parameter, value as captioned)
    ("a", "solid"): ("N", g.N_MODERN),
    ("a", "dashed"): ("N", g.N_MODERN / 2),
    ("b", "solid"): ("r", 7.5e10),
    ("b", "dashed"): ("r", 3e10),
}
CAPTION_R_TENFOLD = 3e11   # the value the Fig. 2b dashed curve actually fits (see README)

STEPS = {  # Fig. 3 caption: (N0, r0) -> (N1, r1) at 2.4 Gyr ago
    "a": (g.N_MODERN, 3e11, g.N_MODERN, 7.5e10),
    "c": (3.6375e15, 3e11, g.N_MODERN, 3e11),
}
T_STEP_GYR = 2.4
BETA_FIG3D = None  # filled by beta_from_fig3d()


def two_way(printed: np.ndarray, model: np.ndarray, scale) -> tuple[float, float]:
    a, b = printed * scale, model * scale
    d1 = cKDTree(b).query(a)[0]
    d2 = cKDTree(a).query(b)[0]
    return float(np.sqrt(np.mean(d1**2))), float(np.sqrt(np.mean(d2**2)))


def densify(p: np.ndarray, step: float) -> np.ndarray:
    """Insert points so no segment exceeds `step` (in the units of p)."""
    seg = np.diff(p, axis=0)
    n = np.maximum(1, np.ceil(np.hypot(seg[:, 0], seg[:, 1]) / step).astype(int))
    k = np.repeat(np.arange(len(seg)), n)
    frac = (np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n) + 1) / np.repeat(n, n)
    return np.vstack([p[:1], p[k] + seg[k] * frac[:, None]])


def printed2(vec, panel, curve, parts=("upper", "unstable", "lower")):
    return np.vstack([vec[("2", panel, curve, p)] for p in parts])


def model2(rd: g.Reading, fixed: str, value: float, panel: str, n=3001):
    O, free, stable = g.branch_curve(rd, **{fixed: value}, n=n)
    xy = np.column_stack([np.log10(free), np.log10(O / rd.pal_mol)])
    x0, x1, y0, y1 = V.FIG2[panel]
    keep = (xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] <= y0) & (xy[:, 1] >= y1)
    return xy[keep], stable[keep], O[keep]


def fig2_scores(vec) -> list[dict]:
    rows = []
    for (panel, curve), (fixed, value) in FIG2_CASES.items():
        p = printed2(vec, panel, curve)
        sc = np.array(SCALE2)
        pd = densify(p * sc, 0.05) / sc
        values = [("as captioned", value)]
        if (panel, curve) == ("b", "dashed"):
            values.append(("r = 3e11", CAPTION_R_TENFOLD))
        for label, val in values:
            for name, rd in g.READINGS.items():
                m, stable, _ = model2(rd, fixed, val, panel)
                d1, d2 = two_way(p, m, SCALE2)
                d2d = two_way(pd, m, SCALE2)[1]
                # stable/unstable agreement: each printed vertex's nearest model point
                idx = cKDTree(m * SCALE2).query(p * SCALE2)[1]
                parts = np.concatenate([np.full(len(vec[("2", panel, curve, q)]), q != "unstable")
                                        for q in ("upper", "unstable", "lower")])
                rows.append({"panel": panel, "curve": curve, "fixed": fixed, "value": label,
                             "reading": name, "printed_vertices": len(p),
                             "printed_to_model_pt": d1, "model_to_printed_pt": d2d,
                             "stability_agreement": float(np.mean(stable[idx] == parts))})
        # nulls
        flat = np.column_stack([pd[:, 0], np.full(len(pd), np.median(p[:, 1]))])
        shifted = p + [1.0, 0.0]
        rows.append({"panel": panel, "curve": curve, "fixed": fixed, "value": "null",
                     "reading": "null: flat at median log O", "printed_vertices": len(p),
                     "printed_to_model_pt": two_way(p, flat, SCALE2)[0],
                     "model_to_printed_pt": two_way(pd, flat, SCALE2)[1], "stability_agreement": np.nan})
        rows.append({"panel": panel, "curve": curve, "fixed": fixed, "value": "null",
                     "reading": "null: printed curve shifted one decade", "printed_vertices": len(p),
                     "printed_to_model_pt": two_way(p, densify(shifted * sc, 0.05) / sc, SCALE2)[0],
                     "model_to_printed_pt": two_way(pd, shifted, SCALE2)[1], "stability_agreement": np.nan})
    return rows


def pal_offset(vec, rd: g.Reading) -> float:
    """Vertical offset (decades) that best aligns the reading with all Fig. 2
    curves; zero if the figure's PAL equals the reading's."""
    pts = []
    for (panel, curve), (fixed, value) in FIG2_CASES.items():
        val = CAPTION_R_TENFOLD if (panel, curve) == ("b", "dashed") else value
        pts.append((printed2(vec, panel, curve), model2(rd, fixed, val, panel)[0]))
    shifts = np.linspace(-0.2, 0.2, 401)
    cost = [sum(two_way(p, m + [0, s], SCALE2)[0] ** 2 for p, m in pts) for s in shifts]
    return float(shifts[int(np.argmin(cost))])


def fold_rows(vec) -> list[dict]:
    rows = []
    for (panel, curve), (fixed, value) in FIG2_CASES.items():
        conn = vec[("2", panel, curve, "unstable")]
        printed = sorted([tuple(conn[0]), tuple(conn[-1])], key=lambda t: -t[1])
        cases = [("as captioned", value)]
        if (panel, curve) == ("b", "dashed"):
            cases.append(("r = 3e11", CAPTION_R_TENFOLD))
        for label, val in cases:
            for name, rd in g.READINGS.items():
                O, free, _ = g.branch_curve(rd, **{fixed: val}, n=8001)
                f = sorted(g.folds(O, free), key=lambda t: -t[0])
                for which, (px, py), mf in zip(("upper", "lower"), printed, f + [(np.nan, np.nan)] * 2):
                    rows.append({"panel": panel, "curve": curve, "value": label, "reading": name,
                                 "fold": which, "printed_log10_param": px, "printed_log10_O_PAL": py,
                                 "model_log10_param": np.log10(mf[1]),
                                 "model_log10_O_PAL": np.log10(mf[0] / rd.pal_mol)})
    return rows


def beta_from_fig3d(vec) -> float:
    """beta implied by the dashed burial step in Fig. 3d zoom: at the step,
    burial - weathering = beta * dN."""
    v = vec[("3", "d_zoom", "burial", "trace")]
    dn = STEPS["c"][2] - STEPS["c"][0]
    return float(v[:, 1].max() * 1e11 / dn)


def run_case(rd: g.Reading, case: str, t_end: float) -> g.Run:
    N0, r0, N1, r1 = STEPS[case]
    t_eval = np.unique(np.concatenate([[0.0], np.logspace(-2, np.log10(t_end), 4000),
                                       np.linspace(0, t_end, 2001)]))
    t_eval = t_eval[t_eval <= t_end]
    return g.step(rd, N0=N0, r0=r0, N1=N1, r1=r1, t_end=t_end, t_eval=t_eval)


def zoom_step_gyr(vec) -> float:
    """Where the zoom panels draw the forcing step: the jump in the reductant
    input of Fig. 3b's zoom. It sits 90 kyr after the labelled 2.4 Gyr."""
    v = vec[("3", "b_zoom", "input", "trace")]
    jump = np.argmax(np.abs(np.diff(v[:, 1])) > 1.0)
    return float(v[jump, 0])


def model3(rd: g.Reading, run: g.Run, curve: str, panel: str, methane_axis: str, t_step: float = T_STEP_GYR):
    """Model trace in Fig. 3 data units (Gyr ago, plotted value), with the
    pre-step steady state drawn back to the left frame edge."""
    t_ago = t_step - run.t / 1e9
    if curve == "oxygen":
        y = np.log10(run.O / rd.pal_mol)
    elif curve == "methane":
        y = np.log10(run.M / rd.pal_mol) if methane_axis == "PAL" else np.log10(run.M / g.MU) + 1.0
    else:
        y = g.budget(run, rd)[curve] / 1e11
        r0 = STEPS["a" if panel[0] == "b" else "c"][1]
        pre = {"escape": r0, "net": 0.0, "burial": 0.0, "input": -r0}[curve] / 1e11
        x0 = V.FIG3[panel][0]
        return np.vstack([[x0, pre], [t_step, pre], np.column_stack([t_ago, y])])
    x0 = V.FIG3[panel][0]
    return np.vstack([[x0, y[0]], np.column_stack([t_ago, y])])


def _clip(m, panel):
    x0, x1, y0, y1 = V.FIG3[panel]
    lo, hi = min(y0, y1), max(y0, y1)
    keep = (m[:, 0] <= x0 + 1e-12) & (m[:, 0] >= x1 - 1e-12)
    m = m[keep]
    m[:, 1] = np.clip(m[:, 1], lo, hi)
    return m


def fig3_scores(vec, beta3d: float) -> tuple[list[dict], dict]:
    rows, runs = [], {}
    t_zoom = zoom_step_gyr(vec)
    for name, rd0 in g.READINGS.items():
        for blabel, beta in (("SI", g.BETA_SI), ("Fig. 3d", beta3d)):
            rd = replace(rd0, beta=beta)
            for case in ("a", "c"):
                long = run_case(rd, case, 4e8)
                short = run_case(rd, case, 1e6)
                runs[(name, blabel, case)] = (rd, long, short)
                budget_panel = "b" if case == "a" else "d"
                for panel, curves in ((case, ("oxygen", "methane")), (budget_panel, ("escape", "burial", "input", "net"))):
                    for zoom in ("", "_zoom"):
                        pn = panel + zoom
                        run = short if zoom else long
                        for curve in curves:
                            key = ("3", pn, curve, "trace")
                            if key not in vec:
                                continue
                            p = vec[key]
                            for axis in (("PAL", "atm right") if curve == "methane" else ("",)):
                                m = _clip(model3(rd, run, curve, pn, axis, t_zoom if zoom else T_STEP_GYR), pn)
                                sc = np.array(SCALE3[pn])
                                m = densify(m * sc, 0.05) / sc
                                d1, _ = two_way(p, m, SCALE3[pn])
                                rows.append({"panel": pn, "curve": curve, "reading": name, "beta": blabel,
                                             "methane_axis": axis, "printed_vertices": len(p),
                                             "step_drawn_at_gyr": t_zoom if zoom else T_STEP_GYR,
                                             "printed_to_model_pt": d1,
                                             "fitted_to_this_trace": blabel == "Fig. 3d" and pn.startswith("d") and curve == "burial"})
    return rows, runs


def transition_times(run: g.Run, rd: g.Reading) -> dict:
    o = run.O / rd.pal_mol
    lo, hi = np.log10(o[0]), np.log10(o[-1])
    out = {}
    for label, level in (("1e-5 PAL", 1e-5), ("upper fold 5e-3 PAL", 5e-3),
                         ("half the log rise", 10 ** (lo + 0.5 * (hi - lo))),
                         ("90% of the log rise", 10 ** (lo + 0.9 * (hi - lo)))):
        i = np.argmax(o >= level)
        out[label] = float(np.interp(np.log10(level), np.log10(o[i - 1:i + 1]), run.t[i - 1:i + 1])) if i > 0 else np.nan
    return out


def reverse_time(rd: g.Reading, r_up: float) -> float:
    """From the high state at modern N and r = 7.5e10, step r up to r_up and time
    the fall of O below 1e-5 PAL."""
    O0 = max(o for o, ok in g.steady_states(g.N_MODERN, 7.5e10, rd) if ok)
    y0 = np.array([np.log(7.5e10 / rd.s), np.log(O0), rd.beta * (g.N_MODERN + 7.5e10) / g.W])
    from scipy.integrate import solve_ivp

    ev = lambda t, z, *a: z[1] - np.log(1e-5 * rd.pal_mol)
    ev.terminal = True
    sol = solve_ivp(g._log_rhs, (0, 1e9), y0, args=(g.N_MODERN, r_up, rd), method="Radau",
                    events=ev, rtol=1e-10, atol=1e-12)
    return float(sol.t_events[0][0]) if sol.t_events[0].size else np.nan


def simplified_agreement(rd: g.Reading, tol=0.01) -> float:
    """Lowest O (PAL) above which the simplified eq. (6) root matches the full
    eq. (12) root to within `tol` in r, along the modern-N curve of Fig. 2a."""
    O = np.logspace(np.log10(1e-12 * rd.pal_mol), np.log10(rd.pal_mol), 1201)
    full = g.r_of_o(O, g.N_MODERN, rd)
    simp = (g.omega(O) * g.N_MODERN / g.psi(O, rd)) ** (1 / g.METHANE_EXPONENT) * rd.s
    bad = np.abs(np.log10(simp / full)) > np.log10(1 + tol)
    return float(O[np.where(bad)[0].max() + 1] / rd.pal_mol) if bad.any() else float(O[0] / rd.pal_mol)


def claims(vec, runs, beta3d: float) -> list[dict]:
    rd = g.READINGS["author_p"]
    rows = []

    def add(claim, stated, value, source, note=""):
        rows.append({"claim": claim, "stated": stated, "author_p": value, "source": source, "note": note})

    for r, stated in ((3e11, "low branch, ~1e-6 PAL (with BIF-era r)"), (7.5e10, "high branch only, ~0.1 PAL")):
        ss = [(o / rd.pal_mol, ok) for o, ok in g.steady_states(g.N_MODERN, r, rd)]
        add(f"steady states at modern N, r = {r:.3g}", stated,
            "; ".join(f"{o:.3g} PAL ({'stable' if ok else 'unstable'})" for o, ok in ss), "p. 684")
    O, free, _ = g.branch_curve(rd, N=g.N_MODERN, n=8001)
    f = sorted([q for q in g.folds(O, free) if q[0] > 1e-10 * rd.pal_mol], key=lambda t: t[0])
    add("lowest high-branch O at modern N", "> 5e-3 PAL", f"{f[1][0] / rd.pal_mol:.3g} PAL", "p. 684")
    add("highest low-branch O at modern N", "< 1e-5 PAL", f"{f[0][0] / rd.pal_mol:.3g} PAL", "p. 684")
    add("bistable range of r at modern N", "contains part of 1.25e11-7.5e11 (shaded band)",
        f"{min(f[0][1], f[1][1]):.3g}-{max(f[0][1], f[1][1]):.3g}", "Fig. 2a")
    O, free, _ = g.branch_curve(rd, r=7.5e10, o_pal=(1e-14, 1e-11), n=401)
    add("prebiotic rise: N at O = 1e-12 PAL, r = 7.5e10", "when N exceeds r",
        f"N = {np.interp(-12, np.log10(O / rd.pal_mol), free):.3g}", "p. 685")
    add("simplified eq. (6) equivalent to full eq. above", "1e9 PAL (as printed)",
        f"{simplified_agreement(rd):.2g} PAL (1% in r); {simplified_agreement(rd, 0.1):.2g} PAL (10%)",
        "Fig. 2 caption, SI p. 10")
    th_g = g.D_GAMMA / rd.pal_mol
    th_d = g.D_DELTA / rd.pal_mol
    add("respiration threshold d_gamma", "0.01 PAL (Pasteur point)", f"{th_g:.3g} PAL", "p. 684, Methods",
        f"[O] = {g.ALPHA * g.D_GAMMA / g.MU * 1e6:.0f} uM; text value matches if 1 PAL = {g.D_GAMMA / 0.01:.3g} mol")
    add("methanotrophy threshold d_delta", "2e-4 PAL; [O] = 2 uM", f"{th_d:.3g} PAL", "p. 684, Methods",
        f"[O] = {g.ALPHA * g.D_DELTA / g.MU * 1e6:.2f} uM; text value matches if 1 PAL = {g.D_DELTA / 2e-4:.3g} mol")
    for beta_label in ("SI", "Fig. 3d"):
        for case, total in (("a", "3e18 mol"), ("c", "9e17 mol")):
            rdb, long, short = runs[("author_p", beta_label, case)]
            b = g.budget(long, rdb)
            add(f"total oxidation, Fig. 3{'b' if case == 'a' else 'd'} (beta {beta_label})", total,
                f"{np.trapezoid(b['net'], long.t):.3g} mol; final O {long.O[-1]:.3g} mol", "Fig. 3 caption")
            tt = transition_times(short, rdb)
            add(f"transition time, case {case} (beta {beta_label})", "150 kyr" if case == "a" else "50 kyr",
                "; ".join(f"{k}: {v / 1e3:.0f} kyr" for k, v in tt.items()), "p. 685")
            add(f"methane fall, case {case} (beta {beta_label})", "factor 2-6",
                f"factor {long.M[0] / long.M.min():.2f}", "p. 685")
            esc = b["escape"]
            target = long.r
            late = np.where(np.abs(esc - target) > 0.1 * target)[0]
            add(f"methane re-adjustment (escape within 10% of r), case {case} (beta {beta_label})",
                "about 50 Myr (case a)" if case == "a" else "recovers (case c)",
                f"{long.t[late.max() + 1] / 1e6:.1f} Myr" if late.size and late.max() + 1 < len(long.t) else "not within run",
                "p. 684")
            if case == "c":
                add(f"organic carbon increase after 400 Myr, case c (beta {beta_label})", "3% over ~500 Myr",
                    f"{(long.C[-1] / long.C[0] - 1) * 100:.2f}%", "Fig. 3 caption")
    for r_up in (7.5e11, 1e12, 3e12):
        t = reverse_time(rd, r_up)
        add(f"reverse switch time, r stepped 7.5e10 -> {r_up:.2g}", "3-7 Myr",
            f"{t / 1e6:.2f} Myr" if np.isfinite(t) else "no switch", "p. 685",
            "the source does not state the reverse forcing")
    tz = zoom_step_gyr(vec)
    for case in ("a", "c"):
        p = vec[("3", f"{case}_zoom", "oxygen", "trace")]
        lo, hi = p[0, 1], p[-1, 1]
        i = np.argmax(p[:, 1] >= lo + 0.5 * (hi - lo))
        add(f"printed transition time, Fig. 3{case} zoom (half the log rise, from the drawn step)",
            "150 kyr" if case == "a" else "50 kyr", f"{(tz - p[i, 0]) * 1e6:.0f} kyr", "Fig. 3 zoom",
            "read from the published vertices, not the model")
    main_in = vec[("3", "b", "input", "trace")][0, 1]
    zoom_in = vec[("3", "b_zoom", "input", "trace")][0, 1]
    add("Fig. 3b pre-step reductant input, main vs zoom panel", "both -3e11",
        f"main {main_in:.3f}e11, zoom {zoom_in:.3f}e11", "Fig. 3b", "same quantity drawn at two levels")
    f0 = (0 - (-6)) / (0 - (-30))
    f1 = f0 * 1.03
    add("delta13C carbonate after 3% more burial", "f = 0.206, +0.23 permil",
        f"f = {f1:.4f}, {(-6 + f1 * 30) / (1 - f1):.3f} permil", "Methods")
    add("beta implied by Fig. 3d burial step", "not printed", f"{beta3d:.4g}", "Fig. 3d",
        f"SI-derived beta = {g.BETA_SI:.4g}")
    add("figure PAL offset (decades) for author_p", "PAL not printed", f"{pal_offset(vec, rd):+.4f}", "Fig. 2",
        f"zero means the figure's PAL is 0.2095 mu = {rd.pal_mol:.4g} mol")
    return rows


def overlay(vec, runs, path: Path) -> None:
    fig, ax = plt.subplots(2, 3, figsize=(13, 7))
    colours = {"faithful": "tab:red", "author_p": "tab:blue", "author_corrected": "tab:orange"}
    for k, ((panel, curve), (fixed, value)) in enumerate(FIG2_CASES.items()):
        a = ax[0, 0 if panel == "a" else 1]
        p = printed2(vec, panel, curve)
        a.plot(p[:, 0], p[:, 1], ".", ms=2, color="k", label="printed vertices" if k in (0, 2) else None)
        val = CAPTION_R_TENFOLD if (panel, curve) == ("b", "dashed") else value
        for name, rd in g.READINGS.items():
            m, _, _ = model2(rd, fixed, val, panel)
            a.plot(m[:, 0], m[:, 1], "-", lw=0.8, color=colours[name], label=name if k in (0, 2) else None)
    ax[0, 0].set(xlabel="log10 r (mol O2 equiv./yr)", ylabel="log10 O2 (PAL)", title="Fig. 2a: N and N/2")
    ax[0, 1].set(xlabel="log10 N (mol O2/yr)", title="Fig. 2b: r = 7.5e10 and 3e11 (captioned 3e10)")
    ax[0, 0].legend(fontsize=7)
    for j, case in enumerate(("a", "c")):
        a = ax[1, j]
        rd, long, _ = runs[("author_p", "Fig. 3d", case)]
        for curve, st in (("oxygen", "-"), ("methane", "--")):
            p = vec[("3", case, curve, "trace")]
            a.plot(p[:, 0], p[:, 1], ".", ms=2, color="k")
            m = _clip(model3(rd, long, curve, case, "PAL"), case)
            a.plot(m[:, 0], m[:, 1], st, lw=0.8, color="tab:blue")
        a.invert_xaxis()
        a.set(xlabel="Gyr ago", ylabel="log10 (PAL)", title=f"Fig. 3{case}: author_p, beta from Fig. 3d")
    a = ax[1, 2]
    rd, long, _ = runs[("author_p", "Fig. 3d", "c")]
    for curve in ("escape", "burial", "input", "net"):
        p = vec[("3", "d", curve, "trace")]
        a.plot(p[:, 0], p[:, 1], ".", ms=2, color="k")
        m = _clip(model3(rd, long, curve, "d", ""), "d")
        a.plot(m[:, 0], m[:, 1], "-", lw=0.8, label=curve)
    a.invert_xaxis()
    a.set(xlabel="Gyr ago", ylabel="1e11 mol O2 equiv./yr", title="Fig. 3d budget (burial step fitted)")
    a.legend(fontsize=7)
    ax[0, 2].axis("off")
    ax[0, 2].text(0, 0.5, "Black dots: vertices of the published\nvector paths. Lines: this reconstruction.",
                  fontsize=9, va="center")
    fig.tight_layout()
    fig.savefig(path, dpi=150, metadata={"Software": None})
    plt.close(fig)


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()})


def main(outdir: Path = OUT) -> None:
    vec = V.load(outdir / "glw2006_vectors.csv")
    beta3d = beta_from_fig3d(vec)
    write(outdir / "glw2006_fig2.csv", fig2_scores(vec))
    write(outdir / "glw2006_folds.csv", fold_rows(vec))
    rows3, runs = fig3_scores(vec, beta3d)
    write(outdir / "glw2006_fig3.csv", rows3)
    write(outdir / "glw2006_claims.csv", claims(vec, runs, beta3d))
    overlay(vec, runs, outdir / "glw2006_overlay.png")


if __name__ == "__main__":
    main(*(Path(a) for a in sys.argv[1:]))
