"""Accepted-step integration of active/dormant pools with explicit absence.

Each isolated habitat, or each dispersing metapopulation, uses a logarithmic
total guild stock and two explicit stage allocations per habitat. This keeps
the total through deep bottlenecks and starts dormant pools at exactly zero.
"""

from dataclasses import dataclass
from time import perf_counter

import numpy as np
from numpy.polynomial import Polynomial
from scipy.special import expit, logsumexp

from . import dormancy as model
from . import habitat_integration as old
from .bottleneck_integration import _RetryingLSODA

Census = old.Census
SCALE = old.SCALE
STAGE_POSITIVE_ENTRY_AGE_YR = 1e-6
STAGE_LINEAR_RATE_YR = 1e8


@dataclass
class DormancyResult(old.HabitatResult):
    log_active: np.ndarray
    log_dormant: np.ndarray


class _StageSourceOverflow(RuntimeError):
    def __init__(self,index):
        super().__init__(f"Stage source exceeds representable coordinate range at {index}")
        self.index=index


class _Coordinates:
    def __init__(self, initial, p):
        self.p, self.m = p, p.state_size
        self.shared = p.dispersal_yr > 0 and np.count_nonzero(p.weights) > 1
        self.groups = []
        for i in range(2):
            patches = [np.flatnonzero(p.weights > 0)] if self.shared else [[j] for j,w in enumerate(p.weights) if w]
            for js in patches:
                nodes = [(int(j), s) for j in js for s in (0,1)]
                indices = np.array([6*j+1+i if s == 0 else 6*j+4+i for j,s in nodes])
                weights = np.array([p.weights[j] if self.shared else 1. for j,s in nodes])
                present = bool(np.any(initial[indices] > 0))
                migration=np.array([[p.dispersal_yr*p.weights[k] if j!=k and s==ss else 0.
                                     for k,ss in nodes] for j,s in nodes])
                self.groups.append(dict(guild=i, nodes=nodes, indices=indices, weights=weights, present=present,migration=migration))
        self.acetate_positive = (initial[3:p.state_size-1:6] > 0) & (p.weights > 0)
        self.stage_positive=np.zeros(self.m,dtype=bool)
        self.stage_positive[np.r_[p.biomass_indices.ravel(),p.dormant_indices.ravel()]]=initial[np.r_[p.biomass_indices.ravel(),p.dormant_indices.ravel()]]>0

    def allocations(self,state,g):
        ix=g["indices"];positive=self.stage_positive[ix];values=state[ix].copy()
        values[positive]=values[positive]**2
        logs=np.full(len(ix),-np.inf)
        with np.errstate(divide="ignore"):
            logs[positive]=2*np.log(abs(state[ix[positive]]))
        use=(~positive)&(values>0);logs[use]=np.log(values[use])
        return values,logs

    def encode(self, physical):
        state = np.r_[physical, np.zeros(len(self.groups))]
        for k,g in enumerate(self.groups):
            total = float(g["weights"] @ physical[g["indices"]])
            if g["present"]:
                state[self.m+k] = old._inverse(total/SCALE)
                state[g["indices"]] = g["weights"]*physical[g["indices"]]/total
                positive=self.stage_positive[g["indices"]]
                state[g["indices"][positive]]=np.sqrt(state[g["indices"][positive]])
            else: state[g["indices"]] = 0.
        for j, positive in enumerate(self.acetate_positive):
            if positive: state[6*j+3] = old._inverse(physical[6*j+3]/old.ACETATE_SCALE)
        return state

    def decode(self, state):
        physical = np.asarray(state[:self.m]).copy()
        stages = np.full((self.p.n_patches,2,2), -np.inf)
        for k,g in enumerate(self.groups):
            if not g["present"]:
                physical[g["indices"]] = 0.; continue
            h,log_h = self.allocations(state,g); total_h = float(sum(h))
            if total_h <= 0: raise RuntimeError("Stage allocation normalizer must be positive")
            z = state[self.m+k]
            physical[g["indices"]] = SCALE*np.logaddexp(0.,z)*h/(total_h*g["weights"])
            for logh,w,(j,s) in zip(log_h,g["weights"],g["nodes"]):
                if np.isfinite(logh):
                    stages[j,g["guild"],s] = old._log_softplus(z)+logh-np.log(total_h)-np.log(w)
        for j, positive in enumerate(self.acetate_positive):
            if positive: physical[6*j+3] = old.ACETATE_SCALE*np.logaddexp(0.,state[6*j+3])
        return physical, stages

    def global_logs(self, state):
        stages = self.decode(state)[1]
        active = self.p.weights > 0
        return logsumexp(stages[active]+np.log(self.p.weights[active,None,None]), axis=(0,2))

    def derivative(self, time, state):
        physical, stages = self.decode(state)
        f = model.fluxes(physical,self.p,trial_extension=True)
        rates = np.r_[model._rhs_from_fluxes(physical,self.p,f), np.zeros(len(self.groups))]
        for j, positive in enumerate(self.acetate_positive):
            if not positive: continue
            local = f["local"][j]; z = state[6*j+3]
            coefficient = local["acetate_production_per_gdw_yr"]
            production = local["acetate_production_mol_l_yr"]
            log_production = (np.log(production) if production > 0 else
                np.log(coefficient)+stages[j,0,0] if coefficient > 0 and np.isfinite(stages[j,0,0]) else -np.inf)
            difference = log_production-(np.log(old.ACETATE_SCALE)-np.logaddexp(0.,-z))
            if difference > np.log(np.finfo(float).max):
                raise RuntimeError("Acetate source exceeds the representable coordinate range")
            source = np.exp(difference) if np.isfinite(difference) else 0.
            factor = 1. if z < -30 else np.logaddexp(0.,z)/expit(z)
            rates[6*j+3] = source-(local["k_rec_yr"]+local["k_other_yr"])*factor
        for k,g in enumerate(self.groups):
            ix = g["indices"]
            if not g["present"]:
                rates[ix] = 0.; rates[self.m+k] = 0.; continue
            h,log_h = self.allocations(state,g); normalizer = float(sum(h)); i = g["guild"]
            growth = np.array([f["net_growth_yr"][j,i] if s == 0 else -f["dormant_loss_yr"] for j,s in g["nodes"]])
            mean = float(h @ growth/normalizer)
            q = g["migration"].copy()
            for a,(j,s) in enumerate(g["nodes"]):
                for b,(kk,ss) in enumerate(g["nodes"]):
                    if j == kk and s != ss: q[a,b] = f["sigma_yr"][j,i] if s == 0 else f["rho_yr"][j,i]
            rates[ix] = h*(growth-mean)+q.T@h-q.sum(axis=1)*h
            for a,index in enumerate(ix):
                if not self.stage_positive[index]:continue
                z=state[index]
                incoming=q[:,a]>0
                log_source=float(logsumexp(np.log(q[incoming,a])+log_h[incoming])) if np.any(incoming) else -np.inf
                if z == 0:
                    if np.isfinite(log_source):raise _StageSourceOverflow(int(index))
                    rates[index]=0.;continue
                difference=log_source-np.log(abs(z))-np.log(2.)
                if difference>np.log(np.finfo(float).max):raise _StageSourceOverflow(int(index))
                source=np.exp(difference) if np.isfinite(difference) else 0.
                rates[index]=.5*(growth[a]-mean-q[a].sum())*z+np.sign(z)*source
            z = state[self.m+k]
            rates[self.m+k] = mean*(1. if z < -30 else np.logaddexp(0.,z)/expit(z))
        return rates


