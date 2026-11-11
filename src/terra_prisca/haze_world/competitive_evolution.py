"""Joint kinetic adaptation and five-stock climate equilibria (S3–S5).

This named variant leaves the historical physical producer unchanged. Trait
fitness is evaluated in the resident environment, not selected on climate.
"""
from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from . import evolved_kinetics as kinetics
from . import population_coupling as reference

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'models/haze_world/figures/competitive_evolution'
LOSSES = (.0003, .001, .003)
ENERGIES = (0., .1, .2, .3, .45, .65)
FRACTIONS = (0., .5)
GROWTH_TOLERANCE_H = 1e-8


@lru_cache(maxsize=20000)
def best(t_k,biology,energy,interpolation):
    return kinetics.best_response(float(t_k),biology,energy,interpolation)


def parameters(loss_h, fraction):
    p = reference.reference()
    return replace(p, biology=replace(p.biology, loss_h=float(loss_h)), acetate_fraction=float(fraction))


def fluxes(y, p, traits):
    if p.activity_feedback != 'fixed':
        raise ValueError('The kinetic-evolution stage fixes product activities')
    pressure, xa, xm, acetate, ratio = np.asarray(y, dtype=float)
    temperature = float(reference.temperature_k(ratio, p.climate))
    pair = kinetics.guilds(temperature, p.biology, traits)
    biomass = np.array([xa, xm])*p.enabled
    uptake = np.array([g.uptake(pressure) for g in pair])
    synthesis = np.array([g.yield_g_mol*(q-g.maintenance) for g,q in zip(pair,uptake)])
    coefficients = np.array([g.assimilation_mol_g for g in pair])
    used = uptake*biomass*reference.HOURS_PER_YEAR
    assimilated = coefficients*np.maximum(synthesis,0.)*biomass*reference.HOURS_PER_YEAR
    catabolic = used-assimilated
    krec,kother = reference.recycling_rates(temperature,p)
    recycled,exported = krec*acetate,kother*acetate
    abiotic = reference.atmosphere(p.climate.case)['flux_to_ratio_per_yr']*p.climate.abiotic_flux
    return dict(temperature_k=temperature, pair=pair,
        supply_h2_mol_l_yr=reference.supply_h2(p)*reference.HOURS_PER_YEAR,
        uptake_h2_mol_l_yr=used,assimilation_h2_mol_l_yr=assimilated,
        catabolic_h2_mol_l_yr=catabolic,
        outlet_h2_mol_l_yr=p.biology.exchange_mol_l_h_pa*(pressure-p.biology.atmosphere_pa)*reference.HOURS_PER_YEAR,
        acetate_production_mol_l_yr=catabolic[0]/4,
        acetate_recycling_mol_l_yr=recycled,acetate_export_mol_l_yr=exported,
        biomass_export_h2_mol_l_yr=coefficients*(p.biology.loss_h+np.maximum(-synthesis,0.))*biomass*reference.HOURS_PER_YEAR,
        methane_source_ratio_yr=reference.inventory_to_ratio(p)*(catabolic[1]/4+recycled)+abiotic,
        methane_loss_ratio_yr=float(p.loss.rate(ratio)),abiotic_ratio_yr=abiotic,
        net_growth_yr=(synthesis-p.biology.loss_h)*reference.HOURS_PER_YEAR,
        k_rec_yr=krec,k_other_yr=kother)


def rhs(y,p,traits):
    f=fluxes(y,p,traits)
    return np.r_[(f['supply_h2_mol_l_yr']-sum(f['uptake_h2_mol_l_yr'])-f['outlet_h2_mol_l_yr'])/reference.HENRY_30C_MOL_L_PA,
        np.asarray(y)[1:3]*f['net_growth_yr']*p.enabled,
        f['acetate_production_mol_l_yr']-f['acetate_recycling_mol_l_yr']-f['acetate_export_mol_l_yr'],
        f['methane_source_ratio_yr']-f['methane_loss_ratio_yr']]


