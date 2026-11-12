"""Independent fixed-mixture balances and bounded verification of C59."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eigvals
from scipy.optimize import brentq

from terra_prisca.haze_world import dynamic_core as model
from terra_prisca.haze_world import dynamic_realisation as runs
from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world.two_guilds import guilds

ROOT=Path(__file__).resolve().parents[2]
PRESSURES=(0.,1.,3.,10.,30.,100.,200.)


def parameters(chemistry,fraction,pressure):
    p=runs.parameters(chemistry,fraction,.001,.3)
    return replace(p,base=replace(p.base,biology=replace(p.base.biology,atmosphere_pa=pressure)))


def fixed_temperature(p):
    def difference(t):
        pair=guilds(t-273.15,p.base.biology)
        return pair[0].rstar(p.base.biology.loss_h)-pair[1].rstar(p.base.biology.loss_h)
    grid=np.unique(np.r_[np.linspace(273.,303.15,301),277.15,288.15])
    values=[difference(t) for t in grid];roots=[]
    for a,b,fa,fb in zip(grid[:-1],grid[1:],values[:-1],values[1:]):
        if np.isfinite([fa,fb]).all() and fa*fb<0:
            value=float(brentq(difference,a,b,xtol=1e-12))
            if not any(abs(value-r)<1e-8 for r in roots):roots.append(value)
    return roots


def fixed_state(p,t):
    curve=core.response(p.base.climate.case)
    ratios=[float(a+(b-a)*(t-ta)/(tb-ta)) for a,b,ta,tb in zip(curve.ratios[:-1],curve.ratios[1:],curve.temperatures_k[:-1],curve.temperatures_k[1:])
            if tb<ta and tb<=t<=ta]
    if len(ratios)!=1:raise ArithmeticError('Need the one reference cooling-branch intersection')
    ratio=ratios[0];pair=guilds(t-273.15,p.base.biology);loss=p.base.biology.loss_h
    pressure=float(pair[0].rstar(loss))
    q=np.array([g.maintenance+loss/g.yield_g_mol for g in pair])
    cat=q-loss*np.array([g.assimilation_mol_g for g in pair])
    rec,export=core.recycling_rates(t,p.base);fraction=rec/(rec+export)
    abiotic=core.atmosphere(p.base.climate.case)['flux_to_ratio_per_yr']*p.base.climate.abiotic_flux
    methane=(p.base.loss.rate(ratio)-abiotic)/(core.inventory_to_ratio(p.base)*core.HOURS_PER_YEAR)
    captured=core.supply_h2(p.base)+p.base.biology.exchange_mol_l_h_pa*(p.base.biology.atmosphere_pa-pressure)
    biomass=np.linalg.solve(np.array([q,cat*np.array([fraction,1.])/4]),np.array([captured,methane]))
    acetate=core.HOURS_PER_YEAR*cat[0]*biomass[0]/(4*(rec+export))
    state=np.r_[pressure,biomass,acetate,ratio]
    cap_upper=np.inf if fraction==0 else q[0]*(4*methane/(fraction*cat[0]))
    cutoff=None if fraction==0 else float(pressure+(cap_upper-core.supply_h2(p.base))/p.base.biology.exchange_mol_l_h_pa)
    return state,dict(upper_reference_branch_pressure_pa=cutoff,
        captured_h2_mol_l_h=float(captured),atmospheric_h2_flux_mol_l_h=float(captured-core.supply_h2(p.base)))


def independent_flow(y,t,p):
    pair=list(guilds(t-273.15,p.base.biology))
    if p.chemistry=='products':
        pair[0]=replace(pair[0],threshold_pa=pair[0].threshold_pa*(y[3]/p.base.acetate_reference_mol_l)**.25)
        pair[1]=replace(pair[1],threshold_pa=pair[1].threshold_pa*(y[-1]*core.co2_pressure_pa(p.base.climate.case)/p.base.methane_reference_pa)**.25)
    q=np.array([g.uptake(y[0]) for g in pair]);growth=np.array([g.yield_g_mol*(v-g.maintenance) for g,v in zip(pair,q)])
    cat=q-np.array([g.assimilation_mol_g for g in pair])*np.maximum(growth,0.)
    rec,export=core.recycling_rates(t,p.base);year=core.HOURS_PER_YEAR
    abiotic=core.atmosphere(p.base.climate.case)['flux_to_ratio_per_yr']*p.base.climate.abiotic_flux
    return np.r_[year/core.HENRY_30C_MOL_L_PA*(core.supply_h2(p.base)-q@y[1:3]-p.base.biology.exchange_mol_l_h_pa*(y[0]-p.base.biology.atmosphere_pa)),
        year*y[1:3]*(growth-p.base.biology.loss_h),year*cat[0]*y[1]/4-(rec+export)*y[3],
        core.inventory_to_ratio(p.base)*(year*cat[1]*y[2]/4+rec*y[3])+abiotic-p.base.loss.rate(y[-1])]


def independent_builder(y,p):
    scale=model.state_scales(y,p);t=model.temperature(y[-1],p)
    a=np.zeros((5,5))
    for k in range(5):
        step=1e-4*scale[k];v=np.zeros(5);v[k]=step
        a[:,k]=(independent_flow(y-2*v,t,p)-8*independent_flow(y-v,t,p)+8*independent_flow(y+v,t,p)-independent_flow(y+2*v,t,p))/(12*step)
    step=1e-3
    b=(independent_flow(y,t-2*step,p)-8*independent_flow(y,t-step,p)+8*independent_flow(y,t+step,p)-independent_flow(y,t+2*step,p))/(12*step)
    curve=core.response(p.base.climate.case)
    j=int(np.searchsorted(curve.ratios,y[-1])-1)
    slope=float((curve.temperatures_k[j+1]-curve.temperatures_k[j])/(curve.ratios[j+1]-curve.ratios[j]))
    a=a*scale[None,:]/scale[:,None];b=b/scale
    def builder(tau):
        if tau==0:
            result=a.copy();result[:,-1]+=b*slope*scale[-1];return result
        result=np.zeros((6,6));result[:5,:5]=a;result[:5,5]=b
        result[5,4]=slope*scale[-1]/tau;result[5,5]=-1/tau
        return result
    return builder


def main():
    original=ROOT/'models/haze_world/review/atmospheric_h2_check.json'
    replay=Path('/tmp/terra-C59-replayed.json')
    expected=json.loads(original.read_text());actual=json.loads(replay.read_text())
    if actual!=expected:raise ArithmeticError('The unchanged source does not replay its committed results')
    rows=[];checks=[];fixed=[]
    for row in expected['rows']:
        p=parameters(row['chemistry'],row['fraction'],row['atmosphere_pa'])
        states=model.equilibrium_states(p)
        mixed=[r for r in states if r['kind']=='mixed']
        for r in mixed:
            state=r['y'];growth=model.biomass_per_capita(state,p)
            if r['status']!='accepted' or r['physiology_status']!='in_domain' or max(abs(growth.ravel()))>1e-7:
                raise ArithmeticError('Unqualified source root used in C59')
            rows.append(dict(chemistry=row['chemistry'],fraction=row['fraction'],atmosphere_pa=row['atmosphere_pa'],
                source_status=r['status'],physiology_status=r['physiology_status'],
                scaled_flow_residual_yr=r['residual'],per_cell_balance_residual_yr=float(max(abs(growth.ravel())))))
        if p.chemistry=='fixed':
            roots=fixed_temperature(p)
            if len(roots)!=1:raise ArithmeticError('Unexpected additional R-star crossing')
            y,metadata=fixed_state(p,roots[0])
            positive=bool(np.all(y[1:4]>0))
            if positive!=bool(mixed):raise ArithmeticError('Fixed independent balance and source inventory disagree')
            err=None if not positive else float(np.max(abs(y-mixed[0]['y'])/model.state_scales(y,p)))
            if err is not None and err>1e-8:raise ArithmeticError('Independent fixed mixture differs')
            fixed.append(dict(fraction=row['fraction'],atmosphere_pa=row['atmosphere_pa'],temperature_k=roots[0],
                local_h2_pa=float(y[0]),positive=positive,XA=float(y[1]),XM=float(y[2]),
                state_relative_error=err,**metadata))
        if mixed and row['atmosphere_pa']==100.:
            y=mixed[0]['y'];builder=independent_builder(y,p)
            def lead(tau):return float(max(eigvals(builder(tau)).real))
            if p.chemistry=='fixed':
                tau0=row['critical_lag_yr']
                tau=float(brentq(lead,tau0*.9,tau0*1.1,xtol=1e-10))
                error=tau/tau0-1
                if abs(error)>1e-4:raise ArithmeticError('Finite-difference critical lag differs')
                checks.append(dict(chemistry=p.chemistry,fraction=row['fraction'],atmosphere_pa=100.,
                    critical_lag_yr=tau,source_critical_lag_yr=tau0,relative_error=error))
            else:
                values={str(tau):lead(tau) for tau in (0.,1.,100.,1e4)}
                if max(values.values())>=0:raise ArithmeticError('Product stability spot check differs')
                checks.append(dict(chemistry=p.chemistry,fraction=row['fraction'],atmosphere_pa=100.,
                                   leading_real_yr=values,scope='Selected finite-lag checks; not all-lag stability'))
    names=[Path(__file__),original,ROOT/'models/haze_world/review/check_atmospheric_h2.py',
           ROOT/'src/terra_prisca/haze_world/dynamic_core.py',ROOT/'src/terra_prisca/haze_world/population_coupling.py',
           ROOT/'src/terra_prisca/haze_world/two_guilds.py',ROOT/'uv.lock']
    result=dict(source_rows=len(expected['rows']),replay_exact=True,mixed_roots=len(rows),qualified_roots=rows,
        fixed_independent=fixed,finite_difference_checks=checks,
        source_sha256={**runs.source_hashes(),**{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in names},
            'src/terra_prisca/haze_response/arney2016.py':sha256((ROOT/'src/terra_prisca/haze_response/arney2016.py').read_bytes()).hexdigest()},
        limitations=['Open prescribed atmospheric reservoir; gas exchange can import hydrogen.',
            'No photochemical hydrogen budget or Archean calibration.',
            'Fixed reference branch boundary is independently diagnosed; general root completeness is not proved.',
            'Products are tested on finite lag grids only.'])
    target=Path(__file__).with_suffix('.json');target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(rows=len(expected['rows']),qualified_mixed=len(rows),fd_checks=len(checks),
        reference_fixed_upper_pressure_pa=next(r['upper_reference_branch_pressure_pa'] for r in fixed if r['fraction']==.5))))


if __name__=='__main__':main()
