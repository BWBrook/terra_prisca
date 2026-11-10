"""Resident equilibria with stationary source–sink dormant pools."""

from dataclasses import replace

import numpy as np
from scipy.optimize import least_squares

from . import dormancy as model
from . import population_coupling as core
from . import turnover_starts


def resident_stability(y,p,guild,relative_steps=(1e-5,1e-6),*,max_refinements=3):
    """Conditional resident spectra, retaining climate-side and step checks.

    Only the named resident is enabled. This does not test invasion by the
    competing guild or global uniqueness, and certifies the smooth cubic ramp
    rather than averaging the linear control's switching corner.
    """
    if guild not in (0,1) or len(relative_steps)<2 or len(set(relative_steps))<2:
        raise ValueError("Choose one resident and at least two distinct Jacobian steps")
    if not isinstance(max_refinements,int) or max_refinements<0:
        raise ValueError("Use a nonnegative bounded refinement count")
    conditional=replace(p,base=replace(p.base,base=replace(p.coupled,enabled=(guild==0,guild==1))))
    y=np.asarray(y,dtype=float)
    if y.shape!=(p.state_size,) or np.any(~np.isfinite(y)) or np.any(y<0):
        return dict(stability="unsupported",supported_stable=False,spectra=[],physiology_domains=[])
    flags=model.temperature_flags(y,conditional)
    if "unsupported" in flags:
        return dict(stability="unsupported",supported_stable=False,spectra=[],physiology_domains=flags)
    patches=np.flatnonzero(p.weights>0)
    indices=[*[6*j+k for j in patches for k in (0,1+guild,3,4+guild)],p.state_size-1]
    scales=np.maximum(abs(y),np.r_[np.tile([10.,1e-4,1e-4,1e-5,1e-4,1e-4],p.n_patches),.01])
    knots=np.unique(np.r_[0.,core.response(p.coupled.climate.case).ratios])
    ratio=float(y[-1]);at_corner=bool(np.any(np.isclose(ratio,knots,rtol=0.,atol=1e-10)))
    sides=([1] if ratio<=1e-10 else [-1,1]) if at_corner else [0]
    records=[]
    for relative in relative_steps:
        if not np.isfinite(relative) or relative<=0:raise ValueError("Use positive finite Jacobian steps")
        for side in sides:
            matrix=np.empty((len(indices),len(indices)))
            center=model.rhs(y,conditional)
            for column,k in enumerate(indices):
                step=relative*scales[k]
                if k==p.state_size-1:
                    if side:
                        distances=(knots-ratio)*side
                        positive=distances[distances>1e-10]
                        if positive.size:step=min(step,float(min(positive))/4)
                    else:
                        positive=abs(knots-ratio);positive=positive[positive>1e-10]
                        if positive.size:step=min(step,float(min(positive))/4)
                delta=np.zeros(p.state_size);delta[k]=step
                if k==p.state_size-1 and side:
                    a=y+side*delta;b=y+2*side*delta
                    if "unsupported" in model.temperature_flags(a,conditional) or "unsupported" in model.temperature_flags(b,conditional):
                        matrix=None;break
                    derivative=(-3*center+4*model.rhs(a,conditional)-model.rhs(b,conditional))/(2*side*step)
                else:
                    a=y+delta;b=y-delta
                    if "unsupported" in model.temperature_flags(a,conditional) or "unsupported" in model.temperature_flags(b,conditional):
                        matrix=None;break
                    derivative=(model.rhs(a,conditional)-model.rhs(b,conditional))/(2*step)
                matrix[:,column]=derivative[indices]*scales[k]/scales[indices]
            if matrix is None:continue
            values=np.linalg.eigvals(matrix)
            records.append(dict(relative_step=float(relative),ratio_side=int(side),
                max_real_yr=float(max(values.real)),eigenvalues=[[float(v.real),float(v.imag)] for v in values]))
    if len(records)!=len(relative_steps)*len(sides):
        return dict(stability="unsupported_perturbation",supported_stable=False,spectra=records,physiology_domains=flags)
    spread=max(max(v["max_real_yr"] for v in records if v["ratio_side"]==s)
               -min(v["max_real_yr"] for v in records if v["ratio_side"]==s) for s in sides)
    largest=max(v["max_real_yr"] for v in records)
    agreement=bool(spread<=max(1e-8,1e-3*abs(largest)))
    if not agreement and getattr(p,"ramp","linear")=="cubic" and max_refinements:
        finest=min(relative_steps)
        refined=resident_stability(y,p,guild,(finest,finest/10),max_refinements=max_refinements-1)
        combined={(v["relative_step"],v["ratio_side"]):v for v in records+refined["spectra"]}
        refined["spectra"]=list(combined.values())
        refined["step_refinements"]=1+refined.get("step_refinements",0)
        refined["refinement_history"]=[dict(relative_steps=list(relative_steps),step_spread_yr=float(spread)),
                                       *refined.get("refinement_history",[])]
        return refined
    if getattr(p,"ramp","linear")!="cubic":status="unqualified_nonsmooth_ramp"
    elif not agreement:status="unresolved_step_dependence"
    elif largest < -max(1e-9,5*spread):status="stable"
    elif all(v["max_real_yr"]>max(1e-9,5*spread) for v in records):status="unstable"
    else:status="marginal_or_side_dependent"
    return dict(stability=status,supported_stable=status=="stable",spectra=records,
        max_real_yr=largest,step_spread_yr=float(spread),step_agreement=agreement,
        final_relative_steps=list(relative_steps),step_refinements=0,refinement_history=[],
        climate_corner=at_corner,physiology_domains=flags,resident_guild=int(guild),
        stability_scope="Conditional enabled resident only; full active+dormant pools; agreeing FD pair with bounded decade refinement and each climate side; cubic ramp")


