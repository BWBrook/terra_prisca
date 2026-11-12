"""Weighted habitat quadrature and operating-point composition counterfactual."""

from dataclasses import dataclass, replace

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.optimize import brentq
from scipy.sparse.linalg import LinearOperator, eigs, ArpackNoConvergence

from . import dynamic_core as reference
from . import population_coupling as core

YEAR = core.HOURS_PER_YEAR


@dataclass(frozen=True)
class Mesh:
    nodes: tuple[float, ...]
    weights: tuple[float, ...]
    panels: tuple[float, ...] = ()
    order: int = 4

    def __post_init__(self):
        x, w = np.array(self.nodes), np.array(self.weights)
        if x.ndim != 1 or not len(x) or w.shape != x.shape or np.any(np.diff(x) <= 0):
            raise ValueError('Use ordered distinct quadrature nodes and matching weights')
        if not np.all(np.isfinite(x)) or not np.all(np.isfinite(w)) or np.any(w <= 0) or abs(sum(w)-1) > 1e-12:
            raise ValueError('Quadrature weights must be positive, finite and sum to one')


def gauss_mesh(sigma, panels=None, order=4):
    if sigma == 0:
        return Mesh((0.,), (1.,), (), order)
    if order < 4:
        raise ValueError('At least four Gauss nodes per panel are required')
    edges = np.linspace(-sigma, sigma, 5) if panels is None else np.asarray(panels)
    if len(edges) < 2 or np.any(np.diff(edges) <= 0) or abs(edges[0]+sigma) > 1e-10 or abs(edges[-1]-sigma) > 1e-10:
        raise ValueError('Panels must partition the full uniform support')
    x, w = leggauss(order)
    nodes, weights = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        nodes.extend((lo+hi)/2+(hi-lo)/2*x)
        weights.extend((hi-lo)/(4*sigma)*w)
    return Mesh(tuple(float(v) for v in nodes), tuple(float(v) for v in weights), tuple(float(v) for v in edges), order)


def midpoint_mesh(sigma, n):
    if sigma == 0:
        return Mesh((0.,), (1.,))
    return Mesh(tuple(sigma*(2*(np.arange(n)+.5)/n-1)), tuple(np.full(n, 1/n)))


@dataclass(frozen=True)
class WeightedParams:
    base: core.Coupled
    chemistry: str = 'fixed'
    sigma_k: float = 0.
    mesh: Mesh = Mesh((0.,), (1.,))
    dispersal_yr: float = .001
    slope_multiplier: float = 1.

    def __post_init__(self):
        if self.chemistry not in reference.CHEMISTRIES or self.sigma_k < 0 or self.dispersal_yr < 0:
            raise ValueError('Use a named chemistry and nonnegative spread and dispersal')
        if self.slope_multiplier <= 0 or not np.isfinite([self.sigma_k, self.dispersal_yr, self.slope_multiplier]).all():
            raise ValueError('Finite parameters and positive slope multiplier are required')
        if np.max(abs(self.offsets)) > self.sigma_k+1e-12:
            raise ValueError('Quadrature nodes exceed the declared support')

    @property
    def n(self): return len(self.mesh.nodes)
    @property
    def offsets(self): return np.asarray(self.mesh.nodes)
    @property
    def weights(self): return np.asarray(self.mesh.weights)
    @property
    def state_size(self): return 4*self.n+1
    @property
    def acetate_feedback(self): return self.chemistry in ('products','acetate_only')
    @property
    def methane_feedback(self): return self.chemistry in ('products','methane_only')


