"""Bounded Radau checks using independent local log-biomass coordinates.

uv run python models/haze_world/review/check_buffered_trajectory.py

The stated invader inoculum is retained. No censuses, clipping, auxiliary
numerical seeds or production coordinate helpers enter the independent solve.
"""

from dataclasses import asdict
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import platform

import numpy as np
from scipy.integrate import solve_ivp

from terra_prisca.haze_world import buffered_experiments as experiments
from terra_prisca.haze_world import habitat_coupling as model
from terra_prisca.haze_world import habitat_equilibria as equilibria
from terra_prisca.haze_world import habitat_integration as production
from terra_prisca.haze_world import population_coupling as source

ROOT=Path(__file__).resolve().parents[3]
YEARS=10.
BIOMASS=np.array([1,2,5,6,9,10])
TOLERANCES=dict(max_scaled_endpoint_difference=1e-4,max_log_biomass_difference=1e-3,
                max_instantaneous_redox_residual_mol_l_yr=1e-12,
                max_integrated_redox_error_mol_l=1e-9)


def source_hashes():
    names=("buffered_experiments.py","habitat_coupling.py","habitat_equilibria.py","habitat_integration.py",
           "population_coupling.py","two_guilds.py","hydrogen_uptake.py","woodii1998.py",
           "methane_budget.py","darwinian.py")
    paths=[Path(__file__),*[ROOT/'src/terra_prisca/haze_world'/name for name in names],
        *[ROOT/name for name in ("src/terra_prisca/haze_response/arney2016.py",
            "models/haze_response/arney2016/cases.csv","models/haze_response/arney2016/figure4.csv",
            "models/haze_world/evidence/peters1998_chemostat.csv",
            "models/haze_world/evidence/kotsyurbenko2001_table2.csv","uv.lock")]]
    return {str(path.relative_to(ROOT)):sha256(path.read_bytes()).hexdigest() for path in paths}


def decode(internal):
    physical=np.asarray(internal[:13],dtype=float).copy()
    physical[BIOMASS]=np.exp(physical[BIOMASS])
    return physical


def external_inventory_rate(y,p):
    f=model.fluxes(y,p)
    total=4*(f['abiotic_ratio_yr']-f['methane_loss_ratio_yr'])/source.inventory_to_ratio(p.base)
    for w,local in zip(p.weights,f['local']):
        if w:
            total+=w*(local['supply_h2_mol_l_yr']-local['outlet_h2_mol_l_yr']-
                      4*local['acetate_export_mol_l_yr']-sum(local['biomass_export_h2_mol_l_yr']))
    return float(total)


def initial_state(case,p):
    resident=1 if case.direction=='A_into_M' else 0
    candidates=equilibria.conditional_states(p,resident)
    qualifying=[e for e in candidates if e['stability']=='stable' and
                all(e['y'][4*j+1+resident]>0 for j,w in enumerate(p.weights) if w)]
    if not qualifying:
        raise RuntimeError(f'No supported stable conditional start: {case.case_id}')
    selected=max(qualifying,key=lambda e:e['r'])
    initial=experiments.seed_state(selected['y'],p,case.direction)
    return initial,dict(selected_ratio=selected['r'],qualifying_ratios=[e['r'] for e in qualifying],
                        protocol='Highest-r stable conditional resident; invader1e-12gDW/L in every active habitat')


