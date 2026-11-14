"""The printed curves of Budyko (1969), traced from the journal scan.

The scan is the PDF published by Tellus A (tellusjournal.org, CC BY 4.0),
SHA-256 below; place it at local/sources/budyko_sellers/budyko1969.pdf. Each
figure is calibrated from its own tick marks. Every printed curve is traced
separately: solid curves as the strokes containing hand-placed seed pixels,
dashed curves as the dashes inside a box. Seeds, boxes and ticks were read
from the scan alone.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .digitise import Axis, Frame, components, page_ink, select_strokes

SCAN_SHA256 = "4690e5238be7a2ea00ebd32703bcd3e25822f90e5647df58dd3829300706b120"
DEFAULT_PDF = Path("local/sources/budyko_sellers/budyko1969.pdf")

# PDF page, tick marks (pixel, value) for x and y, plot box, axis-line pixels.
FRAMES = {
    "fig2": (4, [(735, -30), (908.5, -20), (1083.5, -10), (1258.5, 0), (1433.5, 10)],
             [(318, 4), (436, 2), (555, 0), (671, -2), (788.5, -4), (906, -6), (1022.5, -8)],
             (566, 1530, 250, 1040), (560.5, 554.5)),
    "fig3": (5, [(1237.5, 0), (1355, 20), (1472, 40), (1588, 60), (1704.5, 80)],
             [(309.5, 30), (427, 20), (545.5, 10), (662.5, 0), (778, -10), (894.5, -20)],
             (1243, 1730, 300, 930), (1237.5, 661.5)),
    "fig4": (6, [(389.5, 0), (497, 20), (604, 40), (820, 80)],
             [(293.5, 30), (401.5, 20), (509.5, 10), (621, 0), (730.5, -10), (839.5, -20)],
             (394, 880, 290, 910), (389.5, 620.5)),
    "fig5": (6, [(1190, 0.0), (1458, -0.01), (1729.5, -0.02)],
             [(2012.5, 20), (2119.5, 10), (2171.5, 5), (2225.5, 0), (2279.5, -5), (2333.5, -10), (2442, -20)],
             (1193, 1790, 1960, 2500), (1190, 2226)),
    "fig6": (7, [(1241, 0), (1356, 20), (1472, 40), (1588, 60), (1705, 80)],
             [(477, 20), (593, 10), (709.5, 0), (828, -10), (945.5, -20)],
             (1246, 1750, 360, 980), (1241, 707.5)),
}

# Solid curves: seed pixels on each stroke. Dashed curves: box, dash size, lettering to drop.
CURVES = {
    ("fig3", "T observed"): dict(seeds=[(1595, 656), (1702, 826)], clip=[(1390, 1407, 441, 457)]),
    ("fig3", "T0"): dict(box=(1280, 1700, 340, 760), size=(60, 135),
                         drop=[(1440, 1462, 375, 396), (1240, 1730, 663, 692)]),
    ("fig4", "T0"): dict(seeds=[(400, 340), (846, 790)], clip=[(715, 732, 624, 640)]),
    ("fig4", "T1.0"): dict(seeds=[(400, 376), (846, 826)]),
    ("fig4", "T1.5"): dict(seeds=[(400, 416), (846, 862)]),
    ("fig5", "Tp"): dict(seeds=[(1200, 2066)]),
    ("fig5", "phi0"): dict(box=(1193, 1615, 1985, 2222), size=(40, 135),
                           drop=[(1424, 1441, 2050, 2071), (1440, 1480, 2185, 2222)]),
    ("fig5", "vertical"): dict(seeds=[(1627, 2400)]),
    ("fig6", "Tq"): dict(seeds=[(1250, 389), (1735, 738)], clip=[(1695, 1725, 711, 740)]),
    ("fig6", "T0"): dict(seeds=[(1250, 408), (1736, 885)]),
}


@dataclass
class Scan:
    pages: dict[int, np.ndarray]
    frames: dict[str, Frame]
    curves: dict[tuple[str, str], np.ndarray]  # traced ink, pixels (x, y)


def load(pdf: Path = DEFAULT_PDF) -> Scan:
    digest = hashlib.sha256(Path(pdf).read_bytes()).hexdigest()
    if digest != SCAN_SHA256:
        raise ValueError(f"{pdf} has SHA-256 {digest}; the calibration is for {SCAN_SHA256}")
    pages = {p: page_ink(pdf, p) for p in sorted({f[0] for f in FRAMES.values()})}
    frames = {name: Frame(Axis.from_ticks(xt), Axis.from_ticks(yt), box, axis)
              for name, (_, xt, yt, box, axis) in FRAMES.items()}
    curves = {}
    for (fig, name), spec in CURVES.items():
        spec = dict(spec)
        clip = spec.pop("clip", [])
        labels, n = components(pages[FRAMES[fig][0]], frames[fig])
        pix = select_strokes(labels, n, **spec)
        for x0, x1, y0, y1 in clip:
            pix = pix[~((pix[:, 0] >= x0) & (pix[:, 0] < x1) & (pix[:, 1] >= y0) & (pix[:, 1] < y1))]
        curves[(fig, name)] = pix
    return Scan(pages, frames, curves)


def fig2_points(scan: Scan, core_px: float = 4.0, merge_px: float = 12.0) -> np.ndarray:
    """Centres of the printed data points of Fig. 2 (filled dots thicker than the line)."""
    from scipy import ndimage

    fr = scan.frames["fig2"]
    ink = scan.pages[FRAMES["fig2"][0]]
    x0, x1, y0, y1 = fr.box
    sub = np.zeros_like(ink)
    sub[y0:y1, x0:x1] = ink[y0:y1, x0:x1]
    core = ndimage.distance_transform_edt(sub) >= core_px
    lab, n = ndimage.label(core)
    centres = np.array(ndimage.center_of_mass(core, lab, range(1, n + 1)))[:, ::-1]
    # A dot crossed by the printed line can split into several cores: merge those within merge_px.
    merged, used = [], np.zeros(len(centres), bool)
    for i, c in enumerate(centres):
        if not used[i]:
            near = (np.hypot(*(centres - c).T) <= merge_px) & ~used
            used |= near
            merged.append(centres[near].mean(axis=0))
    return fr.to_data(np.array(merged))
