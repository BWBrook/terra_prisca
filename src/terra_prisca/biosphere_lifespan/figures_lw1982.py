"""Regenerate the reconstruction of Lovelock & Whitfield (1982) Fig. 2.

    uv run python -m terra_prisca.biosphere_lifespan.figures_lw1982 [outdir]

Writes lw1982_fig2.png and lw1982_fig2.csv: the straight Sun line, sqrt(CO2)
under the faithful rule and the alternative readings, and the 150 ppm limit.
The temperature band is drawn from the limits the text states.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import lw1982 as m

T = np.round(np.arange(-4000.0, 2000.01, 10.0), 6)
CO2_KEYS = ("faithful", "text_7000", "two_thirds", "linear_c", "whk_constant_T")
# (t, C) vertices of the band as the text states it (upper, then lower limit).
BAND_UPPER = [(-3500, 40), (-2200, 40), (-2200, 25), (0, 25)]
BAND_LOWER = [(-3500, 15), (-2200, 15), (-2200, 5), (-2200, 15), (0, 15)]


def main(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    tc = T[T >= m.T_PAST]
    co2 = {k: np.sqrt(m.co2(tc, m.READINGS[k])) for k in CO2_KEYS}
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.4, 6.0), sharex=True, height_ratios=(2, 1))
    for k, style, lab in (("faithful", "k-", "faithful: 70,000 ppm at -3,500 Myr"),
                          ("text_7000", "k--", "text's 7,000 ppm"),
                          ("two_thirds", "k-.", "2/3 power"),
                          ("whk_constant_T", "k:", "WHK eq. (6), constant T")):
        keep = co2[k] >= np.sqrt(m.C_LIMIT)
        a.plot(tc[keep], co2[k][keep], style, lw=1, label=lab)
    a.axhline(np.sqrt(m.C_LIMIT), color="k", lw=0.6)
    a.text(150, np.sqrt(m.C_LIMIT) + 4, "150 ppm limit", fontsize=7)
    a.set_ylim(0, 300), a.set_ylabel("sqrt(CO2 / ppm)")
    a.legend(fontsize=7, loc="upper right")
    a2 = a.twinx()
    a2.plot(T, m.luminosity(T), "C3-", lw=1)
    a2.set_ylim(0.6, 1.3), a2.set_ylabel("solar luminosity (red)", color="C3")
    a.set_title(f"Lovelock & Whitfield (1982) Fig. 2, reconstructed: 150 ppm at +{m.lifespan():.0f} Myr", fontsize=9)
    b.plot(*zip(*BAND_UPPER), "k-", lw=0.8)
    b.plot(*zip(*BAND_LOWER), "k-", lw=0.8)
    b.set_ylim(0, 50), b.set_ylabel("temperature band (C),\nfrom the text")
    b.set_xlim(-4000, 2000), b.set_xlabel("time from present (Myr)")
    fig.tight_layout()
    fig.savefig(outdir / "lw1982_fig2.png", dpi=120, metadata={"Software": None})
    plt.close(fig)
    with (outdir / "lw1982_fig2.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["t_Myr", "L", *(f"sqrtC_{k}" for k in CO2_KEYS)])
        for i, t in enumerate(T):
            j = i - int(np.sum(T < m.T_PAST))
            w.writerow([f"{t:.0f}", f"{m.luminosity(t):.5f}",
                        *((f"{co2[k][j]:.4f}" if j >= 0 else "") for k in CO2_KEYS)])


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/biosphere_lifespan/figures"))