def _local(stocks, ratio, temperature, p, means):
    n = len(stocks)
    local = np.zeros((n,4)); emission = np.zeros(n)
    matrices = np.zeros((n,4,4)); rcolumns = np.zeros((n,4)); h = np.zeros((n,4)); hr = np.zeros(n)
    enabled = np.asarray(p.base.enabled)
    conversion = core.inventory_to_ratio(p.base)
    for j, (state, tk) in enumerate(zip(stocks, temperature)):
        pair = reference.local_guilds(state, ratio, float(tk), p)
        pressure, xa, xm, acetate = state
        x = state[1:3]*enabled
        uptake = np.array([float(g.uptake(pressure)) for g in pair])
        yields = np.array([g.yield_g_mol for g in pair])
        growth = yields*(uptake-np.array([g.maintenance for g in pair]))
        coefficient = np.array([g.assimilation_mol_g for g in pair])
        catabolic = uptake-coefficient*np.maximum(growth,0.)
        rec, export = core.recycling_rates(float(tk),p.base)
        local[j,0] = YEAR/core.HENRY_30C_MOL_L_PA*(core.supply_h2(p.base)-uptake@x-p.base.biology.exchange_mol_l_h_pa*(pressure-p.base.biology.atmosphere_pa))
        local[j,1:3] = YEAR*x*(growth-p.base.biology.loss_h)+p.dispersal_yr*(means-state[1:3])*enabled
        local[j,3] = YEAR/4*catabolic[0]*x[0]-(rec+export)*acetate
        emission[j] = conversion*(YEAR/4*catabolic[1]*x[1]+rec*acetate)
        slopes = np.array([g.rate_scale*g.km_pa/(g.km_pa+pressure-g.threshold_pa)**2 if pressure > g.threshold_pa else 0. for g in pair])
        dq = np.zeros((2,4)); dq[:,0] = slopes
        if p.acetate_feedback and acetate > 0:
            dq[0,3] = -slopes[0]*pair[0].threshold_pa/(4*acetate)
        qr = np.zeros(2)
        if p.methane_feedback and ratio > 0:
            qr[1] = -slopes[1]*pair[1].threshold_pa/(4*ratio)
        a = matrices[j]
        a[0] = -YEAR/core.HENRY_30C_MOL_L_PA*(x@dq)
        a[0,0] -= YEAR/core.HENRY_30C_MOL_L_PA*p.base.biology.exchange_mol_l_h_pa
        a[0,1:3] = -YEAR/core.HENRY_30C_MOL_L_PA*uptake*enabled
        rcolumns[j,0] = -YEAR/core.HENRY_30C_MOL_L_PA*(x@qr)
        for k in (0,1):
            a[1+k] = YEAR*x[k]*yields[k]*dq[k]
            a[1+k,1+k] += YEAR*(growth[k]-p.base.biology.loss_h)*enabled[k]-p.dispersal_yr*enabled[k]
            rcolumns[j,1+k] = YEAR*x[k]*yields[k]*qr[k]
        factor = 1-coefficient*yields*(growth > 0.)
        a[3] = YEAR/4*x[0]*factor[0]*dq[0]
        a[3,1] += YEAR/4*catabolic[0]*enabled[0]
        a[3,3] -= rec+export
        rcolumns[j,3] = YEAR/4*x[0]*factor[0]*qr[0]
        h[j] = conversion*YEAR/4*x[1]*factor[1]*dq[1]
        h[j,2] += conversion*YEAR/4*catabolic[1]*enabled[1]
        h[j,3] += conversion*rec
        hr[j] = conversion*YEAR/4*x[1]*factor[1]*qr[1]
    return local, emission, matrices, rcolumns, h, hr


def physical_rhs(y, p, temperature_k=None):
    y=np.asarray(y,float)
    if y.shape!=(p.state_size,): raise ValueError('Wrong weighted-habitat state size')
    stocks=y[:-1].reshape(p.n,4)
    t=reference.temperature(y[-1],p) if temperature_k is None else float(temperature_k)
    local, emitted, *_ = _local(stocks,y[-1],t+p.offsets,p,p.weights@stocks[:,1:3])
    abiotic=core.atmosphere(p.base.climate.case)['flux_to_ratio_per_yr']*p.base.climate.abiotic_flux
    return np.r_[local.ravel(),p.weights@emitted+abiotic-p.base.loss.rate(y[-1])]


def per_capita(y,p):
    y=np.asarray(y); stocks=y[:-1].reshape(p.n,4); t=reference.temperature(y[-1],p)
    means=p.weights@stocks[:,1:3]; out=np.zeros((p.n,2))
    for j, tk in enumerate(t+p.offsets):
        pair=reference.local_guilds(stocks[j],y[-1],tk,p)
        for k,g in enumerate(pair):
            if p.base.enabled[k]:
                out[j,k]=YEAR*(g.yield_g_mol*(g.uptake(stocks[j,0])-g.maintenance)-p.base.biology.loss_h)+p.dispersal_yr*(means[k]/stocks[j,k+1]-1)
    return out


