"""Score the Sellers (1969) reconstruction against the printed figures and tables.

    uv run python -m terra_prisca.budyko_sellers.fidelity_sellers1969 [pdf] [outdir]

Writes sellers1969_fidelity.csv (per printed curve or point set: RMSE and
largest error, for the faithful reading, null controls and rejected
readings), sellers1969_numbers.csv (the paper's stated numbers against the
model) and sellers1969_overlay.png to models/budyko_sellers/fidelity/.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .scan_sellers1969 import DEFAULT_PDF, load
from .sellers1969 import (AREA, BELT_LAT, CIRC_LAT, ICE_GUESS, KLY_YR, NB, Scenario, Sellers1969, model,
                          radiative_equilibrium)

FIG5_CASES = {"1": {0: .50, 1: .50}, "2": {0: .40, 1: .40}, "3": {16: .50, 17: .50},
              "4": {16: .44, 17: .40}, "5": {0: .50, 1: .50, 16: .50, 17: .50},
              "6": {0: .40, 1: .40, 16: .44, 17: .40}}
FIG7_CURVES = {"a": dict(s=2.00), "b": dict(s=2.02), "c": dict(s=2.10), "d": dict(s=2.20),
               "e": dict(s=1.98), "f": dict(s=1.96), "g": dict(k_mult=2.0), "h": dict(k_mult=0.5),
               "i": dict(s=1.94, k_mult=2.0)}
TABLE3_H = np.array([0.0, 1.4, 23.0, 50.5, 114.8, 96.4, 76.2, 41.3, 23.0, 23.9, 34.4, 46.9, 24.8, 6.9, 0.5,
                     2.3, 3.7, 0.0])
TABLE3_DQ = np.array([0.0, 0.1, 1.6, 4.2, 11.3, 10.7, 9.2, 5.3, 3.0, 3.2, 4.4, 5.7, 2.8, 0.7, 0.0, 0.2, 0.2, 0.0])
TABLE3_DT1 = np.array([27.0, 25.9, 24.2, 22.0, 19.0, 15.1, 12.6, 11.4, 11.3, 11.3, 11.4, 11.9, 12.8, 14.2, 16.5,
                       19.1, 22.2, 24.4])
TABLE3_DT2 = np.array([25.2, 24.2, 22.6, 20.5, 17.6, 13.9, 11.5, 10.5, 10.3, 10.4, 10.5, 10.9, 11.7, 13.7, 15.3,
                       17.7, 20.5, 22.5])
S_GRID = np.round(np.arange(1.80, 2.2001, 0.0025), 4)
LAND = 1.0 - np.genfromtxt(Path(__file__).with_name("data") / "ocean_fraction_belts.csv",
                           delimiter=",", names=True)["ocean_belt"]


def sweep(m: Sellers1969, law: str):
    """T-bar along S_GRID by continuation from the present state, down and up.

    The anchored 0.005 law is defined for cooling only: re-anchoring b keeps
    today's albedo but leaves jumps of up to 0.22 at the warm switch, which the
    paper never reaches (its 0.005 points stop at S = 2.00). Above 2.00 it is NaN."""
    down = S_GRID[S_GRID <= 2.0][::-1]
    up = S_GRID[S_GRID >= 2.0] if law != "0.005-anchored" else S_GRID[:0]
    tb = {s: np.nan for s in S_GRID}
    for seq in (down, up):
        for s, st in zip(seq, m.continuation(seq, lambda x: Scenario(s=x, law=law))):
            tb[s] = st["Tbar"] if st["ok"] else np.nan
    return np.array([tb[s] for s in S_GRID])


def critical_s(m: Sellers1969, lo=1.94, hi=2.0, tol=1e-4):
    """Smallest S on the warm branch of the 0.009 law: below it the planet ices over."""
    warm = m.present()["T"]
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        st = m.solve(Scenario(s=mid), warm)
        if st["ok"] and st["Tbar"] > -50:
            hi, warm = mid, st["T"]
        else:
            lo = mid
    return hi


def experiments(m: Sellers1969) -> dict:
    p = m.present()
    out = {"present": p, "divergence": m.belt_divergence(p)}
    out["fig5"] = {k: m.solve(Scenario(fixed_albedo=fa)) for k, fa in FIG5_CASES.items()}
    out["fig6"] = {law: sweep(m, law) for law in ("0.009", "0.005-anchored", "fixed")}
    out["Sc"] = critical_s(m)
    # Curve i has three equilibria (13.0, 3.1 and -99.1 C); the paper's text and figures
    # match the middle one, reached here from a uniform 250 K start (the warm one from
    # the present state, the ice-covered one from ICE_GUESS).
    out["fig7"] = {k: m.solve(Scenario(**kw), np.full(NB, 250.0) if k == "i" else None)
                   for k, kw in FIG7_CURVES.items()}
    out["i warm"] = m.solve(Scenario(s=1.94, k_mult=2.0))
    heat = [m.continuation(np.linspace(0, 1, 11), lambda x: Scenario(heat=x * TABLE3_H * LAND * KLY_YR))[-1]]
    heat.append(m.solve(Scenario(heat=TABLE3_H * LAND * KLY_YR, dqs=TABLE3_DQ * LAND * KLY_YR), heat[0]["T"]))
    out["table3"] = heat
    out["fixed -10%"] = m.solve(Scenario(s=1.80, law="fixed"))
    out["m -3%"] = m.solve(Scenario(m=0.485))
    return out


def scan_targets(scan, ex) -> list[tuple[str, str, np.ndarray, np.ndarray, np.ndarray]]:
    """(figure, curve, abscissa, printed value, model value) for every scored item."""
    p, dv = ex["present"], ex["divergence"]
    rows = []
    present = {("fig4", "T"): (BELT_LAT, p["Tc"]), ("fig4", "v"): (CIRC_LAT, p["v"]),
               ("fig4", "albedo"): (BELT_LAT, p["albedo"]),
               ("fig3", "C"): (CIRC_LAT, p["C"] / 1e3), ("fig3", "Lc"): (CIRC_LAT, p["Lc"] / 1e3),
               ("fig3", "F"): (CIRC_LAT, p["F"] / 1e3), ("fig3", "P"): (CIRC_LAT, p["P"] / 1e3),
               ("fig2", "dC"): (BELT_LAT, dv["C"]), ("fig2", "Ldc"): (BELT_LAT, dv["Lc"]),
               ("fig2", "dF"): (BELT_LAT, dv["F"]), ("fig2", "Rs"): (BELT_LAT, p["Rs"] / KLY_YR)}
    for key, (lat, val) in present.items():
        pts = scan.points[key]
        rows.append((*key, pts[:, 0], pts[:, 1], np.interp(-pts[:, 0], -lat, val)))
    for k in ("5", "6"):
        pts = scan.points[("fig5", k)]
        d = ex["fig5"][k]["Tc"] - p["Tc"]
        rows.append(("fig5", k, pts[:, 0], pts[:, 1], np.interp(-pts[:, 0], -BELT_LAT, d)))
    for k in ("1", "2", "3", "4", "3 south", "4 south"):
        lat, val = trace_columns(scan.traces[("fig5", k)][1], -85, 85)
        d = ex["fig5"][k.split()[0]]["Tc"] - p["Tc"]
        rows.append(("fig5", k, lat, val, np.interp(-lat, -BELT_LAT, d)))
    for law, name in (("0.009", "0.009"), ("0.005-anchored", "0.005")):
        pts = scan.points[("fig6", name)]
        rows.append(("fig6", name, pts[:, 0], pts[:, 1], interp_s(pts[:, 0], ex["fig6"][law])))
    s, t = trace_columns(scan.traces[("fig6", "fixed")][1], 1.80, 2.20)
    rows.append(("fig6", "fixed", s, t, interp_s(s, ex["fig6"]["fixed"])))
    for name, sts in (("K x2", [ex["fig7"]["g"]["Tbar"], ex["fig7"]["i"]["Tbar"]]),
                      ("K x0.5", [ex["fig7"]["h"]["Tbar"]])):
        pts = scan.points[("fig6", name)]
        rows.append(("fig6", name, pts[:, 0], pts[:, 1], np.array(sts)))
    pts = scan.points[("fig7", "a")]
    rows.append(("fig7", "a", pts[:, 0], pts[:, 1], np.interp(-pts[:, 0], -BELT_LAT, ex["fig7"]["a"]["Tc"])))
    for k in "bcdefghi":
        lat, val = trace_columns(scan.traces[("fig7", k)][1], -85, 85)
        rows.append(("fig7", k, lat, val, np.interp(-lat, -BELT_LAT, ex["fig7"][k]["Tc"])))
    return rows


def table_targets(ex):
    p = ex["present"]
    return [("table3", "dT1", BELT_LAT, TABLE3_DT1, ex["table3"][0]["Tc"] - p["Tc"]),
            ("table3", "dT2", BELT_LAT, TABLE3_DT2, ex["table3"][1]["Tc"] - p["Tc"])]


def trace_columns(data, lo, hi, step=None):
    """Traced curve resampled to one value per unit step of the abscissa (median of nearby trace points)."""
    x, y = data[:, 0], data[:, 1]
    lo, hi = min(lo, hi), max(lo, hi)
    keep = (x >= lo) & (x <= hi)
    x, y = x[keep], y[keep]
    step = step or (2.5 if hi - lo > 10 else 0.005)
    grid = np.arange(lo, hi + 1e-9, step)
    out = [(g, np.median(y[np.abs(x - g) <= step / 2])) for g in grid if np.any(np.abs(x - g) <= step / 2)]
    a = np.array(out).reshape(-1, 2)
    return a[:, 0], a[:, 1]


def interp_s(s, tbar):
    ok = ~np.isnan(tbar)
    return np.interp(s, S_GRID[ok], tbar[ok])


def summarise(rows, reading):
    out = []
    for fig, curve, x, printed, modelled in rows:
        err = np.asarray(modelled) - np.asarray(printed)
        ok = ~np.isnan(err)
        out.append(dict(reading=reading, figure=fig, curve=curve, n=int(ok.sum()),
                        rmse=float(np.sqrt(np.mean(err[ok] ** 2))) if ok.any() else np.nan,
                        max_abs=float(np.max(np.abs(err[ok]))) if ok.any() else np.nan))
    return out


def observed_at(scan, lat, ring_px: float = 10.0):
    """Fig. 4's observed temperature line at the given latitudes, read away from the computed circles."""
    px, data = scan.traces[("fig4", "T observed")]
    rings = scan.frames[("fig4", "T")].to_px(scan.points[("fig4", "T")])
    clear = np.min(np.hypot(*(px[:, None, :] - rings[None, :, :]).transpose(2, 0, 1)), axis=1) > ring_px
    d = data[clear]
    o = np.argsort(d[:, 0])
    return np.interp(lat, d[o, 0], d[o, 1])


