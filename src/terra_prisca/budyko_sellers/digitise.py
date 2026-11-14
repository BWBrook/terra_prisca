"""Calibrate and trace printed line figures from 1-bit journal scans.

Shared by the Budyko (1969) and Sellers (1969) fidelity checks. Each printed
curve is identified separately, as the connected ink strokes chosen by seed
pixels (solid curves) or by a box and a size range (dashes). Seeds and boxes
are read from the scan alone, never from model output, so the traced curves
are independent of the reconstruction.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import matplotlib.image as mpimg
import numpy as np
from scipy.spatial import cKDTree


def page_ink(pdf: Path, page: int) -> np.ndarray:
    """Boolean ink mask of the embedded page scan, at its native resolution."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdfimages", "-png", "-f", str(page), "-l", str(page), str(pdf), f"{tmp}/p"], check=True)
        img = mpimg.imread(sorted(Path(tmp).glob("p-*.png"))[0])
    if img.ndim == 3:
        img = img[..., :3].mean(axis=2)
    return img < 0.5


@dataclass(frozen=True)
class Axis:
    """Linear map from pixel coordinate to data value, fitted to tick marks."""

    slope: float
    intercept: float
    residual: float  # largest tick residual, in pixels

    @classmethod
    def from_ticks(cls, ticks: list[tuple[float, float]]) -> "Axis":
        px, val = np.array(ticks, dtype=float).T
        slope, intercept = np.polyfit(px, val, 1)
        resid = np.abs((val - intercept) / slope - px).max()
        return cls(float(slope), float(intercept), float(resid))

    def value(self, px):
        return self.slope * np.asarray(px, dtype=float) + self.intercept

    def pixel(self, val):
        return (np.asarray(val, dtype=float) - self.intercept) / self.slope


@dataclass(frozen=True)
class Frame:
    """A calibrated plot: x and y axes plus the pixel box holding the curves."""

    x: Axis
    y: Axis
    box: tuple[int, int, int, int]  # x0, x1, y0, y1 in pixels
    axis_px: tuple[float, float]  # pixel x of the y-axis line, pixel y of the x-axis line
    exclude: tuple[tuple[int, int, int, int], ...] = ()  # lettering, as x0, x1, y0, y1

    def to_px(self, xy: np.ndarray) -> np.ndarray:
        xy = np.asarray(xy, dtype=float)
        return np.column_stack([self.x.pixel(xy[:, 0]), self.y.pixel(xy[:, 1])])

    def to_data(self, pxy: np.ndarray) -> np.ndarray:
        pxy = np.asarray(pxy, dtype=float)
        return np.column_stack([self.x.value(pxy[:, 0]), self.y.value(pxy[:, 1])])

    def curve_pixels(self, ink: np.ndarray, axis_halfwidth: int = 3) -> np.ndarray:
        x0, x1, y0, y1 = self.box
        mask = np.zeros_like(ink)
        mask[y0:y1, x0:x1] = ink[y0:y1, x0:x1]
        ax_x, ax_y = (int(round(v)) for v in self.axis_px)
        mask[:, ax_x - axis_halfwidth:ax_x + axis_halfwidth + 1] = False
        mask[ax_y - axis_halfwidth:ax_y + axis_halfwidth + 1, :] = False
        for ex0, ex1, ey0, ey1 in self.exclude:
            mask[ey0:ey1, ex0:ex1] = False
        ys, xs = np.nonzero(mask)
        return np.column_stack([xs, ys]).astype(float)


def components(ink: np.ndarray, frame: Frame):
    """Connected ink strokes inside the frame, with the axis lines removed."""
    from scipy import ndimage

    pix = frame.curve_pixels(ink).astype(int)
    mask = np.zeros_like(ink)
    mask[pix[:, 1], pix[:, 0]] = True
    labels, n = ndimage.label(mask, structure=np.ones((3, 3)))
    return labels, n


def select_strokes(labels: np.ndarray, n: int, seeds=(), box=None, size=(1, np.inf),
                   drop=(), search_px: int = 6) -> np.ndarray:
    """Pixels (x, y) of the strokes chosen either by seed points (each takes the
    stroke nearest the seed) or by a bounding box and a size range (dashes).
    Strokes whose first pixel lies in a `drop` box (lettering) are excluded."""
    from scipy import ndimage

    chosen = set()
    for sx, sy in seeds:
        win = labels[sy - search_px:sy + search_px + 1, sx - search_px:sx + search_px + 1]
        ys, xs = np.nonzero(win)
        if xs.size == 0:
            raise ValueError(f"no ink within {search_px} px of seed {(sx, sy)}")
        i = np.argmin(np.hypot(xs - search_px, ys - search_px))
        chosen.add(int(win[ys[i], xs[i]]))
    if box is not None:
        x0, x1, y0, y1 = box
        sizes = ndimage.sum(labels > 0, labels, range(1, n + 1))
        for i, sl in enumerate(ndimage.find_objects(labels)):
            ys, xs = sl
            inside = x0 <= xs.start and xs.stop <= x1 and y0 <= ys.start and ys.stop <= y1
            dropped = any(d[0] <= xs.start < d[1] and d[2] <= ys.start < d[3] for d in drop)
            if inside and not dropped and size[0] <= sizes[i] <= size[1]:
                chosen.add(i + 1)
    ys, xs = np.nonzero(np.isin(labels, list(chosen)))
    return np.column_stack([xs, ys]).astype(float)


def densify(poly: np.ndarray, spacing: float = 0.5) -> np.ndarray:
    poly = np.asarray(poly, dtype=float)
    seg = np.hypot(*np.diff(poly, axis=0).T)
    s = np.r_[0.0, np.cumsum(seg)]
    t = np.arange(0.0, s[-1] + spacing, spacing)
    return np.column_stack([np.interp(t, s, poly[:, 0]), np.interp(t, s, poly[:, 1])])


def column_median(pix: np.ndarray, frame: Frame, min_count: int = 2, max_spread_px: float = 8.0) -> np.ndarray:
    """Printed curve as y(x): the median ink row in each pixel column, in data units.

    Columns whose ink spans more than max_spread_px (steep or vertical strokes)
    are dropped, so the result is defined only where the curve is single-valued."""
    cols = np.unique(pix[:, 0])
    out = []
    for c in cols:
        ys = pix[pix[:, 0] == c, 1]
        if ys.size >= min_count and np.ptp(ys) <= max_spread_px:
            out.append((c, np.median(ys)))
    return frame.to_data(np.array(out)) if out else np.empty((0, 2))


def chamfer(model_px: np.ndarray, ink_px: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Two-way distances, in pixels: model samples to the traced ink, and traced ink to the model."""
    dense = densify(model_px)
    to_ink = cKDTree(ink_px).query(dense)[0]
    to_model = cKDTree(dense).query(ink_px)[0]
    return to_ink, to_model
