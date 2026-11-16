"""Fig. 2 of Lovelock & Whitfield (1982), read from the journal scan.

The scan is the Nature publisher PDF (3 pages; each page a 220-ppi colour JPEG,
SHA-256 below); place it at local/sources/biosphere_lifespan/lovelock_whitfield1982.pdf.
It is copyrighted and is not redistributed. Every tick and seed below was read
from the scan alone, never from model output.

The frame lines are exactly vertical and horizontal (each spans 484 rows in a
single pixel column), so each scale is a separate linear map fitted to its ticks:

  - time: seven ticks on the bottom frame, -4,000 to 2,000 Myr;
  - luminosity: the right-hand labels of the middle axis, 0.7 to 1.2;
  - sqrt(CO2): the left-hand labels of the same ticks, 0 to 300 sqrt(ppm),
    with unlabelled ticks at the odd fifties;
  - mean temperature (left frame, 0-100 C): the top and bottom frame lines;
    the axis has labels but no ticks.

Lines are traced by following ink within +-4 px of a straight guess between
two seeds and refitting (+-2 px for the CO2 stroke beyond t = 0 and the limit line). A column is used only when that window holds a single
run of ink at most 4 px tall; columns where a second stroke enters the window
(crossings, labels, the CO2 limit beside the CO2 line) are dropped and counted.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from terra_prisca.budyko_sellers.digitise import Axis, page_ink

SCAN_SHA256 = "d763245eb2867e041766f6a6ab2d04013b30749eeb938d794b6c8c07477eeab3"
DEFAULT_PDF = Path("local/sources/biosphere_lifespan/lovelock_whitfield1982.pdf")
PAGE = 2

TIME_TICKS = [(144.5, -4000), (260.0, -3000), (375.0, -2000), (490.0, -1000),
              (606.0, 0), (722.0, 1000), (838.0, 2000)]
LUM_TICKS = [(210.0, 1.2), (259.0, 1.1), (307.0, 1.0), (355.0, 0.9), (403.0, 0.8), (451.0, 0.7)]
SQRTC_TICKS = [(210.0, 300), (259.0, 250), (307.0, 200), (355.0, 150), (403.0, 100),
               (451.0, 50), (499.0, 0)]
TEMP_TICKS = [(161.0, 100), (643.5, 0)]
TEMP_LABEL_ROWS = [(165.0, 100), (259.5, 80), (351.5, 60), (449.0, 40), (546.0, 20), (642.0, 0)]
MIDDLE_AXIS_X = 606.0

# (first seed, last seed) in pixels for each straight line.
SEEDS = {
    "sun": ((146, 447), (837, 238)),
    "co2": ((206, 240), (604, 480)),
    "co2_tail": ((608, 482), (636, 498)),
    "limit": ((612, 488), (740, 488)),
}
HALF = 4
# Beyond t = 0 the CO2 stroke runs within 1-9 px of the horizontal limit line;
# a +-2 px window keeps the two apart, and columns where they merge are dropped.
HALF_BY_LINE = {"co2_tail": 2, "limit": 2}
# Columns where the CO2 stroke and the limit line share ink (rows 486-490),
# read from the native scan; neither line is measured there.
OVERLAP = {"co2_tail": (615, 625), "limit": (615, 625)}
MAX_RUN = 4  # the strokes are 1-3 px thick; a taller run is two strokes merged

# Temperature band: horizontal segments (row, x0, x1) as printed, and the x
# windows holding each glaciation minimum.
BAND_LEVELS = {
    "Archaean upper": (451, 202, 329),
    "Archaean lower": (571, 202, 324),
    "post-2.2 Gyr upper": (523, 363, 490),
    "post-2.2 Gyr lower": (571, 359, 486),
}
# The last excursion, which runs down the middle axis at t = 0, cannot be
# separated from the axis and is not read.
GLACIATION_WINDOWS = [(326, 360), (490, 503), (505, 524), (525, 545), (547, 566), (567, 580)]
GLACIATION_ROWS = (540, 635)  # stops above the bottom-frame ticks (rows 636-641)


def check(pdf: Path) -> None:
    digest = hashlib.sha256(Path(pdf).read_bytes()).hexdigest()
    if digest != SCAN_SHA256:
        raise ValueError(f"{pdf} has SHA-256 {digest}; the calibration is for {SCAN_SHA256}")


@dataclass(frozen=True)
class Scan:
    ink: np.ndarray
    time: Axis
    lum: Axis
    sqrtc: Axis
    temp: Axis


def load(pdf: Path = DEFAULT_PDF) -> Scan:
    check(pdf)
    return Scan(page_ink(pdf, PAGE), Axis.from_ticks(TIME_TICKS), Axis.from_ticks(LUM_TICKS),
                Axis.from_ticks(SQRTC_TICKS), Axis.from_ticks(TEMP_TICKS))


@dataclass(frozen=True)
class Trace:
    centres: np.ndarray   # (x, y) per accepted column
    pixels: np.ndarray    # every ink pixel (x, y) of the accepted columns
    dropped: np.ndarray   # columns in the seeded span left out (crossings, labels, gaps)


def trace_full(sc: Scan, key: str, half: int | None = None) -> Trace:
    """Follow a straight printed line. In each column the window +-half px about
    the current line must hold exactly one run of ink, at most MAX_RUN px tall;
    a second stroke in the window (a crossing or a nearby line) or a merged run
    makes the column ambiguous, and it is dropped and counted."""
    half = HALF_BY_LINE.get(key, HALF) if half is None else half
    (x0, y0), (x1, y1) = SEEDS[key]
    xs = np.arange(int(x0), int(x1) + 1)
    k, c = (y1 - y0) / (x1 - x0), y0 - (y1 - y0) / (x1 - x0) * x0
    for _ in range(5):
        pts, pix, drop = [], [], []
        for x in xs:
            o = OVERLAP.get(key)
            if o and o[0] <= x <= o[1]:
                drop.append(x)
                continue
            lo = int(round(k * x + c - half))
            idx = np.nonzero(sc.ink[lo:lo + 2 * half + 1, x])[0]
            runs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1) if idx.size else []
            if len(runs) == 1 and runs[0].size <= MAX_RUN:
                pts.append((x, lo + idx.mean()))
                pix += [(x, lo + i) for i in idx]
            else:
                drop.append(x)
        pts = np.array(pts)
        k, c = np.polyfit(pts[:, 0], pts[:, 1], 1)
    return Trace(pts, np.array(pix, float), np.array(drop, int))


def trace(sc: Scan, key: str, half: int | None = None) -> np.ndarray:
    """Pixel centres (x, y) of a straight printed line, one per usable column."""
    return trace_full(sc, key, half).centres


def band_levels(sc: Scan) -> dict[str, tuple[float, float, float]]:
    """Each horizontal band segment as (temperature C, t_start, t_end)."""
    out = {}
    for name, (row, x0, x1) in BAND_LEVELS.items():
        rows = [r for r in range(row - 2, row + 3) if sc.ink[r, x0:x1 + 1].mean() > 0.6]
        out[name] = (float(sc.temp.value(np.mean(rows))), float(sc.time.value(x0)), float(sc.time.value(x1)))
    return out


def glaciation_minima(sc: Scan) -> list[tuple[float, float]]:
    """Lowest ink of each V-shaped glaciation, as (t Myr, temperature C)."""
    out = []
    for x0, x1 in GLACIATION_WINDOWS:
        r0, r1 = GLACIATION_ROWS
        ys, xs = np.nonzero(sc.ink[r0:r1, x0:x1 + 1])
        j = ys.max()
        x = xs[ys == j].mean() + x0
        out.append((float(sc.time.value(x)), float(sc.temp.value(j + r0))))
    return out
