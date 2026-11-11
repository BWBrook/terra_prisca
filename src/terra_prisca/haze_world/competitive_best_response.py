"""S1/S2 maps for measured-range kinetic-position adaptation.

The specification and preview are preserved inputs. A preview-only control
retains its historical sub-measured trait range to diagnose its bound error;
the new variant always restricts heritable positions to measured 4–30 C.
"""
import argparse
import csv
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, minimize_scalar

from . import evolved_kinetics as model
from . import population_coupling as core
from . import two_guilds, hydrogen_uptake, woodii1998, methane_budget, darwinian

ROOT=Path(__file__).resolve().parents[3]
OUTPUT=ROOT/'models/haze_world/figures/competitive_evolution'
SPEC=ROOT/'models/haze_world/competitive-evolution-spec.md'
PREVIEW=ROOT/'models/haze_world/review/competitive_evolution_preview_evolved.json'
ENERGIES=(0.,.1,.2,.3,.45,.65)
INTERPOLATIONS=model.INTERPOLATIONS
ANCHOR_LOSSES=(.0003,.001,.003)
TEMPERATURES_K=np.round(np.arange(273.,303.1501,.05),8)
COOLING_RANGE_K=(273.39,297.008)


def loss_grid():
    points=.0002*10**(np.arange(17)/12)
    return tuple(sorted(set(np.r_[points,.005,ANCHOR_LOSSES])))


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def winner(ra,rm):
    if not np.isfinite(ra) and not np.isfinite(rm):return 'neither_viable'
    return 'acetogen' if ra<rm else 'methanogen' if rm<ra else 'tie'


def grid_envelope(temperatures_k,biology,energy_ev,interpolation='linear_shape',*,freeze_thresholds=False,freeze_maintenance=False,legacy_trait_min_c=None):
    t=np.asarray(temperatures_k,dtype=float)
    local=[model.local_guilds(float(v),biology,freeze_thresholds=freeze_thresholds,freeze_maintenance=freeze_maintenance) for v in t]
    if legacy_trait_min_c is None:
        traits=model.TRAIT_GRID_C
        weighted,k=model.grid_profiles(biology,float(energy_ev),interpolation)
    else:
        if interpolation!='linear_shape':raise ValueError('Historical preview control is linear only')
        traits=np.round(np.arange(legacy_trait_min_c,30.0001,.01),2)
        nodes_v,nodes_k,_,_=model.profiles(biology)
        v=np.array([np.interp(traits,model.NODES_C,x) for x in nodes_v])
        k=np.array([np.interp(traits,model.NODES_C,x) for x in nodes_k])
        weighted=v*np.exp(energy_ev/model.KB_EV/(traits+273.15))
    minima=np.full((2,len(t)),np.inf);positions=np.full((2,len(t)),np.nan)
    for left in range(0,len(t),128):
        right=min(left+128,len(t));factor=np.exp(-energy_ev/model.KB_EV/t[left:right])
        for i in range(2):
            q=np.array([g[i].maintenance+biology.loss_h/g[i].yield_g_mol for g in local[left:right]])
            h=np.array([g[i].threshold_pa for g in local[left:right]])
            capacity=factor[:,None]*weighted[i][None,:]
            if local[0][i].kinetics=='first_order':
                values=h[:,None]+k[i][None,:]*q[:,None]/capacity
            else:
                gap=capacity-q[:,None]
                values=h[:,None]+np.divide(k[i][None,:]*q[:,None],gap,out=np.full_like(gap,np.inf),where=gap>0)
            idx=np.argmin(values,axis=1)
            minima[i,left:right]=values[np.arange(right-left),idx]
            positions[i,left:right]=traits[idx]
    return minima,positions


def _roots(function, temperatures, values):
    roots=[]
    for a,b,fa,fb in zip(temperatures[:-1],temperatures[1:],values[:-1],values[1:]):
        if np.isfinite(fa) and np.isfinite(fb) and fa*fb<0:
            left,right=float(a),float(b)
            if not np.isfinite(function(left)) or not np.isfinite(function(right)):continue
            if function(left)*function(right)>0:
                left=max(float(temperatures[0]),left-.1);right=min(float(temperatures[-1]),right+.1)
            if function(left)*function(right)<0:
                roots.append(float(brentq(function,left,right,xtol=2e-10)))
        if np.isfinite(fa) and abs(fa)<1e-9:roots.append(float(a))
    absolute=np.abs(values)
    for j in np.flatnonzero((absolute[1:-1]<=absolute[:-2])&(absolute[1:-1]<=absolute[2:]))+1:
        if not np.isfinite(absolute[j]) or absolute[j]>.1:continue
        result=minimize_scalar(lambda x: abs(function(float(x))),bounds=(temperatures[j-1],temperatures[j+1]),method='bounded',options={'xatol':1e-10})
        if result.fun<1e-8:roots.append(float(result.x))
    unique=[]
    for root in sorted(roots):
        if not unique or abs(root-unique[-1])>1e-5:unique.append(root)
    return unique


