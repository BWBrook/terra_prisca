"""Caldeira & Kasting (1992) scored against the printed Fig. 2 and the text.

    uv run python -m terra_prisca.biosphere_lifespan.fidelity_ck1992 [pdf] [outdir]

Writes, to models/biosphere_lifespan/fidelity/:
  ck1992_calibration.csv  scale fits and tick residuals
  ck1992_fidelity.csv     each printed curve against each reading: column error
                          in data units on the curve's shallow stretches
  ck1992_two_way.csv      two-way pixel distances, model to traced centres and back
  ck1992_events.csv       printed and reconstructed values at the figure's features
  ck1992_coupled.csv      each alternative reading with the SO2 factor refitted under it
  ck1992_claims.csv       the text's numerical claims against the reconstruction
  ck1992_overlay.png      traced points (never the scan) with the faithful model
"""

from __future__ import annotations

import csv
import sys
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from terra_prisca.budyko_sellers.digitise import densify
from terra_prisca.walker_hays_kasting import whk1981

from . import ck1992 as m
from . import lw1982
from . import scan_ck1992 as s

OUT = Path("models/biosphere_lifespan/fidelity")
STEP = 0.0025  # Gyr between model samples (about 0.19 px)
SHALLOW = 2.0  # px/px: column errors only where the trace is flatter than this

SENSITIVITY = {
    "dT_minus_0.5": replace(m.FAITHFUL, name="eq. (4) - 0.5 K (its stated mean error)", dT_offset=-0.5),
    "dT_plus_0.5": replace(m.FAITHFUL, name="eq. (4) + 0.5 K", dT_offset=0.5),
    "albedo_plus_0.01": replace(m.FAITHFUL, name="eq. (5) + 0.01 (its stated mean error)", albedo_offset=0.01),
}
SCORED = {**m.READINGS, **m.CONTROLS, **SENSITIVITY}


def gough_ratio(t):
    """Gough (1981) eq. (1), future t (Gyr) from today, Sun age 4.7 Gyr: a null for S/S0."""
    return 1.0 / (1.0 - 0.4 * np.asarray(t, float) / 4.7)


def lw_ratio(t):
    """Lovelock & Whitfield's straight Sun line: a null for S/S0."""
    return lw1982.luminosity(np.asarray(t, float) * 1000.0)


SUN_NULLS = {"Gough (1981)": gough_ratio, "Lovelock & Whitfield straight line": lw_ratio}


@lru_cache(maxsize=None)
def model(r: m.Reading) -> dict[str, np.ndarray]:
    tr = m.trajectory(np.arange(0.0, 1.6 + STEP / 2, STEP), r)
    tr["log_P_atm"] = np.log10(tr["P_atm_ppm"])
    tr["log_P_soil"] = np.log10(tr["P_soil_ppm"])
    for k in ("T_K", "Pi_ratio", "log_P_atm", "log_P_soil"):
        tr[k] = np.where(tr["in_fit"], tr[k], np.nan)
    return tr


MODEL_KEY = {"P_soil": "log_P_soil", "P_atm": "log_P_atm", "merged": "log_P_atm",
             "S_ratio": "S_ratio", "Pi_ratio": "Pi_ratio", "T_K": "T_K"}
CURVES = ("P_soil", "P_atm", "merged", "S_ratio", "Pi_ratio", "T_K")
UNITS = {"P_soil": "log10 ppm", "P_atm": "log10 ppm", "merged": "log10 ppm",
         "S_ratio": "S/S0", "Pi_ratio": "Pi/Pi0", "T_K": "K"}


@lru_cache(maxsize=None)
def _traces(pdf: Path) -> tuple:
    sc = s.load(pdf)
    return sc, {c: s.trace(sc, c) for c in CURVES}


def traced(sc: s.Scan, tr: dict) -> dict[str, np.ndarray]:
    return {c: sc.to_data(c, tr[c].centres) for c in CURVES}


def _shallow(sc: s.Scan, curve: str, px: np.ndarray) -> np.ndarray:
    p = sc.panels[s.CURVE_AXES[curve][0]]
    u, v = p.u(*px.T), p.v(*px.T)
    du, dv = np.gradient(u), np.gradient(v)
    return np.abs(dv) < SHALLOW * np.abs(du)


