"""Score the GLW (2006) readings against the printed Figs 2 and 3, the
Supplementary Figs 2 and 3, and the text.

    uv run python -m terra_prisca.goldblatt_lenton_watson.fidelity_glw2006 [outdir]

Reads the vector geometry written by vectors.py (glw2006_vectors.csv,
glw2006_frames.csv, glw2006_si_vectors.csv) and writes, to
models/goldblatt_lenton_watson/fidelity/:

  glw2006_fig2.csv     each Fig. 2 curve against each reading and null
  glw2006_folds.csv    fold positions, printed and modelled
  glw2006_fig3.csv     each Fig. 3 trace against each reading, beta and methane axis
  glw2006_si.csv       Supplementary Figs 2 and 3, and the SI-only polynomial
  glw2006_claims.csv   the stated numbers, recomputed
  glw2006_overlay.png  model curves drawn over the printed vertices

Scoring. Every curve, printed or modelled, is a list of polylines. Model curves
are clipped segment by segment at the calibrated frame, so a curve that leaves
the frame and comes back is two visible runs, never one joined line. Each run is
densified to 0.01 pt on its own. Distances are measured on the printed page in
points, in both directions: printed-to-model and model-to-printed, each as an
RMS over arc length. Both are taken on the common support, the span of the
support coordinate (log O in Fig. 2, time in Fig. 3) that both curves cover;
the length of each curve outside that span, and of the model outside the frame,
is reported separately.
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
from scipy.integrate import solve_ivp
from scipy.spatial import cKDTree

from . import glw2006 as g
from . import vectors as V

OUT = Path("models/goldblatt_lenton_watson/fidelity")
STEP_PT = 0.01

FIG2_CASES = {  # (panel, curve): (fixed parameter, value as captioned)
    ("a", "solid"): ("N", g.N_MODERN),
    ("a", "dashed"): ("N", g.N_MODERN / 2),
    ("b", "solid"): ("r", 7.5e10),
    ("b", "dashed"): ("r", 3e10),
}
CAPTION_R_TENFOLD = 3e11   # the value the Fig. 2b dashed curve actually fits (see README)
FIG2_PARTS = ("upper", "unstable", "lower")

STEPS = {  # Fig. 3 caption: (N0, r0) -> (N1, r1) at 2.4 Gyr ago
    "a": (g.N_MODERN, 3e11, g.N_MODERN, 7.5e10),
    "c": (3.6375e15, 3e11, g.N_MODERN, 3e11),
}
T_STEP_GYR = 2.4
R_PRE = 3e11               # pre-step r in both Fig. 3 cases; the pre-step state is in balance
assert all(v[1] == R_PRE for v in STEPS.values())

# Kasting, Pavlov & Siefert (2001), Orig. Life Evol. Biosph. 31, 271-285, eq. (1)
# and Table I: Ts (K) at 0.8 of present solar luminosity, x = log10 f(CH4),
# y = log10 f(CO2), fitted over 1e-5 < pCO2 < 1e-2 atm and 1e-5 < f(CH4) < 1e-2.
KASTING_K = (-0.7542, 0.2625, -0.9025, -0.4325, -9.1088, 1.3738, -9.6900, -28.1973, -4.8311, 301.0699)
KASTING_CO2 = (1e-5, 1e-2)

# Catling, Zahnle & McKay (2001), Science 293, 839-843, eq. (1): diffusion-limited
# H escape 2.5e13 f_total H2 molecules cm^-2 s^-1, with f_total = 2 f(CH4) here.
CATLING_COEFF = 2.5e13
R_EARTH_CM = 6.371e8
YEAR_S = 3.15576e7
AVOGADRO = 6.02214076e23
SULPHUR_BOUND_PAL = 1e-5   # SI: mass-independent sulphur fractionation requires O < 1e-5 PAL


# ----------------------------------------------------------------- geometry

def frames(path: Path = V.FRAMES):
    return V.load_frames(path)


def scale(fr: dict) -> np.ndarray:
    """Points per data unit along x and y."""
    return np.array([fr["width_pt"] / abs(fr["x_left"] - fr["x_right"]),
                     fr["height_pt"] / abs(fr["y_top"] - fr["y_bottom"])])


def box(fr: dict) -> tuple[float, float, float, float]:
    return (min(fr["x_left"], fr["x_right"]), max(fr["x_left"], fr["x_right"]),
            min(fr["y_top"], fr["y_bottom"]), max(fr["y_top"], fr["y_bottom"]))


def clip_runs(p: np.ndarray, bx) -> list[np.ndarray]:
    """Clip a polyline at the box segment by segment (Liang-Barsky) and return
    its visible runs. A run ends wherever the line leaves the box."""
    if len(p) < 2:
        return []
    xmin, xmax, ymin, ymax = bx
    a, d = p[:-1], np.diff(p, axis=0)
    t0, t1 = np.zeros(len(d)), np.ones(len(d))
    ok = np.ones(len(d), bool)
    for pp, qq in ((-d[:, 0], a[:, 0] - xmin), (d[:, 0], xmax - a[:, 0]),
                   (-d[:, 1], a[:, 1] - ymin), (d[:, 1], ymax - a[:, 1])):
        ok &= ~((pp == 0) & (qq < 0))
        with np.errstate(divide="ignore", invalid="ignore"):
            r = qq / pp
        t0 = np.where(pp < 0, np.maximum(t0, r), t0)
        t1 = np.where(pp > 0, np.minimum(t1, r), t1)
    ok &= t0 <= t1
    idx = np.flatnonzero(ok)
    if not idx.size:
        return []
    starts, ends = a + t0[:, None] * d, a + t1[:, None] * d
    brk = np.flatnonzero((np.diff(idx) != 1) | (t1[idx[:-1]] < 1) | (t0[idx[1:]] > 0)) + 1
    return [np.vstack([starts[s[0]], ends[s]]) for s in np.split(idx, brk)]


def length(runs, sc) -> float:
    return float(sum(np.hypot(*(np.diff(r * sc, axis=0)).T).sum() for r in runs if len(r) > 1))


def densify(p: np.ndarray, step: float) -> np.ndarray:
    """Insert points so no segment exceeds `step` (in the units of p)."""
    if len(p) < 2:
        return p
    seg = np.diff(p, axis=0)
    n = np.maximum(1, np.ceil(np.hypot(seg[:, 0], seg[:, 1]) / step).astype(int))
    k = np.repeat(np.arange(len(seg)), n)
    frac = (np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n) + 1) / np.repeat(n, n)
    return np.vstack([p[:1], p[k] + seg[k] * frac[:, None]])


def _samples(runs, sc):
    """Arc-length samples (pt) of the densified runs: segment midpoints, each
    weighted by its segment's length, plus the segments themselves."""
    mids, w, segs = [], [], []
    for r in runs:
        q = densify(r * sc, STEP_PT)
        if len(q) < 2:
            continue
        mids.append(0.5 * (q[1:] + q[:-1]))
        w.append(np.hypot(*np.diff(q, axis=0).T))
        segs.append(np.stack([q[:-1], q[1:]], axis=1))
    if not mids:
        return np.empty((0, 2)), np.empty(0), np.empty((0, 2, 2))
    return np.vstack(mids), np.concatenate(w), np.vstack(segs)


