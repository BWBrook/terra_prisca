from dataclasses import replace
import numpy as np
from terra_prisca.haze_world import population_coupling as pc
from terra_prisca.haze_world.methane_budget import temperature_k
p = pc.reference()                      # f=0.5 default
ponly = replace(p, enabled=(False, True))
m = [e for e in pc.equilibrium_states(ponly) if e["kind"] == "methanogen" and e["stable"]][0]
y0 = m["y"].copy(); y0[1] = 1e-12
one_cell = 3e-13 / (p.habitat_l_cm2 * 5.1e18)
ts = np.r_[0, np.arange(1, 41)]
s = pc.integrate(y0, p, 40., sample_times=ts)
logM = s.log_biomass[1]; logA = s.log_biomass[0]
for t, la, lm, r in zip(ts, logA, logM, s.y[4]):
    if t in (0, 5, 10, 15, 18, 19, 20, 25, 30, 40):
        print(f"t={t:4.0f} cells_A=1e{(la-np.log(one_cell))/np.log(10):6.2f} cells_M=1e{(lm-np.log(one_cell))/np.log(10):6.2f} T={float(temperature_k(r,p.climate)):.6f}")
cross = np.interp(0, -(logM - np.log(one_cell)), ts)
print("M below one global cell at t ≈", round(float(cross), 3), "yr; start T", m["t_k"])
# pick the acetogen-only state and ask what climate eventually follows without methanogens
aonly = replace(p, enabled=(True, False))
print([(e["kind"], round(e["t_k"],3), e["stable"]) for e in pc.equilibrium_states(aonly)])
