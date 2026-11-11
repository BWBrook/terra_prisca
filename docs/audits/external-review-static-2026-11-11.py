"""Independent bounded checks of X4–X8, X13–X17; never overwrites review evidence."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import csv
import json

import numpy as np
from scipy.optimize import brentq
from scipy.integrate import solve_ivp
from scipy.special import logsumexp

from terra_prisca.haze_world import population_coupling as pc, two_guilds as tg
from terra_prisca.haze_world import hydrogen_uptake as hu

ROOT = Path(__file__).resolve().parents[2]


def crossing(config, losses=None):
    la, lm = losses or (config.loss_h, config.loss_h)
    def difference(t):
        a, m = tg.guilds(float(t - 273.15), config)
        return a.rstar(la) - m.rstar(lm)
    grid = np.unique(np.r_[np.linspace(273., 303.15, 605),
                              np.asarray(tg.TEMPERATURES_C) + 273.15])
    values = [difference(t) for t in grid]
    out = []
    for lo, hi, flo, fhi in zip(grid[:-1], grid[1:], values[:-1], values[1:]):
        if np.isfinite(flo) and np.isfinite(fhi) and flo * fhi < 0:
            t = brentq(difference, lo, hi, xtol=1e-11)
            if abs(difference(t)) < 1e-6:
                out.append(dict(temperature_k=float(t),
                                slope_pa_k=float((difference(t + 1e-4) - difference(t - 1e-4)) / 2e-4)))
    return out


def supply_limits(base, temperature):
    a, m = tg.guilds(temperature - 273.15, base.biology)
    pressure = a.rstar(base.biology.loss_h)
    frame = list(csv.DictReader((ROOT / 'models/haze_response/arney2016/figure4.csv').open()))
    curve = [r for r in frame if r['case'] == 'B'][2:8]
    t = np.array([float(r['temperature_k']) for r in curve])
    r = np.array([float(r['ch4_co2_ratio']) for r in curve])
    ratio = float(np.interp(temperature, t[::-1], r[::-1]))
    abiotic = pc.atmosphere(base.climate.case)['flux_to_ratio_per_yr'] * base.climate.abiotic_flux
    methane = float((base.loss.rate(ratio)-abiotic) / pc.inventory_to_ratio(base) / pc.HOURS_PER_YEAR)
    outlet = base.biology.exchange_mol_l_h_pa * (pressure - base.biology.atmosphere_pa)
    eta = [1 - g.assimilation_mol_g * base.biology.loss_h / float(g.uptake(pressure)) for g in (a, m)]
    scale = .3 / pc.supply_h2(base)
    lower = (outlet + 4 * methane / eta[1]) * scale
    rows = []
    for f in (0., .5, .9, .95, .98, 1.):
        upper = (outlet + 4 * methane / (f * eta[0])) * scale if f else None
        rows.append(dict(f=f, lower_potential=lower, upper_potential=upper,
                         endpoint_ratio=upper / lower if upper else None,
                         ideal_no_assimilation_no_outlet_ratio=1/f if f else None))
    return dict(temperature_k=temperature, ratio=ratio, eta_a=eta[0], eta_m=eta[1],
                abiotic_ratio_yr=abiotic,
                outlet_h2=outlet, rows=rows)


def demographics():
    path = ROOT / 'models/haze_world/figures/bottleneck/main_0010_environment.npz'
    data = np.load(path)
    times, birth, death, migration, logs = [data[k] for k in ('times', 'birth', 'death', 'migration', 'log_counts')]
    minimum = np.exp(logsumexp(logs, axis=1).min())
    rows = []
    for extra in (0., 8.766, 87.66):
        # Backward survival in ordinary probability, independent of branching.py.
        def ode(time, u):
            b = np.array([np.interp(time, times, birth[:, j]) for j in range(birth.shape[1])]) + extra
            d = np.array([np.interp(time, times, death[:, j]) for j in range(death.shape[1])]) + extra
            return b*u*u - (b-d)*u + migration.sum(axis=1)*u - migration@u
        sol = solve_ivp(ode, (times[-1], times[0]), np.ones(birth.shape[1]),
                        method='DOP853', rtol=1e-10, atol=1e-24, max_step=.25)
        if not sol.success or np.any(sol.y[:, -1] <= 0):
            raise ArithmeticError('Independent survival integration failed')
        log_lambda = logsumexp(logs[0] + np.log(sol.y[:, -1]))
        rows.append(dict(extra_balanced_birth_death_yr=extra,
                         half_survival_minimum_cells=float(minimum * np.log(2) * np.exp(-log_lambda))))
    return rows


def assay_noise(config, draws=1024):
    rng = np.random.default_rng(1192026)
    tables = [hu.parameters(t, strain) for strain in (hu.ACETOGEN, hu.MSB) for t in tg.TEMPERATURES_C]
    temperatures = np.asarray(tg.TEMPERATURES_C)
    roots = []
    missing = 0
    for _ in range(draws):
        v = np.array([max(rng.normal(r.vmax_nmol_h, r.vmax_ci/1.96), 1.) for r in tables]).reshape(2, -1)
        k = np.array([max(rng.normal(r.km_pa, r.km_ci/1.96), 1.) for r in tables]).reshape(2, -1)
        def difference(tc):
            pair = tg.guilds(float(tc), config)
            values = []
            for i, g in enumerate(pair):
                original_relative = tg.shape(float(tc), (hu.ACETOGEN, hu.MSB)[i], config.low_temperature_variant)[0]
                capacity = g.rate_scale / original_relative * np.interp(tc, temperatures, v[i]) / v[i, -1]
                required = g.maintenance + config.loss_h / g.yield_g_mol
                values.append(g.threshold_pa + np.interp(tc, temperatures, k[i])*required/(capacity-required)
                              if capacity > required else np.inf)
            return values[0]-values[1]
        # The reference crossing lies on the measured 4–15 C intervals.
        grid = np.linspace(4., 30., 105)
        vals = [difference(t) for t in grid]
        found = [brentq(difference, lo, hi) + 273.15 for lo, hi, a, b in
                 zip(grid[:-1], grid[1:], vals[:-1], vals[1:])
                 if np.isfinite(a) and np.isfinite(b) and a*b < 0]
        if found:
            roots.append(found[-1])
        else:
            missing += 1
    return dict(draws=draws, missing=missing, sd_k=float(np.std(roots)),
                quantiles_2_5_50_97_5_k=np.percentile(roots, [2.5, 50, 97.5]).tolist(),
                assumption='Independent Gaussian V and K errors with published 95-percent halfwidth divided by 1.96; independent assay errors and their correlations are not measured.')


def main():
    ref = pc.reference()
    base = ref.biology
    rows = []
    for c in tg.parameter_grid(hu.MSB):
        config = replace(base, capacity_ratio=c.capacity_ratio, yield_m=c.yield_m,
                         maintenance_m30=c.maintenance_m30, loss_h=c.loss_h,
                         threshold_a30=c.threshold_a30)
        roots = crossing(config)
        warm = all(tg.guilds(t, config)[1].rstar(config.loss_h) < tg.guilds(t, config)[0].rstar(config.loss_h) for t in (20., 30.))
        good = any(273.39 < r['temperature_k'] < 297.008 and r['slope_pa_k'] > 0 for r in roots)
        old = pc.switch_temperatures(config)
        old_good = any(273.39 < t < 297.008 for t in old)
        rows.append(dict(on_cooling_branch=good, warm_m=warm, roots=roots,
                         root_pressures_pa=[float(tg.guilds(r['temperature_k']-273.15, config)[0].rstar(config.loss_h)) for r in roots],
                         config=dict(capacity_ratio=c.capacity_ratio, yield_m=c.yield_m,
                         maintenance_m30=c.maintenance_m30, loss_h=c.loss_h,
                         threshold_a30=c.threshold_a30),
                         production_roots=list(old), production_good=old_good))
    central = crossing(base)[0]['temperature_k']
    carbon_factors = ((12000/1800)**.5, (12000/1800)**.25)
    report = dict(
        scope='Bounded checks of published reviewer examples; grid counts are not probabilities; no Stage B or C full build.',
        grid=dict(total=len(rows), restoring_on_branch=sum(r['on_cooling_branch'] for r in rows),
                  warm_m=sum(r['warm_m'] for r in rows), warm_m_restoring=sum(r['warm_m'] and r['on_cooling_branch'] for r in rows),
                  differing_classifications=[r for r in rows if r['on_cooling_branch'] != r['production_good']]),
        reference=crossing(base), rounded_dry_mass=crossing(replace(base, capacity_ratio=.38)),
        exact_dry_mass_ratio=(560/7)/(760/3.6),
        exact_dry_mass=crossing(replace(base, capacity_ratio=(560/7)/(760/3.6))),
        msp=crossing(replace(base, methanogen=hu.MSP)),
        unequal_loss=[dict(m_loss_h=lm, roots=crossing(base, (.001, lm))) for lm in (.0005, .00075, .001, .00125, .002)],
        co2_factors=carbon_factors,
        co2_diagnostic=crossing(replace(base, threshold_a30=base.threshold_a30*carbon_factors[0], threshold_m30=base.threshold_m30*carbon_factors[1])),
        supply_band=supply_limits(ref, central),
        donor_h2_molecules_cm2_s=4*ref.climate.donor_flux,
        atmosphere_pa=base.atmosphere_pa,
        demographics=demographics(),
        assay_noise=assay_noise(base),
        bank_half_life_fraction=[dict(entry_to_survivor_ratio=r, fraction=float(np.log(2)/np.log(r))) for r in (1e6, 1e12, float(np.exp(54.3492)))],
    )
    climate = list(csv.DictReader((ROOT / 'models/haze_response/arney2016/figure4.csv').open()))
    b = [r for r in climate if r['case'] == 'B']
    report['climate_geometry'] = dict(cooling_vertices=len(b[2:8]), cooling_segments=len(b[2:8])-1,
        local_slope_k_per_ratio=(float(b[5]['temperature_k'])-float(b[4]['temperature_k']))/(float(b[5]['ch4_co2_ratio'])-float(b[4]['ch4_co2_ratio'])))
    paths = ['src/terra_prisca/haze_world/two_guilds.py', 'src/terra_prisca/haze_world/population_coupling.py',
             'models/haze_response/arney2016/figure4.csv', 'models/haze_world/figures/bottleneck/main_0010_environment.npz',
             'docs/audits/external-review-static-2026-11-11.py']
    report['sha256'] = {p: sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    Path(__file__).with_suffix('.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'sha256'}, indent=2))


if __name__ == '__main__':
    main()