@dataclass
class Blocks:
    local: np.ndarray
    mean: np.ndarray
    ratio: np.ndarray
    temperature: np.ndarray
    emission: np.ndarray
    emission_ratio: float
    emission_temperature: float
    selector: np.ndarray
    weights: np.ndarray
    climate_slope: float


def local_blocks(y,p,temperature_step=1e-4):
    y=np.asarray(y); x=y[:-1].reshape(p.n,4); t=reference.temperature(y[-1],p)
    means=p.weights@x[:,1:3]
    _,_,a,c,h,hr=_local(x,y[-1],t+p.offsets,p,means)
    step=float(temperature_step)
    low=277.15 if p.base.biology.low_temperature_variant=='none' else 273.
    if t-p.sigma_k-low<2*step:
        points=(0,1,2); coef=(-3,4,-1); denom=2*step
    elif 303.15-t-p.sigma_k<2*step:
        points=(0,-1,-2);coef=(3,-4,1);denom=2*step
    else:
        points=(-2,-1,1,2);coef=(1,-8,8,-1);denom=12*step
    b=np.zeros_like(x); ht=0.
    for offset,factor in zip(points,coef):
        flow,emitted,*_=_local(x,y[-1],t+p.offsets+offset*step,p,means)
        b+=factor*flow/denom;ht+=factor*(p.weights@emitted)/denom
    injection=np.zeros((p.n,4,2)); injection[:,1,0]=p.dispersal_yr*p.base.enabled[0];injection[:,2,1]=p.dispersal_yr*p.base.enabled[1]
    return Blocks(a,injection,c,b,h,float(p.weights@hr-p.base.loss.slope(y[-1])),float(ht),
                  np.array([[0.,1.,0.,0.],[0.,0.,1.,0.]]),p.weights,reference.climate_slope(y[-1],p))


def block_solve(blocks,local_rhs,global_rhs,climate=True):
    b=blocks; v=b.ratio+b.temperature*b.climate_slope if climate else b.ratio
    scalar=b.emission_ratio+b.emission_temperature*b.climate_slope if climate else b.emission_ratio
    k=b.selector.shape[0]
    rhs=np.concatenate((b.mean,v[:,:,None],np.asarray(local_rhs)[:,:,None]),axis=2)
    solved=np.linalg.solve(b.local,rhs)
    z=solved[:,:,:k]; zr=solved[:,:,k]; t=solved[:,:,k+1]
    dtype=np.result_type(solved,global_rhs)
    schur=np.zeros((k+1,k+1),dtype=dtype);right=np.zeros(k+1,dtype=dtype)
    schur[:k,:k]=np.eye(k)+np.einsum('n,ab,nbk->ak',b.weights,b.selector,z)
    schur[:k,k]=np.einsum('n,ab,nb->a',b.weights,b.selector,zr)
    right[:k]=np.einsum('n,ab,nb->a',b.weights,b.selector,t)
    schur[k,:k]=-np.einsum('n,nb,nbk->k',b.weights,b.emission,z)
    schur[k,k]=scalar-np.einsum('n,nb,nb->',b.weights,b.emission,zr)
    right[k]=global_rhs-np.einsum('n,nb,nb->',b.weights,b.emission,t)
    solution=np.linalg.solve(schur,right)
    local=t-np.einsum('nbk,k->nb',z,solution[:k])-zr*solution[k]
    return np.r_[local.ravel(),solution[k]],float(np.linalg.cond(schur))


def dense_matrix(y,p,tau=0.,blocks=None):
    b=local_blocks(y,p) if blocks is None else blocks
    n,m,k=b.local.shape[0],b.local.shape[1],b.selector.shape[0]
    size=n*m+1; out=np.zeros((size+(tau>0),)*2)
    for j in range(n):
        ix=slice(j*m,(j+1)*m);out[ix,ix]=b.local[j]
        for q in range(n):out[ix,q*m:(q+1)*m]+=b.mean[j]@b.selector*b.weights[q]
        out[ix,size-1]=b.ratio[j];out[size-1,ix]=b.emission[j]*b.weights[j]
        if tau>0:out[ix,size]=b.temperature[j]
        else:out[ix,size-1]+=b.temperature[j]*b.climate_slope
    out[size-1,size-1]=b.emission_ratio
    if tau>0:
        out[size-1,size]=b.emission_temperature
        out[size,size-1]=b.climate_slope/tau;out[size,size]=-1/tau
    else:out[size-1,size-1]+=b.emission_temperature*b.climate_slope
    return out