def _model_values(curve: str, t: np.ndarray, r) -> np.ndarray:
    if callable(r):
        return r(t)
    mo = model(r)
    return np.interp(t, mo["t_Gyr"], mo[MODEL_KEY[curve]], left=np.nan, right=np.nan)


def _candidates(curve: str) -> dict:
    out = {k: r for k, r in SCORED.items() if not (curve == "P_soil" and r.weathering == "whk")}
    if curve == "S_ratio":
        out = {"faithful": m.FAITHFUL, **SUN_NULLS}
    return out


def scores(pdf: Path = s.DEFAULT_PDF) -> list[dict]:
    sc, tr = _traces(pdf)
    data = traced(sc, tr)
    rows = []
    for curve in CURVES:
        d = data[curve]
        keep = _shallow(sc, curve, tr[curve].centres)
        for key, r in _candidates(curve).items():
            y = _model_values(curve, d[:, 0], r)
            ok = keep & np.isfinite(y)
            res = d[ok, 1] - y[ok]
            rows.append({"curve": curve, "reading": key, "units": UNITS[curve],
                         "points": int(len(d)), "used": int(ok.sum()),
                         "no_model_value": int((keep & ~np.isfinite(y)).sum()),
                         "rmse": float(np.sqrt(np.mean(res ** 2))) if ok.any() else np.nan,
                         "bias": float(res.mean()) if ok.any() else np.nan,
                         "max_abs": float(np.abs(res).max()) if ok.any() else np.nan})
    return rows


def _model_px(sc: s.Scan, curve: str, r, t_lo: float, t_hi: float) -> np.ndarray:
    if callable(r):
        t = np.arange(t_lo, t_hi + 1e-12, STEP)
        y = r(t)
    else:
        mo = model(r)
        sel = (mo["t_Gyr"] >= t_lo) & (mo["t_Gyr"] <= t_hi)
        t, y = mo["t_Gyr"][sel], mo[MODEL_KEY[curve]][sel]
    ok = np.isfinite(y)
    if ok.sum() < 2:
        return np.empty((0, 2))
    px = sc.to_px(curve, np.column_stack([t[ok], y[ok]]))
    return densify(px, 0.25)


def two_way(pdf: Path = s.DEFAULT_PDF) -> list[dict]:
    """Distances between the model curve, drawn on the scan's calibrated axes,
    and the traced centres. Model samples inside excluded boxes or frame
    margins are dropped (the trace has no points there); no gap is bridged."""
    sc, tr = _traces(pdf)
    data = traced(sc, tr)
    pname = {c: s.CURVE_AXES[c][0] for c in CURVES}
    rows = []
    for curve in CURVES:
        ink = tr[curve].centres
        t_lo, t_hi = data[curve][:, 0].min(), data[curve][:, 0].max()
        for key, r in _candidates(curve).items():
            mp = _model_px(sc, curve, r, t_lo, t_hi)
            if not len(mp):
                continue
            keep = np.array([s._excluded(x, y, sc, pname[curve]) is None for x, y in mp])
            mk = mp[keep]
            if not len(mk):  # the whole model curve lies in excluded boxes or frame margins
                to_model = cKDTree(mp).query(ink)[0]
                rows.append({"curve": curve, "reading": key, "model_samples": 0,
                             "model_samples_excluded": int((~keep).sum()), "trace_points": int(len(ink)),
                             "trace_to_model_median_px": float(np.median(to_model)),
                             "trace_to_model_p95_px": float(np.percentile(to_model, 95))})
                continue
            to_ink = cKDTree(ink).query(mk)[0]
            to_model = cKDTree(mp).query(ink)[0]
            gaps = np.hypot(*np.diff(mp, axis=0).T)
            rows.append({"curve": curve, "reading": key, "model_samples": int(keep.sum()),
                         "model_samples_excluded": int((~keep).sum()), "trace_points": int(len(ink)),
                         "max_model_spacing_px": float(gaps.max()),
                         "model_to_trace_median_px": float(np.median(to_ink)),
                         "model_to_trace_p95_px": float(np.percentile(to_ink, 95)),
                         "trace_to_model_median_px": float(np.median(to_model)),
                         "trace_to_model_p95_px": float(np.percentile(to_model, 95))})
    return rows


