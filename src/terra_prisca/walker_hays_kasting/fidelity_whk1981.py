"""Score the reconstruction of Walker, Hays & Kasting (1981) against the printed paper.

    uv run python -m terra_prisca.walker_hays_kasting.fidelity_whk1981 [pdf] [outdir]

Fig. 2: every printed curve (four V/V0 curves in each panel, and the broken
constant-P line) is traced from the scan and compared column by column with
eqs (2) and (6) evaluated at the same dTe, under the faithful reading, the
rejected readings and the null controls declared on the board (thread 170).
Fig. 1: the slope of the dashed Lagache line, the class segments, and the
runoff implied by Table 1's rates divided by Fig. 1a's concentrations.
Stated numbers: each figure the text gives, recomputed.

Writes to models/walker_hays_kasting/fidelity/ by default.
"""

from __future__ import annotations

import csv
import sys
from itertools import permutations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree

from terra_prisca.budyko_sellers.digitise import chamfer

from . import owen1979
from . import scan_whk1981 as scan_mod
from .whk1981 import (
    CONTROLS, FAITHFUL, READINGS, RUNOFF_EFOLD_K, TE0, TS0, Reading, arrhenius_efold,
    combined_efold, doubling_warming, dTe_from_luminosity, equilibrium, sensitivity,
)

V_RATIOS = (0.5, 1.0, 2.0, 4.0)
LOG10E = np.log10(np.e)

# Every reading and control scored on Fig. 2. "natural_log" is the faithful
# model with panel b read as ln P/P0; "no_change" is dT = 0 and P = P0.
ROWS = ["faithful", "unrounded", "no_runoff", "precip_runoff", "no_h2o", "natural_log",
        "no_feedback", "thermostat", "no_change"]
LABELS = {
    "faithful": "Faithful: eqs (2) and (6) as printed",
    "unrounded": "Constants unrounded (13.64 K, 4.093 K)",
    "no_runoff": "No runoff term (17.7 K)",
    "precip_runoff": "Runoff following precipitation (7.85 K)",
    "no_h2o": "No water-vapour amplification",
    "natural_log": "Panel b read as natural log",
    "no_feedback": "Null: no feedback (P = P0)",
    "thermostat": "Null: perfect thermostat (W independent of P)",
    "no_change": "Null: no change (dT = 0, P = P0)",
}


def reading(key: str) -> Reading | None:
    if key in READINGS:
        return READINGS[key]
    if key in CONTROLS:
        return CONTROLS[key]
    if key == "natural_log":
        return FAITHFUL
    return None


def predict(key: str, panel: str, v: float | None, dTe: np.ndarray) -> np.ndarray:
    """Model value at each dTe for one printed curve; v None is the broken line."""
    dTe = np.asarray(dTe, float)
    if key == "no_change":
        return np.zeros_like(dTe)
    r = reading(key)
    if v is None:  # constant-P line, panel a
        return r.te_gain * dTe
    out = np.empty_like(dTe)
    for i, x in enumerate(dTe):
        dT, p = equilibrium(float(x), v, r)
        if panel == "a":
            out[i] = dT
        elif not np.isfinite(p) or p <= 0:
            out[i] = np.nan
        else:
            out[i] = np.log(p) if key == "natural_log" else np.log10(p)
    return out


def changes(key: str, panel: str, v: float | None) -> bool:
    """Whether a reading alters this curve at all (it is scored only if so)."""
    if key == "faithful":
        return True
    if v is None:
        return key in ("no_h2o", "no_change")
    if key == "natural_log":
        return panel == "b"
    return True


def printed(sc) -> dict[tuple[str, float | None], np.ndarray]:
    out = {}
    for (p, v), pix in sc.curves.items():
        out[(p, v)] = scan_mod.column_trace(pix, sc.fig2[p])
    out[("a", None)] = scan_mod.column_trace(sc.broken, sc.fig2["a"], max_spread_px=14.0)
    return out


def score(trace: np.ndarray, pred: np.ndarray) -> dict:
    err = pred - trace[:, 1]
    ok = np.isfinite(err)
    e = err[ok]
    return dict(columns=int(ok.sum()), columns_unsupported=int((~ok).sum()),
                rmse=float(np.sqrt(np.mean(e ** 2))) if e.size else np.nan,
                median_abs=float(np.median(np.abs(e))) if e.size else np.nan,
                max_abs=float(np.max(np.abs(e))) if e.size else np.nan,
                bias=float(np.mean(e)) if e.size else np.nan, mask=ok)


