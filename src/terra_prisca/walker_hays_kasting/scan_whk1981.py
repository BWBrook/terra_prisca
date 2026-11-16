"""The printed figures of Walker, Hays & Kasting (1981), read from the journal scan.

The scan is the AGU/Wiley publisher PDF (7 pages, 300-ppi bilevel page images,
SHA-256 below); place it at local/sources/walker_hays_kasting/whk1981.pdf. It is
copyrighted and is not redistributed. Every tick, seed and box below was read
from the scan alone, never from model output.

Fig. 2 (page 5): each panel is calibrated by an affine map fitted to its tick
marks and labelled frame lines, which absorbs the slight rotation and shear of
the drafted original. The four solid curves of each panel are the connected
strokes containing a seed pixel. In panel a, the broken constant-P line touches
three of them; it is traced as its seven isolated dashes, a straight line is
fitted to those, and a band around that line is removed from the solid curves.

Fig. 1 (page 4): horizontal class segments (Meybeck's data) and the dashed
Lagache slope line of panel b. Its y axis carries only one tick (1.0) and the
labelled bottom frame (0.5), so its calibration has no redundancy.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import ndimage

from terra_prisca.budyko_sellers.digitise import AffineFrame, page_ink

SCAN_SHA256 = "e8efc69a42ad77e71644e32e512ec3a8225090b50ed7050597b548f8337a849a"
DEFAULT_PDF = Path("local/sources/walker_hays_kasting/whk1981.pdf")

FIG2_PAGE = 5
FIG1_PAGE = 4

# Fig. 2, x ticks (px, py, dTe) on the top frame, the shared middle line and the
# bottom frame, plus the left frame line, labelled -20 under the bottom corner.
FIG2_X = [(1780.5, 349, -10), (2001.0, 349, 0), (1779.5, 1005, -10), (1999.0, 1005, 0),
          (1775.5, 1795, -10), (1996.0, 1795, 0),
          (1557.0, 400, -20), (1557.0, 1700, -20)]
# y ticks (px, py, value): inner ticks on both sides; labelled frame lines.
FIG2_Y = {
    "a": [(1565.5, 562.0, 0), (1565.5, 783.0, -10), (2118.5, 567.0, 0), (2118.5, 788.0, -10),
          (1560.0, 341.0, 10), (2125.0, 342.5, 10), (1560.0, 1003.5, -20), (2125.0, 1005.5, -20)],
    "b": [(1565.5, 1136.0, 2), (1565.5, 1358.0, 1), (1565.5, 1579.0, 0),
          (2118.5, 1141.0, 2), (2118.5, 1363.0, 1), (2118.5, 1584.0, 0),
          (1560.0, 1799.5, -1), (2125.0, 1802.0, -1)],
}
FIG2_BOX = {"a": (1567, 2120, 348, 999), "b": (1567, 2120, 1011, 1795)}

# Seed pixels on each solid curve (read from columns 1580 and 1720 of the scan).
FIG2_SEEDS = {
    ("a", 4.0): (1580, 668), ("a", 2.0): (1580, 823), ("a", 1.0): (1580, 973), ("a", 0.5): (1720, 978),
    ("b", 4.0): (1580, 1023), ("b", 2.0): (1580, 1078), ("b", 1.0): (1580, 1142), ("b", 0.5): (1580, 1222),
}
# The seven dashes of the broken line that touch no solid curve (one pixel on each).
# Tick marks a curve runs into, removed from that curve (x0, x1, y0, y1).
FIG2_CLIP = {("b", 2.0): (2100, 2121, 1580, 1589)}
FIG2_DASHES = [(1789, 981), (1829, 908), (1867, 830), (1941, 683), (1977, 609), (2048, 467), (2081, 400)]
BAND_PX = 6.0  # half-width of the band around the broken line removed from solid curves

# Fig. 1.
FIG1_X = {
    "a": [(748.5, 540, 0), (859.5, 329, 200), (969.5, 329, 400), (1079.5, 329, 600), (1191.5, 540, 800),
          (858.5, 753, 200), (967.5, 753, 400), (1078.5, 753, 600)],
    "b": [(1245.5, 329, 0), (1353.5, 329, 5), (1465.5, 329, 10), (1574.5, 329, 15), (1685.5, 329, 20),
          (1795.5, 329, 25), (1244.5, 753, 0), (1353.5, 753, 5), (1464.5, 753, 10), (1573.0, 753, 15),
          (1684.5, 753, 20), (1794.5, 753, 25)],
}
# 1.0 ticks at the left frame, both sides of the middle frame and the right frame;
# the bottom frame, labelled 0.5.
FIG1_Y = [(760.0, 488.0, 1.0), (1180.0, 488.0, 1.0), (1205.0, 488.5, 1.0), (1840.0, 488.5, 1.0),
          (760.0, 759.0, 0.5), (1180.0, 759.0, 0.5), (1205.0, 759.0, 0.5), (1840.0, 759.0, 0.5)]
FIG1_BOX = {"a": (752, 1188, 327, 756), "b": (1196, 1848, 327, 756)}

# Fig. 1 class segments: (panel, temperature class, style) -> box (x0, x1, y0, y1)
# holding only that segment's strokes (dots of the dash-dot lines included).
FIG1_SEGMENTS = {
    ("a", "15-25", "short"): (750, 772, 380, 389),
    ("a", ">20", "upper, left"): (755, 915, 394, 409),
    ("a", ">20", "upper, right"): (1088, 1186, 394, 409),
    ("a", ">20", "lower"): (900, 1186, 448, 463),
    ("a", "4-15", "left"): (760, 908, 564, 573),
    ("a", "4-15", "middle"): (898, 1105, 602, 611),
    ("a", "4-15", "right"): (1088, 1186, 537, 546),
    ("a", "<4", "left"): (808, 910, 717, 727),
    ("a", "<4", "middle"): (896, 1103, 699, 709),
    ("a", "<4", "right"): (1090, 1186, 634, 644),
    ("b", "<4", "solid"): (1236, 1338, 678, 712),
    ("b", "4-15", "solid"): (1326, 1580, 546, 592),
    ("b", "15-25", "solid"): (1572, 1795, 376, 420),
    ("b", ">20", "dash-dot"): (1660, 1800, 420, 460),
}
# The dashes of the Lagache line in panel b that touch no segment.
FIG1_LAGACHE_DASHES = [(1221, 723), (1329, 658), (1401, 614), (1549, 525), (1620, 483), (1824, 361)]


@dataclass
class Scan:
    pages: dict[int, np.ndarray]
    fig2: dict[str, AffineFrame]
    fig1: dict[str, AffineFrame]
    curves: dict[tuple[str, float], np.ndarray]  # solid curves, pixels (x, y), band removed
    broken: np.ndarray  # isolated dashes of the constant-P line, pixels
    broken_line: tuple[float, float]  # fitted pixel line x = k*y + c
    band_removed: dict[tuple[str, float], int]  # pixels removed per curve
    segments: dict[tuple[str, str, str], np.ndarray]
    lagache: np.ndarray  # isolated dash pixels


def _labels(ink, box):
    x0, x1, y0, y1 = box
    m = np.zeros_like(ink)
    m[y0:y1, x0:x1] = ink[y0:y1, x0:x1]
    return ndimage.label(m, structure=np.ones((3, 3)))


def _pick(labels, seeds, search=6):
    ids = set()
    for sx, sy in seeds:
        win = labels[sy - search:sy + search + 1, sx - search:sx + search + 1]
        ys, xs = np.nonzero(win)
        if xs.size == 0:
            raise ValueError(f"no ink within {search} px of {(sx, sy)}")
        i = np.argmin(np.hypot(xs - search, ys - search))
        ids.add(int(win[ys[i], xs[i]]))
    return ids


def _pixels(labels, ids):
    ys, xs = np.nonzero(np.isin(labels, list(ids)))
    return np.column_stack([xs, ys]).astype(float)


def check(pdf: Path) -> None:
    digest = hashlib.sha256(Path(pdf).read_bytes()).hexdigest()
    if digest != SCAN_SHA256:
        raise ValueError(f"{pdf} has SHA-256 {digest}; the calibration is for {SCAN_SHA256}")


def load(pdf: Path = DEFAULT_PDF) -> Scan:
    check(pdf)
    pages = {p: page_ink(pdf, p) for p in (FIG1_PAGE, FIG2_PAGE)}
    ink2, ink1 = pages[FIG2_PAGE], pages[FIG1_PAGE]

    fig2 = {p: AffineFrame.fit(FIG2_X, FIG2_Y[p], FIG2_BOX[p]) for p in "ab"}
    fig1 = {p: AffineFrame.fit(FIG1_X[p], FIG1_Y, FIG1_BOX[p]) for p in "ab"}

    lab_a, _ = _labels(ink2, FIG2_BOX["a"])
    dash_ids = _pick(lab_a, FIG2_DASHES)
    if len(dash_ids) != len(FIG2_DASHES):
        raise ValueError("two dash seeds hit the same stroke")
    broken = _pixels(lab_a, dash_ids)
    k, c = np.polyfit(broken[:, 1], broken[:, 0], 1)
    norm = np.hypot(1.0, k)

    curves, removed = {}, {}
    for p in "ab":
        lab, _ = _labels(ink2, FIG2_BOX[p])
        for (panel, v), seed in FIG2_SEEDS.items():
            if panel != p:
                continue
            ids = _pick(lab, [seed])
            if ids & dash_ids and p == "a":
                raise ValueError(f"curve {v} seed landed on a dash")
            pix = _pixels(lab, ids)
            if (p, v) in FIG2_CLIP:
                x0, x1, y0, y1 = FIG2_CLIP[(p, v)]
                pix = pix[~((pix[:, 0] >= x0) & (pix[:, 0] < x1) & (pix[:, 1] >= y0) & (pix[:, 1] < y1))]
            if p == "a":
                d = np.abs(pix[:, 0] - (k * pix[:, 1] + c)) / norm
                keep = d > BAND_PX
                removed[(p, v)] = int((~keep).sum())
                pix = pix[keep]
            curves[(p, v)] = pix
    ids_all = [next(iter(_pick(lab_a, [s]))) for (pp, _), s in FIG2_SEEDS.items() if pp == "a"]
    if len(set(ids_all)) != 4:
        raise ValueError("two panel-a curves share a stroke")

    lab1, _ = _labels(ink1, (FIG1_BOX["a"][0], FIG1_BOX["b"][1], 327, 756))
    segments = {}
    for key, (x0, x1, y0, y1) in FIG1_SEGMENTS.items():
        sub = np.zeros_like(ink1)
        sub[y0:y1, x0:x1] = ink1[y0:y1, x0:x1]
        ys, xs = np.nonzero(sub)
        segments[key] = np.column_stack([xs, ys]).astype(float)
    lab_b, _ = _labels(ink1, FIG1_BOX["b"])
    lag_ids = _pick(lab_b, FIG1_LAGACHE_DASHES)
    if len(lag_ids) != len(FIG1_LAGACHE_DASHES):
        raise ValueError("two Lagache dash seeds hit the same stroke")
    lagache = _pixels(lab_b, lag_ids)
    return Scan(pages, fig2, fig1, curves, broken, (float(k), float(c)), removed, segments, lagache)


def column_trace(pix: np.ndarray, frame: AffineFrame, min_count: int = 2, max_spread_px: float = 8.0) -> np.ndarray:
    """Printed curve in data units: the median ink row of each pixel column,
    mapped through the affine frame. Columns whose ink spans more than
    max_spread_px (steep strokes, or a column still touching another mark) are
    dropped, so the result is defined only where the curve is single-valued."""
    out = []
    for col in np.unique(pix[:, 0]):
        ys = pix[pix[:, 0] == col, 1]
        if ys.size >= min_count and np.ptp(ys) <= max_spread_px:
            out.append((col, np.median(ys)))
    return frame.to_data(np.array(out)) if out else np.empty((0, 2))


def segment_level(pix: np.ndarray, frame: AffineFrame) -> tuple[float, float, float]:
    """(x start, x end, log10 concentration) of a horizontal class segment.

    The level is the modal ink row (the line itself, not the dots of a dash-dot
    line), and the ends are the extreme columns that carry ink on that row +-2 px."""
    rows, counts = np.unique(pix[:, 1], return_counts=True)
    r0 = rows[np.argmax(counts)]
    near = pix[np.abs(pix[:, 1] - r0) <= 2]
    centre = near[:, 1].mean()
    x0, x1 = near[:, 0].min(), near[:, 0].max()
    (a, lev), (b, _) = frame.to_data(np.array([[x0, centre], [x1, centre]]))
    return float(a), float(b), float(lev)
