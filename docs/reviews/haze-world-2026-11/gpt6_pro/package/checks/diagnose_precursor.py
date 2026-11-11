from pathlib import Path
import importlib.util,json,warnings
import numpy as np
from scipy.integrate import solve_ivp as scipy_solve
from terra_prisca.haze_world import methane_budget as model
root=Path.cwd()
spec=importlib.util.spec_from_file_location('test_budget',root/'tests/test_methane_budget.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
p=t.HIGH
expected=[e for e in model.equilibria(p) if e['stable'] and e['eta']>0][-1]
c=model.atmosphere('B')['flux_to_ratio_per_yr'];initial=np.array([c*p.donor_flux/.1,1e-6,model.response('B').ratios[-1]])
rows=[]
for method,step in [('LSODA',None),('LSODA',1000.),('LSODA',100.),('Radau',None)]:
 record={}
 def capture(*args,**kwargs):
  kwargs['method']=method
  if step is not None:kwargs['max_step']=step
  sol=scipy_solve(*args,**kwargs)
  bad=np.flatnonzero(np.any(~np.isfinite(sol.y),axis=0))
  record.update(success=sol.success,status=sol.status,message=sol.message,nfev=sol.nfev,accepted_points=len(sol.t),first_nonfinite_accepted_time=None if not len(bad) else float(sol.t[bad[0]]),final_internal=[None if not np.isfinite(v) else float(v) for v in sol.y[:,-1]])
  return sol
 model.solve_ivp=capture
 with warnings.catch_warnings(record=True) as warn:
  warnings.simplefilter('always')
  try:
   result=model.integrate_full(initial,p,3e5)
   record['returned']=[None if not np.isfinite(v) else float(v) for v in result]
  except Exception as e:record['error']=str(e)
  record['warnings']=sorted(set(str(w.message) for w in warn))
 record.update(method=method,max_step=step)
 rows.append(record)
model.solve_ivp=scipy_solve
report={'scope':'Only the original single-guild three-stock integrate_full routine; no claim about the later population/refuge/dormancy integrators.','expected_reduced_warm_ratio':float(expected['r']),'results':rows}
Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
