"""Short independent cell-process controls; no long tails or parameter fitting.

uv run python models/haze_world/review/finite_process_check.py
"""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
from scipy.integrate import solve_ivp

from terra_prisca.haze_world import finite_populations as finite
from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world.finite_experiments import Case, parameters, initial_state


def toy_run(initial_cells, immigration, minimum, years, *, area=5.1e18, stride=1, growth=(0.,0.)):
    p=replace(core.reference(),activity_feedback='products')
    process=finite.CellProcess(minimum_cells=minimum,census_yr=1.,immigration_cells_yr=immigration,surface_cm2=area)
    volume=p.habitat_l_cm2*area;cell_mass=process.cell_mass_gdw
    y=np.array([23.,initial_cells[0]*cell_mass/volume,initial_cells[1]*cell_mass/volume,.001,.195])
    def rhs(state,params):return np.array([0.,growth[0]*state[1],growth[1]*state[2],0.,0.])
    with patch.object(core,'rhs',rhs),patch.object(core,'fluxes',lambda state,params:dict(net_growth_yr=np.array(growth))):
        result=finite.integrate_finite(y,p,years,process,sample_every_censuses=stride)
    cells=result.y[1:3]*volume/cell_mass
    remaining_gdw=result.y[1:3,-1]*volume
    expected_gdw=np.array(initial_cells)*cell_mass+result.ledger['immigrant_gdw']-result.ledger['culled_gdw']
    if growth==(0.,0.):
        scale=np.maximum(np.array(initial_cells)*cell_mass+result.ledger['immigrant_gdw'],cell_mass)
        relative_ledger_error=float(np.max(np.abs(remaining_gdw-expected_gdw)/scale))
        assert relative_ledger_error<3e-6
        result.metadata['independent_relative_ledger_error']=relative_ledger_error
    allocation=np.array([g.assimilation_mol_g for g in core.activity_guilds(y,p)])
    assert np.allclose(result.ledger['immigrant_h2_mol'],result.ledger['immigrant_gdw']*allocation)
    assert np.allclose(result.ledger['culled_h2_mol'],result.ledger['culled_gdw']*allocation)
    return result,cells


