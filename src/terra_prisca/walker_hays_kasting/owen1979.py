"""WHK eq. (5) checked against Owen, Cess & Ramanathan (1979), Table 1.

Nature 277, 640-642, doi:10.1038/277640a0.

    uv run python -m terra_prisca.walker_hays_kasting.owen1979 [outdir]

WHK (p. 9779) obtain T_g(CO2) by subtracting T_e and T_g(H2O) from Owen et al.'s
quoted surface temperatures, and fit 2.3 (P/P0)^0.364. Owen et al.'s present
row gives 290 K, not WHK's 285 K, so the subtraction leaves 4.8 K today, not
2.3 K. The printed law is approximately consistent with an inferred procedure:
lower Owen et al.'s temperatures by 5 K (to WHK's present) and pass a power law
through today and the 4.25 Gyr row, which gives exponent 0.367. WHK state
neither the normalisation nor the choice of fitted rows, so their actual
procedure stays undocumented.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

from . import whk1981 as w

# Owen et al. (1979) Table 1: (Gyr before present, S W m-2, P_CO2 bar, Ts K,
# Ts K without the weak CO2 bands).
TABLE1 = [(4.25, 1039, 0.31, 310, 284), (3.5, 1096, 0.070, 296, 284), (3.0, 1133, 0.033, 293, 284),
          (2.5, 1171, 0.018, 292, 286), (2.0, 1209, 0.0086, 290, 286), (1.5, 1247, 0.0029, 288, 286),
          (1.0, 1284, 0.00065, 286, 285), (0.5, 1322, 0.00032, 287, 287), (0.0, 1360, 0.00032, 290, 290)]
P0_BAR = 0.00032
S0 = 1360.0


def derived(shift_K: float = 5.0, weak_bands: bool = True) -> dict[str, np.ndarray]:
    """T_g(CO2) implied by Owen et al.'s Ts after WHK's subtraction (eqs 3-4)."""
    t = np.array(TABLE1, float)
    ts = (t[:, 3] if weak_bands else t[:, 4]) - shift_K
    te = w.TE0 * (t[:, 1] / S0) ** 0.25
    tg_h2o = 29.7 + w.FAITHFUL.h2o_slope * (ts - w.TS0)
    return {"gyr": t[:, 0], "S": t[:, 1], "p": t[:, 2] / P0_BAR, "ts": ts, "te": te, "tg_co2": ts - te - tg_h2o}


def eq5(p):
    return w.FAITHFUL.gh_coeff * np.asarray(p, float) ** w.FAITHFUL.gh_exponent


def fits() -> list[dict]:
    rows = []
    for label, shift, weak in (("shifted to 285 K", 5.0, True), ("as printed (290 K today)", 0.0, True),
                               ("shifted, weak bands deleted", 5.0, False)):
        d = derived(shift, weak)
        p, g = d["p"], d["tg_co2"]
        b_end = float(np.log(g[0] / g[-1]) / np.log(p[0] / p[-1]))
        (a_ls, b_ls), _ = curve_fit(lambda x, a, b: a * x ** b, p, g, p0=(2.3, 0.36))
        resid = g - eq5(p)
        rows.append({"owen_temperatures": label, "tg_co2_today": float(g[-1]),
                     "endpoint_exponent": b_end, "endpoint_coefficient": float(g[-1]),
                     "lsq_coefficient": float(a_ls), "lsq_exponent": float(b_ls),
                     "eq5_resid_max": float(np.abs(resid).max()),
                     "eq5_resid_rms": float(np.sqrt(np.mean(resid ** 2)))})
    return rows


def rows_table() -> list[dict]:
    d = derived()
    return [{"gyr_bp": g, "S": s, "p_over_p0": p, "ts_owen_minus_5": ts, "te": te,
             "tg_co2_derived": tg, "tg_co2_eq5": float(eq5(p)), "residual": tg - float(eq5(p))}
            for g, s, p, ts, te, tg in zip(d["gyr"], d["S"], d["p"], d["ts"], d["te"], d["tg_co2"])]


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        wr.writeheader()
        for r in rows:
            wr.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()})


def main(outdir: Path = Path("models/walker_hays_kasting/fidelity")) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    write(outdir / "whk1981_eq5_owen_rows.csv", rows_table())
    write(outdir / "whk1981_eq5_owen_fits.csv", fits())


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/walker_hays_kasting/fidelity"))