def null_rows(scan, ex):
    """Controls: no transport (radiative equilibrium), no change (perturbation leaves T as it is),
    and fixed albedo where the paper let it vary."""
    m = model()
    p = ex["present"]
    rad = radiative_equilibrium(m)
    rows = []
    pts = scan.points[("fig4", "T")]
    rows.append(("no transport", "fig4", "T", pts[:, 0], pts[:, 1], np.interp(-pts[:, 0], -BELT_LAT, rad["Tc"])))
    pts = scan.points[("fig4", "albedo")]
    rows.append(("no transport", "fig4", "albedo", pts[:, 0], pts[:, 1],
                 np.interp(-pts[:, 0], -BELT_LAT, rad["albedo"])))
    pts = scan.points[("fig4", "T")]
    rows.append(("observed T offered as the solution", "fig4", "T", pts[:, 0], pts[:, 1],
                 observed_at(scan, pts[:, 0])))
    for fig, curve, x, printed, modelled in scan_targets(scan, ex) + table_targets(ex):
        if fig == "fig5" or fig == "table3":
            rows.append(("no change", fig, curve, x, printed, np.zeros_like(printed)))
        elif fig == "fig6" and curve in ("0.009", "0.005"):
            rows.append(("no change", fig, curve, x, printed, np.full_like(printed, p["Tbar"])))
            rows.append(("fixed albedo", fig, curve, x, printed, interp_s(x, ex["fig6"]["fixed"])))
        elif fig == "fig7" and curve != "a":
            rows.append(("no change", fig, curve, x, printed, np.interp(-x, -BELT_LAT, p["Tc"])))
    fixed5 = {}
    for k, fa in FIG5_CASES.items():
        fixed5[k] = m.solve(Scenario(fixed_albedo=fa, law="fixed"))["Tc"] - p["Tc"]
    for fig, curve, x, printed, modelled in scan_targets(scan, ex):
        if fig == "fig5":
            rows.append(("fixed albedo", fig, curve, x, printed, np.interp(-x, -BELT_LAT, fixed5[curve.split()[0]])))
    out = []
    for name, *r in rows:
        out += summarise([tuple(r)], name)
    return out