def crossings(biology,energy_ev,interpolation='linear_shape',*,freeze_thresholds=False,freeze_maintenance=False,temperature_step_k=.05,legacy_trait_min_c=None):
    temperatures=TEMPERATURES_K if temperature_step_k==.05 else np.round(np.arange(273.,303.15001,temperature_step_k),8)
    envelope,positions=grid_envelope(temperatures,biology,energy_ev,interpolation,freeze_thresholds=freeze_thresholds,freeze_maintenance=freeze_maintenance,legacy_trait_min_c=legacy_trait_min_c)
    finite=np.all(np.isfinite(envelope),axis=0)
    difference=np.subtract(envelope[0],envelope[1],where=finite,out=np.full(len(temperatures),np.nan))
    cache={}
    def difference_at(t):
        if legacy_trait_min_c is None:
            if t not in cache:cache[t]=model.best_response(t,biology,energy_ev,interpolation,freeze_thresholds=freeze_thresholds,freeze_maintenance=freeze_maintenance)
            r=cache[t]['rstars_pa']
        else:r=grid_envelope([t],biology,energy_ev,interpolation,freeze_thresholds=freeze_thresholds,freeze_maintenance=freeze_maintenance,legacy_trait_min_c=legacy_trait_min_c)[0][:,0]
        return r[0]-r[1] if np.all(np.isfinite(r)) else np.nan
    records=[]
    for root in _roots(difference_at,temperatures,difference):
        below,above=difference_at(max(273.,root-.001)),difference_at(min(303.15,root+.001))
        orientation='acetogen_cold' if below<0<above else 'methanogen_cold' if below>0>above else 'tangent'
        if legacy_trait_min_c is None:
            response=model.best_response(root,biology,energy_ev,interpolation,freeze_thresholds=freeze_thresholds,freeze_maintenance=freeze_maintenance)
            trait_positions=response['positions_c'];rstars=response['rstars_pa'];kinds=[v['kind'] for v in response['guild_results']]
        else:
            r,u=grid_envelope([root],biology,energy_ev,interpolation,freeze_thresholds=freeze_thresholds,freeze_maintenance=freeze_maintenance,legacy_trait_min_c=legacy_trait_min_c)
            trait_positions=u[:,0];rstars=r[:,0];kinds=['legacy_grid']*2
        records.append(dict(temperature_k=root,positions_c=tuple(float(u) for u in trait_positions),rstars_pa=tuple(float(r) for r in rstars),trait_kinds=kinds,
            orientation=orientation,cold_winner='acetogen' if below<0 else 'methanogen',warm_winner='acetogen' if above<0 else 'methanogen',
            on_cooling_branch=bool(COOLING_RANGE_K[0]<=root<=COOLING_RANGE_K[1]),residual_pa=float(difference_at(root))))
    return dict(crossings=records,cold_end_winner=winner(*envelope[:,0]),warm_end_winner=winner(*envelope[:,-1]),
        sampled_difference_min_pa=float(np.min(difference[finite])) if np.any(finite) else None,
        sampled_difference_max_pa=float(np.max(difference[finite])) if np.any(finite) else None,
        sampled_both_viable=int(sum(finite)),sampled_temperatures=len(temperatures),temperature_step_k=temperature_step_k)


def reference_crossings(biology):
    def f(t):return np.subtract(*[g.rstar(biology.loss_h) for g in two_guilds.guilds(t-273.15,biology)])
    values=np.array([f(t) for t in TEMPERATURES_K])
    return _roots(f,TEMPERATURES_K,values)


def row_record(loss,e,interpolation,variant,result,root,index):
    base=dict(loss_h=loss,energy_ev=e,interpolation=interpolation,variant=variant,crossing_index=index,
        crossings=len(result['crossings']),cold_end_winner=result['cold_end_winner'],warm_end_winner=result['warm_end_winner'],
        sampled_both_viable=result['sampled_both_viable'],sampled_temperatures=result['sampled_temperatures'],
        sampled_difference_min_pa=result['sampled_difference_min_pa'],sampled_difference_max_pa=result['sampled_difference_max_pa'])
    if root is None:return dict(base,status='no_crossing',temperature_k='',orientation='',on_cooling_branch='',position_a_c='',position_m_c='',rstar_a_pa='',rstar_m_pa='',kind_a='',kind_m='',residual_pa='')
    return dict(base,status='crossing',temperature_k=root['temperature_k'],orientation=root['orientation'],on_cooling_branch=root['on_cooling_branch'],
        position_a_c=root['positions_c'][0],position_m_c=root['positions_c'][1],rstar_a_pa=root['rstars_pa'][0],rstar_m_pa=root['rstars_pa'][1],
        kind_a=root['trait_kinds'][0],kind_m=root['trait_kinds'][1],residual_pa=root['residual_pa'])


