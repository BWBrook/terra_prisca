"""Nonlinear fate of the lag-destabilised mixed state (log-biomass coordinates)."""
from dataclasses import replace
import sys, json
import numpy as np
from scipy.integrate import solve_ivp
from terra_prisca.haze_world import population_coupling as pc
from terra_prisca.haze_world.methane_budget import temperature_k

CELL_G = None
def run(f, tau, years, kick=1e-3):
    p = replace(pc.reference(), acetate_fraction=f)
    e = [e for e in pc.equilibrium_states(p) if e["kind"] == "mixed"][0]
    y0 = e["y"].copy()
    z0 = np.r_[y0[0], np.log(y0[1] * (1 + kick)), np.log(y0[2]), y0[3], y0[4], e["t_k"]]
    def rhs(t, z):
        y = np.r_[z[0], np.exp(z[1]), np.exp(z[2]), z[3], z[4]]
        T = min(max(z[5], 273.0001), 303.1499)
        fl = pc.fluxes_at_temperature(y, p, T)
        return np.r_[
            (fl["supply_h2_mol_l_yr"] - sum(fl["uptake_h2_mol_l_yr"]) - fl["outlet_h2_mol_l_yr"]) / pc.HENRY_30C_MOL_L_PA,
            fl["net_growth_yr"],
            fl["acetate_production_mol_l_yr"] - fl["acetate_recycling_mol_l_yr"] - fl["acetate_export_mol_l_yr"],
            fl["methane_source_ratio_yr"] - fl["methane_loss_ratio_yr"],
            (float(temperature_k(max(z[4], 0), p.climate)) - z[5]) / tau]
    ts = np.linspace(0, years, int(years) + 1)
    s = solve_ivp(rhs, (0, years), z0, method="LSODA", rtol=1e-8, atol=1e-10, t_eval=ts)
    T = s.y[5]; la, lm = s.y[1] / np.log(10), s.y[2] / np.log(10)
    n = len(ts)
    out = dict(f=f, tau=tau, ok=bool(s.success), t_end=float(s.t[-1]), T_eq=e["t_k"],
               log10XA_eq=float(np.log10(y0[1])), log10XM_eq=float(np.log10(y0[2])))
    for name, sl in (("first_third", slice(0, n // 3)), ("last_third", slice(2 * n // 3, n))):
        out[name] = dict(T_min=float(T[sl].min()), T_max=float(T[sl].max()),
                         log10XA_min=float(la[sl].min()), log10XM_min=float(lm[sl].min()),
                         Tsurf_eq_min=float(min(temperature_k(max(r,0), p.climate) for r in s.y[4][sl])),
                         Tsurf_eq_max=float(max(temperature_k(max(r,0), p.climate) for r in s.y[4][sl])))
    return out, s

if __name__ == "__main__":
    for f, tau, years in ((0., 3., 12000), (0., 30., 6000), (.5, 10., 8000), (0., 300., 8000)):
        try:
            out, s = run(f, tau, years)
            print(json.dumps(out))
        except Exception as ex:
            print("FAIL", f, tau, repr(ex)[:300])