def redox_residual(y,p,traits):
    f=fluxes(y,p,traits);dy=rhs(y,p,traits)
    coefficients=np.array([g.assimilation_mol_g for g in f['pair']])
    conversion=reference.inventory_to_ratio(p)
    stored=reference.HENRY_30C_MOL_L_PA*dy[0]+coefficients@dy[1:3]+4*dy[3]+4*dy[4]/conversion
    external=f['supply_h2_mol_l_yr']-f['outlet_h2_mol_l_yr']-4*f['acetate_export_mol_l_yr']-sum(f['biomass_export_h2_mol_l_yr'])+4*(f['abiotic_ratio_yr']-f['methane_loss_ratio_yr'])/conversion
    return float(stored-external)


def roots(function,grid,atol=1e-10):
    values=[function(float(x)) for x in grid]
    found=[float(x) for x,v in zip(grid,values) if np.isfinite(v) and abs(v)<=atol]
    for a,b,fa,fb in zip(grid[:-1],grid[1:],values[:-1],values[1:]):
        if np.isfinite(fa) and np.isfinite(fb) and fa*fb<0:
            value=brentq(function,a,b,xtol=1e-12)
            if np.isfinite(function(value)) and abs(function(value))<max(atol*100,1e-7):found.append(value)
    unique=[]
    for value in sorted(found):
        if not unique or value-unique[-1]>1e-7:unique.append(value)
    return unique


def ratio_roots(temperature,p):
    grid=reference._ratio_grid(p,501)
    return roots(lambda r:float(reference.temperature_k(r,p.climate))-temperature,grid,1e-9)


def mixed_state(ratio,p,traits):
    temperature=float(reference.temperature_k(ratio,p.climate))
    pair=kinetics.guilds(temperature,p.biology,traits)
    pressures=np.array([g.rstar(p.biology.loss_h) for g in pair])
    if not np.all(np.isfinite(pressures)) or abs(pressures[0]-pressures[1])>1e-5:return None
    pressure=float(np.mean(pressures))
    captured=reference.supply_h2(p)-p.biology.exchange_mol_l_h_pa*(pressure-p.biology.atmosphere_pa)
    if captured<=0:return None
    required=np.array([g.maintenance+p.biology.loss_h/g.yield_g_mol for g in pair])
    fraction=1-np.array([g.assimilation_mol_g for g in pair])*p.biology.loss_h/required
    krec,kother=reference.recycling_rates(temperature,p)
    effective=krec/(krec+kother)
    abiotic=reference.atmosphere(p.climate.case)['flux_to_ratio_per_yr']*p.climate.abiotic_flux
    needed=(float(p.loss.rate(ratio))-abiotic)/(reference.inventory_to_ratio(p)*captured*reference.HOURS_PER_YEAR/4)
    denominator=effective*fraction[0]-fraction[1]
    if abs(denominator)<1e-12:return None
    share=(needed-fraction[1])/denominator
    if not 0<share<1:return None
    return np.r_[pressure,captured*np.array([share,1-share])/required,
        captured*reference.HOURS_PER_YEAR*share*fraction[0]/(4*(krec+kother)),ratio]


def resident_state(ratio,p,traits,index):
    temperature=float(reference.temperature_k(ratio,p.climate))
    pair=kinetics.guilds(temperature,p.biology,traits);g=pair[index]
    pressure=g.rstar(p.biology.loss_h)
    captured=reference.supply_h2(p)-p.biology.exchange_mol_l_h_pa*(pressure-p.biology.atmosphere_pa)
    if not np.isfinite(pressure) or captured<=0:return None
    biomass=np.zeros(2);biomass[index]=captured/float(g.uptake(pressure))
    state=np.r_[pressure,biomass,0.,ratio]
    f=fluxes(state,p,traits)
    state[3]=f['acetate_production_mol_l_yr']/(f['k_rec_yr']+f['k_other_yr'])
    return state


