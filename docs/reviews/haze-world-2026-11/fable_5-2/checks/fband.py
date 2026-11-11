from dataclasses import replace
import numpy as np
from scipy.optimize import brentq
from terra_prisca.haze_world import population_coupling as pc
def has_mixed(pot, f):
    p = replace(pc.reference(pot), acetate_fraction=f)
    return any(e["kind"] == "mixed" and e["stable"] for e in pc.equilibrium_states(p))
for f in (0., .5, .9, .95, .98, .99, 1.):
    grid = np.round(np.arange(.20, .80, .0025), 4)
    ok = [x for x in grid if has_mixed(float(x), f)]
    print(f"f={f}: stable mixed for potential in [{min(ok) if ok else None}, {max(ok) if ok else None}]  ratio={max(ok)/min(ok) if ok else None}")