def curve_name(p: str, v: float | None) -> str:
    return f"Fig. 2{p}, constant P" if v is None else f"Fig. 2{p}, V/V0 = {v:g}"


def fig2_scores(sc, traces) -> list[dict]:
    rows = []
    for (p, v), tr in traces.items():
        base = score(tr, predict("faithful", p, v, tr[:, 0]))
        for key in ROWS:
            if not changes(key, p, v):
                continue
            pred = predict(key, p, v, tr[:, 0])
            s = score(tr, pred)
            same = base["mask"] & s["mask"]
            fb = predict("faithful", p, v, tr[:, 0])[same] - tr[same, 1]
            rows.append(dict(curve=curve_name(p, v), reading=key, columns=s["columns"],
                             columns_unsupported=s["columns_unsupported"], rmse=s["rmse"],
                             median_abs=s["median_abs"], max_abs=s["max_abs"], bias=s["bias"],
                             faithful_rmse_same_columns=float(np.sqrt(np.mean(fb ** 2))) if fb.size else np.nan,
                             unit="K" if p == "a" else ("ln" if key == "natural_log" else "decades")))
    return rows


def fig2_chamfer(sc) -> list[dict]:
    """Two-way pixel distances between the faithful curves and the traced ink.

    Model samples are taken every 0.01 K of dTe inside the plot box (under
    0.5 px apart), and model-to-ink is measured at the samples themselves. Ink was
    deliberately removed in two places: the band of +-BAND_PX around the broken
    line (panel a solid curves) and the clipped tick boxes. Model samples lying
    there have no ink to meet by construction, so they are excluded from the
    model-to-ink score and counted. For the broken line, only samples within the
    rows its dashes span are used; the gaps between dashes stay in the score, so
    its model-to-ink fraction within 3 px measures the dash duty cycle, not fit.
    Ink-to-model uses every traced pixel."""
    rows = []
    grid = np.linspace(-20.5, 6.5, 2701)
    k, c = sc.broken_line
    for (p, v), pix in [*sc.curves.items(), (("a", None), sc.broken)]:
        fr = sc.fig2[p]
        y = predict("faithful", p, v, grid)
        m = fr.to_px(np.column_stack([grid, y]))
        x0, x1, y0, y1 = fr.box
        m = m[(m[:, 0] >= x0) & (m[:, 0] < x1) & (m[:, 1] >= y0) & (m[:, 1] < y1)]
        excluded = np.zeros(len(m), bool)
        if v is None:
            excluded |= (m[:, 1] < pix[:, 1].min()) | (m[:, 1] > pix[:, 1].max())
        elif p == "a":
            excluded |= np.abs(m[:, 0] - (k * m[:, 1] + c)) / np.hypot(1.0, k) <= scan_mod.BAND_PX
        if (p, v) in scan_mod.FIG2_CLIP:
            cx0, cx1, cy0, cy1 = scan_mod.FIG2_CLIP[(p, v)]
            excluded |= (m[:, 0] >= cx0) & (m[:, 0] < cx1) & (m[:, 1] >= cy0) & (m[:, 1] < cy1)
        _, to_model = chamfer(m, pix)
        to_ink = cKDTree(pix).query(m[~excluded])[0]  # at the samples, so no segment bridges a gap
        rows.append(dict(curve=curve_name(p, v),
                         model_samples=int(len(m)), model_samples_excluded=int(excluded.sum()),
                         model_to_ink_median_px=float(np.median(to_ink)),
                         model_to_ink_p95_px=float(np.percentile(to_ink, 95)),
                         model_within_3px=float(np.mean(to_ink <= 3.0)),
                         ink_px=len(pix),
                         ink_to_model_median_px=float(np.median(to_model)),
                         ink_to_model_p95_px=float(np.percentile(to_model, 95)),
                         ink_within_3px=float(np.mean(to_model <= 3.0))))
    return rows


def broken_line_fit(sc) -> dict:
    d = sc.fig2["a"].to_data(sc.broken)
    k, c = np.polyfit(d[:, 0], d[:, 1], 1)
    return dict(slope=float(k), intercept=float(c), n_px=len(d))


