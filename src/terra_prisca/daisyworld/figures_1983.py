"""Regenerate Figs 1a-d and 2 of Watson & Lovelock (1983).

    uv run python -m terra_prisca.daisyworld.figures_1983 [outdir]
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .wl1983 import EXPERIMENTS, hysteresis_sweep, lifeless_temperature

LUM_MIN, LUM_MAX, LUM_STEP = 0.6, 1.7, 0.002

TITLES = {
    "fig1a_neutral": "Fig. 1a: neutral daisies (albedo 0.5)",
    "fig1b_black": "Fig. 1b: black daisies only",
    "fig1c_white": "Fig. 1c: white daisies only",
    "fig1d_both": "Fig. 1d: black and white daisies",
    "fig2_cloud": "Fig. 2: cloud (albedo 0.8) over black daisies",
}


def run_all() -> dict[str, tuple[dict, dict]]:
    return {name: hysteresis_sweep(LUM_MIN, LUM_MAX, LUM_STEP, p) for name, p in EXPERIMENTS.items()}


def write_csv(results: dict, path: Path) -> None:
    with path.open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["experiment", "direction", "lum", "area_white", "area_black", "t_e", "t_w", "t_b", "converged"])
        for name, (up, down) in results.items():
            for direction, r in (("up", up), ("down", down)):
                for i in range(len(r["lum"])):
                    w.writerow([name, direction, f"{r['lum'][i]:.4f}", f"{r['a_w'][i]:.6f}", f"{r['a_b'][i]:.6f}",
                                f"{r['t_e'][i]:.4f}", f"{r['t_w'][i]:.4f}", f"{r['t_b'][i]:.4f}", int(r["converged"][i])])


def plot_panel(fig, outer, name: str, up: dict, down: dict) -> None:
    p = EXPERIMENTS[name]
    inner = outer.subgridspec(2, 1, hspace=0.0)
    ax_a, ax_t = fig.add_subplot(inner[0]), fig.add_subplot(inner[1])
    for r, ls, label in ((up, "-", "increasing L"), (down, "--", "decreasing L")):
        if p.black:
            ax_a.plot(r["lum"], 100 * r["a_b"], ls, color="0.1", lw=1.3, label=f"black, {label}" if p.white else label)
        if p.white:
            ax_a.plot(r["lum"], 100 * r["a_w"], ls, color="0.55", lw=1.3, label=f"white, {label}")
        ax_t.plot(r["lum"], r["t_e"], ls, color="0.1", lw=1.3)
    ax_t.plot(up["lum"], lifeless_temperature(up["lum"], p), ":", color="0.3", lw=1.2, label="no life")
    ax_a.set_title(TITLES[name], fontsize=10, loc="left")
    ax_a.set_ylabel("Area (%)")
    ax_t.set_ylabel("Temp (°C)")
    ax_t.set_xlabel("Solar luminosity")
    ax_a.set_ylim(0, 80)
    ax_t.set_ylim(-10, 70)
    for ax in (ax_a, ax_t):
        ax.set_xlim(0.55, 1.7)
    ax_a.tick_params(labelbottom=False)
    ax_a.legend(fontsize=7, frameon=False, loc="upper right")
    ax_t.legend(fontsize=7, frameon=False, loc="upper left")


def main(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    results = run_all()
    write_csv(results, outdir / "wl1983_sweeps.csv")
    fig = plt.figure(figsize=(11, 13))
    grid = fig.add_gridspec(3, 2, hspace=0.35, wspace=0.25)
    for k, name in enumerate(EXPERIMENTS):
        plot_panel(fig, grid[k // 2, k % 2], name, *results[name])
    fig.suptitle("Daisyworld, Watson & Lovelock (1983): reconstruction", fontsize=12)
    fig.savefig(outdir / "wl1983_figures.png", dpi=130, bbox_inches="tight")
    for name in results:
        up, down = results[name]
        print(f"{name}: non-converged steps up={int((~up['converged'].astype(bool)).sum())} "
              f"down={int((~down['converged'].astype(bool)).sum())}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/daisyworld/figures"))
