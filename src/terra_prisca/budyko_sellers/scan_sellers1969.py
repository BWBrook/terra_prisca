"""The printed results of Sellers (1969), read from the journal scan.

The scan is the AMS PDF (SHA-256 below), placed at
local/sources/budyko_sellers/sellers1969.pdf; it is not redistributed. Each
figure is calibrated from its own ruled frame and tick marks with an affine
map, which absorbs the small rotation and shear of the pasted-up original:
constant-latitude lines run parallel to the fitted left frame line, and
constant-value lines parallel to the fitted bottom axis. Tick pixels were
found by scanning just inside each axis; their values were read from the
printed labels.

Sellers marks his computed values with small circles on top of the observed
curves (Figs 2-4). These are found by an annulus detector (`find_rings`)
inside each panel and assigned to the nearest belt or circle latitude. The
detector sees only the scan, never model output.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .digitise import AffineFrame, find_rings, fit_line, page_ink, refine_component, refine_ring, track

SCAN_SHA256 = "a75e656dc9ee1268c696a610f68d157a2c4c48b525a57b9ecb5c1e5e24beec08"
DEFAULT_PDF = Path("local/sources/budyko_sellers/sellers1969.pdf")

BELTS = np.arange(85.0, -86.0, -10.0)
CIRCLES = np.arange(80.0, -81.0, -10.0)

# Per figure: page; left frame line and bottom axis line as (across, along)
# search ranges for fit_line; bottom tick pixels (x), for 80N..80S unless
# given as (pixel, value) pairs; plot box
# (x0, x1, y0, y1); panels with left-axis ticks (y pixel, value), the y range
# searched for circles, and whether the points sit at belts or circles.
FIGS = {
    "fig2": dict(
        page=4, left=((352, 368), (1535, 2570)), bottom=((2570, 2586), (365, 1125)),
        xticks=[400.0, 443.0, 485.5, 528.0, 570.0, 614.0, 655.5, 699.0, 741.0, 783.0, 827.0, 869.0,
                913.0, 955.0, 999.0, 1040.5, 1084.0],
        box=(366, 1124, 1533, 2566),
        panels={
            "dC": dict(ticks=[(1570.5, 60), (1611, 40), (1653, 20), (1694.5, 0), (1736.5, -20), (1778, -40),
                              (1820, -60), (1863.5, -80), (1903, -100)], yr=(1533, 1925), at="belt"),
            "Ldc": dict(ticks=[(1945.5, 20), (1987, 0), (2029.5, -20), (2071.5, -40)], yr=(1925, 2095), at="belt"),
            "dF": dict(ticks=[(2114.5, 20), (2157, 0), (2198, -20)], yr=(2095, 2218), at="belt"),
            "Rs": dict(ticks=[(2239.5, 40), (2282.5, 20), (2322.5, 0), (2364.5, -20), (2407, -40), (2448.5, -60),
                              (2489.5, -80), (2531.5, -100)], yr=(2218, 2566), at="belt"),
        }),
    "fig3": dict(
        page=4, left=((1362, 1378), (340, 1350)), bottom=((1350, 1362), (1375, 2110)),
        xticks=[1412.0, 1453.0, 1495.0, 1537.0, 1578.0, 1619.5, 1661.0, 1702.5, 1744.0, 1786.5, 1827.5,
                1868.5, 1911.0, 1949.5, 1994.0, 2034.0, 2076.5],
        box=(1374, 2112, 338, 1352),
        panels={
            "C": dict(ticks=[(375.5, 300), (415.5, 200), (456, 100), (497.5, 0), (538.5, -100), (579, -200),
                             (619.5, -300), (660, -400)], yr=(338, 720), at="circle"),
            "Lc": dict(ticks=[(700, 100), (740.5, 0), (782, -100)], yr=(720, 843), at="circle"),
            "F": dict(ticks=[(824, 100), (863, 0), (904.5, -100)], yr=(843, 925), at="circle"),
            "P": dict(ticks=[(945.5, 400), (986, 300), (1028.5, 200), (1068.5, 100), (1110, 0), (1151, -100),
                             (1192.5, -200), (1233.5, -300), (1275.5, -400), (1315.5, -500)],
                      yr=(925, 1352), at="circle"),
        }),
    "fig4": dict(
        page=5, left=((400, 422), (345, 1125)), bottom=((1122, 1140), (425, 1130)),
        xticks=[446.5, 487.0, 527.5, 568.5, 608.5, 649.0, 689.0, 730.0, 770.5, 811.5, 851.5, 892.5, 931.5,
                973.0, 1012.5, 1053.5, 1094.0],
        box=(414, 1134, 342, 1124),
        panels={
            "T": dict(ticks=[(375, 20), (415.5, 10), (455, 0), (495, -10), (534, -20), (573.5, -30)],
                      yr=(342, 598), at="belt"),
            "v": dict(ticks=[(614, 10), (653, 5), (693, 0), (732.5, -5), (772, -10)], yr=(598, 792), at="circle"),
            "albedo": dict(ticks=[(812, 0.9), (851, 0.8), (890.5, 0.7), (930.5, 0.6), (970, 0.5), (1009.5, 0.4),
                                  (1049, 0.3), (1089, 0.2)], yr=(792, 1124), at="belt"),
        }),
    "fig5": dict(
        page=5, left=((1340, 1356), (1690, 2725)), bottom=((2724, 2740), (1356, 2125)),
        xticks=[1392.5, 1435.5, 1479.5, 1523.0, 1566.5, 1609.5, 1653.5, 1696.0, 1740.0, 1783.5, 1827.0,
                1870.5, 1913.5, 1957.0, 2000.5, 2044.0, 2087.5],
        box=(1352, 2128, 1960, 2728),
        panels={"dT": dict(ticks=[(1970, 18), (2054, 16), (2138.5, 14), (2224.5, 12), (2310.5, 10), (2394.5, 8),
                                  (2478.5, 6), (2606.5, 3), (2647.5, 2), (2690.5, 1)], yr=(1960, 2728), at="belt")}),
    "fig6": dict(
        page=6, left=((356, 372), (1860, 2700)), bottom=((2700, 2716), (372, 1045)),
        xticks=[(364.8, 1.80), (468.5, 1.86), (639.0, 1.96), (672.0, 1.98), (810.0, 2.06), (845.0, 2.08),
                (1051.0, 2.20)],
        box=(370, 1047, 1860, 2545),
        panels={"Tbar": dict(ticks=[(1900.5, 40), (1990.5, 20), (2079, 0), (2171.5, -20), (2260.5, -40),
                                    (2349.5, -60), (2439, -80), (2528.5, -100)], yr=(1860, 2545), at="S")}),
    "fig7": dict(
        page=6, left=((1350, 1368), (345, 1390)), bottom=((1388, 1404), (1368, 2128)),
        xticks=[1401.5, 1445.5, 1488.0, 1530.5, 1572.5, 1617.0, 1660.0, 1703.5, 1745.5, 1789.0, 1832.0,
                1875.0, 1916.0, 1961.0, 2003.0, 2046.0, 2089.0],
        box=(1364, 2128, 342, 1390),
        panels={"T": dict(ticks=[(422, 40), (505, 30), (589, 20), (758, 0), (842, -10), (926, -20), (1010, -30),
                                 (1095, -40), (1180, -50), (1263.5, -60), (1348, -70)], yr=(342, 1390), at="belt")}),
}

# Printed curves without point markers, traced from hand-read seed pixels
# (the labels at the curve ends identify them). Several seeds trace a curve
# from both ends; "strict" stops a trace where curves converge; "rows" traces
# a steep curve row by row; "keep" limits a trace to pixel-x ranges where the
# curve is clear of its neighbours (Fig. 5's curves 2-5 merge near 30N-30S).
TRACES = {
    # Fig. 4's solid line is the observed profile; the circles on it are computed.
    ("fig4", "T observed"): dict(seeds=[(600, 420)], box=(414, 1134, 342, 598)),
    ("fig5", "1"): dict(seeds=[(1720, 2700)]),
    ("fig5", "2"): dict(seeds=[(1370, 2415), (2070, 2600)], strict=True, keep=[(1352, 1560), (1830, 2128)]),
    ("fig5", "3"): dict(seeds=[(1380, 2565)], strict=True, keep=[(1352, 1600)]),
    ("fig5", "4"): dict(seeds=[(1380, 2530)], strict=True, keep=[(1352, 1600)]),
    ("fig5", "3 south"): dict(seeds=[(2112, 2205)], strict=True, rows=True),
    ("fig5", "4 south"): dict(seeds=[(2112, 2097)], strict=True, rows=True),
    ("fig6", "fixed"): dict(seeds=[(450, 2062)]),
    ("fig6", "0.009 drop"): dict(seeds=[(633, 2300)], rows=True),
    ("fig7", "d"): dict(seeds=[(1725, 420)]), ("fig7", "c"): dict(seeds=[(1725, 465)]),
    ("fig7", "b"): dict(seeds=[(1725, 517)]), ("fig7", "f"): dict(seeds=[(1725, 620)]),
    ("fig7", "i"): dict(seeds=[(1725, 670)]),
    # g crosses the circled curve a near x = 1630 and 1810 and runs flat below it
    # (y ~ 551) between them. Traced from the left end it switches onto a at the
    # first crossing, so it is traced from its own crest and stopped at x = 2000,
    # before it converges with c and d.
    ("fig7", "g"): dict(segments=[((1725, 551), (1364, 2000))]),
    ("fig7", "e"): dict(seeds=[(1365, 975)]),
}

# Dashed curves read as their isolated dashes: connected components of the
# given size and elongation (ratio of principal axes), clear of the frame
# ticks and of the horizontal reference lines. Fig. 7's h is its only dashed
# curve; dashes that touch a solid curve near the crest are lost, not guessed.
DASHES = {
    ("fig7", "h"): dict(size=(30, 150), elongation=3.0, margin=20, drop_rows=[(662, 682), (838, 858)], drop_boxes=[(2050, 2128, 640, 1240)]),
}
# Reference lines and lettering kept out of the traces, as (x0, x1, y0, y1).
TRACE_EXCLUDE = {"fig4": [(414, 1134, 444, 467)], "fig5": [(1440, 2000, 1680, 1960)], "fig6": [], "fig7": []}

# Fig. 6 marks its computed points with circles (two albedo laws), a square
# (a and K's doubled) and a triangle (halved). Positions are read by eye and
# then refined on the scan: circles to the annulus-score maximum, squares
# and triangles to the centre of their ink.
FIG6_MARKS = {
    "0.009": [(1050, 1940), (880, 1971), (743, 2007), (707, 2018), (673, 2034), (637, 2075), (606, 2525),
              (536, 2529)],
    "0.005": [(673, 2034), (707, 2018), (605, 2048), (535, 2070), (501, 2086), (467, 2219), (398, 2287),
              (364, 2309)],
    "K x2": [(708, 1998), (605, 2064)],
    "K x0.5": [(707, 2094)],
}

# Detections rejected on inspection of the scan, (figure, x, y) within 6 px:
# lettering ("Lc", "P", "-60", "dC", "dF", "R") and a second response to one ring.
NOT_POINTS = [
    ("fig3", 1615, 679), ("fig3", 1696, 993),
    ("fig2", 466, 1816), ("fig2", 456, 1991), ("fig2", 684, 1749), ("fig2", 769, 1562),
    ("fig2", 774, 2105), ("fig2", 889, 2275),
]


@dataclass
class Scan:
    pages: dict[int, np.ndarray]
    frames: dict[tuple[str, str], AffineFrame]
    points: dict[tuple[str, str], np.ndarray]  # (abscissa, value) of each circled point
    traces: dict[tuple[str, str], tuple[np.ndarray, np.ndarray]]  # traced curve: pixels, data


def frame_for(ink, spec, panel) -> AffineFrame:
    kl, cl = fit_line(ink, True, *spec["left"])
    kb, cb = fit_line(ink, False, *spec["bottom"])
    xpts = []
    xt = spec["xticks"]
    pairs = xt if np.ndim(xt) == 2 else list(zip(xt, CIRCLES))
    for px, lat in pairs:
        py = kb * px + cb
        xpts += [(px, py, lat), (px - 500 * kl, py - 500, lat)]
    ypts = []
    for py, val in panel["ticks"]:
        px = kl * py + cl
        ypts += [(px, py, val), (px + 500, py + 500 * kb, val)]
    return AffineFrame.fit(xpts, ypts, spec["box"])


def read_points(ink, spec, frames, fig) -> dict[str, np.ndarray]:
    """Circled points of every panel of a figure. Panels are stacked, so at each
    latitude the rings run top to bottom in panel order; when a latitude has one
    ring per panel they are assigned in that order, otherwise each ring goes to
    the panel whose y range holds it."""
    x0, x1, y0, y1 = spec["box"]
    rings = find_rings(ink, (x0, x1, y0, y1))
    rings = np.array([r for r in rings
                      if not any(f == fig and np.hypot(r[0] - x, r[1] - y) < 6 for f, x, y in NOT_POINTS)])
    names = list(spec["panels"])
    any_frame = frames[names[0]]
    lat_of = any_frame.to_data(rings)[:, 0]
    out = {n: [] for n in names}
    for at, targets in (("belt", BELTS), ("circle", CIRCLES)):
        group = [n for n in names if spec["panels"][n]["at"] == at]
        if not group:
            continue
        for lat in targets:
            near = rings[np.abs(lat_of - lat) < 2.5]
            near = near[np.argsort(near[:, 1])]
            if len(near) == len(group):
                pairs = zip(group, near)
            else:
                pairs = [(n, r) for r in near for n in group
                         if spec["panels"][n]["yr"][0] <= r[1] < spec["panels"][n]["yr"][1]]
            for n, r in pairs:
                out[n].append((lat, frames[n].to_data(r)[0, 1]))
    return {n: np.array(v).reshape(-1, 2) for n, v in out.items()}


def rings_in(ink, spec, frame):
    """Data coordinates of every circled point in a figure's plot box."""
    return frame.to_data(find_rings(ink, spec["box"])).reshape(-1, 2)


