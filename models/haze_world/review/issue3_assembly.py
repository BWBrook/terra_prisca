"""Pressure-test Issue 3: can the regulating community assemble in one habitat?

Two bounded checks on the homogeneous B3 finite-census integrator
(`dynamic_transients.integrate`, one-cell ten-year census):

1. Methane response speed. The methane equation's right-hand side is
   multiplied by s, which divides the methane lifetime by s and multiplies
   every methane source by s. Steady states are unchanged; only the time
   for methane to respond shrinks. Fixed products, tau = 0, both invasion
   directions, f = 0 and 0.5, s = 1, 10, 100, 1000 (lifetimes 10 kyr to
   10 yr). s = 1 reproduces the stored C52 runs.
2. Lifeless start. Donor-only hydrogen and abiotic methane, with both groups
   introduced together at the invasion dose (1e-12 g dry weight per litre).
   Fixed products, tau = 0, f = 0, 0.5 and 0.9, 100 kyr, step limit 1 yr.
   `issue3_lifeless.py` repeats this with the plain population integrator.

Run: uv run python models/haze_world/review/issue3_assembly.py
"""

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from terra_prisca.haze_world import dynamic_transients as dt
from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world.methane_budget import atmosphere

OUT = Path(__file__).with_suffix('.json')
T_STAR = 281.5348
YEARS = 100000.
DOSE = 1e-12


class Speeded(dt.Coordinates):
    scale = 1.

    def derivative(self, t, state, temperature_k=None):
        rates = super().derivative(t, state, temperature_k)
        if self._scaling:
            rates = np.array(rates, float)
            rates[4] *= self.scale
        return rates

    _scaling = True

    def jacobian(self, t, state):
        self._scaling = False
        try:
            matrix = super().jacobian(t, state)
        finally:
            self._scaling = True
        matrix[4] *= self.scale
        return matrix


def summary(result, p):
    t, temps = result['t'], result['temperature_k']
    present = np.isfinite(result['log_biomass'][:, -1])
    cross = np.flatnonzero((temps[:-1] - T_STAR) * (temps[1:] - T_STAR) <= 0)
    conv = result['global_log_cell_conversion']
    final_cells = [float((result['log_biomass'][i, -1] + conv) / np.log(10)) if present[i] else None for i in range(2)]
    return dict(
        status=result['status'], horizon_yr=float(t[-1]),
        endpoint=('both' if all(present) else 'acetogen_only' if present[0]
                  else 'methanogen_only' if present[1] else 'empty'),
        final_temperature_k=float(temps[-1]), final_log10_cells=final_cells,
        temperature_range_k=[float(v) for v in result['temperature_range_k']],
        first_T_star_crossing_yr=float(t[cross[0] + 1]) if len(cross) else None,
        n_T_star_crossings=int(len(cross)),
        removals=result['events'],
        temperature_at_first_removal_k=(float(np.interp(result['events'][0]['time_yr'], t, temps))
                                        if result['events'] else None),
        final_window_temperature_span_k=float(np.ptp(temps[t >= .8 * t[-1]])),
        wall_seconds=result['wall_seconds'])


def speed_case(args):
    f, direction, s = args
    dt.Coordinates = type('S', (Speeded,), dict(scale=float(s)))
    case = dt.Case(f'speed_f{f:g}_{direction}_s{s:g}', 'B3', 'fixed', f, 0., direction)
    y, temp = dt.initial(case)
    p = dt.parameters(case)
    res = dt.integrate(y, p, YEARS, 0., temp, census=True)
    return dict(check='methane_speed', fraction=f, direction=direction, speed=s,
                methane_lifetime_yr=p.loss.lifetime_yr / s, initial_temperature_k=temp, **summary(res, p))


def lifeless_case(f):
    dt.Coordinates = Speeded
    case = dt.Case(f'lifeless_f{f:g}', 'B3', 'fixed', f, 0.)
    p = dt.parameters(case)
    abiotic = atmosphere(p.climate.case)['flux_to_ratio_per_yr'] * p.climate.abiotic_flux
    r0 = float(p.loss.inverse(abiotic))
    h0 = p.biology.atmosphere_pa + core.supply_h2(p) / p.biology.exchange_mol_l_h_pa
    temp = float(core.temperature_k(r0, p.climate))
    y = np.array([h0, DOSE, DOSE, 0., r0])
    fl = core.fluxes_at_temperature(y, p, temp)
    y[3] = fl['acetate_production_mol_l_yr'] / (fl['k_rec_yr'] + fl['k_other_yr'])
    out = dict(check='lifeless', fraction=f, initial_ratio=r0, initial_temperature_k=temp,
               initial_hydrogen_pa=h0, initial_acetate_mol_l=float(y[3]))
    # The default 50-yr step limit lets the acetate-source certificate fail
    # during the initial bloom; a 1-yr limit passes it.
    res = dt.integrate(y, p, YEARS, 0., temp, census=True, max_step=1.)
    out.update(summary(res, p))
    unc = dt.integrate(y, p, YEARS, 0., temp, census=False, max_step=1.)
    conv = unc['global_log_cell_conversion']
    out['uncensored'] = dict(
        status=unc['status'],
        min_log10_cells=[float((v + conv) / np.log(10)) for v in unc['min_log_biomass']],
        min_time_yr=[float(v) for v in unc['min_times_yr']],
        first_below_cell_yr=unc['first_below_cell_yr'],
        final_log10_cells=[float((v + conv) / np.log(10)) for v in unc['log_biomass'][:, -1]],
        final_temperature_k=float(unc['temperature_k'][-1]),
        final_window_temperature_span_k=float(np.ptp(unc['temperature_k'][unc['t'] >= .8 * unc['t'][-1]])))
    t, temps = res['t'], res['temperature_k']
    out['trace'] = [dict(time_yr=float(a), temperature_k=float(b),
                         log10_cells=[float((v + res['global_log_cell_conversion']) / np.log(10))
                                      if np.isfinite(v) else None for v in res['log_biomass'][:, j]])
                    for j, (a, b) in enumerate(zip(t, temps))
                    if a in (0., 1., 2., 5., 10., 20., 50., 100., 200., 500., 1000., 2000., 5000., 10000., 50000., 100000.)]
    return out


def main():
    speed = [(f, d, s) for f in (0., .5) for d in ('A_into_M', 'M_into_A') for s in (1, 10, 100, 1000)]
    part = OUT.with_name(OUT.stem + '_speed.json')
    with ProcessPoolExecutor(8) as pool:
        if part.exists():
            rows = json.loads(part.read_text())
        else:
            rows = list(pool.map(speed_case, speed))
            part.write_text(json.dumps(rows, indent=1, default=float) + '\n')
        rows += list(pool.map(lifeless_case, (0., .5, .9)))
    OUT.write_text(json.dumps(rows, indent=1, default=float) + '\n')
    part.unlink()
    for r in rows:
        print(r['check'], r['fraction'], r.get('direction', ''), r.get('speed', ''), r['endpoint'],
              round(r['final_temperature_k'], 2), r['removals'][:2], r['first_T_star_crossing_yr'],
              r.get('uncensored', {}).get('final_log10_cells'))


if __name__ == '__main__':
    main()
