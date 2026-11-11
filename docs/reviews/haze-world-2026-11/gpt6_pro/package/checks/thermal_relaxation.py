"""Reviewer counterfactual: retain all equilibria, give temperature finite relaxation.

Run with the tagged repository installed and this script outside its worktree.
This is a structural sensitivity experiment, not a calibrated Archean climate.
"""
from dataclasses import replace
import json
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from terra_prisca.haze_world import population_coupling as c
from terra_prisca.haze_world.methane_budget import temperature_k

OUT = Path(__file__).resolve().parent

def fixed_temperature_rhs(y, p, t):
    f = c.fluxes_at_temperature(y, p, t)
    return np.r_[
        (f['supply_h2_mol_l_yr'] - sum(f['uptake_h2_mol_l_yr']) - f['outlet_h2_mol_l_yr']) / c.HENRY_30C_MOL_L_PA,
        np.asarray(y)[1:3] * f['net_growth_yr'] * p.enabled,
        f['acetate_production_mol_l_yr'] - f['acetate_recycling_mol_l_yr'] - f['acetate_export_mol_l_yr'],
        f['methane_source_ratio_yr'] - f['methane_loss_ratio_yr'],
    ]

def jacobian(fun, x, scales, step):
    """Five-point stencil, similarity-scaled physical coordinates."""
    j=np.empty((len(x),len(x)))
    for k,s in enumerate(scales):
        d=np.eye(len(x))[k]*s*step
        j[:,k]=(-fun(x+2*d)+8*fun(x+d)-8*fun(x-d)+fun(x-2*d))/(12*s*step)*s/scales
    return j

def six_rhs(z, p, tau):
    return np.r_[fixed_temperature_rhs(z[:5],p,z[5]),(temperature_k(z[4],p.climate)-z[5])/tau]

def analyze(f,step=1e-5,activity='fixed'):
    p=replace(c.reference(),acetate_fraction=f,activity_feedback=activity)
    e=next(x for x in c.equilibrium_states(p) if x['kind']=='mixed' and x['stable'])
    y=e['y']; t=e['t_k']; z=np.r_[y,t]
    scales=np.r_[np.maximum(abs(y),[10.,1e-4,1e-4,1e-5,.01]),1.]
    eig=np.linalg.eigvals(jacobian(lambda v:c.rhs(v,p),y,scales[:5],step))
    base=sorted(eig,key=lambda x:x.real,reverse=True)
    rows=[]
    def vals(tau):
        return np.linalg.eigvals(jacobian(lambda v:six_rhs(v,p,tau),z,scales,step))
    def maximum(tau):return max(vals(tau).real)
    tau_grid=[1e-5,.01,.05,.1,.15,.2,.5,1.,2.,5.,10.,30.,100.,300.,1000.,10000.]
    critical=[]
    for x1,x2 in zip(tau_grid[:-1],tau_grid[1:]):
        if maximum(x1)*maximum(x2)<0:critical.append(brentq(maximum,x1,x2,xtol=1e-10))
    for tau in tau_grid:
        v=vals(tau); lead=v[np.argmax(v.real)]
        rows.append(dict(tau_temperature_years=tau,max_real_per_year=float(lead.real),imag_per_year=float(abs(lead.imag)),period_years=float(2*np.pi/abs(lead.imag)) if lead.imag else None))
    # Independent block construction from fixed-T ecological matrix and dF/dT.
    a=jacobian(lambda v:fixed_temperature_rhs(v,p,t),y,scales[:5],step)
    h=step
    b=(-fixed_temperature_rhs(y,p,t+2*h)+8*fixed_temperature_rhs(y,p,t+h)-8*fixed_temperature_rhs(y,p,t-h)+fixed_temperature_rhs(y,p,t-2*h))/(12*h)/scales[:5]
    dr=scales[4]*step
    slope=(temperature_k(y[4]+dr,p.climate)-temperature_k(y[4]-dr,p.climate))/(2*dr)
    mat=np.zeros((6,6));mat[:5,:5]=a;mat[:5,5]=b;mat[5,4]=slope*scales[4];mat[5,5]=-1
    block_eig=np.linalg.eigvals(mat)
    direct=vals(1.)
    discrepancy=max(min(abs(v-w) for w in direct) for v in block_eig)
    # Chain rule recovers original reduced 5-stock Jacobian.
    reduced=a.copy();reduced[:,4]+=b*slope*scales[4]
    reduced_err=float(np.max(abs(reduced-jacobian(lambda v:c.rhs(v,p),y,scales[:5],step))))
    return dict(f=f,activity_feedback=activity,stencil_step=step,equilibrium=y.tolist(),temperature_k=t,
        residual_six_at_tau_1=six_rhs(z,p,1.).tolist(),
        original_eigenvalues=[dict(real=float(v.real),imag=float(v.imag)) for v in base],
        tau_critical_years=critical[0] if critical else None,all_detected_critical_times=critical,
        block_vs_direct_eigenvalue_max_abs_difference=float(discrepancy),
        chain_rule_jacobian_max_abs_difference=reduced_err,
        thermal_relaxation_rows=rows)

if __name__=='__main__':
    result=[analyze(f,step,activity) for activity in ('fixed','products') for f in (0.,.5) for step in (1e-4,1e-5,1e-6)]
    (OUT/'thermal_relaxation_results.json').write_text(json.dumps(result,indent=2)+'\n')
    for row in result:
        print(row['activity_feedback'],row['f'],row['stencil_step'],'critical_tau',row['tau_critical_years'],'block_error',row['block_vs_direct_eigenvalue_max_abs_difference'],'chain_error',row['chain_rule_jacobian_max_abs_difference'])
        if row['stencil_step']==1e-5:
            for q in row['thermal_relaxation_rows']:print(q)