def by_order(data, targets, names, tol):
    """At each target abscissa, rings sorted top to bottom are given to `names` in order."""
    out = {n: [] for n in names}
    for x in targets:
        near = data[np.abs(data[:, 0] - x) < tol]
        near = near[np.argsort(-near[:, 1])]
        for n, r in zip(names, near):
            out[n].append((x, r[1]))
    return {n: np.array(v).reshape(-1, 2) for n, v in out.items()}


def special_points(ink, fig, spec, frame):
    data = rings_in(ink, spec, frame)
    if fig == "fig5":  # curves 6 and 5 carry the circles; 6 is always the upper
        both = by_order(data, BELTS, ["6", "5"], 2.5)
        return {n: v for n, v in both.items()}
    if fig == "fig7":  # the circles mark curve a, the present state; take the strongest ring per belt
        pts, sc = find_rings(ink, spec["box"], scores=True)
        d = frame.to_data(pts)
        out = []
        for lat in BELTS:
            near = np.nonzero(np.abs(d[:, 0] - lat) < 2.5)[0]
            if near.size:
                out.append(d[near[np.argmax(sc[near])]])
        return {"a": np.array(out).reshape(-1, 2)}
    if fig == "fig6":
        out = {}
        for name, marks in FIG6_MARKS.items():
            ref = refine_ring if name in ("0.009", "0.005") else refine_component
            out[name] = frame.to_data(np.array([ref(ink, m) for m in marks]))
        return out
    raise KeyError(fig)


