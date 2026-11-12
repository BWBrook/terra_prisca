"""Secondary matched methanogen-only controls for the frozen continuum map."""
import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eigvals
from scipy.optimize import brentq

from . import continuum_core as weighted, dynamic_core as biology, dynamic_realisation as b1
from . import population_coupling as core

ROOT=Path(__file__).resolve().parents[3]


def fields(ratio,p):
    t=biology.temperature(ratio,p)
    if t-p.sigma_k<273.-1e-10 or t+p.sigma_k>303.15+1e-10:return None
    pair=[biology.local_guilds([0.,0.,0.,0.],ratio,float(t+o),p)[1] for o in p.offsets]
    return dict(V=np.array([g.rate_scale for g in pair]),K=np.array([g.km_pa for g in pair]),
        h=np.array([g.threshold_pa for g in pair]),Y=np.array([g.yield_g_mol for g in pair]),
        m=np.array([g.maintenance for g in pair]),assim=np.array([g.assimilation_mol_g for g in pair]))


def at_mean(mean,parameters,p):
    f=parameters;d=p.dispersal_yr;exchange=p.base.biology.exchange_mol_l_h_pa
    supply=core.supply_h2(p.base);a=weighted.YEAR*f['Y']
    c=d+weighted.YEAR*(f['Y']*f['m']+p.base.biology.loss_h)
    j=supply-exchange*(f['h']-p.base.biology.atmosphere_pa)
    qa=j*a+exchange*f['K']*a+d*mean
    qb=-j*(f['V']*a+c)-exchange*f['K']*c-d*mean*f['V']
    qc=j*f['V']*c
    discriminant=qb*qb-4*qa*qc
    rounding=32*np.finfo(float).eps*(qb*qb+4*abs(qa*qc))
    active=j>0
    if np.any(discriminant[active] < -rounding[active]):return None
    uptake=np.zeros_like(j)
    uptake[active]=2*qc[active]/(-qb[active]+np.sqrt(np.maximum(discriminant[active],0.)))
    deficit=c-a*uptake
    if np.any(deficit<=0):return None
    x=d*mean/deficit
    pressure=np.where(j>0,f['h']+f['K']*uptake/(f['V']-uptake),
                      p.base.biology.atmosphere_pa+supply/exchange)
    return pressure,x,uptake


def pure_resident(ratio,p):
    f=fields(ratio,p)
    if f is None:return None
    def balance(logmean):
        mean=np.exp(logmean);values=at_mean(mean,f,p)
        return float(p.weights@values[1]/mean-1) if values is not None else 1e100
    lo,hi=np.log(1e-12),np.log(.1)
    if balance(lo)<=0:return None
    while balance(hi)>0 and hi<10:hi+=np.log(10.)
    if balance(hi)>0:return None
    mean=float(np.exp(brentq(balance,lo,hi,xtol=1e-12)))
    pressure,biomass,uptake=at_mean(mean,f,p)
    stocks=np.zeros((p.n,4));stocks[:,0]=pressure;stocks[:,2]=biomass
    return np.r_[stocks.ravel(),ratio]


def search_grid(p,n=121):
    abiotic=core.atmosphere(p.base.climate.case)['flux_to_ratio_per_yr']*p.base.climate.abiotic_flux
    lo=float(p.base.loss.inverse(abiotic))
    hi=float(p.base.loss.inverse(core.inventory_to_ratio(p.base)*weighted.YEAR*core.supply_h2(p.base)/4+abiotic))
    curve=core.response(p.base.climate.case)
    extra=[]
    for target in (273.+p.sigma_k,303.15-p.sigma_k):
        for a,b,ta,tb in zip(curve.ratios[:-1],curve.ratios[1:],curve.temperatures_k[:-1],curve.temperatures_k[1:]):
            if ta!=tb and min(ta,tb)<=target<=max(ta,tb):extra.append(a+(b-a)*(target-ta)/(tb-ta))
        if min(p.base.climate.t_zero_k,curve.temperatures_k[0])<=target<=max(p.base.climate.t_zero_k,curve.temperatures_k[0]):
            q=p.base.climate
            if curve.temperatures_k[0]!=q.t_zero_k:
                extra.append(q.bridge_scale*np.expm1((target-q.t_zero_k)/(curve.temperatures_k[0]-q.t_zero_k)*np.log1p(curve.ratios[0]/q.bridge_scale)))
    return np.unique(np.r_[np.linspace(lo,hi,n),[v for v in np.r_[curve.ratios,extra] if lo<=v<=hi]])