def linear_operator(y,p,tau=0.,blocks=None):
    b=local_blocks(y,p) if blocks is None else blocks
    n,m=b.local.shape[:2];size=n*m+1
    def matvec(v):
        x=np.asarray(v[:size-1]).reshape(n,m);r=v[size-1]
        t=v[size] if tau>0 else b.climate_slope*r
        mean=b.selector@(b.weights@x)
        out=np.einsum('nij,nj->ni',b.local,x)+np.einsum('nik,k->ni',b.mean,mean)+b.ratio*r+b.temperature*t
        atm=np.einsum('n,ni,ni->',b.weights,b.emission,x)+b.emission_ratio*r+b.emission_temperature*t
        return np.r_[out.ravel(),atm,(b.climate_slope*r-t)/tau] if tau>0 else np.r_[out.ravel(),atm]
    return LinearOperator((size+(tau>0),)*2,matvec=matvec,dtype=float)


def inverse_operator(y,p,shift=0.,tau=0.,blocks=None):
    """Solve the full shifted operator through local blocks and a small Schur system."""
    b=local_blocks(y,p) if blocks is None else blocks
    n,m=b.local.shape[:2];size=n*m+1
    denominator=1+shift*tau
    if abs(denominator)<1e-14:raise np.linalg.LinAlgError('Thermal elimination pole')
    ratio=b.ratio+b.temperature*b.climate_slope/denominator
    scalar=b.emission_ratio-shift+b.emission_temperature*b.climate_slope/denominator
    shifted=Blocks(b.local-shift*np.eye(m)[None,:,:],b.mean,ratio,np.zeros_like(b.temperature),
                   b.emission,scalar,0.,b.selector,b.weights,0.)
    def solve(v):
        local=np.asarray(v[:size-1]).reshape(n,m)
        right=v[size-1]
        if tau>0:
            local=local+b.temperature*tau*v[size]/denominator
            right=right+b.emission_temperature*tau*v[size]/denominator
        result,_=block_solve(shifted,local,right,False)
        return np.r_[result,(b.climate_slope*result[-1]-tau*v[size])/denominator] if tau>0 else result
    return LinearOperator((size+(tau>0),)*2,matvec=solve,dtype=np.result_type(shift,float))


def operator_scales(y,p,blocks=None,tau=0.):
    if blocks is not None and blocks.local.shape[1]==3:
        x=np.asarray(y[:-1]).reshape(p.n,4)
        base=np.r_[np.c_[np.maximum(x[:,0],10.),np.maximum(x[:,1:3].sum(axis=1),1e-5),np.maximum(x[:,3],1e-6)].ravel(),max(y[-1],.01)]
    else:base=reference.state_scales(y,p)
    return np.r_[base,1.] if tau>0 else base


def scaled_operator(y,p,tau=0.,blocks=None,shift=None):
    b=local_blocks(y,p) if blocks is None else blocks
    scale=operator_scales(y,p,b,tau)
    physical=linear_operator(y,p,tau,b) if shift is None else inverse_operator(y,p,shift,tau,b)
    def matvec(value):return physical@(np.asarray(value)*scale)/scale
    return LinearOperator(physical.shape,matvec=matvec,dtype=physical.dtype)


def spectrum(y,p,tau=0.,blocks=None,shifts=(0.,.005j,.05j),k=6,tolerance=1e-11,residual_tolerance=1e-8):
    b=local_blocks(y,p) if blocks is None else blocks
    operator=scaled_operator(y,p,tau,b)
    if operator.shape[0]<=24:
        scale=operator_scales(y,p,b,tau)
        matrix=dense_matrix(y,p,tau,b)*scale[None,:]/scale[:,None]
        values=np.linalg.eigvals(matrix)
        return dict(status='dense',eigenvalues=values,leading_real=float(max(values.real)),
                    max_eigen_residual=0.,failures=[])
    candidates=[];residuals=[];failures=[]
    complex_operator=LinearOperator(operator.shape,matvec=lambda z:operator@z,dtype=complex)
    for shift in shifts:
        try:
            inverse=scaled_operator(y,p,tau,b,complex(shift))
            values,vectors=eigs(complex_operator,k=min(k,operator.shape[0]-2),sigma=complex(shift),
                                OPinv=inverse,which='LM',tol=tolerance,maxiter=1500)
        except (np.linalg.LinAlgError,ArpackNoConvergence) as error:
            failures.append(dict(shift=[float(np.real(shift)),float(np.imag(shift))],error=type(error).__name__))
            continue
        for value,vector in zip(values,vectors.T):
            error=float(np.linalg.norm(operator@vector-value*vector)/max(np.linalg.norm(vector),1e-300))
            if error<residual_tolerance:
                candidates.append(value);residuals.append(error)
    if not candidates:return dict(status='unresolved',eigenvalues=np.array([],complex),leading_real=None,max_eigen_residual=None,failures=failures)
    values=np.asarray(candidates)
    return dict(status='shift_invert_candidates' if not failures else 'partial_shift_invert',eigenvalues=values,
                leading_real=float(max(values.real)),max_eigen_residual=max(residuals),failures=failures)


