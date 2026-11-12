"""Independent C0 controls and selected C1 characteristic comparisons."""

import argparse
import inspect
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import time

import numpy as np

from terra_prisca.haze_world import continuum_characteristic as own
from terra_prisca.haze_world import dynamic_core as primary
from terra_prisca.haze_world import population_coupling as physical

ROOT=Path(__file__).resolve().parents[2]

CASES=(('fixed',.5,1.,1e-4),('fixed',.5,3.,1e-4),('fixed',.5,6.,1e-4),
       ('fixed',0.,3.,1e-3),('fixed',.5,3.,1e-2),('products',.5,6.,1e-4))


def produce_selected(directory,max_doublings=6):
    from terra_prisca.haze_world import continuum_core as weighted
    directory.mkdir(parents=True,exist_ok=True)
    entries=[]
    for chemistry,fraction,sigma,dispersal in CASES:
        label=f'{chemistry}_f{fraction:g}_s{sigma:g}_d{dispersal:g}'
        base=replace(physical.reference(),acetate_fraction=fraction)
        p=weighted.WeightedParams(base,chemistry,sigma,weighted.gauss_mesh(sigma),dispersal)
        started=time.monotonic();answer=weighted.adaptive_equilibrium(p,max_levels=24)
        if answer['status']!='logit_resolved':
            entries.append(dict(case_id=label,chemistry=chemistry,fraction=fraction,sigma_k=sigma,
                                dispersal_yr=dispersal,status=answer['status'],mesh_converged=False))
            print(label,answer['status'],flush=True)
            continue
        p=answer['p'];y=answer['y'];history=[];converged=False
        previous=None
        for level in range(max_doublings+1):
            slopes=weighted.slopes(y,p)
            blocks=own.assemble(p,y)
            checks=[own.critical_lags(blocks,frequencies=size) for size in (361,721)]
            row=dict(level=level,n=p.n,Sc=slopes['Sc'],S0=slopes['S0'],G_loc=slopes['G_loc'],
                     characteristic_checks=checks)
            if previous is not None:
                slopes_ok=all(abs(row[name]-previous[name])<=max(.001,.02*abs(row[name])) for name in ('Sc','S0'))
                first=previous['characteristic_checks'][-1];last=checks[-1]
                finite=first['critical_lag_yr'] is not None and last['critical_lag_yr'] is not None
                lag_change=abs(first['critical_lag_yr']-last['critical_lag_yr'])/last['critical_lag_yr'] if finite else None
                lag_ok=bool((finite and lag_change<.02) or (first['status']==last['status']=='not_detected_through_10000'))
                ffirst,flast=checks
                freq_finite=ffirst['critical_lag_yr'] is not None and flast['critical_lag_yr'] is not None
                frequency_ok=bool((freq_finite and abs(ffirst['critical_lag_yr']-flast['critical_lag_yr'])/flast['critical_lag_yr']<.02)
                                  or(ffirst['status']==flast['status']=='not_detected_through_10000'))
                row.update(slopes_converged=slopes_ok,lag_converged=lag_ok,lag_relative_change=lag_change,frequency_grid_converged=frequency_ok)
                converged=slopes_ok and lag_ok and frequency_ok
            history.append(row)
            if converged:break
            if level==max_doublings:break
            mesh,diagnostic=weighted.refine_panels(y,p,force_mixed=True)
            if diagnostic['status']=='endpoint_unresolved' or len(mesh.nodes)>4096 or len(mesh.nodes)==p.n:
                row['refinement_stop']=diagnostic['status'] if len(mesh.nodes)<=4096 else 'node_limit'
                break
            nextp=replace(p,mesh=mesh)
            nextanswer=weighted.adaptive_equilibrium(nextp,seed=weighted.interpolate_state(y,p,nextp),max_levels=24)
            if nextanswer['status']!='logit_resolved':
                row['refinement_stop']=nextanswer['status'];break
            previous=row;p,y=nextanswer['p'],nextanswer['y']
        entry=dict(case_id=label,chemistry=chemistry,fraction=fraction,sigma_k=sigma,dispersal_yr=dispersal,
                   status='characteristic_mesh_converged' if converged else 'mesh_unresolved',mesh_converged=converged,
                   offsets=p.offsets.tolist(),weights=p.weights.tolist(),panels=list(p.mesh.panels),y=y.tolist(),
                   Sc=slopes['Sc'],S0=slopes['S0'],G_loc=slopes['G_loc'],history=history,
                   primary_tau_yr=None,primary_status='awaiting_primary_operator',sampled_primary_stable=False,
                   elapsed_seconds=time.monotonic()-started)
        path=directory/(label+'.json');path.write_text(json.dumps(entry,indent=2,allow_nan=False)+'\n')
        entries.append(entry)
        print(label,entry['status'],'n',p.n,'tau',history[-1]['characteristic_checks'][-1]['critical_lag_yr'],flush=True)
    (directory/'selected_states.json').write_text(json.dumps(dict(cases=entries),indent=2,allow_nan=False)+'\n')
    return entries


