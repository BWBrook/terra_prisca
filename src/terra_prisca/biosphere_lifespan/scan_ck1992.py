"""Fig. 2 of Caldeira & Kasting (1992), read from the journal scan.

The scan is the Nature publisher PDF (3 pages, each a 650-ppi bilevel stencil;
SHA-256 below); place it at local/sources/biosphere_lifespan/caldeira_kasting1992.pdf.
It is copyrighted and is not redistributed. Every tick and knot below was read
from the scan alone, never from model output.

Fig. 2 has two panels sharing a time axis, 0-1.6 Gyr:

  - upper: pCO2 (ppm, log, 1-10,000; left) with Psoil and Patm, and S/S0
    (1.00-1.20; right);
  - lower: Pi/Pi0 (0-1.0; left) and T (273-373 K; right).

The page is rotated and sheared by a few pixels over the figure. Each panel's
frame lines are fitted; pixel (x, y) is mapped to u = x - kv*y and
v = y - kh*x, where kh and kv are the mean slopes of the panel's horizontal and
vertical frame lines, and every scale is a linear map of u or v fitted to its
ticks. The time ticks are the 15 inward ticks on each panel's top frame
(0.1-1.5 Gyr); the pCO2 scale uses its five decade ticks; S/S0, Pi/Pi0 and T
use every tick.

Each curve is traced from hand-read knots by refining a dense polyline along
its normals: at each sample the normal window (+-HALF px) must hold a single
ink run no thicker than MAX_RUN px, whose centre becomes the trace point. A
sample whose window holds no run, two runs, or a merged run, or which lies in
an excluded box (crossings, labels, the junction of Psoil and Patm, frames),
is dropped and counted.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from terra_prisca.budyko_sellers.digitise import Axis, densify, fit_line, page_ink

SCAN_SHA256 = "3fc7926249fdb3faa961e21f3d34029b68e7f7ec1e7549ad6cb34904a250b7b9"
DEFAULT_PDF = Path("local/sources/biosphere_lifespan/caldeira_kasting1992.pdf")
PAGE = 3

# Frame-line search windows: (across, along) for fit_line.
FRAMES = {
    "upper": {"left": ((860, 900), (560, 1410)), "right": ((2065, 2100), (560, 1410)),
              "top": ((535, 560), (900, 2070)), "bottom": ((1410, 1440), (900, 2070))},
    "lower": {"left": ((860, 900), (1530, 2380)), "right": ((2065, 2100), (1530, 2380)),
              "top": ((1500, 1530), (900, 2070)), "bottom": ((2385, 2410), (900, 2070))},
}
TICK_DEPTH = (7, 14)     # px from the frame line's fitted centre, inward or outward
MINOR_DEPTH = (6, 10)


@dataclass(frozen=True)
class AxisSpec:
    frame: str          # which frame line the ticks sit on
    outward: bool       # ticks point away from the plot
    values: tuple       # tick values in order of increasing pixel coordinate
    depth: tuple = TICK_DEPTH
    span: tuple | None = None   # pixel range along the frame to search


TIME_VALUES = tuple(round(0.1 * i, 1) for i in range(1, 16))
AXES = {
    ("upper", "time"): AxisSpec("top", False, TIME_VALUES, span=(920, 2050)),
    ("lower", "time"): AxisSpec("top", False, TIME_VALUES, span=(920, 2035)),
    ("upper", "log10_ppm"): AxisSpec("left", True, (4.0, 3.0, 2.0, 1.0, 0.0), span=(540, 1440)),
    ("upper", "S_ratio"): AxisSpec("right", True, tuple(round(1.20 - 0.01 * i, 2) for i in range(21)),
                                   depth=MINOR_DEPTH, span=(540, 1440)),
    ("lower", "Pi_ratio"): AxisSpec("left", True, tuple(round(1.0 - 0.1 * i, 1) for i in range(11)),
                                    depth=MINOR_DEPTH, span=(1500, 2410)),
    ("lower", "T_K"): AxisSpec("right", True, tuple(373.0 - 10.0 * i for i in range(11)),
                               depth=MINOR_DEPTH, span=(1500, 2410)),
}
CURVE_AXES = {"P_soil": ("upper", "log10_ppm"), "P_atm": ("upper", "log10_ppm"),
              "merged": ("upper", "log10_ppm"), "S_ratio": ("upper", "S_ratio"),
              "Pi_ratio": ("lower", "Pi_ratio"), "T_K": ("lower", "T_K")}

# Knots (x, y) read from the scan, in order of increasing time.
KNOTS = {
    "P_soil": [(895, 651), (1000, 664), (1100, 691), (1200, 736), (1250, 766), (1300, 801),
               (1350, 846), (1400, 896), (1450, 956), (1475, 996), (1500, 1046), (1510, 1086),
               (1515, 1130), (1520, 1170), (1528, 1200)],
    "P_atm": [(895, 882), (1000, 935), (1100, 986), (1200, 1040), (1300, 1095), (1400, 1150),
              (1450, 1174), (1500, 1196), (1525, 1207)],
    "merged": [(1538, 1220), (1560, 1252), (1600, 1312), (1625, 1360), (1640, 1398), (1648, 1416)],
    "S_ratio": [(895, 1421), (1000, 1366), (1200, 1262), (1400, 1157), (1600, 1048), (1800, 935),
                (2000, 816), (2075, 770)],
    "Pi_ratio": [(890, 1520), (950, 1607), (1000, 1692), (1100, 1880), (1200, 2052), (1285, 2222),
                 (1350, 2290), (1400, 2333), (1450, 2365), (1500, 2384), (1540, 2392)],
    "T_K": [(895, 2258), (1000, 2252), (1100, 2245), (1200, 2235), (1285, 2222), (1350, 2212),
            (1400, 2200), (1450, 2186), (1500, 2170), (1550, 2161), (1600, 2160), (1650, 2151),
            (1700, 2131), (1750, 2101), (1800, 2065), (1850, 2010), (1900, 1930), (1950, 1822),
            (2000, 1690), (2040, 1565), (2054, 1522)],
}
HALF = 10
MAX_RUN = 13   # strokes are 6-9 px thick along the normal; a taller run is two strokes merged
STEP = 2.0     # px between samples along the polyline

# Excluded boxes (x0, x1, y0, y1): crossings and junctions of two curves, and
# the stretch of Psoil that the subscript of its label touches.
EXCLUDE = {
    "Psoil x S": (1490, 1530, 1070, 1120),
    "Patm x S": (1395, 1440, 1135, 1180),
    "Psoil-Patm junction": (1515, 1545, 1195, 1225),
    "Pi x T": (1265, 1305, 2200, 2245),
    "Psoil label": (1065, 1150, 640, 712),
}
FRAME_MARGIN = 12  # px kept clear of every frame line


def check(pdf: Path) -> None:
    digest = hashlib.sha256(Path(pdf).read_bytes()).hexdigest()
    if digest != SCAN_SHA256:
        raise ValueError(f"{pdf} has SHA-256 {digest}; the calibration is for {SCAN_SHA256}")


@dataclass(frozen=True)
class Panel:
    kh: float
    kv: float
    lines: dict  # name -> (k, c) from fit_line

    def u(self, x, y):
        return np.asarray(x, float) - self.kv * np.asarray(y, float)

    def v(self, x, y):
        return np.asarray(y, float) - self.kh * np.asarray(x, float)

    def xy(self, u, v):
        """Inverse of (u, v)."""
        u, v = np.asarray(u, float), np.asarray(v, float)
        x = (u + self.kv * v) / (1.0 - self.kv * self.kh)
        return x, v + self.kh * x


def ink_mask(pdf: Path) -> np.ndarray:
    ink = page_ink(pdf, PAGE)
    return ~ink if ink.mean() > 0.5 else ink  # the stencil comes out inverted


def fit_panel(ink: np.ndarray, name: str) -> Panel:
    f = FRAMES[name]
    lines = {side: fit_line(ink, side in ("left", "right"), *f[side]) for side in f}
    kh = 0.5 * (lines["top"][0] + lines["bottom"][0])
    kv = 0.5 * (lines["left"][0] + lines["right"][0])
    return Panel(kh, kv, lines)


def _runs(idx: np.ndarray) -> list[np.ndarray]:
    return np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1) if idx.size else []


def ticks(ink: np.ndarray, panel: Panel, spec: AxisSpec) -> np.ndarray:
    """Tick centres along a frame line, as (position along, position across) in
    pixels: runs of rows (or columns) whose ink fills the band TICK_DEPTH off
    the frame, on the tick side."""
    k, c = panel.lines[spec.frame]
    vertical = spec.frame in ("left", "right")
    sign = {"left": -1, "right": 1, "top": -1, "bottom": 1}[spec.frame] * (1 if spec.outward else -1)
    lo, hi = spec.depth
    along = np.arange(*spec.span)
    fill = []
    for a in along:
        centre = k * a + c
        off = np.arange(lo, hi) * sign
        idx = np.round(centre + off).astype(int)
        fill.append(ink[a, idx].mean() if vertical else ink[idx, a].mean())
    hits = _runs(np.nonzero(np.array(fill) > 0.7)[0])
    centres = np.array([along[h].mean() for h in hits])
    return np.column_stack([centres, k * centres + c])


def _assign(found: np.ndarray, n: int) -> np.ndarray:
    """Keep the n tick runs that sit on a uniform spacing (labels or curves that
    touch the frame make extra runs)."""
    pos = found[:, 0]
    if len(pos) == n:
        return found
    best = None
    for i in range(len(pos)):
        for j in range(i + 1, len(pos)):
            step = (pos[j] - pos[i]) / max(1, round((pos[j] - pos[i]) / ((pos[-1] - pos[0]) / (n - 1))))
            grid = pos[i] + step * (np.arange(n) - round((pos[i] - pos[0]) / step))
            pick = [int(np.argmin(np.abs(pos - g))) for g in grid]
            err = np.abs(pos[pick] - grid).max()
            if len(set(pick)) == n and (best is None or err < best[0]):
                best = (err, pick)
    return found[best[1]]


def axis(ink: np.ndarray, panel: Panel, spec: AxisSpec) -> Axis:
    found = ticks(ink, panel, spec)
    if spec.frame in ("left", "right"):
        found = _assign(found, len(spec.values)) if len(found) != len(spec.values) else found
        coord = panel.v(found[:, 1], found[:, 0])  # (x on frame, y along)
    else:
        found = _assign(found, len(spec.values)) if len(found) != len(spec.values) else found
        coord = panel.u(found[:, 0], found[:, 1])
    if len(found) != len(spec.values):
        raise ValueError(f"found {len(found)} ticks, expected {len(spec.values)}")
    return Axis.from_ticks(list(zip(coord, spec.values)))


@dataclass(frozen=True)
class Scan:
    ink: np.ndarray
    panels: dict
    axes: dict

    def to_data(self, curve: str, px: np.ndarray) -> np.ndarray:
        """(x, y) pixels of a curve to (t Gyr, value), value in the curve's units
        (log10 ppm for pCO2)."""
        pname, aname = CURVE_AXES[curve]
        p = self.panels[pname]
        x, y = px[:, 0], px[:, 1]
        return np.column_stack([self.axes[(pname, "time")].value(p.u(x, y)),
                                self.axes[(pname, aname)].value(p.v(x, y))])

    def to_px(self, curve: str, data: np.ndarray) -> np.ndarray:
        pname, aname = CURVE_AXES[curve]
        p = self.panels[pname]
        u = self.axes[(pname, "time")].pixel(data[:, 0])
        v = self.axes[(pname, aname)].pixel(data[:, 1])
        return np.column_stack(p.xy(u, v))


def load(pdf: Path = DEFAULT_PDF) -> Scan:
    check(pdf)
    ink = ink_mask(pdf)
    panels = {n: fit_panel(ink, n) for n in FRAMES}
    axes = {key: axis(ink, panels[key[0]], spec) for key, spec in AXES.items()}
    return Scan(ink, panels, axes)


@dataclass(frozen=True)
class Trace:
    centres: np.ndarray   # (x, y) per accepted sample, in order along the curve
    dropped: np.ndarray   # (x, y) of the samples left out
    reasons: dict         # count of dropped samples by reason


def _excluded(x: float, y: float, sc: Scan, pname: str) -> str | None:
    for name, (x0, x1, y0, y1) in EXCLUDE.items():
        if x0 <= x <= x1 and y0 <= y <= y1:
            return name
    p = sc.panels[pname]
    for side, (k, c) in p.lines.items():
        d = abs(x - (k * y + c)) if side in ("left", "right") else abs(y - (k * x + c))
        if d < FRAME_MARGIN:
            return "frame"
    return None


def trace(sc: Scan, curve: str, half: int = HALF, iters: int = 4) -> Trace:
    pname = CURVE_AXES[curve][0]
    pts = densify(np.array(KNOTS[curve], float), STEP)
    h, w = sc.ink.shape
    for it in range(iters):
        d = np.gradient(pts, axis=0)
        n = np.column_stack([-d[:, 1], d[:, 0]]) / np.hypot(d[:, 0], d[:, 1])[:, None]
        new, ok, why = pts.copy(), np.zeros(len(pts), bool), []
        offs = np.arange(-half, half + 1)
        for i, (p, nv) in enumerate(zip(pts, n)):
            reason = _excluded(*p, sc, pname)
            if reason is None:
                q = np.round(p + offs[:, None] * nv).astype(int)
                inside = (q[:, 0] >= 0) & (q[:, 0] < w) & (q[:, 1] >= 0) & (q[:, 1] < h)
                prof = np.zeros(len(offs), bool)
                prof[inside] = sc.ink[q[inside, 1], q[inside, 0]]
                runs = _runs(np.nonzero(prof)[0])
                if len(runs) == 1 and runs[0].size <= MAX_RUN:
                    new[i] = p + offs[runs[0]].mean() * nv
                    ok[i] = True
                else:
                    reason = "none" if not runs else ("two strokes" if len(runs) > 1 else "merged")
            why.append(reason)
        if it < iters - 1:  # move only the accepted samples, then re-space
            pts = densify(new[ok], STEP) if ok.sum() > 3 else pts
            # keep excluded stretches on the original knots so they stay excluded
            pts = _rejoin(pts, np.array(KNOTS[curve], float))
    reasons = {}
    for r in why:
        if r is not None:
            reasons[r] = reasons.get(r, 0) + 1
    return Trace(new[ok], pts[~ok], reasons)


def _rejoin(pts: np.ndarray, knots: np.ndarray) -> np.ndarray:
    """Ensure the refined polyline still spans the knots' ends."""
    out = pts
    if np.hypot(*(pts[0] - knots[0])) > 2 * STEP:
        out = np.vstack([knots[:1], out])
    if np.hypot(*(pts[-1] - knots[-1])) > 2 * STEP:
        out = np.vstack([out, knots[-1:]])
    return densify(out, STEP)
