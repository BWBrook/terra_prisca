"""Preview: does selection on methanogen growth keep the cold-edge equilibrium?

Monomorphic adaptive dynamics on the thermal optimum T_opt, case B, fixed
thermal half-width. A rare mutant invades a resident at equilibrium (D*, T*)
when rho_m(T*) > rho_r(T*) (it draws the donor below the resident's D*), so the
selection gradient is d ln rho(T*; T_opt)/d T_opt. Optional hotter-is-better
trade-off: rho_max = 10 exp[(E/k)(1/300 K - 1/T_opt)]. Scratch-grade stepping,
not the planned variant.

    uv run python models/haze_world/review/evolution_preview.py OUT.json
"""

import json
import sys
from dataclasses import replace

import numpy as np

from terra_prisca.haze_world.experiments import flux_for_potential, t_opt_for_edge
from terra_prisca.haze_world.methane_budget import Params, equilibria

KB_EV = 8.617333e-5


def rho_max(t_opt, e_ev):
    return 10.0 * np.exp(e_ev / KB_EV * (1 / 300.0 - 1 / t_opt))


def log_rho(t, t_opt, e_ev, w=20.0):
    return np.log(rho_max(t_opt, e_ev) * max(1e-300, 1 - ((t - t_opt) / w) ** 2))


def run(r_pot, e_ev, start_edge=281.0):
    p0 = replace(Params(), donor_flux=float(flux_for_potential(r_pot, Params())))
    passive = [e for e in equilibria(replace(p0, thermal=False)) if e["stable"]][-1]
    t_opt, path = t_opt_for_edge(start_edge, p0), []
    for _ in range(400):
        q = replace(p0, t_opt_k=t_opt, growth_ratio_max=float(rho_max(t_opt, e_ev)))
        e = [x for x in equilibria(q, n_grid=3001) if x["stable"] and x["eta"] > 0][-1]
        g = (log_rho(e["t_k"], t_opt + 1e-3, e_ev) - log_rho(e["t_k"], t_opt - 1e-3, e_ev)) / 2e-3
        path.append({"t_opt_k": t_opt, "t_k": e["t_k"], "r": e["r"], "eta": e["eta"], "domain": e["domain"]})
        if abs(g) < 1e-5:
            break
        t_opt += float(np.clip(10 * g, -0.5, 0.5))
    return {"potential_ratio": r_pot, "activation_energy_ev": e_ev, "start": path[0], "end": path[-1],
            "steps": len(path), "domains_visited": sorted({s["domain"] for s in path}),
            "passive_t_k": passive["t_k"], "passive_domain": passive["domain"]}


if __name__ == "__main__":
    rows = [run(r, e) for r in (0.22, 0.30) for e in (0.0, 0.32, 0.65)]
    for x in rows:
        print(f"r_pot {x['potential_ratio']:.2f} E {x['activation_energy_ev']:.2f} eV: "
              f"T* {x['start']['t_k']:.2f} -> {x['end']['t_k']:.2f} K, T_opt {x['start']['t_opt_k']:.2f} -> "
              f"{x['end']['t_opt_k']:.2f} K, eta {x['end']['eta']:.4f}, passive {x['passive_t_k']:.2f} K, "
              f"domains {x['domains_visited']}")
    with open(sys.argv[1], "w") as fh:
        json.dump(rows, fh, indent=1)
