"""Preview for the competitive-evolution spec: which temperature dependences create the
acetogen/methanogen switch in the coupled reference physiology (population_coupling.reference).

R*(T) = h(T) + K(T) q/(V(T) - q), q = m(T) + L/Y. Components are frozen one at a time:
- kinetics: V and K (measured strain shapes) held at a fixed temperature;
- thresholds: fixed-energy cessation pressures h held at their 30 C values;
- maintenance: shared Arrhenius factor (never frozen; common to both guilds).
Run: uv run python models/haze_world/review/competitive_evolution_preview.py
"""
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world.two_guilds import guilds, maintenance_factor

OUT = Path(__file__).with_suffix(".json")
TS = np.round(np.arange(-0.15, 30.01, 0.25), 2)


def rstars(t, cfg, kinetic_t=None, loss=None, threshold_t=None):
    loss = cfg.loss_h if loss is None else loss
    kin = guilds(t if kinetic_t is None else kinetic_t, cfg)
    thr = guilds(t if threshold_t is None else threshold_t, cfg)
    loc = guilds(t, cfg)
    return [replace(gk, maintenance=gl.maintenance, threshold_pa=gt.threshold_pa).rstar(loss)
            for gk, gt, gl in zip(kin, thr, loc)]


def scan(cfg, kinetic_t=None, loss=None, threshold_t=None):
    f = lambda t: np.subtract(*rstars(t, cfg, kinetic_t, loss, threshold_t))
    d = np.array([f(t) for t in TS])  # A - M
    crossings = []
    for i in range(len(TS) - 1):
        if np.isfinite(d[i]) and np.isfinite(d[i + 1]) and d[i] * d[i + 1] < 0:
            tc = brentq(f, TS[i], TS[i + 1])
            # orientation: who wins (lower R*) just below the crossing
            below = "acetogen" if f(tc - 0.25) < 0 else "methanogen"
            crossings.append({"t_c": round(tc, 3), "t_k": round(tc + 273.15, 3), "cold_winner": below})
    winner = ["acetogen" if x < 0 else "methanogen" for x in d]
    return {"crossings": crossings, "cold_end_winner": winner[0], "warm_end_winner": winner[-1],
            "rstar_diff_a_minus_m_pa": {str(k): float(f(k)) for k in (0., 8., 15., 30.)}}


def main():
    cfg = core.reference().biology
    res = {"config": {"threshold_shape": cfg.threshold_shape, "low_temperature_variant": cfg.low_temperature_variant}}
    for loss in (3e-4, 1e-3, 3e-3):
        res[f"L={loss:g}"] = {
            "reference": scan(cfg, None, loss),
            "kinetics_at_30C": scan(cfg, 30., loss),
            "kinetics_at_15C": scan(cfg, 15., loss),
            "thresholds_at_30C": scan(cfg, None, loss, 30.),
            "kinetics_and_thresholds_at_30C": scan(cfg, 30., loss, 30.),
        }
    g30 = guilds(30., cfg)
    res['thresholds_pa'] = {str(t): [g.threshold_pa for g in guilds(t, cfg)] for t in (0., 15., 30.)}
    res["peak_traits_30C"] = [{"guild": g.name, "V": g.rate_scale, "K_pa": g.km_pa, "h_pa": g.threshold_pa,
                               "Y": g.yield_g_mol, "m30": g.maintenance} for g in g30]
    res["maintenance_factor_4C_over_30C"] = maintenance_factor(4., cfg.maintenance_energy_j)
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()


# --- Best-response kinetics under a thermal-translation trait -------------------------
# A strain with kinetic position t_k behaves at local temperature T like the reference
# strain at t_k (V and K from the measured shape, t_k in [-0.15, 30] C: no extrapolation),
# times a hotter-is-better factor exp[-(E/kB)(1/T - 1/t_k)] on V. E = 0 is unconstrained.
# Thresholds (fixed cessation energy), maintenance and yield do not evolve.
KB_EV = 8.617333e-5
TK_GRID = np.round(np.arange(-0.15, 30.001, 0.05), 3)


def best_rstar(index, t, cfg, loss, e_ev):
    local = guilds(t, cfg)[index]
    best = (np.inf, None)
    for tk in TK_GRID:
        g = guilds(tk, cfg)[index]
        v = g.rate_scale * np.exp(-(e_ev / KB_EV) * (1 / (t + 273.15) - 1 / (tk + 273.15)))
        r = replace(g, rate_scale=v, maintenance=local.maintenance, threshold_pa=local.threshold_pa).rstar(loss)
        if r < best[0]:
            best = (r, tk)
    return best


def evolved_scan(cfg, loss, e_ev, ts=np.round(np.r_[-0.15, np.arange(0., 30.01, 0.5)], 2)):
    rows = []
    for t in ts:
        (ra, ka), (rm, km) = best_rstar(0, t, cfg, loss, e_ev), best_rstar(1, t, cfg, loss, e_ev)
        rows.append((t, ra - rm, ka, km))
    crossings = []
    for (t0, d0, *_), (t1, d1, *_) in zip(rows, rows[1:]):
        if np.isfinite(d0) and np.isfinite(d1) and d0 * d1 < 0:
            tc = t0 + (t1 - t0) * d0 / (d0 - d1)
            crossings.append({"t_k": round(tc + 273.15, 2), "cold_winner": "acetogen" if d0 < 0 else "methanogen"})
    return {"crossings": crossings,
            "winner_at": {str(t): ("acetogen" if d < 0 else "methanogen") for t, d, *_ in rows if t in (0., 8., 15., 23.)},
            "best_kinetic_temperature_c": {str(t): {"acetogen": ka, "methanogen": km} for t, d, ka, km in rows if t in (0., 8., 15., 23.)}}


def evolved_main():
    cfg = core.reference().biology
    out = {}
    for loss in (3e-4, 1e-3, 3e-3):
        for e in (0., 0.2, 0.45, 0.65):
            out[f"L={loss:g},E={e}"] = evolved_scan(cfg, loss, e)
    path = OUT.with_name(OUT.stem + "_evolved.json")
    path.write_text(json.dumps(out, indent=1) + "\n")
    return out


if __name__ == "__main__":
    for k, v in evolved_main().items():
        print(k, v["crossings"], v["winner_at"], v["best_kinetic_temperature_c"]["8.0"])
