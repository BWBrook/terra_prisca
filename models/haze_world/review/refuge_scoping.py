"""Scoping numbers for the two-habitat refuge design (Claude review, 10 Nov 2026).

uv run python models/haze_world/review/refuge_scoping.py

1. Switch temperature T_sw (equal R*) of the reference physiology.
2. At each conditional pure-guild start: the climate relaxation time (slowest
   eigenvalue of the full Jacobian) against the competitive exclusion rate the
   invader imposes, and the ratio Pi = exclusion rate x climate time / ln(N/N_min).
   Pi >> 1 means the loser falls through any floor before climate moves.
3. The fixed-activity refuge offset: how far a habitat must sit from the global
   temperature for the losing resident to keep the lower R* there.
"""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from terra_prisca.haze_world.population_coupling import (equilibrium_states, fluxes, guilds, jacobian,
                                                         reference, switch_temperatures)

CELL_G, AREA_CM2 = 3e-13, 5.1e18


def main():
    base = reference()
    t_sw = switch_temperatures(base.biology)
    rows = []
    for f in (0., .5, .9):
        p = replace(base, acetate_fraction=f)
        for index, resident in enumerate(("acetogen", "methanogen")):
            enabled = (index == 0, index == 1)
            stable = [e for e in equilibrium_states(replace(p, enabled=enabled)) if e["kind"] == resident and e["stable"]]
            for e in stable:
                y = e["y"]
                invader = 1 - index
                growth = fluxes(y, p)["net_growth_yr"][invader]
                eig = np.linalg.eigvals(jacobian(y, replace(p, enabled=enabled))).real
                slowest = float(np.max(eig))
                cells = y[1 + index] * p.habitat_l_cm2 * AREA_CM2 / CELL_G
                t = e["t_k"]
                pair = guilds(t - 273.15, p.biology)
                rstar = [g.rstar(p.biology.loss_h) for g in pair]
                rows.append(dict(
                    acetate_fraction=f, resident=resident, t_k=round(t, 3),
                    invader_growth_yr=round(float(growth), 3),
                    rstar_resident_pa=round(float(rstar[index]), 3), rstar_invader_pa=round(float(rstar[invader]), 3),
                    climate_time_yr=round(-1 / slowest, 1), resident_cells=float(f"{cells:.3g}"),
                    pi_one_cell=round(abs(growth) * (-1 / slowest) / np.log(cells), 1) if growth > 0 else None,
                    refuge_offset_k=round(min(abs(t - s) for s in t_sw), 2) if growth > 0 else None,
                    refuge_side=("warmer" if resident == "methanogen" else "colder") if growth > 0 else None))
    out = dict(switch_temperatures_k=[round(x, 3) for x in t_sw], starts=rows,
               notes="Fixed activities. invader_growth at the resident's own state; Pi uses the invader's initial "
                     "growth as a proxy for the resident's decline rate once displaced. refuge_offset is |T_start - T_sw|.")
    path = Path(__file__).with_suffix(".json")
    path.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