def frozen_projection(y,p):
    x=np.asarray(y[:-1]).reshape(p.n,4);total=x[:,1:3].sum(axis=1)
    if np.any(total<=0):raise ValueError('Freeze only a community with positive total biomass')
    share=x[:,1]/total
    expand=np.zeros((p.n,4,3));collapse=np.zeros((p.n,3,4))
    expand[:,0,0]=1;expand[:,1,1]=share;expand[:,2,1]=1-share;expand[:,3,2]=1
    collapse[:,0,0]=1;collapse[:,1,1:3]=1;collapse[:,2,3]=1
    return share,expand,collapse


def frozen_blocks(y,p,blocks=None):
    b=local_blocks(y,p) if blocks is None else blocks
    _,expand,collapse=frozen_projection(y,p)
    local=np.einsum('nai,nij,njb->nab',collapse,b.local,expand)
    mean=np.zeros((p.n,3,1));mean[:,1,0]=p.dispersal_yr
    return Blocks(local,mean,np.einsum('nai,ni->na',collapse,b.ratio),
                  np.einsum('nai,ni->na',collapse,b.temperature),
                  np.einsum('ni,nij->nj',b.emission,expand),b.emission_ratio,b.emission_temperature,
                  np.array([[0.,1.,0.]]),b.weights,b.climate_slope)


def slopes(y,p,side=0):
    b=local_blocks(y,p);b.climate_slope=reference.climate_slope(y[-1],p,side)
    if b.climate_slope==0:
        return dict(status='climate_insensitive',Sc=0.,S0=0.,G_loc=None)
    forcing=np.zeros((p.n,4));forcing[:,0]=YEAR/core.HENRY_30C_MOL_L_PA*core.supply_h2(p.base)
    result={}
    for name,blocks,forcing_local in (('Sc',b,forcing),('S0',frozen_blocks(y,p,b),forcing[:,[0,1,3]])):
        try:
            derivative,condition=block_solve(blocks,-forcing_local,0.)
            result[name]=float(b.climate_slope*derivative[-1]);result[name+'_schur_condition']=condition
        except np.linalg.LinAlgError:
            result[name]=None;result[name+'_schur_condition']=None
    if result['Sc'] is None or result['S0'] is None:
        status='singular_response'
    elif abs(result['S0'])<1e-10:
        status='zero_frozen_slope'
    else:status='defined'
    result.update(status=status,G_loc=result['Sc']/result['S0'] if status=='defined' else None)
    return result


def interpolate_state(y,old,new):
    x=np.asarray(y[:-1]).reshape(old.n,4)
    values=np.stack([np.exp(np.interp(new.offsets,old.offsets,np.log(np.maximum(x[:,j],1e-300)))) for j in range(4)],axis=1)
    return np.r_[values.ravel(),y[-1]]


def local_profile_correction(seed,p,means):
    """Correct interpolated nodes on their local resource/immigration manifold."""
    seed=np.asarray(seed);stocks=seed[:-1].reshape(p.n,4)
    corrected=[_local_endpoint(float(offset),means,seed[-1],p,value)
               for offset,value in zip(p.offsets,stocks)]
    if any(value is None for value in corrected):return None
    return np.r_[np.stack(corrected).ravel(),seed[-1]]