def _distance(pts, segs, k=4):
    """Exact distance from each point to the nearest of the polyline segments,
    searched among the k segments with the nearest midpoints."""
    mid = segs.mean(axis=1)
    _, idx = cKDTree(mid).query(pts, k=min(k, len(segs)))
    idx = idx.reshape(len(pts), -1)
    a, b = segs[idx, 0], segs[idx, 1]
    ab = b - a
    t = np.clip(np.einsum("ijk,ijk->ij", pts[:, None] - a, ab) / np.maximum(np.einsum("ijk,ijk->ij", ab, ab), 1e-300), 0, 1)
    return np.hypot(*(a + t[..., None] * ab - pts[:, None]).transpose(2, 0, 1)).min(axis=1)


def score(printed: list, model: list, sc, axis: int | None) -> dict:
    """Two-way RMS distances (pt) on the common support of coordinate `axis`
    (0 = x, 1 = y; None = everywhere), with the length of each curve outside it."""
    sc = np.asarray(sc, float)
    pm, pw, ps = _samples(printed, sc)
    mm, mw, ms = _samples(model, sc)
    nan = {"printed_to_model_pt": np.nan, "model_to_printed_pt": np.nan,
           "printed_outside_support_pt": np.nan, "model_outside_support_pt": np.nan}
    if not len(mm) or not len(pm):
        return nan
    if axis is None:
        inp, inm = np.ones(len(pm), bool), np.ones(len(mm), bool)
    else:
        lo = max(ps[:, :, axis].min(), ms[:, :, axis].min())
        hi = min(ps[:, :, axis].max(), ms[:, :, axis].max())
        inp = (pm[:, axis] >= lo) & (pm[:, axis] <= hi)
        inm = (mm[:, axis] >= lo) & (mm[:, axis] <= hi)
    rms = lambda d, w: float(np.sqrt(np.sum(w * d**2) / np.sum(w))) if np.sum(w) > 0 else np.nan
    return {"printed_to_model_pt": rms(_distance(pm[inp], ms), pw[inp]),
            "model_to_printed_pt": rms(_distance(mm[inm], ps), mw[inm]),
            "printed_outside_support_pt": float(pw[~inp].sum()),
            "model_outside_support_pt": float(mw[~inm].sum())}


# ----------------------------------------------------------------- Fig. 2

def printed2(vec, panel, curve) -> list[np.ndarray]:
    return [vec[("2", panel, curve, p)] for p in FIG2_PARTS]


def model2_points(rd: g.Reading, fixed: str, value: float, n=3001):
    O, free, stable = g.branch_curve(rd, **{fixed: value}, n=n)
    return np.column_stack([np.log10(free), np.log10(O / rd.pal_mol)]), stable


def model2(rd: g.Reading, fixed: str, value: float, fr: dict, n=3001):
    """Visible runs of the steady-state curve, its off-frame length (pt), and
    all points with their stability."""
    xy, stable = model2_points(rd, fixed, value, n)
    runs = clip_runs(xy, box(fr))
    off = length([xy], scale(fr)) - length(runs, scale(fr))
    return runs, off, xy, stable


