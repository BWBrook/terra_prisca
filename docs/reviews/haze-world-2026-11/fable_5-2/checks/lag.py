"""Reviewer check: does the reference mixed state stay stable when surface/habitat
temperature relaxes to T(r) with a finite time constant instead of instantly?"""
from dataclasses import replace
import numpy as np
from terra_prisca.haze_world import population_coupling as pc
from terra_prisca.haze_world.methane_budget import temperature_k

def mixed(p):
    return [e for e in pc.equilibrium_states(p) if e["kind"] == "mixed"]

def rhs6(z, p, tau):
    y, T = z[:5], z[5]
    f = pc.fluxes_at_temperature(y, p, T)
    d = np.r_[
        (f["supply_h2_mol_l_yr"] - sum(f["uptake_h2_mol_l_yr"]) - f["outlet_h2_mol_l_yr"]) / pc.HENRY_30C_MOL_L_PA,
        y[1:3] * f["net_growth_yr"],
        f["acetate_production_mol_l_yr"] - f["acetate_recycling_mol_l_yr"] - f["acetate_export_mol_l_yr"],
        f["methane_source_ratio_yr"] - f["methane_loss_ratio_yr"],
        (float(temperature_k(y[4], p.climate)) - T) / tau]
    return d

def jac6(z, p, tau):
    scales = np.maximum(np.abs(z), [10., 1e-4, 1e-4, 1e-5, .01, 1.])
    J = np.empty((6, 6))
    for j in range(6):
        h = scales[j] * 1e-6
        d = np.eye(6)[j] * h
        J[:, j] = (rhs6(z + d, p, tau) - rhs6(z - d, p, tau)) / (2 * h)
    return J

for f in (0., .5):
    for L in (1e-3,):
        p = replace(pc.reference(), acetate_fraction=f)
        p = replace(p, biology=replace(p.biology, loss_h=L))
        for e in mixed(p):
            lam = e["eigenvalues"]
            osc = lam[np.argmax(np.abs(lam.imag))]
            print(f"f={f} L={L} T={e['t_k']:.4f} r={e['r']:.6f} max_real={e['max_real_yr']:.3e} "
                  f"osc={osc:.5g} period={2*np.pi/abs(osc.imag):.2f} damp={-1/osc.real:.1f}")
            z = np.r_[e["y"], e["t_k"]]
            for tau in (1e-3, .05, .1, .15, .2, .3, .5, 1, 3, 10, 30, 100, 300, 1000, 3000):
                ev = np.linalg.eigvals(jac6(z, p, tau))
                lead = ev[np.argmax(ev.real)]
                print(f"   tau_T={tau:8.3f} yr  leading eig={lead:.4e}  "
                      + (f"period={2*np.pi/abs(lead.imag):.1f} yr e-fold={1/lead.real:.1f} yr" if abs(lead.imag) > 0 else ""))
