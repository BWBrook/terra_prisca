import importlib.util,json,sys
from pathlib import Path
import numpy as np
import pytest
from numpy.polynomial import Polynomial
root=Path.cwd()
from terra_prisca.haze_world import habitat_integration as h
from terra_prisca.haze_world import refuge_integration as r
records=[]
for name,module,test,idx in [('habitat',h,'test_exit_is_detected_on_a_nonmonotone_climate_path_and_fixed_refuge_is_constant',-1),('refuge',r,'test_domain_exit_is_found_even_if_temperature_reenters_before_step_endpoint',8)]:
 path=root/'tests'/f'test_{name}_integration.py'
 spec=importlib.util.spec_from_file_location(name+'_test',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 old=module._exit_time
 def wrapped(dense,left,right,interval,*args,old=old,name=name,idx=idx):
  result=old(dense,left,right,interval,*args)
  if result is not None:
   k=(args[0].state_size-1) if args else idx
   ratio=Polynomial(dense.yh[k]);lo=(left-dense.t)/dense.h;hi=(right-dense.t)/dense.h
   records.append({'type':name,'left':left,'right':right,'dense_t_old':dense.t_old,'dense_t':dense.t,'dense_h':dense.h,'interval':interval,'ratio_coefficients':dense.yh[k].tolist(),'lo':lo,'hi':hi,'ratio_at_left':float(ratio(lo)),'ratio_at_right':float(ratio(hi)),'exit_time':result,'ratio_at_exit':float(ratio((result-dense.t)/dense.h)),'physical_r_dense_left':float(dense(left)[k]),'physical_r_dense_right':float(dense(right)[k]),'boundary_roots':[{'boundary':b,'roots':[(float(v.real),float(v.imag)) for v in (ratio-b).roots()]} for b in interval if np.isfinite(b)]})
  return result
 module._exit_time=wrapped
 with pytest.MonkeyPatch.context() as patch:
  try:getattr(m,test)(patch)
  except AssertionError:pass
 module._exit_time=old
print(json.dumps(records,indent=2))
Path(__file__).with_suffix('.json').write_text(json.dumps(records,indent=2))