def _fit_at(d: np.ndarray, sel: np.ndarray, x: float) -> float:
    k, c = np.polyfit(d[sel, 0], d[sel, 1], 1)
    return float(k * x + c)


def _first_t(d: np.ndarray, level: float) -> float:
    """First time a traced curve (ordered along its length) passes level."""
    y = d[:, 1] - level
    i = np.nonzero(np.sign(y[1:]) != np.sign(y[:-1]))[0]
    if not i.size:
        return np.nan
    j = i[0]
    return float(d[j, 0] + (d[j + 1, 0] - d[j, 0]) * (-y[j]) / (y[j + 1] - y[j]))


def printed_events(pdf: Path = s.DEFAULT_PDF) -> dict[str, float]:
    sc, tr = _traces(pdf)
    d = traced(sc, tr)
    early = {c: d[c][:, 0] < 0.08 for c in ("P_atm", "P_soil", "Pi_ratio", "T_K", "S_ratio")}
    pa, mg = d["P_atm"], d["merged"]
    ka, ca = np.polyfit(pa[pa[:, 0] > 0.7, 0], pa[pa[:, 0] > 0.7, 1], 1)
    km, cm = np.polyfit(mg[mg[:, 0] < 0.92, 0], mg[mg[:, 0] < 0.92, 1], 1)
    t_kink = (cm - ca) / (ka - km)
    late = mg[:, 0] > mg[-1, 0] - 0.04
    kl, cl = np.polyfit(mg[late, 0], mg[late, 1], 1)
    T = d["T_K"]
    return {
        "P_atm_ppm at t=0": 10 ** _fit_at(d["P_atm"], early["P_atm"], 0.0),
        "P_soil_ppm at t=0": 10 ** _fit_at(d["P_soil"], early["P_soil"], 0.0),
        "Pi_ratio at t=0": _fit_at(d["Pi_ratio"], early["Pi_ratio"], 0.0),
        "T_K at t=0": _fit_at(T, early["T_K"], 0.0),
        "S_ratio at t=1.6": _fit_at(d["S_ratio"], d["S_ratio"][:, 0] > 1.4, 1.6),
        "kink in P_atm, t Gyr": float(t_kink),
        "kink in P_atm, ppm": float(10 ** (ka * t_kink + ca)),
        "P_atm reaches 1 ppm, t Gyr": float(-cl / kl),
        "Pi_ratio falls to 0.05, t Gyr": _first_t(d["Pi_ratio"], 0.05),
        "T at 0.9 Gyr, K": float(np.interp(0.9, T[:, 0], T[:, 1])),
        "T reaches 300 K, t Gyr": _first_t(T, 300.0),
        "T reaches 323.15 K, t Gyr": _first_t(T, 323.15),
        "T reaches 353.15 K, t Gyr": _first_t(T, 353.15),
        "T reaches 363.15 K, t Gyr": _first_t(T, 363.15),
        "T reaches 370 K, t Gyr": _first_t(T, 370.0),
    }


def _cross(t: np.ndarray, y: np.ndarray, j: int, level: float) -> float:
    return float(t[j - 1] + (t[j] - t[j - 1]) * (y[j - 1] - level) / (y[j - 1] - y[j]))


def model_events(r: m.Reading = m.FAITHFUL) -> dict[str, float]:
    mo = model(r)
    s0 = m.state(0.0, r)
    t = mo["t_Gyr"]
    pi = mo["Pi_ratio"]
    i = np.nonzero(pi <= 0.05)[0]
    return {
        "P_atm_ppm at t=0": s0["P_atm_ppm"],
        "P_soil_ppm at t=0": s0["P_soil_ppm"],
        "Pi_ratio at t=0": s0["Pi_ratio"],
        "T_K at t=0": s0["T_K"],
        "S_ratio at t=1.6": float(m.solar(1.6, r)) / m.S0,
        "kink in P_atm, t Gyr": m.co2_time(r.p_min, r),
        "kink in P_atm, ppm": r.p_min * 1e6,
        "P_atm reaches 1 ppm, t Gyr": m.co2_time(r.p_floor, r),
        "Pi_ratio falls to 0.05, t Gyr": _cross(t, pi, i[0], 0.05) if i.size else np.nan,
        "T at 0.9 Gyr, K": m.state(0.9, r)["T_K"],
        "T reaches 300 K, t Gyr": m.temperature_time(300.0, r),
        "T reaches 323.15 K, t Gyr": m.temperature_time(323.15, r),
        "T reaches 353.15 K, t Gyr": m.temperature_time(353.15, r),
        "T reaches 363.15 K, t Gyr": m.temperature_time(363.15, r),
        "T reaches 370 K, t Gyr": m.temperature_time(370.0, r),
    }


