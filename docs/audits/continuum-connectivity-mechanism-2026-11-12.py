"""Local Hopf-margin diagnostic on the four accepted sigma-one endpoint states."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import csv
import json

import numpy as np
from scipy.linalg import eig

from terra_prisca.haze_world import continuum_core as c, dynamic_core as d, population_coupling as p

ROOT=Path(__file__).resolve().parents[2]


def load(row):
    for path in (ROOT/'local/haze/continuum_habitats').glob('*.json'):
        record=json.loads(path.read_text())
        if not isinstance(record,dict) or not record.get('y'):continue
        keys=('fraction','sigma_k','dispersal_yr','nominal_potential')
        if record.get('chemistry')==row['chemistry'] and all(record.get(k)==float(row[k]) for k in keys) and abs(record['ratio']-float(row['ratio']))<1e-12:
            mesh=c.Mesh(tuple(record['offsets']),tuple(record['weights']),tuple(record['panels']))
            base=replace(p.reference(record['nominal_potential']),acetate_fraction=record['fraction'])
            params=c.WeightedParams(base,record['chemistry'],record['sigma_k'],mesh,record['dispersal_yr'])
            return record,params,np.array(record['y']),path
    raise FileNotFoundError('Accepted cached state not found')


def analyse(row,refine=False):
    record,q,y,path=load(row)
    tau=record['lag']['tau_c']
    if refine:
        mesh,_=c.refine_panels(y,q,force_mixed=True)
        qq=replace(q,mesh=mesh)
        found=c.equilibrium(c.interpolate_state(y,q,qq),qq)
        if found is None:raise ArithmeticError('Diagnostic mesh root unresolved')
        y,q=found['y'],qq
        record=dict(record,temperature_k=found['t_k'],ratio=found['r'],nodes=q.n)
    scale=c.operator_scales(y,q,tau=tau)
    def matrix(value,params=q):
        return c.dense_matrix(value,params,tau)*scale[None,:]/scale[:,None]
    for _ in range(5 if refine else 1):
        a=matrix(y)
        values,left,right=eig(a,left=True,right=True)
        candidates=np.flatnonzero(values.imag>0)
        index=candidates[np.argmax(values[candidates].real)]
        lam=values[index];lv=left[:,index];rv=right[:,index]
        overlap=np.vdot(lv,rv)
        if not refine or abs(lam.real)<1e-10:break
        derivative=np.vdot(lv,np.r_[np.zeros(len(a)-1),-a[-1]@rv])/overlap
        tau*=float(np.exp(np.clip(-lam.real/derivative.real,-.1,.1)))
    explicit=np.zeros_like(a)
    for guild in (1,2):
        ix=4*np.arange(q.n)+guild
        explicit[np.ix_(ix,ix)]=q.dispersal_yr*(np.ones((q.n,1))*q.weights[None,:]-np.eye(q.n))
    explicit=explicit*scale[None,:]/scale[:,None]
    logtau=np.zeros_like(a);logtau[-1]=-a[-1]
    derivative_tau=np.vdot(lv,logtau@rv)/overlap
    flow_d=np.zeros_like(y)
    stocks=y[:-1].reshape(q.n,4);means=q.weights@stocks[:,1:3]
    flow_d[:-1].reshape(q.n,4)[:,1:3]=q.dispersal_yr*(means-stocks[:,1:3])
    state_d,_=c.block_solve(c.local_blocks(y,q),-flow_d[:-1].reshape(q.n,4),0.)
    direct=np.vdot(lv,explicit@rv)/overlap
    components=[]
    for h in (1e-3,5e-4,2.5e-4):
        if np.any(y-h*state_d<=0):continue
        shifted=(matrix(y+h*state_d)-matrix(y-h*state_d))/(2*h)
        indirect=np.vdot(lv,shifted@rv)/overlap
        components.append(dict(log_d_step=h,lambda_explicit_real=float(direct.real),
            lambda_state_shift_real=float(indirect.real),lambda_logtau_real=float(derivative_tau.real),
            logtau_logd_explicit=float(-direct.real/derivative_tau.real),
            logtau_logd_state_shift=float(-indirect.real/derivative_tau.real),
            logtau_logd_total=float(-(direct+indirect).real/derivative_tau.real)))
    physical=rv*scale
    local=physical[:-2].reshape(q.n,4)
    ma=q.weights@local[:,1];mm=q.weights@local[:,2]
    normal=physical[-1]
    ratios=[ma/means[0]/normal,mm/means[1]/normal,(ma/means[0]-mm/means[1])/normal,physical[-2]/y[-1]/normal]
    return dict(fraction=q.base.acetate_fraction,dispersal_yr=q.dispersal_yr,nodes=q.n,
        tau_c_yr=tau,temperature_k=record['temperature_k'],climate_slope=d.climate_slope(y[-1],q),
        eigenvalue=[float(lam.real),float(lam.imag)],period_yr=float(2*np.pi/abs(lam.imag)),
        eigen_residual=float(np.linalg.norm(a@rv-lam*rv)),left_right_condition=float(1/abs(overlap)),
        temperature_logd=float(d.climate_slope(y[-1],q)*state_d[-1]),
        mean_A_logd=float(q.weights@state_d[:-1].reshape(q.n,4)[:,1]/means[0]),
        mean_M_logd=float(q.weights@state_d[:-1].reshape(q.n,4)[:,2]/means[1]),
        mode_per_kelvin={k:[float(v.real),float(v.imag)] for k,v in zip(('relative_mean_A','relative_mean_M','log_ratio_A_M','relative_methane'),ratios)},
        components=components,additional_mixed_panel_doubling=refine,input_path=str(path.relative_to(ROOT)),input_sha256=sha256(path.read_bytes()).hexdigest())


def main():
    rows=list(csv.DictReader((ROOT/'models/haze_world/figures/continuum_habitats/c1_resolved.csv').open()))
    selected=[r for r in rows if r['chemistry']=='fixed' and float(r['fraction']) in (0.,.5) and float(r['sigma_k'])==1 and float(r['dispersal_yr']) in (.0001,.001) and float(r['nominal_potential'])==.3]
    result=dict(scope='Four accepted endpoints and two extra mesh checks; local tangent diagnostic, not a finite-difference intervention at nonequilibrium or a global stability theorem.',
                rows=[analyse(r) for r in selected],refined_rows=[analyse(r,True) for r in selected if float(r['fraction'])==.5])
    files=[Path(__file__),ROOT/'src/terra_prisca/haze_world/continuum_core.py',ROOT/'models/haze_world/figures/continuum_habitats/c1_resolved.csv']
    result['source_sha256']={str(f.relative_to(ROOT)):sha256(f.read_bytes()).hexdigest() for f in files}
    Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
