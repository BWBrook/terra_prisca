"""Reviewer experiment: N climate-tracking habitats with a spread of local temperatures,
shared methane, weak cell exchange and optional thermal lag. Uses the repository's
local metabolism (population_coupling.fluxes_at_temperature) unchanged."""
from dataclasses import replace
import sys, json, time
import numpy as np
from scipy.integrate import solve_ivp
from terra_prisca.haze_world import population_coupling as pc
from terra_prisca.haze_world.methane_budget import temperature_k

ONE_CELL = lambda p: 3e-13 / (p.habitat_l_cm2 * 5.1e18)

def make(p, offsets, d, tau):
    n = len(offsets); w = np.full(n, 1 / n)
    conv = pc.inventory_to_ratio(p)
    def rhs(t, z):
        r = z[4 * n] if np.isfinite(z[4 * n]) else 0.; T = z[4 * n + 1] if tau else float(temperature_k(max(r, 0.), p.climate))
        out = np.zeros_like(z); L = np.clip(z[:4 * n].reshape(n, 4)[:, 1:3], -1e5, 0.); X = np.exp(L); top = L.max(0); logmean = top + np.log(w @ np.exp(L - top))
        methane = 0.
        for j in range(n):
            a = 4 * j
            y = np.r_[max(z[a], 0.), X[j], max(z[a + 3], 0.), max(r, 0.)]
            fl = pc.fluxes_at_temperature(y, p, float(np.clip(T + offsets[j], 273.0001, 303.1499)))
            out[a] = (fl["supply_h2_mol_l_yr"] - sum(fl["uptake_h2_mol_l_yr"]) - fl["outlet_h2_mol_l_yr"]) / pc.HENRY_30C_MOL_L_PA
            out[a + 1:a + 3] = fl["net_growth_yr"] + d * np.expm1(np.minimum(logmean - L[j], 600.))
            out[a + 3] = fl["acetate_production_mol_l_yr"] - fl["acetate_recycling_mol_l_yr"] - fl["acetate_export_mol_l_yr"]
            methane += w[j] * fl["methane_local_mol_l_yr"]
            ab, loss = fl["abiotic_ratio_yr"], fl["methane_loss_ratio_yr"]
        out[4 * n] = conv * methane + ab - loss
        if tau: out[4 * n + 1] = (float(temperature_k(max(r, 0.), p.climate)) - T) / tau
        return out
    return rhs

def pack(y5, n, tau, p, xa=None, xm=None):
    loc = np.r_[y5[0], np.log(xa if xa else y5[1]), np.log(xm if xm else y5[2]), y5[3]]
    z = np.r_[np.tile(loc, n), y5[4]]
    return np.r_[z, float(temperature_k(y5[4], p.climate))] if tau else z

def summarize(s, p, n, tau, tail):
    one = np.log(ONE_CELL(p)); w = 1 / n
    logs = s.y[:4 * n].reshape(n, 4, -1)
    A = np.log(np.exp(logs[:, 1] - logs[:, 1].max(0)).sum(0) * w) + logs[:, 1].max(0)
    M = np.log(np.exp(logs[:, 2] - logs[:, 2].max(0)).sum(0) * w) + logs[:, 2].max(0)
    T = np.array([float(temperature_k(max(r, 0), p.climate)) for r in s.y[4 * n]])
    k = s.t >= s.t[-1] - tail
    return dict(T_end=round(T[-1], 4), T_tail_min=round(T[k].min(), 4), T_tail_max=round(T[k].max(), 4),
                T_all_min=round(T.min(), 3), T_all_max=round(T.max(), 3),
                log10_cells_A_min=round((A.min() - one) / np.log(10), 2), log10_cells_M_min=round((M.min() - one) / np.log(10), 2),
                log10_cells_A_end=round((A[-1] - one) / np.log(10), 2), log10_cells_M_end=round((M[-1] - one) / np.log(10), 2))

def run(label, p, offsets, d, tau, z0, years, tail=2000.):
    t0 = time.time(); n = len(offsets)
    s = solve_ivp(make(p, offsets, d, tau), (0, years), z0, method="LSODA", rtol=1e-7, atol=1e-9, first_step=1e-6,
                  t_eval=np.linspace(0, years, int(years / 5) + 1))
    out = dict(label=label, ok=bool(s.success), years=years, **summarize(s, p, n, tau, tail), wall_s=round(time.time() - t0))
    print(json.dumps(out), flush=True)
    return s

if __name__ == "__main__":
    which = sys.argv[1]
    N, D = 9, 1e-3
    if which == "supply":      # (a) does the set point stay pinned across supply?
        for spread in (0., 3., 6.):
            offs = np.linspace(-spread, spread, N)
            for f in (0.5,):
                for pot in (.24, .30, .36, .44):
                    p = replace(pc.reference(pot), acetate_fraction=f)
                    e = [e for e in pc.equilibrium_states(p) if e["kind"] == "mixed" and e["stable"]][0]
                    run(f"supply spread=±{spread} f={f} pot={pot}", p, offs, D, 0., pack(e["y"], N, 0., p), 30000.)
    if which == "lag":         # (b) is the heterogeneous thermostat stable with thermal inertia?
        p = replace(pc.reference(), acetate_fraction=0.)
        e = [e for e in pc.equilibrium_states(p) if e["kind"] == "mixed" and e["stable"]][0]
        for spread, tau in ((0., 3.), (3., 3.), (6., 3.), (6., 30.), (6., 300.)):
            offs = np.linspace(-spread, spread, N)
            z0 = pack(e["y"], N, tau, p); z0[1] += 1e-3
            run(f"lag f=0 spread=±{spread} tau_T={tau}", p, offs, D, tau, z0, 12000., tail=3000.)
    if which == "invade":      # (c) does an invasion still exterminate the resident?
        p = pc.reference()     # f=0.5, the C07 focal case
        for spread in (0., 3., 6.):
            offs = np.linspace(-spread, spread, N)
            for res, idx in (("M", 2), ("A", 1)):
                en = (False, True) if res == "M" else (True, False)
                e = [e for e in pc.equilibrium_states(replace(p, enabled=en)) if e["stable"] and e["kind"] != "lifeless"][0]
                y = e["y"].copy()
                z0 = pack(y, N, 0., p, xa=1e-12 if res == "M" else None, xm=1e-12 if res == "A" else None)
                run(f"invade resident={res} spread=±{spread} (start T={e['t_k']:.2f})", p, offs, D, 0., z0, 30000.)
