"""Regenerate the reconstruction of Sellers (1969).

    uv run python -m terra_prisca.budyko_sellers.figures_sellers1969 [outdir]

Writes sellers1969_figures.png, sellers1969_present.csv (the present state by
belt and circle) and sellers1969_solar.csv (global mean temperature against
the solar constant for the three albedo laws, with the hysteresis of the
0.009 law: continuation down from today and back up from the ice-covered state).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .fidelity_sellers1969 import FIG7_CURVES, S_GRID, sweep
from .sellers1969 import BELT_LAT, CIRC_LAT, KLY_YR, NB, Scenario, model


def ice_return(m):
    """0.009 law from the ice-covered state, S rising: the planet stays frozen far above today's S."""
    s_up = np.round(np.arange(1.80, 3.0001, 0.01), 4)
    ice = m.solve(Scenario(s=1.80), np.full(NB, 175.0))
    sts = m.continuation(s_up, lambda x: Scenario(s=x), start=ice["T"])
    return s_up, np.array([st["Tbar"] if st["ok"] else np.nan for st in sts])


def main(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    m = model()
    p = m.present()
    laws = {law: sweep(m, law) for law in ("0.009", "0.005-anchored", "fixed")}
    s_up, t_up = ice_return(m)
    prof = {k: m.solve(Scenario(**kw), np.full(NB, 250.0) if k == "i" else None)["Tc"] for k, kw in FIG7_CURVES.items()}

    fig, ax = plt.subplots(2, 2, figsize=(12, 9))
    a = ax[0, 0]
    a.plot(BELT_LAT, p["Tc"], "k-", label="T (deg C)")
    a2 = a.twinx()
    a2.plot(BELT_LAT, p["albedo"], "C3--", label="albedo")
    a2.set_ylabel("planetary albedo", color="C3")
    a.set_title(f"Present state: T-bar = {p['Tbar']:.2f} deg C")
    a.set_ylabel("sea-level T (deg C)")
    a = ax[0, 1]
    for k in ("C", "Lc", "F", "P"):
        a.plot(CIRC_LAT, p[k] / 1e3, label=k)
    a.set_title("Northward transport (kcal cm-1 s-1)")
    a = ax[1, 0]
    for law, c in (("0.009", "k"), ("0.005-anchored", "C0"), ("fixed", "C2")):
        a.plot(S_GRID, laws[law], color=c, label=law)
    a.plot(s_up, t_up, "k:", lw=1, label="0.009 from ice, S rising")
    a.axvline(2.0, color="grey", lw=0.5)
    a.set_xlabel("solar constant S (ly/min)")
    a.set_ylabel("T-bar (deg C)")
    a.set_title("Global mean temperature against S (Fig. 6)")
    a = ax[1, 1]
    for k, t in prof.items():
        a.plot(BELT_LAT, t, label=k)
    a.set_title("Profiles of Fig. 7 (a present; i on its cold equilibrium)")
    for a in (ax[0, 0], ax[0, 1], ax[1, 1]):
        a.set_xlim(90, -90)
        a.set_xlabel("latitude (deg, N positive)")
    for a in ax.flat:
        a.legend(fontsize=7)
    fig.suptitle("Sellers (1969) reconstruction, faithful reading")
    fig.tight_layout()
    fig.savefig(outdir / "sellers1969_figures.png", dpi=110)
    plt.close(fig)

    dv = m.belt_divergence(p)
    with (outdir / "sellers1969_present.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["kind", "latitude", "T_degC", "albedo", "Rs_kly_yr", "dC", "Ldc", "dF", "v_cm_s",
                    "C_kcal_cm_s", "Lc_kcal_cm_s", "F_kcal_cm_s", "P_kcal_cm_s"])
        for i in range(NB):
            w.writerow(["belt", BELT_LAT[i], round(p["Tc"][i], 4), round(p["albedo"][i], 4),
                        round(p["Rs"][i] / KLY_YR, 4), round(dv["C"][i], 4), round(dv["Lc"][i], 4),
                        round(dv["F"][i], 4), "", "", "", "", ""])
        for j in range(NB - 1):
            w.writerow(["circle", CIRC_LAT[j], "", "", "", "", "", "", round(p["v"][j], 4),
                        *(round(p[k][j] / 1e3, 4) for k in ("C", "Lc", "F", "P"))])
    with (outdir / "sellers1969_solar.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["S_ly_min", "Tbar_0.009", "Tbar_0.005_anchored", "Tbar_fixed"])
        for i, s in enumerate(S_GRID):
            w.writerow([s, *(round(float(laws[k][i]), 4) for k in laws)])
        w.writerow([])
        w.writerow(["S_ly_min", "Tbar_0.009_from_ice"])
        for s, t in zip(s_up, t_up):
            w.writerow([s, round(float(t), 4)])


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/budyko_sellers/figures"))
