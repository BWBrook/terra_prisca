from pathlib import Path
import importlib.util,json
import numpy as np
import pytest
from terra_prisca.haze_world import habitat_integration as h, refuge_integration as r
root=Path.cwd();rows=[]
def trimmed(poly,lo,hi):
 # Diagnostic control ONLY. Production needs interval-aware scaling and residual checks.
 q=poly.trim(tol=1e-14*np.max(abs(poly.coef)))
 return [float(z.real) for z in q.roots() if abs(z.imag)<1e-8 and lo<=z.real<=hi]
for name,module,test in [('habitat',h,'test_exit_is_detected_on_a_nonmonotone_climate_path_and_fixed_refuge_is_constant'),('refuge',r,'test_domain_exit_is_found_even_if_temperature_reenters_before_step_endpoint')]:
 spec=importlib.util.spec_from_file_location(name+'_test',root/'tests'/f'test_{name}_integration.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 with pytest.MonkeyPatch.context() as patch:
  patch.setattr(module,'_real_roots',trimmed)
  try:getattr(m,test)(patch);result='passes'
  except Exception as e:result=repr(e)
 rows.append({'selector':f'tests/test_{name}_integration.py::{test}','temporary_root_control':result})
print(json.dumps(rows,indent=2));Path(__file__).with_suffix('.json').write_text(json.dumps(rows,indent=2))