def homogeneous():
    rows=[]
    for fraction in (0.,.5):
        base=replace(physical.reference(),acetate_fraction=fraction)
        for chemistry in ('fixed','products','acetate_only','methane_only'):
            parameters=primary.DynamicParams(base,chemistry)
            state=next(e['y'] for e in primary.equilibrium_states(parameters) if e['kind']=='mixed')
            p=SimpleNamespace(base=base,chemistry=chemistry,offsets=np.zeros(1),weights=np.ones(1),
                              dispersal_yr=.001,slope_multiplier=1.)
            slopes=own.homogeneous_frozen_gain(p,state)
            blocks=own.assemble(p,state)
            spectra=own.critical_lags(blocks,frequencies=721)
            rows.append(dict(chemistry=chemistry,fraction=fraction,y=state.tolist(),
                             **slopes,characteristic=spectra))
    return rows


def selected(states):
    rows=[]
    for entry in states:
        if 'y' not in entry:
            rows.append(dict(case_id=entry['case_id'],passed=False,comparison_kind='missing_state',status=entry['status']))
            continue
        base=physical.reference(float(entry.get('potential',.3)))
        base=replace(base,acetate_fraction=float(entry['fraction']))
        p=SimpleNamespace(base=base,chemistry=entry['chemistry'],offsets=np.array(entry['offsets']),
                          weights=np.array(entry['weights']),dispersal_yr=float(entry['dispersal_yr']),
                          slope_multiplier=1.)
        y=np.array(entry['y'])
        results=[]
        for size in (361,721):
            results.append(own.critical_lags(own.assemble(p,y),frequencies=size))
        main=results[-1];primary_tau=entry.get('primary_tau_yr')
        finite=main['critical_lag_yr'] is not None and primary_tau is not None
        relative=abs(main['critical_lag_yr']-primary_tau)/abs(primary_tau) if finite else None
        frequency_finite=all(r['critical_lag_yr'] is not None for r in results)
        frequency_change=abs(results[0]['critical_lag_yr']-results[1]['critical_lag_yr'])/results[1]['critical_lag_yr'] if frequency_finite else None
        censored=main['status']=='not_detected_through_10000' and entry.get('primary_status')=='not_detected_through_10000'
        bracket=entry.get('primary_sign_bracket')
        bracket_pass=bool(main['critical_lag_yr'] is not None and bracket and
                          bracket[0]<=main['critical_lag_yr']<=bracket[1] and
                          entry.get('primary_bracket_signs',[])==[-1,1])
        passed=bool(entry.get('mesh_converged',False) and
                    ((finite and relative<.02 and frequency_change is not None and frequency_change<.02) or
                     (bracket_pass and frequency_change is not None and frequency_change<.02) or
                     (censored and all(r['status']=='not_detected_through_10000' for r in results) and entry.get('sampled_primary_stable',False))))
        rows.append(dict(case_id=entry['case_id'],chemistry=entry['chemistry'],fraction=entry['fraction'],
                         sigma_k=entry['sigma_k'],dispersal_yr=entry['dispersal_yr'],nodes=len(entry['weights']),
                         Sc=entry.get('Sc'),S0=entry.get('S0'),G_loc=entry.get('G_loc'),
                         mesh_converged=entry.get('mesh_converged',False),primary_tau_yr=primary_tau,
                         primary_status=entry.get('primary_status'),relative_tau_difference=relative,
                         frequency_grid_relative_change=frequency_change,
                         comparison_kind='finite_margin' if finite else 'independent_sign_bracket' if bracket_pass else 'consistent_right_censoring' if censored else 'unresolved',
                         primary_sign_bracket=bracket,primary_operator_checks=entry.get('primary_operator_checks'),
                         passed=passed,characteristic_checks=results))
    return rows