def jacobian(y,p,traits,step=1e-5,r_side=0):
    y=np.asarray(y);scale=np.maximum(abs(y),[10.,1e-4,1e-4,1e-5,.01])
    center=rhs(y,p,traits);columns=[]
    for j in range(5):
        delta=np.eye(5)[j]*scale[j]*step
        if j==4 and r_side:derivative=(rhs(y+r_side*delta,p,traits)-center)/(r_side*scale[j]*step)
        else:derivative=(rhs(y+delta,p,traits)-rhs(y-delta,p,traits))/(2*scale[j]*step)
        columns.append(derivative*scale[j]/scale)
    return np.column_stack(columns)


def climate_slope(ratio,p):
    response=reference.response(p.climate.case)
    if ratio<response.ratios[0]:
        h=max(1e-8,abs(ratio)*1e-5)
        return float((reference.temperature_k(ratio+h,p.climate)-reference.temperature_k(ratio-h,p.climate))/(2*h))
    if ratio>response.ratios[-1]:return 0.
    j=min(max(int(np.searchsorted(response.ratios,ratio,side='right'))-1,0),len(response.ratios)-2)
    return float((response.temperatures_k[j+1]-response.temperatures_k[j])/(response.ratios[j+1]-response.ratios[j]))


def describe(kind,y,p,traits):
    vertices=reference.response(p.climate.case).ratios
    sides=(-1,1) if np.any(np.isclose(y[-1],vertices,rtol=0,atol=1e-9)) else (0,)
    matrices=[jacobian(y,p,traits,step,side) for step in (1e-4,1e-5) for side in sides]
    spectra=[np.linalg.eigvals(matrix) for matrix in matrices]
    maximum=max(float(max(e.real)) for e in spectra)
    stable=maximum < -1e-8
    pairs=[v for e in spectra for v in e if v.imag>1e-7]
    leading=max(pairs,key=lambda z:z.real) if pairs else None
    temperature=float(reference.temperature_k(y[-1],p.climate))
    return dict(kind=kind,y=list(map(float,y)),temperature_k=temperature,ratio=float(y[-1]),
        stable=stable,stability='stable' if stable else 'unstable' if maximum>1e-8 else 'marginal',
        max_real_yr=maximum,jacobians_scaled=[matrix.tolist() for matrix in matrices],
        jacobian_steps=[1e-4,1e-5],jacobian_ratio_sides=list(sides),eigenvalues=[[[float(v.real),float(v.imag)] for v in e] for e in spectra],
        complex_period_yr=float(2*np.pi/leading.imag) if leading is not None else None,
        damping_time_yr=float(-1/leading.real) if leading is not None and leading.real<0 else None,
        quality_factor=float(leading.imag/(-2*leading.real)) if leading is not None and leading.real<0 else None,
        climate_domain=str(reference.domain(y[-1],p.climate)),climate_slope_k_per_ratio=climate_slope(y[-1],p),
        maximum_percapita_residual_h=float(max(abs(g.net_growth(y[0],p.biology.loss_h)) for i,g in enumerate(kinetics.guilds(temperature,p.biology,traits)) if y[i+1]>0)) if np.any(y[1:3]>0) else 0.,
        redox_residual=float(redox_residual(y,p,traits)))


def fixed_equilibria(p,traits,n_grid=501):
    grid=reference._ratio_grid(p,n_grid);states=[]
    abiotic=reference.atmosphere(p.climate.case)['flux_to_ratio_per_yr']*p.climate.abiotic_flux
    ratio=float(p.loss.inverse(abiotic));pressure=p.biology.atmosphere_pa+reference.supply_h2(p)/p.biology.exchange_mol_l_h_pa
    states.append(describe('lifeless',np.array([pressure,0.,0.,0.,ratio]),p,traits))
    for index,name in enumerate(('acetogen','methanogen')):
        def balance(r):
            state=resident_state(r,p,traits,index)
            return rhs(state,p,traits)[-1] if state is not None else np.nan
        for r in roots(balance,grid,1e-13):
            state=resident_state(r,p,traits,index)
            if state is not None:states.append(describe(name,state,p,traits))
    def difference(r):
        t=float(reference.temperature_k(r,p.climate));rs=[g.rstar(p.biology.loss_h) for g in kinetics.guilds(t,p.biology,traits)]
        return rs[0]-rs[1] if np.all(np.isfinite(rs)) else np.nan
    for r in roots(difference,grid):
        state=mixed_state(r,p,traits)
        if state is not None:states.append(describe('mixed',state,p,traits))
    return sorted(states,key=lambda r:(r['ratio'],r['kind']))