def load(pdf: Path = DEFAULT_PDF) -> Scan:
    digest = hashlib.sha256(Path(pdf).read_bytes()).hexdigest()
    if digest != SCAN_SHA256:
        raise ValueError(f"{pdf} has SHA-256 {digest}; the calibration is for {SCAN_SHA256}")
    pages = {p: page_ink(pdf, p) for p in sorted({f["page"] for f in FIGS.values()})}
    frames, points = {}, {}
    for fig, spec in FIGS.items():
        ink = pages[spec["page"]]
        fr = {name: frame_for(ink, spec, panel) for name, panel in spec["panels"].items()}
        for name in fr:
            frames[(fig, name)] = fr[name]
        if fig in ("fig5", "fig6", "fig7"):
            for name, pts in special_points(ink, fig, spec, fr[next(iter(fr))]).items():
                points[(fig, name)] = pts
        else:
            for name, pts in read_points(ink, spec, fr, fig).items():
                points[(fig, name)] = pts
    traces = {}
    for (fig, name), t in TRACES.items():
        spec = FIGS[fig]
        ink = pages[spec["page"]]
        pieces = []
        segments = t.get("segments") or [(sd, None) for sd in t["seeds"]]
        for seed, span in segments:
            seed = snap(ink, seed)
            if t.get("rows"):
                x0, x1, y0, y1 = spec["box"]
                ex = [(e[2], e[3], e[0], e[1]) for e in TRACE_EXCLUDE[fig]]
                px = track(ink.T, (y0, y1, x0, x1), (seed[1], seed[0]), exclude=ex, strict=t.get("strict", False))[:, ::-1]
            else:
                px = track(ink, t.get("box", spec["box"]), seed, exclude=TRACE_EXCLUDE[fig], strict=t.get("strict", False))
            if span is not None:
                px = px[(px[:, 0] >= span[0]) & (px[:, 0] <= span[1])]
            pieces.append(px)
        px = np.unique(np.vstack(pieces), axis=0)
        if "keep" in t:
            px = px[np.any([(px[:, 0] >= a) & (px[:, 0] <= b) for a, b in t["keep"]], axis=0)]
        traces[(fig, name)] = (px, frames[(fig, next(iter(spec["panels"])))].to_data(px))
    for (fig, name), d in DASHES.items():
        spec = FIGS[fig]
        px = dash_pixels(pages[spec["page"]], spec["box"], **d)
        traces[(fig, name)] = (px, frames[(fig, next(iter(spec["panels"])))].to_data(px))
    return Scan(pages, frames, points, traces)


