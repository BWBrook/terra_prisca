"""Read the printed curves of Figs 2 and 3 straight from the article's vector paths.

    uv run --with pymupdf python -m terra_prisca.goldblatt_lenton_watson.vectors [pdf] [out.csv]

The Nature PDF (SHA-256 below) draws every curve as a stroked polyline, so the
published geometry can be read exactly rather than traced from a raster. Place
it at local/sources/goldblatt_lenton_watson/nature05169.pdf; it is copyrighted
and is not redistributed. The output CSV holds the curve vertices in data units
and is what the fidelity scoring and the tests read; PyMuPDF is needed only to
regenerate it.

Calibration. Each panel's frame is the grey quad drawn around it. For Fig. 2
the axes are fitted to the major (decade) ticks on the left and bottom frame
edges; the frame itself must then sit at the axis limits, which is checked.
Fig. 3 has fewer ticks, so its axes are the frame limits, checked against the
major ticks that exist.

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
DEFAULT_PDF = Path("local/sources/goldblatt_lenton_watson/nature05169.pdf")
OUT = Path("models/goldblatt_lenton_watson/fidelity/glw2006_vectors.csv")

SOLID, DASHED_2, DOTTED, DASHED_3, DASHDOT = "[] 0", "[ 6 6 ] 0", "[ .5 4 ] 0", "[ 6 2 ] 0", "[ 3 1 1 1 ] 0"

# Axis limits (x0, x1, y0, y1) in data units, read from the tick labels.
# Fig. 2: log10 of r or N (mol O2 equiv./yr) and log10 O2 (PAL).
# Fig. 3: time (Gyr ago, decreasing to the right) and log10 O2 (PAL) or flux (1e11 mol/yr).
FIG2 = {"a": (8.0, 16.0, 0.0, -11.0), "b": (10.0, 18.0, 0.0, -11.0)}
FIG3 = {"a": (2.5, 2.0, 0.0, -6.0), "a_zoom": (2.4, 2.399, 0.0, -6.0),
        "b": (2.5, 2.0, 8.0, -4.0), "b_zoom": (2.4, 2.399, 8.0, -4.0),
        "c": (2.5, 2.0, 0.0, -6.0), "c_zoom": (2.4, 2.399, 0.0, -6.0),
        "d": (2.5, 2.0, 8.0, -4.0), "d_zoom": (2.4, 2.399, 8.0, -4.0)}


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
        if d["type"] != "s" or d["color"][0] > 0.5 or abs(d["width"] - 0.5) > 1e-6:
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


def _tick_fit(pos, first, step):
    vals = first + step * np.arange(len(pos))
    k, c = np.polyfit(pos, vals, 1)
    return k, c, float(np.abs(k * pos + c - vals).max())


def _row(fig, panel, curve, part, v, fr: Frame):
    x, y = fr.data(v[:, 0], v[:, 1])
    return [{"figure": fig, "panel": panel, "curve": curve, "part": part, "vertex": i,
             "x": float(a), "y": float(b)} for i, (a, b) in enumerate(zip(x, y))]


def fig2(page) -> tuple[list[dict], list[dict]]:
    frames = _frames(page, FIG2)
    rows, checks = [], []
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
    return rows, checks


def _connected(path) -> bool:
    its = path["items"]
    return all((a[2].x, a[2].y) == (b[1].x, b[1].y) for a, b in zip(its, its[1:]))


def _curvy(path, v: np.ndarray) -> bool:
    if not _connected(path):
        return False
    d = np.diff(v, axis=0)
    oblique = (np.abs(d[:, 0]) > 1e-3) & (np.abs(d[:, 1]) > 1e-3)
    return len(v) > 20 and oblique.mean() > 0.2


def fig3(page) -> tuple[list[dict], list[dict]]:
    frames = _frames(page, FIG3)
    rows, checks = [], []
    for name, fr in frames.items():
        inside = [d for d in page.get_drawings() if d["type"] == "s" and fr.holds(d["rect"], pad=0.2)]
        ys = _ticks(page, fr, "y", *((0.4, 0.5) if name.endswith("zoom") else (1.0, 1.5)))
        vals = fr.data(fr.x0, ys)[1]
        step = 1.0 if name[0] in "ac" else 2.0
        checks.append({"check": f"fig3{name} y ticks off grid", "n": len(ys),
                       "value": float(np.abs(vals - step * np.round(vals / step)).max()),
                       "unit": "decades" if name[0] in "ac" else "1e11 mol/yr"})
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
    return rows, checks


def extract(pdf: Path = DEFAULT_PDF) -> tuple[list[dict], list[dict]]:
    import pymupdf

    if _sha(pdf) != PDF_SHA256:
        raise ValueError(f"{pdf} is not the expected article PDF")
    doc = pymupdf.open(pdf)
    r2, c2 = fig2(doc[1])
    r3, c3 = fig3(doc[2])
    return r2 + r3, c2 + c3


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


def main(pdf: Path = DEFAULT_PDF, out: Path = OUT) -> None:
    rows, checks = extract(pdf)
    write(out, rows)
    write(out.with_name("glw2006_calibration.csv"), checks)
    for c in checks:
        print(c)


if __name__ == "__main__":
    main(*(Path(a) for a in sys.argv[1:]))
