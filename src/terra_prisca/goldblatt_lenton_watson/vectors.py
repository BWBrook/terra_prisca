"""Read the printed curves of Figs 2 and 3 straight from the article's vector paths.

    uv run --with pymupdf python -m terra_prisca.goldblatt_lenton_watson.vectors [pdf] [si_pdf] [out.csv]

The Nature PDF (SHA-256 below) draws every curve as a stroked polyline, so the
published geometry can be read exactly rather than traced from a raster. Place
it at local/sources/goldblatt_lenton_watson/nature05169.pdf; it is copyrighted
and is not redistributed. The output CSV holds the curve vertices in data units
and is what the fidelity scoring and the tests read; PyMuPDF is needed only to
regenerate it.

Calibration. Each panel's frame is the grey quad drawn around it, and both
axes of every panel are fitted to its major ticks on the left and bottom frame
edges. The fitted frame limits and sizes go to glw2006_frames.csv, which the
scoring reads. In Fig. 3's zoom panels the time axis runs from 2.4001 to
2.399 Gyr ago: the "2.4" tick sits inside the frame. The right-hand ordinate of
Figs 3a and 3c (pO2 and pCH4 in atm) has its own ticks, drawn about 2 pt below
the left-hand (PAL) ticks; it is fitted separately and stored as a mapping onto
the left-hand axis.

The Supplementary Information PDF (SI_SHA256) is read the same way: the marker
centres of Supplementary Fig. 2 and the fitted line of Supplementary Fig. 3,
both as log10 values, go to glw2006_si_vectors.csv.

Paths drawn twice at identical coordinates, in either direction, are counted once.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

PDF_SHA256 = "37a2345b997afe01dad259c4f2525f18edbbdc3703ad545211cd859ebfb58112"
SI_SHA256 = "d2236ec0ec767fbcf61031cc4faf3655f1f8f050633e3d18205c1263109d5046"
DEFAULT_PDF = Path("local/sources/goldblatt_lenton_watson/nature05169.pdf")
SI_PDF = Path("local/sources/goldblatt_lenton_watson/nature05169-s1.pdf")
OUT = Path("models/goldblatt_lenton_watson/fidelity/glw2006_vectors.csv")
FRAMES = OUT.with_name("glw2006_frames.csv")
SI_OUT = OUT.with_name("glw2006_si_vectors.csv")

SOLID, DASHED_2, DOTTED, DASHED_3, DASHDOT = "[] 0", "[ 6 6 ] 0", "[ .5 4 ] 0", "[ 6 2 ] 0", "[ 3 1 1 1 ] 0"

# Axis limits (x0, x1, y0, y1) in data units, read from the tick labels.
# Fig. 2: log10 of r or N (mol O2 equiv./yr) and log10 O2 (PAL).
# Fig. 3: time (Gyr ago, decreasing to the right) and log10 O2 (PAL) or flux (1e11 mol/yr).
FIG2 = {"a": (8.0, 16.0, 0.0, -11.0), "b": (10.0, 18.0, 0.0, -11.0)}
FIG3 = {"a": (2.5, 2.0, 0.0, -6.0), "a_zoom": (2.4001, 2.399, 0.0, -6.0),
        "b": (2.5, 2.0, 8.0, -4.0), "b_zoom": (2.4001, 2.399, 8.0, -4.0),
        "c": (2.5, 2.0, 0.0, -6.0), "c_zoom": (2.4001, 2.399, 0.0, -6.0),
        "d": (2.5, 2.0, 8.0, -4.0), "d_zoom": (2.4001, 2.399, 8.0, -4.0)}
# Fig. 3 major ticks, as (first value, step) from the left or top: the main time
# axes tick every 0.1 Gyr from 2.5; the zoom time axes tick only at 2.4 and 2.399,
# with the frame extending 0.1 kyr before 2.4; y ticks every decade (a, c) or
# every 2e11 mol/yr (b, d).
FIG3_TICKS = {"x": {"main": (2.5, -0.1), "zoom": (2.4, -0.001)},
              "y": {"ac": (0.0, -1.0), "bd": (8.0, -2.0)}}
TICK_LEN = {"main": (1.0, 1.6), "zoom": (0.4, 0.6)}
RIGHT_AXIS = (-1.0, -1.0)   # Figs 3a, 3c right ordinate: top major tick 10^-1 atm, one per decade
RIGHT_EDGE_TOL = 0.15       # pt; the 3c zoom right ticks start 0.09 pt outside the frame


@dataclass(frozen=True)
class Frame:
    x0: float
    x1: float
    y0: float
    y1: float
    lim: tuple[float, float, float, float]

    def data(self, px, py):
        a, b, c, d = self.lim
        return (a + (np.asarray(px) - self.x0) * (b - a) / (self.x1 - self.x0),
                c + (np.asarray(py) - self.y0) * (d - c) / (self.y1 - self.y0))

    def holds(self, rect, pad=1.5):
        return (rect.x0 >= self.x0 - pad and rect.x1 <= self.x1 + pad
                and rect.y0 >= self.y0 - pad and rect.y1 <= self.y1 + pad)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vertices(path) -> np.ndarray:
    pts = []
    for it in path["items"]:
        if it[0] != "l":
            raise ValueError("curve path holds a non-line segment")
        p, q = it[1], it[2]
        if not pts or (pts[-1][0], pts[-1][1]) != (p.x, p.y):
            pts.append((p.x, p.y))
        pts.append((q.x, q.y))
    return np.array(pts)


def _unique(paths):
    seen, out = set(), []
    for p in paths:
        if any(it[0] != "l" for it in p["items"]):
            continue
        v = _vertices(p)
        key = (p["dashes"], round(p["width"], 3), min(v.round(3).tobytes(), v[::-1].round(3).tobytes()))
        if key not in seen:
            seen.add(key)
            out.append((p, v))
    return out


def _frames(page, limits: dict) -> dict[str, Frame]:
    quads = sorted([d["rect"] for d in page.get_drawings()
                    if d["type"] == "s" and d["color"][0] > 0.5 and d["items"][0][0] == "qu"],
                   key=lambda r: (round(r.y0 / 20), r.x0))
    names = list(limits)
    if len(quads) != len(names):
        raise ValueError(f"expected {len(names)} frames, found {len(quads)}")
    return {n: Frame(q.x0, q.x1, q.y0, q.y1, limits[n]) for n, q in zip(names, quads)}


def _ticks(page, fr: Frame, axis: str, major_len=2.0, max_len=4.0):
    """Major tick positions (pt) on the left (axis='y') or bottom (axis='x') edge."""
    out = []
    for d in page.get_drawings():
        if d["type"] != "s" or d["color"][0] > 0.5 or abs(d["width"] - 0.5) > 0.01:
            continue
        for it in d["items"]:
            if it[0] != "l":
                continue
            p, q = it[1], it[2]
            if axis == "y" and abs(p.y - q.y) < 1e-3 and abs(min(p.x, q.x) - fr.x0) < 0.05 \
                    and major_len < abs(p.x - q.x) < max_len and fr.y0 - 0.5 <= p.y <= fr.y1 + 0.5:
                out.append(p.y)
            if axis == "x" and abs(p.x - q.x) < 1e-3 and abs(max(p.y, q.y) - fr.y1) < 0.05 \
                    and major_len < abs(p.y - q.y) < max_len and fr.x0 - 0.5 <= p.x <= fr.x1 + 0.5:
                out.append(p.x)
    return np.unique(np.round(out, 3))


def _right_ticks(page, fr: Frame) -> np.ndarray:
    """Major ticks (pt) on the right edge. Minor ticks share one short length;
    the majors are the most common length between 1.5 and 2.5 times it, which
    excludes the stray marks at the frame corners."""
    found = []
    for d in page.get_drawings():
        if d["type"] != "s" or d["color"][0] > 0.5:
            continue
        for it in d["items"]:
            if it[0] != "l":
                continue
            p, q = it[1], it[2]
            if abs(p.y - q.y) < 1e-3 and abs(max(p.x, q.x) - fr.x1) < RIGHT_EDGE_TOL \
                    and 0.1 < abs(p.x - q.x) < 2.0 and fr.y0 - 0.5 <= p.y <= fr.y1 + 0.5:
                found.append((round(p.y, 3), round(abs(p.x - q.x), 2)))
    found = sorted(set(found))
    lengths = np.array([n for _, n in found])
    minor = np.bincount(np.round(lengths * 100).astype(int)).argmax() / 100
    cand = lengths[(lengths > 1.5 * minor) & (lengths < 2.5 * minor)]
    major = np.bincount(np.round(cand * 100).astype(int)).argmax() / 100
    return np.array([y for y, n in found if abs(n - major) < 0.005])


def _frame_row(fig, panel, fr: Frame, right=(np.nan, np.nan)) -> dict:
    return {"figure": fig, "panel": panel, "x_left": fr.lim[0], "x_right": fr.lim[1],
            "y_top": fr.lim[2], "y_bottom": fr.lim[3], "width_pt": fr.x1 - fr.x0,
            "height_pt": fr.y1 - fr.y0, "right_at_left_zero": right[0], "right_per_left": right[1]}


def _tick_fit(pos, first, step):
    vals = first + step * np.arange(len(pos))
    k, c = np.polyfit(pos, vals, 1)
    return k, c, float(np.abs(k * pos + c - vals).max())


def _row(fig, panel, curve, part, v, fr: Frame):
    x, y = fr.data(v[:, 0], v[:, 1])
    return [{"figure": fig, "panel": panel, "curve": curve, "part": part, "vertex": i,
             "x": float(a), "y": float(b)} for i, (a, b) in enumerate(zip(x, y))]


def fig2(page) -> tuple[list[dict], list[dict], list[dict]]:
    frames = _frames(page, FIG2)
    rows, checks, frame_rows = [], [], []
    for name, fr in frames.items():
        ys, xs = _ticks(page, fr, "y"), _ticks(page, fr, "x")
        ky, cy, ry = _tick_fit(ys, fr.lim[2], -1.0)
        kx, cx, rx = _tick_fit(xs, fr.lim[0], 1.0)
        checks += [
            {"check": f"fig2{name} y ticks", "n": len(ys), "value": ry, "unit": "decades max residual"},
            {"check": f"fig2{name} x ticks", "n": len(xs), "value": rx, "unit": "decades max residual"},
            {"check": f"fig2{name} frame top", "n": 1, "value": ky * fr.y0 + cy - fr.lim[2], "unit": "decades"},
            {"check": f"fig2{name} frame bottom", "n": 1, "value": ky * fr.y1 + cy - fr.lim[3], "unit": "decades"},
            {"check": f"fig2{name} frame left", "n": 1, "value": kx * fr.x0 + cx - fr.lim[0], "unit": "decades"},
            {"check": f"fig2{name} frame right", "n": 1, "value": kx * fr.x1 + cx - fr.lim[1], "unit": "decades"},
        ]
        fr = Frame(fr.x0, fr.x1, fr.y0, fr.y1,
                   (kx * fr.x0 + cx, kx * fr.x1 + cx, ky * fr.y0 + cy, ky * fr.y1 + cy))
        frame_rows.append(_frame_row("2", name, fr))
        inside = [d for d in page.get_drawings() if d["type"] == "s" and fr.holds(d["rect"])]
        grey = [d for d in inside if d["color"][0] > 0.5 and abs(d["width"] - 1.0) < 1e-6]
        for g in _unique(grey):
            checks.append({"check": f"fig2{name} grey line", "n": 1,
                           "value": float(fr.data(g[1][:, 0], g[1][:, 1])[0].mean()), "unit": "log10 mol/yr"})
        curves = _unique([d for d in inside if d["color"][0] < 0.5 and abs(d["width"] - 1.0) < 1e-6])
        families = {"solid": [v for p, v in curves if p["dashes"] == SOLID],
                    "dashed": [v for p, v in curves if p["dashes"] == DASHED_2]}
        dotted = [v for p, v in curves if p["dashes"] == DOTTED]
        for fam, branches in families.items():
            if len(branches) != 2:
                raise ValueError(f"fig2{name} {fam}: expected two stable branches")
            upper, lower = sorted(branches, key=lambda v: v[:, 1].mean())
            ends = np.vstack([upper[[0, -1]], lower[[0, -1]]])
            conn = min(dotted, key=lambda v: min(np.hypot(*(ends - v[0]).T).min(),
                                                 np.hypot(*(ends - v[-1]).T).min()))
            gap = max(np.hypot(*(ends - v).T).min() for v in (conn[0], conn[-1]))
            checks.append({"check": f"fig2{name} {fam} connector gap", "n": 1, "value": float(gap), "unit": "pt"})
            for part, v in (("upper", upper), ("lower", lower), ("unstable", conn)):
                rows += _row("2", name, fam, part, v, fr)
    return rows, checks, frame_rows


def _connected(path) -> bool:
    its = path["items"]
    return all((a[2].x, a[2].y) == (b[1].x, b[1].y) for a, b in zip(its, its[1:]))


def _curvy(path, v: np.ndarray) -> bool:
    if not _connected(path):
        return False
    d = np.diff(v, axis=0)
    oblique = (np.abs(d[:, 0]) > 1e-3) & (np.abs(d[:, 1]) > 1e-3)
    return len(v) > 20 and oblique.mean() > 0.2


def fig3(page) -> tuple[list[dict], list[dict], list[dict]]:
    frames = _frames(page, FIG3)
    rows, checks, frame_rows = [], [], []
    for name, fr in frames.items():
        inside = [d for d in page.get_drawings() if d["type"] == "s" and fr.holds(d["rect"], pad=0.2)]
        kind = "zoom" if name.endswith("zoom") else "main"
        xs = _ticks(page, fr, "x", *TICK_LEN[kind])
        ys = _ticks(page, fr, "y", *TICK_LEN[kind])
        kx, cx, rx = _tick_fit(xs, *FIG3_TICKS["x"][kind])
        ky, cy, ry = _tick_fit(ys, *FIG3_TICKS["y"]["ac" if name[0] in "ac" else "bd"])
        lim = (kx * fr.x0 + cx, kx * fr.x1 + cx, ky * fr.y0 + cy, ky * fr.y1 + cy)
        checks += [
            {"check": f"fig3{name} x ticks", "n": len(xs), "value": rx, "unit": "Gyr max residual"},
            {"check": f"fig3{name} y ticks", "n": len(ys), "value": ry,
             "unit": ("decades" if name[0] in "ac" else "1e11 mol/yr") + " max residual"},
            {"check": f"fig3{name} frame left", "n": 1, "value": lim[0], "unit": "Gyr ago"},
            {"check": f"fig3{name} frame right", "n": 1, "value": lim[1], "unit": "Gyr ago"},
            {"check": f"fig3{name} frame top", "n": 1, "value": lim[2], "unit": "axis units"},
            {"check": f"fig3{name} frame bottom", "n": 1, "value": lim[3], "unit": "axis units"},
        ]
        right = (np.nan, np.nan)
        if name[0] in "ac":
            rs = _right_ticks(page, fr)
            if len(rs) != 6 or len(ys) != 7:
                raise ValueError(f"fig3{name}: expected 6 right and 7 left major ticks, found {len(rs)}, {len(ys)}")
            kr, cr, rr = _tick_fit(rs, *RIGHT_AXIS)
            pt0 = -cy / ky                                   # left value 0 (1 PAL)
            right = (kr * pt0 + cr, kr / ky)
            checks += [
                {"check": f"fig3{name} right ticks", "n": len(rs), "value": rr, "unit": "decades max residual"},
                {"check": f"fig3{name} right axis at 1 PAL", "n": 1, "value": 10 ** right[0], "unit": "atm"},
                {"check": f"fig3{name} right/left decade ratio", "n": 1, "value": right[1], "unit": ""},
            ]
        fr = Frame(fr.x0, fr.x1, fr.y0, fr.y1, lim)
        frame_rows.append(_frame_row("3", name, fr, right))
        for p, v in _unique(inside):
            style = p["dashes"]
            if name[0] in "ac":
                if style == DASHED_3:
                    curve = "methane"
                elif style == SOLID and p["color"][0] < 0.5 and _curvy(p, v):
                    curve = "oxygen"
                else:
                    continue
            else:
                if p["color"][0] > 0.5 and abs(p["width"] - 2.0) < 1e-6:
                    curve = "net"
                elif style == DASHED_3:
                    curve = "burial"
                elif style == DASHDOT:
                    curve = "input"
                elif style == SOLID and p["color"][0] < 0.5 and _curvy(p, v):
                    curve = "escape"
                else:
                    continue
            rows += _row("3", name, curve, "trace", v, fr)
    return rows, checks, frame_rows


SI_FIGS = {  # page index, (x first major, step), (y first major from top, step), tick length window
    "S2": (6, (14.0, 2.0), (16.0, -1.0), (1.5, 1.8)),
    "S3": (7, (8.0, 2.0), (6.0, -2.0), (1.5, 1.8)),
}
S2_MARKERS = {"re": "0.01 PAL", "cccc": "0.1 PAL", "lll": "1 PAL", "llll": "1 PAL"}


def si_figs(doc) -> tuple[list[dict], list[dict]]:
    """Supplementary Figs 2 and 3 as log10 values: S2 marker centres by oxygen
    level (caption: triangles 1 PAL, circles 0.1 PAL, squares 0.01 PAL), and
    the fitted line of S3."""
    rows, checks = [], []
    for fig, (pg, xt, yt, tl) in SI_FIGS.items():
        page = doc[pg]
        rect = max((d["rect"] for d in page.get_drawings() if d["items"][0][0] == "re"), key=lambda r: r.width)
        fr = Frame(rect.x0, rect.x1, rect.y0, rect.y1, (0, 1, 0, 1))
        xs, ys = _ticks(page, fr, "x", *tl), _ticks(page, fr, "y", *tl)
        kx, cx, rx = _tick_fit(xs, *xt)
        ky, cy, ry = _tick_fit(ys, *yt)
        checks += [{"check": f"{fig} x ticks", "n": len(xs), "value": rx, "unit": "decades max residual"},
                   {"check": f"{fig} y ticks", "n": len(ys), "value": ry, "unit": "decades max residual"}]
        fr = Frame(fr.x0, fr.x1, fr.y0, fr.y1,
                   (kx * fr.x0 + cx, kx * fr.x1 + cx, ky * fr.y0 + cy, ky * fr.y1 + cy))
        inside = [d for d in page.get_drawings() if d["type"] == "s" and fr.holds(d["rect"], pad=8)]
        if fig == "S2":
            marks: dict[str, list] = {}
            for d in inside:
                kind = "".join(it[0] for it in d["items"])
                r = d["rect"]
                if kind in S2_MARKERS and 3 < r.width < 8:
                    marks.setdefault(S2_MARKERS[kind], []).append(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2))
            for level, pts in marks.items():
                rows += _row("S2", "", level, "markers", np.array(sorted(pts)), fr)
        else:
            line = [d for d in inside if abs(d["width"] - 0.99) < 0.01 and len(d["items"]) > 50]
            if len(line) != 1:
                raise ValueError("S3: expected one fitted line")
            rows += _row("S3", "", "fit", "line", _vertices(line[0]), fr)
    return rows, checks


def extract(pdf: Path = DEFAULT_PDF, si_pdf: Path = SI_PDF):
    import pymupdf

    if _sha(pdf) != PDF_SHA256:
        raise ValueError(f"{pdf} is not the expected article PDF")
    if _sha(si_pdf) != SI_SHA256:
        raise ValueError(f"{si_pdf} is not the expected Supplementary Information PDF")
    doc = pymupdf.open(pdf)
    r2, c2, f2 = fig2(doc[1])
    r3, c3, f3 = fig3(doc[2])
    rs, cs = si_figs(pymupdf.open(si_pdf))
    return r2 + r3, c2 + c3 + cs, f2 + f3, rs


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.9g}" if isinstance(v, float) else v) for k, v in r.items()})


def load(path: Path = OUT) -> dict[tuple[str, str, str, str], np.ndarray]:
    """Vertices keyed by (figure, panel, curve, part), as an (n, 2) array of x, y."""
    out: dict = {}
    with path.open() as fh:
        for r in csv.DictReader(fh):
            out.setdefault((r["figure"], r["panel"], r["curve"], r["part"]), []).append((float(r["x"]), float(r["y"])))
    return {k: np.array(v) for k, v in out.items()}


def load_frames(path: Path = FRAMES) -> dict[tuple[str, str], dict[str, float]]:
    """Calibrated frame of each panel, keyed by (figure, panel)."""
    with path.open() as fh:
        return {(r["figure"], r["panel"]): {k: float(v) for k, v in r.items() if k not in ("figure", "panel")}
                for r in csv.DictReader(fh)}


def main(pdf: Path = DEFAULT_PDF, si_pdf: Path = SI_PDF, out: Path = OUT) -> None:
    rows, checks, frames, si_rows = extract(pdf, si_pdf)
    write(out, rows)
    write(out.with_name("glw2006_calibration.csv"), checks)
    write(out.with_name(FRAMES.name), frames)
    write(out.with_name(SI_OUT.name), si_rows)
    for c in checks:
        print(c)


if __name__ == "__main__":
    main(*(Path(a) for a in sys.argv[1:]))