def write_table(path,rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)


def preview_comparison():
    preview=json.loads(PREVIEW.read_text());biology=core.reference().biology;rows=[]
    for loss in ANCHOR_LOSSES:
        for e in (0.,.2,.45,.65):
            config=replace(biology,loss_h=loss)
            actual=crossings(config,e)
            historical=crossings(config,e,legacy_trait_min_c=-.15)
            old=preview[f'L={loss:g},E={e}']['crossings']
            rows.append(dict(loss_h=loss,energy_ev=e,preview_crossings_k=[v['t_k'] for v in old],
                measured_range_crossings_k=[v['temperature_k'] for v in actual['crossings']],
                historical_range_crossings_k=[v['temperature_k'] for v in historical['crossings']],
                historical_range_positions_c=[v['positions_c'] for v in historical['crossings']],
                measured_range_positions_c=[v['positions_c'] for v in actual['crossings']]))
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--preview-check',action='store_true');args=parser.parse_args()
    OUTPUT.mkdir(parents=True,exist_ok=True)
    pinned=dict(spec_sha256=digest(SPEC),preview_sha256=digest(PREVIEW),preview_source_sha256=digest(PREVIEW.with_name('competitive_evolution_preview.py')))
    comparison=preview_comparison()
    manifest=dict(inputs=pinned,input_tables_sha256={str(p.relative_to(ROOT)):digest(p) for p in (
            ROOT/'models/haze_world/evidence/kotsyurbenko2001_table2.csv',
            ROOT/'models/haze_world/evidence/peters1998_chemostat.csv',
            ROOT/'models/haze_response/arney2016/figure4.csv',ROOT/'models/haze_response/arney2016/cases.csv')},preview_comparison=comparison,
        interpretation='Preview code admitted heritable kinetic positions below measured4C, contrary to its prose/spec. Production enforces4–30C; preview and KE predictions remain unchanged. Independent audit resolves shared differences above0.5K as this bound error.',
        numerical_choices=dict(trait_grid_c=[4.,30.,.01],actual_temperature_grid_k=[273.,303.15,.05],
            continuous_refinement='Dense global0.01C grid; bounded refinement near every sampled local minimum competitive with the global grid minimum; measured nodes/endpoints explicit. Not an interval proof of all continuous global extrema.',
            temperature_roots='Finite sign brackets plus near-zero local minima; infinities are never sign roots',loss_grid=list(loss_grid()),energies=list(ENERGIES),interpolations=list(INTERPOLATIONS)))
    if args.preview_check:
        print(json.dumps(manifest,indent=2));return
    rows=[];biology=core.reference().biology
    for interpolation in INTERPOLATIONS:
        for loss in loss_grid():
            cfg=replace(biology,loss_h=loss)
            for e in ENERGIES:
                result=crossings(cfg,e,interpolation)
                rows.extend(row_record(loss,e,interpolation,'evolved',result,root,index) for index,root in enumerate(result['crossings'] or [None]))
    anchors=[]
    for interpolation in INTERPOLATIONS:
        for loss in ANCHOR_LOSSES:
            cfg=replace(biology,loss_h=loss)
            for e in (0.,.65):
                baseline=crossings(cfg,e,interpolation)
                for label,fh,fm in (('baseline',False,False),('thresholds_30c',True,False),('maintenance_30c',False,True),('both_30c',True,True)):
                    result=baseline if label=='baseline' else crossings(cfg,e,interpolation,freeze_thresholds=fh,freeze_maintenance=fm)
                    current=[row_record(loss,e,interpolation,label,result,root,index) for index,root in enumerate(result['crossings'] or [None])]
                    for record in current:
                        base=baseline['crossings']
                        record['nearest_baseline_shift_k']=min(abs(record['temperature_k']-r['temperature_k']) for r in base) if record['temperature_k']!='' and base else ''
                    anchors.extend(current)
    write_table(OUTPUT/'best_response.csv',rows);write_table(OUTPUT/'anchors.csv',anchors)
    manifest.update(source_sha256={str(Path(m.__file__).relative_to(ROOT)):digest(m.__file__) for m in (model,core,two_guilds,hydrogen_uptake,woodii1998,methane_budget,darwinian)},
        controller_sha256=digest(__file__),outputs={name:digest(OUTPUT/name) for name in ('best_response.csv','anchors.csv')},
        counts=dict(parameter_settings=len(loss_grid())*len(ENERGIES)*len(INTERPOLATIONS),best_response_rows=len(rows),anchor_rows=len(anchors)))
    (OUTPUT/'best_response_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(manifest['counts']))

if __name__=='__main__':main()