def fit_so2_factor(pdf: Path = s.DEFAULT_PDF, base: m.Reading = m.FAITHFUL) -> float:
    """SO2 factor at which the model's 10 ppm kink falls at the printed kink."""
    from scipy.optimize import brentq

    target = printed_events(pdf)["kink in P_atm, t Gyr"]
    return brentq(lambda x: m.co2_time(m.P_MIN_C4, replace(base, so2_factor=x)) - target, 0.05, 1.5, xtol=1e-6)


COUPLED_BASES = {"faithful": m.FAITHFUL, "t0_printed": m.READINGS["t0_printed"],
                 "chemistry_T": m.READINGS["chemistry_T"], "volk_p_half": m.READINGS["volk_p_half"]}
OUT_OF_SAMPLE = ("Pi_ratio at t=0", "P_atm reaches 1 ppm, t Gyr", "Pi_ratio falls to 0.05, t Gyr",
                 "T reaches 300 K, t Gyr", "T at 0.9 Gyr, K")


def coupled(pdf: Path = s.DEFAULT_PDF) -> list[dict]:
    """Each alternative choice with the SO2 factor refitted to the kink under it,
    so that no alternative is judged against a base that misses the low-CO2
    phase. The kink is fitted; every column after so2_share is a test."""
    pr = printed_events(pdf)
    sc, tr = _traces(pdf)
    rows = []
    for key, base in COUPLED_BASES.items():
        fac = fit_so2_factor(pdf, base)
        r = replace(base, name=f"{key}, SO2 refitted", so2_factor=fac)
        ev = model_events(r)
        row = {"base": key, "so2_factor": fac, "so2_share": m.so2_share(r)}
        for k in OUT_OF_SAMPLE:
            row[f"{k} (printed {pr[k]:.4g})"] = ev[k]
        data = traced(sc, tr)
        for c in CURVES:
            if c == "S_ratio":
                continue
            ink = tr[c].centres
            t_lo, t_hi = data[c][:, 0].min(), data[c][:, 0].max()
            mp = _model_px(sc, c, r, t_lo, t_hi)
            keep = np.array([s._excluded(x, y, sc, s.CURVE_AXES[c][0]) is None for x, y in mp])
            row[f"{c} median px"] = float(np.median(cKDTree(ink).query(mp[keep])[0]))
            row[f"{c} p95 px"] = float(np.percentile(cKDTree(mp).query(ink)[0], 95))
        rows.append(row)
    return rows


EVENT_READINGS = {"faithful": m.FAITHFUL, "so2_fitted": m.READINGS["so2_fitted"], "t0_printed": m.READINGS["t0_printed"],
                  "so2_half": m.READINGS["so2_half"], "chemistry_T": m.READINGS["chemistry_T"],
                  "dT_minus_0.5": SENSITIVITY["dT_minus_0.5"]}


def events(pdf: Path = s.DEFAULT_PDF) -> list[dict]:
    pr = printed_events(pdf)
    mod = {k: model_events(r) for k, r in EVENT_READINGS.items()}
    return [{"feature": f, "printed": v, **{k: mod[k][f] for k in mod}} for f, v in pr.items()]


def calibration(pdf: Path = s.DEFAULT_PDF) -> list[dict]:
    sc, _ = _traces(pdf)
    rows = [{"item": f"{p} frame slopes", "kh": sc.panels[p].kh, "kv": sc.panels[p].kv} for p in sc.panels]
    for (p, a), ax in sc.axes.items():
        rows.append({"item": f"{p} {a}", "units_per_px": ax.slope, "max_tick_residual_px": ax.residual,
                     "ticks": len(s.AXES[(p, a)].values)})
    for c in CURVES:
        t = _traces(pdf)[1][c]
        rows.append({"item": f"trace {c}", "points": len(t.centres), "dropped": len(t.dropped),
                     "dropped_by": "; ".join(f"{k}={v}" for k, v in sorted(t.reasons.items()))})
    return rows


