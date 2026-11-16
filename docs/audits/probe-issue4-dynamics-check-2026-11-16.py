"""Independent physical finite differences and analytic forcing windows for Issue 4."""
import json
from pathlib import Path
import sys
from dataclasses import replace
import numpy as np
from scipy.linalg import eigvals
from scipy.optimize import brentq
import argparse
parser=argparse.ArgumentParser(description="Bounded Issue 4 independent check; no integrations")
parser.add_argument("--output",type=Path,required=True)
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'models/haze_world/review'))
import issue4_acetate_fate as source
from terra_prisca.haze_world import dynamic_core as model,dynamic_realisation as b1
from terra_prisca.haze_world import population_coupling as core

j=json.loads((ROOT/'models/haze_world/review/issue4_acetate_fate.json').read_text())
out=[]
for row in j['sweep']:
    if row['f'] not in (.5,1.) or row['window_position'] not in (.5,.95):continue
    p=b1.parameters(row['chemistry'],row['f'],.001,row['potential'])
    roots=[x for x in model.equilibrium_states(p) if x['kind']=='mixed']
    eq=min(roots,key=lambda x:abs(x['r']-row['ratio']))
    y=np.array(eq['y']);T=eq['t_k'];s=model.state_scales(y,p)
    def F(z,t):return model.physical_rhs(z*s,p,t)/s
    z=y/s;J=np.zeros((5,5));h=1e-4
    for k in range(5):
        dz=np.eye(5)[k]*h
        J[:,k]=(F(z+dz,T)-F(z-dz,T))/(2*h)
    b=(F(z,T+.001)-F(z,T-.001))/.002
    hr=y[-1]*1e-5
    slope=(model.temperature(y[-1]+hr,p)-model.temperature(y[-1]-hr,p))/(2*hr)*s[-1]
    def leading(tau):
        if tau==0:
            A=J.copy();A[:,-1]+=b*slope
        else:
            A=np.zeros((6,6));A[:5,:5]=J;A[:5,5]=b
            A[5,4]=slope/tau;A[5,5]=-1/tau
        return float(max(eigvals(A).real))
    critical=None
    if row['tau_c'] is not None and row['tau_c']>0:
        critical=brentq(leading,row['tau_c']*.8,row['tau_c']*1.2,xtol=1e-8)
    delta=1e-4;temps=[]
    for sign in (-1,1):
        pp=replace(p,base=replace(p.base,climate=replace(p.base.climate,donor_flux=p.base.climate.donor_flux*np.exp(sign*delta))))
        rr=[x for x in model.equilibrium_states(pp) if x['kind']=='mixed']
        xx=min(rr,key=lambda x:abs(x['r']-eq['r']))
        temps.append(xx['t_k'])
    Sc=(temps[1]-temps[0])/(2*delta)
    out.append(dict(f=row['f'],position=row['window_position'],chemistry=row['chemistry'],
        archived_tau=row['tau_c'],finite_difference_tau=critical,leading_at_30=leading(30.),
        leading_at_zero=leading(0.),leading_at_1e4=leading(1e4),archived_Sc=row['Sc'],finite_difference_Sc=Sc,
        residual=float(np.max(abs(model.physical_rhs(y,p)/s)))))

q=j['parts'];curve=core.response('B');forcing=[]
for r in j['forcing']:
    P=r['potential'];captured=P/.3*q['j_ref']-q['outlet']
    base=core.reference()
    abiotic=core.atmosphere('B')['flux_to_ratio_per_yr']*base.climate.abiotic_flux
    conversion=core.inventory_to_ratio(base)*core.HOURS_PER_YEAR/4
    low=base.loss.lifetime_yr*(abiotic+conversion*captured*r['f']*q['eta_A'])
    high=base.loss.lifetime_yr*(abiotic+conversion*captured*q['eta_M'])
    intervals=[]
    for a,b,Ta,Tb in zip(curve.ratios[:-1],curve.ratios[1:],curve.temperatures_k[:-1],curve.temperatures_k[1:]):
        if Tb>=Ta:continue
        l=max(a,low);h=min(b,high)
        if l>=h:continue
        tlo=Ta+(l-a)*(Tb-Ta)/(b-a);thi=Ta+(h-a)*(Tb-Ta)/(b-a)
        intervals.append((q['t_star']-tlo,q['t_star']-thi))
    bounds=[min(a for a,b in intervals),max(b for a,b in intervals)]
    forcing.append(dict(f=r['f'],independent_low=bounds[0],independent_high=bounds[1],
                        independent_width=bounds[1]-bounds[0],archived_width=r['width_k'],ratio_low=low,ratio_high=high))

for row in out:
    if row['archived_tau'] is not None:
        assert np.isclose(row['finite_difference_tau'],row['archived_tau'],rtol=1e-6)
    assert np.isclose(row['finite_difference_Sc'],row['archived_Sc'],rtol=1e-5,atol=1e-6)
for row in forcing:
    assert abs(row['independent_width']-row['archived_width'])<.02
result=dict(margins=out,forcing=forcing)
args.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
