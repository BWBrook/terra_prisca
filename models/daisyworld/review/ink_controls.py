"""Check axis contamination in the 1983 scan's nearest-ink fidelity score.

Run from the repository root:
    uv run python models/daisyworld/review/ink_controls.py PATH_TO_PDF OUTPUT_CSV

The original calibration is reused deliberately: this checks the score, not the
calibration. The area >5% subset excludes zero-area axis segments, but still
allows matches to other printed curves and is not a curve-identification test.
"""

import csv
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import numpy as np
from scipy.ndimage import distance_transform_edt

from terra_prisca.daisyworld.fidelity_1983 import (
    INK, PANELS, SCAN_SHA256, _resample, calibrate, model_curves,
)
from terra_prisca.daisyworld.wl1983 import EXPERIMENTS, hysteresis_sweep


def main(pdf: Path, output: Path) -> None:
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != SCAN_SHA256:
        raise ValueError("The panel calibration requires the scan identified in the model README")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([
            "pdftoppm", "-r", "300", "-f", "4", "-l", "5", "-png", str(pdf), f"{tmp}/p",
        ], check=True)
        pages = {n: mpimg.imread(next(Path(tmp).glob(f"p-*{n}.png"))) for n in (4, 5)}

    rows = []
    for name, frame in PANELS.items():
        ink = pages[frame[0]][..., :3].mean(axis=2) < INK
        dist = distance_transform_edt(~ink)
        cal = calibrate(ink, frame)
        up, down = hysteresis_sweep(0.6, 1.7, 0.002, EXPERIMENTS[name])
        curves = [c for c in model_curves(name, up, down, cal)
                  if c[0].startswith("up") and "area" in c[0]]
        curves.append(("all-zero null", cal["x"](up["lum"]),
                       np.full_like(up["lum"], cal["y_area"](0.0))))
        for label, x, y in curves:
            for subset in ("all", "area >5%"):
                keep = (x > frame[1] + 3) & (x < frame[2] - 3)
                if subset == "area >5%":
                    keep &= y < cal["y_area"](5.0)
                if keep.sum() < 2:
                    continue
                xs, ys = _resample(x[keep], y[keep])
                d = dist[np.round(ys).astype(int), np.round(xs).astype(int)]
                rows.append({"panel": name, "curve": label, "subset": subset,
                             "points": d.size, "median_px": round(float(np.median(d)), 2),
                             "frac_within_3px": round(float(np.mean(d <= 3)), 3)})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