def fig2_scores(vec, F) -> list[dict]:
    rows = []
    for (panel, curve), (fixed, value) in FIG2_CASES.items():
        fr = F[("2", panel)]
        sc, p = scale(fr), printed2(vec, panel, curve)
        base = {"panel": panel, "curve": curve, "fixed": fixed}
        values = [("as captioned", value)]
        if (panel, curve) == ("b", "dashed"):
            values.append(("r = 3e11", CAPTION_R_TENFOLD))
        for label, val in values:
            for name, rd in g.READINGS.items():
                runs, off, xy, stable = model2(rd, fixed, val, fr)
                inside = (xy[:, 0] >= box(fr)[0]) & (xy[:, 0] <= box(fr)[1])
                idx = cKDTree(xy[inside] * sc).query(np.vstack(p) * sc)[1]
                truth = np.concatenate([np.full(len(q), part != "unstable") for q, part in zip(p, FIG2_PARTS)])
                rows.append({**base, "value": label, "reading": name, **score(p, runs, sc, 1),
                             "model_off_frame_pt": off,
                             "stability_agreement": float(np.mean(stable[inside][idx] == truth))})
        flat = [np.array([[min(q[:, 0].min() for q in p), np.median(np.vstack(p)[:, 1])],
                          [max(q[:, 0].max() for q in p), np.median(np.vstack(p)[:, 1])]])]
        shifted = [q + [1.0, 0.0] for q in p]
        for label, m, axis in (("null: flat at median log O", flat, None),
                               ("null: printed curve shifted one decade", shifted, 1)):
            rows.append({**base, "value": "null", "reading": label, **score(p, m, sc, axis),
                         "model_off_frame_pt": 0.0, "stability_agreement": np.nan})
    return rows


def pal_offset(vec, F, rd: g.Reading) -> float:
    """Vertical offset (decades) that best aligns the reading with all Fig. 2
    curves; zero if the figure's PAL equals the reading's."""
    pts = []
    for (panel, curve), (fixed, value) in FIG2_CASES.items():
        val = CAPTION_R_TENFOLD if (panel, curve) == ("b", "dashed") else value
        xy, _ = model2_points(rd, fixed, val)
        sc = scale(F[("2", panel)])
        pts.append((np.vstack(printed2(vec, panel, curve)) * sc, densify(xy * sc, STEP_PT), sc[1]))

    def cost(s):
        return sum(np.sum(cKDTree(m + [0, s * sy]).query(p)[0] ** 2) for p, m, sy in pts)

    coarse = np.linspace(-0.2, 0.2, 41)
    c0 = coarse[int(np.argmin([cost(s) for s in coarse]))]
    fine = np.linspace(c0 - 0.01, c0 + 0.01, 41)
    return float(fine[int(np.argmin([cost(s) for s in fine]))])


def fold_rows(vec, readings=None) -> list[dict]:
    rows = []
    for (panel, curve), (fixed, value) in FIG2_CASES.items():
        conn = vec[("2", panel, curve, "unstable")]
        printed = sorted([tuple(conn[0]), tuple(conn[-1])], key=lambda t: -t[1])
        cases = [("as captioned", value)]
        if (panel, curve) == ("b", "dashed"):
            cases.append(("r = 3e11", CAPTION_R_TENFOLD))
        for label, val in cases:
            for name, rd in (readings or g.READINGS).items():
                O, free, _ = g.branch_curve(rd, **{fixed: val}, n=8001)
                f = sorted(g.folds(O, free), key=lambda t: -t[0])
                for which, (px, py), mf in zip(("upper", "lower"), printed, f + [(np.nan, np.nan)] * 2):
                    rows.append({"panel": panel, "curve": curve, "value": label, "reading": name,
                                 "fold": which, "printed_log10_param": px, "printed_log10_O_PAL": py,
                                 "model_log10_param": np.log10(mf[1]),
                                 "model_log10_O_PAL": np.log10(mf[0] / rd.pal_mol)})
    return rows


# ----------------------------------------------------------------- Fig. 3

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


def model3(rd: g.Reading, run: g.Run, curve: str, fr: dict, methane_axis: str = "PAL"):
    """Model trace in Fig. 3 data units (Gyr ago, plotted value), with the
    pre-step steady state drawn back to the left frame edge. Methane is plotted
    either on the left axis in PAL-of-O2 units, or on the right axis as ticked
    (log10 atm, mapped onto the left axis through that panel's tick fit)."""
    t_ago = T_STEP_GYR - run.t / 1e9
    x0 = fr["x_left"]
    if curve in ("escape", "net", "burial", "input"):
        y = g.budget(run, rd)[curve] / 1e11
        pre = {"escape": R_PRE, "net": 0.0, "burial": 0.0, "input": -R_PRE}[curve] / 1e11
        return np.vstack([[x0, pre], [T_STEP_GYR, pre], np.column_stack([t_ago, y])])
    if curve == "oxygen":
        y = np.log10(run.O / rd.pal_mol)
    elif methane_axis == "PAL":
        y = np.log10(run.M / rd.pal_mol)
    else:
        y = (np.log10(run.M / g.MU) - fr["right_at_left_zero"]) / fr["right_per_left"]
    return np.vstack([[x0, y[0]], np.column_stack([t_ago, y])])