def primary_checks(entries):
    from terra_prisca.haze_world import continuum_core as weighted
    result=[]
    for original in entries:
        entry=dict(original)
        if not entry.get('mesh_converged',False):
            result.append(entry);continue
        base=replace(physical.reference(),acetate_fraction=float(entry['fraction']))
        mesh=weighted.Mesh(tuple(entry['offsets']),tuple(entry['weights']),tuple(entry['panels']))
        p=weighted.WeightedParams(base,entry['chemistry'],float(entry['sigma_k']),mesh,float(entry['dispersal_yr']))
        y=np.array(entry['y']);b=weighted.local_blocks(y,p)
        tau=entry['history'][-1]['characteristic_checks'][-1]['critical_lag_yr']
        lags=[.99*tau,tau,1.01*tau] if tau is not None else [0.,.03,.1,.3,1.,3.,10.,30.,100.,300.,1000.,10000.]
        checks=[]
        for lag in lags:
            m=weighted.dense_matrix(y,p,lag,blocks=b)
            scales=weighted.operator_scales(y,p,blocks=b,tau=lag)
            m=m*scales[None,:]/scales[:,None]
            lead=np.linalg.eigvals(m)
            value=lead[np.argmax(lead.real)]
            checks.append(dict(tau_yr=lag,leading_real_yr=float(value.real),leading_imag_yr=float(abs(value.imag))))
        entry['primary_operator_checks']=checks
        if tau is not None:
            entry['primary_sign_bracket']=[.99*tau,1.01*tau]
            entry['primary_bracket_signs']=[int(np.sign(checks[0]['leading_real_yr'])),int(np.sign(checks[-1]['leading_real_yr']))]
            entry['primary_status']='independent_sign_bracket'
        else:
            entry['sampled_primary_stable']=all(r['leading_real_yr']<0 for r in checks)
            entry['primary_status']='not_detected_through_10000' if entry['sampled_primary_stable'] else 'sampled_instability'
        result.append(entry)
        print(entry['case_id'],'primary',entry['primary_status'],flush=True)
    functions=('_local','physical_rhs','local_blocks','dense_matrix')
    functional_hash=sha256('\n'.join(inspect.getsource(getattr(weighted,name)) for name in functions).encode()).hexdigest()
    return result,dict(physical_function_sha256=functional_hash,source_sha256=sha256(Path(weighted.__file__).read_bytes()).hexdigest(),
                       route='Full operator dense spectra at independent characteristic candidate +/-1percent, or prescribed censored lag grid.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--states',type=Path)
    parser.add_argument('--produce-selected',type=Path)
    parser.add_argument('--primary-output',type=Path)
    args=parser.parse_args()
    sources=[Path(__file__),Path(own.__file__),Path(primary.__file__),Path(physical.__file__),
             *[ROOT/'src/terra_prisca/haze_world'/name for name in
               ('two_guilds.py','methane_budget.py','darwinian.py','hydrogen_uptake.py','woodii1998.py')],
             ROOT/'models/haze_world/continuum-habitats-spec.md',
             ROOT/'models/haze_world/continuum-habitats-methods.md',
             ROOT/'models/haze_response/arney2016/figure4.csv',
             ROOT/'models/haze_response/arney2016/cases.csv',
             ROOT/'models/haze_world/evidence/kotsyurbenko2001_table2.csv',
             ROOT/'models/haze_world/evidence/peters1998_chemostat.csv',ROOT/'uv.lock']
    report=dict(scope='Independent selected characteristic and homogeneous frozen-composition checks; no continuum certificate from an unresolved mesh.',
                homogeneous=homogeneous(),selected=[],selected_status='awaiting_qualified_states')
    if args.states:
        entries=json.loads(args.states.read_text())
        if isinstance(entries,dict):
            if 'operator_provenance' in entries:
                report['primary_operator_provenance']=entries['operator_provenance']
            entries=entries['cases']
        sources.append(ROOT/'src/terra_prisca/haze_world/continuum_core.py')
        if args.primary_output:
            entries,record=primary_checks(entries)
            args.primary_output.write_text(json.dumps(dict(cases=entries,operator_provenance=record),indent=2,allow_nan=False)+'\n')
            report['primary_operator_provenance']=record
            sources.append(ROOT/'src/terra_prisca/haze_world/continuum_core.py')
        report['selected']=selected(entries)
        report['selected_status']='completed' if all(r['passed'] for r in report['selected']) else 'one_or_more_unresolved'
        report['states_file_sha256']=sha256(args.states.read_bytes()).hexdigest()
    if args.produce_selected:
        report['selected_production']=produce_selected(args.produce_selected)
        sources.append(ROOT/'src/terra_prisca/haze_world/continuum_core.py')
    report['source_sha256']={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in sources}
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    for row in report['homogeneous']:
        print(row['chemistry'],row['fraction'],'Sc',row['sc'],'S0',row['s0'],'Glocal',row['gain_local'],row['characteristic']['status'])


if __name__=='__main__':
    main()