def claims() -> list[dict]:
    rate_now = m.SUN_COEFF / (m.TAU0_GYR * 1000.0) * m.S0
    rate_09 = (float(m.solar(0.9)) - m.S0) / 900.0
    lw = lw1982.FAITHFUL
    a, b = lw.c_now ** 0.5, lw.c_past ** 0.5
    lw_zero = 1.0 + (float(lw1982.luminosity(lw.t_past)) - 1.0) * (-a) / (b - a)
    a0 = float(m.albedo(m.t0()))
    trap = lambda k: (1.0 - a0) * (k - 1.0) * m.S0 / 4.0
    c3 = m.C3
    fit = m.READINGS["so2_fitted"]
    c3_fit = replace(fit, p_min=m.P_MIN_C3)
    t50, t100 = m.temperature_time(323.15), m.temperature_time(373.15)
    ocean_kg, earth_cm2 = 1.4e21, 4 * np.pi * (6.371e8) ** 2
    h_atoms = 2 * ocean_kg * 1e3 / 18.015 * 6.02214e23 / earth_cm2
    t50_low = m.first_crossing(lambda t: m.temperature(float(m.solar(t)), m.P_FIT[0]), 323.15)
    T09 = m.state(0.9)["T_K"] - m.state(0.0)["T_K"]
    return [
        {"claim": "WHK's weathering implies an exponent 0.6 on aH", "printed": 0.6,
         "reconstructed": whk1981.FAITHFUL.co2_exponent / 0.5,
         "note": "WHK P^0.3 with aH ~ P^0.5 gives aH^0.6"},
        {"claim": "S rises at ~0.12 W m-2 Myr-1 (eq. 1)", "printed": 0.12, "reconstructed": rate_now,
         "note": f"today; the mean over the next 0.9 Gyr is {rate_09:.4f}"},
        {"claim": "C&K's reading of L&W: sqrt(P) falls to zero at S = 1.017 S0", "printed": 1.017,
         "reconstructed": lw_zero, "note": "zero of the faithful L&W rule (lw1982), 70,000 ppm anchor"},
        {"claim": "L&W imply only ~4 W m-2 of trapping by 320 ppm", "printed": 4.0, "reconstructed": trap(1.017),
         "note": f"(1 - a0)(0.017) S0/4 with a0 = {a0:.4f} from eq. (5); {trap(lw_zero):.2f} with the reconstructed zero"},
        {"claim": "C3-only world (Pmin = 150 ppm): ~0.5 Gyr", "printed": 0.5, "reconstructed": m.co2_time(m.P_MIN_C3, c3), "so2_fitted": m.co2_time(m.P_MIN_C3, c3_fit),
         "note": f"separate run, P_half recalibrated to {m.p_half(c3) * 1e6:.1f} ppm; the C4 run passes 150 ppm at {m.co2_time(m.P_MIN_C3):.3f} Gyr"},
        {"claim": "C4 limit (Pmin = 10 ppm): 0.9 Gyr", "printed": 0.9, "reconstructed": m.co2_time(m.P_MIN_C4), "so2_fitted": m.co2_time(m.P_MIN_C4, fit),
         "note": "the printed kink is in ck1992_events.csv"},
        {"claim": "Patm reaches 1 ppm after ~1 Gyr", "printed": 1.0, "reconstructed": m.co2_time(m.P_FLOOR),
         "so2_fitted": m.co2_time(m.P_FLOOR, fit), "note": ""},
        {"claim": "constant temperature for the next 0.9 Gyr", "printed": 0.9, "reconstructed": T09,
         "so2_fitted": m.state(0.9, fit)["T_K"] - m.state(0.0, fit)["T_K"],
         "note": f"T rises by this many K over 0.9 Gyr in the faithful run; held literally at T0, CO2 must reach 10 ppm by {m.constant_T_time(10e-6):.3f} Gyr and 1 ppm by {m.constant_T_time(1e-6):.3f} Gyr"},
        {"claim": "with negligible CO2, T exceeds 50 C after ~1.5 Gyr", "printed": 1.5, "reconstructed": t50_low,
         "note": f"Patm = 0.01 ppm (the fit's lower bound); at the 1 ppm floor, {t50:.3f} Gyr"},
        {"claim": "T passes 80 C at ~1.5 Gyr (caption)", "printed": 1.5, "reconstructed": m.temperature_time(353.15), "note": ""},
        {"claim": "T goes from 50 to 100 C in <0.2 Gyr", "printed": 0.2, "reconstructed": t100 - t50,
         "note": f"{t50:.3f} to {t100:.3f} Gyr"},
        {"claim": "above 300 K at the floor, weathering exceeds supply", "printed": 300.0, "reconstructed": m.floor_threshold_T(),
         "so2_fitted": m.floor_threshold_T(fit),
         "note": "T at which F(Psoil = Patm = 1 ppm) = F0"},
        {"claim": "ocean loss takes ~1 Gyr at 6e11 H cm-2 s-1", "printed": 1.0,
         "reconstructed": h_atoms / 6e11 / 3.156e16,
         "note": "ocean mass 1.4e21 kg, not stated in the paper"},
    ]


