"""C0 local-gain inventory and C1 adaptive habitat experiments."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from dataclasses import replace
from hashlib import sha256
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eigvals
from scipy.optimize import brentq

from . import continuum_core as model
from . import dynamic_core as legacy
from . import dynamic_realisation as b1

ROOT=Path(__file__).resolve().parents[3]
OUTPUT=ROOT/'models/haze_world/figures/continuum_habitats'
SHIFTS=(0.,.001j,.003j,.01j,.03j,.1j,.3j,1j)
CHECKS=(('fixed',.5,1.,1e-4),('fixed',.5,3.,1e-4),('fixed',.5,6.,1e-4),
        ('fixed',0.,3.,1e-3),('fixed',.5,3.,1e-2),('products',.5,6.,1e-4))


def digest(path):return sha256(Path(path).read_bytes()).hexdigest()


def sources():
    names=[Path(__file__),Path(model.__file__),Path(legacy.__file__),Path(b1.__file__)]
    names += [Path(legacy.__file__).with_name(p) for p in ('population_coupling.py','methane_budget.py','darwinian.py','two_guilds.py','hydrogen_uptake.py','woodii1998.py')]
    names += [ROOT/p for p in ('models/haze_world/continuum-habitats-spec.md','models/haze_world/continuum-habitats-methods.md',
                'models/haze_world/evidence/kotsyurbenko2001_table2.csv','models/haze_world/evidence/peters1998_chemostat.csv',
                'models/haze_response/arney2016/figure4.csv','models/haze_response/arney2016/cases.csv','uv.lock')]
    return {str(p.relative_to(ROOT)):digest(p) for p in names}


def clean(value):
    if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value,(tuple,list,np.ndarray)):return [clean(v) for v in value]
    if isinstance(value,(np.integer,np.bool_)):return value.item()
    if isinstance(value,(np.floating,float)):return float(value) if np.isfinite(value) else None
    if isinstance(value,complex):return [value.real,value.imag]
    return value


def parameters(chemistry,fraction,sigma,d,potential=.3,mesh=None):
    p=b1.parameters(chemistry,fraction,.001,potential)
    return model.WeightedParams(p.base,chemistry,sigma,mesh or model.gauss_mesh(sigma),d)


def spectrum(y,p,tau=0.,blocks=None):
    blocks=model.local_blocks(y,p) if blocks is None else blocks
    size=p.n*blocks.local.shape[1]+1+(tau>0)
    if size<=2048:
        scale=model.operator_scales(y,p,blocks,tau)
        matrix=model.dense_matrix(y,p,tau,blocks)*scale[None,:]/scale[:,None]
        values=eigvals(matrix,check_finite=True)
        lead=values[np.argmax(values.real)]
        return dict(status='full_collocation_spectrum',leading_real=float(lead.real),leading_imag=float(abs(lead.imag)),residual=None)
    record=model.spectrum(y,p,tau,blocks=blocks,shifts=SHIFTS,tolerance=1e-10)
    if record['leading_real'] is None:
        return dict(status='unresolved',leading_real=None,leading_imag=None,residual=None)
    values=record['eigenvalues'];lead=values[np.argmax(values.real)]
    return dict(status=record['status'],leading_real=float(lead.real),leading_imag=float(abs(lead.imag)),residual=record['max_eigen_residual'])


def lag_check(y,p,blocks=None):
    blocks=model.local_blocks(y,p) if blocks is None else blocks
    memo={}
    def get(tau):
        if tau not in memo:memo[tau]=spectrum(y,p,tau,blocks)
        return memo[tau]
    def scalar(tau):
        row=get(float(tau))
        if row['leading_real'] is None or row['status'] in ('unresolved','partial_shift_invert'):raise ArithmeticError('Unresolved primary spectrum')
        return row['leading_real']
    zero=get(0.)
    if zero['leading_real'] is None or zero['status'] in ('unresolved','partial_shift_invert'):return dict(status='spectrum_unresolved',tau_c=None,spectra=[])
    initial=zero['leading_real']
    status='already_unstable' if initial>1e-9 else 'neutral' if initial>=-1e-9 else 'not_detected_through_10000'
    crossing=[]
    grid=np.unique(np.r_[b1.LAGS[1:],np.geomspace(.001,1e4,22)])
    left=0.;fl=initial
    try:
        for right in grid:
            fr=scalar(right)
            if fl*fr<0:
                found=brentq(scalar,left,float(right),xtol=1e-7)
                crossing.append(dict(tau_yr=found,direction='loss' if fl<0 else 'restabilisation'))
            left,fl=float(right),fr
    except ArithmeticError:
        status='spectrum_unresolved'
    losses=[r['tau_yr'] for r in crossing if r['direction']=='loss']
    if losses and status not in ('already_unstable','neutral','spectrum_unresolved'):status='finite_crossing'
    return dict(status=status,tau_c=losses[0] if losses else (0. if status in ('already_unstable','neutral') else None),
                crossings=crossing,leading_zero=zero,
                spectra=[dict(tau_yr=tau,**get(tau)) for tau in b1.LAGS+(1e4,)],
                maximum_eigen_residual=max([r['residual'] for r in memo.values() if r['residual'] is not None],default=None))


def gain_check(y,p):
    result=model.slopes(y,p)
    if result['status'] not in ('defined','climate_insensitive'):return result
    if result['status']=='defined':
        finite=model.frozen_supply_check(y,p,step=1e-4)
        result['S0_finite_difference']=finite['S0_finite_difference']
        result['frozen_ratio_error']=max(r['maximum_ratio_error'] for r in finite['points'])
        error=abs(result['S0']-finite['S0_finite_difference'])
        result['frozen_fd_agrees']=finite['status']=='passed' and error<=max(.001,.02*abs(result['S0']))
        result['frozen_fd_max_residual']=max(r['residual'] for r in finite['points'])
        if not result['frozen_fd_agrees']:
            fine=model.frozen_supply_check(y,p,step=1e-5)
            result['S0_finite_difference_fine']=fine['S0_finite_difference']
            result['frozen_fd_agrees']=fine['status']=='passed' and abs(result['S0']-fine['S0_finite_difference'])<=max(.001,.02*abs(result['S0']))
    frozen=spectrum(y,p,blocks=model.frozen_blocks(y,p))
    result['frozen_leading_real']=frozen['leading_real'];result['frozen_spectrum_status']=frozen['status']
    return result


def measure(y,p):
    blocks=model.local_blocks(y,p)
    edge=float(np.max(np.linalg.eigvals(blocks.local).real))
    slopes=gain_check(y,p); lag=lag_check(y,p,blocks)
    return dict(temperature_k=legacy.temperature(y[-1],p),ratio=float(y[-1]),nodes=p.n,
                Sc=slopes.get('Sc'),S0=slopes.get('S0'),G_loc=slopes.get('G_loc'),gain_status=slopes['status'],
                gain=slopes,lag=lag,sink_spectrum_edge_yr=edge,
                per_cell_balance_residual_yr=float(np.max(abs(model.per_capita(y,p)))))


def slopes_agree(a,b):
    return all(a.get(k) is not None and b.get(k) is not None and
               abs(a[k]-b[k])<=max(.001,.02*abs(b[k])) for k in ('Sc','S0'))


def lag_agrees(a,b):
    if a['status']!=b['status']:return False
    if a['status']=='not_detected_through_10000':return True
    if a['status']=='finite_crossing':return abs(a['tau_c']-b['tau_c'])<=.02*abs(b['tau_c'])
    return False


def c1_case(setting):
    chemistry,fraction,sigma,d,potential=setting
    p=parameters(*setting)
    result=model.adaptive_equilibrium(p,max_levels=32)
    common=dict(chemistry=chemistry,fraction=fraction,sigma_k=sigma,dispersal_yr=d,nominal_potential=potential)
    if 'y' not in result:return dict(common,status=result['status'],history=result.get('history',[]))
    p=result['p'];y=result['y'];history=[]
    if result['status']!='logit_resolved':return dict(common,status=result['status'],history=result.get('history',[]))
    previous=measure(y,p)
    converged=False
    for iteration in range(7):
        mesh,zone=model.refine_panels(y,p,force_mixed=True)
        if len(mesh.nodes)==p.n:
            edges=np.asarray(p.mesh.panels);mesh=model.gauss_mesh(sigma,np.sort(np.r_[edges,(edges[:-1]+edges[1:])/2]))
        if len(mesh.nodes)>4096:break
        q=replace(p,mesh=mesh);found=model.equilibrium(model.interpolate_state(y,p,q),q)
        if found is None:break
        _,logit_check=model.refine_panels(found['y'],q)
        if logit_check['status']!='logit_resolved':
            found=model.adaptive_equilibrium(q,seed=found['y'],max_levels=32)
            if found.get('status')!='logit_resolved':break
            q=found['p']
        current=measure(found['y'],q)
        entry=dict(iteration=iteration,nodes_before=p.n,nodes_after=q.n,
                   slopes_agree=slopes_agree(previous,current),lag_agrees=lag_agrees(previous['lag'],current['lag']),
                   before=previous,after=current)
        history.append(entry)
        p,y,previous=q,found['y'],current
        if entry['slopes_agree'] and entry['lag_agrees'] and current['gain'].get('frozen_fd_agrees',False):
            converged=True;break
    _,zone=model.refine_panels(y,p)
    return dict(common,status='converged' if converged else 'doubling_unresolved',**previous,
                mixed_width_k=zone.get('mixed_width_k'),mesh_history=result.get('history',[]),doubling_history=history,
                offsets=p.mesh.nodes,weights=p.mesh.weights,panels=p.mesh.panels,y=y)


def c0_rows():
    path=ROOT/'models/haze_world/figures/dynamic_realisation/stability_gain.csv'
    rows=list(csv.DictReader(path.open())); result=[]
    for row in rows:
        if row['status']!='accepted' or int(row['n_habitats'])!=1:continue
        p0=b1.parameters(row['chemistry'],float(row['fraction']),float(row['loss_h']),float(row['nominal_potential']))
        choices=[r for r in legacy.equilibrium_states(p0) if r['kind']=='mixed']
        if not choices:continue
        record=min(choices,key=lambda e:abs(e['r']-float(row['ratio'])))
        if abs(record['r']-float(row['ratio']))>1e-8:raise ArithmeticError('C0 branch does not reproduce B1')
        p=model.WeightedParams(p0.base,p0.chemistry)
        y=record['y'];metrics=measure(y,p)
        old={k:row.get(k) for k in ('gain','gain_status','control_slope_k','control_temperature_k')}
        result.append(dict(chemistry=p.chemistry,fraction=float(row['fraction']),loss_h=float(row['loss_h']),
                           nominal_potential=float(row['nominal_potential']),sigma_k=0.,status='homogeneous',
                           **metrics,old_matched_control=old,y=y))
    return result


def flat(record):
    result={k:v for k,v in record.items() if not isinstance(v,(dict,list,tuple,np.ndarray))}
    result.update(critical_lag_status=record.get('lag',{}).get('status'),critical_lag_yr=record.get('lag',{}).get('tau_c'),
                  leading_real_zero=record.get('lag',{}).get('leading_zero',{}).get('leading_real'),
                  frozen_leading_real=record.get('gain',{}).get('frozen_leading_real'),
                  frozen_fd_agrees=record.get('gain',{}).get('frozen_fd_agrees'),
                  S0_finite_difference=record.get('gain',{}).get('S0_finite_difference_fine',record.get('gain',{}).get('S0_finite_difference')),
                  S0_finite_difference_step=1e-5 if 'S0_finite_difference_fine' in record.get('gain',{}) else 1e-4,
                  S0_finite_difference_coarse=record.get('gain',{}).get('S0_finite_difference'))
    return result


def write_tables(output,c0,c1,hashes):
    output.mkdir(parents=True,exist_ok=True)
    b1.write_csv(output/'c0_local_gain.csv',[flat(r) for r in c0])
    b1.write_csv(output/'c1_resolved.csv',[flat(r) for r in c1])
    selected=[]
    for r in c1:
        if r['nominal_potential']!=.3 or tuple(r[k] for k in ('chemistry','fraction','sigma_k','dispersal_yr')) not in CHECKS:continue
        if 'y' not in r:continue
        selected.append(dict(case_id='_'.join(str(r[k]) for k in ('chemistry','fraction','sigma_k','dispersal_yr')),
            chemistry=r['chemistry'],fraction=r['fraction'],sigma_k=r['sigma_k'],dispersal_yr=r['dispersal_yr'],
            offsets=r['offsets'],weights=r['weights'],y=r['y'],mesh_converged=r['status']=='converged',
            primary_tau_yr=r['lag']['tau_c'],primary_status=r['lag']['status'],
            sampled_primary_stable=all(q['leading_real'] is not None and q['leading_real']<0 for q in r['lag']['spectra'])))
    (output/'characteristic_states.json').write_text(json.dumps(clean(selected),indent=2,allow_nan=False)+'\n')
    manifest=dict(source_sha256=hashes,method_freeze_commit='39572a4',C0_records=len(c0),C1_records=len(c1),
                  C1_converged=sum(r['status']=='converged' for r in c1),
                  output_sha256={name:digest(output/name) for name in ('c0_local_gain.csv','c1_resolved.csv','characteristic_states.json')})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def run(output,cache,workers=2,only='all',limit=None):
    output.mkdir(parents=True,exist_ok=True);cache.mkdir(parents=True,exist_ok=True)
    hashes=sources();stamp=sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()[:20]
    path=cache/f'c0-{stamp}.json'
    if path.exists():c0=json.loads(path.read_text())
    else:
        c0=clean(c0_rows());path.write_text(json.dumps(c0,allow_nan=False)+'\n')
    jobs=list(itertools.product(('fixed','products'),(0.,.5),(1.,3.,6.),(1e-4,1e-3,1e-2,1e-1),(.3,)))
    jobs+=list(itertools.product(('fixed','products'),(0.,.5),(3.,),(1e-4,1e-3,1e-2,1e-1),(.24,.36)))
    if only=='c0':jobs=[]
    if limit is not None:jobs=jobs[:limit]
    c1=[];pending=[]
    for setting in jobs:
        path=cache/(sha256(json.dumps([stamp,setting]).encode()).hexdigest()[:24]+'.json')
        if path.exists():c1.append(json.loads(path.read_text()))
        else:pending.append((setting,path))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        work={pool.submit(c1_case,setting):path for setting,path in pending}
        for i,future in enumerate(as_completed(work),1):
            result=clean(future.result());work[future].write_text(json.dumps(result,allow_nan=False)+'\n');c1.append(result)
            print(f'C1 completed {i}/{len(pending)} new settings',flush=True)
    c1.sort(key=lambda r:tuple(str(r[k]) for k in ('chemistry','fraction','sigma_k','dispersal_yr','nominal_potential')))
    manifest=write_tables(output,c0,c1,hashes);print(json.dumps(manifest,indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUTPUT)
    parser.add_argument('--cache',type=Path,default=ROOT/'local/haze/continuum_habitats')
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--only',choices=('all','c0'),default='all')
    parser.add_argument('--limit',type=int)
    args=parser.parse_args();run(args.output,args.cache,args.workers,args.only,args.limit)


if __name__=='__main__':main()