def fig3_scores(vec, F, beta3d: float) -> tuple[list[dict], dict]:
    rows, runs = [], {}
    for name, rd0 in g.READINGS.items():
        for blabel, beta in (("SI", g.BETA_SI), ("Fig. 3d", beta3d)):
            rd = replace(rd0, beta=beta)
            for case in ("a", "c"):
                long = run_case(rd, case, 4e8)
                short = run_case(rd, case, 1e6)
                runs[(name, blabel, case)] = (rd, long, short)
                budget_panel = "b" if case == "a" else "d"
                if name == "faithful" and blabel == "SI":
                    rows += fig3_nulls(vec, F, case, budget_panel)
                for panel, curves in ((case, ("oxygen", "methane")),
                                      (budget_panel, ("escape", "burial", "input", "net"))):
                    for zoom in ("", "_zoom"):
                        pn = panel + zoom
                        fr = F[("3", pn)]
                        run = short if zoom else long
                        for curve in curves:
                            key = ("3", pn, curve, "trace")
                            if key not in vec:
                                continue
                            for axis in (("PAL", "atm (right, as ticked)") if curve == "methane" else ("",)):
                                m = model3(rd, run, curve, fr, axis if axis else "PAL")
                                vis = clip_runs(m, box(fr))
                                rows.append({"panel": pn, "curve": curve, "reading": name, "beta": blabel,
                                             "methane_axis": axis, "printed_vertices": len(vec[key]),
                                             **score([vec[key]], vis, scale(fr), 0),
                                             "model_off_frame_pt": length([m], scale(fr)) - length(vis, scale(fr)),
                                             "fitted_to_this_trace": blabel == "Fig. 3d" and pn.startswith("d")
                                             and curve == "burial"})
    return rows, runs


def fig3_nulls(vec, F, case: str, budget_panel: str) -> list[dict]:
    """No-switch null: each printed trace's own first (pre-step) value held
    across the calibrated frame."""
    rows = []
    for panel in (case, case + "_zoom", budget_panel, budget_panel + "_zoom"):
        fr = F[("3", panel)]
        for (fig, pn, curve, _), p in vec.items():
            if fig != "3" or pn != panel:
                continue
            flat = np.array([[fr["x_left"], p[0, 1]], [fr["x_right"], p[0, 1]]])
            rows.append({"panel": pn, "curve": curve, "reading": "null: no switch", "beta": "",
                         "methane_axis": "", "printed_vertices": len(p),
                         **score([p], clip_runs(flat, box(fr)), scale(fr), 0),
                         "model_off_frame_pt": 0.0, "fitted_to_this_trace": False})
    return rows


# ----------------------------------------------------------------- SI figures

def si_reading(si, dy: float = 0.0, dx: float = 0.0) -> g.Reading:
    """SI-only reading: a quartic fitted to the line of Supplementary Fig. 3.
    The figure plots methane oxidation (mol CH4/yr) over M^0.7; the SI's
    equations remove 1/2 Psi M^0.7 of methane and Psi M^0.7 of oxygen, so
    Psi is twice the plotted value. dx, dy shift the line (decades) to test
    calibration sensitivity."""
    line = si[("S3", "", "fit", "line")]
    c = np.polyfit(line[:, 0] + dx, line[:, 1] + dy + np.log10(2.0), 4)
    return g.Reading("si_fig_s3", coeffs=tuple(float(v) for v in c))


def si_rows(si) -> list[dict]:
    rows = []
    for level, stated in (("1 PAL", 0.58), ("0.1 PAL", 0.75), ("0.01 PAL", 0.70)):
        v = si[("S2", "", level, "markers")]
        rows.append({"item": f"S2 log-log slope, oxidation vs methane, {level}", "stated": f"n = {stated}",
                     "value": f"{np.polyfit(v[:, 0], v[:, 1], 1)[0]:.5f}", "note": f"{len(v)} markers"})
    line = si[("S3", "", "fit", "line")]
    for name, coeffs in (("full-precision", g.COEFFS_AUTHOR), ("printed four-decimal", g.COEFFS_PRINTED)):
        d = line[:, 1] - np.polyval(coeffs, line[:, 0])
        rows.append({"item": f"S3 line minus log10 Psi ({name} coefficients)", "stated": "log10 Psi",
                     "value": f"mean {d.mean():+.4f}, sd {d.std():.4f} decades",
                     "note": f"RMS about -log10 2: {np.sqrt(np.mean((d + np.log10(2)) ** 2)):.4f} decades"})
    for label, dx, dy in (("as drawn", 0, 0), ("line +0.003 decades in y", 0, 0.003),
                          ("line -0.003 decades in y", 0, -0.003), ("line +0.003 decades in x", 0.003, 0),
                          ("line -0.003 decades in x", -0.003, 0)):
        rd = si_reading(si, dy, dx)
        O, free, _ = g.branch_curve(rd, N=g.N_MODERN, n=8001)
        f = sorted(g.folds(O, free), key=lambda t: t[0])
        ss = g.steady_states(g.N_MODERN, 3e11, rd)
        rows.append({"item": f"SI-only quartic ({label}): bistable r at modern N",
                     "stated": "1.336e11-5.519e11 with the full-precision coefficients",
                     "value": "-".join(f"{q[1]:.4g}" for q in f) if len(f) == 2 else f"{len(f)} folds",
                     "note": "stable O at r = 3e11: " + ", ".join(f"{o / rd.pal_mol:.4g}" for o, ok in ss if ok)
                     + " PAL; coefficients " + ", ".join(f"{c:.7g}" for c in rd.coeffs)})
    rf = g.READINGS["faithful"]
    O, free, _ = g.branch_curve(rf, N=g.N_MODERN, n=8001)
    f = sorted(g.folds(O, free), key=lambda t: t[0])
    for r in (3e11, 5e11):
        ss = g.steady_states(g.N_MODERN, r, rf)
        rows.append({"item": f"printed four-decimal coefficients: stable states at modern N, r = {r:.0e}",
                     "stated": "two stable states in the bistable range",
                     "value": ", ".join(f"{o / rf.pal_mol:.4g}" for o, ok in ss if ok) + " PAL",
                     "note": "bistable range " + "-".join(f"{q[1]:.3g}" for q in f) + " under this reading"})
    return rows