def equilibrium(seed,p,tolerance=1e-8,max_steps=70):
    y=np.asarray(seed,float).copy()
    if y.shape!=(p.state_size,) or np.any(y<=0):return None
    def residual(state):
        if reference.temperature_status(state,p)['physiology_status']!='in_domain':return np.inf
        f=physical_rhs(state,p);scale=reference.state_scales(state,p)
        return max(float(np.max(abs(f/scale))),float(np.max(abs(per_capita(state,p)))))
    score=residual(y)
    for iteration in range(max_steps):
        if score<tolerance:break
        b=local_blocks(y,p)
        # Equilibrium uses the actual climate curve, not its sensitivity multiplier.
        b.climate_slope/=p.slope_multiplier
        try:delta,_=block_solve(b,-physical_rhs(y,p)[:-1].reshape(p.n,4),-physical_rhs(y,p)[-1])
        except np.linalg.LinAlgError:return None
        fraction=min(1.,float(.7/max(np.max(abs(delta/y)),.7)))
        accepted=False
        for _ in range(20):
            trial=y+fraction*delta
            trial_score=residual(trial) if np.all(trial>0) else np.inf
            if trial_score<score:
                y,score=trial,trial_score;accepted=True;break
            fraction/=2
        if not accepted:return None
    if score>=tolerance:return None
    return dict(y=y,r=float(y[-1]),t_k=reference.temperature(y[-1],p),residual=score,
                iterations=iteration,status='accepted',**reference.temperature_status(y,p))


def homogeneous_seeds(p):
    q=reference.DynamicParams(p.base,p.chemistry,dispersal_yr=p.dispersal_yr)
    return [r for r in reference.equilibrium_states(q) if r['kind']=='mixed' and r['status']=='accepted']


def homotopy(p,seed=None):
    starts=homogeneous_seeds(p) if seed is None else [seed]
    results=[]
    for start in starts:
        value=np.asarray(start['y'] if isinstance(start,dict) else start)
        y=np.r_[np.tile(value[:4],p.n),value[-1]] if len(value)==5 else value.copy()
        previous=0.
        steps=np.unique(np.r_[np.geomspace(.001,min(p.sigma_k,1.),8),np.arange(1.,p.sigma_k,.5),p.sigma_k]) if p.sigma_k else [0.]
        success=True
        for target in steps:
            found=_homotopy_step(y,p,previous,float(target))
            if found is None:success=False;break
            y=found['y'];previous=float(target)
        if success:results.append(found)
    return results


def _homotopy_step(y,p,previous,target,depth=0):
    factor=target/p.sigma_k if p.sigma_k else 0.
    mesh=Mesh(tuple(np.asarray(p.mesh.nodes)*factor),p.mesh.weights,
              tuple(np.asarray(p.mesh.panels)*factor) if p.mesh.panels else (),p.mesh.order)
    q=replace(p,sigma_k=float(target),mesh=mesh)
    found=equilibrium(y,q)
    if found is not None or depth>=14 or target-previous<1e-5:return found
    midpoint=(previous+target)/2
    middle=_homotopy_step(y,p,previous,midpoint,depth+1)
    return None if middle is None else _homotopy_step(middle['y'],p,midpoint,target,depth+1)


