"""Condition genuinely singular allocation charts at saved accepted states.

This named numerical driver copies the 7046 accepted-step flow. Changes are
limited to typed allocation-Newton failures and explicit accepted post-step
chart conversion followed by restart. Physical equations, tolerances, census,
positivity checks and dense-flow accounting remain frozen.
"""

from hashlib import sha256
from time import perf_counter
from types import SimpleNamespace

import numpy as np
from numpy.polynomial import Polynomial
from scipy.special import expit, logsumexp

from . import dormancy_chemical_integration as chemical
from . import dormancy_jacobian_integration as frozen
from . import dormancy_trial_integration as guarded
from . import dormancy as model
from . import habitat_integration as old
from .dormancy_integration import (Census, DormancyResult, SCALE,
    STAGE_POSITIVE_ENTRY_AGE_YR, STAGE_LINEAR_RATE_YR, _StageSourceOverflow,
    _log_totals, _dense_minima, _points, _positive_piece)

_ChemicalConditioning=frozen._ChemicalConditioning
switching_slope=frozen.switching_slope
_matrix_values=chemical._primitive_values


def _stage_error(index,time,state,term):
    error=_StageSourceOverflow(int(index))
    error.stage_cause=dict(kind="unrepresentable_allocation_newton_row",term=term,
        state_index=int(index),trial_time_yr=float(time),
        trial_coordinate_sha256=sha256(state.tobytes()).hexdigest(),trial_root=float(state[index]))
    return error


class _Coordinates(chemical._Coordinates):
    def __init__(self,initial,p):
        super().__init__(initial,p)
        self.stage_conditioning_events=[]

    def condition_stage(self,state,time,index,phase,error=None):
        if not self.stage_positive[index]:raise RuntimeError("Stage conditioning requires a positive chart")
        before=self.decode(state)[0].copy();totals=state[self.m:].copy()
        global_before=self.global_logs(state).copy();accepted_hash=sha256(state.tobytes()).hexdigest()
        root=float(state[index]);log_h=float(2*np.log(abs(root))) if root else -np.inf
        log_source=-np.inf
        flux=model.fluxes(before,self.p,trial_extension=True)
        for group in self.groups:
            if not group["present"] or index not in group["indices"]:continue
            position=list(group["indices"]).index(index)
            q=group["migration"].copy()
            for a,(j,stage) in enumerate(group["nodes"]):
                for b,(k,other) in enumerate(group["nodes"]):
                    if j==k and stage!=other:
                        q[a,b]=flux["sigma_yr"][j,group["guild"]] if stage==0 else flux["rho_yr"][j,group["guild"]]
            logs=self.allocations(state,group)[1];incoming=q[:,position]>0
            if np.any(incoming):log_source=float(logsumexp(np.log(q[incoming,position])+logs[incoming]))
            break
        value=float(root**2)
        self.stage_positive[index]=False;state[index]=value
        self.condition_producer_chemical(state,time,index)
        after=self.decode(state)[0]
        identical=before.tobytes()==after.tobytes()
        totals_identical=totals.tobytes()==state[self.m:].tobytes()
        if not identical or not totals_identical:raise RuntimeError("Stage chart conversion changed accepted physical stocks or total coordinates")
        after_log=float(np.log(value)) if value>0 else -np.inf
        event=dict(time_yr=float(time),state_index=int(index),phase=phase,
            accepted_coordinate_sha256=accepted_hash,prior_root=root,log_allocation=log_h,
            linear_allocation=value,linear_log_allocation=after_log,
            retained_stage_log_lost=bool(np.isfinite(log_h) and not np.isfinite(after_log)),
            log_incoming_allocation_rate_yr=log_source,
            physical_state_bitwise_preserved=identical,total_coordinates_bitwise_preserved=totals_identical,
            global_guild_logs_bitwise_preserved=global_before.tobytes()==self.global_logs(state).tobytes(),
            inventory_before=float(model.inventory(before,self.p)),inventory_after=float(model.inventory(after,self.p)),
            cause=getattr(error,"stage_cause",None),
            scope="Saved accepted root squared into its decoded linear allocation; no seed or stock reset. Global total logarithms retained; subfloat stage logarithms may be lost.")
        self.stage_conditioning_events.append(event)
        return event


