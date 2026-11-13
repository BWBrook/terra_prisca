"""Shared figure style: one palette, one type scale, one save routine.

Colour follows the entity in every figure. Each colour is paired with a
marker or line style so that panels stay legible in greyscale print.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "models" / "haze_world" / "paper" / "figures"
DATA = OUT / "data"

MM = 1 / 25.4
SINGLE = 84 * MM
DOUBLE = 174 * MM

INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#9a9893"
GRID = "#e4e3df"

ACETOGEN = "#2a78d6"
METHANOGEN = "#eb6834"
THIRD = "#1baf7a"

ENTITY = {
    "acetogen": dict(color=ACETOGEN, marker="o", linestyle="-"),
    "methanogen": dict(color=METHANOGEN, marker="s", linestyle="--"),
    "mixture": dict(color=INK, marker="D", linestyle="-"),
    "temperature": dict(color=INK, marker=None, linestyle="-"),
}

MECHANISM = {
    "exact": dict(color=INK, marker="D"),
    "acetate": dict(color=ACETOGEN, marker="o"),
    "spread": dict(color=THIRD, marker="^"),
    "onoff": dict(color=MUTED, marker="."),
}

RC = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 7.5,
    "axes.labelsize": 7.5,
    "axes.titlesize": 7.5,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6.5,
    "axes.linewidth": 0.6,
    "axes.edgecolor": INK_2,
    "axes.labelcolor": INK,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "lines.linewidth": 1.2,
    "lines.markersize": 4,
    "legend.frameon": False,
    "savefig.dpi": 600,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
}


def apply():
    plt.rcParams.update(RC)


def panel_label(ax, letter, x=-0.16, y=1.04):
    ax.text(x, y, f"({letter})", transform=ax.transAxes, fontsize=8,
            fontstyle="italic", color=INK, ha="left", va="bottom")


def one_cell_line(ax, **kw):
    ax.axhline(0.0, color=INK_2, linewidth=0.7, linestyle=":", zorder=0, **kw)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=0.02,
                metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return OUT / f"{name}.pdf"
