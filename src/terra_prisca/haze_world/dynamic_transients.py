"""Homogeneous B2/B3 lagged trajectories and conditional first-window survival."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
from time import perf_counter

import numpy as np
from numpy.polynomial import Polynomial
from scipy.integrate import LSODA
from scipy.special import expit

from . import branching
from . import bottleneck
from . import dynamic_core as dynamic
from . import dynamic_realisation as static
from . import habitat_coupling as habitat
from . import habitat_integration as positive
from . import population_coupling as core
from .dense_roots import exit_time, real_roots
from .finite_experiments import initial_state, Case as InvasionCase
from .finite_populations import CellProcess

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Case:
    case_id: str
    stage: str
    chemistry: str
    fraction: float
    tau_yr: float
    direction: str = ''
    years: float = 100000.


def design():
    cases=[]
    for f, tau in ((0.,1.),(0.,10.),(0.,100.),(.5,10.),(.5,100.)):
        cases.append(Case(f'B2_f{f:g}_tau{tau:g}','B2','fixed',f,tau,years=30000.))
    for chemistry in ('fixed','products'):
        for f in (0.,.5):
            for tau in (0.,3.,30.):
                for direction in ('A_into_M','M_into_A'):
                    cases.append(Case(f'B3_{chemistry}_f{f:g}_tau{tau:g}_{direction}',
                                      'B3',chemistry,f,tau,direction))
    return cases


def parameters(case):
    return replace(core.reference(),acetate_fraction=case.fraction,activity_feedback=case.chemistry)


def initial(case):
    p=parameters(case)
    if case.stage=='B2':
        e=next(r for r in core.equilibrium_states(p) if r['kind']=='mixed' and r['stable'])
        y=e['y'].copy(); y[1]*=np.exp(.001)
        return y,float(e['t_k'])
    source=InvasionCase('dynamic_initial',case.chemistry,case.fraction,1.,0.,case.direction)
    y=initial_state(source)
    return y,float(core.temperature_k(y[4],p.climate))


class Coordinates(positive._Coordinates):
    def __init__(self,y,p,tau,temperature):
        super().__init__(y,habitat.Habitats(base=p))
        self.base=p;self.tau=tau;self.initial_temperature=temperature
        self.trial_source_extensions=0
        low=4. if p.biology.low_temperature_variant=='none' else -.15
        self.acetogen_capacity_bound=max(core.guilds(t,p.biology)[0].rate_scale
                                        for t in (low,4.,10.,15.,20.,25.,30.))

    def encode(self,physical,temperature=None):
        state=super().encode(physical)
        return np.r_[state,self.initial_temperature if temperature is None else temperature] if self.tau else state

    def actual_temperature(self,state):
        return float(state[5]) if self.tau else float(core.temperature_k(state[4],self.base.climate))

    def source_log(self,state,temperature_k=None):
        y,logs=self.decode(state)
        t=self.actual_temperature(state) if temperature_k is None else temperature_k
        f=core.fluxes_at_temperature(y,self.base,float(np.clip(t,273.,303.15)))
        coefficient=f['acetate_production_per_gdw_yr']
        return (np.log(coefficient)+logs[0,0]-np.log(positive.ACETATE_SCALE)+np.logaddexp(0.,-state[3])
                if self.acetate_positive[0] and coefficient>0 and np.isfinite(logs[0,0]) else -np.inf)

    def interval_source_bound(self,dense,left,right):
        if not self.acetate_positive[0] or not self.present[0,0]:return -np.inf
        if self.base.biology.kinetics!='saturating':raise ValueError('Source certificate requires bounded uptake')
        a,b=(left-dense.t)/dense.h,(right-dense.t)/dense.h
        extrema=[]
        for k in (1,3):
            poly=Polynomial(dense.yh[k]);xs=[a,b,*real_roots(poly.deriv(),a,b)]
            extrema.append([float(poly(x)) for x in xs])
        za=max(extrema[0]);zc=min(extrema[1])
        logsoft=za if za < -30 else np.log(np.logaddexp(0.,za))
        return float(np.log(core.HOURS_PER_YEAR*self.acetogen_capacity_bound/4)+np.log(positive.SCALE)
                     +logsoft-np.log(positive.ACETATE_SCALE)+np.logaddexp(0.,-zc)+1e-12)

    def derivative(self,_,state,temperature_k=None):
        y,logs=self.decode(state)
        t=self.actual_temperature(state) if temperature_k is None else float(temperature_k)
        # Boundary freezing belongs only to rejected solver trial states.
        trial_t=float(np.clip(t,273.,303.15))
        f=core.fluxes_at_temperature(y,self.base,trial_t)
        rates=np.r_[(f['supply_h2_mol_l_yr']-sum(f['uptake_h2_mol_l_yr'])-f['outlet_h2_mol_l_yr'])/core.HENRY_30C_MOL_L_PA,
                    y[1:3]*f['net_growth_yr'],
                    f['acetate_production_mol_l_yr']-f['acetate_recycling_mol_l_yr']-f['acetate_export_mol_l_yr'],
                    f['methane_source_ratio_yr']-f['methane_loss_ratio_yr']]
        for i in range(2):
            z=state[i+1]
            factor=1. if z < -30 else np.logaddexp(0.,z)/expit(z)
            rates[i+1]=f['net_growth_yr'][i]*factor if self.present[0,i] else 0.
        if self.acetate_positive[0]:
            z=state[3]
            coefficient=f['acetate_production_per_gdw_yr']
            source_log=(np.log(coefficient)+logs[0,0]-np.log(positive.ACETATE_SCALE)+np.logaddexp(0.,-z)
                        if coefficient>0 and np.isfinite(logs[0,0]) else -np.inf)
            if source_log>100:
                self.trial_source_extensions+=1
                source=np.exp(100.)*(1+source_log-100.)
            else:source=np.exp(source_log) if np.isfinite(source_log) else 0.
            factor=1. if z < -30 else np.logaddexp(0.,z)/expit(z)
            rates[3]=source-(f['k_rec_yr']+f['k_other_yr'])*factor
        if self.tau:
            rates=np.r_[rates,(core.temperature_k(y[4],self.base.climate)-t)/self.tau]
        return rates

    def jacobian(self,_,state):
        y,_=self.decode(state);t=float(np.clip(self.actual_temperature(state),273.,303.15))
        pair=core.activity_guilds_at_temperature(y,self.base,t)
        pressure,xa,xm,acetate,ratio=y
        uptake=np.array([g.uptake(pressure) for g in pair]);x=np.array([xa,xm])
        yields=np.array([g.yield_g_mol for g in pair]);assim=np.array([g.assimilation_mol_g for g in pair])
        synthesis=yields*(uptake-np.array([g.maintenance for g in pair]))
        derivative=np.zeros((2,len(state)))
        derivative[:,0]=[g.rate_scale*g.km_pa/(g.km_pa+pressure-g.threshold_pa)**2 if pressure>g.threshold_pa else 0. for g in pair]
        f=core.fluxes_at_temperature(y,self.base,t)
        s=np.zeros(5);factor=np.ones(4);factor_prime=np.zeros(4)
        for k in (1,2,3):
            z=state[k];e=expit(z);soft=np.logaddexp(0.,z)
            factor[k]=1. if z < -30 else soft/e
            factor_prime[k]=0. if z < -30 else 1-factor[k]*(1-e)
            s[k]=(positive.ACETATE_SCALE if k==3 else positive.SCALE)*e
        s[1:3]*=self.present[0]
        if self.base.activity_feedback=='products':
            derivative[0,3]=-derivative[0,0]*pair[0].threshold_pa/(4*factor[3])
            derivative[1,4]=-derivative[1,0]*pair[1].threshold_pa/(4*ratio)
        matrix=np.zeros((len(state),len(state)))
        matrix[0]=-core.HOURS_PER_YEAR/core.HENRY_30C_MOL_L_PA*(x@derivative)
        matrix[0,0]-=core.HOURS_PER_YEAR/core.HENRY_30C_MOL_L_PA*self.base.biology.exchange_mol_l_h_pa
        matrix[0,1:3]=-core.HOURS_PER_YEAR/core.HENRY_30C_MOL_L_PA*uptake*s[1:3]
        net=f['net_growth_yr']
        for i in range(2):
            if self.present[0,i]:
                matrix[i+1]=core.HOURS_PER_YEAR*yields[i]*derivative[i]*factor[i+1]
                matrix[i+1,i+1]+=net[i]*factor_prime[i+1]
        coefficient=f['acetate_production_per_gdw_yr']
        source_log=self.source_log(state,t)
        source=(np.exp(100.)*(1+source_log-100.) if source_log>100 else np.exp(source_log)) if np.isfinite(source_log) else 0.
        source_derivative=np.exp(100.) if source_log>100 else source
        if coefficient>0 and self.present[0,0]:
            grad=core.HOURS_PER_YEAR/4*(1-assim[0]*yields[0]*(synthesis[0]>0))*derivative[0]/coefficient
            grad[1]+=1/factor[1];grad[3]-=1-expit(state[3])
            matrix[3]=source_derivative*grad
        matrix[3,3]-=(f['k_rec_yr']+f['k_other_yr'])*factor_prime[3]
        conv=core.inventory_to_ratio(self.base)
        matrix[4]=conv*core.HOURS_PER_YEAR/4*xm*(1-assim[1]*yields[1]*(synthesis[1]>0))*derivative[1]
        matrix[4,2]+=conv*core.HOURS_PER_YEAR/4*(uptake[1]-assim[1]*max(synthesis[1],0.))*s[2]
        matrix[4,3]+=conv*f['k_rec_yr']*s[3]
        matrix[4,4]-=self.base.loss.slope(ratio)
        h=1e-4
        if t-2*h<273.:
            column=(-3*self.derivative(0.,state,t)+4*self.derivative(0.,state,t+h)-self.derivative(0.,state,t+2*h))/(2*h)
        elif t+2*h>303.15:
            column=(3*self.derivative(0.,state,t)-4*self.derivative(0.,state,t-h)+self.derivative(0.,state,t-2*h))/(2*h)
        else:column=(self.derivative(0.,state,t-2*h)-8*self.derivative(0.,state,t-h)+8*self.derivative(0.,state,t+h)-self.derivative(0.,state,t+2*h))/(12*h)
        slope=dynamic.climate_slope(ratio,dynamic.DynamicParams(self.base,self.base.activity_feedback))
        if self.tau:
            matrix[:5,5]=column[:5];matrix[5,4]=slope/self.tau;matrix[5,5]=-1/self.tau
        else:matrix[:,4]+=column*slope
        return matrix


def integrate(y0,p,years,tau=0.,temperature=None,*,census=False,rtol=2e-8,max_step=50.,sample_step=1.):
    if temperature is None:temperature=float(core.temperature_k(y0[4],p.climate))
    coords=Coordinates(np.asarray(y0,float),p,tau,temperature)
    state=coords.encode(np.asarray(y0,float),temperature)
    if not np.all(np.isfinite(state)):raise ValueError('Initial coordinates must be finite')
    process=CellProcess(); conversion=np.log(p.habitat_l_cm2*process.surface_cm2/process.cell_mass_gdw)
    times=[0.];ys=[np.asarray(y0,float).copy()]; logs=[np.log(y0[1:3])]; temps=[temperature]
    min_logs=np.log(y0[1:3]);min_times=np.zeros(2);first_cell=[None,None]
    minimum_y=np.tile(y0,(2,1));minimum_logs=np.tile(np.log(y0[1:3]),(2,1));minimum_temperature=np.full(2,temperature)
    extrema=[temperature,temperature];events=[];ranges=[]
    t=0.;next_sample=sample_step;next_census=10.;steps=resets=0;start=perf_counter();status='completed'
    dense_intervals=0;maximum_accepted_source_log=-np.inf;maximum_interval_source_bound=-np.inf;trial_extensions=0
    while t<years:
        solver=LSODA(coords.derivative,t,state,years,rtol=rtol,atol=np.r_[[1e-9,1e-9,1e-9,1e-10,1e-12],1e-8] if tau else [1e-9,1e-9,1e-9,1e-10,1e-12],max_step=max_step,
                     jac=coords.jacobian if coords.acetate_positive[0] else None)
        restart=False
        while solver.status=='running':
            left=float(solver.t);before=solver.y.copy();solver.step();steps+=1
            if solver.status=='failed':raise ArithmeticError('LSODA failed')
            if not np.all(np.isfinite(solver.y)):raise ArithmeticError('Accepted nonfinite coordinate')
            right=float(solver.t);dense=solver.dense_output()
            source_checks=[coords.source_log(before),coords.source_log(dense((left+right)/2)),coords.source_log(solver.y)]
            maximum_accepted_source_log=max(maximum_accepted_source_log,max(source_checks))
            if maximum_accepted_source_log>100:raise ArithmeticError('Trial chemical extension reached an accepted state')
            maximum_interval_source_bound=max(maximum_interval_source_bound,coords.interval_source_bound(dense,left,right))
            if maximum_interval_source_bound>100:raise ArithmeticError('Trial chemical extension not excluded on accepted interval')
            bound=exit_time(dense,left,right,(273.,303.15),5) if tau else positive._exit_time(dense,left,right,positive._ratio_interval(y0,coords.p),coords.p)
            end=min(right,bound) if bound is not None else right
            removal=None
            while census and next_census<=end+1e-10:
                cs=dense(next_census);cy,cl=coords.decode(cs)
                lost=[i for i in range(2) if coords.present[0,i] and cl[0,i]+conversion < -1e-12]
                if lost:
                    removal=(next_census,cs,cy,cl,lost);end=next_census;break
                next_census+=10.
            values,vt=positive._dense_minima(dense,left,end,coords,before)
            dense_intervals+=1
            for i in range(2):
                if coords.present[0,i] and values[0,i]<min_logs[i]:
                    min_logs[i]=values[0,i];min_times[i]=vt[0,i]
                    ms=dense(vt[0,i]);my,ml=coords.decode(ms)
                    minimum_y[i]=my;minimum_logs[i]=ml[0];minimum_temperature[i]=coords.actual_temperature(ms)
                if coords.present[0,i] and first_cell[i] is None:
                    floor_z=positive._inverse(np.exp(-conversion)/positive.SCALE)
                    poly=Polynomial(dense.yh[i+1])-floor_z
                    for x in real_roots(poly,(left-dense.t)/dense.h,(end-dense.t)/dense.h):
                        when=float(dense.t+dense.h*x)
                        if when>=left-1e-9:first_cell[i]=when;break
            if tau:
                poly=Polynomial(dense.yh[5]);a,b=(left-dense.t)/dense.h,(end-dense.t)/dense.h
                tv=[poly(v) for v in [a,b,*real_roots(poly.deriv(),a,b)]]
                low,high=float(min(tv)),float(max(tv))
            else:low,high=positive._dense_temperature_range(dense,left,end,coords.p)
            extrema[0]=min(extrema[0],low);extrema[1]=max(extrema[1],high)
            ranges.append((left,end,low,high))
            while next_sample<=end+1e-10:
                s=dense(min(next_sample,end));yy,ll=coords.decode(s)
                times.append(float(min(next_sample,end)));ys.append(yy);logs.append(ll[0]);temps.append(coords.actual_temperature(s));next_sample+=sample_step
            state=dense(end);t=float(end)
            yy,ll=coords.decode(state)
            if yy[0]<-1e-8 or yy[3]<-1e-12 or yy[4]<-1e-12:raise ArithmeticError('Accepted negative chemical stock')
            if removal:
                _,state,yy,ll,lost=removal
                for i in lost:
                    events.append(dict(time_yr=t,guild=i,log_removed_cells=float(ll[0,i]+conversion)))
                    yy[i+1]=0.
                temp=coords.actual_temperature(state);trial_extensions+=coords.trial_source_extensions
                coords=Coordinates(yy,p,tau,temp);state=coords.encode(yy,temp)
                next_census=t+10.;restart=True;resets+=1
                if times[-1]==t:ys[-1]=yy;logs[-1]=coords.decode(state)[1][0]
                else:times.append(t);ys.append(yy);logs.append(coords.decode(state)[1][0]);temps.append(temp)
                break
            if bound is not None:
                status='domain_censored';break
            if not coords.acetate_positive[0] and yy[3]>0:
                temp=coords.actual_temperature(state);trial_extensions+=coords.trial_source_extensions
                coords=Coordinates(yy,p,tau,temp);state=coords.encode(yy,temp)
                restart=True;resets+=1;break
        if status!='completed':break
        if not restart:
            t=float(solver.t);state=solver.y.copy()
    yy,ll=coords.decode(state);temp=coords.actual_temperature(state)
    if times[-1]!=t:times.append(t);ys.append(yy);logs.append(ll[0]);temps.append(temp)
    return dict(t=np.array(times),y=np.array(ys).T,log_biomass=np.array(logs).T,temperature_k=np.array(temps),
                min_log_biomass=min_logs,min_times_yr=min_times,first_below_cell_yr=first_cell,
                minimum_y=minimum_y,minimum_logs=minimum_logs,minimum_temperature=minimum_temperature,
                global_log_cell_conversion=conversion,temperature_range_k=extrema,step_temperature_ranges=np.array(ranges),
                status=status,events=events,steps=steps,resets=resets,dense_intervals=dense_intervals,
                maximum_accepted_source_log=maximum_accepted_source_log,
                maximum_interval_source_bound=maximum_interval_source_bound,
                rejected_trial_source_extensions=trial_extensions+coords.trial_source_extensions,
                wall_seconds=perf_counter()-start)


def rates(result,p,guild):
    if 'birth_yr' not in result:
        birth=[];death=[];fractions=[]
        for j,t in enumerate(result['temperature_k']):
            y=result['y'][:,j];gs=core.activity_guilds_at_temperature(y,p,float(t))
            uptake=np.array([g.uptake(y[0]) for g in gs]);amount=uptake*y[1:3]
            synthesis=np.array([g.yield_g_mol*(q-g.maintenance) for g,q in zip(gs,uptake)])
            birth.append(np.maximum(synthesis,0.)*core.HOURS_PER_YEAR)
            death.append((p.biology.loss_h+np.maximum(-synthesis,0.))*core.HOURS_PER_YEAR)
            fractions.append(amount/sum(amount) if sum(amount)>0 else np.zeros(2))
        result['birth_yr']=np.array(birth).T;result['death_yr']=np.array(death).T;result['uptake_fraction']=np.array(fractions).T
    return result['birth_yr'][guild],result['death_yr'][guild],result['uptake_fraction'][guild]


def first_window(result,p,guild):
    t=result['t'];log_counts=result['log_biomass'][guild]+result['global_log_cell_conversion']
    minimum=float(result['min_log_biomass'][guild]+result['global_log_cell_conversion'])
    threshold=min(np.log(1e16),minimum+np.log(1e8));prescribed=threshold;reductions=0
    birth,death,fraction=rates(result,p,guild)
    windows=bottleneck.excursions(log_counts,threshold)
    while windows and max(np.max(fraction[a:b+1]) for a,b,_ in windows)>1e-10:
        threshold-=np.log(10.);reductions+=1;windows=bottleneck.excursions(log_counts,threshold)
    if not windows:return dict(status='no_locally_rare_window',probability=None,threshold_reductions=reductions)
    lo,hi,terminal=windows[0]
    selected=np.arange(lo,hi+1)
    logu=branching.backward_survival(t[selected],birth[selected,None],death[selected,None],np.zeros((1,1)),
                                    rtol=1e-10,atol=1e-12,max_step=1.)
    value=branching.lineages(np.array([log_counts[lo]]),logu)
    other=result['first_below_cell_yr'][1-guild]
    own=result['first_below_cell_yr'][guild]
    return dict(status='terminal_window_censored' if terminal else 'closed_first_rare_window',
                start_yr=float(t[lo]),end_yr=float(t[hi]),terminal=terminal,
                prescribed_log_threshold=float(prescribed),log_threshold=float(threshold),threshold_reductions=reductions,
                max_uptake_fraction=float(np.max(fraction[selected])),
                log_entry_cells=float(log_counts[lo]),log_type_survival=float(logu[0]),
                log_survival_probability=bottleneck._log_probability(value['log_lambda']),
                downstream_of_other_guild_below_one=bool(other is not None and other<t[lo]),
                downstream_of_own_guild_below_one=bool(own is not None and own<t[lo]),
                probability_scope='First rare window in recorded exogenous environment, not joint recovery or indefinite persistence',
                **value)


def clean(value):
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(np.ndarray,list,tuple)):return [clean(v) for v in value]
    if isinstance(value,np.generic):return clean(value.item())
    if isinstance(value,float) and not np.isfinite(value):return None
    return value


def hashes():
    paths=[Path(__file__),Path(core.__file__),Path(positive.__file__),Path(branching.__file__),Path(bottleneck.__file__),
           ROOT/'src/terra_prisca/haze_world/habitat_coupling.py',ROOT/'src/terra_prisca/haze_world/finite_populations.py',
           ROOT/'src/terra_prisca/haze_world/dense_roots.py',ROOT/'src/terra_prisca/haze_world/two_guilds.py',
           ROOT/'src/terra_prisca/haze_world/hydrogen_uptake.py',ROOT/'src/terra_prisca/haze_world/woodii1998.py',
           ROOT/'src/terra_prisca/haze_world/methane_budget.py',ROOT/'src/terra_prisca/haze_world/finite_experiments.py',
           ROOT/'src/terra_prisca/haze_world/darwinian.py',
           ROOT/'models/haze_world/dynamic-realisation-spec.md',ROOT/'models/haze_world/continuum-habitats-spec.md',
           ROOT/'models/haze_world/continuum-habitats-methods.md',
           ROOT/'models/haze_world/evidence/kotsyurbenko2001_table2.csv',
           ROOT/'models/haze_response/arney2016/figure4.csv',ROOT/'models/haze_response/arney2016/cases.csv',ROOT/'uv.lock']
    return {str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in paths}


def save_raw(path,result):
    arrays={k:v for k,v in result.items() if isinstance(v,np.ndarray)}
    np.savez_compressed(path,**arrays)
    return sha256(path.read_bytes()).hexdigest()


def run_case(case,raw,rtol=2e-8,max_step=50.,sample_step=1.):
    source=hashes();protocol=dict(case=asdict(case),rtol=rtol,max_step=max_step,sample_step=sample_step,source_sha256=source)
    epoch=raw/'source_epochs'/sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()[:20]
    for name,digest in source.items():
        target=epoch/name
        if not target.exists():
            target.parent.mkdir(parents=True,exist_ok=True)
            temporary=target.with_name(target.name+f'.{os.getpid()}.tmp')
            shutil.copyfile(ROOT/name,temporary);os.replace(temporary,target)
        if sha256(target.read_bytes()).hexdigest()!=digest:raise ArithmeticError('Producer epoch differs from declared source')
    fingerprint=sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest()[:20]
    receipt_path=raw/f'{case.case_id}-{fingerprint}.json'
    if receipt_path.exists():return json.loads(receipt_path.read_text())
    y,t=initial(case);p=parameters(case)
    unc=integrate(y,p,case.years,case.tau_yr,t,rtol=rtol,max_step=max_step,sample_step=sample_step)
    logs=(unc['min_log_biomass']+unc['global_log_cell_conversion'])/np.log(10.)
    late=unc['t']>=.8*unc['t'][-1]
    row=dict(case_id=case.case_id,stage=case.stage,chemistry=case.chemistry,fraction=case.fraction,
             tau_yr=case.tau_yr,direction=case.direction,status=unc['status'],horizon_yr=float(unc['t'][-1]),
             acetogen_log10_min_cells=float(logs[0]),methanogen_log10_min_cells=float(logs[1]),
             acetogen_min_time_yr=float(unc['min_times_yr'][0]),methanogen_min_time_yr=float(unc['min_times_yr'][1]),
             first_acetogen_below_cell_yr=unc['first_below_cell_yr'][0],first_methanogen_below_cell_yr=unc['first_below_cell_yr'][1],
             peak_temperature_k=unc['temperature_range_k'][1],minimum_temperature_k=unc['temperature_range_k'][0],
             final_window_temperature_span_k=float(np.ptp(unc['temperature_k'][late])))
    spans=[]
    for left,right in zip(np.linspace(.6*unc['t'][-1],unc['t'][-1],5)[:-1],np.linspace(.6*unc['t'][-1],unc['t'][-1],5)[1:]):
        z=unc['temperature_k'][(unc['t']>=left)&(unc['t']<=right)]
        spans.append(float(np.ptp(z)))
    envelope=('growing_final_windows' if spans[-1]>1.05*max(spans[-2],1e-6) else
              'bounded_over_observed_final_windows' if abs(spans[-1]-spans[-2])<=.05*max(spans[-2],1e-6) else
              'changing_finite_envelope')
    row.update(envelope_class=envelope,late_window_spans=json.dumps(spans),
               below_one_cell_anywhere=bool(min(logs)<0),envelope_scope='Finite observed windows, not an attracting-cycle or boundedness theorem')
    windows={name:first_window(unc,p,g) for g,name in enumerate(('acetogen','methanogen'))}
    filepath=raw/f'{case.case_id}-{fingerprint}.npz';digest=save_raw(filepath,unc)
    row.update(uncensored_raw=str(filepath.relative_to(ROOT)),uncensored_sha256=digest)
    for g,name in enumerate(('acetogen','methanogen')):
        probability=windows[name]
        for k in ('status','survival_probability','log_survival_probability','start_yr','end_yr','downstream_of_other_guild_below_one','downstream_of_own_guild_below_one'):
            row[name+'_first_window_'+k]=probability.get(k)
    finite=None
    if case.stage=='B3':
        finite=integrate(y,p,case.years,case.tau_yr,t,census=True,rtol=rtol,max_step=max_step,sample_step=sample_step)
        fp=raw/f'{case.case_id}-{fingerprint}-census.npz';fh=save_raw(fp,finite)
        present=np.isfinite(finite['log_biomass'][:,-1])
        row.update(census_status=finite['status'],census_endpoint=('both' if all(present) else 'acetogen_only' if present[0] else 'methanogen_only' if present[1] else 'empty'),
                   census_horizon_yr=float(finite['t'][-1]),census_final_temperature_k=float(finite['temperature_k'][-1]),
                   census_raw=str(fp.relative_to(ROOT)),census_sha256=fh,census_events=json.dumps(finite['events']))
    receipt=dict(protocol=protocol,row=row,uncensored_metadata={k:v for k,v in unc.items() if not isinstance(v,np.ndarray)},
                 first_windows=windows,
                 census_metadata={k:v for k,v in finite.items() if not isinstance(v,np.ndarray)} if finite else None)
    receipt_path.write_text(json.dumps(clean(receipt),indent=2,allow_nan=False)+'\n')
    return clean(receipt)


def export_trace(receipt,output):
    row=receipt['row'];data=np.load(ROOT/row['uncensored_raw'])
    t=data['t'];horizon=t[-1]
    chosen=np.flatnonzero((t<=200)|((t>=horizon-2000)&np.isclose(t/5,np.rint(t/5)))|np.isclose(t/500,np.rint(t/500)))
    conversion=receipt['uncensored_metadata']['global_log_cell_conversion']
    records=[]
    for j in chosen:
        y=data['y'][:,j];logs=data['log_biomass'][:,j]
        records.append(dict(time_yr=t[j],hydrogen_pa=y[0],acetogens_gdw_l=y[1],methanogens_gdw_l=y[2],
             acetate_mol_l=y[3],methane_ratio=y[4],temperature_k=data['temperature_k'][j],
             log10_acetogen_cells=(logs[0]+conversion)/np.log(10.),log10_methanogen_cells=(logs[1]+conversion)/np.log(10.),
             sample_kind='original_1yr_sample'))
    for i in range(2):
        y=data['minimum_y'][i];logs=data['minimum_logs'][i]
        records.append(dict(time_yr=data['min_times_yr'][i],hydrogen_pa=y[0],acetogens_gdw_l=y[1],methanogens_gdw_l=y[2],
             acetate_mol_l=y[3],methane_ratio=y[4],temperature_k=data['minimum_temperature'][i],
             log10_acetogen_cells=(logs[0]+conversion)/np.log(10.),log10_methanogen_cells=(logs[1]+conversion)/np.log(10.),
             sample_kind='checked_dense_minimum_'+str(i)))
    records.sort(key=lambda r:r['time_yr']);static.write_csv(output/('transient_'+row['case_id']+'.csv'),records)


def run(output,raw,workers=2,limit=None):
    output.mkdir(parents=True,exist_ok=True);raw.mkdir(parents=True,exist_ok=True)
    cases=design()[:limit] if limit else design();receipts=[];failures=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(run_case,c,raw):c for c in cases}
        for f in as_completed(futures):
            try:
                value=f.result();receipts.append(value);print(value['row']['case_id'],'complete',flush=True)
            except Exception as error:
                failure=dict(case=asdict(futures[f]),exception=type(error).__name__,message=str(error))
                failures.append(failure);print(futures[f].case_id,'UNQUALIFIED',type(error).__name__,str(error),flush=True)
    if failures:
        (raw/'failures_latest.json').write_text(json.dumps(dict(source_sha256=hashes(),failures=failures),indent=2)+'\n')
        raise ArithmeticError(f'{len(failures)} transient cases lack qualified completion; public result tables not updated')
    for stage,name in (('B2','oscillations.csv'),('B3','invasions.csv')):
        rows=[r['row'] for r in receipts if r['row']['stage']==stage]
        rows.sort(key=lambda r:r['case_id'])
        if rows:static.write_csv(output/name,rows)
    selected={'B2_f0_tau1','B2_f0_tau100','B2_f0.5_tau10',
              'B3_fixed_f0.5_tau3_A_into_M','B3_fixed_f0.5_tau3_M_into_A',
              'B3_products_f0.5_tau3_A_into_M','B3_products_f0.5_tau3_M_into_A'}
    for receipt in receipts:
        if receipt['row']['case_id'] in selected:export_trace(receipt,output)
    manifest=dict(source_sha256=hashes(),cases=len(receipts),rows=[r['row'] for r in receipts],
                  scope='Homogeneous B2/B3; conditional first rare windows, dense continuum minima and separate finite-census endpoints')
    (output/'transient_manifest.json').write_text(json.dumps(clean(manifest),indent=2,allow_nan=False)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'models/haze_world/figures/dynamic_realisation')
    parser.add_argument('--raw',type=Path,default=ROOT/'local/haze/dynamic_transients')
    parser.add_argument('--workers',type=int,default=2);parser.add_argument('--limit',type=int)
    args=parser.parse_args();run(args.output,args.raw,args.workers,args.limit)


if __name__=='__main__':main()
