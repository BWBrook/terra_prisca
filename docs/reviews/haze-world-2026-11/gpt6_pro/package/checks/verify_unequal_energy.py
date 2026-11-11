from dataclasses import replace
from pathlib import Path
import csv,json
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import minimize_scalar,brentq
from terra_prisca.haze_world import population_coupling as pc
from terra_prisca.haze_world import two_guilds as tg
p0=pc.reference();bio=p0.biology
base=tg.guilds(30.,bio)
with open('models/haze_world/evidence/kotsyurbenko2001_table2.csv') as h:table=list(csv.DictReader(h))
arrays=[]
for name in ['Acetobacterium bakii','methanogenic strain MSB']:
 rows=[r for r in table if r['strain']==name]
 arrays.append(tuple(np.array([float(r[k]) for r in rows]) for k in ['temperature_C','Vmax_nmol_h_for20mL','Km_Pa']))
ugrid=np.linspace(4,30,26001)
interpolators=[(PchipInterpolator(a[0],np.log(a[1]/a[1][-1])),PchipInterpolator(a[0],np.log(a[2]))) for a in arrays]
def vk(u,i,T,E,shape):
 nodes,v,k=arrays[i]
 if shape=='linear_shape':vv=np.interp(u,nodes,v)/v[-1];kk=np.interp(u,nodes,k)
 else:vv=np.exp(interpolators[i][0](u));kk=np.exp(interpolators[i][1](u))
 vv=base[i].rate_scale*vv*np.exp(-E/8.617333e-5*(1/T-1/(u+273.15)))
 return vv,kk

def best(T,E,i,shape):
 g=tg.guilds(T-273.15,bio)[i];q=g.maintenance+bio.loss_h/g.yield_g_mol
 def rstar(u):
  v,k=vk(u,i,T,E,shape)
  return g.threshold_pa+np.divide(k*q,v-q,out=np.full_like(np.asarray(v),np.inf),where=v>q)
 values=rstar(ugrid);j=int(np.argmin(values));u=float(ugrid[j])
 trials=[(float(values[j]),u)]+[(float(rstar(x)),float(x)) for x in arrays[i][0]]
 if 0<j<len(ugrid)-1:
  sol=minimize_scalar(rstar,bounds=(ugrid[j-1],ugrid[j+1]),method='bounded',options={'xatol':1e-12});trials.append((float(sol.fun),float(sol.x)))
 v,u=min(trials)
 return v,u,dict(grid_minimum=float(values[j]),grid_position_c=float(ugrid[j]),grid_step_c=.001,minimum_rstar=float(v),position_c=float(u))

def pair(T,energies,positions,shape):
 local=tg.guilds(T-273.15,bio)
 out=[]
 for i in (0,1):
  v,k=vk(positions[i],i,T,energies[i],shape);out.append(replace(local[i],rate_scale=float(v),km_pa=float(k)))
 return out

def rhs(y,p,energies,positions,shape):
 pressure,xa,xm,ac,r=y;T=float(pc.temperature_k(r,p.climate));gs=pair(T,energies,positions,shape)
 x=np.array([xa,xm]);uptake=np.array([g.uptake(pressure) for g in gs]);growth=np.array([g.yield_g_mol*(u-g.maintenance) for g,u in zip(gs,uptake)])
 h=np.array([g.assimilation_mol_g for g in gs]);cat=(uptake-h*np.maximum(growth,0))*x*pc.HOURS_PER_YEAR
 kr,ko=pc.recycling_rates(T,p);gamma=pc.inventory_to_ratio(p);abiotic=pc.atmosphere(p.climate.case)['flux_to_ratio_per_yr']*p.climate.abiotic_flux
 return np.r_[(pc.supply_h2(p)-uptake@x-p.biology.exchange_mol_l_h_pa*(pressure-p.biology.atmosphere_pa))*pc.HOURS_PER_YEAR/pc.HENRY_30C_MOL_L_PA,
 x*(growth-p.biology.loss_h)*pc.HOURS_PER_YEAR,cat[0]/4-(kr+ko)*ac,gamma*(cat[1]/4+kr*ac)+abiotic-p.loss.rate(r)]

