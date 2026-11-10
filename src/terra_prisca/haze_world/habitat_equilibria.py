"""Conditional starts and local equilibrium refinement for N habitats.

Finite scalar bracketing and seeded numerical roots do not enumerate all basins.
"""

from dataclasses import replace
from functools import lru_cache

import numpy as np
from scipy.optimize import brentq, least_squares

from . import habitat_coupling as model
from . import population_coupling as core
from .methane_budget import response

BIOMASS_SCALE = 1e-3


def local_resident(r, temperature, base, guild):
    supply = core.supply_h2(base)
    outlet = base.biology.exchange_mol_l_h_pa
    maximum_acetate = supply * core.HOURS_PER_YEAR * base.acetate_lifetime_yr / 4

    def state(acetate):
        y = np.array([0., 0., 0., acetate, r])
        organism = core.activity_guilds_at_temperature(y, base, temperature)[guild]
        pressure = organism.rstar(base.biology.loss_h)
        captured = supply - outlet * (pressure - base.biology.atmosphere_pa)
        if not np.isfinite(pressure) or captured <= 0:
            return None
        y[0], y[1+guild] = pressure, captured / float(organism.uptake(pressure))
        return y

    if guild == 0 and base.activity_feedback == "products":
        def balance(acetate):
            y = state(acetate)
            if y is None:
                return acetate
            f = core.fluxes_at_temperature(y, base, temperature)
            return acetate - f["acetate_production_mol_l_yr"] / (f["k_rec_yr"] + f["k_other_yr"])
        acetate = brentq(balance, 0., maximum_acetate, xtol=1e-18)
        return state(acetate)
    y = state(0.)
    if y is not None:
        f = core.fluxes_at_temperature(y, base, temperature)
        y[3] = f["acetate_production_mol_l_yr"] / (f["k_rec_yr"] + f["k_other_yr"])
    return y


def scaled_residual(y, p):
    supply = core.supply_h2(p.base) * core.HOURS_PER_YEAR
    scales = np.r_[np.tile([supply/core.HENRY_30C_MOL_L_PA,
        BIOMASS_SCALE*core.HOURS_PER_YEAR*p.base.biology.loss_h,
        BIOMASS_SCALE*core.HOURS_PER_YEAR*p.base.biology.loss_h, supply/4], p.n_patches),
        core.inventory_to_ratio(p.base)*supply/4]
    return model.rhs(y,p)/scales


def describe(y, p):
    vertices = response(p.base.climate.case).ratios
    sides = (-1,1) if np.any(np.isclose(y[-1],vertices,rtol=0,atol=1e-10)) else (0,)
    spectra = []
    for side in sides:
        try:
            spectra.extend(np.linalg.eigvals(model.jacobian(y,p,r_side=side)))
        except ValueError:
            continue
    maximum = float(max(np.real(spectra))) if spectra else np.nan
    status = ("unresolved" if not np.isfinite(maximum) else "unstable" if maximum>1e-8
              else "marginal" if maximum>=-1e-8 else "stable")
    f = model.fluxes(y,p)
    return dict(y=np.asarray(y),r=float(y[-1]),global_temperature_k=f["global_temperature_k"],
                temperatures_k=f["temperatures_k"],physiology_domains=model.temperature_flags(y,p),
                climate_domain=f["climate_domain"],stability=status,max_real_yr=maximum,
                eigenvalues=np.asarray(spectra),max_scaled_residual=float(max(abs(scaled_residual(y,p)))),
                redox_residual=model.redox_residual(y,p))


