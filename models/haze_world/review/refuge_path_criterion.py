"""Path-extreme refuge criterion against Codex's refuge runs (Claude review, 10 Nov 2026).

uv run python models/haze_world/review/refuge_path_criterion.py

The pre-registered P1 used each invasion's starting temperature. Here the refuge counts
as protective only if it stays on the loser's side of T_sw along the whole recorded path:
the cold patch's path maximum below T_sw (M into A), or the warm patch's path minimum
above it (A into M). A loser is "lost" when it was culled in both patches; "survived"
includes runs censored by a physiological domain exit.
"""

import csv
import json
from pathlib import Path

T_SW = 281.534823
FIG = Path(__file__).resolve().parents[1] / "figures/refuge_coupling"


def classify(row):
    if row["direction"] == "M_into_A":
        loser, key = "a", "path_max_temperature_cold_k"
        margin = T_SW - float(row[key])
    else:
        loser, key = "m", "path_min_temperature_warm_k"
        margin = float(row[key]) - T_SW
    lost = all(row[f"first_cull_{p}_{loser}_yr"] != "" for p in ("cold", "warm"))
    return dict(case_id=row["case_id"], direction=row["direction"], fraction=row["fraction"],
                contrast_k=row["contrast_k"], dispersal_yr=row["dispersal_yr"], status=row["attempt_status"],
                margin_k=round(margin, 3), protected=margin > 0, lost=lost)


def main():
    rows = []
    for name in ("selected_main.csv", "selected_subsets.csv"):
        with (FIG / name).open() as handle:
            for r in csv.DictReader(handle):
                if r["attempt_status"] != "no_supported_conditional_start_found" and float(r["contrast_k"]) > 0:
                    rows.append(dict(source=name, **classify(r)))
    table = {}
    for r in rows:
        key = f"{r['direction']}|{'protected' if r['protected'] else 'unprotected'}|{'lost' if r['lost'] else 'survived'}"
        table[key] = table.get(key, 0) + 1
    exceptions = [r for r in rows if r["protected"] == r["lost"]]
    out = dict(t_switch_k=T_SW, counts=table,
               protected_but_lost=[r for r in exceptions if r["protected"]],
               unprotected_survivors=[r for r in exceptions if not r["protected"]])
    path = Path(__file__).with_suffix(".json")
    path.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(dict(counts=table, n_protected_lost=len(out["protected_but_lost"])), indent=1))
    for r in out["unprotected_survivors"]:
        print(r)


if __name__ == "__main__":
    main()