# Table 1 (Meybeck 1979), transcribed from the scan: rates in 1e6 g km-2 yr-1 of SiO2.
# (temperature class, runoff class in mm yr-1, name, rate, poorly determined)
TABLE1 = [
    ("<4", (120, 280), "tundra and taiga", 0.75, True),
    ("<4", (280, 630), "wet taiga", 1.6, False),
    ("<4", (630, None), "very wet taiga (high relief)", 5.75, False),
    ("4-15", (30, 120), "semi-arid temperate", 0.8, True),
    ("4-15", (120, 280), "temperate", 1.4, False),
    ("4-15", (280, 630), "wet temperate", 2.35, False),
    ("4-15", (630, None), "very wet temperate (high relief)", 10.0, True),
    ("15-25", (0, 30), "arid", 0.25, False),
    (">20", (30, 120), "mixed tropical", 2.35, False),
    (">20", (120, 280), "mixed tropical", 2.35, False),
    (">20", (280, 630), "wet tropical", 4.15, False),
    (">20", (630, None), "very wet tropical (plains)", 11.4, False),
    (">20", (630, None), "very wet tropical (mountains)", 16.4, False),
]


def fig1_table(sc) -> tuple[list[dict], list[dict]]:
    """Segment levels, and the runoff each Table 1 rate implies at the
    concentration printed for its class in Fig. 1a (1000 * rate / mg l-1, mm yr-1)."""
    segs = []
    for key, pix in sc.segments.items():
        x0, x1, lev = scan_mod.segment_level(pix, sc.fig1[key[0]])
        segs.append(dict(panel=key[0], temperature_class=key[1], segment=key[2],
                         x_start=x0, x_end=x1, log10_SiO2=lev, SiO2_mg_per_l=10 ** lev))
    # Candidate segments for each Table 1 cell: Fig. 1a segments of its
    # temperature class covering at least half its runoff class (to 800).
    cand = []
    for tclass, (r0, r1), name, rate, poor in TABLE1:
        lo, hi = r0, (r1 if r1 is not None else 800)
        cand.append([s for s in segs if s["panel"] == "a" and s["temperature_class"] == tclass
                     and min(hi, s["x_end"]) - max(lo, s["x_start"]) >= 0.5 * (hi - lo)])
    # Cells sharing a class whose candidates are the same set of n > 1 segments
    # are paired one-to-one; the paper does not say which goes with which, so
    # every pairing is reported, labelled. Otherwise each cell has one candidate.
    rows = []
    done = set()
    for i, (tclass, (r0, r1), name, rate, poor) in enumerate(TABLE1):
        if i in done:
            continue
        group = [j for j, (t, rc, *_ ) in enumerate(TABLE1) if t == tclass and rc == (r0, r1)]
        segs_i = cand[i]
        if len(group) > 1 and len(segs_i) == len(group):
            for n_pair, perm in enumerate(permutations(range(len(segs_i)))):
                label = "pairing " + "ABCDEF"[n_pair]
                for j, sidx in zip(group, perm):
                    rows.append(_implied_row(TABLE1[j], segs_i[sidx], label))
            done.update(group)
            continue
        if len(segs_i) != 1:
            raise ValueError(f"Table 1 cell {name} {r0}-{r1} has {len(segs_i)} candidate segments")
        rows.append(_implied_row(TABLE1[i], segs_i[0], "unique"))
    return segs, rows


def _implied_row(cell, seg, pairing) -> dict:
    tclass, (r0, r1), name, rate, poor = cell
    implied = 1000.0 * rate / seg["SiO2_mg_per_l"]
    inside = implied >= r0 and (r1 is None or implied <= r1)
    return dict(temperature_class=tclass, runoff_class=f"{r0}-{r1}" if r1 else f">{r0}",
                name=name, rate=rate, poorly_determined=poor, segment=seg["segment"], pairing=pairing,
                log10_SiO2=seg["log10_SiO2"], implied_runoff_mm=implied, inside_class=inside)


def lagache_fit(sc) -> dict:
    d = sc.fig1["b"].to_data(sc.lagache)
    k, c = np.polyfit(d[:, 0], d[:, 1], 1)
    return dict(slope=float(k), intercept=float(c), n_px=len(d),
                efold_implied_K=float(LOG10E / k),
                slope_17_7=LOG10E / 17.7, slope_13_7=LOG10E / 13.7, slope_ln_17_7=1 / 17.7)


