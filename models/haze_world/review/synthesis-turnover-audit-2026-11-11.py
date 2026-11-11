"""Independent recounts and algebraic checks for synthesis C12-C15/C21-C23."""
from collections import Counter
from hashlib import sha256
import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world import habitat_coupling as habitat
from terra_prisca.haze_world import turnover, turnover_experiments as experiments
from terra_prisca.haze_world import dormancy as dormancy
from terra_prisca.haze_world import dormancy_experiments as dormancy_cases
from terra_prisca.haze_world.two_guilds import guilds

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
INPUTS = {}


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def read(name):
    path = ROOT/name
    INPUTS[name] = digest(path)
    return json.loads(path.read_text())


def table(name):
    path = ROOT/name
    INPUTS[name] = digest(path)
    return list(csv.DictReader(path.open()))


def rstar_difference(temperature, loss):
    pair = guilds(temperature-273.15, core.reference().biology)
    pressures = []
    for g in pair:
        q = g.maintenance+loss/g.yield_g_mol
        if q>=g.rate_scale:return float('nan')
        pressures.append(g.threshold_pa+g.km_pa*q/(g.rate_scale-q))
    return pressures[0]-pressures[1]


def switch(loss):
    grid=np.linspace(273.,303.,601)
    pairs=[(a,b) for a,b in zip(grid[:-1],grid[1:]) if np.isfinite(rstar_difference(a,loss)) and np.isfinite(rstar_difference(b,loss)) and rstar_difference(a,loss)*rstar_difference(b,loss)<0]
    assert len(pairs)==1
    return brentq(lambda t:rstar_difference(t, loss), *pairs[0], xtol=1e-10)


def inventory():
    rows = table('models/haze_world/figures/turnover/regimes.csv')
    bounds = read('models/haze_world/figures/turnover/boundaries.json')['boundaries']
    stable = [r for r in rows if r['kind']=='mixed' and r['stable']=='True']
    origin = next(r for r in bounds if r['event']=='mixed_geometry_climate_minimum' and r.get('fraction')==0)
    acetogen = next(r for r in bounds if r['event']=='acetogen_invaded' and r.get('fraction')==0)
    end_mixed = next(r for r in bounds if r['event']=='methanogen_invaded' and r.get('fraction')==0 and r['loss_h']>.001)
    end_two = next(r for r in bounds if r['event']=='methanogen_invaded' and r.get('fraction')==0 and r['loss_h']>end_mixed['loss_h'])
    onset = brentq(lambda loss:rstar_difference(origin['temperature_k'], loss), 1e-4, 1e-3, xtol=1e-15)
    bifurcation = brentq(lambda loss:rstar_difference(acetogen['temperature_k'], loss), 1e-3, 2e-3, xtol=1e-15)
    assert abs(onset-origin['loss_h'])<1e-13
    assert abs(bifurcation-acetogen['loss_h'])<1e-13
    counterexamples = []
    for loss in (.0042, .0095):
        states = turnover.equilibria(0.,loss)
        counterexamples.append(dict(loss_h=loss,stable_kinds=[s['kind'] for s in states if s['stable']]))
    return dict(equilibria=len(rows),parameter_settings=len({r['profile_id'] for r in rows}),
        sampled_stable_mixed_temperature_range_k=[min(float(r['temperature_k']) for r in stable),max(float(r['temperature_k']) for r in stable)],
        root_delimited_branch_temperature_limits_k=[origin['temperature_k'],end_mixed['temperature_k']],
        independently_rooted_onset_loss_h=onset, independently_rooted_acetogen_stability_loss_h=bifurcation,
        acetogen_mixed_bistability_interval_loss_h=[bifurcation,end_mixed['loss_h']],
        two_pure_guild_bistability_interval_loss_h=[end_mixed['loss_h'],end_two['loss_h']],
        high_loss_counterexamples=counterexamples,
        interpretation='Root-delimited temperature limits are not the sampled grid range. Bistable above the first boundary is not an unbounded-in-loss theorem.')