def _log_totals(stages): return logsumexp(stages,axis=2)


def _points(dense,left,right,indices):
    lo,hi = (left-dense.t)/dense.h,(right-dense.t)/dense.h
    points = [lo,hi]
    for index in indices:
        poly = Polynomial(dense.yh[index])
        points.extend(old._real_roots(poly.deriv(),lo,hi))
    return lo,hi,np.unique(points)


def _positive_piece(dense,left,right,coords,start):
    lo,hi = (left-dense.t)/dense.h,(right-dense.t)/dense.h
    indices = [*range(0,coords.m-1,6),coords.m-1]
    indices += [6*j+3 for j,w in enumerate(coords.p.weights) if w and not coords.acetate_positive[j]]
    indices += [int(i) for g in coords.groups if g["present"] for i in g["indices"] if not coords.stage_positive[i]]
    for i in indices:
        poly = Polynomial(dense.yh[i])
        radius=max(abs(lo),abs(hi))
        if poly.coef[0]-sum(abs(poly.coef[k])*radius**k for k in range(1,len(poly.coef)))>=0:
            continue
        points=[hi,*[x for x in old._real_roots(poly.deriv(),lo,hi) if lo<x<hi]]
        if min([start[i],*[float(poly(x)) for x in points]]) < 0: return False
    return True


