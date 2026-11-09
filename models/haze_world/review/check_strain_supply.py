"""Final-supply equilibrium feasibility for the H scenario reviewed at85041a0.

Run from repository root with uv run python <this file> OUTPUT_DIRECTORY.
No population time integrations; numerical equilibrium threshold only.
"""
from pathlib import Path
import sys
from dataclasses import replace
import json
import numpy as np
from scipy.optimize import brentq, minimize_scalar
from terra_prisca.haze_world.darwinian import Constraint, reference, strain, singular_theta, fixed_equilibria, evolved
from terra_prisca.haze_world.experiments import flux_for_potential
from terra_prisca.haze_world.methane_budget import atmosphere, temperature_k, capture_efficiency, growth_ratio

outdir=Path(sys.argv[1])
outdir.mkdir(parents=True,exist_ok=True)
p, losses=reference(); loss=losses[2]; con=Constraint(energy_ev=.65)
p=replace(p,donor_flux=float(flux_for_potential(.02,p)))
conversion=atmosphere(p.case)['flux_to_ratio_per_yr']
r_abiotic=loss.inverse(conversion*p.abiotic_flux)
r_max=loss.inverse(conversion*(p.donor_flux+p.abiotic_flux))
maintenance_potential=p.lifetime_yr*conversion*p.maintenance_flux
rows=[]
for theta in (285.5,286.,286.5,287.,287.5):
    q=strain(p,theta,con)
    def flow(r):
        return conversion*(q.donor_flux*capture_efficiency(temperature_k(r,q),q)+q.abiotic_flux)-loss.rate(r)
    xs=np.linspace(0,r_max*1.01,100001); f=flow(xs); roots=[]
    for i in np.flatnonzero(f[:-1]*f[1:]<0):
        r=brentq(flow,xs[i],xs[i+1],xtol=1e-15)
        h=1e-7; derivative=(flow(r+h)-flow(r-h))/(2*h)
        roots.append(dict(r=r,t_k=float(temperature_k(r,q)),eta=float(capture_efficiency(temperature_k(r,q),q)),flow_derivative=float(derivative),stable=bool(derivative<0)))
    rows.append(dict(theta=theta,rho_peak=float(q.growth_ratio_max),production_roots=fixed_equilibria(q,loss),independent_roots=roots))
minima=[]
for theta in (285.5,286.,286.5,287.,287.5,None):
    def required(r):
        t=float(temperature_k(r,p)); th=singular_theta(t,con) if theta is None else theta
        q=strain(p,th,con); rho=float(growth_ratio(t,q))
        return r-r_abiotic+maintenance_potential/(rho-1) if rho>1 else np.inf
    xs=np.linspace(r_abiotic,.05,10001); values=np.array([required(r) for r in xs]); i=int(values.argmin())
    fit=minimize_scalar(required,bounds=(xs[max(0,i-2)],xs[min(len(xs)-1,i+2)]),method='bounded',options={'xatol':1e-15})
    r=float(fit.x);t=float(temperature_k(r,p));th=singular_theta(t,con) if theta is None else theta
    minima.append(dict(theta=theta,critical_potential=float(fit.fun),ratio_at_fold=r,temperature_at_fold=t,
                       singular_theta_at_fold=th,current_potential=.02,
                       max_quasi_steady_balance_per_yr=(.02-float(fit.fun))/p.lifetime_yr))
report=dict(reviewed_commit='85041a0',final_potential=.02,loss=loss.label,t_zero=p.t_zero_k,
            donor_flux=p.donor_flux,maximum_ratio=r_max,rows=rows,evolutionary_endpoint=evolved(p,con,loss),
            critical_supply_minima=minima,
            scope='No positive equilibrium under assumed265K bridge; does not alone rule out nonstationary full-system attractors or prove global extinction.')
(outdir/'final_supply_equilibria.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