def refuge_checks():
    rows=table('models/haze_world/figures/turnover/refuges.csv')
    endpoints=read('models/haze_world/figures/turnover/endpoint_assessment.json')['endpoint_states']
    details={r['case_id']:r for r in endpoints}
    cases={r.case_id:r for r in experiments.design()}
    result=[]
    for key in ('refuges_0115','refuges_0149'):
        detail=details[key];p=experiments.parameters(cases[key]);y=np.array(detail['y'])
        flow=habitat.fluxes(y,p);catabolism=np.array([f['catabolic_h2_mol_l_yr'] if f else [0.,0.] for f in flow['local']])
        global_m=float((p.weights@catabolism)[1]/np.sum(p.weights@catabolism))
        bulk_m=float(catabolism[0,1]/np.sum(catabolism[0]))
        source=flow['abiotic_ratio_yr']+core.inventory_to_ratio(p.base)*sum(
            p.weights[j]*f['methane_local_mol_l_yr'] for j,f in enumerate(flow['local']) if j and f)
        assert p.base.loss.kind=='power' and p.base.loss.elasticity==1
        forced_ratio=source*p.base.loss.lifetime_yr
        forced_temperature=float(core.temperature_k(forced_ratio,p.base.climate))
        t_switch=switch(cases[key].loss_h)
        result.append(dict(case_id=key,loss_h=cases[key].loss_h,fraction=cases[key].fraction,
            layout=cases[key].layout,dispersal_yr=cases[key].dispersal_yr,
            temperature_k=float(core.temperature_k(y[-1],p.base.climate)),switch_k=t_switch,
            global_methanogen_catabolism_percent=100*global_m,bulk_methanogen_catabolism_percent=100*bulk_m,
            bulk_methanogen_net_growth_yr=float(flow['local'][0]['net_growth_yr'][1]),
            refuge_flux_only_methane_ratio=forced_ratio,refuge_flux_only_temperature_k=forced_temperature,
            refuge_flux_only_margin_above_switch_k=forced_temperature-t_switch,
            forcing_scope='Fixed endpoint refuge flux, omit bulk methane; not a separately solved spatial endpoint'))
    return result


def cycle_checks():
    result=[]
    for key in ('0024','0126','0012'):
        path=f'models/haze_world/review/'+('dormancy0012_cycle_check.json' if key=='0012' else f'dormancy126_cycle_{key}.json')
        compact=read(path);receipt_path=compact.get('full_receipt',compact.get('full_receipt_file'))
        receipt=read(receipt_path);raw=ROOT/receipt['raw_file'];assert digest(raw)==receipt['raw_sha256']
        case=dormancy_cases.Case(**receipt['protocol']['case']);p=dormancy_cases.parameters(case)
        with np.load(raw) as d:
            t=d['t'];y=d['y'];temperature=core.temperature_k(y[-1],p.coupled.climate)
        root=compact['mixed_equilibrium'];state=np.asarray(root['y']);indices=root['active_state_indices']
        spectra=[]
        for step in (1e-7,1e-8):
            scale=np.maximum(abs(state),np.tile([100.,1e-3,1e-3,1e-3,1e-3,1e-3],p.n_patches).tolist()+[.2])
            matrix=np.empty((len(indices),len(indices)))
            for col,index in enumerate(indices):
                delta=np.zeros(p.state_size);delta[index]=scale[index]*step
                matrix[:,col]=(dormancy.rhs(state+delta,p,trial_extension=True)-dormancy.rhs(state-delta,p,trial_extension=True))[indices]/(2*step)/scale[indices]
            spectra.append(float(np.max(np.linalg.eigvals(matrix).real)))
        assert max(spectra)<0
        result.append(dict(case_id=case.case_id,raw_file=str(raw.relative_to(ROOT)),raw_sha256=digest(raw),
            observed_interval_yr=[float(t[0]),float(t[-1])],temperature_range_k=float(np.ptp(temperature)),
            recomputed_max_real_eigenvalues_yr=spectra,census_events=(receipt['control_culls']['count'] if isinstance(receipt.get('control_culls'),dict) else len(receipt.get('control_culls',receipt.get('extinction_events',[])))),
            interpretation='Finite recurrence beside a local stable root; case0012 includes local census events, not a demonstrated continuous periodic orbit.'))
    closure=read('models/haze_world/review/cycle-closure-results-2026-11-11.json')
    linear=[];unresolved=[]
    for row in closure['linear']:
        if row['status']!='completed' or row['actual_horizon_yr']<20000:
            unresolved.append(dict(case_id=row['protocol']['case']['case_id'],returned_horizon_yr=row['actual_horizon_yr'],status=row['status']));continue
        raw=ROOT/row['raw_file'];assert digest(raw)==row['raw_sha256']
        p=dormancy_cases.parameters(dormancy_cases.Case(**row['protocol']['case']))
        with np.load(raw) as d:
            t=d['t'];temperature=core.temperature_k(d['y'][-1],p.coupled.climate)
        previous=float(np.ptp(temperature[(t>=10000)&(t<=15000)]));late=float(np.ptp(temperature[t>=15000]))
        linear.append(dict(case_id=row['protocol']['case']['case_id'],horizon_yr=float(t[-1]),previous_span_k=previous,late_span_k=late,span_ratio=late/previous))
    assert len(linear)==3
    return dict(cubic=result,linear=linear,unresolved_warm_cases=unresolved)