def _poly_bounds(poly,lo,hi,initial):
    radius=max(abs(lo),abs(hi));delta=sum(abs(poly.coef[k])*radius**k for k in range(1,len(poly.coef)))
    error=32*np.finfo(float).eps*(abs(poly.coef[0])+delta+abs(initial)+1e-300)
    return min(poly.coef[0]-delta,initial)-error,max(poly.coef[0]+delta,initial)+error


def _dense_minima(dense,left,right,coords,start,previous=None):
    n = coords.p.n_patches
    values,at = np.full((n,2),-np.inf),np.full((n,2),left)
    global_values,global_at = np.full(2,-np.inf),np.full(2,left)
    lo,hi=(left-dense.t)/dense.h,(right-dense.t)/dense.h
    initial=coords.decode(start)[1];local_initial=_log_totals(initial);global_initial=coords.global_logs(start)
    by_guild=[[],[]]
    for k,g in enumerate(coords.groups):
        if not g["present"]:continue
        i=g["guild"];z=Polynomial(dense.yh[coords.m+k]);zd=z.deriv()
        zpoints=[lo,hi,*old._real_roots(zd,lo,hi)]
        if not coords.shared:
            j=g["nodes"][0][0]
            candidates=[(local_initial[j,i] if x==lo else old._log_softplus(float(z(x))),x) for x in zpoints]
            value,x=min(candidates);values[j,i],at[j,i]=value,dense.t+dense.h*x
            by_guild[i].append((j,z))
            continue
        candidates=[(global_initial[i] if x==lo else old._log_softplus(float(z(x))),x) for x in zpoints]
        value,x=min(candidates);global_values[i],global_at[i]=value,dense.t+dense.h*x
        polys=[Polynomial(dense.yh[ix]) for ix in g["indices"]]
        derivatives=[poly.deriv() for poly in polys]
        positive=coords.stage_positive[g["indices"]]
        lower=[];upper=[]
        for poly,index,on in zip(polys,g["indices"],positive):
            a,b=_poly_bounds(poly,lo,hi,start[index])
            lower.append(0. if on and a<=0<=b else min(a*a,b*b) if on else max(0.,a))
            upper.append(max(a*a,b*b) if on else max(0.,b))
        lower,upper=np.array(lower),np.array(upper)
        zlow,_=_poly_bounds(z,lo,hi,start[coords.m+k])
        def allocation_values(x):
            raw=np.array([poly(x) for poly in polys]);der=np.array([poly(x) for poly in derivatives])
            der[positive]=2*raw[positive]*der[positive]
            raw[positive]=raw[positive]**2
            return raw,der
        for j,w in enumerate(coords.p.weights):
            if not w:continue
            nodes=np.array([jj==j for jj,s in g["nodes"]])
            if previous is not None:
                lower_sum=float(sum(lower[nodes]));upper_norm=float(sum(upper))
                bound=old._log_softplus(zlow)+np.log(lower_sum)-np.log(upper_norm)-np.log(w) if lower_sum>0 else -np.inf
                if np.isneginf(previous[j,i]) or bound>=previous[j,i]:
                    values[j,i]=previous[j,i];continue
            points=zpoints.copy()
            for derivative_ in derivatives:points+=old._real_roots(derivative_,lo,hi)
            for poly,on in zip(polys,positive):
                if on:points+=old._real_roots(poly,lo,hi)
            def stock(x):
                if x==lo:return local_initial[j,i]
                hs,_=allocation_values(x);allocation=float(sum(hs[nodes]))
                return old._log_softplus(float(z(x)))+np.log(allocation)-np.log(sum(hs))-np.log(w) if allocation>0 else -np.inf
            if min(float(sum(allocation_values(x)[0][nodes])) for x in points)>0:
                def derivative(x):
                    hs,hd=allocation_values(x)
                    return old._log_softplus_derivative(z(x))*zd(x)+np.sum(hd[nodes],axis=0)/np.sum(hs[nodes],axis=0)-np.sum(hd,axis=0)/np.sum(hs,axis=0)
                points+=old._bracketed_candidates(derivative,stock,lo,hi)
            value,x=min((stock(x),x) for x in points);values[j,i],at[j,i]=value,dense.t+dense.h*x
    if not coords.shared:
        for i,items in enumerate(by_guild):
            if not items:continue
            if len(items)==1:
                j,_=items[0];global_values[i]=values[j,i]+np.log(coords.p.weights[j]);global_at[i]=at[j,i];continue
            polys=[z for j,z in items];weights=np.log([coords.p.weights[j] for j,z in items])
            points=[lo,hi]
            for z in polys:points+=old._real_roots(z.deriv(),lo,hi)
            def stock(x):return float(logsumexp(weights+np.array([old._log_softplus(float(z(x))) for z in polys])))
            def derivative(x):
                x=np.asarray(x);zs=np.array([z(x) for z in polys]);logs=weights.reshape((-1,)+(1,)*x.ndim)+old._array_log_softplus(zs)
                return np.sum(np.exp(logs-logsumexp(logs,axis=0))*old._log_softplus_derivative(zs)*np.array([z.deriv()(x) for z in polys]),axis=0)
            points+=old._bracketed_candidates(derivative,stock,lo,hi)
            value,x=min((global_initial[i] if x==lo else stock(x),x) for x in points)
            global_values[i],global_at[i]=value,dense.t+dense.h*x
    return values,at,global_values,global_at