# ----------------------------------------------------------------- claims

def kasting_ts(f_ch4, f_co2):
    x, y = np.log10(f_ch4), np.log10(f_co2)
    k = KASTING_K
    return (k[0] * x**3 + k[1] * y**3 + k[2] * x**2 * y + k[3] * x * y**2 + k[4] * x**2 + k[5] * y**2
            + k[6] * x * y + k[7] * x + k[8] * y + k[9])


def catling_s() -> float:
    """Escape coefficient implied by Catling et al. eq. (1): mol O2 equiv./yr per
    mol CH4. Each CH4 carries two H2 equivalents and each O2 equivalent removes
    two, so the O2-equivalent flux is 2.5e13 f(CH4) per cm^2 per s."""
    area = 4 * np.pi * R_EARTH_CM**2
    return CATLING_COEFF * area * YEAR_S / AVOGADRO / g.MU


def crossing(t, y, level):
    i = int(np.argmax(y >= level))
    return float(np.interp(level, y[i - 1:i + 1], t[i - 1:i + 1])) if i > 0 else np.nan


def transition_times(run: g.Run, rd: g.Reading) -> dict:
    lo = np.log10(run.O / rd.pal_mol)
    a, b = lo[0], lo[-1]
    out = {}
    for label, level in (("1e-5 PAL", -5.0), ("upper fold 5e-3 PAL", np.log10(5e-3)),
                         ("25% of the log rise", a + 0.25 * (b - a)), ("half the log rise", a + 0.5 * (b - a)),
                         ("75% of the log rise", a + 0.75 * (b - a)), ("90% of the log rise", a + 0.9 * (b - a))):
        out[label] = crossing(run.t, lo, level)
    out["25-75% duration"] = out["75% of the log rise"] - out["25% of the log rise"]
    return out


def reverse_time(rd: g.Reading, r_up: float) -> float:
    """From the high state at modern N and r = 7.5e10, step r up to r_up and time
    the fall of O below 1e-5 PAL."""
    O0 = max(o for o, ok in g.steady_states(g.N_MODERN, 7.5e10, rd) if ok)
    y0 = np.array([np.log(7.5e10 / rd.s), np.log(O0), rd.beta * (g.N_MODERN + 7.5e10) / g.W])
    ev = lambda t, z, *a: z[1] - np.log(SULPHUR_BOUND_PAL * rd.pal_mol)
    ev.terminal = True
    sol = solve_ivp(g._log_rhs, (0, 1e9), y0, args=(g.N_MODERN, r_up, rd), method="Radau",
                    events=ev, rtol=1e-10, atol=1e-12)
    return float(sol.t_events[0][0]) if sol.t_events[0].size else np.nan


def simplified_agreement(rd: g.Reading, tol=0.01) -> float:
    """Lowest O (PAL) above which the simplified eq. (6) root matches the full
    eq. (12) root to within `tol` in r, along the modern-N curve of Fig. 2a."""
    O = np.logspace(np.log10(g.O_VALID[0]), np.log10(rd.pal_mol), 1201)
    full = g.r_of_o(O, g.N_MODERN, rd)
    simp = (g.omega(O) * g.N_MODERN / g.psi(O, rd)) ** (1 / g.METHANE_EXPONENT) * rd.s
    bad = np.abs(np.log10(simp / full)) > np.log10(1 + tol)
    return float(O[np.where(bad)[0].max() + 1] / rd.pal_mol) if bad.any() else float(O[0] / rd.pal_mol)


def methane_events(long: g.Run, short: g.Run, rd: g.Reading) -> dict:
    """Methane ratios at three distinct moments: when O first crosses 1e-5 PAL,
    at the first trough, and at the lowest value over the whole run."""
    m0 = long.M[0]
    lo = np.log10(short.O / rd.pal_mol)
    tx = crossing(short.t, lo, -5.0)
    mx = float(np.exp(np.interp(tx, short.t, np.log(short.M))))
    dm = np.diff(long.M)
    first = int(np.argmax((dm[:-1] < 0) & (dm[1:] >= 0))) + 1
    return {"t_cross": tx, "M_cross": mx, "fall_cross": m0 / mx,
            "t_first": float(long.t[first]), "fall_first": m0 / long.M[first],
            "t_min": float(long.t[np.argmin(long.M)]), "fall_min": m0 / long.M.min()}