def numbers() -> list[dict]:
    rows = []

    def add(q, text, recon, note=""):
        rows.append(dict(quantity=q, text=text, reconstruction=recon, note=note))

    direct = arrhenius_efold()
    add("Direct e-folding of weathering, T^2/4600 at 285 K", "17.7 K", f"{direct:.2f} K")
    add("Combined e-folding, direct and runoff (60 K)", "13.7 K",
        f"{combined_efold(17.7, RUNOFF_EFOLD_K):.2f} K (from 17.7); {combined_efold(direct, RUNOFF_EFOLD_K):.2f} K (unrounded)")
    add("e-folding of P in eq. (2), 0.3 x 13.7", "4.11 K", f"{0.3 * 13.7:.3f} K")
    add("Exponent of V/V0 in eq. (2), 1/0.3", "10/3", f"{1 / 0.3:.4f}")
    add("Eq. (6) coefficient of dTe, 1/(1 - 0.5)", "2", f"{FAITHFUL.te_gain:g}")
    add("Eq. (6) CO2 coefficient, 2.3/(1 - 0.5)", "4.6", f"{FAITHFUL.gh_amp:g}")
    add("Eq. (3) today: Te + Tg(H2O) + Tg(CO2)", "285 K", f"{253 + 29.7 + 2.3:.1f} K", "closes exactly")
    add("Warming for doubled CO2, eq. (6)", "1.3 K", f"{doubling_warming():.3f} K")
    d25 = float(dTe_from_luminosity(0.75))
    add("dTe for a 25% fainter Sun, Te ~ L^(1/4)", "-18 K", f"{d25:.2f} K")
    dT18, p18 = equilibrium(-18.0, 1.0)
    dT25, p25 = equilibrium(d25, 1.0)
    add("dT at dTe = -18 K, V/V0 = 1", "-18 K", f"{dT18:.2f} K ({dT25:.2f} K at dTe = {d25:.2f})")
    add("Surface temperature at that point", "265 K", f"{TS0 + dT18:.2f} K ({TS0 + dT25:.2f} K)",
        "285 - 18 = 267; the text's 265 K disagrees with its own -18 K")
    te265 = float(np.interp(-20.0, [equilibrium(x, 1.0)[0] for x in np.arange(-25, -15, 0.01)],
                            np.arange(-25, -15, 0.01)))
    add("dTe that would give T = 265 K at V/V0 = 1", "-", f"{te265:.2f} K (luminosity {(1 + te265 / 253) ** 4:.3f})")
    add("Feedback reduces the change by about a half (V/V0 = 1)", "about 1/2",
        "; ".join(f"dT/(2 dTe) = {equilibrium(x, 1.0)[0] / (2 * x):.3f} at dTe = {x:g}" for x in (-18, -10, -2)),
        f"local slope at today: {sensitivity(0.0) / 2:.3f} of the no-feedback slope")
    add("P/P0 at dTe = -18 K, V/V0 = 1", "-", f"{p18:.1f}")
    keep285 = (1 + 36 / 4.6) ** (1 / 0.364)
    keep285_exact = (1 - 2 * d25 / 4.6) ** (1 / 0.364)
    ow = owen1979.TABLE1[0]
    dte_owen = TE0 * ((ow[1] / owen1979.S0) ** 0.25 - 1.0)
    keep_owen = (1 - 2 * dte_owen / 4.6) ** (1 / 0.364)
    add("P/P0 that holds dT = 0, eq. (6)", "'up to 1000 times' (WHK's summary of Owen et al. 1979)",
        f"{keep285:.0f} at dTe = -18 K (paper's rounding); {keep285_exact:.0f} at dTe = {d25:.2f} K (exact 25%)",
        f"Owen et al.'s Table 1 gives P/P0 = {ow[2] / owen1979.P0_BAR:.0f} at {ow[1] / owen1979.S0:.0%} of today's sunlight "
        f"(dTe = {dte_owen:.1f} K) with Ts = {ow[3]} K, a warm state; eq. (6) needs {keep_owen:.0f} there to hold dT = 0")
    holland = 3.3e14
    add("Fluid carbon implied by doubling in 400 kyr", "-", f"{holland * 4e5:.2e} g CO2 = {holland * 4e5 * 12 / 44:.2e} g C")
    bar = 1e5 * 5.10e14 / 9.81 * 1e3  # g of CO2 in a 1-bar column over the Earth
    add("Time to accumulate 1 bar of CO2 at 3.3(+-1.1)e14 g/yr", "20 Myr",
        f"{bar / holland / 1e6:.1f} Myr ({bar / 4.4e14 / 1e6:.1f}-{bar / 2.2e14 / 1e6:.1f})",
        "area 5.10e14 m2, g = 9.81 m s-2")
    add("Sellers (1965) precipitation e-folding vs Clausius-Clapeyron at 285 K", "14.1 K",
        f"{285.0 ** 2 * 461.5 / 2.47e6:.1f} K", "not used in eq. (1)")
    return rows