def _allocation_jacobian(time, state, coords):
    """Approximate Newton matrix; switching/allocation derivatives are analytic."""
    coords.jacobian_evaluations += 1
    center, flux = _matrix_values(state, coords)
    size = len(state)
    matrix = np.empty((size,size))
    gradient = np.zeros((*flux["net_growth_yr"].shape,size))
    stage_indices = set(int(i) for group in coords.groups for i in group["indices"])
    for index in range(size):
        root = index < coords.m and coords.stage_positive[index]
        step = 1e-6*abs(state[index]) if root else 1e-6*max(abs(state[index]), 1e-8 if index in stage_indices else 1.)
        if step == 0.: step = np.nextafter(0.,1.)
        plus, minus = state.copy(), state.copy()
        plus[index] += step; minus[index] -= step
        if (index in stage_indices and not root and minus[index] < 0) or (root and abs(state[index]) <= step):
            fp, fluxp = _matrix_values(plus, coords)
            width = plus[index]-state[index]
            matrix[:,index] = (fp-center)/width
            gradient[...,index] = (fluxp["net_growth_yr"]-flux["net_growth_yr"])/width
        else:
            fp, fluxp = _matrix_values(plus, coords)
            fm, fluxm = _matrix_values(minus, coords)
            width = plus[index]-minus[index]
            matrix[:,index] = (fp-fm)/width
            gradient[...,index] = (fluxp["net_growth_yr"]-fluxm["net_growth_yr"])/width
    loss = coords.p.coupled.biology.loss_h*model.core.HOURS_PER_YEAR
    neg = np.clip(-flux["net_growth_yr"]/loss,0.,1.)
    pos = np.clip(flux["net_growth_yr"]/loss,0.,1.)
    dsigma = -coords.p.switching_factor*switching_slope(neg,coords.p.ramp)[...,None]*gradient
    drho = coords.p.switching_factor*switching_slope(pos,coords.p.ramp)[...,None]*gradient
    for group in coords.groups:
        if not group["present"]:
            matrix[group["indices"]] = 0.
            continue
        ix, nodes, guild = group["indices"], group["nodes"], group["guild"]
        h = coords.allocations(state,group)[0]
        dh = np.zeros((len(ix),size))
        for a,index in enumerate(ix): dh[a,index] = 2*state[index] if coords.stage_positive[index] else 1.
        growth = np.array([flux["net_growth_yr"][j,guild] if s == 0 else -flux["dormant_loss_yr"] for j,s in nodes])
        dgrowth = np.array([gradient[j,guild] if s == 0 else np.zeros(size) for j,s in nodes])
        mean = float(h@growth/sum(h))
        dmean = ((growth-mean)@dh+h@dgrowth)/sum(h)
        q = group["migration"].copy(); dq = np.zeros((*q.shape,size))
        for a,(j,s) in enumerate(nodes):
            for b,(k,ss) in enumerate(nodes):
                if j == k and s != ss:
                    q[a,b] = flux["sigma_yr"][j,guild] if s == 0 else flux["rho_yr"][j,guild]
                    dq[a,b] = dsigma[j,guild] if s == 0 else drho[j,guild]
        incoming = q.T@h
        dincoming = np.einsum("baj,b->aj",dq,h)+q.T@dh
        out, dout = q.sum(axis=1), dq.sum(axis=1)
        for a,index in enumerate(ix):
            coefficient = growth[a]-mean-out[a]
            dcoefficient = dgrowth[a]-dmean-dout[a]
            if coords.stage_positive[index]:
                z = state[index]
                if z == 0.:
                    if incoming[a] != 0. or np.any(dincoming[a] != 0.):
                        raise _stage_error(index,time,state,"zero_root_source_or_differential")
                    coords.zero_root_limits[int(index)]=coords.zero_root_limits.get(int(index),0)+1
                    matrix[index] = 0.
                    matrix[index,index] = .5*coefficient
                    continue
                try:
                    with np.errstate(over="raise", invalid="raise", divide="raise"):
                        matrix[index] = .5*z*dcoefficient+dincoming[a]/(2*z)
                        matrix[index,index] += .5*coefficient-(incoming[a]/(2*z))/z
                except FloatingPointError as error:
                    raise _stage_error(index,time,state,"root_allocation_newton_row") from error
                if np.any(~np.isfinite(matrix[index])):
                    raise _stage_error(index,time,state,"root_allocation_newton_row")
            else:
                matrix[index] = h[a]*dcoefficient+coefficient*dh[a]+dincoming[a]
    if np.any(~np.isfinite(matrix)):
        raise guarded._InvalidTrial("nonfinite_newton_matrix", "Nonfinite dormancy Newton matrix")
    return matrix


def coordinate_jacobian(time,state,coords):
    namespace=chemical.coordinate_jacobian.__globals__.copy()
    namespace["frozen"]=SimpleNamespace(coordinate_jacobian=_allocation_jacobian,
        old=old,_ChemicalConditioning=_ChemicalConditioning)
    return chemical._copied(chemical.coordinate_jacobian,namespace)(time,state,coords)


