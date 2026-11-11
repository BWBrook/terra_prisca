"""Reviewer check: how conditional is the existence/location of the restoring crossing?"""
from dataclasses import replace
import itertools, json
import numpy as np
from terra_prisca.haze_world import population_coupling as pc, two_guilds as tg
from terra_prisca.haze_world import hydrogen_uptake as hu

ref = pc.reference().biology
LO, HI = 273.39, 297.008   # case-B cooling branch span

def switches(b):
    out = []
    for ts in pc.switch_temperatures(b):
        a0, m0 = [g.rstar(b.loss_h) for g in tg.guilds(ts - 273.15 - .05, b)] if ts-273.15-.05 >= -.15 else (np.nan, np.nan)
        orient = "A-cold" if a0 < m0 else "M-cold"
        out.append((round(ts, 3), orient))
    return out

print("reference", switches(ref))
one_at_a_time = {
 "capacity_ratio=0.38 (dry-mass basis)": dict(capacity_ratio=.38),
 "capacity_ratio=1.5": dict(capacity_ratio=1.5),
 "yield_m=0.4": dict(yield_m=.4), "yield_m=1.7": dict(yield_m=1.7),
 "maintenance_m30=0.3e-3": dict(maintenance_m30=.3e-3), "maintenance_m30=2.3e-3": dict(maintenance_m30=2.3e-3),
 "threshold_a30=5": dict(threshold_a30=5.), "threshold_a30=95": dict(threshold_a30=95.),
 "threshold_shape=constant": dict(threshold_shape="constant"),
 "maintenance_energy=0": dict(maintenance_energy_j=0.),
 "maintenance_energy=35 kJ": dict(maintenance_energy_j=35000.),
 "constant thr + no maint T-dep": dict(threshold_shape="constant", maintenance_energy_j=0.),
 "MSP": dict(methanogen=hu.MSP),
 "first_order acetogen": dict(kinetics="first_order"),
 "arrhenius continuation": dict(low_temperature_variant="arrhenius_continuation"),
 "loss 1e-4": dict(loss_h=1e-4), "loss 3e-4": dict(loss_h=3e-4), "loss 3e-3": dict(loss_h=3e-3), "loss 1e-2": dict(loss_h=1e-2),
}
for k, v in one_at_a_time.items():
    print(f"{k:42s}", switches(replace(ref, **v)))

# full 243 grid on the coupled reference structure
for strain in (hu.MSB, hu.MSP):
    n = dict(total=0, restoring_on_branch=0, any_switch=0, mcold=0, multi=0)
    warmM = dict(total=0, restoring_on_branch=0)
    for c in tg.parameter_grid(strain):
        b = replace(ref, methanogen=strain, capacity_ratio=c.capacity_ratio, yield_m=c.yield_m,
                    maintenance_m30=c.maintenance_m30, loss_h=c.loss_h, threshold_a30=c.threshold_a30)
        s = switches(b)
        n["total"] += 1
        n["any_switch"] += bool(s)
        n["multi"] += len(s) > 1
        n["mcold"] += any(o == "M-cold" for _, o in s)
        good = any(o == "A-cold" and LO < t < HI for t, o in s)
        n["restoring_on_branch"] += good
        wins = [np.argmin([g.rstar(b.loss_h) for g in tg.guilds(t, b)]) == 1 for t in (20., 30.)]
        if all(wins):
            warmM["total"] += 1; warmM["restoring_on_branch"] += good
    print(strain, n, "| M wins 20&30C:", warmM)