def check_case(case):
    p=experiments.parameters(case)
    initial,start=initial_state(case,p)
    internal=np.r_[initial,0.]
    internal[BIOMASS]=np.log(initial[BIOMASS])

    def derivative(_,z):
        physical=decode(z)
        rates=model.rhs(physical,p)
        rates[BIOMASS]/=physical[BIOMASS]
        return np.r_[rates,external_inventory_rate(physical,p)]

    independent=solve_ivp(derivative,(0.,YEARS),internal,method='Radau',rtol=2e-10,
        atol=[1e-9,1e-10,1e-10,1e-20]*3+[1e-13,1e-13],first_step=1e-6,max_step=.05)
    if not independent.success:
        raise RuntimeError(f'Independent Radau failure: {case.case_id}: {independent.message}')
    physical=np.column_stack([decode(z) for z in independent.y.T])
    if np.any(~np.isfinite(physical)) or np.any(physical<0):
        raise RuntimeError(f'Independent Radau accepted nonphysical stocks: {case.case_id}')
    if any('unsupported' in model.temperature_flags(y,p) for y in physical.T):
        raise RuntimeError(f'Independent Radau left supported physiology: {case.case_id}')
    result=production.integrate(initial,p,YEARS,census=None)
    if not result.success or result.status!='completed':
        raise RuntimeError(f'Production continuum failure: {case.case_id}: {result.status}')
    if np.any(~np.isfinite(result.y)) or np.any(result.y<0):
        raise RuntimeError(f'Production accepted nonphysical stocks: {case.case_id}')
    before,after=physical[:,-1],result.y[:,-1]
    scales=np.maximum(np.maximum(abs(initial),abs(before)),[10.,1e-12,1e-12,1e-10]*3+[.01])
    differences=abs(after-before)
    scaled=float(max(differences/scales))
    log_difference=abs(result.log_biomass[:,:,-1].ravel()-independent.y[BIOMASS,-1])
    maximum_redox=float(max(abs(model.redox_residual(y,p)) for y in physical.T))
    inventory_change=model.inventory(before,p)-model.inventory(initial,p)
    integrated_error=float(abs(inventory_change-independent.y[13,-1]))
    assert scaled<TOLERANCES['max_scaled_endpoint_difference'],(case.case_id,scaled)
    assert max(log_difference)<TOLERANCES['max_log_biomass_difference'],(case.case_id,log_difference)
    assert maximum_redox<TOLERANCES['max_instantaneous_redox_residual_mol_l_yr']
    assert integrated_error<TOLERANCES['max_integrated_redox_error_mol_l']
    return dict(case=asdict(case),parameters=asdict(p),initial_y=initial.tolist(),start=start,
        independent_method='Radau; six independent local log biomasses, physical pressure/acetate/methane and external-redox observer',
        independent_rtol=2e-10,independent_max_step_yr=.05,independent_first_step_yr=1e-6,
        independent_nfev=independent.nfev,independent_njev=independent.njev,independent_nlu=independent.nlu,
        production_nfev=result.metadata['nfev'],production_accepted_steps=result.metadata['accepted_steps'],
        independent_final_y=before.tolist(),production_final_y=after.tolist(),
        absolute_endpoint_difference=differences.tolist(),endpoint_scales=scales.tolist(),
        max_scaled_endpoint_difference=scaled,log_biomass_difference=log_difference.tolist(),
        max_log_biomass_difference=float(max(log_difference)),nonnegative_accepted_physical_stocks=True,
        strictly_positive_accepted_biomasses=True,supported_sampled_physiology=True,
        maximum_instantaneous_redox_residual_mol_l_yr=maximum_redox,
        integrated_external_inventory_mol_l=float(independent.y[13,-1]),physical_inventory_change_mol_l=float(inventory_change),
        integrated_redox_error_mol_l=integrated_error)


def main():
    before=source_hashes()
    cases=[experiments.Case('radau_default',.5,'both',.001,'A_into_M',years=YEARS),
           experiments.Case('radau_tiny_exchange',.5,'both',1e-9,'M_into_A',years=YEARS),
           experiments.Case('radau_products',.5,'both',1e-6,'A_into_M',activity='products',years=YEARS)]
    outputs=[check_case(case) for case in cases]
    if source_hashes()!=before:
        raise RuntimeError('Inputs changed during the bounded check; rerun after source freeze')
    report=dict(duration_yr=YEARS,census='none; ten-year uncensored prefix before any scheduled intervention',
        cases=outputs,tolerances=TOLERANCES,source_sha256=before,
        environment=dict(python=platform.python_version(),numpy=importlib.metadata.version('numpy'),scipy=importlib.metadata.version('scipy')),
        scope='Independent numerical method and coordinates for three bounded continuum prefixes; shares physical RHS and start construction; not empirical validation or long-time/full-grid qualification')
    Path(__file__).with_name('buffered_trajectory_check.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps([dict(case=o['case']['case_id'],max_scaled_endpoint_difference=o['max_scaled_endpoint_difference'],
        max_log_biomass_difference=o['max_log_biomass_difference'],integrated_redox_error_mol_l=o['integrated_redox_error_mol_l']) for o in outputs],indent=2))


if __name__=='__main__':main()