def integrate(y0,p,years,*,census=None,sample_every_censuses=100,rtol=2e-8,max_step=np.inf):
    initial = np.asarray(y0,dtype=float).copy()
    if initial.shape != (p.state_size,) or np.any(~np.isfinite(initial)) or np.any(initial < 0):
        raise ValueError("Provide finite nonnegative dormancy stocks")
    if not np.isfinite(years) or years < 0 or not np.isfinite(rtol) or rtol <= 0 or not max_step > 0:
        raise ValueError("Invalid horizon or integration controls")
    if census is not None and not isinstance(census,Census): raise ValueError("Use Census")
    if not isinstance(sample_every_censuses,int) or sample_every_censuses < 1: raise ValueError("Invalid census stride")
    for j,w in enumerate(p.weights):
        if not w and np.any(initial[6*j:6*j+6] != 0): raise ValueError("Inactive habitat stocks must be zero")
        for i,on in enumerate(p.coupled.enabled):
            if not on and (initial[6*j+1+i] != 0 or initial[6*j+4+i] != 0): raise ValueError("Disabled guild must be absent")
    started = perf_counter(); coords = _Coordinates(initial,p); state = coords.encode(initial)
    physical,stage = coords.decode(state); total_logs = _log_totals(stage)
    continuum_min,pre_min,jump_min = (total_logs.copy() for _ in range(3))
    continuum_time,pre_time = np.zeros_like(total_logs),np.zeros_like(total_logs)
    global_min = coords.global_logs(state); global_pre = global_min.copy(); global_jump = global_min.copy()
    global_time,global_pre_time = np.zeros(2),np.zeros(2)
    removed = np.zeros((p.n_patches,2),bool); globally_removed = np.zeros(2,bool)
    times=[]; samples=[]; stage_samples=[]; acetate_logs=[]; census_times=[]; activity=[]; events=[]; trial_events=[]; stage_switches=[]; stage_underflows=[]
    ledger = {name:np.zeros((p.n_patches,2)) for name in ("culled_cells","culled_gdw","culled_h2_mol","inventory_jump_h2_mol_l")}
    volumes = np.zeros(p.n_patches) if census is None else p.coupled.habitat_l_cm2*census.surface_cm2*p.weights
    conversion = np.full(p.n_patches,-np.inf)
    if census is not None: conversion[p.weights>0] = np.log(volumes[p.weights>0]/census.cell_mass_gdw)
    coefficients = np.array([model.core.ASSIMILATION_A,p.coupled.biology.assimilation_m])
    interval = next((x for x in model.supported_ratio_intervals(p) if x[0] <= initial[-1] <= x[1]),None)
    status = "completed" if interval is not None else "initial_unsupported"; domain_exit=None
    temperature_range = np.repeat(float(model.core.temperature_k(initial[-1],p.coupled.climate)),2)
    nfev=steps=resets=retries=acetate_resets=failure_retries=0

    def append(t,state):
        physical,stage = coords.decode(state)
        a = np.array([old._log_softplus(state[6*j+3],old.ACETATE_SCALE) if coords.acetate_positive[j]
                      else np.log(physical[6*j+3]) if physical[6*j+3]>0 else -np.inf for j in range(p.n_patches)])
        if times and t == times[-1]: samples[-1],stage_samples[-1],acetate_logs[-1] = physical.copy(),stage.copy(),a
        else: times.append(float(t));samples.append(physical.copy());stage_samples.append(stage.copy());acetate_logs.append(a)

    def cull(t,state):
        physical,stages = coords.decode(state); logs = _log_totals(stages); changed=False
        if census.minimum_cells:
            for j,w in enumerate(p.weights):
                if not w: continue
                for i in range(2):
                    if np.isfinite(logs[j,i]) and logs[j,i]+conversion[j] < np.log(census.minimum_cells)-1e-12:
                        mass = physical[6*j+1+i]+physical[6*j+4+i]; cells=float(np.exp(logs[j,i]+conversion[j]))
                        jump = w*coefficients[i]*mass
                        events.append(dict(time_yr=float(t),patch=p.patch_names[j],guild=old.GUILDS[i],
                            removed_cells=cells,log_removed_cells=float(logs[j,i]+conversion[j]),removed_gdw=float(mass*volumes[j]),
                            removed_h2_mol=float(mass*volumes[j]*coefficients[i]),inventory_jump_h2_mol_l=float(jump)))
                        for name,value in zip(ledger,(cells,mass*volumes[j],mass*volumes[j]*coefficients[i],jump)):
                            ledger[name][j,i] += value
                        for k,g in enumerate(coords.groups):
                            if g["guild"] != i or not g["present"]: continue
                            h,log_h=coords.allocations(state,g);norm=float(sum(h))
                            target = np.array([jj == j for jj,s in g["nodes"]])
                            if not np.any(target):continue
                            h[target]=0.; remaining=float(sum(h))
                            coords.stage_positive[g["indices"][target]]=False
                            if remaining == 0:
                                g["present"]=False;state[g["indices"]]=0.;coords.stage_positive[g["indices"]]=False
                            else:
                                z=state[coords.m+k]
                                log_scaled=old._log_softplus(z)+np.log(remaining)-np.log(norm)-np.log(SCALE)
                                state[coords.m+k]=log_scaled if log_scaled < -30 else old._inverse(np.exp(log_scaled))
                                state[g["indices"]]=h/remaining
                                for a,index in enumerate(g["indices"]):
                                    if coords.stage_positive[index]:
                                        value=log_h[a]-np.log(remaining)
                                        state[index]=np.sign(state[index])*np.exp(value/2)
                        removed[j,i]=True;changed=True
        logs=_log_totals(coords.decode(state)[1]); jump_min[:]=np.minimum(jump_min,logs)
        global_after=coords.global_logs(state);global_jump[:]=np.minimum(global_jump,global_after)
        globally_removed[:] |= ~np.isfinite(global_after)
        census_times.append(float(t));activity.append(sum(int(np.isfinite(logs[j,i])) << (2*j+i) for j in range(p.n_patches) for i in range(2)))
        return changed

    def make_solver(state,t,limit=max_step):
        for _ in range(4*p.n_patches+1):
            try:initial_rate=coords.derivative(t,state)
            except _StageSourceOverflow as error:
                targets=[error.index]
            else:
                targets=[int(index) for g in coords.groups if g["present"] for index in g["indices"]
                         if coords.stage_positive[index] and initial_rate[index]*np.sign(state[index])>STAGE_LINEAR_RATE_YR*abs(state[index])]
                if not targets:break
            for index in targets:
                log_h=float(2*np.log(abs(state[index]))) if state[index] else -np.inf;value=float(state[index]**2)
                stage_underflows.append(dict(time_yr=t,state_index=index,log_allocation=log_h,linear_allocation=value,
                    scope="Positive-stage source is ill-conditioned; retain its physical allocation exactly in linear coordinates"))
                coords.stage_positive[index]=False;state[index]=value
        else:raise RuntimeError("Cannot condition stage coordinates for integration")
        atol=np.r_[np.tile([1e-7,1e-14,1e-14,1e-11,1e-14,1e-14],p.n_patches),1e-11,np.full(len(coords.groups),1e-8)]
        if p.dispersal_yr > 0: atol[np.r_[p.biomass_indices.ravel(),p.dormant_indices.ravel()]]=min(1e-14,p.dispersal_yr*min(p.weights[p.weights>0])*1e-7)
        atol[:coords.m][coords.stage_positive]=1e-12
        for j,on in enumerate(coords.acetate_positive):
            if on: atol[6*j+3]=1e-8
        first=min(1e-6*p.coupled.acetate_lifetime_yr,years-t,limit)
        logarithmic=np.arange(coords.m,len(state));nonzero=logarithmic[abs(initial_rate[logarithmic])>0]
        if nonzero.size:first=min(first,float(min(.01*np.maximum(abs(state[nonzero]),1.)/abs(initial_rate[nonzero]))))
        positive=np.flatnonzero(coords.stage_positive);nonzero=positive[abs(initial_rate[positive])>0]
        if nonzero.size:first=min(first,float(min(.01*np.maximum(abs(state[nonzero]),1e-12)/abs(initial_rate[nonzero]))))
        return _RetryingLSODA(coords.derivative,t,state,years,events=trial_events,rtol=rtol,atol=atol,max_step=limit,first_step=first)

    def update(dense,left,right,start):
        values,at,gvalues,gat=_dense_minima(dense,left,right,coords,start,continuum_min)
        mask=values<continuum_min;continuum_min[mask],continuum_time[mask]=values[mask],at[mask]
        mask=(values<pre_min)&~removed;pre_min[mask],pre_time[mask]=values[mask],at[mask]
        mask=gvalues<global_min;global_min[mask],global_time[mask]=gvalues[mask],gat[mask]
        mask=(gvalues<global_pre)&~globally_removed;global_pre[mask],global_pre_time[mask]=gvalues[mask],gat[mask]
        lo,hi,points=_points(dense,left,right,[p.state_size-1]);ratios=np.array([Polynomial(dense.yh[p.state_size-1])(x) for x in points])
        vertices=model.core.response(p.coupled.climate.case).ratios
        ratios=np.r_[ratios,vertices[(vertices>=min(ratios))&(vertices<=max(ratios))]]
        ts=model.core.temperature_k(ratios,p.coupled.climate);temperature_range[0]=min(temperature_range[0],min(ts));temperature_range[1]=max(temperature_range[1],max(ts))

    if status != "completed":
        domain_exit=dict(time_yr=0.,temperatures_k=model.temperatures(initial,p),physiology_domains=model.temperature_flags(initial,p));append(0.,state)
    else:
        if census is not None:cull(0.,state)
        append(0.,state); solver=make_solver(state,0.) if years else None
        next_census=census.census_yr if census is not None else np.inf;census_number=1;retry_streak=0;step_limited=False
        while solver is not None and solver.status == "running":
            start=solver.y.copy();left=float(solver.t)
            try:message=solver.step()
            except _StageSourceOverflow as error:
                nfev+=solver.nfev;index=error.index
                if coords.stage_positive[index]:
                    value=float(start[index]**2);log_h=float(2*np.log(abs(start[index]))) if start[index] else -np.inf
                    stage_underflows.append(dict(time_yr=left,state_index=index,log_allocation=log_h,linear_allocation=value,
                        scope="Incoming source exceeds positive-coordinate range; retain the physical allocation in linear coordinates without a seed"))
                    coords.stage_positive[index]=False;start[index]=value;solver=make_solver(start,left);resets+=1;continue
                retries+=1;retry_streak+=1
                if retry_streak>20:raise RuntimeError("Cannot resolve stage source trial by refinement") from error
                span=abs(solver._last_trial_time-left)
                candidates=[x for x in (max_step,span,solver.step_size) if x is not None and np.isfinite(x) and x>0]
                limit=min(candidates)/2 if candidates else 0.
                if not limit>0 or left+limit == left:raise RuntimeError("Stage trial refinement is below time representation") from error
                solver=make_solver(start,left,limit);step_limited=True;continue
            if solver.status == "failed":
                nfev+=solver.nfev;failure_retries+=1;retry_streak+=1
                if retry_streak>20:raise RuntimeError(f"Dormancy integration failed at {left:g}: {message}")
                span=abs(solver._last_trial_time-left)
                candidates=[x for x in (max_step,span,solver.step_size) if x is not None and np.isfinite(x) and x>0]
                limit=min(candidates)/2 if candidates else min(1e-6,years-left)
                if not limit>0 or left+limit==left:raise RuntimeError(f"Dormancy solver cannot advance at {left:g}")
                solver=make_solver(start,left,limit);step_limited=True;continue
            right=float(solver.t)
            if right == left:
                if right == years:
                    append(right,solver.y);break
                raise RuntimeError(f"Dormancy solver made no time progress at {left:g} of {years:g} years")
            dense=solver.dense_output();end=right
            lo,hi=(left-dense.t)/dense.h,(right-dense.t)/dense.h;ratio=Polynomial(dense.yh[p.state_size-1])
            checks=[lo,hi]
            for boundary in interval:
                if np.isfinite(boundary):checks += old._real_roots(ratio-boundary,lo,hi)
            for a,b in zip(sorted(set(checks))[:-1],sorted(set(checks))[1:]):
                if not interval[0] <= ratio((a+b)/2) <= interval[1]:end=float(dense.t+dense.h*a);break
            if not _positive_piece(dense,left,end,coords,start):
                retries+=1;retry_streak+=1
                if retry_streak>20:raise RuntimeError("Cannot retain nonnegative dormancy allocations")
                nfev+=solver.nfev;solver=make_solver(start,left,(right-left)/2);step_limited=True;continue
            retry_streak=0;steps+=1;restarted=False
            while next_census <= end+16*np.finfo(float).eps*max(1.,end):
                time=min(next_census,end);accepted=start.copy() if time == left else dense(time)
                logs=_log_totals(coords.decode(accepted)[1])
                removing=census.minimum_cells>0 and np.any(np.isfinite(logs)&(logs+conversion[:,None]<np.log(census.minimum_cells)-1e-12))
                if removing:update(dense,left,time,start)
                changed=cull(time,accepted)
                if changed or census_number%sample_every_censuses==0 or time == years:append(time,accepted)
                census_number+=1;next_census=census_number*census.census_yr
                if changed:
                    nfev+=solver.nfev;solver=make_solver(accepted,time) if time < years else None;resets+=1;restarted=True;step_limited=False;break
            if restarted:continue
            update(dense,left,end,start);accepted=start.copy() if end == left else dense(end)
            physical,_=coords.decode(accepted)
            if census is None or end == years or end < right:append(end,accepted)
            if end < right:
                status="domain_exit";domain_exit=dict(time_yr=end,temperatures_k=model.temperatures(physical,p),physiology_domains=model.temperature_flags(physical,p));break
            switching=[j for j,w in enumerate(p.weights) if w and not coords.acetate_positive[j] and physical[6*j+3]>0]
            linear_candidates=[int(index) for g in coords.groups if g["present"] for index in g["indices"]
                               if not coords.stage_positive[index] and accepted[index]>0]
            stage_promotions=[]
            if linear_candidates:
                derivative=coords.derivative(end,accepted)
                for index in linear_candidates:
                    age=accepted[index]/max(abs(derivative[index]),np.finfo(float).tiny)
                    if age>=max(STAGE_POSITIVE_ENTRY_AGE_YR,100*np.spacing(max(end,1.))):stage_promotions.append(index)
            if (switching or stage_promotions) and end < years:
                for j in switching:coords.acetate_positive[j]=True;accepted[6*j+3]=old._inverse(physical[6*j+3]/old.ACETATE_SCALE)
                for index in stage_promotions:
                    value=float(accepted[index]);accepted[index]=np.sqrt(value);coords.stage_positive[index]=True
                    stage_switches.append(dict(time_yr=end,state_index=index,allocation=value,coordinate="square_root",scope="First conditioned positive accepted allocation; no added seed"))
                nfev+=solver.nfev;solver=make_solver(accepted,end);acetate_resets+=int(bool(switching));resets+=int(bool(stage_promotions));step_limited=False
            elif step_limited and end < years:
                nfev+=solver.nfev;solver=make_solver(accepted,end);resets+=1;step_limited=False
        if solver is not None:nfev+=solver.nfev
    stage_samples=np.moveaxis(np.asarray(stage_samples),0,-1);log_totals=logsumexp(stage_samples,axis=2)
    metadata=dict(nfev=nfev,accepted_steps=steps,solver_resets=resets+acetate_resets+retries,relative_tolerance=rtol,
        allocation_positivity_retries=retries,solver_failure_retries=failure_retries,acetate_coordinate_resets=acetate_resets,wall_seconds=perf_counter()-started,
        linear_allocation_absolute_tolerance=min(1e-14,p.dispersal_yr*min(p.weights[p.weights>0])*1e-7) if p.dispersal_yr>0 else 1e-14,
        positive_allocation_absolute_tolerance=1e-12,
        acetate_trial_retries=len(trial_events),acetate_trial_retry_events=trial_events,n_censuses=len(census_times),
        global_log_cell_conversion=None if census is None else float(np.log(p.coupled.habitat_l_cm2*census.surface_cm2/census.cell_mass_gdw)),
        patch_volume_l=volumes,supported_ratio_interval=interval,external_immigration="none",
        minimum_scope="Numerical extrema of accepted dense flow; X+Z per habitat, contemporaneous weighted global sums; not interval certified",
        population_coordinate="Log-softplus total guild stocks with explicit square-root active/dormant allocations; per-habitat totals when exchange is zero",
        stage_underflow_scope="Total guild logarithms retained; stage allocations may underflow below floating point and are replenished only by physical conversion or migration",
        initial_dormant_scope="Exact zeros, no added seed; conversion enters through nonnegative linear stage allocations",
        stage_coordinate_switches=stage_switches,stage_source_restarts=stage_underflows,
        stage_positive_entry_age_yr=STAGE_POSITIVE_ENTRY_AGE_YR,stage_linear_relative_rate_yr=STAGE_LINEAR_RATE_YR,
        last_physical_time_yr=float(times[-1]),
        census=None if census is None else dict(minimum_cells=census.minimum_cells,census_yr=census.census_yr,
            cell_mass_gdw=census.cell_mass_gdw,surface_cm2=census.surface_cm2),
        final_temperatures_k=model.temperatures(samples[-1],p),final_physiology_domains=model.temperature_flags(samples[-1],p),
        **old._temperature_metadata(temperature_range,p.base))
    physicals=np.asarray(samples).T
    return DormancyResult(np.asarray(times),physicals,log_totals,np.asarray(acetate_logs).T,
        np.array([model.temperatures(y,p) for y in samples]).T,np.array([model.temperature_flags(y,p) for y in samples]).T,
        np.array([str(model.core.domain(y[-1],p.coupled.climate)) for y in samples]),status=="completed",status,domain_exit,
        np.asarray(census_times),np.asarray(activity,dtype=object),events,continuum_min,continuum_time,pre_min,pre_time,jump_min,
        global_min,global_time,global_pre,global_pre_time,global_jump,ledger,metadata,
        stage_samples[:,:,0,:],stage_samples[:,:,1,:])


def integrate_finite(y0,p,years,process=Census(),**kwargs):return integrate(y0,p,years,census=process,**kwargs)