@lru_cache(maxsize=256)
def joint_temperatures(loss_h,energy_ev,interpolation):
    biology=parameters(loss_h,0.).biology
    def difference(t):
        result=best(float(t),biology,energy_ev,interpolation)
        a,m=result['rstars_pa'];return a-m if np.isfinite(a) and np.isfinite(m) else np.nan
    return tuple(roots(difference,np.linspace(273.15,303.15,601)))


def mutant_growth(position, index, y,p,traits):
    positions=list(traits.positions_c);positions[index]=float(position)
    mutant=replace(traits,positions_c=tuple(positions))
    g=kinetics.guilds(float(reference.temperature_k(y[-1],p.climate)),p.biology,mutant)[index]
    return float(g.net_growth(y[0],p.biology.loss_h))


def convergence(y,p,traits,best):
    t=float(reference.temperature_k(y[-1],p.climate));weights=y[1:3]/sum(y[1:3]);records=[]
    modes=[];curvatures=[];one_sided=[]
    for index,(u,detail) in enumerate(zip(traits.positions_c,best['guild_results'])):
        center=mutant_growth(u,index,y,p,traits);h=1e-3
        nodes=np.min(abs(kinetics.NODES_C-u))<1e-6
        kind=detail['kind']
        if kind=='interior' and not nodes:
            h=min(h,float(min(abs(kinetics.NODES_C-u)))/4,u-4.,30.-u)
            left=mutant_growth(u-h,index,y,p,traits);right=mutant_growth(u+h,index,y,p,traits)
            curvature=(left-2*center+right)/h**2
            modes.append('smooth');curvatures.append(curvature)
            one_sided.append(dict(left_slope=(center-left)/h,right_slope=(right-center)/h))
        else:
            left=(center-mutant_growth(u-h,index,y,p,traits))/h if u>4. else None
            right=(mutant_growth(u+h,index,y,p,traits)-center)/h if u<30. else None
            modes.append('projected_boundary' if kind.endswith('bound') else 'one_sided_node')
            curvatures.append(None);one_sided.append(dict(left_slope=left,right_slope=right))
    dp=1e-3
    def diff_at(temperature):
        a,m=[g.rstar(p.biology.loss_h) for g in kinetics.guilds(temperature,p.biology,traits)];return a-m
    thermal_slope=(diff_at(t+dp)-diff_at(t-dp))/(2*dp)
    for ratio in (.1,1.,10.):
        eigen=[];conditions=[]
        for index,(mode,curvature,slopes) in enumerate(zip(modes,curvatures,one_sided)):
            if mode=='smooth':
                eigen.append(float(weights[index]*(ratio if index==0 else 1.)*curvature));conditions.append(curvature < -1e-10)
            else:
                conditions.append((slopes['left_slope'] is None or slopes['left_slope']>1e-10) and (slopes['right_slope'] is None or slopes['right_slope'] < -1e-10))
        qualified=abs(thermal_slope)>1e-6 and all(conditions)
        records.append(dict(mutation_supply_a_over_m=ratio,convergence='attracting' if qualified else 'marginal_or_unqualified',
            canonical_eigenvalues=eigen if all(m=='smooth' for m in modes) else None,
            canonical_jacobian=np.diag(eigen).tolist() if all(m=='smooth' for m in modes) else None,
            resident_abundance_weights=weights.tolist(),fitness_curvatures_h_c2=curvatures,
            coordinate_kinds=modes,one_sided_selection=one_sided,thermal_crossing_slope_pa_k=float(thermal_slope),
            scope='Positive per-cell supply weights normalized by resident total cells; smooth ESS has zero first-order environment response. Nodes use inward one-sided selection, not an arbitrary Jacobian.'))
    return records