def dash_pixels(ink, box, size, elongation, margin, drop_rows, drop_boxes=()):
    """Pixels of the isolated, elongated dash components inside box."""
    from scipy import ndimage

    x0, x1, y0, y1 = box
    sub = np.zeros_like(ink)
    sub[y0:y1, x0:x1] = ink[y0:y1, x0:x1]
    lab, _ = ndimage.label(sub, structure=np.ones((3, 3)))
    keep = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        ys, xs = np.nonzero(lab[sl] == i + 1)
        if not size[0] <= ys.size <= size[1]:
            continue
        xs, ys = xs + sl[1].start, ys + sl[0].start
        ev = np.sort(np.linalg.eigvalsh(np.cov(np.vstack([xs, ys]))))
        cx, cy = xs.mean(), ys.mean()
        inside = x0 + margin <= cx <= x1 - margin and y0 + margin <= cy <= y1 - margin
        on_line = any(a <= cy <= b for a, b in drop_rows) or any(a <= cx <= b and c <= cy <= d for a, b, c, d in drop_boxes)
        if inside and not on_line and np.sqrt(ev[1] / max(ev[0], 1e-9)) >= elongation:
            keep.append(np.column_stack([xs, ys]))
    return np.vstack(keep).astype(float)


def snap(ink, seed, radius=12):
    """Nearest ink pixel to a hand-read seed."""
    x, y = seed
    ys, xs = np.nonzero(ink[y - radius:y + radius + 1, x - radius:x + radius + 1])
    i = np.argmin(np.hypot(xs - radius, ys - radius))
    return x + xs[i] - radius, y + ys[i] - radius
