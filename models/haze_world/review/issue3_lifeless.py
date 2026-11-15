"""Issue 3 check 2: lifeless start in one uniform habitat, both groups rare.

Donor-only hydrogen, abiotic methane, no acetate, both groups at the
invasion dose (1e-12 g dry weight per litre), fixed products, tau = 0,
f = 0, 0.5, 0.9, 100 kyr. Uses the plain population integrator
(`population_coupling.integrate`) with the paper's census rule applied at
every ten-year census: a group with fewer than one global cell is removed.
The censored cross-check runs 1,000 years in ten-year segments (the first
removal and the state after it); the production integrator in
`issue3_assembly.py` carries the 100-kyr census endpoint. The uncensored run
covers 100 kyr.
The uncensored run is reported alongside.

Run: uv run python models/haze_world/review/issue3_lifeless.py
"""

import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world import dynamic_transients as dt
from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world.finite_populations import CellProcess
from terra_prisca.haze_world.methane_budget import atmosphere

OUT = Path(__file__).with_suffix('.json')
T_STAR = 281.5348
YEARS = 100000.
CENSUS_YEARS = 1000.
DOSE = 1e-12
SAMPLES = np.array([0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000.])


def start(f):
    p = dt.parameters(dt.Case('lifeless', 'B3', 'fixed', f, 0.))
    abiotic = atmosphere(p.climate.case)['flux_to_ratio_per_yr'] * p.climate.abiotic_flux
    r0 = float(p.loss.inverse(abiotic))
    h0 = p.biology.atmosphere_pa + core.supply_h2(p) / p.biology.exchange_mol_l_h_pa
    return p, np.array([h0, DOSE, DOSE, 0., r0])


def cells(p):
    c = CellProcess()
    return np.log(p.habitat_l_cm2 * c.surface_cm2 / c.cell_mass_gdw)


def log10_cells(res, j, conv):
    return [float((v + conv) / np.log(10)) if np.isfinite(v) else None for v in res.log_biomass[:, j]]


def temperature(r, p):
    return float(core.temperature_k(r, p.climate))


def censored(f):
    p, y = start(f)
    conv = cells(p)
    t, removals, clipped, low = 0., [], [], [None, None]
    while t < CENSUS_YEARS:
        span = 10.
        res = core.integrate(y, p, span, np.linspace(0., span, 11))
        logs = res.log_biomass + conv
        if removals:
            low = [min(v for v in (low[i], float(np.min(logs[i]) / np.log(10))) if v is not None)
                   if y[i + 1] > 0 else None for i in range(2)]
        state = res.y[:, -1]
        clipped.append(min(state[3], 0.))
        y = np.array([state[0], *[np.exp(res.log_biomass[i, -1]) if y[i + 1] > 0 else 0. for i in range(2)],
                      max(state[3], 0.), state[4]])
        t += span
        for i in range(2):
            if y[i + 1] > 0 and logs[i, -1] < 0:
                removals.append(dict(time_yr=t, guild=('acetogen', 'methanogen')[i],
                                     log10_cells=float(logs[i, -1] / np.log(10)), temperature_k=temperature(y[4], p)))
                y[i + 1] = 0.
    return dict(fraction=f, removals=removals,
                state_at_horizon=('both' if all(y[1:3] > 0) else 'acetogen_only' if y[1] > 0
                          else 'methanogen_only' if y[2] > 0 else 'empty'),
                final_temperature_k=temperature(y[4], p), final_ratio=float(y[4]),
                survivor_min_log10_cells_after_removal=low, horizon_yr=t,
                most_negative_clipped_acetate_mol_l=float(min(clipped, default=0.)))


def uncensored(f):
    p, y = start(f)
    res = core.integrate(y, p, YEARS, SAMPLES)
    conv = cells(p)
    trace = [dict(time_yr=float(t), temperature_k=temperature(res.y[4][j], p), ratio=float(res.y[4][j]),
                  log10_cells=log10_cells(res, j, conv)) for j, t in enumerate(SAMPLES)]
    return dict(initial_temperature_k=trace[0]['temperature_k'], initial_hydrogen_pa=float(y[0]),
                initial_ratio=float(y[4]), trace=trace)


def main():
    rows = []
    for f in (0., .5, .9):
        row = censored(f)
        row['uncensored'] = uncensored(f)
        rows.append(row)
        print(f, row['state_at_horizon'], round(row['final_temperature_k'], 3), row['removals'],
              row['survivor_min_log10_cells_after_removal'])
    OUT.write_text(json.dumps(rows, indent=1) + '\n')


if __name__ == '__main__':
    main()