def _local_endpoint(offset,means,ratio,p,seed):
    tk=reference.temperature(ratio,p)+offset
    pair=reference.local_guilds([0.,0.,0.,0.],ratio,tk,p)
    original=reference.guilds(tk-273.15,p.base.biology)[0]
    d=p.dispersal_yr
    if d<=0:return None
    effective=p.base.biology.loss_h+d/YEAR
    ceiling=p.base.biology.atmosphere_pa+core.supply_h2(p.base)/p.base.biology.exchange_mol_l_h_pa
    caps=[g.rstar(effective) for g in pair]
    upper=min(ceiling,caps[1],caps[0] if not p.acetate_feedback else np.inf)
    upper-=max(1e-12,abs(upper)*1e-13)
    rec,export=core.recycling_rates(tk,p.base)
    def state_at(pressure):
        def material(acetate):
            gs=reference.local_guilds([pressure,0.,0.,acetate],ratio,tk,p)
            uptake=np.array([float(g.uptake(pressure)) for g in gs])
            growth=np.array([g.yield_g_mol*(q-g.maintenance) for g,q in zip(gs,uptake)])
            deficit=d-YEAR*(growth-p.base.biology.loss_h)
            if np.any(deficit<=0):return None
            biomass=d*means/deficit
            synthesis=np.maximum(growth,0.)
            cat=uptake-np.array([g.assimilation_mol_g for g in gs])*synthesis
            pool=YEAR/4*cat[0]*biomass[0]/(rec+export)
            return uptake,biomass,pool
        if p.acetate_feedback:
            kinetic=original.rstar(effective)-original.threshold_pa
            threshold=max(pressure-kinetic,0.)
            critical=p.base.acetate_reference_mol_l*(threshold/original.threshold_pa)**4 if np.isfinite(kinetic) else 0.
            lower=max(0.,critical)
            def balance(pool):
                result=material(pool)
                return pool-result[2] if result is not None else -1e100
            high=max(1e-8,lower*2+1e-10)
            while balance(high)<0 and high<1e6:high*=2
            if balance(high)<0:return None
            acetate=brentq(balance,lower,high,xtol=1e-16)
        else:
            result=material(0.)
            if result is None:return None
            acetate=result[2]
        result=material(acetate)
        if result is None:return None
        uptake,biomass,_=result
        balance=core.supply_h2(p.base)-uptake@biomass-p.base.biology.exchange_mol_l_h_pa*(pressure-p.base.biology.atmosphere_pa)
        return np.r_[pressure,biomass,acetate],float(balance)
    def balance(pressure):
        result=state_at(pressure)
        return result[1] if result is not None else -1e100
    try:
        pressure=brentq(balance,0.,upper,xtol=1e-13)
        result=state_at(pressure)
    except (ValueError,OverflowError):return None
    return None if result is None else result[0]


def refine_panels(y,p,force_mixed=False,max_logit_change=1.):
    if not p.mesh.panels:return p.mesh,dict(status='homogeneous',max_logit_change=0.,mixed_width_k=0.)
    x=np.asarray(y[:-1]).reshape(p.n,4);means=p.weights@x[:,1:3]
    edges=np.asarray(p.mesh.panels);endpoint=[]
    for edge in edges:
        seed=np.array([np.exp(np.interp(edge,p.offsets,np.log(np.maximum(x[:,j],1e-300)))) for j in range(4)])
        value=_local_endpoint(float(edge),means,y[-1],p,seed)
        if value is None:return p.mesh,dict(status='endpoint_unresolved')
        endpoint.append(np.log(value[1])-np.log(value[2]))
    endpoint=np.asarray(endpoint)
    node_logit=np.log(x[:,1])-np.log(x[:,2])
    ranges=[];mixed=[]
    for j,(lo,hi) in enumerate(zip(edges[:-1],edges[1:])):
        values=np.r_[endpoint[j:j+2],node_logit[(p.offsets>lo)&(p.offsets<hi)]]
        ranges.append(float(max(values)-min(values)))
        mixed.append(min(values)<np.log(99) and max(values)>-np.log(99))
    changes=np.asarray(ranges);mixed=np.asarray(mixed)
    split=mixed if force_mixed else changes>max_logit_change
    panels=np.unique(np.r_[edges,((edges[:-1]+edges[1:])/2)[split]])
    def logit_at(offset):
        seed=np.array([np.exp(np.interp(offset,p.offsets,np.log(np.maximum(x[:,j],1e-300)))) for j in range(4)])
        state=_local_endpoint(float(offset),means,y[-1],p,seed)
        if state is None:raise ValueError('Mixed-width root unresolved')
        return float(np.log(state[1])-np.log(state[2]))
    points=np.unique(np.r_[edges,p.offsets]); cuts=list(points)
    values=np.array([endpoint[np.flatnonzero(edges==z)[0]] if z in edges else node_logit[np.flatnonzero(p.offsets==z)[0]] for z in points])
    try:
        for lo,hi,a,b in zip(points[:-1],points[1:],values[:-1],values[1:]):
            for target in (-np.log(99),np.log(99)):
                if (a-target)*(b-target)<0:cuts.append(brentq(lambda z:logit_at(z)-target,lo,hi,xtol=1e-10))
        cuts=np.unique(cuts)
        width=float(sum(hi-lo for lo,hi in zip(cuts[:-1],cuts[1:]) if abs(logit_at((lo+hi)/2))<np.log(99)))
    except ValueError:
        return p.mesh,dict(status='endpoint_unresolved')
    return gauss_mesh(p.sigma_k,panels,p.mesh.order),dict(status='refined' if any(split) else 'logit_resolved',
        max_logit_change=float(max(changes)),mixed_width_k=width,panels_split=int(sum(split)),
        endpoint_logit=endpoint.tolist())