READINGS = {"ocean band mean": dict(ocean="band"), "Tetens vapour pressure": dict(vapour="tetens"),
            "vT in deg C": dict(vt_kelvin=False), "|dT| per hemisphere": dict(grad_mean="hemisphere")}


def key_numbers(ex, scan):
    p = ex["present"]
    f7, fx = ex["fig7"], ex["fixed -10%"]["Tc"] - p["Tc"]
    drop = scan.traces[("fig6", "0.009 drop")][1]
    drop = drop[(drop[:, 1] > -90) & (drop[:, 1] < -10)]
    def edge(st, level=-10.0):
        t, lat = st["Tc"][:9], BELT_LAT[:9]
        return float(np.interp(level, t, lat))
    f6 = ex["fig6"]
    m = model()
    sc_i = Scenario(s=1.94, k_mult=2.0)
    ice_i = m.solve(sc_i, np.full(NB, ICE_GUESS))
    g = scan.traces[("fig7", "g")][1]
    g = g[np.argsort(g[:, 0])]

    def g_at(lat):
        return float(np.interp(lat, g[:, 0], g[:, 1]))

    def ends(t):
        """Equator-pole difference, linearly extrapolated from the two belts nearest each end."""
        return float((t[8] + 0.5 * (t[8] - t[7])) - (t[0] + 0.5 * (t[0] - t[1])))

    s005 = S_GRID[np.nanargmax(np.where(S_GRID < 1.95, np.abs(np.gradient(f6["0.005-anchored"])), -1))]
    return [
        ("present T-bar (deg C)", "about 14.0 (text)", p["Tbar"]),
        ("0.009 law: S at the jump to ice cover (ly/min)", f"{np.median(drop[:, 0]):.4f} (Fig. 6 vertical)", ex["Sc"]),
        ("0.009 law: -2% ice edge where T = -10 C (deg N)", "50 (text)", edge(f7["f"])),
        ("ice-covered T-bar (deg C)", "-100 (text)", float(np.nanmin(f6["0.009"]))),
        ("0.005 law: steepest fall in T-bar at S (ly/min)", "1.87 (Fig. 6); 5-6% (text)", float(s005)),
        ("fixed albedo -10%: cooling at 0-20 and 50-60 (deg C)", "14.3 (text)",
         float(np.mean(-fx[[3, 7, 8, 9, 10, 14]]))),
        ("fixed albedo -10%: cooling at 80-90 (deg C)", "13.0 (text)", float(np.mean(-fx[[0, 17]]))),
        ("fixed albedo +10%: warming of T-bar (deg C)", "about 12 (text)",
         float(interp_s([2.20], f6["fixed"])[0] - p["Tbar"])),
        ("K x2: warming of T-bar (deg C)", "about 5 (text)", f7["g"]["Tbar"] - p["Tbar"]),
        ("present NH difference, belt centres 5N-85N (deg C)", "48 (text, equator-pole)", p["Tc"][8] - p["Tc"][0]),
        ("present NH difference, extrapolated to 0-90N (deg C)", "48 (text, equator-pole)", ends(p["Tc"])),
        ("K x2: NH difference, belt centres 5N-85N (deg C)", f"28 (text); {g_at(5) - g_at(85):.1f} (Fig. 7 g)",
         f7["g"]["Tc"][8] - f7["g"]["Tc"][0]),
        ("K x2: NH difference, extrapolated to 0-90N (deg C)",
         f"28 (text); {g_at(0) - g_at(90):.1f} (Fig. 7 g, 0N to its end at {g[-1, 0]:.1f}N)", ends(f7["g"]["Tc"])),
        ("K x0.5: polar belts (deg C)", "below -70 (text)", float(max(f7["h"]["Tc"][0], f7["h"]["Tc"][17]))),
        ("K x0.5: 40-50N and 40-50S (deg C)", "below -10 (text)", float(max(f7["h"]["Tc"][4], f7["h"]["Tc"][13]))),
        ("-3% and K x2: NH equator-pole difference (deg C)", "26 (text)", f7["i"]["Tc"][8] - f7["i"]["Tc"][0]),
        ("-3% and K x2: equatorial cooling (deg C)", "about 16 (text)", p["Tc"][8] - f7["i"]["Tc"][8]),
        ("-3% and K x2: T-bar on the warm equilibrium (deg C)", "not reported", ex["i warm"]["Tbar"]),
        ("-3% and K x2: T-bar on the cold equilibrium (deg C)", f"{scan.points[('fig6', 'K x2')][1, 1]:.1f} (Fig. 6 square)",
         f7["i"]["Tbar"]),
        ("-3% and K x2: T-bar on the ice-covered equilibrium (deg C)", "not reported", ice_i["Tbar"]),
        ("-3% and K x2: leading growth rate, warm / plotted / ice-covered root (per unit heat capacity)",
         "steady states only (paper)", " / ".join(f"{m.growth_rates(st['T'], sc_i)[0].real:.3f}"
                                                   for st in (ex["i warm"], f7["i"], ice_i))),
        ("m -3%: T-bar (deg C)", "brink of an ice age (text)", ex["m -3%"]["Tbar"]),
        ("albedo 80-90N, case 3 (untreated)", "0.61 (Fig. 5)", ex["fig5"]["3"]["albedo"][0]),
        ("albedo 70-80N, case 3 (untreated)", "0.58 (Fig. 5)", ex["fig5"]["3"]["albedo"][1]),
        ("albedo 70-80N, case 4 (untreated)", "0.57 (Fig. 5)", ex["fig5"]["4"]["albedo"][1]),
        ("albedo 70-80S, case 1 (untreated)", "0.79 (Fig. 5)", ex["fig5"]["1"]["albedo"][16]),
        ("albedo 80-90S, case 1 (untreated)", "0.84 (Fig. 5)", ex["fig5"]["1"]["albedo"][17]),
        ("albedo 70-80S, case 2 (untreated)", "0.78 (Fig. 5)", ex["fig5"]["2"]["albedo"][16]),
        ("albedo 80-90S, case 2 (untreated)", "0.82 (Fig. 5)", ex["fig5"]["2"]["albedo"][17]),
        ("case 2: warming poleward of 70N, max (deg C)", "about 7 (text)",
         float(np.max(ex["fig5"]["2"]["Tc"][:2] - p["Tc"][:2]))),
        ("case 2: warming 0-20N and 0-20S, mean (deg C)", "about 1 (text)",
         float(np.mean(ex["fig5"]["2"]["Tc"][7:11] - p["Tc"][7:11]))),
        ("case 2: warming 70-90S (deg C)", "1-3 (text)", float(np.max(ex["fig5"]["2"]["Tc"][16:] - p["Tc"][16:]))),
        ("case 3: warming 80-90S (deg C)", "12-15 (text)", ex["fig5"]["3"]["Tc"][17] - p["Tc"][17]),
        ("case 4: warming 80-90S (deg C)", "12-15 (text)", ex["fig5"]["4"]["Tc"][17] - p["Tc"][17]),
        ("case 3: warming 80-90N (deg C)", "about 4 (text)", ex["fig5"]["3"]["Tc"][0] - p["Tc"][0]),
        ("cases 5 and 6: warming 80-90N (deg C)", "7-10 (text)",
         f'{ex["fig5"]["5"]["Tc"][0] - p["Tc"][0]:.2f} / {ex["fig5"]["6"]["Tc"][0] - p["Tc"][0]:.2f}'),
        ("cases 5 and 6: warming 80-90S (deg C)", "13-17 (text)",
         f'{ex["fig5"]["5"]["Tc"][17] - p["Tc"][17]:.2f} / {ex["fig5"]["6"]["Tc"][17] - p["Tc"][17]:.2f}'),
        ("cases 5 and 6: largest tropical warming, 0-20 (deg C)", "never exceeds 2 (text)",
         float(np.max(ex["fig5"]["6"]["Tc"][7:11] - p["Tc"][7:11]))),
        ("Table 3 dT1, area mean (deg C)", f"about 15 (text); {np.sum(TABLE3_DT1 * AREA) / np.sum(AREA):.1f} (table)",
         float(np.sum((ex["table3"][0]["Tc"] - p["Tc"]) * AREA) / np.sum(AREA))),
    ]