def state(T,p,energies,positions,shape,r):
 gs=pair(T,energies,positions,shape);pressure=np.mean([g.rstar(bio.loss_h) for g in gs]);q=np.array([g.maintenance+bio.loss_h/g.yield_g_mol for g in gs]);h=np.array([g.assimilation_mol_g for g in gs]);kr,ko=pc.recycling_rates(T,p)
 cap=pc.supply_h2(p)-bio.exchange_mol_l_h_pa*(pressure-bio.atmosphere_pa);abiotic=pc.atmosphere(p.climate.case)['flux_to_ratio_per_yr']*p.climate.abiotic_flux
 matrix=np.array([q,[(kr/(kr+ko))*(q[0]-h[0]*bio.loss_h),q[1]-h[1]*bio.loss_h]])
 x=np.linalg.solve(matrix,[cap,4*(p.loss.rate(r)-abiotic)/(pc.inventory_to_ratio(p)*pc.HOURS_PER_YEAR)])
 ac=pc.HOURS_PER_YEAR*(q[0]-h[0]*bio.loss_h)*x[0]/4/(kr+ko)
 y=np.r_[pressure,x,ac,r]
 if np.min(x)<=0:return dict(feasible=False,y=y.tolist())
 scale=np.maximum(abs(y),[10.,1e-4,1e-4,1e-5,.01]);eigs=[]
 for step in [1e-4,1e-5,1e-6]:
  jac=np.column_stack([(rhs(y+np.eye(5)[j]*step*scale[j],p,energies,positions,shape)-rhs(y-np.eye(5)[j]*step*scale[j],p,energies,positions,shape))/(2*step)/scale for j in range(5)])
  eigen=np.linalg.eigvals(jac);eigs.append(dict(step=step,max_real_per_yr=float(max(eigen.real)),eigenvalues=[[float(e.real),float(e.imag)] for e in eigen]))
 return dict(feasible=True,y=y.tolist(),scaled_rhs=(rhs(y,p,energies,positions,shape)/scale).tolist(),jacobians=eigs)

results=[]
for energies,bracket in [((0.,0.),(277,279)),((.45,0.),(290,293)),((.65,.1),(283,286))]:
 for shape in ['linear_shape','smooth_shape']:
  def diff(T):return best(T,energies[0],0,shape)[0]-best(T,energies[1],1,shape)[0]
  grid=np.linspace(273.15,303.15,121); vals=[diff(T) for T in grid];roots=[]
  for left,right,fa,fb in zip(grid[:-1],grid[1:],vals[:-1],vals[1:]):
   if fa*fb<0:roots.append(brentq(diff,left,right,xtol=1e-10))
  for T in roots:
   b=[best(T,energies[i],i,shape) for i in (0,1)];u=[a[1] for a in b]
   curve=pc.response(p0.climate.case);ratios=[]
   for r0,r1,t0,t1 in zip(curve.ratios[:-1],curve.ratios[1:],curve.temperatures_k[:-1],curve.temperatures_k[1:]):
    if (t0-T)*(t1-T)<0:ratios.append(brentq(lambda r:float(pc.temperature_k(r,p0.climate))-T,r0,r1,xtol=1e-13))
   communities=[]
   for ratio in ratios:
    if float(pc.temperature_k(ratio+1e-7,p0.climate))-float(pc.temperature_k(ratio-1e-7,p0.climate))>=0:continue
    for f in [0.,.5]:communities.append(dict(f=f,ratio=ratio,**state(T,replace(p0,acetate_fraction=f),energies,u,shape,ratio)))
   results.append(dict(energies=energies,shape=shape,T=T,best_responses=[a[2] for a in b],slope=(diff(T+.001)-diff(T-.001))/.002,cooling_communities=communities))
Path(__file__).with_name('verify_unequal_energy.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
