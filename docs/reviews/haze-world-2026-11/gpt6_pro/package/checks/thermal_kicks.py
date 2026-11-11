"""Small nonlinear kicks validating the finite-thermal-response linear result."""
import json
from dataclasses import replace
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from thermal_relaxation import c, six_rhs, jacobian

out=[]
for f,tau in [(0.,.1),(0.,1.),(.5,2.)]:
    p=replace(c.reference(),acetate_fraction=f)
    e=next(x for x in c.equilibrium_states(p) if x['kind']=='mixed' and x['stable'])
    z=np.r_[e['y'],e['t_k']]
    scales=np.r_[np.maximum(abs(z[:5]),[10.,1e-4,1e-4,1e-5,.01]),1.]
    j=jacobian(lambda v:six_rhs(v,p,tau),z,scales,1e-4)
    eig,vec=np.linalg.eig(j)
    k=int(np.argmax(eig.real))
    seed=vec[:,k].real
    seed=seed/np.linalg.norm(seed)*1e-5
    initial=z+scales*seed
    sol=solve_ivp(lambda _,q:six_rhs(q,p,tau),(0.,1000.),initial,
        method='Radau',rtol=1e-10,atol=np.array([1e-10,1e-15,1e-15,1e-15,1e-13,1e-10]),
        t_eval=np.arange(0.,1000.1,1.),max_step=2.)
    if not sol.success:raise RuntimeError(sol.message)
    coeff=np.linalg.solve(vec,(sol.y-z[:,None])/scales[:,None])[k]
    amplitude=np.abs(coeff)
    slope,intercept=np.polyfit(sol.t,np.log(amplitude),1)
    out.append(dict(f=f,tau_temperature_years=tau,method='Radau',
        predicted_growth_rate_year= float(eig[k].real),measured_growth_rate_year=float(slope),
        initial_mode_amplitude=float(amplitude[0]),final_mode_amplitude=float(amplitude[-1]),
        maximum_temperature_departure_k=float(np.max(abs(sol.y[5]-z[5]))),
        max_log_amplitude_residual=float(np.max(abs(np.log(amplitude)-(slope*sol.t+intercept)))),
        solver_success=bool(sol.success),rhs_evaluations=int(sol.nfev)))
    print(out[-1],flush=True)
Path(__file__).with_name('thermal_kicks_results.json').write_text(json.dumps(out,indent=2)+'\n')