def invasion(y,p,traits,community_id):
    t=float(reference.temperature_k(y[-1],p.climate))
    positions,growth=kinetics.uptake_grid(y[0],t,p.biology,traits.energy_ev,traits.interpolation)
    rows=[]
    for index in range(2):
        j=int(np.argmax(growth[index]));maximum=float(growth[index,j])
        rows.append(dict(community_id=community_id,guild='a' if index==0 else 'm',
            mutants=len(positions),maximum_mutant_growth_h=maximum,best_grid_position_c=float(positions[j]),
            tolerance_h=GROWTH_TOLERANCE_H,passes=maximum<=GROWTH_TOLERANCE_H))
    return rows


def write_table(name,rows):
    OUT.mkdir(parents=True,exist_ok=True)
    fields=sorted(set(k for r in rows for k in r))
    with (OUT/name).open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator='\n');writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(v,sort_keys=True,separators=(',',':')) if isinstance(v,(dict,list,tuple)) else '' if v is None else v for k,v in row.items()})


def run_communities():
    communities=[];inventories=[];invasions=[]
    for loss in LOSSES:
      for energy in ENERGIES:
       for interpolation in kinetics.INTERPOLATIONS:
        temperatures=joint_temperatures(loss,energy,interpolation)
        for fraction in FRACTIONS:
            p=parameters(loss,fraction)
            setting=f'L{loss:g}_E{energy:g}_{interpolation}_f{fraction:g}'
            found=[]
            for temperature in temperatures:
                response_best=best(temperature,p.biology,energy,interpolation)
                if any(u is None for u in response_best['positions_c']):continue
                traits=kinetics.Traits(tuple(response_best['positions_c']),energy,interpolation)
                coarse=fixed_equilibria(p,traits,501)
                states=fixed_equilibria(p,traits,1001)
                inventory_agrees=len(coarse)==len(states) and all(a['kind']==b['kind'] and a['stability']==b['stability'] and abs(a['ratio']-b['ratio'])<1e-7 for a,b in zip(coarse,states))
                joint=[s for s in states if s['kind']=='mixed' and abs(s['temperature_k']-temperature)<1e-5]
                for j,state in enumerate(joint):
                    cid=f'{setting}_T{temperature:.9f}_{j}'
                    checks=invasion(np.asarray(state['y']),p,traits,cid);invasions.extend(checks)
                    conv=convergence(np.asarray(state['y']),p,traits,response_best) if state['stable'] else [dict(convergence='undefined_on_ecologically_unstable_branch',mutation_supply_a_over_m=r) for r in (.1,1.,10.)]
                    community=dict(setting_id=setting,community_id=cid,loss_h=loss,energy_ev=energy,
                        interpolation=interpolation,fraction=fraction,status='joint_community',
                        positions_c=traits.positions_c,optimum_kinds=[x['kind'] for x in response_best['guild_results']],
                        convergence=conv,S4_pass=all(c['passes'] for c in checks),
                        cooling_branch=state['climate_domain']=='arney' and state['climate_slope_k_per_ratio']<0,
                        **state)
                    found.append(community);communities.append(community)
                for state in states:
                    inventories.append(dict(setting_id=setting,trait_reference_temperature_k=temperature,
                        positions_c=traits.positions_c,grid_501_1001_agrees=inventory_agrees,**state))
            if not found:
                communities.append(dict(setting_id=setting,loss_h=loss,energy_ev=energy,
                    interpolation=interpolation,fraction=fraction,status='no_feasible_joint_community',
                    candidate_temperatures_k=list(temperatures),cooling_branch=False))
    write_table('communities.csv',communities);write_table('equilibria.csv',inventories);write_table('invasions.csv',invasions)
    return communities,inventories,invasions