def refine(seed, p):
    """Refine the supported branch implied by a seed's global/local occupancy."""
    seed = np.asarray(seed,dtype=float)
    active = [j for j,w in enumerate(p.weights) if w]
    positive = [i for i,enabled in enumerate(p.base.enabled)
                if enabled and p.weights @ seed[p.biomass_indices[:,i]]>0]
    present = [(j,i) for j in active for i in positive
               if p.dispersal_yr>0 or seed[4*j+1+i]>0]
    if not present:
        return None
    starting = seed.copy()
    local = model.fluxes(starting,p)["local"]
    for j,i in present:
        if starting[4*j+1+i]==0:
            total = p.weights @ seed[p.biomass_indices[:,i]]
            starting[4*j+1+i] = max(p.dispersal_yr*total/max(abs(local[j]["net_growth_yr"][i]),1e-3),1e-20)
    acetate_patches = [j for j in active if (j,0) in present]
    for j in acetate_patches:
        if starting[4*j+3]<=0:
            f = core.fluxes_at_temperature(model.local_state(starting,j),p.base,float(model.temperatures(starting,p)[j]))
            starting[4*j+3] = max(f["acetate_production_mol_l_yr"]/(f["k_rec_yr"]+f["k_other_yr"]),1e-20)
    values = [starting[4*j]/100 for j in active]
    values += [np.log(starting[4*j+1+i]/BIOMASS_SCALE) for j,i in present]
    values += [np.log(starting[4*j+3]/BIOMASS_SCALE) for j in acetate_patches]
    values += [starting[-1]/.2]
    n = len(active)
    def decode(z):
        y = np.zeros(p.state_size)
        for j,value in zip(active,z[:n]):y[4*j]=100*value
        for (j,i),value in zip(present,z[n:]):y[4*j+1+i]=BIOMASS_SCALE*np.exp(value)
        for j,value in zip(acetate_patches,z[n+len(present):]):y[4*j+3]=BIOMASS_SCALE*np.exp(value)
        y[-1]=z[-1]*.2
        return y
    supply = core.supply_h2(p.base)*core.HOURS_PER_YEAR
    rate = core.HOURS_PER_YEAR*p.base.biology.loss_h
    def equations(z):
        y=decode(z);f=model.fluxes(y,p,trial_extension=True)
        mean=p.weights @ y[p.biomass_indices]
        result=[(f["local"][j]["supply_h2_mol_l_yr"]-sum(f["local"][j]["uptake_h2_mol_l_yr"])
                 -f["local"][j]["outlet_h2_mol_l_yr"])/supply for j in active]
        result += [(f["local"][j]["net_growth_yr"][i]+p.dispersal_yr*(mean[i]/y[4*j+1+i]-1))/rate for j,i in present]
        result += [(f["local"][j]["acetate_production_mol_l_yr"]-f["local"][j]["acetate_recycling_mol_l_yr"]
                    -f["local"][j]["acetate_export_mol_l_yr"])/(supply/4) for j in acetate_patches]
        result += [(f["methane_source_ratio_yr"]-f["methane_loss_ratio_yr"])/(core.inventory_to_ratio(p.base)*supply/4)]
        return np.asarray(result)
    pressure_max=p.base.biology.atmosphere_pa+core.supply_h2(p.base)/p.base.biology.exchange_mol_l_h_pa
    lower=[0.]*n+[-100.]*(len(present)+len(acetate_patches))+[0.]
    upper=[pressure_max/100]*n+[30.]*(len(present)+len(acetate_patches))+[5.]
    fit=least_squares(equations,np.asarray(values),bounds=(lower,upper),jac="3-point",
                      x_scale="jac",ftol=1e-12,xtol=1e-12,gtol=1e-12,max_nfev=400)
    y=decode(fit.x)
    if (max(abs(equations(fit.x)))>1e-8 or "unsupported" in model.temperature_flags(y,p)
            or max(abs(scaled_residual(y,p)))>1e-8):
        return None
    return describe(y,p)


@lru_cache(maxsize=None)
def conditional_states(p, guild, n_grid=121):
    conditional=replace(p,base=replace(p.base,enabled=(guild==0,guild==1)))
    zero=replace(conditional,dispersal_yr=0.)
    def branch(r):
        y=np.zeros(p.state_size);y[-1]=r
        ts=model.temperatures(y,p)
        if "unsupported" in model.temperature_flags(y,p):return None
        for j,w in enumerate(p.weights):
            if w:
                block=local_resident(r,float(ts[j]),conditional.base,guild)
                if block is None:return None
                y[4*j:4*j+4]=block[:4]
        return y
    grid=core._ratio_grid(p.base,n_grid)
    def balance(r):
        y=branch(r)
        return model.rhs(y,zero)[-1] if y is not None else np.nan
    candidates=[]
    for r in core._roots(balance,grid,1e-14):
        seed=branch(r)
        result=describe(seed,conditional) if p.dispersal_yr==0 else refine(seed,conditional)
        if result is None and p.dispersal_yr>0:
            current=seed
            for d in np.geomspace(min(1e-6,p.dispersal_yr),p.dispersal_yr,6):
                step=refine(current,replace(conditional,dispersal_yr=float(d)))
                if step is None:break
                current=step["y"]
            else:result=describe(current,conditional)
        if result is not None and not any(abs(result["r"]-old["r"])<1e-9 for old in candidates):
            candidates.append(result)
    return candidates
