"""Issue 1 check: does habitat spread set the local sensitivity geometrically?

Weak-mixing limit: habitats colder than T* are acetogen-held, warmer ones
methanogen-held. Steady methane balance then gives
    1/|S| = 1/k + 1/|S_geo|,   |S_geo| = 2 sigma (P_lo/P) Q/(Q-1),
with k = |dT_clim/dr| r* (haze sensitivity per e-fold of methane) and Q the
homogeneous coexistence supply ratio (Q -> infinity at f = 0). No fitted
parameters. Compares against every fixed-chemistry spread state in ESM S4.

Run: uv run python models/haze_world/review/issue1_geometric_check.py
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
S4 = ROOT / "models/haze_world/paper/esm/s4_states.csv"
S8 = ROOT / "models/haze_world/paper/esm/s8_coexistence_interval.csv"
OUT = Path(__file__).with_suffix(".json")

SLOPE = 721.258          # K per unit ratio at the reference switch (ESM S2)
R_STAR = 0.1951068748    # reference methane ratio at T*


def coexistence():
    lo, hi = {}, {}
    for row in csv.DictReader(open(S8)):
        f = float(row["f"])
        lo[f] = float(row["lower end, methanogens alone"])
        up = row["upper end, acetogens alone"]
        hi[f] = float(up) if up[0].isdigit() else float("inf")
    return lo, hi


def main():
    k = SLOPE * R_STAR
    lo, hi = coexistence()
    rows = []
    for r in csv.DictReader(open(S4)):
        sigma = float(r["sigma_K"] or 0)
        if sigma <= 0 or r["chemistry"] != "fixed" or not r["S"]:
            continue
        f, P = float(r["f"]), float(r["supply_potential"])
        Q = hi[f] / lo[f]
        factor = 1.0 if Q == float("inf") else Q / (Q - 1)
        s_geo = 2 * sigma * (lo[f] / P) * factor
        pred = 1 / (1 / k + 1 / s_geo)
        rows.append(dict(f=f, d_per_yr=float(r["d_per_yr"]), P=P, sigma_K=sigma,
                         S_computed=abs(float(r["S"])), S_predicted=pred,
                         ratio=abs(float(r["S"])) / pred))
    weak = [x["ratio"] for x in rows if x["d_per_yr"] <= 1e-3]
    summary = dict(k_K_per_efold=k, n_states=len(rows), n_weak_mixing=len(weak),
                   weak_ratio_min=min(weak), weak_ratio_max=max(weak),
                   all_ratio_min=min(x["ratio"] for x in rows),
                   all_ratio_max=max(x["ratio"] for x in rows))
    OUT.write_text(json.dumps(dict(summary=summary, rows=rows), indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