@lru_cache(maxsize=4096)
def fixed_shape(biology,traits):
    v,k=kinetics.shape(np.asarray(traits.positions_c),biology,traits.interpolation)
    warm=kinetics.local_guilds(303.15,biology)
    return np.diag(v),np.diag(k),warm


def rstars_at_temperature(temperature,biology,traits):
    v,k,warm=fixed_shape(biology,traits)
    threshold=kinetics.reference.thresholds(float(temperature)-273.15,biology)
    maintenance=kinetics.reference.maintenance_factor(float(temperature)-273.15,biology.maintenance_energy_j)
    capacity=v*np.exp(-traits.energy_ev/kinetics.KB_EV*(1/float(temperature)-1/(np.asarray(traits.positions_c)+273.15)))
    required=np.array([g.maintenance*maintenance+biology.loss_h/g.yield_g_mol for g in warm])
    return np.asarray(threshold)+np.divide(k*required,capacity-required,out=np.full(2,np.inf),where=capacity>required)


def cooling_ratios(temperature,p):
    curve=reference.response(p.climate.case);out=[]
    for r0,r1,t0,t1 in zip(curve.ratios[:-1],curve.ratios[1:],curve.temperatures_k[:-1],curve.temperatures_k[1:]):
        if t1<t0 and t1-1e-8<=temperature<=t0+1e-8:
            value=float(r0+(temperature-t0)*(r1-r0)/(t1-t0))
            if not out or min(abs(value-z) for z in out)>1e-8:out.append(value)
    return out


def branch_state(p,traits,previous_temperature):
    def difference(t):
        r=rstars_at_temperature(t,p.biology,traits)
        return float(r[0]-r[1]) if np.all(np.isfinite(r)) else np.nan
    candidates=[]
    for radius in (.1,.5,2.,10.,30.):
        low=max(273.15,previous_temperature-radius);high=min(303.15,previous_temperature+radius)
        fl,fh=difference(low),difference(high)
        if np.isfinite(fl) and np.isfinite(fh) and fl*fh<0:
            candidates=[brentq(difference,low,high,xtol=1e-10)];break
    if not candidates:candidates=roots(difference,np.linspace(273.15,303.15,121))
    states=[]
    for t in candidates:
        for r in cooling_ratios(t,p):
            state=mixed_state(r,p,traits)
            if state is not None:states.append(state)
    return min(states,key=lambda y:abs(float(reference.temperature_k(y[-1],p.climate))-previous_temperature)) if states else None


def canonical_gradient(y,p,traits):
    gradient=[]
    for index,u in enumerate(traits.positions_c):
        h=1e-3;center=mutant_growth(u,index,y,p,traits)
        is_node=np.min(abs(kinetics.NODES_C-u))<1e-8
        if is_node:
            left=(center-mutant_growth(u-h,index,y,p,traits))/h if u>4. else None
            right=(mutant_growth(u+h,index,y,p,traits)-center)/h if u<30. else None
            if left is not None and right is not None and left<0<right:
                return None,'repelling_trait_corner'
            if left is not None and left<0:gradient.append(left)
            elif right is not None and right>0:gradient.append(right)
            else:gradient.append(0.)
        else:
            h=min(h,float(min(abs(kinetics.NODES_C-u)))/3,u-4.,30.-u)
            gradient.append((mutant_growth(u+h,index,y,p,traits)-mutant_growth(u-h,index,y,p,traits))/(2*h))
    weights=y[1:3]/sum(y[1:3])
    return weights*np.asarray(gradient),'projected_canonical'


