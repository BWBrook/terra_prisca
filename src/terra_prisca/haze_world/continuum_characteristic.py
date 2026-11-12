"""Independent four-variable characteristic reduction for weighted habitats.

Local derivatives are assembled from uptake equations, not the production
Jacobian. Elimination poles and back-substitution residuals are retained.
"""

from dataclasses import dataclass, replace
from types import SimpleNamespace

import numpy as np
from scipy.optimize import brentq, root

from . import population_coupling as physical
from .two_guilds import guilds


@dataclass
class CharacteristicBlocks:
    local: np.ndarray
    injection: np.ndarray
    emission: np.ndarray
    mean_selector: np.ndarray
    weights: np.ndarray
    methane_direct: float
    temperature_direct: float
    climate_slope: float
    local_scales: np.ndarray
    global_scales: np.ndarray

    @property
    def n(self):
        return len(self.weights)

    @property
    def sink_edge(self):
        return float(np.max(np.linalg.eigvals(self.local).real))


def _pair(x, ratio, temperature, p):
    result = guilds(float(temperature)-273.15, p.base.biology)
    factors = np.ones(2)
    if p.chemistry in ('products', 'acetate_only'):
        factors[0] = (x[3]/p.base.acetate_reference_mol_l)**.25
    if p.chemistry in ('products', 'methane_only'):
        factors[1] = (ratio*physical.co2_pressure_pa(p.base.climate.case)/p.base.methane_reference_pa)**.25
    return tuple(replace(g, threshold_pa=g.threshold_pa*f) for g,f in zip(result,factors))


def _flows(x, ratio, temperature, p):
    pair = _pair(x, ratio, temperature, p)
    uptake = np.array([g.uptake(x[0]) for g in pair])
    yields = np.array([g.yield_g_mol for g in pair])
    synthesis = yields*(uptake-np.array([g.maintenance for g in pair]))
    catabolism = uptake-np.array([g.assimilation_mol_g for g in pair])*np.maximum(synthesis,0.)
    rec, export = physical.recycling_rates(temperature,p.base)
    year = physical.HOURS_PER_YEAR
    local = np.r_[year/physical.HENRY_30C_MOL_L_PA*(physical.supply_h2(p.base)-uptake@x[1:3]
                         -p.base.biology.exchange_mol_l_h_pa*(x[0]-p.base.biology.atmosphere_pa)),
                  year*x[1:3]*(synthesis-p.base.biology.loss_h)-p.dispersal_yr*x[1:3],
                  year*catabolism[0]*x[1]/4-(rec+export)*x[3]]
    emission = physical.inventory_to_ratio(p.base)*(year*catabolism[1]*x[2]/4+rec*x[3])
    return local,float(emission)


def _temperature_derivative(x, ratio, t, p, step):
    def values(temp):
        a,b=_flows(x,ratio,temp,p)
        return np.r_[a,b]
    low = 277.15 if p.base.biology.low_temperature_variant == 'none' else 273.
    if t-2*step < low:
        return (-3*values(t)+4*values(t+step)-values(t+2*step))/(2*step)
    if t+2*step > 303.15:
        return (3*values(t)-4*values(t-step)+values(t-2*step))/(2*step)
    return (values(t-2*step)-8*values(t-step)+8*values(t+step)-values(t+2*step))/(12*step)


def _climate_slope(ratio,p,side=0):
    curve=physical.response(p.base.climate.case)
    if ratio<curve.ratios[0]:
        q=p.base.climate
        return p.slope_multiplier*(curve.temperatures_k[0]-q.t_zero_k)/((q.bridge_scale+ratio)*np.log1p(curve.ratios[0]/q.bridge_scale))
    if ratio>curve.ratios[-1]:
        return 0.
    j=np.searchsorted(curve.ratios,ratio,side='left' if side<0 else 'right')-1
    if j<0:
        return _climate_slope(np.nextafter(curve.ratios[0],0.),p,side)
    if j>=len(curve.ratios)-1:
        return 0.
    return float(p.slope_multiplier*np.diff(curve.temperatures_k)[j]/np.diff(curve.ratios)[j])


