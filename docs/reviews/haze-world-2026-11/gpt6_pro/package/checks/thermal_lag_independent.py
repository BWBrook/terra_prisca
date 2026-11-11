from pathlib import Path
import json,sys
import numpy as np
from dataclasses import replace
from scipy.optimize import brentq
sys.path.insert(0, str(Path.cwd() / 'src'))
from terra_prisca.haze_world import population_coupling as model

def derivative(logstocks,T,p):
    stocks=np.exp(logstocks)
    f=model.fluxes_at_temperature(stocks,p,T)
    # Independently assemble physical stock flows and then transform to log coordinates.
    flow=np.zeros(5)
    flow[0]=(f['supply_h2_mol_l_yr']-sum(f['uptake_h2_mol_l_yr'])-f['outlet_h2_mol_l_yr'])/model.HENRY_30C_MOL_L_PA
    flow[1:3]=stocks[1:3]*f['net_growth_yr']
    flow[3]=f['acetate_production_mol_l_yr']-f['acetate_recycling_mol_l_yr']-f['acetate_export_mol_l_yr']
    flow[4]=f['methane_source_ratio_yr']-f['methane_loss_ratio_yr']
    return flow/stocks

rows=[]
for fraction in (0.,.5):
 p=replace(model.reference(),acetate_fraction=fraction)
 e=next(e for e in model.equilibrium_states(p) if e['kind']=='mixed' and e['stable'])
 logs=np.log(e['y']);T=e['t_k']
 for delta in [1e-3,1e-4,1e-5]:
  J0=np.column_stack([(derivative(logs+np.eye(5)[j]*delta,T,p)-derivative(logs-np.eye(5)[j]*delta,T,p))/(2*delta) for j in range(5)])
  BT=(derivative(logs,T+delta,p)-derivative(logs,T-delta,p))/(2*delta)
  slope=(model.temperature_k(np.exp(logs[4]+delta),p.climate)-model.temperature_k(np.exp(logs[4]-delta),p.climate))/(2*delta)
  static=J0.copy();static[:,4]+=BT*slope
  ev=np.linalg.eigvals(static);lead=ev[np.argmax(ev.real)]
  gamma=-float(lead.real);omega=float(abs(lead.imag))
  a=2*gamma;K=gamma**2+omega**2
  def evs(tau):
   J=np.zeros((6,6));J[:5,:5]=J0;J[:5,5]=BT;J[5,4]=slope/tau;J[5,5]=-1/tau
   return np.linalg.eigvals(J)
  critical=brentq(lambda tau:max(evs(tau).real),.001,10.,xtol=1e-10)
  rows.append({'f':fraction,'log_step':delta,'T':T,'static_leading_real':float(lead.real),'static_leading_imag':float(lead.imag),'critical_thermal_tau_years':critical,'two_pole_control_approximation':a/(K-a*a),'at_tau_1':[{'real':float(v.real),'imag':float(v.imag)} for v in sorted(evs(1.),key=lambda v:v.real,reverse=True)]})
Path(__file__).with_suffix('.json').write_text(json.dumps(rows,indent=2))
for r in rows:print(r['f'],r['log_step'],r['critical_thermal_tau_years'],r['two_pole_control_approximation'],r['at_tau_1'][0])