def canonical_path(loss,energy,interpolation,fraction,max_trait_step=.025,max_steps=2000):
    p=parameters(loss,fraction)
    ref=reference.switch_temperatures(p.biology)
    start=min(ref,key=lambda t:abs(t-281.5)) if ref else None
    case=f'L{loss:g}_E{energy:g}_{interpolation}_f{fraction:g}'
    if start is None or not 4<=start-273.15<=30:
        return [dict(setting_id=case,status='no_measured_reference_start',max_trait_step_c=max_trait_step)]
    traits=kinetics.Traits((float(start-273.15),float(start-273.15)),energy,interpolation)
    temperature=start;clock=0.;rows=[];last_state=None;last_traits=None;last_clock=0.;maximum_temperature_step=0.
    for step in range(max_steps+1):
        y=branch_state(p,traits,temperature)
        if y is None:
            status='supported_mixed_branch_lost'
            break
        next_temperature=float(reference.temperature_k(y[-1],p.climate))
        maximum_temperature_step=max(maximum_temperature_step,abs(next_temperature-temperature))
        temperature=next_temperature
        ecological=describe('mixed',y,p,traits)
        if not ecological['stable']:
            status='stable_ecological_branch_lost';break
        last_state=y;last_traits=traits;last_clock=clock
        if step%10==0:
            rows.append(dict(setting_id=case,step=step,relative_evolution_time=clock,status='mixed_branch',
                max_trait_step_c=max_trait_step,temperature_k=temperature,positions_c=traits.positions_c,
                biomass_a_gdw_l=float(y[1]),biomass_m_gdw_l=float(y[2]),ratio=float(y[-1])))
        velocity,status=canonical_gradient(y,p,traits)
        if velocity is None:break
        speed=max(abs(velocity))
        if speed<1e-10:
            status='projected_stationary';break
        dt=max_trait_step/speed
        for index,v in enumerate(velocity):
            u=traits.positions_c[index]
            nodes=kinetics.NODES_C[(kinetics.NODES_C-u)*np.sign(v)>1e-8]
            if v and len(nodes):dt=min(dt,float(min(abs(nodes-u)))/abs(v))
        positions=np.clip(np.asarray(traits.positions_c)+dt*velocity,4.,30.)
        for index,u in enumerate(positions):
            node=kinetics.NODES_C[np.argmin(abs(kinetics.NODES_C-u))]
            if abs(u-node)<1e-8:positions[index]=node
        if max(abs(positions-np.asarray(traits.positions_c)))<1e-9:
            status='unresolved_trait_step';break
        traits=replace(traits,positions_c=tuple(map(float,positions)));clock+=dt
    else:status='bounded_path_not_converged'
    attempted=traits
    if last_state is not None:
        traits=last_traits;temperature=float(reference.temperature_k(last_state[-1],p.climate))
    end=dict(setting_id=case,step=step,relative_evolution_time=last_clock if last_state is not None else clock,status=status,max_trait_step_c=max_trait_step,
        attempted_positions_c=attempted.positions_c,attempted_relative_evolution_time=clock,maximum_temperature_step_k=maximum_temperature_step,
        temperature_k=temperature,positions_c=traits.positions_c,
        scope='Projected canonical coexistence branch; relative time uncalibrated. Branch loss is not a finite-demographic extinction event.')
    if last_state is not None:
        end.update(biomass_a_gdw_l=float(last_state[1]),biomass_m_gdw_l=float(last_state[2]),ratio=float(last_state[-1]))
    if status!='projected_stationary':
        alternatives=fixed_equilibria(p,attempted,301)
        end['stable_alternatives']=[dict(kind=r['kind'],temperature_k=r['temperature_k']) for r in alternatives if r['stable']]
    rows.append(end)
    return rows