def dormant_balance(y,p):
    f=model.fluxes(y,p)
    active=np.flatnonzero(p.weights>0)
    for guild in range(2):
        if not p.coupled.enabled[guild]:continue
        matrix=np.diag(f["rho_yr"][active,guild]+f["dormant_loss_yr"]+p.dispersal_yr)
        matrix-=p.dispersal_yr*np.ones((len(active),1))*p.weights[active][None,:]
        source=f["sigma_yr"][active,guild]*y[p.biomass_indices[active,guild]]
        dormant=np.linalg.solve(matrix,source)
        if np.any(dormant<0):raise ArithmeticError("Negative stationary dormant pool")
        y[p.dormant_indices[active,guild]]=dormant
    return y


def conditional_states(p,guild):
    enabled=(guild==0,guild==1)
    conditional=replace(p,base=replace(p.base,base=replace(p.coupled,enabled=enabled)))
    original=turnover_starts.conditional_states(p.base,guild)
    candidates=[];active=np.flatnonzero(p.weights>0);n=len(active)
    supply=core.supply_h2(p.coupled)*core.HOURS_PER_YEAR
    loss=p.coupled.biology.loss_h*core.HOURS_PER_YEAR
    pressure_max=p.coupled.biology.atmosphere_pa+core.supply_h2(p.coupled)/p.coupled.biology.exchange_mol_l_h_pa
    for old in original["qualifying"]:
        seed=model.reference_state(old["y"],conditional)
        if len(active)==1:
            diagnostic=resident_stability(seed,conditional,guild)
            result=dict(y=seed,r=old["r"],reference_stability=old["stability"],max_scaled_residual=old["max_scaled_residual"],
                        dormant_balance_residual=0.,well_mixed_embedding=True,**diagnostic)
            candidates.append(result);continue
        acetate=active if guild==0 else np.array([],dtype=int)
        values=np.r_[seed[6*active]/100,np.log(seed[6*active+1+guild]/1e-3),
                     np.log(np.maximum(seed[6*acetate+3],1e-30)/1e-3),seed[-1]/.2]
        lower=np.r_[np.zeros(n),np.full(n+len(acetate),-100.),0.]
        upper=np.r_[np.full(n,pressure_max/100),np.full(n+len(acetate),30.),5.]
        def decode(z):
            y=np.zeros(p.state_size);y[6*active]=100*z[:n]
            y[6*active+1+guild]=1e-3*np.exp(z[n:2*n])
            y[6*acetate+3]=1e-3*np.exp(z[2*n:2*n+len(acetate)])
            y[-1]=.2*z[-1]
            return dormant_balance(y,conditional)
        def equations(z):
            y=decode(z);f=model.fluxes(y,conditional,trial_extension=True);dy=model.rhs(y,conditional,trial_extension=True)
            result=[dy[6*j]*core.HENRY_30C_MOL_L_PA/supply for j in active]
            result += [dy[6*j+1+guild]/(loss*y[6*j+1+guild]) for j in active]
            result += [dy[6*j+3]/(supply/4) for j in acetate]
            result += [dy[-1]/(core.inventory_to_ratio(p.coupled)*supply/4)]
            return np.asarray(result)
        fit=least_squares(equations,values,bounds=(lower,upper),jac="3-point",x_scale="jac",
                          ftol=1e-12,xtol=1e-12,gtol=1e-12,max_nfev=1000)
        residual=float(max(abs(equations(fit.x))))
        if residual>1e-8:continue
        y=decode(fit.x);dy=model.rhs(y,conditional)
        if "unsupported" in model.temperature_flags(y,conditional):continue
        diagnostic=resident_stability(y,conditional,guild)
        candidates.append(dict(y=y,r=float(y[-1]),
            max_scaled_residual=residual,dormant_balance_residual=float(max(abs(dy[conditional.dormant_indices]).ravel())),
            well_mixed_embedding=False,reference_stability=old["stability"],**diagnostic))
    qualifying=[v for v in candidates if v["supported_stable"] and all(v["y"][6*j+1+guild]>0 for j in active)]
    return dict(candidates=candidates,qualifying=qualifying,
        selected=max(qualifying,key=lambda x:x["r"]) if qualifying else None,
        stability_scope="Only supported cubic roots with agreeing conditional resident spectra qualify; no claim of full-community stability or global root completeness")
