from pathlib import Path
import json,sys
import numpy as np
from scipy.special import logsumexp
from scipy.integrate import solve_ivp
repo=Path.cwd()
sys.path.insert(0,str(repo/'src'))
from terra_prisca.haze_world import branching as b
x=np.load(repo/'models/haze_world/figures/bottleneck/main_0010_environment.npz')
t,bi,de,mi,lc=(x[k] for k in ('times','birth','death','migration','log_counts'))
minimum=float(np.exp(logsumexp(lc,axis=1).min()))
rows=[]
for extra in [0.,.8766,8.766,87.66]:
 lu=b.backward_survival(t,bi+extra,de+extra,mi,rtol=1e-10,atol=1e-12,max_step=.25)
 ll=float(logsumexp(lc[0]+lu))
 s=float(np.exp(np.log(np.log(2))-ll))
 rows.append(dict(extra_balanced_birth_death_yr=extra,log_lambda=ll,P=float(-np.expm1(-np.exp(ll))),half_survival_count_scale=s,N_min_at_half_survival=s*minimum,max_deterministic_growth_difference=float(np.max(abs((bi+extra)-(de+extra)-(bi-de))))))
# Independent ordinary-probability backward ODE in chosen recorded environment.
# d u_j /dt = b_j*u_j^2 -(b_j-d_j)*u_j +sum q_jk*(u_j-u_k)
def rhs(time,u):
 birth=np.array([np.interp(time,t,bi[:,j]) for j in range(bi.shape[1])])
 death=np.array([np.interp(time,t,de[:,j]) for j in range(de.shape[1])])
 return birth*u*u-(birth-death)*u+(mi.sum(axis=1)*u-mi@u)
sol=solve_ivp(rhs,(t[-1],t[0]),np.ones(bi.shape[1]),method='DOP853',rtol=1e-11,atol=1e-24,max_step=.1)
independent_logu=np.log(sol.y[:,-1])
base=b.backward_survival(t,bi,de,mi,rtol=1e-11,atol=1e-12,max_step=.1)
# Isolated homogeneous bank ratio calculation and the purely demographic coefficient.
ratios=[1e2,1e4,1e6,1e8,1e12,np.exp(54.3492)]
report={'scope':'Recorded external environment; balanced birth/death addition preserves mean dynamics exactly but changes demographic variance. It is a structural sensitivity, not an asserted alternative Archean rate calibration.', 'first_window_years':[float(t[0]),float(t[-1])], 'reference_minimum_cells':minimum,'sensitivity':rows,'independent_probability_ODE':{'success':sol.success,'evaluations':sol.nfev,'logu':independent_logu.tolist(),'logu_reference':base.tolist(),'max_abs_log_difference':float(max(abs(independent_logu-base)))},'bank_half_life_fraction':[{'entry_to_required_survivor_ratio':float(r),'fraction':float(np.log(2)/np.log(r))} for r in ratios]}
Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