def main():
    out={}
    r,n=toy_run((0.,0.),(0.,0.),0.,2.5,growth=(10.,10.))
    assert np.all(r.y[1:3]==0) and not r.extinction_events and not r.arrival_events
    out['exact_absence_no_immigration']=dict(final_cells=n[:,-1].tolist(),events=len(r.extinction_events))
    r,n=toy_run((0.,0.),(2.,0.),0.,2.5)
    assert np.isclose(n[0,-1],5.,rtol=2e-6) and np.all(n[1]==0)
    assert not r.extinction_events and r.arrival_events[0]['time_yr']==1.
    out['rare_zero_initial_immigration']=dict(final_cells=n[:,-1].tolist(),times=r.t.tolist(),
        first_retained_census_yr=r.arrival_events[0]['time_yr'],census_flags=r.census_activity.tolist())
    r,n=toy_run((0.,0.),(2.,0.),5.,2.5,stride=2)
    assert np.isclose(n[0,-1],1.,rtol=2e-6)
    assert np.allclose(r.ledger['culled_cells'],[4.,0.],rtol=2e-6)
    assert [e['time_yr'] for e in r.extinction_events]==[1.,2.]
    assert not r.arrival_events and np.all(r.census_activity==0)
    assert r.t.tolist()==[0.,2.,2.5] and r.metadata['n_censuses']==3
    out['immigration_and_repeated_culls']=dict(final_cells=n[:,-1].tolist(),times=r.t.tolist(),
        removal_times=[e['time_yr'] for e in r.extinction_events],first_extinction_field=r.first_extinction_yr,
        immigrant_cells=r.ledger['immigrant_cells'].tolist(),culled_cells=r.ledger['culled_cells'].tolist(),
        census_flags=r.census_activity.tolist(),last_census_yr=r.metadata['last_census_yr'],
        relative_global_mass_ledger_error=r.metadata['independent_relative_ledger_error'])
    r,n=toy_run((.5,0.),(0.,0.),1.,0.)
    assert n[0,-1]==0 and r.first_extinction_yr==0 and len(r.extinction_events)==1
    out['initial_census_removal']=dict(removed_cells=r.ledger['culled_cells'].tolist(),
        first_extinction_yr=r.first_extinction_yr,min_cells_field=r.min_cells.tolist())
    r,n=toy_run((0.,0.),(1e8,0.),0.,2.5,area=1.)
    assert np.isclose(n[0,-1],2.5e8,rtol=2e-6)
    out['dense_scaled_linear_boundary']=dict(final_cells=n[:,-1].tolist())
    p=replace(core.reference(),activity_feedback='products')
    y=next(e['y'] for e in core.equilibrium_states(p) if e['kind']=='mixed').copy()
    y*=np.array([1.01,.99,1.01,1.01,1.0001])
    proc=finite.CellProcess(minimum_cells=0,census_yr=.25)
    r=finite.integrate_finite(y,p,2.,proc,sample_every_censuses=1)
    control=core.integrate(y,p,2.,sample_times=r.t)
    error=float(np.max(np.abs(r.y-control.y)/np.maximum(np.abs(control.y),1e-12)))
    assert error<3e-5 and not r.extinction_events and r.metadata['solver_resets']==0
    out['Nmin_zero_continuum_control']=dict(maximum_relative_state_difference=error,
        duration_yr=2.,solver_resets=r.metadata['solver_resets'])
    case=Case('independent_first_census_0123','products',.9,1.,.1,'M_into_A',years=10.)
    p,proc=parameters(case);y0=initial_state(case)
    run=finite.integrate_finite(y0,p,10.,proc,sample_every_censuses=1)
    volume=p.habitat_l_cm2*proc.surface_cm2
    immigration=np.array(proc.immigration_cells_yr)*proc.cell_mass_gdw/volume
    initial=y0.copy();initial[1:3]/=immigration
    def independent_rhs(t,state):
        physical=state.copy();physical[1:3]*=immigration
        rates=core.rhs(physical,p)
        rates[1:3]=core.fluxes(physical,p)['net_growth_yr']*state[1:3]+1.
        return rates
    reference=solve_ivp(independent_rhs,(0.,10.),initial,method='Radau',rtol=2e-9,
        atol=[1e-8,1e-9,1e-9,1e-12,1e-12])
    assert reference.success
    expected=reference.y[:,-1].copy();expected[1:3]*=immigration
    pre_census=expected[1:3]*volume/proc.cell_mass_gdw
    expected[1:3][pre_census<proc.minimum_cells]=0.
    metric=np.maximum(np.abs(expected),[1.,1e-25,1e-25,1e-9,.001])
    error=float(np.max(np.abs(run.y[:,-1]-expected)/metric))
    population_error=np.abs(run.y[1:3,-1]-expected[1:3])/expected[1:3]
    assert error<3e-5 and np.max(population_error)<1e-4
    out['case0123_first_census_comparison']=dict(duration_yr=10.,
        maximum_relative_or_scaled_state_difference=error,independent_pre_census_cells=pre_census.tolist(),
        relative_population_differences=population_error.tolist(),
        lsoda_final_cells=(run.y[1:3,-1]*volume/proc.cell_mass_gdw).tolist(),
        removal_times=[e['time_yr'] for e in run.extinction_events],
        final_state=run.y[:,-1].tolist(),lsoda_nfev=run.metadata['nfev'],radau_nfev=reference.nfev)
    out['scope']='Short boundary/census/ledger checks; toy controls use frozen nonpopulation states, not biological forecasts.'
    out['core_sha256']=sha256(Path(finite.__file__).read_bytes()).hexdigest()
    Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