class _StageLSODA(chemical._ChemicalLSODA):
    def _chemical_jacobian(self,time,state):
        try:return coordinate_jacobian(time,state,self.coordinates)
        except _ChemicalConditioning as error:
            if hasattr(error,"chemical_cause"):
                self._record_request(error,getattr(self,"_guard_left",time),getattr(self,"_guard_start",state))
            raise


def _accepted_integrate(y0,p,years,*,census=None,sample_every_censuses=100,rtol=2e-8,max_step=np.inf):
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
        for _ in range(5*p.n_patches+1):
            stage_error=None
            try:initial_rate=coords.derivative(t,state)
            except _StageSourceOverflow as error:
                targets=[error.index];stage_error=error
            except RuntimeError as error:
                if str(error) != guarded._OVERFLOW: raise
                coords.request_linear_acetate(t,state)
                pending,coords._pending_chemical=coords._pending_chemical,{}
                if not pending: raise
                coords.condition_chemicals(state,t,pending,"initial_source_chemical_chart")
                continue
            else:
                chemical=[j for j,on in enumerate(coords.acetate_positive) if on and abs(initial_rate[6*j+3])>STAGE_LINEAR_RATE_YR]
                if chemical:
                    coords.condition_chemicals(state,t,chemical,"initial_rate_chemical_chart")
                    continue
                targets=[int(index) for g in coords.groups if g["present"] for index in g["indices"]
                         if coords.stage_positive[index] and initial_rate[index]*np.sign(state[index])>STAGE_LINEAR_RATE_YR*abs(state[index])]
                if not targets:break
            for index in targets:
                stage_underflows.append(coords.condition_stage(state,t,index,"solver_construction",stage_error))
        else:raise RuntimeError("Cannot condition stage coordinates for integration")
        atol=np.r_[np.tile([1e-7,1e-14,1e-14,1e-11,1e-14,1e-14],p.n_patches),1e-11,np.full(len(coords.groups),1e-8)]
        if p.dispersal_yr > 0: atol[np.r_[p.biomass_indices.ravel(),p.dormant_indices.ravel()]]=min(1e-14,p.dispersal_yr*min(p.weights[p.weights>0])*1e-7)
        atol[:coords.m][coords.stage_positive]=1e-12
        for j,on in enumerate(coords.acetate_positive):
            if on: atol[6*j+3]=1e-8
            elif p.weights[j]:
                index=6*j+3
                coords.chemical_atol_history.append(dict(time_yr=float(t),patch=j,stock=float(state[index]),rate=float(initial_rate[index]),atol=float(atol[index])))
        first=min(1e-6*p.coupled.acetate_lifetime_yr,years-t,limit)
        logarithmic=np.r_[np.arange(coords.m,len(state)),[6*j+3 for j,on in enumerate(coords.acetate_positive) if on]].astype(int);nonzero=logarithmic[abs(initial_rate[logarithmic])>0]
        if nonzero.size:first=min(first,float(min(.01*np.maximum(abs(state[nonzero]),1.)/abs(initial_rate[nonzero]))))
        positive=np.flatnonzero(coords.stage_positive);nonzero=positive[abs(initial_rate[positive])>0]
        if nonzero.size:first=min(first,float(min(.01*np.maximum(abs(state[nonzero]),1e-12)/abs(initial_rate[nonzero]))))
        return _GuardedLSODA(coords.derivative,t,state,years,events=trial_events,nominal_max_step=max_step,rtol=rtol,atol=atol,max_step=limit,first_step=first)

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
            except _ChemicalConditioning as error:
                nfev+=solver.nfev
                coords.condition_chemicals(start,left,error.indices,"accepted_rate_chemical_chart")
                solver=make_solver(start,left);resets+=1;step_limited=False;continue
            except _StageSourceOverflow as error:
                nfev+=solver.nfev;index=error.index
                if coords.stage_positive[index]:
                    stage_underflows.append(coords.condition_stage(start,left,index,"native_step",error))
                    solver=make_solver(start,left);resets+=1;continue
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
            producer_present=lambda j:any(g["guild"]==0 and g["present"] and 6*j+1 in g["indices"] for g in coords.groups)
            chemical_candidates=[j for j,w in enumerate(p.weights) if w and not coords.acetate_positive[j] and physical[6*j+3]>0
                                 and (coords.stage_positive[6*j+1] or not producer_present(j))]
            switching=[];poststep_conditioned=False
            def accepted_rate():
                nonlocal poststep_conditioned
                for _ in range(len(accepted)+1):
                    try:return coords.derivative(end,accepted)
                    except _StageSourceOverflow as error:
                        if not coords.stage_positive[error.index]:raise
                        stage_underflows.append(coords.condition_stage(accepted,end,error.index,"accepted_poststep",error))
                        poststep_conditioned=True
                raise RuntimeError("Cannot condition accepted post-step stage coordinates")
            if chemical_candidates:
                chemical_rate=accepted_rate()
                for j in chemical_candidates:
                    age=physical[6*j+3]/max(abs(chemical_rate[6*j+3]),np.finfo(float).tiny)
                    if age>=max(STAGE_POSITIVE_ENTRY_AGE_YR,100*np.spacing(max(end,1.))):switching.append(j)
            linear_candidates=[int(index) for g in coords.groups if g["present"] for index in g["indices"]
                               if not coords.stage_positive[index] and accepted[index]>0]
            stage_promotions=[]
            if linear_candidates:
                derivative=accepted_rate()
                for index in linear_candidates:
                    age=accepted[index]/max(abs(derivative[index]),np.finfo(float).tiny)
                    if age>=max(STAGE_POSITIVE_ENTRY_AGE_YR,100*np.spacing(max(end,1.))):stage_promotions.append(index)
            if (switching or stage_promotions or poststep_conditioned) and end < years:
                for j in switching:coords.acetate_positive[j]=True;accepted[6*j+3]=old._inverse(physical[6*j+3]/old.ACETATE_SCALE)
                for index in stage_promotions:
                    value=float(accepted[index]);accepted[index]=np.sqrt(value);coords.stage_positive[index]=True
                    stage_switches.append(dict(time_yr=end,state_index=index,allocation=value,coordinate="square_root",scope="First conditioned positive accepted allocation; no added seed"))
                nfev+=solver.nfev;solver=make_solver(accepted,end);acetate_resets+=int(bool(switching));resets+=int(bool(stage_promotions or poststep_conditioned));step_limited=False
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
        numerical_variant="analytic_switching_jacobian_chemical_age",
        newton_evaluations=coords.jacobian_evaluations,zero_root_newton_limits=coords.zero_root_limits,
        trial_guard_events=coords.rejected,trial_guard_stage_conditioning_events=coords.conditioned,
        trial_guard_finite_trial_observations=coords.finite_trials[0],
        chemical_conditioning_events=coords.chemical_events,chemical_linear_atol_history=coords.chemical_atol_history,
        chemical_linear_entry_rate_yr=STAGE_LINEAR_RATE_YR,chemical_positive_entry_age_yr=STAGE_POSITIVE_ENTRY_AGE_YR,
        **old._temperature_metadata(temperature_range,p.base))
    physicals=np.asarray(samples).T
    return DormancyResult(np.asarray(times),physicals,log_totals,np.asarray(acetate_logs).T,
        np.array([model.temperatures(y,p) for y in samples]).T,np.array([model.temperature_flags(y,p) for y in samples]).T,
        np.array([str(model.core.domain(y[-1],p.coupled.climate)) for y in samples]),status=="completed",status,domain_exit,
        np.asarray(census_times),np.asarray(activity,dtype=object),events,continuum_min,continuum_time,pre_min,pre_time,jump_min,
        global_min,global_time,global_pre,global_pre_time,global_jump,ledger,metadata,
        stage_samples[:,:,0,:],stage_samples[:,:,1,:])