def claims() -> list[dict]:
    """The paper's qualitative statements about the model, tested on a grid."""
    grid = np.arange(-20.0, 6.01, 0.5)
    rows = []

    def add(claim, ok, detail):
        rows.append(dict(claim=claim, holds=bool(ok), detail=detail))

    p = {v: np.array([equilibrium(x, v)[1] for x in grid]) for v in V_RATIOS}
    s = {v: np.array([sensitivity(x, v) for x in grid]) for v in V_RATIOS}
    add("Larger V gives more CO2", all(np.all(p[a] < p[b]) for a, b in zip(V_RATIOS, V_RATIOS[1:])),
        "P/P0 increases with V/V0 at every dTe on the grid")
    add("Larger V gives stronger feedback", all(np.all(s[a] > s[b]) for a, b in zip(V_RATIOS, V_RATIOS[1:])),
        f"d(dT)/d(dTe) at dTe = -10: " + ", ".join(f"V={v:g}: {sensitivity(-10, v):.3f}" for v in V_RATIOS))
    add("Curvature: weaker feedback at lower P (higher dTe)", all(np.all(np.diff(s[v]) > 0) for v in V_RATIOS),
        f"V/V0 = 1: slope {s[1.0][0]:.3f} at dTe = -20, {s[1.0][-1]:.3f} at +6; no-feedback slope 2")
    expo = [0.2, 0.3, 0.4]
    sens = [[sensitivity(x, 1.0, Reading(co2_exponent=e, p_efold_K=None, v_exponent=None)) for x in (-15, -5, 3)]
            for e in expo]
    add("A weaker P dependence of weathering gives stronger feedback",
        all(sens[0][i] < sens[1][i] < sens[2][i] for i in range(3)),
        "slope at dTe = -15, -5, +3 for exponents 0.2/0.3/0.4: "
        + "; ".join("/".join(f"{sens[j][i]:.3f}" for j in range(3)) for i in range(3)))
    ef = [READINGS["precip_runoff"], READINGS["faithful"], READINGS["no_runoff"]]
    se = [sensitivity(-10, 1.0, r) for r in ef]
    add("A stronger runoff dependence on temperature buffers more", se[0] < se[1] < se[2],
        f"slope at dTe = -10 for e-folding 7.85/13.7/17.7 K: {se[0]:.3f}/{se[1]:.3f}/{se[2]:.3f}")
    add("Te and V uniquely determine T and P", True,
        "g(dT) = dT - eq.(6)(eq.(2)(dT)) is strictly increasing, so the root is unique (tested)")
    return rows


