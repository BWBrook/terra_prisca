"""Scoping R* for acetogen versus methanogen with matched growth anchors and swept transfers.

uv run python models/haze_world/review/stage3_rstar_scoping.py
Not a calibration: shows which unknowns decide the steady-state H2 winner.
Q = m + d/Y; R* = p* + Km Q/(qmax - Q), nonviable if Q >= qmax. Rates in mmol H2 gDW^-1 h^-1.
"""

import itertools
import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world.hydrogen_uptake import ACETOGEN, MSB, parameters

HERE = Path(__file__).resolve().parent
R = 8.314
E_MAINT = 69e3  # Tijhuis et al. 1993 (10.1002/bit.260420415), value to verify against source

# Matched acetogen anchor, Peters et al. 1998, A. woodii, 30 C.
Y_A, M_A30, MU_A30 = 1.7, 1.6, 0.024
QMAX_A30 = MU_A30 / Y_A * 1e3 + M_A30


def arrhenius(t_c, ref_c=30.0, e=E_MAINT):
    return float(np.exp(-e / R * (1 / (t_c + 273.15) - 1 / (ref_c + 273.15))))


def rstar(qmax, km, pstar, y, m, d):
    q = m + d / y * 1e3
    return pstar + km * q / (qmax - q) if q < qmax else float("inf")


def case(t_c, gamma, y_m, m_m30, d, pstar_a):
    a, b = parameters(t_c, ACETOGEN), parameters(t_c, MSB)
    qa = QMAX_A30 * a.vmax_nmol_h / parameters(30.0, ACETOGEN).vmax_nmol_h
    qm = gamma * QMAX_A30 * b.vmax_nmol_h / parameters(30.0, MSB).vmax_nmol_h
    ra = rstar(qa, a.km_pa, pstar_a, Y_A, M_A30 * arrhenius(t_c), d)
    rm = rstar(qm, b.km_pa, 1.0, y_m, m_m30 * arrhenius(t_c), d)
    return ra, rm


def main():
    grid = dict(gamma=(0.38, 0.74, 1.5), y_m=(0.4, 0.78, 1.7), m_m30=(0.3, 1.0, 2.3),
                d=(1e-4, 1e-3, 1e-2), pstar_a=(5.0, 20.0, 95.0))
    rows = []
    for t_c in (4.0, 30.0):
        for combo in itertools.product(*grid.values()):
            ra, rm = case(t_c, *combo)
            rows.append(dict(t_c=t_c, **dict(zip(grid, combo)), rstar_a=ra, rstar_m=rm,
                             winner="none" if np.isinf(ra) and np.isinf(rm) else "acetogen" if ra < rm else "methanogen"))
    summary = {}
    for t_c in (4.0, 30.0):
        sub = [r for r in rows if r["t_c"] == t_c]
        summary[f"{t_c:g}C"] = {w: sum(r["winner"] == w for r in sub) for w in ("acetogen", "methanogen", "none")}
    # Pattern filter: methanogens win at 30 C (warm anoxic sediments); report what that leaves at 4 C.
    key = lambda r: tuple(r[k] for k in grid)
    warm = {key(r) for r in rows if r["t_c"] == 30.0 and r["winner"] == "methanogen"}
    cold = [r for r in rows if r["t_c"] == 4.0 and key(r) in warm]
    summary["4C_given_methanogens_win_30C"] = {w: sum(r["winner"] == w for r in cold) for w in ("acetogen", "methanogen", "none")}
    decisive = {}
    for k, values in grid.items():
        decisive[k] = {str(v): {w: sum(r["winner"] == w and r[k] == v for r in cold) for w in ("acetogen", "methanogen")}
                       for v in values}
    out = dict(anchors=dict(Y_A=Y_A, m_A30=M_A30, qmax_A30=QMAX_A30, E_maint_J=E_MAINT,
                            maint_factor_4C=arrhenius(4.0)), grid=grid, summary=summary,
               cold_winner_by_parameter=decisive)
    (HERE / "stage3_rstar_scoping.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