def adapted_single_states(p,energy,interpolation):
    grid=reference._ratio_grid(p,301);rows=[]
    for index,name in enumerate(('acetogen','methanogen')):
        def balance(r):
            t=float(reference.temperature_k(r,p.climate));response_best=best(t,p.biology,energy,interpolation)
            if any(u is None for u in response_best['positions_c']):return np.nan
            traits=kinetics.Traits(tuple(response_best['positions_c']),energy,interpolation)
            y=resident_state(r,p,traits,index)
            return rhs(y,p,traits)[-1] if y is not None else np.nan
        for r in roots(balance,grid,1e-13):
            t=float(reference.temperature_k(r,p.climate));response_best=best(t,p.biology,energy,interpolation)
            traits=kinetics.Traits(tuple(response_best['positions_c']),energy,interpolation)
            y=resident_state(r,p,traits,index)
            if y is None:continue
            _,growth=kinetics.uptake_grid(y[0],t,p.biology,energy,interpolation)
            row=describe(name,y,p,traits)
            row.update(positions_c=traits.positions_c,maximum_each_guild_mutant_growth_h=list(map(float,np.max(growth,axis=1))),
                scope='Pure-resident best-response equilibrium; absent guild best response is an invasion assay, not selection in an absent population')
            rows.append(row)
    return rows


def run_paths(communities):
    grouped={}
    for c in communities:grouped.setdefault(c['setting_id'],[]).append(c)
    trigger={}
    for case,rows in grouped.items():
        valid=[c for c in rows if c['status']=='joint_community' and c['cooling_branch'] and c['stable']]
        if not valid or any(any(r['convergence']!='attracting' for r in c['convergence']) for c in valid):trigger[case]=rows[0]
    paths=[];single=[]
    for case,c in trigger.items():
        args=(c['loss_h'],c['energy_ev'],c['interpolation'],c['fraction'])
        for step in (.05,.025):paths.extend(canonical_path(*args,max_trait_step=step))
        p=parameters(c['loss_h'],c['fraction'])
        for row in adapted_single_states(p,c['energy_ev'],c['interpolation']):single.append(dict(setting_id=case,**row))
    write_table('paths.csv',paths);write_table('adapted_single.csv',single)
    return paths,single

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if not args.run:parser.print_help();return
    prerequisite=OUT/'best_response_manifest.json'
    prior=json.loads(prerequisite.read_text())
    sources=dict(prior['source_sha256'])
    sources[str(Path(__file__).relative_to(ROOT))]=sha256(Path(__file__).read_bytes()).hexdigest()
    for path,expected in sources.items():
        if sha256((ROOT/path).read_bytes()).hexdigest()!=expected:raise RuntimeError('Changed source after S1: '+path)
    communities,equilibria,invasions=run_communities()
    paths,single=run_paths(communities)
    if any(sha256((ROOT/path).read_bytes()).hexdigest()!=expected for path,expected in sources.items()):raise RuntimeError('Source changed during execution')
    data=dict(source_sha256=sources,prerequisite_manifest_sha256=sha256(prerequisite.read_bytes()).hexdigest(),
        protocol=dict(mutant_grid_step_c=.01,mutant_growth_tolerance_h=GROWTH_TOLERANCE_H,
        ecology_jacobian_steps=[1e-4,1e-5],canonical_mutation_a_over_m=[.1,1.,10.],
        path_max_trait_steps_c=[.05,.025],path_max_steps=2000,
        path_start='Both kinetic positions matched to the reference-switch local temperature',
        path_stop='Loss of supported stable mixed branch, checked every step, not demographic extinction'),settings=72,community_rows=len(communities),equilibrium_rows=len(equilibria),
        inventory_refinement_disagreements=sum(not r['grid_501_1001_agrees'] for r in equilibria),
        invasion_rows=len(invasions),path_rows=len(paths),adapted_single_rows=len(single),missing=sum(c['status']!='joint_community' for c in communities),
        scope='Joint stationary points, fixed-trait ecological Jacobians and recorded mutant grid; 501/1001 bracketing agreement does not prove absence of every tangent root or global attractor; no evolutionary time calibration',
        outputs={name:sha256((OUT/name).read_bytes()).hexdigest() for name in ('communities.csv','equilibria.csv','invasions.csv','paths.csv','adapted_single.csv')})
    (OUT/'communities_manifest.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps(data,indent=2))

if __name__=='__main__':main()