def overlay(traces, sc, lag, segs, path: Path) -> None:
    fig, ax = plt.subplots(1, 3, figsize=(14, 5.2))
    grid = np.linspace(-20, 5.8, 400)
    for i, p in enumerate("ab"):
        a = ax[i]
        for (pp, v), tr in traces.items():
            if pp != p:
                continue
            a.plot(tr[:, 0], tr[:, 1], ".", ms=1.5, color="0.55")
            a.plot(grid, predict("faithful", p, v, grid), "C3-", lw=0.9)
        a.set_xlim(-20, 5.8)
        a.set_xlabel("dTe (K)")
    ax[0].set_ylim(-20, 10)
    ax[0].set_ylabel("dT (K)")
    ax[0].set_title("Fig. 2a: digitised (grey), reconstruction (red)", fontsize=9)
    ax[1].set_ylim(-1, 2.62)
    ax[1].set_ylabel("log10 P/P0")
    ax[1].set_title("Fig. 2b", fontsize=9)
    a = ax[2]
    d = sc.fig1["b"].to_data(sc.lagache)
    a.plot(d[:, 0], d[:, 1], ".", ms=1, color="0.55", label="Lagache dashes (digitised)")
    t = np.linspace(-2.5, 27.5, 10)
    a.plot(t, lag["intercept"] + lag["slope"] * t, "0.3", lw=0.6, label=f"fit, slope {lag['slope']:.4f}")
    a.plot(t, lag["intercept"] + lag["slope_17_7"] * t, "C3-", lw=0.9, label="slope from 17.7 K")
    a.plot(t, lag["intercept"] + lag["slope_13_7"] * t, "C0--", lw=0.8, label="slope from 13.7 K")
    for s in segs:
        if s["panel"] == "b":
            a.plot([s["x_start"], s["x_end"]], [s["log10_SiO2"]] * 2, "k-", lw=1.2)
    a.set_xlim(-2.5, 27.5)
    a.set_ylim(0.5, 1.31)
    a.set_xlabel("temperature (deg C)")
    a.set_ylabel("log10 SiO2 (mg/l)")
    a.set_title("Fig. 1b: class segments and Lagache slope", fontsize=9)
    a.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=110, metadata={"Software": None})
    plt.close(fig)


def _fmt(v):
    if isinstance(v, (bool, np.bool_)):
        return str(bool(v))
    if isinstance(v, float):
        return "" if np.isnan(v) else f"{v:.6g}"
    return v


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: _fmt(v) for k, v in r.items()})


def main(pdf: Path, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    owen1979.main(outdir)
    sc = scan_mod.load(pdf)
    traces = printed(sc)
    write(outdir / "whk1981_fidelity.csv", fig2_scores(sc, traces))
    write(outdir / "whk1981_chamfer.csv", fig2_chamfer(sc))
    bl = broken_line_fit(sc)
    lag = lagache_fit(sc)
    segs, implied = fig1_table(sc)
    write(outdir / "whk1981_fig1_segments.csv", segs)
    write(outdir / "whk1981_fig1_implied_runoff.csv", implied)
    calib = [dict(figure=f"Fig. 2{p}", residual_rel=f.residual, px_per_unit_x=f.px_per_unit()[0],
                  px_per_unit_y=f.px_per_unit()[1]) for p, f in sc.fig2.items()]
    calib += [dict(figure=f"Fig. 1{p}", residual_rel=f.residual, px_per_unit_x=f.px_per_unit()[0],
                   px_per_unit_y=f.px_per_unit()[1]) for p, f in sc.fig1.items()]
    write(outdir / "whk1981_calibration.csv", calib)
    lines = [dict(line="Fig. 2a broken line", quantity="slope dT/dTe", printed=bl["slope"], model=FAITHFUL.te_gain),
             dict(line="Fig. 2a broken line", quantity="intercept (K)", printed=bl["intercept"], model=0.0),
             dict(line="Fig. 1b Lagache line", quantity="slope (decades per K)", printed=lag["slope"],
                  model=lag["slope_17_7"]),
             dict(line="Fig. 1b Lagache line", quantity="implied e-folding (K)", printed=lag["efold_implied_K"],
                  model=17.7),
             dict(line="Fig. 1b Lagache line", quantity="slope if 13.7 K", printed=lag["slope"], model=lag["slope_13_7"]),
             dict(line="Fig. 1b Lagache line", quantity="slope if natural log, 17.7 K", printed=lag["slope"],
                  model=lag["slope_ln_17_7"])]
    write(outdir / "whk1981_lines.csv", lines)
    write(outdir / "whk1981_numbers.csv", numbers())
    write(outdir / "whk1981_claims.csv", claims())
    pts = []
    for (p, v), tr in traces.items():
        for x, y in tr:
            pts.append(dict(curve=curve_name(p, v), dTe=round(float(x), 4), value=round(float(y), 4)))
    write(outdir / "whk1981_printed_curves.csv", pts)
    overlay(traces, sc, lag, segs, outdir / "whk1981_overlay.png")


if __name__ == "__main__":
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else scan_mod.DEFAULT_PDF
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("models/walker_hays_kasting/fidelity")
    main(pdf, out)
