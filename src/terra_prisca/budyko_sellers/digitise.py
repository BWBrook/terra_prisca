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


def fit_line(ink: np.ndarray, vertical: bool, across: tuple[int, int], along: tuple[int, int]):
    """Least-squares fit of a ruled line: x = k*y + c if vertical, else y = k*x + c.
    `across` bounds the search perpendicular to the line, `along` its extent."""
    a0, a1 = across
    t = np.arange(*along)
    pos = []
    for u in t:
        strip = ink[u, a0:a1] if vertical else ink[a0:a1, u]
        c = np.nonzero(strip)[0]
        pos.append(np.median(c) + a0 if c.size else np.nan)
    pos = np.array(pos)
    ok = ~np.isnan(pos)
    for _ in range(4):
        k, c = np.polyfit(t[ok], pos[ok], 1)
        ok = np.abs(pos - (k * t + c)) < 1.5
    return float(k), float(c)


def line_points(line, vertical: bool, along) -> np.ndarray:
    """Pixels (x, y) sampled along a fitted line."""
    k, c = line
    t = np.linspace(along[0], along[1], 25)
    return np.column_stack([k * t + c, t]) if vertical else np.column_stack([t, k * t + c])


@dataclass(frozen=True)
class AffineFrame:
    """Data coordinates as affine functions of pixel (x, y); absorbs the small
    rotation and shear of a pasted-up, scanned figure."""

    cx: tuple[float, float, float]
    cy: tuple[float, float, float]
    box: tuple[int, int, int, int]
    residual: float  # largest calibration residual, in data units of the worse axis (relative)

    @classmethod
    def fit(cls, xpts, ypts, box):
        """xpts, ypts: rows (px, py, value) for the x and y data coordinates."""
        def plane(p):
            p = np.asarray(p, dtype=float)
            a = np.column_stack([p[:, 0], p[:, 1], np.ones(len(p))])
            coef, *_ = np.linalg.lstsq(a, p[:, 2], rcond=None)
            span = np.ptp(p[:, 2]) or 1.0
            return tuple(map(float, coef)), float(np.abs(a @ coef - p[:, 2]).max() / span)
        cx, rx = plane(xpts)
        cy, ry = plane(ypts)
        return cls(cx, cy, box, max(rx, ry))

    def to_data(self, pxy):
        pxy = np.atleast_2d(np.asarray(pxy, dtype=float))
        a = np.column_stack([pxy[:, 0], pxy[:, 1], np.ones(len(pxy))])
        return np.column_stack([a @ np.array(self.cx), a @ np.array(self.cy)])

    def to_px(self, xy):
        xy = np.atleast_2d(np.asarray(xy, dtype=float))
        m = np.array([self.cx[:2], self.cy[:2]])
        rhs = xy - np.array([self.cx[2], self.cy[2]])
        return np.linalg.solve(m, rhs.T).T

    def px_per_unit(self):
        """Pixels per data unit along x and y (for converting pixel distances)."""
        m = np.array([self.cx[:2], self.cy[:2]])
        inv = np.linalg.inv(m)
        return float(np.hypot(*inv[:, 0])), float(np.hypot(*inv[:, 1]))


def ring_score(ink: np.ndarray, box, r_in: float = 3.0, r_out: float = 6.0) -> np.ndarray:
    """Inked fraction of an annulus centred on each pixel of the box."""
    from scipy import ndimage

    x0, x1, y0, y1 = box
    r = int(np.ceil(r_out))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    d = np.hypot(xx, yy)
    ker = ((d >= r_in) & (d <= r_out)).astype(float)
    return ndimage.correlate(ink[y0:y1, x0:x1].astype(float), ker / ker.sum(), mode="constant")


def refine_ring(ink: np.ndarray, guess, search: int = 6, **kw) -> np.ndarray:
    """Centre of the circle nearest a hand-read position: the annulus-score maximum within `search` px."""
    gx, gy = guess
    sc = ring_score(ink, (gx - search, gx + search + 1, gy - search, gy + search + 1), **kw)
    iy, ix = np.unravel_index(np.argmax(sc), sc.shape)
    return np.array([gx - search + ix, gy - search + iy], dtype=float)