def reduced_blocks(y,p):
    b=weighted.local_blocks(y,p);ix=np.array([0,2])
    return weighted.Blocks(b.local[:,ix][:,:,ix],b.mean[:,ix,1:2],b.ratio[:,ix],b.temperature[:,ix],
        b.emission[:,ix],b.emission_ratio,b.emission_temperature,np.array([[0.,1.]]),b.weights,b.climate_slope)


def describe(y,p):
    f=weighted.physical_rhs(y,p);scale=biology.state_scales(y,p)
    residual=max(float(np.max(abs(f/scale))),float(np.max(abs(weighted.per_capita(y,p)))))
    b=reduced_blocks(y,p)
    stock=y[:-1].reshape(p.n,4)
    scales=np.r_[np.c_[np.maximum(stock[:,0],10.),np.maximum(stock[:,2],1e-5)].ravel(),max(y[-1],.01)]
    matrix=weighted.dense_matrix(y,p,blocks=b)*scales[None,:]/scales[:,None]
    lead=float(max(eigvals(matrix).real))
    forcing=np.zeros((p.n,2));forcing[:,0]=weighted.YEAR/core.HENRY_30C_MOL_L_PA*core.supply_h2(p.base)
    slope=None
    try:
        derivative,_=weighted.block_solve(b,-forcing,0.)
        slope=float(b.climate_slope*derivative[-1])
    except np.linalg.LinAlgError:pass
    status='qualified' if residual<1e-7 else 'balance_unresolved'
    if lead>=-1e-9:status='unstable_control' if lead>1e-9 else 'neutral_control'
    curve=core.response(p.base.climate.case)
    if np.any(np.isclose(y[-1],curve.ratios,rtol=0.,atol=1e-10)):status='climate_corner_control'
    if slope is None:status='singular_control'
    return dict(control_status=status,control_temperature_k=biology.temperature(y[-1],p),
        control_ratio=float(y[-1]),control_slope_k=slope,control_max_real_yr=lead,
        control_balance_residual_yr=residual,support_min_k=biology.temperature(y[-1],p)-p.sigma_k,
        support_max_k=biology.temperature(y[-1],p)+p.sigma_k)


def matched(p,community_slope):
    p=replace(p,base=replace(p.base,enabled=(False,True)))
    grid=search_grid(p)
    def balance(r):
        y=pure_resident(r,p)
        return float(weighted.physical_rhs(y,p)[-1]) if y is not None else np.nan
    roots=[]
    for r in scalar_roots(balance,grid):
        y=pure_resident(r,p)
        if y is not None:roots.append(describe(y,p))
    eligible=[r for r in roots if r['control_status']=='qualified']
    record=dict(gain=None,gain_status='no_admissible_control_detected',control_roots=roots,
                search_nodes=len(grid),supported_search_nodes=sum(fields(float(r),p) is not None for r in grid),
                search_scope='Finite scalar supported-domain search; no clipping; absence is not certified.')
    if len(eligible)>1:record['gain_status']='ambiguous_control'
    elif len(eligible)==1:
        row=eligible[0];record.update(row)
        if row['control_slope_k'] is None:record['gain_status']='singular_control'
        elif abs(row['control_slope_k'])<1e-10:record['gain_status']='zero_control_slope'
        else:record.update(gain_status='defined',gain=float(community_slope/row['control_slope_k']))
    elif any(r['control_status']=='balance_unresolved' for r in roots):record['gain_status']='unresolved_control_balance'
    elif roots:record['gain_status']='no_stable_admissible_control'
    return record