def adaptive_equilibrium(p,seed=None,max_levels=14,max_nodes=4096):
    if seed is None:
        roots=homotopy(p)
        if not roots:return dict(status='homotopy_unresolved')
        start=min(roots,key=lambda r:reference.climate_slope(r['r'],p))
    else:start=equilibrium(seed,p)
    if start is None:return dict(status='seed_unresolved')
    history=[];record=start
    for level in range(max_levels):
        mesh,diagnostic=refine_panels(record['y'],p)
        history.append(dict(level=level,n=p.n,**diagnostic))
        if diagnostic['status']=='logit_resolved':
            return dict(record,p=p,history=history,status='logit_resolved')
        if diagnostic['status']=='endpoint_unresolved':return dict(record,p=p,history=history,status='endpoint_unresolved')
        if len(mesh.nodes)>max_nodes:return dict(record,p=p,history=history,status='node_limit')
        q=replace(p,mesh=mesh);predictor=interpolate_state(record['y'],p,q)
        found=equilibrium(predictor,q)
        if found is None:
            means=p.weights@record['y'][:-1].reshape(p.n,4)[:,1:3]
            corrected=local_profile_correction(predictor,q,means)
            found=equilibrium(corrected,q) if corrected is not None else None
            history[-1]['local_profile_correction_attempted']=True
            history[-1]['local_profile_correction_accepted']=found is not None
        if found is None:return dict(record,p=p,history=history,status='refinement_root_unresolved')
        record,p=found,q
    return dict(record,p=p,history=history,status='level_limit')


def frozen_supply_check(y,p,step=1e-4):
    share,expand,collapse=frozen_projection(y,p)
    x=y[:-1].reshape(p.n,4)
    initial=np.c_[x[:,0],x[:,1:3].sum(axis=1),x[:,3]]
    answers=[]
    for multiplier in (np.exp(-step),np.exp(step)):
        q=replace(p,base=replace(p.base,climate=replace(p.base.climate,donor_flux=p.base.climate.donor_flux*multiplier)))
        z=np.r_[initial.ravel(),y[-1]]
        def reconstruct(state):
            values=np.einsum('nij,nj->ni',expand,state[:-1].reshape(p.n,3))
            return np.r_[values.ravel(),state[-1]]
        def residual(state):
            if np.any(state<=0):return np.inf
            full=reconstruct(state)
            if reference.temperature_status(full,q)['physiology_status']!='in_domain':return np.inf
            flow=physical_rhs(full,q)
            reduced=np.r_[np.einsum('nij,nj->ni',collapse,flow[:-1].reshape(p.n,4)).ravel(),flow[-1]]
            scales=np.maximum(abs(state),np.r_[np.tile([10.,1e-5,1e-6],p.n),.01])
            scales[np.arange(p.n)*3+1]=state[np.arange(p.n)*3+1]
            return float(max(abs(reduced/scales)))
        for _ in range(40):
            full=reconstruct(z);flow=physical_rhs(full,q)
            local=np.einsum('nij,nj->ni',collapse,flow[:-1].reshape(p.n,4))
            b=frozen_blocks(full,q)
            score=residual(z)
            if score<1e-9:break
            try:delta,_=block_solve(b,-local,-flow[-1])
            except np.linalg.LinAlgError:break
            alpha=min(1.,.7/max(np.max(abs(delta/z)),.7))
            for _ in range(20):
                trial=z+alpha*delta
                if residual(trial)<score:z=trial;break
                alpha/=2
            else:break
        full=reconstruct(z)
        score=residual(z)
        answers.append(dict(temperature_k=reference.temperature(full[-1],q),state=full,
                            residual=score,status='accepted' if score<1e-7 else 'unresolved',
                            maximum_ratio_error=float(max(abs(full[:-1].reshape(p.n,4)[:,1]/full[:-1].reshape(p.n,4)[:,1:3].sum(axis=1)-share)))))
    derivative=(answers[1]['temperature_k']-answers[0]['temperature_k'])/(2*step)
    return dict(status='passed' if all(r['status']=='accepted' for r in answers) else 'unresolved',
                S0_finite_difference=float(derivative),points=answers)