def integrate(y0,p,years,**kwargs):
    instances=[];events=[]
    def coordinates(initial,parameters):
        value=_Coordinates(initial,parameters);instances.append(value);return value
    def constructor(*args,**options):
        return _StageLSODA(*args,progress_events=events,**options)
    namespace=_accepted_integrate.__globals__.copy()
    namespace.update(_Coordinates=coordinates,_GuardedLSODA=constructor)
    function=chemical._copied(_accepted_integrate,namespace)
    try:result=function(y0,p,years,**kwargs)
    except RuntimeError as error:
        error.native_zero_time_events=events.copy()
        error.chemical_conditioning_requests=[v for c in instances for v in c.chemical_conditioning_requests]
        error.stage_conditioning_events=[v for c in instances for v in c.stage_conditioning_events]
        raise
    result.metadata.update(base_numerical_variant=result.metadata["numerical_variant"],
        numerical_variant="analytic_dormancy_stage_conditioning",
        native_zero_time_retries=len(events),native_zero_time_events=events,
        chemical_conditioning_requests=[v for c in instances for v in c.chemical_conditioning_requests],
        stage_conditioning_events=[v for c in instances for v in c.stage_conditioning_events])
    return result


def integrate_finite(y0,p,years,process=Census(),**kwargs):
    return integrate(y0,p,years,census=process,**kwargs)