def write(path: Path, rows: list[dict]) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()})


def overlay(pdf: Path, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sc, tr = _traces(pdf)
    d = traced(sc, tr)
    mo = model(m.FAITHFUL)
    mf = model(m.READINGS["so2_fitted"])
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.5, 7.5), sharex=True)
    for c, col in (("P_soil", "C3"), ("P_atm", "C0"), ("merged", "C0")):
        a1.plot(d[c][:, 0], d[c][:, 1], ".", ms=1.5, color=col)
    a1.plot(mo["t_Gyr"], mo["log_P_soil"], color="C3", lw=1, label="P_soil, reconstructed")
    a1.plot(mo["t_Gyr"], mo["log_P_atm"], color="C0", lw=1, label="P_atm, reconstructed")
    a1.plot(mf["t_Gyr"], mf["log_P_soil"], color="C3", lw=1, ls="--", label="SO2 term fitted to the kink")
    a1.plot(mf["t_Gyr"], mf["log_P_atm"], color="C0", lw=1, ls="--")
    a1.set_ylabel("log10 pCO2 (ppm)")
    b1 = a1.twinx()
    b1.plot(d["S_ratio"][:, 0], d["S_ratio"][:, 1], ".", ms=1.5, color="C2")
    b1.plot(mo["t_Gyr"], mo["S_ratio"], color="C2", lw=1)
    b1.set_ylabel("S/S0")
    a1.legend(fontsize=7, loc="lower left")
    a2.plot(d["Pi_ratio"][:, 0], d["Pi_ratio"][:, 1], ".", ms=1.5, color="C4")
    a2.plot(mo["t_Gyr"], mo["Pi_ratio"], color="C4", lw=1)
    a2.plot(mf["t_Gyr"], mf["Pi_ratio"], color="C4", lw=1, ls="--")
    a2.set_ylabel("Pi/Pi0")
    b2 = a2.twinx()
    b2.plot(d["T_K"][:, 0], d["T_K"][:, 1], ".", ms=1.5, color="C1")
    b2.plot(mo["t_Gyr"], mo["T_K"], color="C1", lw=1)
    b2.plot(mf["t_Gyr"], mf["T_K"], color="C1", lw=1, ls="--")
    b2.set_ylabel("T (K)")
    a2.set_xlabel("Time t in Gyr from present")
    a1.set_title("Caldeira & Kasting (1992) Fig. 2: traced points (dots), faithful (solid), SO2 fitted to the kink (dashed)", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main(pdf: Path = s.DEFAULT_PDF, outdir: Path = OUT) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    write(outdir / "ck1992_calibration.csv", calibration(pdf))
    write(outdir / "ck1992_fidelity.csv", scores(pdf))
    write(outdir / "ck1992_two_way.csv", two_way(pdf))
    write(outdir / "ck1992_events.csv", events(pdf))
    write(outdir / "ck1992_coupled.csv", coupled(pdf))
    write(outdir / "ck1992_claims.csv", claims())
    overlay(pdf, outdir / "ck1992_overlay.png")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(Path(args[0]) if args else s.DEFAULT_PDF, Path(args[1]) if len(args) > 1 else OUT)