def assemble(p,y,temperature_step=1e-4,side=0):
    """Assemble independently scaled local blocks and four global couplings."""
    y=np.asarray(y,float); offsets=np.asarray(p.offsets,float); weights=np.asarray(p.weights,float)
    n=len(weights)
    if y.shape!=(4*n+1,) or np.any(~np.isfinite(y)) or np.any(y<=0):
        raise ValueError('The characteristic check requires a strictly positive mixed state')
    if not np.isclose(sum(weights),1.) or np.any(weights<=0) or not all(p.base.enabled):
        raise ValueError('Use positive normalized weights and both enabled guilds')
    ratio=y[-1];t=float(physical.temperature_k(ratio,p.base.climate));stocks=y[:-1].reshape(n,4)
    scales=np.maximum(stocks,[10.,1e-5,1e-5,1e-6])
    global_scales=np.r_[np.maximum(weights@stocks[:,1:3],1e-5),max(ratio,.01),1.]
    local=np.zeros((n,4,4));inject=np.zeros((n,4,4));emission=np.zeros((n,4));selector=np.zeros((n,2,4))
    direct_r=[];direct_t=[]
    year=physical.HOURS_PER_YEAR;conv=physical.inventory_to_ratio(p.base)
    for j,(x,offset) in enumerate(zip(stocks,offsets)):
        pair=_pair(x,ratio,t+offset,p)
        q=np.array([g.uptake(x[0]) for g in pair]);ys=np.array([g.yield_g_mol for g in pair])
        syn=ys*(q-np.array([g.maintenance for g in pair]));coef=np.array([g.assimilation_mol_g for g in pair])
        cat=q-coef*np.maximum(syn,0.)
        slopes=np.array([g.rate_scale*g.km_pa/(g.km_pa+x[0]-g.threshold_pa)**2 if x[0]>g.threshold_pa else 0. for g in pair])
        dq=np.zeros((2,5));dq[:,0]=slopes
        if p.chemistry in ('products','acetate_only'):
            dq[0,3]=-slopes[0]*pair[0].threshold_pa/(4*x[3])
        if p.chemistry in ('products','methane_only'):
            dq[1,4]=-slopes[1]*pair[1].threshold_pa/(4*ratio)
        m=np.zeros((4,5))
        m[0]=-year/physical.HENRY_30C_MOL_L_PA*(x[1:3]@dq)
        m[0,0]-=year/physical.HENRY_30C_MOL_L_PA*p.base.biology.exchange_mol_l_h_pa
        m[0,1:3]=-year/physical.HENRY_30C_MOL_L_PA*q
        for k in (0,1):
            m[1+k]=year*x[1+k]*ys[k]*dq[k]
            m[1+k,1+k]+=year*(syn[k]-p.base.biology.loss_h)-p.dispersal_yr
        dcat=(1-coef*ys*(syn>0.))[:,None]*dq
        rec,export=physical.recycling_rates(t+offset,p.base)
        m[3]=year*x[1]/4*dcat[0]
        m[3,1]+=year*cat[0]/4;m[3,3]-=rec+export
        h=conv*year*x[2]/4*dcat[1]
        h[2]+=conv*year*cat[1]/4;h[3]+=conv*rec
        bt=_temperature_derivative(x,ratio,t+offset,p,temperature_step)
        local[j]=m[:,:4]*scales[j][None,:]/scales[j][:,None]
        inject[j,1,0]=p.dispersal_yr*global_scales[0]/scales[j,1]
        inject[j,2,1]=p.dispersal_yr*global_scales[1]/scales[j,2]
        inject[j,:,2]=m[:,4]*global_scales[2]/scales[j]
        inject[j,:,3]=bt[:4]*global_scales[3]/scales[j]
        emission[j]=h[:4]*scales[j]/global_scales[2]
        direct_r.append(h[4]);direct_t.append(bt[4]*global_scales[3]/global_scales[2])
        selector[j,0,1]=scales[j,1]/global_scales[0]
        selector[j,1,2]=scales[j,2]/global_scales[1]
    rr=float(weights@direct_r-p.base.loss.slope(ratio))
    rt=float(weights@direct_t)
    return CharacteristicBlocks(local,inject,emission,selector,weights,rr,rt,
        _climate_slope(ratio,p,side)*global_scales[2]/global_scales[3],scales,global_scales)


def matrix(blocks,lam,tau):
    resolved=np.linalg.solve(lam*np.eye(4)[None,:,:]-blocks.local,blocks.injection)
    result=np.zeros((4,4),dtype=complex)
    result[:2,:2]=np.eye(2)
    result[:2]-=np.einsum('n,nij,njk->ik',blocks.weights,blocks.mean_selector,resolved)
    result[2,2]=lam-blocks.methane_direct;result[2,3]=-blocks.temperature_direct
    result[2]-=np.einsum('n,ni,nij->j',blocks.weights,blocks.emission,resolved)
    result[3,2]=-blocks.climate_slope;result[3,3]=1+tau*lam
    return result