def overlay(scan, ex, path):
    fig, ax = plt.subplots(3, 3, figsize=(15, 13))
    p, dv = ex["present"], ex["divergence"]
    a = ax[0, 0]
    for k, c in (("T", "k"),):
        pts = scan.points[("fig4", k)]
        a.plot(pts[:, 0], pts[:, 1], "o", mfc="none", color=c, label="Fig. 4 circles")
    a.plot(BELT_LAT, p["Tc"], "r.-", label="reconstruction")
    a.set_title("Fig. 4: present T (deg C)")
    a = ax[0, 1]
    for k, c in (("C", "C0"), ("Lc", "C1"), ("F", "C2"), ("P", "k")):
        pts = scan.points[("fig3", k)]
        a.plot(pts[:, 0], pts[:, 1], "o", mfc="none", color=c, label=f"Fig. 3 {k}")
        a.plot(CIRC_LAT, p[k] / 1e3, "-", color=c, lw=1)
    a.set_title("Fig. 3: northward transport (kcal/cm/s); lines = reconstruction")
    a = ax[0, 2]
    for k, c, mv in (("dC", "C0", dv["C"]), ("Ldc", "C1", dv["Lc"]), ("dF", "C2", dv["F"]),
                     ("Rs", "k", p["Rs"] / KLY_YR)):
        pts = scan.points[("fig2", k)]
        a.plot(pts[:, 0], pts[:, 1], "o", mfc="none", color=c, label=f"Fig. 2 {k}")
        a.plot(BELT_LAT, mv, "-", color=c, lw=1)
    a.set_title("Fig. 2: belt fluxes (kly/yr)")
    a = ax[1, 0]
    for k in ("v", "albedo"):
        pts = scan.points[("fig4", k)]
        sc = 10 if k == "albedo" else 1
        a.plot(pts[:, 0], pts[:, 1] * sc, "o", mfc="none", label=f"Fig. 4 {k}" + (" x10" if sc > 1 else ""))
        a.plot(BELT_LAT if k == "albedo" else CIRC_LAT, p[k] * sc, "r-", lw=1)
    a.set_title("Fig. 4: v (cm/s) and albedo x10")
    a = ax[1, 1]
    for i, k in enumerate("123456"):
        c = f"C{i}"
        a.plot(BELT_LAT, ex["fig5"][k]["Tc"] - p["Tc"], "-", color=c, lw=1, label=k)
        keys = [("fig5", k)] if k in "56" else [("fig5", k)] + ([("fig5", k + " south")] if k in "34" else [])
        for key in keys:
            if key in scan.points:
                q = scan.points[key]
                a.plot(q[:, 0], q[:, 1], "o", mfc="none", color=c, ms=5)
            if key in scan.traces:
                d = scan.traces[key][1]
                a.plot(d[:, 0], d[:, 1], ".", color=c, ms=1)
    a.set_title("Fig. 5: warming from polar albedo changes (deg C)")
    a = ax[1, 2]
    for law, c, name in (("0.009", "k", "0.009"), ("0.005-anchored", "C0", "0.005"), ("fixed", "C2", "fixed")):
        a.plot(S_GRID, ex["fig6"][law], "-", color=c, lw=1, label=law)
        if ("fig6", name) in scan.points:
            q = scan.points[("fig6", name)]
            a.plot(q[:, 0], q[:, 1], "o", mfc="none", color=c)
    d = scan.traces[("fig6", "fixed")][1]
    a.plot(d[:, 0], d[:, 1], ".", color="C2", ms=1)
    d = scan.traces[("fig6", "0.009 drop")][1]
    a.plot(d[:, 0], d[:, 1], ".", color="k", ms=1)
    for name, mk in (("K x2", "s"), ("K x0.5", "^")):
        q = scan.points[("fig6", name)]
        a.plot(q[:, 0], q[:, 1], mk, mfc="none", color="C3", label=f"Fig. 6 {name}")
    a.plot([2.0, 1.94, 2.0], [ex["fig7"]["g"]["Tbar"], ex["fig7"]["i"]["Tbar"], ex["fig7"]["h"]["Tbar"]], "x",
           color="C3", label="reconstruction, K changed")
    a.set_title("Fig. 6: global mean T vs solar constant")
    a.legend(fontsize=7)
    a = ax[2, 0]
    for i, k in enumerate("abcdefghi"):
        c = f"C{i}"
        a.plot(BELT_LAT, ex["fig7"][k]["Tc"], "-", color=c, lw=1, label=k)
        if k == "a":
            q = scan.points[("fig7", "a")]
            a.plot(q[:, 0], q[:, 1], "o", mfc="none", color=c)
        else:
            d = scan.traces[("fig7", k)][1]
            a.plot(d[:, 0], d[:, 1], ".", color=c, ms=1)
    a.set_title("Fig. 7: T profiles (traces dotted, model lines)")
    a.legend(fontsize=7, ncol=3)
    a = ax[2, 1]
    for k, c, tab in (("dT1", "C0", TABLE3_DT1), ("dT2", "C1", TABLE3_DT2)):
        i = 0 if k == "dT1" else 1
        a.plot(BELT_LAT, tab, "o", mfc="none", color=c, label=f"Table 3 {k}")
        a.plot(BELT_LAT, ex["table3"][i]["Tc"] - p["Tc"], "-", color=c, lw=1)
    a.set_title("Table 3: warming from added heat (deg C)")
    a = ax[2, 2]
    q = scan.points[("fig4", "T")]
    rad = radiative_equilibrium(model())
    a.plot(q[:, 0], q[:, 1], "o", mfc="none", color="k", label="Fig. 4 T")
    a.plot(BELT_LAT, p["Tc"], "r-", lw=1, label="reconstruction")
    a.plot(BELT_LAT, rad["Tc"], "C0--", lw=1, label="null: no transport")
    a.set_title("Null control: no transport")
    for a in ax.flat:
        if a is not ax[1, 2]:
            a.set_xlim(90, -90)
            a.axhline(0, color="grey", lw=0.4)
        a.legend(fontsize=7) if not a.get_legend() else None
    fig.suptitle("Sellers (1969): scan (markers, dots) against the faithful reconstruction (lines)")
    fig.tight_layout()
    fig.savefig(path, dpi=100)
    plt.close(fig)


def main(pdf: Path, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    scan = load(pdf)
    ex = experiments(model())
    rows = summarise(scan_targets(scan, ex) + table_targets(ex), "faithful")
    rows += null_rows(scan, ex)
    for name, kw in READINGS.items():
        try:
            exr = experiments(model(**kw))
            rows += summarise(scan_targets(scan, exr) + table_targets(exr), name)
        except RuntimeError as err:
            rows.append(dict(reading=name, figure="all", curve=str(err), n=0, rmse=np.nan, max_abs=np.nan))
    with (outdir / "sellers1969_fidelity.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    with (outdir / "sellers1969_numbers.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["quantity", "paper", "reconstruction"])
        for q, paper, val in key_numbers(ex, scan):
            w.writerow([q, paper, val if isinstance(val, str) else round(float(val), 4)])
    overlay(scan, ex, outdir / "sellers1969_overlay.png")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(Path(args[0]) if args else DEFAULT_PDF,
         Path(args[1]) if len(args) > 1 else Path("models/budyko_sellers/fidelity"))
