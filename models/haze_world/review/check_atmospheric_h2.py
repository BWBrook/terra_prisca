"""Claude's X8 check: atmospheric H2 pressure against the homogeneous reference mixture.

    uv run python models/haze_world/review/check_atmospheric_h2.py \
        --output models/haze_world/review/atmospheric_h2_check.json
"""

import argparse
import json
from dataclasses import replace

from terra_prisca.haze_world import dynamic_core as m
from terra_prisca.haze_world import dynamic_realisation as d

PRESSURES = (0., 1., 3., 10., 30., 100., 200.)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = []
    for chemistry in ("fixed", "products"):
        for fraction in (0., .5):
            for pa in PRESSURES:
                p = d.parameters(chemistry, fraction, .001, .30)
                p = replace(p, base=replace(p.base, biology=replace(p.base.biology, atmosphere_pa=pa)))
                states = m.equilibrium_states(p)
                mixed = [s for s in states if s["kind"] == "mixed"]
                if not mixed:
                    rows.append(dict(chemistry=chemistry, fraction=fraction, atmosphere_pa=pa, status="no_mixed_state",
                                     found=[dict(kind=s["kind"], temperature_k=m.temperature(s["y"][-1], p)) for s in states]))
                for s in mixed:
                    y = s["y"]
                    spec = d.lag_spectrum(d.thermal_builder(y, p))
                    rows.append(dict(chemistry=chemistry, fraction=fraction, atmosphere_pa=pa, status="mixed",
                                     temperature_k=m.temperature(y[-1], p), local_h2_pa=float(y[0]),
                                     dT_dlog_supply_k=m.implicit_response(y, p)["dtemperature_dlog_supply"],
                                     critical_lag_status=spec["critical_lag_status"],
                                     critical_lag_yr=spec["critical_lag_yr"]))
                print(json.dumps(rows[-1]), flush=True)
    with open(args.output, "w") as fh:
        json.dump(dict(setting="homogeneous, L=1e-3/h, supply 0.30; atmosphere_pa varied with fixed exchange coefficient", rows=rows), fh, indent=1)


if __name__ == "__main__":
    main()
