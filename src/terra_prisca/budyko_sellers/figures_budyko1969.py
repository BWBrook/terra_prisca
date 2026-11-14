"""Regenerate the reconstruction of Budyko (1969) Figs 3-6.

    uv run python -m terra_prisca.budyko_sellers.figures_budyko1969 [outdir]

Writes budyko1969_figures.png and budyko1969_curves.csv (zonal profiles and
the ice-edge branch, including its unstable equatorward part).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .budyko1969 import model

LAT = np.linspace(0.0, 90.0, 901)


def main(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    m = model()
    profiles = {"T0": m.profile(LAT), "T1.0": m.profile(LAT, -0.010), "T1.5": m.profile(LAT, -0.015),
                "Tq": m.ice_free(LAT)}
    branch = m.branch(np.arange(m.p.edge_now, 0.0, -0.1))
    crit = m.critical()
    stable = branch["edge"] >= crit["edge"]

    fig, ax = plt.subplots(2, 2, figsize=(11, 8.5))
    a = ax[0, 0]
    a.plot(LAT, profiles["T0"], "k-", label="T0, present (eq. 4)")
    a.set_title("Fig. 3: present-day zonal temperature")
    a = ax[0, 1]
    for name, ls in (("T0", "-"), ("T1.0", "--"), ("T1.5", ":")):
        a.plot(LAT, profiles[name], "k" + ls, label=name)
    a.set_title("Fig. 4: radiation reduced by 0, 1.0 and 1.5%")
    a = ax[1, 0]
    a.plot(branch["eps"][stable], branch["tp"][stable], "k-", label="T_p, stable")
    a.plot(branch["eps"][~stable], branch["tp"][~stable], "k:", lw=0.8, label="T_p, unstable")
    a2 = a.twinx()
    a2.plot(branch["eps"][stable], branch["edge"][stable], "C3-", label="phi_0, stable")
    a2.plot(branch["eps"][~stable], branch["edge"][~stable], "C3:", lw=0.8, label="phi_0, unstable")
    a2.set_ylabel("ice edge phi_0 (deg)", color="C3")
    a.axvline(crit["eps"], color="grey", lw=0.6)
    a.set_xlim(0.002, -0.03)
    a.set_xlabel("dQ_p / Q_p")
    a.set_ylabel("T_p (deg C)")
    a.set_title(f"Fig. 5: runaway at dQ_p/Q_p = {crit['eps']:.4f}, phi_0 = {crit['edge']:.1f} deg")
    a = ax[1, 1]
    a.plot(LAT, profiles["T0"], "k-", label="T0")
    a.plot(LAT, profiles["Tq"], "k--", label="Tq, no polar ice")
    a.set_title("Fig. 6: effect of the polar ice")
    for a in (ax[0, 0], ax[0, 1], ax[1, 1]):
        a.set_xlabel("latitude (deg)")
        a.set_ylabel("T (deg C)")
        a.set_xlim(0, 90)
        a.axhline(0, color="grey", lw=0.5)
        a.legend(fontsize=8)
    ax[1, 0].legend(loc="lower left", fontsize=8)
    fig.suptitle("Budyko (1969) reconstruction, faithful reading", fontsize=11)
    fig.tight_layout()
    fig.savefig(outdir / "budyko1969_figures.png", dpi=120)
    plt.close(fig)

    with (outdir / "budyko1969_curves.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["latitude", *profiles])
        for i in range(0, len(LAT), 5):
            w.writerow([round(LAT[i], 2), *(round(float(v[i]), 4) for v in profiles.values())])
    with (outdir / "budyko1969_branch.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["ice_edge", "dQp_over_Qp", "T_p", "stable"])
        for e, x, t, s in zip(branch["edge"], branch["eps"], branch["tp"], stable):
            w.writerow([round(float(e), 2), round(float(x), 6), round(float(t), 4), bool(s)])


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/budyko_sellers/figures"))
