"""Regenerate the reconstruction of Caldeira & Kasting (1992) Fig. 2.

    uv run python -m terra_prisca.biosphere_lifespan.figures_ck1992 [outdir]

Writes ck1992_fig2.png and ck1992_fig2.csv: Psoil, Patm, S/S0, Pi/Pi0 and T
over the next 1.6 Gyr, for the faithful reading (equilibrium constants traced
to the sources), the reading with the SO2 term fitted to the printed kink, and
the C3-only world (Pmin = 150 ppm). Every state column is left empty above
373.15 K, the top of the range the climate fits were made over.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import ck1992 as m

T = np.round(np.arange(0.0, 1.6 + 1e-9, 0.01), 6)
RUNS = {"faithful": m.FAITHFUL, "so2_fitted": m.READINGS["so2_fitted"], "c3": m.C3}
FIELDS = ("P_atm_ppm", "P_soil_ppm", "Pi_ratio", "T_K")


def runs() -> dict[str, dict[str, np.ndarray]]:
    out = {}
    for k, r in RUNS.items():
        tr = m.trajectory(T, r)
        for f in FIELDS:
            tr[f] = np.where(tr["in_fit"], tr[f], np.nan)
        out[k] = tr
    return out


def main(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    tr = runs()
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.0, 7.0), sharex=True)
    for k, ls, lab in (("faithful", "-", "faithful (source-traced constants)"),
                       ("so2_fitted", "--", f"SO2 term x {m.SO2_FIT_FACTOR} (fitted to the kink)"),
                       ("c3", ":", "C3 world, Pmin = 150 ppm")):
        a.semilogy(T, tr[k]["P_soil_ppm"], "C3" + ls, lw=1)
        a.semilogy(T, tr[k]["P_atm_ppm"], "C0" + ls, lw=1, label=lab)
        b.plot(T, tr[k]["Pi_ratio"], "C4" + ls, lw=1)
    a.set_ylim(1, 1e4), a.set_ylabel("pCO2 (ppm): Psoil red, Patm blue")
    a.legend(fontsize=7, loc="lower left")
    a2 = a.twinx()
    a2.plot(T, tr["faithful"]["S_ratio"], "C2-", lw=1)
    a2.set_ylim(1.0, 1.2), a2.set_ylabel("S/S0 (green)")
    b.set_ylim(0, 1.0), b.set_ylabel("Pi/Pi0 (purple)")
    b2 = b.twinx()
    for k, ls in (("faithful", "-"), ("so2_fitted", "--"), ("c3", ":")):
        b2.plot(T, tr[k]["T_K"], "C1" + ls, lw=1)
    b2.set_ylim(273, 373), b2.set_ylabel("T (K, orange)")
    b.set_xlim(0, 1.6), b.set_xlabel("Time t in Gyr from present")
    a.set_title(f"Caldeira & Kasting (1992) Fig. 2, reconstructed: 10 ppm at {m.co2_time(m.P_MIN_C4):.2f} Gyr "
                f"(fitted SO2: {m.co2_time(m.P_MIN_C4, RUNS['so2_fitted']):.2f})", fontsize=8)
    fig.tight_layout()
    fig.savefig(outdir / "ck1992_fig2.png", dpi=120, metadata={"Software": None})
    plt.close(fig)
    with (outdir / "ck1992_fig2.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["t_Gyr", "S_ratio", *(f"{f}_{k}" for k in RUNS for f in FIELDS)])
        for i, t in enumerate(T):
            row = [f"{t:.2f}", f"{tr['faithful']['S_ratio'][i]:.6f}"]
            for k in RUNS:
                row += ["" if not np.isfinite(tr[k][f][i]) else f"{tr[k][f][i]:.6g}" for f in FIELDS]
            w.writerow(row)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/biosphere_lifespan/figures"))
