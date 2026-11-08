"""Score the reconstruction against the published Figs 1 and 2 of Watson & Lovelock (1983).

    uv run python -m terra_prisca.daisyworld.fidelity_1983 PATH_TO_PDF [outdir]

Needs the 6-page scan of the paper (Tellus 35B, 284-289) with SHA-256 below, which
is not redistributed here; see models/daisyworld/README.md for where to obtain it.
Pages 4-5 are rendered at 300 dpi with poppler's pdftoppm, and each panel is
calibrated from its own tick marks.

Two scores are reported per panel:
- ink distance: for densely resampled points along each model curve that the paper
  plots, the distance to the nearest dark pixel of the scan, in pixels
  (1 px ~ 0.0017 in L, ~0.36 % area, ~0.25 deg C). Any ink counts, so zero-area
  stretches score perfectly by following the axis: a null row (an all-zero
  population) shows this per panel, and area curves are also scored on their
  occupied branch (area > 5 %) alone. Even that subset is a one-way nearest-ink
  score, not a match to an identified printed curve;
- transitions: luminosities of vertical jumps in the scan's area panel versus
  those in the reconstruction. They are transitions under the 0.01 reseeding
  protocol, not necessarily mathematical bifurcations.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import distance_transform_edt

from .wl1983 import EXPERIMENTS, hysteresis_sweep, lifeless_temperature

SCAN_SHA256 = "85b32bb0fa9e9314caaea4b4413fb6008c4eb10c7f29c9b1a7dc49333d3fef8f"
INK = 0.55
OCCUPIED_PCT = 5.0

# Panel frames in the 300-dpi renderings: page, inner y-axis x, right frame x, top
# frame y, area/temperature separator y (area 0), x-axis y (0 deg C).
PANELS = {
    "fig1a_neutral": (4, 195.0, 922.0, 495.5, 736.5, 1013.0),
    "fig1b_black": (4, 1178.5, 1903.0, 489.5, 735.0, 1014.0),
    "fig1c_white": (4, 192.5, 919.5, 1147.0, 1379.0, 1649.5),
    "fig1d_both": (4, 1170.5, 1894.0, 1143.0, 1376.5, 1648.0),
    "fig2_cloud": (5, 625.5, 1348.5, 482.5, 729.0, 1011.0),
}
# Which sweep directions each published panel shows (Fig. 1c alone shows decreasing L).
DIRECTIONS = {k: ("up",) for k in PANELS} | {"fig1c_white": ("up", "down")}


def _runs(mask: np.ndarray, gap: int = 2) -> np.ndarray:
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return np.array([])
    breaks = np.flatnonzero(np.diff(idx) > gap)
    starts = np.r_[idx[0], idx[breaks + 1]]
    ends = np.r_[idx[breaks], idx[-1]]
    return (starts + ends) / 2.0


def calibrate(ink: np.ndarray, frame: tuple) -> dict:
    _, xi, xr, ytop, ysep, yax = frame
    best = None
    for y0, y1 in ((yax - 11, yax - 7), (yax + 7, yax + 11), (yax - 8, yax - 5), (yax + 5, yax + 8)):
        tx = _runs(ink[int(y0):int(y1), int(xi) + 8:int(xr) - 5].any(axis=0)) + int(xi) + 8
        if tx.size < 5:
            continue
        d = np.median(np.diff(tx))
        k = np.round((tx - xi) / d)
        keep = np.abs((tx - xi) / d - k) < 0.12
        if best is None or keep.sum() > best[0]:
            best = (keep.sum(), tx[keep], k[keep])
    _, tx, k = best
    lum_a, lum_b = np.polyfit(tx, 0.5 + 0.1 * k, 1)  # inner axis is L = 0.5, ticks every 0.1
    ty = _runs(ink[int(ytop) + 4:int(yax) + 3, int(xi) + 4:int(xi) + 8].any(axis=1)) + int(ytop) + 4
    area_px = np.median(np.diff(ty[(ty > ytop + 5) & (ty < ysep - 3)]))  # ticks every 10 %
    temp_px = np.median(np.diff(ty[(ty > ysep + 3) & (ty < yax - 3)]))  # ticks every 10 deg C
    return {"x": lambda lum: (np.asarray(lum) - lum_b) / lum_a,
            "lum": lambda x: lum_a * np.asarray(x) + lum_b,
            "y_area": lambda pct: ysep - np.asarray(pct) / 10.0 * area_px,
            "y_temp": lambda t: yax - np.asarray(t) / 10.0 * temp_px,
            "n_ticks": int(len(tx))}


def _resample(x: np.ndarray, y: np.ndarray, spacing: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    seg = np.hypot(np.diff(x), np.diff(y))
    s = np.r_[0.0, np.cumsum(seg)]
    t = np.arange(0.0, s[-1], spacing)
    return np.interp(t, s, x), np.interp(t, s, y)


def model_curves(name: str, up: dict, down: dict, cal: dict) -> list[tuple[str, np.ndarray, np.ndarray]]:
    p = EXPERIMENTS[name]
    curves = []
    for direction in DIRECTIONS[name]:
        r = up if direction == "up" else down
        o = np.argsort(r["lum"]) if direction == "down" else slice(None)
        lum = r["lum"][o]
        x = cal["x"](lum)
        if p.white:
            curves.append((f"{direction} area white", x, cal["y_area"](100 * r["a_w"][o])))
        if p.black:
            curves.append((f"{direction} area black", x, cal["y_area"](100 * r["a_b"][o])))
        curves.append((f"{direction} temperature", x, cal["y_temp"](r["t_e"][o])))
    return curves


def scan_jumps(ink: np.ndarray, frame: tuple, cal: dict, heights=(8.0, 25.0, 50.0), tol_px: float = 14.0) -> list[float]:
    """Luminosities of near-vertical strokes: ink crossings at every one of `heights`
    (area %) lying within tol_px of each other horizontally. Lettering is too short
    to span 8-50 %, and sloping curves cross the three heights far apart."""
    _, xi, xr, *_ = frame
    lo, hi = int(xi) + 6, int(xr) - 6
    crossings = [_runs(ink[int(round(float(cal["y_area"](h)))), lo:hi]) + lo for h in heights]
    jumps = []
    for x0 in crossings[0]:
        xs = [x0]
        for c in crossings[1:]:
            near = c[np.abs(c - x0) <= tol_px] if c.size else c
            if near.size == 0:
                break
            xs.append(near[np.argmin(np.abs(near - x0))])
        else:
            jumps.append(float(cal["lum"](np.mean(xs))))
    return jumps


def model_jumps(r: dict, min_jump: float = 0.15) -> list[float]:
    total = r["a_w"] + r["a_b"]
    i = np.flatnonzero(np.abs(np.diff(total)) > min_jump)
    return [float((r["lum"][j] + r["lum"][j + 1]) / 2) for j in i]


def main(pdf: Path, outdir: Path) -> None:
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if digest != SCAN_SHA256:
        sys.exit(f"{pdf} has SHA-256 {digest}; the calibration is for {SCAN_SHA256}")
    outdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", "300", "-f", "4", "-l", "5", "-png", str(pdf), f"{tmp}/p"], check=True)
        pages = {n: mpimg.imread(next(Path(tmp).glob(f"p-*{n}.png"))) for n in (4, 5)}
    rows, overlay = [], plt.figure(figsize=(13, 13))
    for k, (name, frame) in enumerate(PANELS.items()):
        img = pages[frame[0]]
        ink = img[..., :3].mean(axis=2) < INK
        dist = distance_transform_edt(~ink)
        cal = calibrate(ink, frame)
        up, down = hysteresis_sweep(0.6, 1.7, 0.002, EXPERIMENTS[name])
        ax = overlay.add_subplot(3, 2, k + 1)
        _, xi, xr, ytop, _, yax = frame
        ax.imshow(img[int(ytop) - 30:int(yax) + 60, int(xi) - 60:int(xr) + 20], cmap="gray",
                  extent=(xi - 60, xr + 20, yax + 60, ytop - 30))
        zero_axis = ("null: all-zero area", cal["x"](up["lum"]), np.full_like(up["lum"], float(cal["y_area"](0.0))))
        for label, x, y in model_curves(name, up, down, cal) + [zero_axis]:
            is_area = "area" in label
            if is_area and not label.startswith("null") and np.all(y >= cal["y_area"](0.0) - 1e-9):
                continue  # a species that never occurs only traces the axis (see the null row)
            subsets = [("full", np.ones_like(x, dtype=bool))]
            if is_area and not label.startswith("null"):
                subsets.append(("occupied (>5 %)", y < cal["y_area"](OCCUPIED_PCT)))
            for subset, mask in subsets:
                keep = mask & (x > xi + 3) & (x < xr - 3)
                if keep.sum() < 2:
                    continue
                xs, ys = _resample(x[keep], y[keep])
                d = dist[np.round(ys).astype(int), np.round(xs).astype(int)]
                rows.append({"panel": name, "curve": label, "subset": subset, "points": d.size,
                             "median_px": round(float(np.median(d)), 2), "p95_px": round(float(np.percentile(d, 95)), 2),
                             "frac_within_3px": round(float(np.mean(d <= 3)), 3)})
            if not label.startswith("null"):
                ax.plot(x, y, "-" if label.startswith("up") else "--",
                        color="red" if label.startswith("up") else "dodgerblue", lw=0.9, alpha=0.7)
        lums = up["lum"]
        ax.plot(cal["x"](lums), cal["y_temp"](lifeless_temperature(lums, EXPERIMENTS[name])), ":", color="green", lw=0.8)
        ax.set_title(f"{name}: scan (black), reconstruction (red up, blue down)", fontsize=8)
        ax.axis("off")
        jumps_model = sorted(model_jumps(up) + (model_jumps(down) if "down" in DIRECTIONS[name] else []))
        rows.append({"panel": name, "curve": "transitions", "scan_jumps_L": [round(v, 3) for v in scan_jumps(ink, frame, cal)],
                     "model_jumps_L": [round(v, 3) for v in jumps_model]})
    overlay.tight_layout()
    overlay.savefig(outdir / "wl1983_overlay.png", dpi=110)
    fields = ["panel", "curve", "subset", "points", "median_px", "p95_px", "frac_within_3px", "scan_jumps_L", "model_jumps_L"]
    with (outdir / "wl1983_fidelity.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print({k: v for k, v in r.items() if v is not None})


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else Path("local/fidelity"))
