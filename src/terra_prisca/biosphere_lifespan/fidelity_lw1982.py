"""Score the Lovelock & Whitfield (1982) reconstruction against the printed Fig. 2.

    uv run python -m terra_prisca.biosphere_lifespan.fidelity_lw1982 [pdf] [outdir]

Writes, to models/biosphere_lifespan/fidelity/:
  lw1982_lines.csv     each printed straight line, fitted in data units
  lw1982_fidelity.csv  the Sun and CO2 lines scored against each reading and null
  lw1982_lifespan.csv  time to 150 ppm and CO2 at the anchors, for every reading
  lw1982_band.csv      the temperature band against the limits the text states
  lw1982_claims.csv    the stated numbers, recomputed
  lw1982_overlay.png   model lines drawn over the scan
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from terra_prisca.walker_hays_kasting import whk1981

from . import lw1982 as m
from . import scan_lw1982 as s

OUT = Path("models/biosphere_lifespan/fidelity")
OCR_SLOPE = 0.25 / 4.5  # Owen et al. (1979): 75% of today's solar constant 4,500 Myr ago, linear


def lines(sc: s.Scan) -> list[dict]:
    rows = []
    for key in s.SEEDS:
        p = s.trace(sc, key)
        t = sc.time.value(p[:, 0])
        y = sc.lum.value(p[:, 1]) if key == "sun" else sc.sqrtc.value(p[:, 1])
        k, c = np.polyfit(t, y, 1)
        kp, cp = np.polyfit(p[:, 0], p[:, 1], 1)
        rows.append({"line": key, "scale": "L/L0" if key == "sun" else "sqrt(ppm)",
                     "columns": len(p), "t_start": t[0], "t_end": t[-1],
                     "slope_per_Myr": k, "value_at_t0": c,
                     "value_at_start": k * t[0] + c, "value_at_end": k * t[-1] + c,
                     "straight_rms_px": float(np.sqrt(np.mean((p[:, 1] - (kp * p[:, 0] + cp)) ** 2)))})
    return rows


def _row(curve, reading, pred, obs, px_per_unit):
    r = pred - obs
    return {"curve": curve, "reading": reading, "columns": len(obs),
            "rmse": float(np.sqrt(np.mean(r ** 2))), "bias": float(np.mean(r)),
            "max_abs": float(np.abs(r).max()),
            "rmse_px": float(np.sqrt(np.mean(r ** 2)) * px_per_unit)}


def scores(sc: s.Scan) -> list[dict]:
    rows = []
    p = s.trace(sc, "sun")
    t, obs = sc.time.value(p[:, 0]), sc.lum.value(p[:, 1])
    ppu = 1 / abs(sc.lum.slope)
    for name, pred in (("faithful (straight, 0.0733/Gyr)", m.luminosity(t)),
                       ("null: Gough (1981)", m.gough_luminosity(t)),
                       ("null: Owen et al. (1979) linear, 0.0556/Gyr", m.luminosity(t, 1000 * OCR_SLOPE / 1000)),
                       ("null: constant Sun", np.ones_like(t))):
        rows.append(_row("Sun line (L/L0)", name, pred, obs, ppu))
    p = s.trace(sc, "co2")
    t, obs = sc.time.value(p[:, 0]), sc.sqrtc.value(p[:, 1])
    ppu = 1 / abs(sc.sqrtc.slope)
    for key, r in m.READINGS.items():
        rows.append(_row("CO2 line (sqrt ppm)", key, np.sqrt(m.co2(t, r)), obs, ppu))
    rows.append(_row("CO2 line (sqrt ppm)", "null: constant CO2 (320 ppm)", np.full_like(t, np.sqrt(m.C_NOW)), obs, ppu))
    return rows


def crossing(sc: s.Scan) -> dict:
    """Where the printed CO2 line meets the printed limit line, in Myr."""
    lim = s.trace(sc, "limit")
    yl = float(np.mean(lim[:, 1]))
    out = {"limit_sqrt_ppm": float(sc.sqrtc.value(yl)), "limit_ppm": float(sc.sqrtc.value(yl)) ** 2}
    for key in ("co2", "co2_tail"):
        p = s.trace(sc, key)
        k, c = np.polyfit(p[:, 0], p[:, 1], 1)
        out[f"{key}_meets_limit_Myr"] = float(sc.time.value((yl - c) / k))
    return out


def lifespans() -> list[dict]:
    rows = []
    for group, d in (("reading", m.READINGS), ("variant", m.VARIANTS), ("control", m.CONTROLS)):
        for key, r in d.items():
            rows.append({"group": group, "key": key, "name": r.name,
                         "co2_at_minus3500_ppm": float(m.co2(m.T_PAST, r)),
                         "co2_today_ppm": float(m.co2(0.0, r)),
                         "years_to_150ppm_Myr": m.lifespan(r)})
    return rows


TEXT_BAND = {"Archaean upper": 40.0, "Archaean lower": 15.0,
             "post-2.2 Gyr upper": 25.0, "post-2.2 Gyr lower": 15.0}


def band(sc: s.Scan) -> list[dict]:
    rows = []
    for name, (temp, t0, t1) in s.band_levels(sc).items():
        rows.append({"feature": name, "t_start": t0, "t_end": t1, "printed_C": temp,
                     "text": {"Archaean upper": "40 C", "Archaean lower": "15 C",
                              "post-2.2 Gyr upper": "20-30 C (upper limit)",
                              "post-2.2 Gyr lower": "glacial 5-10 C plus 5-15 C"}[name],
                     "text_value_C": TEXT_BAND[name]})
    for t, temp in s.glaciation_minima(sc):
        rows.append({"feature": "glaciation minimum", "t_start": t, "t_end": t, "printed_C": temp,
                     "text": "glaciations 5-10 C", "text_value_C": 5.0})
    return rows


def claims(sc: s.Scan) -> list[dict]:
    x = crossing(sc)
    ln = {r["line"]: r for r in lines(sc)}
    p_kept = m.C_PAST / m.C_NOW
    t_kept = whk1981.TS0 + float(whk1981.surface_dT(0.0, p_kept)) - 273.15
    return [
        {"claim": "150 ppm is reached in about 100 Myr", "stated": 100.0,
         "reconstructed": m.lifespan(), "note": "faithful rule (70,000 ppm anchor); printed lines cross at "
         f"{x['co2_meets_limit_Myr']:.0f} Myr (main line) and {x['co2_tail_meets_limit_Myr']:.0f} Myr (tail)"},
        {"claim": "150 ppm with the text's 7,000 ppm anchor", "stated": 100.0,
         "reconstructed": m.lifespan(m.READINGS["text_7000"]), "note": "the literal text gives 3 times the stated span"},
        {"claim": "CO2 3,500 Myr ago (ppm)", "stated": 7000.0,
         "reconstructed": ln["co2"]["value_at_start"] ** 2,
         "note": f"printed line read at its start (t = {ln['co2']['t_start']:.0f} Myr); "
                 "Owen et al. (1979) Table 1, from Hart (1978): 0.070 bar = 70,000 ppm"},
        {"claim": "CO2 today (ppm)", "stated": 320.0, "reconstructed": ln["co2"]["value_at_t0"] ** 2,
         "note": "printed line at t = 0"},
        {"claim": "CO2 limit (ppm)", "stated": 150.0, "reconstructed": x["limit_ppm"], "note": "printed limit line"},
        {"claim": "Sun's output up 30% since 4,500 Myr ago (per cent of today's)", "stated": 30.0,
         "reconstructed": 100 * (1 - float(m.luminosity(-4500.0))),
         "note": f"printed Sun line; as a rise relative to the young Sun it is "
                 f"{100 * (1 / float(m.luminosity(-4500.0)) - 1):.0f}%"},
        {"claim": "without the CO2 decline, might by now have exceeded 50 C", "stated": 50.0,
         "reconstructed": t_kept,
         "note": "WHK eq. (6) with CO2 held at 70,000 ppm and today's Sun; L&W give no climate model"},
        {"claim": "2/3 power would not change the qualitative conclusion", "stated": float("nan"),
         "reconstructed": m.lifespan(m.READINGS["two_thirds"]),
         "note": "C^(2/3) linear in L, same anchors"},
    ]


def overlay(sc: s.Scan, path: Path) -> None:
    """Model lines over the digitised traces, in data units. The scan itself is
    not drawn: it is copyrighted."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(9, 3.6))
    p = s.trace(sc, "sun")
    a.plot(sc.time.value(p[:, 0]), sc.lum.value(p[:, 1]), ".", ms=1.5, color="0.6", label="printed (traced)")
    t = np.linspace(-4000, 2000, 400)
    a.plot(t, m.luminosity(t), "r-", lw=0.8, label="faithful: straight, 0.0733/Gyr")
    a.plot(t, m.gough_luminosity(t), "b:", lw=0.8, label="null: Gough (1981)")
    a.set_xlabel("time (Myr)"), a.set_ylabel("L/L0"), a.legend(fontsize=7), a.set_title("Sun line", fontsize=9)
    for key in ("co2", "co2_tail"):
        p = s.trace(sc, key)
        b.plot(sc.time.value(p[:, 0]), sc.sqrtc.value(p[:, 1]), ".", ms=1.5, color="0.6",
               label="printed (traced)" if key == "co2" else None)
    tc = np.linspace(-3500, 200, 300)
    for key, style in (("faithful", "r-"), ("text_7000", "m--"), ("two_thirds", "c-."), ("linear_c", "g:")):
        b.plot(tc, np.sqrt(m.co2(tc, m.READINGS[key])), style, lw=0.8, label=key)
    b.axhline(np.sqrt(m.C_LIMIT), color="r", lw=0.5)
    b.set_ylim(0, 300), b.set_xlabel("time (Myr)"), b.set_ylabel("sqrt(CO2 / ppm)")
    b.legend(fontsize=7), b.set_title("CO2 line", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=130, metadata={"Software": None})
    plt.close(fig)


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()})


def main(pdf: Path = s.DEFAULT_PDF, outdir: Path = OUT) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    sc = s.load(pdf)
    write(outdir / "lw1982_lines.csv", lines(sc))
    write(outdir / "lw1982_fidelity.csv", scores(sc))
    write(outdir / "lw1982_lifespan.csv", lifespans())
    write(outdir / "lw1982_band.csv", band(sc))
    write(outdir / "lw1982_claims.csv", claims(sc))
    overlay(sc, outdir / "lw1982_overlay.png")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(Path(a[0]) if a else s.DEFAULT_PDF, Path(a[1]) if len(a) > 1 else OUT)