def tau_at_frequency(blocks,omega):
    if not np.isfinite(omega) or omega<=0:
        raise ValueError('Frequency must be positive')
    lam=1j*omega;m=matrix(blocks,lam,0.)
    scales=np.maximum(np.max(np.abs(m),axis=1),1.)
    m=m/scales[:,None]
    cofactor=np.linalg.det(m[:3,:3])/scales[3]
    denominator=lam*cofactor
    if not np.isfinite(denominator) or abs(denominator)<1e-28:
        return complex(np.nan,np.nan)
    return -np.linalg.det(m)/denominator


def validate_root(blocks,lam,tau):
    m=matrix(blocks,lam,tau);row_scales=np.maximum(np.max(abs(m),axis=1),1.)
    _,singular,vh=np.linalg.svd(m/row_scales[:,None])
    z=vh[-1].conj();response=np.linalg.solve(lam*np.eye(4)[None,:,:]-blocks.local,blocks.injection)
    x=np.einsum('nij,j->ni',response,z)
    local_res=lam*x-np.einsum('nij,nj->ni',blocks.local,x)-np.einsum('nij,j->ni',blocks.injection,z)
    means=np.einsum('n,nij,nj->i',blocks.weights,blocks.mean_selector,x)
    atm=blocks.methane_direct*z[2]+blocks.temperature_direct*z[3]+np.einsum('n,ni,ni->',blocks.weights,blocks.emission,x)
    full=np.r_[local_res.ravel(),z[:2]-means,lam*z[2]-atm,(1+tau*lam)*z[3]-blocks.climate_slope*z[2]]
    pole_distance=float(np.min(abs(np.linalg.eigvals(blocks.local)-lam)))
    residual=float(np.max(abs(full))/max(1.,np.max(abs(x)),np.max(abs(z))))
    return dict(smallest_singular=float(singular[-1]),backsubstitution_residual=residual,
                local_pole_distance=pole_distance,
                accepted=bool(singular[-1]<1e-7 and residual<1e-7 and pole_distance>1e-9))


def crossing_direction(blocks,lam,tau):
    at_root=matrix(blocks,lam,tau)
    scales=np.maximum(np.max(abs(at_root),axis=1),1.)
    normalized=at_root/scales[:,None]
    d_tau=lam*np.linalg.det(normalized[:3,:3])/scales[3]
    step=1e-5*max(abs(lam),.001)
    def determinant(z):
        return np.linalg.det(matrix(blocks,z,tau)/scales[:,None])
    d_lam=(determinant(lam-2*step)-8*determinant(lam-step)+8*determinant(lam+step)-determinant(lam+2*step))/(12*step)
    if abs(d_lam)<1e-20:
        return dict(crossing_direction='degenerate_unresolved',real_speed_per_tau=None)
    speed=-d_tau/d_lam
    return dict(crossing_direction='loss' if speed.real>0 else 'restabilisation',real_speed_per_tau=float(speed.real))


def critical_lags(blocks,max_tau=1e4,omega_bounds=(1e-6,10.),frequencies=361):
    """Find validated imaginary-axis crossings; not an interval-completeness proof."""
    grid=np.geomspace(*omega_bounds,frequencies)
    values=[tau_at_frequency(blocks,float(w)) for w in grid]
    roots=[]
    for lo,hi,a,b in zip(grid[:-1],grid[1:],values[:-1],values[1:]):
        if not np.isfinite([a.real,a.imag,b.real,b.imag]).all() or a.imag*b.imag>=0:
            continue
        try:
            omega=brentq(lambda w:tau_at_frequency(blocks,w).imag,float(lo),float(hi),xtol=1e-12)
            candidate=tau_at_frequency(blocks,omega)
            tau=float(candidate.real)
            if tau<=0 or tau>max_tau or abs(candidate.imag)>1e-5*max(1.,tau):
                continue
            check=validate_root(blocks,1j*omega,tau)
            if check['accepted'] and not any(abs(tau-r['tau_yr'])<1e-6*max(1.,tau) for r in roots):
                roots.append(dict(tau_yr=tau,omega_yr=float(omega),period_yr=float(2*np.pi/omega),
                                  **check,**crossing_direction(blocks,1j*omega,tau)))
        except (ValueError,np.linalg.LinAlgError):
            continue
    roots.sort(key=lambda r:r['tau_yr'])
    losses=[r for r in roots if r['crossing_direction']=='loss']
    return dict(status='crossing_found' if losses else 'not_detected_through_10000',
                critical_lag_yr=losses[0]['tau_yr'] if losses else None,
                crossings=roots,sink_edge_yr=blocks.sink_edge,
                frequency_bounds=list(omega_bounds),frequency_points=frequencies,
                limitation='Imaginary-axis crossings from finite frequency bracketing; initial stability and crossing direction require separate checks.')