def refine_component(ink: np.ndarray, guess, radius: int = 14) -> np.ndarray:
    """Bounding-box centre of the isolated symbol (square, triangle) nearest a hand-read position."""
    from scipy import ndimage

    gx, gy = guess
    sub = ink[gy - radius:gy + radius + 1, gx - radius:gx + radius + 1]
    lab, _ = ndimage.label(sub, structure=np.ones((3, 3)))
    ys, xs = np.nonzero(lab)
    k = lab[ys[np.argmin(np.hypot(xs - radius, ys - radius))], xs[np.argmin(np.hypot(xs - radius, ys - radius))]]
    ys, xs = np.nonzero(lab == k)
    return np.array([gx - radius + 0.5 * (xs.min() + xs.max()), gy - radius + 0.5 * (ys.min() + ys.max())])


def find_rings(ink: np.ndarray, box, r_in: float = 3.0, r_out: float = 6.0,
               threshold: float = 0.7, separation: float = 8.0, scores: bool = False):
    """Centres (x, y) of the small open or filled circles that mark computed
    points: local maxima of the inked fraction of an annulus. A plain line
    crossing the annulus inks about a third of it; a circle inks nearly all."""
    from scipy import ndimage

    x0, x1, y0, y1 = box
    score = ring_score(ink, box, r_in, r_out)
    peak = (score == ndimage.maximum_filter(score, size=int(2 * separation) + 1)) & (score >= threshold)
    ys, xs = np.nonzero(peak)
    order = np.argsort(-score[ys, xs])
    kept = []
    for i in order:
        p = (xs[i], ys[i])
        if all(np.hypot(p[0] - q[0], p[1] - q[1]) >= separation for q in kept):
            kept.append(p)
    pts = np.array(kept, dtype=float).reshape(-1, 2)
    if scores:
        return pts + [x0, y0], np.array([score[int(p[1]), int(p[0])] for p in kept])
    return pts + [x0, y0]


def track(ink: np.ndarray, box, seed, max_gap: int = 30, window: int = 7, fit_cols: int = 25,
          exclude=(), strict: bool = False) -> np.ndarray:
    """Follow one printed curve column by column from a seed pixel, in both
    directions. In each column the ink run nearest the curve's extrapolated
    position (a straight-line fit to the last `fit_cols` columns) is taken, so
    the trace carries through crossings and across dash gaps of up to
    `max_gap` columns. With `strict`, a column where two runs lie within
    reach is treated as a gap, so the trace stops where curves converge
    instead of guessing. Returns (x, y) column centres along the curve."""
    x0, x1, y0, y1 = box
    mask = np.zeros_like(ink)
    mask[y0:y1, x0:x1] = ink[y0:y1, x0:x1]
    for ex0, ex1, ey0, ey1 in exclude:
        mask[ey0:ey1, ex0:ex1] = False

    def runs(col):
        ys = np.nonzero(col)[0]
        if ys.size == 0:
            return []
        breaks = np.nonzero(np.diff(ys) > 1)[0]
        starts = np.r_[ys[0], ys[breaks + 1]]
        ends = np.r_[ys[breaks], ys[-1]]
        return list(zip(starts, ends))

    sx, sy = seed
    out = {}
    for step in (1, -1):
        pts = [(sx, float(sy))]
        x, gap = sx, 0
        while x0 <= x + step < x1 and gap <= max_gap:
            x += step
            recent = np.array(pts[-fit_cols:])
            if len(recent) >= 4 and np.ptp(recent[:, 0]) > 0:
                k, c = np.polyfit(recent[:, 0], recent[:, 1], 1)
                pred = k * x + c
                slope = abs(k)
            else:
                pred, slope = pts[-1][1], 1.0
            tol = window + slope * (1 + gap)
            best, n_cand = None, 0
            for a, b in runs(mask[:, x]):
                if b - a > 4 * window + 4 * slope:  # a ruled line or lettering block
                    continue
                lo, hi = max(a, pred - tol), min(b, pred + tol)
                if lo > hi:
                    continue
                centre = 0.5 * (lo + hi) if b - a > 2 * window + 2 * slope else 0.5 * (a + b)
                d = abs(centre - pred)
                n_cand += 1
                if best is None or d < best[0]:
                    best = (d, centre)
            if best is None or (strict and n_cand > 1):
                gap += 1
                continue
            gap = 0
            pts.append((x, float(best[1])))
        for p in pts:
            out[p[0]] = p[1]
    xs = np.array(sorted(out))
    return np.column_stack([xs, [out[x] for x in xs]])
