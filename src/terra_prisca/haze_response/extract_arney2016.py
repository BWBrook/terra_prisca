"""Extract Fig. 4 vector polylines from the authors' accepted manuscript.

uv run python -m terra_prisca.haze_response.extract_arney2016 PDF OUTPUT_DIRECTORY

Only numerical coordinates and derived plots are written. The PDF and Poppler
SVG conversion stay outside the output directory and are not redistributed.
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

SOURCE_SHA256 = "a61f0bfdc3051ea7471af981faa0f85806b4967d8639db6804ad44d70b04ebca"
CASES = {
    "A": dict(pco2_bar=0.01, pressure_bar=1.0, xmin=0.0014, xmax=0.0026,
              onset_ratio=0.18, max_clear_k=284, stabilized_k=263, ice_k=257),
    "B": dict(pco2_bar=0.018, pressure_bar=1.0, xmin=0.0016, xmax=0.0045,
              onset_ratio=0.15, max_clear_k=299, stabilized_k=274, ice_k=271),
    "C": dict(pco2_bar=0.01, pressure_bar=0.5, xmin=0.0014, xmax=0.0026,
              onset_ratio=0.19, max_clear_k=282, stabilized_k=262, ice_k=257),
    "D": dict(pco2_bar=0.0036, pressure_bar=0.5, xmin=0.0005, xmax=0.0019,
              onset_ratio=0.28, max_clear_k=273, stabilized_k=251, ice_k=241),
}


def points(path: ET.Element) -> np.ndarray:
    raw = path.attrib["d"]
    if re.search(r"[A-KN-Za-kn-z]", raw):
        raise ValueError("Expected a polyline with absolute M/L commands")
    values = np.array([float(v) for v in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", raw)])
    xy = values.reshape(-1, 2)
    matrix = path.get("transform", "")
    if matrix:
        if not matrix.startswith("matrix("):
            raise ValueError("Unexpected SVG coordinate transform")
        a, b, c, d, e, f = map(float, re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", matrix))
        xy = xy @ np.array([[a, b], [c, d]]) + [e, f]
    return xy


def extract(svg: Path) -> tuple[list[dict], list[dict]]:
    root = ET.parse(svg).getroot()
    curves, frames, references, markers = [], [], [], []
    for path in root.iter("{http://www.w3.org/2000/svg}path"):
        stroke = path.get("stroke", "")
        width = float(path.get("stroke-width", "0"))
        if stroke.startswith("rgb(27.45") and width > 3:
            curves.append(points(path))
        elif stroke == "rgb(0%, 0%, 0%)" and 0 < width < 0.5:
            xy = points(path)
            if len(xy) >= 2 and abs(xy[0, 1] - xy[1, 1]) < 1e-5 and xy[1, 0] - xy[0, 0] > 100:
                frames.append(xy[:2])
        elif "stroke-dasharray" in path.attrib and width > 3:
            references.append(points(path))
        elif stroke.startswith("rgb(100%, 58.03") and 2 < width < 3:
            markers.append(points(path))
    if len(curves) != 4:
        raise ValueError(f"Expected four grey response curves, found {len(curves)}")
    curves.sort(key=lambda xy: np.mean(xy[:, 1]))
    curves = sorted(curves[:2], key=lambda xy: xy[:, 0].mean()) + sorted(curves[2:], key=lambda xy: xy[:, 0].mean())
    rows, checks = [], []
    for (case, config), xy in zip(CASES.items(), curves, strict=True):
        spanning = [fr for fr in frames if fr[0, 0] < xy[:, 0].min() and fr[1, 0] > xy[:, 0].max()]
        bottom = min((fr for fr in spanning if fr[0, 1] > xy[:, 1].max()), key=lambda fr: fr[0, 1])
        top = max((fr for fr in spanning if fr[0, 1] < xy[:, 1].min()), key=lambda fr: fr[0, 1])
        x0, x1 = bottom[:, 0]
        y_bottom, y_top = bottom[0, 1], top[0, 1]
        if not np.allclose(top[:, 0], bottom[:, 0]):
            raise ValueError("Panel frame edges disagree")
        pressure = config["xmin"] + (xy[:, 0] - x0) / (x1 - x0) * (config["xmax"] - config["xmin"])
        temperature = 240 + (y_bottom - xy[:, 1]) / (y_bottom - y_top) * 70
        if not np.all(np.diff(pressure) > 0):
            raise ValueError("Expected increasing methane along each response")
        ref_t = []
        for line in references:
            if (line[:, 0].min() > x0 and line[:, 0].max() < x1
                    and y_top < line[0, 1] < y_bottom):
                ref_t.append(240 + (y_bottom - line[0, 1]) / (y_bottom - y_top) * 70)
        if len(ref_t) != 2 or not np.allclose(sorted(ref_t), [248, 273.15], atol=0.02):
            raise ValueError(f"Reference-line calibration failed for case {case}: {ref_t}")
        marker = [line.mean(axis=0) for line in markers
                  if np.all((line[:, 0] > x0) & (line[:, 0] < x1)
                            & (line[:, 1] > y_top) & (line[:, 1] < y_bottom))]
        if len(marker) != 1:
            raise ValueError(f"Expected one cooling-onset marker in case {case}")
        cooling_ratio = (config["xmin"] + (marker[0][0] - x0) / (x1 - x0)
                         * (config["xmax"] - config["xmin"])) / config["pco2_bar"]
        for i, (p, t) in enumerate(zip(pressure, temperature, strict=True)):
            rows.append(dict(case=case, vertex=i, p_ch4_bar=round(float(p), 10),
                             ch4_co2_ratio=round(float(p / config["pco2_bar"]), 8),
                             temperature_k=round(float(t), 3)))
        checks.append(dict(case=case, vertices=len(xy), reference_line_k=sorted(ref_t),
                           figure_cooling_onset_ratio=float(cooling_ratio),
                           table_haze_formation_ratio=config["onset_ratio"],
                           vector_max_k=float(temperature.max()), table_max_clear_k=config["max_clear_k"],
                           max_difference_k=float(temperature.max() - config["max_clear_k"]),
                           last_vertex_k=float(temperature[-1]), table_stabilized_k=config["stabilized_k"],
                           last_difference_k=float(temperature[-1] - config["stabilized_k"])))
    return rows, checks


def main(pdf: Path, outdir: Path) -> None:
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Extraction is defined only for the checksum-identified arXiv v1 PDF")
    with tempfile.TemporaryDirectory() as tmp:
        svg = Path(tmp) / "figure4.svg"
        subprocess.run(["pdftocairo", "-f", "65", "-l", "65", "-svg", str(pdf), str(svg)], check=True)
        rows, checks = extract(svg)
    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / "figure4.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with (outdir / "cases.csv").open("w", newline="") as fh:
        fields = ["case", "p_co2_bar", "surface_pressure_bar", "solar_fraction", "epoch_ga", "surface_albedo",
                  "haze_formation_ratio", "table_max_clear_k", "table_stabilized_k", "table_ice_k"]
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(fields)
        for case, c in CASES.items():
            writer.writerow([case, c["pco2_bar"], c["pressure_bar"], 0.81, 2.7, 0.32,
                             c["onset_ratio"], c["max_clear_k"], c["stabilized_k"], c["ice_k"]])
    (outdir / "checkpoint_comparison.json").write_text(json.dumps(checks, indent=2) + "\n")
    fig, axes = plt.subplots(2, 2, figsize=(9, 6), constrained_layout=True)
    for ax, (case, c) in zip(axes.flat, CASES.items(), strict=True):
        subset = [r for r in rows if r["case"] == case]
        ratio = [r["ch4_co2_ratio"] for r in subset]
        temps = [r["temperature_k"] for r in subset]
        ax.plot(ratio, temps, "o-", color="#244c62", markersize=3, label="Figure 4 vector vertices")
        ax.axhline(c["max_clear_k"], ls="--", color="#d17b18", lw=1, label="Table 2 clear maximum")
        ax.axhline(c["stabilized_k"], ls=":", color="#d17b18", lw=1, label="Table 2 stabilized")
        ax.axhline(273.15, ls="--", color="0.75", lw=0.7)
        ax.set(title=f"Case {case}: CO₂ {c['pco2_bar']} bar, total {c['pressure_bar']} bar",
               xlabel="Surface CH₄ / CO₂", ylabel="Surface temperature (K)", ylim=(245, 303))
    axes[0, 0].legend(fontsize=7)
    fig.suptitle("Arney et al. (2016): extracted equilibrium response at 2.7 Ga")
    fig.savefig(outdir / "response.png", dpi=160)
    plt.close(fig)
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