def dense_matrix(blocks,tau):
    """Testing-only reconstruction of the same block system, without elimination."""
    if tau<=0:
        raise ValueError('Use positive lag for the dense reconstruction')
    n=blocks.n;m=np.zeros((4*n+2,4*n+2))
    for j in range(n):
        s=slice(4*j,4*j+4);m[s,s]=blocks.local[j]
        for k in range(n):
            m[s,4*k:4*k+4]+=blocks.injection[j,:,:2]@blocks.mean_selector[k]*blocks.weights[k]
        m[s,-2:]=blocks.injection[j,:,2:]
        m[-2,s]=blocks.weights[j]*blocks.emission[j]
    m[-2,-2]=blocks.methane_direct;m[-2,-1]=blocks.temperature_direct
    m[-1,-2]=blocks.climate_slope/tau;m[-1,-1]=-1/tau
    return m


def homogeneous_frozen_gain(p,y,perturbations=(1e-3,1e-4,1e-5)):
    """Independent C0 sum-projection and finite-supply frozen-ratio checks."""
    if len(p.weights)!=1:
        raise ValueError('This independent finite-input control is homogeneous')
    y=np.asarray(y,float);blocks=assemble(p,y)
    full=dense_matrix(blocks,1.)
    ecology=full[:-1,:-1].copy()
    ecology[:,-1]+=full[:-1,-1]*blocks.climate_slope
    scales=np.r_[blocks.local_scales.ravel(),blocks.global_scales[2]]
    total=y[1]+y[2];share=y[1]/total
    embed=np.zeros((5,4));project=np.zeros((4,5))
    embed[0,0]=project[0,0]=1.
    embed[1,1]=share*total/scales[1];embed[2,1]=(1-share)*total/scales[2]
    project[1,1:3]=scales[1:3]/total
    embed[3,2]=project[2,3]=embed[4,3]=project[3,4]=1.
    frozen=project@ecology@embed
    forcing=np.zeros(5)
    forcing[0]=physical.HOURS_PER_YEAR/physical.HENRY_30C_MOL_L_PA*physical.supply_h2(p.base)/scales[0]
    closed=np.linalg.solve(ecology,-forcing);control=np.linalg.solve(frozen,-project@forcing)
    sc=float(blocks.climate_slope*closed[-1]);s0=float(blocks.climate_slope*control[-1])
    reduced_initial=np.array([y[0],total,y[3],y[4]])
    control_scales=np.array([scales[0],total,scales[3],scales[4]])
    rows=[]
    for step in perturbations:
        temperatures=[];residuals=[]
        for sign in (-1.,1.):
            base=replace(p.base,climate=replace(p.base.climate,donor_flux=p.base.climate.donor_flux*np.exp(sign*step)))
            q=SimpleNamespace(base=base,chemistry=p.chemistry,dispersal_yr=p.dispersal_yr)
            def decode(z):
                return np.exp(z)*control_scales
            def equations(z):
                pressure,b,acetate,ratio=decode(z)
                x=np.array([pressure,share*b,(1-share)*b,acetate])
                t=float(physical.temperature_k(ratio,base.climate))
                local,emission=_flows(x,ratio,t,q)
                abiotic=physical.atmosphere(base.climate.case)['flux_to_ratio_per_yr']*base.climate.abiotic_flux
                rates=np.r_[local[0],sum(local[1:3])+p.dispersal_yr*b,local[3],emission+abiotic-base.loss.rate(ratio)]
                return rates/control_scales*np.array([1e-5,1.,1.,1e4])
            solution=root(equations,np.log(reduced_initial/control_scales),tol=1e-10)
            residual=float(max(abs(equations(solution.x))))
            if residual>1e-7 or not np.isfinite(solution.x).all():
                raise ArithmeticError('Frozen-ratio finite-input root is unresolved')
            temperatures.append(float(physical.temperature_k(decode(solution.x)[-1],base.climate)))
            residuals.append(residual)
        slope=float((temperatures[1]-temperatures[0])/(2*step))
        rows.append(dict(log_supply_step=step,s0_finite=slope,relative_difference=abs(slope-s0)/max(abs(s0),1e-12),
                         maximum_root_residual=max(residuals)))
    return dict(sc=sc,s0=s0,gain_local=sc/s0 if abs(s0)>1e-12 else None,
                frozen_leading_real_yr=float(max(np.linalg.eigvals(frozen).real)),
                frozen_condition=float(np.linalg.cond(frozen)),finite_perturbations=rows,
                scope='Within-habitat composition frozen at the same operating point; total biomass and chemistry respond.')
