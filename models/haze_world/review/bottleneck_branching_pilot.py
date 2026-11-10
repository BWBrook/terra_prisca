"""Pilot: survival of a rare guild through a deterministic bottleneck.

uv run python models/haze_world/review/bottleneck_branching_pilot.py

Reruns selected buffered-refuge invasions with the removal floor at zero and
1-year sampling, then treats the rare guild as a linear multitype birth-death
process in the environment of that uncensored trajectory. Per-cell rates in
habitat j: birth b = Y max(q-m, 0), death delta = loss + Y max(m-q, 0), and
migration j->k at d w_k (the cell-count form of the density exchange). The
probability u_j(t) that one cell's lineage is alive at t_out solves, backwards,

    du_j/dt = -b_j u_j (1-u_j) + delta_j u_j + sum_k m_jk (u_j - u_k),
    u_j(t_out) = 1,

and the population survives with probability 1 - exp(-sum_j N_j(t_in) u_j(t_in)).
The window [t_in, t_out] brackets the bottleneck where the guild is below
N_lin cells, too rare to alter H2, acetate or methane.
"""

from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

from terra_prisca.haze_world import buffered_experiments as experiments
from terra_prisca.haze_world import habitat_coupling as model
from terra_prisca.haze_world import habitat_integration as integration
from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world.population_coupling import HOURS_PER_YEAR

OUT = Path(__file__).with_suffix(".json")
CASES = [("main", "main_0008_t100000", 3000.), ("main", "main_0010_t100000", 3000.),
         ("main", "main_0012_t100000", 3000.), ("sensitivity", "sensitivity_0048_t100000", 3000.),
         ("main", "main_0040_t100000", 5000.), ("sensitivity", "sensitivity_0054_t100000", 5000.)]
GUILD = 0


def rates(y, p, log_x, t):
    """Per-cell birth and death of the acetogen in each active habitat (1/yr)."""
    ts = model.temperatures(y, p)
    out = []
    for j, patch in enumerate(p.patches):
        if patch.weight == 0:
            out.append((np.nan, np.nan))
            continue
        local = model.local_state(y, j).copy()
        local[1:3] = np.exp(log_x[j])
        pair = core.activity_guilds_at_temperature(local, p.base, float(ts[j]))
        g = pair[GUILD]
        s = g.yield_g_mol * (g.uptake(local[0]) - g.maintenance)
        b = max(s, 0.) * HOURS_PER_YEAR
        dlt = (p.base.biology.loss_h + max(-s, 0.)) * HOURS_PER_YEAR
        net = core.fluxes_at_temperature(local, p.base, float(ts[j]))["net_growth_yr"][GUILD]
        assert abs((b - dlt) - net) <= 1e-9 * max(1., abs(net)), (t, j, b, dlt, net)
        out.append((b, dlt))
    return np.array(out)


