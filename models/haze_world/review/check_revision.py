"""Read-only28295c0 review. Run without args for static audit; add --runs for3 full-state survivor checks."""
import csv,json,sys,time
from pathlib import Path
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.integrate import solve_ivp
from terra_prisca.haze_world.darwinian import Constraint, reference, singular_theta, peak_growth, local_regulation, evolved, strain, climate_slopes
from terra_prisca.haze_world.methane_budget import atmosphere,temperature_k,response
from terra_prisca.haze_world.experiments import flux_for_potential
from terra_prisca.haze_world.strains import Run,StrainModel,supply_schedule,viability_threshold
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=True)
def static():
 p,laws=reference();law=laws[2];c=atmosphere(p.case)['flux_to_ratio_per_yr'];ra=law.lifetime_yr*c*p.abiotic_flux;pk=law.lifetime_yr*c*p.maintenance_flux
 thresholds=[]
 for t0 in (265.,283.):
  q=replace(p,t_zero_k=t0)
  for E in (0.,.65):
   con=Constraint(energy_ev=E)
   for theta in (None,273.5 if E==0 else 285.5):
    def required(r):
     T=temperature_k(r,q);th=singular_theta(T,con) if theta is None else theta
     rho=float(peak_growth(th,con))*max(0,1-((T-th)/20)**2)
     return r-ra+pk/(rho-1) if rho>1 else np.inf
    xs=ra+np.geomspace(1e-10,.5,10001);vals=np.array([required(x) for x in xs]);i=vals.argmin()
    fit=minimize_scalar(required,bounds=(xs[max(0,i-2)],xs[min(len(xs)-1,i+2)]),method='bounded',options={'xatol':1e-15})
    production=viability_threshold(q,con,law,theta)
    thresholds.append(dict(T0=t0,E=E,theta=theta,independent=float(fit.fun),production=production['potential'],error=production['potential']-float(fit.fun),r_at_min=float(fit.x)))
 print('thresholds',json.dumps(thresholds))
 # Explicit climate-vertex equilibrium formerly misclassified when rho_T=0.
 resp=response(p.case);r=float(resp.ratios[5]);t=float(resp.temperatures_k[5]);phi=float(law.rate(r))/c-p.abiotic_flux+p.maintenance_flux/9
 reg=local_regulation(replace(p,donor_flux=phi,t_opt_k=t),law,{'r':r,'t_k':t})
 print('repaired_vertex_flag',reg['at_vertex'],'two_derivatives',reg['left']['dT_dlnS'],reg['right']['dT_dlnS'])
 con=Constraint(floor_k=289.);e=evolved(p,con,laws[0]);q=strain(p,e['theta_k'],con)
 false_vertex={'r':e['r'],'slopes':climate_slopes(e['r'],q),'distance_to_vertex':float(min(abs(resp.ratios-e['r']))),'flag':bool(local_regulation(q,laws[0],e)['at_vertex'])}
 print('smooth_false_vertex',false_vertex)
 rows=list(csv.DictReader(open('models/haze_world/figures/strains_rescue.csv')))
 keys=('constraint','t_zero_k','final_potential','census_yr');frozen={tuple(r[k] for k in keys):r for r in rows if float(r['mutation'])==0}
 harm=[r for r in rows if frozen[tuple(r[k] for k in keys)]['survived']=='True' and r['survived']!='True']
 viable_h=[r for r in rows if r['constraint']=='H E=0.65' and r['best_viable']=='True']
 summary={'rows':len(rows),'unique':len({tuple(r[k] for k in keys+('mutation',)) for r in rows}),'viable_H':len(viable_h),'viable_H_survive':sum(r['survived']=='True' for r in viable_h),'viable_H_settled':sum(r['settled_last_20kyr']=='True' for r in viable_h),'mutation_harms_matched_frozen_survivor':len(harm),'thresholds':thresholds,'vertex_fixed':bool(reg['at_vertex']),'smooth_false_vertex':false_vertex}
 print('static',json.dumps(summary));(OUT/'static.json').write_text(json.dumps(summary,indent=2)+'\n')