def claims(vec, F, runs, beta3d: float) -> list[dict]:
    rd = g.READINGS["author_p"]
    rows = []

    def add(claim, stated, value, source, note=""):
        rows.append({"claim": claim, "stated": stated, "author_p": value, "source": source, "note": note})

    for r, stated in ((3e11, "low branch, ~1e-6 PAL (with BIF-era r)"), (7.5e10, "high branch only, ~0.1 PAL")):
        ss = [(o / rd.pal_mol, ok) for o, ok in g.steady_states(g.N_MODERN, r, rd)]
        add(f"steady states at modern N, r = {r:.3g}", stated,
            "; ".join(f"{o:.3g} PAL ({'stable' if ok else 'unstable'})" for o, ok in ss), "p. 684")
    O, free, _ = g.branch_curve(rd, N=g.N_MODERN, n=8001)
    f = sorted(g.folds(O, free), key=lambda t: t[0])
    add("lowest high-branch O at modern N", "> 5e-3 PAL", f"{f[1][0] / rd.pal_mol:.3g} PAL", "p. 684")
    add("highest low-branch O at modern N", "< 1e-5 PAL", f"{f[0][0] / rd.pal_mol:.3g} PAL", "p. 684")
    add("bistable range of r at modern N", "contains part of 1.25e11-7.5e11 (shaded band)",
        f"{min(f[0][1], f[1][1]):.4g}-{max(f[0][1], f[1][1]):.4g}", "Fig. 2a")
    r_bound = float(g.r_of_o(SULPHUR_BOUND_PAL * rd.pal_mol, g.N_MODERN, rd)[0])
    add("low stable state above the SI's 1e-5 PAL sulphur bound", "low state below 1e-5 PAL",
        f"for r between {f[0][1]:.4g} and {r_bound:.4g} at modern N", "SI p. 1, Fig. 2a",
        "the low branch ends at the lower fold, 1.99e-5 PAL")
    # prebiotic: outside the polynomial's domain, two extensions
    o12 = 1e-12 * rd.pal_mol
    n_quartic = float(g.n_of_o(o12, 7.5e10, replace(rd)))
    q0 = np.log10(g.O_VALID[0])
    slope = np.polyval(np.polyder(rd.coeffs), q0)
    psi_lin = 10 ** (np.polyval(rd.coeffs, q0) + slope * (np.log10(o12) - q0))
    om = float(g.omega(o12))
    n_lin = ((2 - om) * 7.5e10 + psi_lin * (7.5e10 / rd.s) ** g.METHANE_EXPONENT) / om
    add("prebiotic rise: N at O = 1e-12 PAL, r = 7.5e10 (EXTRAPOLATION)", "when N exceeds r",
        f"N = {n_quartic:.3g} (quartic extended); {n_lin:.3g} (log-linear from 1e8 mol)", "p. 685",
        f"1e-12 PAL = {o12:.3g} mol, below the fit's stated 1e8 mol limit")
    add("simplified eq. (6) equivalent to full eq. above", "1e9 PAL (as printed)",
        f"{simplified_agreement(rd):.2g} PAL (1% in r); {simplified_agreement(rd, 0.1):.2g} PAL (10%)",
        "Fig. 2 caption, SI p. 10")
    for label, d, level, stated in (("respiration (d_gamma)", g.D_GAMMA, 0.01, "0.01 PAL (Pasteur point)"),
                                    ("methanotrophy (d_delta)", g.D_DELTA, 2e-4, "2e-4 PAL; [O] = 2 uM")):
        frac = level * rd.pal_mol / (d + level * rd.pal_mol)
        add(f"{label} threshold", stated, f"half-saturation {d / rd.pal_mol:.3g} PAL; "
            f"{frac:.3f} saturated at the stated level", "p. 684, Methods",
            f"[O] at half-saturation = {g.ALPHA * d / g.MU * 1e6:.2f} uM; the source does not define the "
            f"threshold operationally; it equals half-saturation only if 1 PAL = {d / level:.3g} mol")
    add("escape coefficient s from Catling et al. (2001) eq. (1)", "3.7e-5 /yr (Goldblatt's later note)",
        f"{catling_s():.4g} /yr", "Catling et al. p. 839", f"R_E = {R_EARTH_CM / 1e5:.0f} km, MU = {g.MU:.4g} mol; "
        f"the figures were drawn with s = {g.S_PRINTED:.3g}")
    for beta_label in ("SI", "Fig. 3d"):
        for case, total in (("a", "3e18 mol"), ("c", "9e17 mol")):
            rdb, long, short = runs[("author_p", beta_label, case)]
            b = g.budget(long, rdb)
            tag = f"case {case} (beta {beta_label})"
            add(f"total oxidation, Fig. 3{'b' if case == 'a' else 'd'} (beta {beta_label})", total,
                f"{np.trapezoid(b['net'], long.t):.3g} mol; final O {long.O[-1]:.3g} mol", "Fig. 3 caption")
            tt = transition_times(short, rdb)
            add(f"transition time, {tag}", "150 kyr" if case == "a" else "50 kyr",
                "; ".join(f"{k}: {v / 1e3:.0f} kyr" for k, v in tt.items()), "p. 685",
                "the source does not define its clock")
            o = long.O / rdb.pal_mol
            at = lambda t: float(np.exp(np.interp(t, long.t, np.log(o))))
            ipk = int(np.argmax(o))
            add(f"oxygen after the switch, {tag}", "rises to ~0.08 PAL" if case == "a" else "rises, then falls back",
                f"{at(5e5):.3g} PAL at 0.5 Myr; {at(1e6):.3g} at 1 Myr; peak {o[ipk]:.4g} at {long.t[ipk] / 1e6:.1f} Myr; "
                f"{o[-1]:.4g} at 400 Myr", "p. 685, Fig. 3")
            if case == "a":
                add(f"time to 0.075 PAL, {tag}", "", f"{crossing(long.t, o, 0.075) / 1e6:.1f} Myr", "Fig. 3a")
            ev = methane_events(long, short, rdb)
            add(f"methane fall when O crosses 1e-5 PAL, {tag}", "factor 2-6",
                f"factor {ev['fall_cross']:.3f} at {ev['t_cross'] / 1e3:.0f} kyr "
                f"({long.M[0] / g.MU * 1e6:.2f} -> {ev['M_cross'] / g.MU * 1e6:.2f} ppm)", "p. 685")
            add(f"methane, first trough and run minimum, {tag}", "",
                f"first trough factor {ev['fall_first']:.3f} at {ev['t_first'] / 1e3:.0f} kyr; "
                f"minimum factor {ev['fall_min']:.3f} at {ev['t_min'] / 1e6:.1f} Myr", "Fig. 3")
            co2 = np.logspace(np.log10(KASTING_CO2[0]), np.log10(KASTING_CO2[1]), 301)
            dT = kasting_ts(long.M[0] / g.MU, co2) - kasting_ts(ev["M_cross"] / g.MU, co2)
            add(f"cooling at fixed CO2 when O crosses 1e-5 PAL, {tag}", "4-9 C (Kasting et al. 2001)",
                f"{dT.min():.2f}-{dT.max():.2f} K over pCO2 1e-5 to 1e-2 atm", "p. 685; Kasting et al. eq. 1",
                "0.8 solar luminosity; the fit is quoted to about 1 K")
            esc = b["escape"]
            late = np.where(np.abs(esc - long.r) > 0.1 * long.r)[0]
            add(f"methane re-adjustment (escape within 10% of r), {tag}",
                "about 50 Myr (case a)" if case == "a" else "recovers (case c)",
                f"{long.t[late.max() + 1] / 1e6:.1f} Myr" if late.size and late.max() + 1 < len(long.t) else "not within run",
                "p. 684")
            if case == "c":
                add(f"organic carbon increase after 400 Myr, {tag}", "3% over ~500 Myr",
                    f"{(long.C[-1] / long.C[0] - 1) * 100:.2f}%", "Fig. 3 caption")
    for r_up in (5.6e11, 6e11, 7.5e11, 1e12, 3e12):
        t = reverse_time(rd, r_up)
        add(f"reverse switch time, r stepped 7.5e10 -> {r_up:.2g}", "3-7 Myr",
            f"{t / 1e6:.2f} Myr" if np.isfinite(t) else "no switch", "p. 685",
            "the source does not state the reverse forcing; time to O < 1e-5 PAL")
    for case in ("a", "c"):
        p = vec[("3", f"{case}_zoom", "oxygen", "trace")]
        lo, hi = p[0, 1], p[-1, 1]
        t_of = lambda q: (T_STEP_GYR - (-crossing(-p[:, 0], p[:, 1], lo + q * (hi - lo)))) * 1e6
        add(f"printed transition, Fig. 3{case} zoom (log rise within the 1 Myr window)",
            "150 kyr" if case == "a" else "50 kyr",
            f"half: {t_of(0.5):.0f} kyr; 25-75%: {t_of(0.75) - t_of(0.25):.0f} kyr", "Fig. 3 zoom",
            "read from the published vertices, not the model")
        pm = vec[("3", f"{case}_zoom", "methane", "trace")]
        tx = -crossing(-p[:, 0], p[:, 1], -5.0)
        mx = np.interp(-tx, -pm[:, 0], pm[:, 1])
        add(f"printed methane fall when O crosses 1e-5 PAL, Fig. 3{case} zoom", "factor 2-6",
            f"factor {10 ** (pm[0, 1] - mx):.3f} at {(T_STEP_GYR - tx) * 1e6:.0f} kyr", "Fig. 3 zoom",
            "read from the published vertices")
    pc = vec[("3", "c", "oxygen", "trace")]
    add("printed peak oxygen, Fig. 3c", "", f"{10 ** pc[:, 1].max():.4g} PAL at {pc[np.argmax(pc[:, 1]), 0]:.3f} Gyr ago",
        "Fig. 3c", "read from the published vertices")
    for panel in ("b", "d"):
        lv = {c: (vec[("3", panel, c, "trace")][0, 1], vec[("3", panel + "_zoom", c, "trace")][0, 1])
              for c in ("input", "escape")}
        add(f"Fig. 3{panel} pre-step fluxes, main vs zoom panel", "input -3e11, escape 3e11",
            "; ".join(f"{c}: main {m:.3f}e11, zoom {z:.3f}e11" for c, (m, z) in lv.items()),
            f"Fig. 3{panel}", "the same quantities drawn in both panels")
    for pn in ("a", "a_zoom", "c", "c_zoom"):
        fr = F[("3", pn)]
        add(f"Fig. 3{pn} right axis: atm at 1 PAL", "0.2095 (O2 fraction)",
            f"{10 ** fr['right_at_left_zero']:.4f}", f"Fig. 3{pn}", "from the right-hand ticks")
    f0 = (0 - (-6)) / (0 - (-30))
    f1 = f0 * 1.03
    add("delta13C carbonate after 3% more burial", "f = 0.206, +0.23 permil",
        f"f = {f1:.4f}, {(-6 + f1 * 30) / (1 - f1):.3f} permil", "Methods")
    add("beta implied by Fig. 3d burial step", "not printed", f"{beta3d:.4g}", "Fig. 3d",
        f"SI-derived beta = {g.BETA_SI:.4g}")
    add("figure PAL offset (decades) for author_p", "PAL not printed", f"{pal_offset(vec, F, rd):+.4f}", "Fig. 2",
        f"zero means the figure's PAL is 0.2095 mu = {rd.pal_mol:.4g} mol")
    return rows