def run(item):
    stage, case_id, years = item
    case = next(c for c in experiments.design(stage) if c.case_id == case_id)
    p = experiments.parameters(case)
    record = experiments.read_record(case, experiments.RAW)
    with gzip.open(experiments.RAW / record["raw_file"], "rt") as stream:
        initial = np.asarray(json.load(stream)["initial"])
    census = integration.Census(minimum_cells=0., census_yr=1.)
    res = integration.integrate_finite(initial, p, years, census, sample_every_censuses=1)
    t = np.asarray(res.t)
    logb = np.asarray(res.log_biomass)
    y = np.asarray(res.y)
    w = p.weights
    active = [j for j in range(p.n_patches) if w[j] > 0]
    conv = float(res.metadata["global_log_cell_conversion"])
    log_cells = np.full((p.n_patches, t.size), -np.inf)
    for j in active:
        log_cells[j] = np.log(w[j]) + logb[j][GUILD] + conv
    log_total = np.logaddexp.reduce(log_cells[active], axis=0)
    k = int(np.argmin(log_total))
    log_min = float(log_total[k])
    log_lin = min(np.log(1e16), log_min + np.log(1e8))
    lo = k
    while lo > 0 and log_total[lo] < log_lin:
        lo -= 1
    hi = k
    while hi < t.size - 1 and log_total[hi] < log_lin:
        hi += 1
    window = slice(lo, hi + 1)
    tw = t[window]
    br = np.array([rates(y[:, i], p, logb[:, :, i], t[i]) for i in range(lo, hi + 1)])
    m = np.array([[p.dispersal_yr * w[kk] if kk != j else 0. for kk in active] for j in active])

    def interp(time):
        return np.array([[np.interp(time, tw, br[:, j, c]) for c in range(2)] for j in active])

    def back(time, logu):
        r = interp(time)
        u = np.exp(logu)
        return -r[:, 0] * (1 - u) + r[:, 1] + (m * (1 - u[None, :] / u[:, None])).sum(axis=1)

    sol = solve_ivp(back, (tw[-1], tw[0]), np.zeros(len(active)), method="LSODA", rtol=1e-9, atol=1e-12)
    logu = sol.y[:, -1]
    log_lambda = float(np.logaddexp.reduce([log_cells[j, lo] + logu[i] for i, j in enumerate(active)]))
    lam = float(np.exp(log_lambda))
    curv = np.gradient(np.gradient(log_total, t), t)[k]
    bulk = active[0]
    d_min = float(np.interp(t[k], tw, br[:, 0, 1]))
    gauss = float(np.exp(log_min) * np.sqrt(max(curv, 0) / (2 * np.pi)) / d_min) if curv > 0 else None
    return dict(case_id=case_id, fraction=case.fraction, configuration=case.configuration,
                refuge_fraction=case.refuge_fraction, dispersal_yr=case.dispersal_yr, direction=case.direction,
                success=bool(res.success), status=res.status, removals=len(res.extinction_events),
                min_time_yr=float(t[k]), log10_min_cells=log_min / np.log(10),
                window_yr=[float(tw[0]), float(tw[-1])], log10_window_cells=float(log_lin / np.log(10)),
                curvature_per_yr2=float(curv), bottleneck_width_yr=float(np.sqrt(2 * np.pi / curv)) if curv > 0 else None,
                bulk_birth_at_min_yr=float(np.interp(t[k], tw, br[:, 0, 0])), bulk_death_at_min_yr=d_min,
                max_global_temperature_k=float(np.max(res.temperatures_k[bulk])),
                expected_surviving_lineages=lam, survival_probability=float(-np.expm1(-lam)),
                gaussian_lineages=gauss,
                cells_for_half_survival_at_min=float(np.exp(log_min) * np.log(2) / lam),
                scale_for_half_survival=float(np.log(2) / lam),
                scale_for_one_cell_floor=float(np.exp(-log_min)))


def main():
    with ProcessPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, CASES))
    OUT.write_text(json.dumps(dict(
        scope="Pilot. Uncensored reruns at 1-year sampling; linear branching process in the trajectory's environment; not a planned-grid result",
        cases=rows), indent=1) + "\n")
    for r in rows:
        print(f"{r['case_id']:26s} d={r['dispersal_yr']:.0e} w={r['refuge_fraction']} min=10^{r['log10_min_cells']:.2f} "
              f"at {r['min_time_yr']:.0f} yr width={r['bottleneck_width_yr'] or float('nan'):.1f} yr "
              f"b=d={r['bulk_death_at_min_yr']:.2f}/yr Lambda={r['expected_surviving_lineages']:.3g} "
              f"(gauss {r['gaussian_lineages'] or float('nan'):.3g}) P={r['survival_probability']:.3g} "
              f"N50={r['cells_for_half_survival_at_min']:.3g} scale50={r['scale_for_half_survival']:.3g} Tmax={r['max_global_temperature_k']:.2f}")


if __name__ == "__main__":
    main()