def job(case):
 label,t0,P,m,dt=case;start=time.monotonic();p,laws=reference();con=Constraint(energy_ev=.65 if label=='H' else 0);run=Run(con,laws[2],mutation=m,b_min_rel=1e-6,t_zero_k=t0,check_yr=dt);model=StrainModel(p,run)
 phi0=float(flux_for_potential(.22,p));phi1=float(flux_for_potential(P,p));y0,_=model.resident_state(phi0);bs=float(y0[2:].sum());bmin=run.b_min_rel*bs;schedule=supply_schedule(phi0,phi1,2000,1000);constant=lambda t:phi1
 first=model.integrate(y0,schedule,183000,bmin,record_every_yr=1000)
 tail=model.integrate(first['y'],constant,20000,bmin,record_every_yr=500)
 y=tail['y'];total=float(y[2:].sum());summary=model.snapshot(203000,y,constant)
 one=solve_ivp(model.rhs,(0,dt),y,method='LSODA',rtol=1e-7,atol=np.r_[1e-12,1e-12,np.full(model.theta.size,1e-3*bmin)],args=(constant,))
 pre=np.maximum(one.y[:,-1],0);post=pre.copy();post[2:][post[2:]<bmin]=0
 later=model.integrate(y,constant,20000,bmin,record_every_yr=500)
 def composition(a):
  b=a[2:];return b/b.sum()
 series=[model.snapshot(183000,first['y'],constant)]+tail['series']
 spans={k:float(max(s[k] for s in series)-min(s[k] for s in series)) for k in ('total_biomass','r','t_k','mean_theta_k')}
 rows=list(csv.DictReader(open('models/haze_world/figures/strains_rescue.csv')))
 row=next(x for x in rows if x['constraint']==con.label and float(x['t_zero_k'])==t0 and float(x['final_potential'])==P and float(x['mutation'])==m and float(x['census_yr'])==dt)
 result={'case':case,'elapsed_seconds':time.monotonic()-start,'tail_spans':spans,'biomass_tail_relative':spans['total_biomass']/total,'composition_tail_L1':float(abs(composition(first['y'])-composition(y)).sum()),'final':summary,'final_csv_delta_T':summary['t_k']-float(row['final_t_k']),'final_csv_delta_theta':summary['mean_theta_k']-float(row['final_mean_theta_k']),'census_cycle':{'biomass_rel_change':float((post[2:].sum()-total)/total),'composition_L1':float(abs(composition(post)-composition(y)).sum()),'methane_rel_change':float((post[1]-y[1])/y[1]),'D_rel_change':float((post[0]-y[0])/y[0]),'T_change':float(temperature_k(post[1],model.p)-summary['t_k']),'removed_biomass_relative':float((pre[2:].sum()-post[2:].sum())/total)},'extension_20k':{'T_change':float(temperature_k(later['y'][1],model.p)-summary['t_k']),'theta_change':float(model.snapshot(223000,later['y'],constant)['mean_theta_k']-summary['mean_theta_k']),'composition_L1':float(abs(composition(later['y'])-composition(y)).sum()),'biomass_rel_change':float((later['y'][2:].sum()-total)/total)},'positive_final_bins':[(float(th),float(b/total)) for th,b in zip(model.theta,y[2:]) if b>0]}
 name=f'{label}-T{t0:g}-P{P:g}-m{m:g}-dt{dt:g}'
 np.savez(OUT/(name+'.npz'),theta=model.theta,y183=first['y'],y203=y,ycycle=post,y223=later['y'],bmin=bmin)
 (OUT/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n');return result

def archived_series():
 rows=list(csv.DictReader(open('models/haze_world/figures/strains_series.csv')))
 keys=('constraint','t_zero_k','final_potential','census_yr','mutation')
 groups={}
 for row in rows: groups.setdefault(tuple(row[k] for k in keys),[]).append(row)
 result=[]
 for key,group in groups.items():
  end=max(float(r['t_yr']) for r in group)
  tail=[r for r in group if float(r['t_yr'])>=end-20000]
  entry={'key':key,'n':len(group),'end':end}
  for field in ('total_biomass','r','t_k','mean_theta_k','living_bins'):
   vals=[float(r[field]) for r in tail if r[field] and np.isfinite(float(r[field]))]
   entry[field+'_range']=max(vals)-min(vals) if vals else None
   entry[field+'_final']=vals[-1] if vals else None
  result.append(entry)
 (OUT/'available_series_audit.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':
 static()
 archived_series()
 if '--runs' in sys.argv:
  cases=[('H',265.,.03,1e-8,100.),('H',283.,.02,1e-6,30.),('U',265.,.02,1e-8,30.)]
  with ProcessPoolExecutor(max_workers=3) as pool:
   for r in pool.map(job,cases):print('survivor',json.dumps(r),flush=True)
