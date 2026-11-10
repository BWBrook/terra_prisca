"""Bounded target-d conditional-root challenge; four configurations only.

uv run python models/haze_world/review/check_refuge_target_d.py

This directly solves pressure, per-capita growth and methane balances at d=1,
without continuing d=0 branches. Shared physiological/climate primitives and
stability evaluation remain common inputs. Finite seeds and variable bounds
provide bounded negative evidence, not an exhaustive absence proof.
"""
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.optimize import least_squares

from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world import refuge_coupling as model
from terra_prisca.haze_world import refuge_equilibria as existing
from terra_prisca.haze_world.finite_experiments import clean

ROOT = Path(__file__).resolve().parents[3]
SOURCE = [ROOT / 'src/terra_prisca/haze_world' / name for name in (
    'refuge_coupling.py', 'refuge_equilibria.py', 'population_coupling.py', 'two_guilds.py',
    'methane_budget.py')]


def source_hashes():
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in SOURCE}


def state_and_residual(z, p, resident):
    p0 = p.base.biology.atmosphere_pa + core.supply_h2(p.base)/p.base.biology.exchange_mol_l_h_pa
    y = np.zeros(9)
    y[[0,4]] = z[:2] * p0
    y[model.BIOMASS_INDICES[:,resident]] = .001 * np.exp(z[2:4])
    y[8] = z[4]
    ts = model.temperatures(y,p)
    if resident == 0:
        for j in (0,1):
            local = core.fluxes_at_temperature(model.local_state(y,j),p.base,float(ts[j]))
            y[4*j+3] = local['acetate_production_mol_l_yr']/(local['k_rec_yr']+local['k_other_yr'])
    flux = model.fluxes(y,p)
    supply = core.supply_h2(p.base)*core.HOURS_PER_YEAR
    pressure = [(f['supply_h2_mol_l_yr']-sum(f['uptake_h2_mol_l_yr'])-f['outlet_h2_mol_l_yr'])/supply for f in flux['local']]
    stocks = y[model.BIOMASS_INDICES[:,resident]]
    growth = [flux['local'][j]['net_growth_yr'][resident] + p.dispersal_yr*p.weights[1-j]*(stocks[1-j]/stocks[j]-1) for j in (0,1)]
    residual = np.r_[pressure,np.asarray(growth)/(core.HOURS_PER_YEAR*p.base.biology.loss_h),
                    (flux['methane_source_ratio_yr']-flux['methane_loss_ratio_yr'])/(core.inventory_to_ratio(p.base)*supply/4)]
    return y,residual


def solve_case(f,w,contrast,resident):
    p=model.Refuge(replace(core.reference(),acetate_fraction=f,enabled=(resident==0,resident==1)),w,contrast,1.)
    coverage=existing.search_coverage(p,201)
    before=existing.equilibrium_states(p,n_grid=201)
    qualifying=[e for e in before if e['stable'] and np.all(e['y'][model.BIOMASS_INDICES[:,resident]]>0)]
    roots=[]; fits=[]
    p0=core.supply_h2(p.base)/p.base.biology.exchange_mol_l_h_pa+p.base.biology.atmosphere_pa
    for interval in coverage['supported_ratio_intervals']:
        lo,hi=interval
        pad=max(1e-11,(hi-lo)*1e-8)
        if hi-lo<=2*pad:continue
        for position in (.2,.5,.8):
            r=lo+(hi-lo)*position
            ts=float(core.temperature_k(r,p.base.climate))+p.offsets
            pressures=[];biomass=[]
            for temperature in ts:
                guild=core.guilds(float(temperature-273.15),p.base.biology)[resident]
                pressure=float(np.clip(guild.rstar(p.base.biology.loss_h),1e-5,.99*p0))
                captured=core.supply_h2(p.base)-p.base.biology.exchange_mol_l_h_pa*(pressure-p.base.biology.atmosphere_pa)
                pressures.append(pressure/p0)
                biomass.append(max(captured/max(float(guild.uptake(pressure)),1e-12),1e-8))
            for factor in (.3,1.,3.):
                z=np.r_[pressures,np.log(np.asarray(biomass)*factor/.001),r]
                fit=least_squares(lambda q:state_and_residual(q,p,resident)[1],z,
                    bounds=([1e-10,1e-10,-80.,-80.,lo+pad],[1.,1.,10.,10.,hi-pad]),
                    jac='3-point',diff_step=1e-5,x_scale='jac',ftol=1e-12,xtol=1e-12,gtol=1e-12,max_nfev=200)
                y,residual=state_and_residual(fit.x,p,resident)
                error=float(max(abs(residual)))
                fits.append(dict(interval=interval,position=position,biomass_multiplier=factor,
                                 max_scaled_residual=error,nfev=fit.nfev,success=fit.success,
                                 active_bounds=fit.active_mask.tolist(),ratio=float(y[8])))
                if error>2e-7:continue
                if any(max(abs(y-e['y'])/np.array([100.,.001,.001,.001,100.,.001,.001,.001,.2]))<1e-6 for e in roots):continue
                row=existing.describe(y,p)
                row['direct_scaled_residual']=error
                row['matches_existing']=any(max(abs(y-e['y'])/np.array([100.,.001,.001,.001,100.,.001,.001,.001,.2]))<1e-6 for e in before)
                roots.append(row)
    return dict(parameters=asdict(p),resident='acetogen' if resident==0 else 'methanogen',coverage=coverage,
                existing_candidate_count=len(before),existing_qualifying_count=len(qualifying),
                existing_qualifying=[dict(r=e['r'],temperatures_k=e['temperatures_k'],stability=e['stability']) for e in qualifying],
                independent_fits=fits,independent_roots=roots,
                missed_supported_stable=[e for e in roots if e['stable'] and not e['matches_existing']])


def main():
    sources=source_hashes();started=perf_counter()
    cases=[]
    for values in [(0.,.5,5.,1),(0.,.5,10.,1),(0.,.1,10.,1),(.5,.5,10.,0)]:
        row=solve_case(*values);cases.append(row)
        print(values,'existing',row['existing_qualifying_count'],'directroots',len(row['independent_roots']),
              'missedstable',len(row['missed_supported_stable']),'bestresidual',min((e['max_scaled_residual'] for e in row['independent_fits']),default=None),flush=True)
    assert source_hashes()==sources,'Frozen source changed during challenge'
    output=dict(source_sha256=sources,checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),scope='Four-case bounded target-d challenge; finite seeds and bounded variables do not establish absence',
                variables='pressure in(0,p0), biomass .001*exp(logX), logX in[-80,10], ratio separately bounded within supported intervals',
                method='Direct target-d pressure balances and local per-capita growth plus exchange, with acetate eliminated algebraically',
                scientific_scope='Challenges unsupported-start classifications for three M-only geometries at d=1/year and one supported A-only positive control; uptake, climate primitives and final stability evaluator are shared with the production model. M-only steady equations also apply at f=0.5 because acetate is absent. No trajectory or full-grid inference is made.',
                completeness='Four configurations, finite generic seeds and bounded variables; no missed root found does not establish nonexistence or global completeness',
                cases=cases,wall_seconds=perf_counter()-started)
    Path(__file__).with_name('refuge_target_d_check.json').write_text(json.dumps(clean(output),indent=2,allow_nan=False)+'\n')

if __name__=='__main__':main()