def scalar_roots(function,grid,zero_tolerance=1e-14):
    values=[function(float(r)) for r in grid]
    candidates=[float(r) for r,v in zip(grid,values) if np.isfinite(v) and abs(v)<=zero_tolerance]
    for a,b,fa,fb in zip(grid[:-1],grid[1:],values[:-1],values[1:]):
        if np.isfinite(fa) and np.isfinite(fb) and fa*fb<0:
            candidates.append(float(brentq(function,a,b,xtol=1e-13)))
    roots=[]
    for r in sorted(candidates):
        value=function(r)
        if np.isfinite(value) and abs(value)<=zero_tolerance and not any(abs(r-v)<1e-9 for v in roots):roots.append(r)
    return roots


def run(output):
    manifest_path=ROOT/'models/haze_world/figures/continuum_habitats/manifest.json'
    manifest=json.loads(manifest_path.read_text())
    used=[name for name in manifest['source_sha256'] if name.startswith('src/') and not name.endswith('/continuum_experiments.py')]
    for name in used:
        if sha256((ROOT/name).read_bytes()).hexdigest()!=manifest['source_sha256'][name]:raise ValueError('Primary model source identity changed: '+name)
    frozen=manifest['finite_input_export_correction']['frozen_cache_sha256']
    rows=[];detailed=[]
    for name,expected in frozen.items():
        path=ROOT/name
        if sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Frozen cache identity changed: '+name)
        record=json.loads(path.read_text())
        if isinstance(record,list):
            for r in record:
                old=r['old_matched_control']
                rows.append(dict(stage='C0',chemistry=r['chemistry'],fraction=r['fraction'],loss_h=r['loss_h'],
                    nominal_potential=r['nominal_potential'],sigma_k=0.,dispersal_yr=.001,
                    community_ratio=r['ratio'],community_slope_k=r['Sc'],**old,
                    control_inventory_scope='Retained B1 secondary comparison; new primary local gain unchanged',
                    input_path=name,input_sha256=expected))
            continue
        r=record
        mesh=weighted.Mesh(tuple(r['offsets']),tuple(r['weights']),tuple(r['panels']))
        base=replace(core.reference(r['nominal_potential']),acetate_fraction=r['fraction'])
        p=weighted.WeightedParams(base,r['chemistry'],r['sigma_k'],mesh,r['dispersal_yr'])
        result=matched(p,r['Sc'])
        common=dict(stage='C1',chemistry=r['chemistry'],fraction=r['fraction'],loss_h=.001,
            nominal_potential=r['nominal_potential'],sigma_k=r['sigma_k'],dispersal_yr=r['dispersal_yr'],
            community_ratio=r['ratio'],community_slope_k=r['Sc'],input_path=name,input_sha256=expected)
        roots=result.pop('control_roots')
        rows.append(dict(common,**result));detailed.append(dict(common,**result,control_roots=roots))
    b1.write_csv(output/'matched_controls.csv',rows)
    sources=[Path(__file__),Path(weighted.__file__),ROOT/'src/terra_prisca/haze_world/dynamic_core.py',manifest_path]
    report=dict(scope='Secondary matched treatment controls; no C0/C1 primary result, equation or prediction changed.',
        C0_records=sum(r['stage']=='C0' for r in rows),C1_records=sum(r['stage']=='C1' for r in rows),
        C1_defined=sum(r['stage']=='C1' and r['gain_status']=='defined' for r in rows),
        source_sha256={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in sources},
        primary_model_sources_verified=len(used),
        output_sha256=sha256((output/'matched_controls.csv').read_bytes()).hexdigest(),records=detailed)
    (output/'matched_controls_manifest.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'models/haze_world/figures/continuum_habitats')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True);report=run(args.output)
    print(json.dumps({k:report[k] for k in ('C0_records','C1_records','C1_defined')}))


if __name__=='__main__':main()
