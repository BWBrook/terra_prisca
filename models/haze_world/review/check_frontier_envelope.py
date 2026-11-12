"""Claude's descriptive envelope of resolved C0/C1 states: residual sensitivity versus delay margin.

    uv run python models/haze_world/review/check_frontier_envelope.py \
        --output models/haze_world/review/frontier_envelope_check.json
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[3]
FIG = ROOT/"models/haze_world/figures/continuum_habitats"
CENSOR = 1e4


def load():
    rows = []
    for name, stage in (("c0_local_gain.csv", "C0"), ("c1_resolved.csv", "C1")):
        for r in csv.DictReader(open(FIG/name)):
            if r["gain_status"] != "defined":
                continue
            status = r["critical_lag_status"]
            tau = float(r["critical_lag_yr"]) if status == "finite_crossing" else CENSOR if status.startswith("not_detected") else 0.
            rows.append(dict(stage=stage, chemistry=r["chemistry"], fraction=float(r["fraction"]),
                             sigma_k=float(r["sigma_k"]), dispersal_yr=r.get("dispersal_yr") or None,
                             loss_h=r.get("loss_h") or None, potential=float(r["nominal_potential"]),
                             Sc=float(r["Sc"]), S0=float(r["S0"]), G_loc=float(r["G_loc"]),
                             status=status, tau_yr=tau))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = load()
    pinned = [r for r in rows if abs(r["Sc"]) < 1e-6]
    graded = [r for r in rows if abs(r["Sc"]) >= 1e-6]
    reversed_open_loop = [r for r in graded if r["S0"] > 0]
    ordinary = [r for r in graded if r["S0"] < 0]
    finite_spatial = [r for r in ordinary if r["stage"] == "C1" and r["status"] == "finite_crossing"]
    rho = spearmanr([abs(r["Sc"]) for r in finite_spatial], [r["tau_yr"] for r in finite_spatial])
    logs = np.polyfit(np.log([abs(r["Sc"]) for r in finite_spatial]), np.log([r["tau_yr"] for r in finite_spatial]), 1)
    result = dict(
        states=len(rows),
        exact_pinning=dict(count=len(pinned), max_abs_Sc_k=max(abs(r["Sc"]) for r in pinned),
                           max_tau_yr=max(r["tau_yr"] for r in pinned),
                           statuses=sorted({r["status"] for r in pinned})),
        graded_ordinary=dict(count=len(ordinary), min_abs_Sc_k=min(abs(r["Sc"]) for r in ordinary),
                             min_tau_yr=min(r["tau_yr"] for r in ordinary),
                             censored=sum(r["status"].startswith("not_detected") for r in ordinary)),
        graded_reversed_open_loop=[{k: r[k] for k in ("chemistry", "fraction", "loss_h", "potential", "Sc", "S0", "status")}
                                   for r in reversed_open_loop],
        finite_spatial=dict(count=len(finite_spatial),
                            points=sorted((round(abs(r["Sc"]), 4), round(r["tau_yr"], 2), round(abs(r["G_loc"]), 4)) for r in finite_spatial),
                            spearman_abs_Sc_tau=float(rho.statistic), spearman_p=float(rho.pvalue),
                            loglog_slope=float(logs[0])),
        note="Descriptive envelope of existing resolved states; not a prespecified test.")
    Path(args.output).write_text(json.dumps(result, indent=1))
    print(json.dumps({k: v for k, v in result.items() if k != "graded_reversed_open_loop"}, indent=1))


if __name__ == "__main__":
    main()
