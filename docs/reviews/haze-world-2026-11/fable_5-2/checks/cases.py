from dataclasses import replace
import numpy as np
from terra_prisca.haze_world import population_coupling as pc
from terra_prisca.haze_world.methane_budget import atmosphere
for case in "ABCD":
    for pot in (.2,.3,.45,.6):
        p0 = pc.reference(pot)
        try:
            clim = replace(p0.climate, case=case)
            # keep the same physical H2 flux and habitat volume as reference case B
            p = replace(p0, climate=clim)
            eqs = pc.equilibrium_states(p)
            print(case, pot, [(e["kind"], round(e["t_k"],3), round(e["r"],4), e["stability"], e["domain"]) for e in eqs])
        except Exception as ex:
            print(case, pot, "ERR", repr(ex)[:200])