def tail_checks():
    assessment=read('models/haze_world/review/dormancy-tail-assessment-2026-11-11.json')
    counts=Counter(row['additional_class'] for row in assessment['rows'])
    candidates=[r for r in assessment['rows'] if r['additional_class']=='macro_stationary_bank_unresolved']
    independent=[]
    for row in candidates:
        raw=ROOT/'local/haze/dormancy'/row['raw_file'];assert digest(raw)==row['raw_sha256']
        with np.load(raw) as d:
            t=d['t'];late=t>=t[-1]-20000.;values=d['y'][:,late];times=t[late]-t[late][0]
        rec=read('local/haze/dormancy/'+next(r['receipt_file'] for r in assessment['selected_receipts'] if r['case_id']==row['case_id']))
        p=dormancy_cases.parameters(dormancy_cases.Case(**rec['protocol']['case']));active=np.flatnonzero(p.weights>0)
        root=np.asarray(row['root']['y']);f=dormancy.fluxes(root,p);worst=0.
        for guild in (0,1):
            indices=p.dormant_indices[active,guild];observed=values[indices]
            a=-np.diag(f['rho_yr'][active,guild]+f['dormant_loss_yr']+p.dispersal_yr)+p.dispersal_yr*np.ones((len(active),1))*p.weights[active][None,:]
            source=f['sigma_yr'][active,guild]*root[p.biomass_indices[active,guild]]
            equilibrium=-np.linalg.solve(a,source);w=np.sqrt(p.weights[active]);b=w[:,None]*a/w[None,:]
            assert np.allclose(b,b.T,rtol=1e-12,atol=1e-14)
            eig,vec=np.linalg.eigh(b);assert np.max(eig)<0
            initial=vec.T@(w*(observed[:,0]-equilibrium))
            predicted=equilibrium[:,None]+(vec@(initial[:,None]*np.exp(eig[:,None]*times)))/w[:,None]
            for j,index in enumerate(indices):
                if index in row['macro']['failing_indices']:
                    error=float(np.max(abs(predicted[j]-observed[j]))/np.ptp(observed[j]));worst=max(worst,error)
        independent.append(dict(case_id=row['case_id'],worst_error_fraction_observed_range=worst))
    assert len(candidates)==41 and all(r['worst_error_fraction_observed_range']>.001 for r in independent)
    return dict(recount=dict(counts),verified_relaxations=counts.get('settled_up_to_dormant_relaxation',0),
        independently_reforecast_failing_cases=independent,
        minimum_case_worst_bank_range_error=min(r['worst_error_fraction_observed_range'] for r in independent),
        route='Independent weighted-symmetric eigendecomposition of frozen bank matrix; differs from augmented-matrix interval exponential in original assessor')


def main():
    result=dict(C12_C13=inventory(),C14_C15=refuge_checks(),C21_C22=cycle_checks(),C23=tail_checks())
    result['inputs_sha256']=INPUTS
    result['source_sha256']={str(Path(m.__file__).relative_to(ROOT)):digest(Path(m.__file__)) for m in (core,habitat,turnover,experiments,dormancy,dormancy_cases)}
    result['checker_sha256']=digest(Path(__file__))
    result['scope']='Read-only frozen-output audit; no physical trajectories, original labels or model assumptions changed. Supported only at the amended finite-record and parameter-conditional scope.'
    HERE.joinpath('synthesis-turnover-audit-2026-11-11.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('inputs_sha256','C23')},indent=2))
    print('tail classes',result['C23']['recount'],'minimum bank error',result['C23']['minimum_case_worst_bank_range_error'])

if __name__=='__main__':main()
