"""Recover Fig. 5a/b numerical checkpoints from the accepted manuscript.

uv run python -m terra_prisca.haze_response.extract_eager_nash2023 PDF OUTPUT_DIR
The plotted baseline and warming increments are calibrated separately, then
added. This does not interpolate between climate models or rerun the GCM.
"""

import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SOURCE_SHA256 = "ac49ba3c761b50cb76910fdf67d071d80050e86ae94cc405c03ffea178e5cd83"
CO2_PA = [100, 300, 1000, 3000]
CH4_PA = np.array([1, 3, 10, 30, 100, 300, 1000, 3500])
COLOURS = ["rgb(100%, 49.803162%, 5.490112%)", "rgb(9.01947%, 74.508667%, 81.175232%)",
           "rgb(17.254639%, 62.744141%, 17.254639%)", "rgb(89.01825%, 46.665955%, 76.077271%)"]


def native_points(path):
    raw = path.attrib["d"]
    if re.search(r"[A-KN-Za-kn-z]", raw):
        raise ValueError("Expected absolute M/L plot coordinates")
    return np.array([float(v) for v in re.findall(r"[-+]?\d*\.?\d+", raw)]).reshape(-1, 2)


def extract(svg):
    paths = list(ET.parse(svg).getroot().iter("{http://www.w3.org/2000/svg}path"))
    curves, baseline, ticks_a, ticks_b, ticks_x = {}, [], [], [], []
    for path in paths:
        if path.get("fill") != "none":
            continue
        if re.search(r"[A-KN-Za-kn-z]", path.get("d", "")):
            continue
        xy = native_points(path)
        colour, width = path.get("stroke"), path.get("stroke-width")
        if width == "1.5" and len(xy) == 4 and colour == "rgb(50.195312%, 50.195312%, 50.195312%)":
            baseline.append(xy)
        if width == "1.5" and len(xy) == 8 and colour in COLOURS and xy[:, 1].min() > 770 and xy[:, 0].min() > 500:
            if colour in curves:
                raise ValueError("Duplicate warming curve")
            curves[colour] = xy
        if width == "0.8" and len(xy) == 2:
            x, y = xy[0]
            dx, dy = xy[1] - xy[0]
            if abs(dy) < 1e-6 and -3.6 < dx < -3.4 and y > 770:
                if abs(x - 62.791021) < 1e-3:
                    ticks_a.append(y)
                if abs(x - 527.21449) < 1e-3:
                    ticks_b.append(y)
            if abs(dx) < 1e-6 and -3.6 < dy < -3.4 and abs(y - 771.909272) < 1e-3 and x > 500:
                ticks_x.append(x)
    if len(baseline) != 1 or len(curves) != 4 or (len(ticks_a), len(ticks_b), len(ticks_x)) != (9, 7, 4):
        raise ValueError("Unexpected figure layout or calibration ticks")
    ta, tb, tx = sorted(ticks_a), sorted(ticks_b), sorted(ticks_x)
    fit_a = np.polyfit(ta, np.arange(270, 288, 2), 1)
    fit_b = np.polyfit(tb, np.arange(-6, 8, 2), 1)
    fit_x = np.polyfit(tx, [0, 1, 2, 3], 1)
    errors = dict(baseline_tick_k=float(np.max(abs(np.polyval(fit_a, ta) - np.arange(270, 288, 2)))),
                  warming_tick_k=float(np.max(abs(np.polyval(fit_b, tb) - np.arange(-6, 8, 2)))))
    if max(errors.values()) > 0.002:
        raise ValueError("Axis residual exceeds vector extraction tolerance")
    base_t = np.polyval(fit_a, baseline[0][:, 1])
    rows = []
    for pco2, colour, t0 in zip(CO2_PA, COLOURS, base_t, strict=True):
        curve = curves[colour]
        inferred_ch4 = 10 ** np.polyval(fit_x, curve[:, 0])
        if not np.allclose(inferred_ch4, CH4_PA, rtol=0.0002):
            raise ValueError("Log methane coordinates do not match the source grid")
        increments = np.polyval(fit_b, curve[:, 1])
        for pch4, delta in zip(np.r_[0, CH4_PA], np.r_[0, increments], strict=True):
            rows.append(dict(case=f"EN{pco2}", p_co2_pa=pco2, p_ch4_pa=int(pch4),
                             ch4_co2_ratio=float(pch4 / pco2), baseline_k=round(float(t0), 4),
                             warming_k=round(float(delta), 4), temperature_k=round(float(t0 + delta), 4)))
    return rows, errors


def main(pdf, output):
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Unidentified Eager-Nash accepted-manuscript PDF")
    with tempfile.TemporaryDirectory() as tmp:
        svg = Path(tmp) / "figure5.svg"
        subprocess.run(["pdftocairo", "-f", "13", "-l", "13", "-svg", str(pdf), str(svg)], check=True)
        rows, errors = extract(svg)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "figure5.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (output / "calibration.json").write_text(json.dumps(errors, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.3), constrained_layout=True)
    for pco2 in CO2_PA:
        subset = [r for r in rows if r["p_co2_pa"] == pco2]
        axes[0].plot([r["p_ch4_pa"] for r in subset], [r["temperature_k"] for r in subset],
                     "o-", markersize=3, label=f"CO₂ {pco2} Pa")
    axes[0].set_xscale("symlog", linthresh=1)
    axes[0].set(xlabel="Surface methane pressure (Pa)", ylabel="Global surface temperature (K)",
                title="Eager-Nash (2023): haze-free checkpoints")
    axes[0].legend(fontsize=8)
    subset = [r for r in rows if r["p_co2_pa"] == 1000]
    axes[1].plot([r["ch4_co2_ratio"] for r in subset], [r["temperature_k"] for r in subset],
                 "o--", markersize=4, label="Eager-Nash: 3D, CO₂ 0.01 bar")
    with Path("models/haze_response/arney2016/figure4.csv").open() as fh:
        arney = [r for r in csv.DictReader(fh) if r["case"] == "A"]
    axes[1].plot([float(r["ch4_co2_ratio"]) for r in arney], [float(r["temperature_k"]) for r in arney],
                 "o-", markersize=3, label="Arney A: 1D, CO₂ 0.01 bar")
    axes[1].set(xlabel="Surface CH₄/CO₂", ylabel="Surface temperature (K)", xlim=(0, 0.26), ylim=(260, 287),
                title="Comparable CO₂; different climate treatments")
    axes[1].legend(fontsize=8)
    fig.savefig(output / "response.png", dpi=160)
    plt.close(fig)
    print(json.dumps(dict(checkpoints=len(rows), calibration=errors, zero_methane_k=base_temps(rows)), indent=2))


def base_temps(rows):
    return {r["case"]: r["temperature_k"] for r in rows if r["p_ch4_pa"] == 0}


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
