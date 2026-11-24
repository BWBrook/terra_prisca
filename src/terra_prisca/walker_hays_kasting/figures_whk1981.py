"""Regenerate the reconstruction of Walker, Hays & Kasting (1981) Fig. 2.

    uv run python -m terra_prisca.walker_hays_kasting.figures_whk1981 [outdir]

Writes whk1981_fig2.png and whk1981_fig2.csv: dT and log10 P/P0 against dTe
for V/V0 = 0.5, 1, 2 and 4 (eqs 2 and 6 solved together), and the constant-P
line dT = 2 dTe.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .whk1981 import FAITHFUL, sweep

V_RATIOS = (0.5, 1.0, 2.0, 4.0)
DTE = np.round(np.arange(-20.0, 6.0001, 0.1), 10)


def curves(r=FAITHFUL) -> dict[float, np.ndarray]:
    return {v: sweep(DTE, v, r) for v in V_RATIOS}


def main(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    c = curves()
    fig, (a, b) = plt.subplots(2, 1, figsize=(5.2, 8.0), sharex=True)
    for v, s in c.items():
        a.plot(s[:, 0], s[:, 1], "k-", lw=1)
        b.plot(s[:, 0], np.log10(s[:, 2]), "k-", lw=1)
        i = int(np.argmax(s[:, 1] >= -20))
        a.annotate(f"{v:g}", (s[i, 0], s[i, 1]), xytext=(4, 3), textcoords="offset points", fontsize=8)
        j = int(np.argmax(np.log10(s[:, 2]) <= 2.4))  # first point inside panel b's axes
        b.annotate(f"{v:g}", (s[j, 0], np.log10(s[j, 2])), xytext=(4, 3), textcoords="offset points", fontsize=8)
    a.plot(DTE, 2 * DTE, "k--", lw=1, label="constant P")
    a.set_ylim(-20, 10)
    a.set_ylabel("dT = Ts - 285 K (K)")
    a.legend(fontsize=8, loc="lower right")
    a.set_title("a. surface temperature; labels are V/V0", fontsize=9)
    b.set_ylim(-1, 2.6)
    b.set_ylabel("log10 P/P0")
    b.set_xlabel("dTe = Te - 253 K (K)")
    b.set_title("b. CO2 partial pressure", fontsize=9)
    b.set_xlim(-20, 5.8)
    fig.suptitle("Walker, Hays & Kasting (1981) Fig. 2, reconstructed", fontsize=10)
    fig.tight_layout()
    fig.savefig(outdir / "whk1981_fig2.png", dpi=120, metadata={"Software": None})
    plt.close(fig)

    with (outdir / "whk1981_fig2.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["dTe", "dT_constant_P",
                    *(f"dT_V{v:g}" for v in V_RATIOS), *(f"log10P_V{v:g}" for v in V_RATIOS)])
        for i, x in enumerate(DTE):
            w.writerow([f"{x:.1f}", f"{2 * x:.4f}",
                        *(f"{c[v][i, 1]:.4f}" for v in V_RATIOS),
                        *(f"{np.log10(c[v][i, 2]):.5f}" for v in V_RATIOS)])


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/walker_hays_kasting/figures"))
