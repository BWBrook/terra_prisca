from dataclasses import replace
import numpy as np
from terra_prisca.haze_world import population_coupling as pc, two_guilds as tg, hydrogen_uptake as hu
from terra_prisca.haze_world.methane_budget import atmosphere, AVOGADRO
p = pc.reference()
for f in (0., .5):
    q = replace(p, acetate_fraction=f, biology=replace(p.biology, methanogen=hu.MSP))
    print("MSP f=", f, [(e["kind"], round(e["t_k"], 3), e["stability"], e["domain"]) for e in pc.equilibrium_states(q)])
b = p.biology
for tc in (4., 8.385, 15., 30.):
    a, m = tg.guilds(tc, b)
    qa, qm = a.maintenance + b.loss_h / a.yield_g_mol, m.maintenance + b.loss_h / m.yield_g_mol
    print(f"T={tc}C  A: V={a.rate_scale:.3e} K={a.km_pa:.0f} h={a.threshold_pa:.2f} Q/V={qa/a.rate_scale:.3f} mumax={a.yield_g_mol*a.rate_scale:.2e}/h R*={a.rstar(b.loss_h):.2f} | "
          f"M: V={m.rate_scale:.3e} K={m.km_pa:.0f} h={m.threshold_pa:.3f} Q/V={qm/m.rate_scale:.3f} mumax={m.yield_g_mol*m.rate_scale:.2e}/h R*={m.rstar(b.loss_h):.2f}")
print("donor flux CH4-eq molecules/cm2/s at potential 0.3:", p.climate.donor_flux, " H2:", 4 * p.climate.donor_flux,
      " methane loss at r=0.195:", 0.195107 / (p.climate.lifetime_yr * atmosphere('B')['flux_to_ratio_per_yr']))
print("supply mol H2/L/h", pc.supply_h2(p), "habitat L/cm2", p.habitat_l_cm2, "lifeless p0 Pa", pc.supply_h2(p)/b.exchange_mol_l_h_pa)
