"""Claude's habitat-resolution check of Stage B1 (fixed chemistry, f=.5, sigma=1 K).

Recomputes the equal-weight midpoint habitat equilibrium from the homogeneous
homotopy at each N and dispersal rate, then the critical thermal lag, the raw
supply slope and the width of the locally mixed zone. Uses the production
Stage-B core; it tests resolution, not the core's algebra.

    uv run python models/haze_world/review/check_habitat_resolution.py \
        --output models/haze_world/review/habitat_resolution_check.json
"""

import argparse
import json
import time
from dataclasses import replace

import numpy as np

from terra_prisca.haze_world import dynamic_core as m
from terra_prisca.haze_world import dynamic_realisation as d

DEFAULT = {1e-3: (9, 17, 33, 65, 97, 129, 193, 257),
           1e-2: (9, 17, 33, 65, 129, 257),
           1e-1: (9, 17, 33, 65, 129)}


def case(dispersal, n, chemistry="fixed", fraction=.5, sigma=1.):
    p = replace(d.parameters(chemistry, fraction, .001, .30, sigma, n), dispersal_yr=dispersal)
    start = time.time()
    rows = []
    for e in (s for s in m.equilibrium_states(p) if s["kind"] == "mixed"):
        y = e["y"]
        spec = d.lag_spectrum(d.thermal_builder(y, p))
        slope = m.implicit_response(y, p)["dtemperature_dlog_supply"]
        stocks = y[:-1].reshape(n, 4)
        share = stocks[:, 1]/(stocks[:, 1]+stocks[:, 2])
        mixed = (share > .01) & (share < .99)
        rows.append(dict(dispersal_yr=dispersal, n=n, temperature_k=m.temperature(y[-1], p),
                         critical_lag_status=spec["critical_lag_status"],
                         critical_lag_yr=spec["critical_lag_yr"],
                         leading_real_tau0_yr=spec["lambda_real_tau_0"],
                         dT_dlog_supply_k=slope, mixed_habitats=int(mixed.sum()),
                         mixed_zone_width_k=float(mixed.sum()*2*sigma/n),
                         seconds=round(time.time()-start, 1)))
    return rows or [dict(dispersal_yr=dispersal, n=n, status="no_mixed_state_found")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--dispersal", type=float)
    parser.add_argument("--n", help="comma-separated habitat counts")
    args = parser.parse_args()
    plan = DEFAULT if args.dispersal is None else {args.dispersal: tuple(int(x) for x in args.n.split(","))}
    rows = []
    for dispersal, counts in plan.items():
        for n in counts:
            for row in case(dispersal, n):
                rows.append(row)
                print(json.dumps(row), flush=True)
    with open(args.output, "w") as fh:
        json.dump(dict(setting="fixed chemistry, f=0.5, L=1e-3/h, supply 0.30, sigma=1 K, equal-weight midpoint habitats",
                       rows=rows), fh, indent=1)


if __name__ == "__main__":
    main()
