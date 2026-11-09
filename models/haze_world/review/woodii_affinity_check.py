"""In-growth affinity implied by the Peters et al. (1998) chemostat residual H2.

uv run python models/haze_world/review/woodii_affinity_check.py
At steady state R*(D) = p* + K Q/(s - Q), Q = m + D/Y. Fit K (and s) to the four
rounded residual-H2 means in log space, with Y and m from Table 2.
"""

import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
ROWS = list(csv.DictReader(open(HERE.parent / "evidence/peters1998_chemostat.csv")))
D = np.array([float(r["dilution_h^-1"]) for r in ROWS])
H = np.array([float(r["residual_H2_Pa"]) for r in ROWS])
Y, M, MU_MAX = 1.7, 1.6, 0.024


def main():
    q = M + D / Y * 1e3
    out = {"transferred_K_A_bakii_30C_pa": 520.0, "fits": []}
    for pstar in (0.0, 20.0):
        res = least_squares(lambda x: np.log(pstar + x[0] * q / (x[1] - q)) - np.log(H),
                            [100.0, 15.0], bounds=([1.0, q.max() + 1e-3], [5000.0, 100.0]))
        k, s = res.x
        out["fits"].append(dict(pstar_pa=pstar, free_capacity=True, K_pa=k, s_mmol_gdw_h=s,
                                washout_h=(s - M) * Y / 1e3,
                                predicted_pa=list(pstar + k * q / (s - q))))
    s = M + MU_MAX / Y * 1e3
    k = float(np.exp(np.mean(np.log(H * (s - q) / q))))
    out["fits"].append(dict(pstar_pa=0.0, free_capacity=False, K_pa=k, s_mmol_gdw_h=s,
                            predicted_pa=list(k * q / (s - q))))
    out["observed_pa"] = list(H)
    (HERE / "woodii_affinity_check.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