# ----------------------------------------------------------------- output

def overlay(vec, F, runs, path: Path) -> None:
    fig, ax = plt.subplots(2, 3, figsize=(13, 7))
    colours = {"faithful": "tab:red", "author_p": "tab:blue", "author_corrected": "tab:orange"}
    for k, ((panel, curve), (fixed, value)) in enumerate(FIG2_CASES.items()):
        a = ax[0, 0 if panel == "a" else 1]
        for q in printed2(vec, panel, curve):
            a.plot(q[:, 0], q[:, 1], ".", ms=2, color="k")
        val = CAPTION_R_TENFOLD if (panel, curve) == ("b", "dashed") else value
        for name, rd in g.READINGS.items():
            runs2, *_ = model2(rd, fixed, val, F[("2", panel)])
            for i, m in enumerate(runs2):
                a.plot(m[:, 0], m[:, 1], "-", lw=0.8, color=colours[name],
                       label=name if k in (0, 2) and i == 0 else None)
    ax[0, 0].set(xlabel="log10 r (mol O2 equiv./yr)", ylabel="log10 O2 (PAL)", title="Fig. 2a: N and N/2")
    ax[0, 1].set(xlabel="log10 N (mol O2/yr)", title="Fig. 2b: r = 7.5e10 and 3e11 (captioned 3e10)")
    ax[0, 0].legend(fontsize=7)
    for j, case in enumerate(("a", "c")):
        a = ax[1, j]
        fr = F[("3", case)]
        rd, long, _ = runs[("author_p", "Fig. 3d", case)]
        for curve, st in (("oxygen", "-"), ("methane", "--")):
            p = vec[("3", case, curve, "trace")]
            a.plot(p[:, 0], p[:, 1], ".", ms=2, color="k")
            for m in clip_runs(model3(rd, long, curve, fr), box(fr)):
                a.plot(m[:, 0], m[:, 1], st, lw=0.8, color="tab:blue")
        a.invert_xaxis()
        a.set(xlabel="Gyr ago", ylabel="log10 (PAL)", title=f"Fig. 3{case}: author_p, beta from Fig. 3d")
    a = ax[1, 2]
    fr = F[("3", "d")]
    rd, long, _ = runs[("author_p", "Fig. 3d", "c")]
    for curve in ("escape", "burial", "input", "net"):
        p = vec[("3", "d", curve, "trace")]
        a.plot(p[:, 0], p[:, 1], ".", ms=2, color="k")
        for i, m in enumerate(clip_runs(model3(rd, long, curve, fr), box(fr))):
            a.plot(m[:, 0], m[:, 1], "-", lw=0.8, label=curve if i == 0 else None)
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
    vec = V.load(outdir / V.OUT.name)
    F = frames(outdir / V.FRAMES.name)
    si = V.load(outdir / V.SI_OUT.name)
    beta3d = beta_from_fig3d(vec)
    write(outdir / "glw2006_fig2.csv", fig2_scores(vec, F))
    write(outdir / "glw2006_folds.csv", fold_rows(vec, {**g.READINGS, "si_fig_s3": si_reading(si)}))
    rows3, runs = fig3_scores(vec, F, beta3d)
    write(outdir / "glw2006_fig3.csv", rows3)
    write(outdir / "glw2006_si.csv", si_rows(si))
    write(outdir / "glw2006_claims.csv", claims(vec, F, runs, beta3d))
    overlay(vec, F, runs, outdir / "glw2006_overlay.png")


if __name__ == "__main__":
    main(*(Path(a) for a in sys.argv[1:]))
