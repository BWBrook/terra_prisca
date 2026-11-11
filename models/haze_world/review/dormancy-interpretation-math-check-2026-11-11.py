"""Bounded algebra checks for the dormancy-review interpretations.

No trajectories are integrated and no earlier result is rewritten.
"""

from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world import branching, dormancy, dormancy_experiments


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def main():
    cases = [
        ("methanogens", 0., .006, .006, .007),
        ("methanogens", .5, .00247, .00245, .002499),
        ("acetogens", 0., .00046, .00046, .0005),
        ("acetogens", .5, .00082, .00082, .0009),
    ]
    threshold = [dict(guild=g, fraction=f, review_approximation=p,
                      measured_bracket=[lo, hi], measured_over_review=[lo/p, hi/p])
                 for g, f, p, lo, hi in cases]
    coefficient = 6.2
    loss = .001*8766
    half_fraction = np.log(2.)/(loss*coefficient)

    gaussian_path = HERE/"check_turnover_gaussian.json"
    gaussian = json.loads(gaussian_path.read_text())["shape_diagnostic"]
    assert abs(gaussian["scalar_relative_difference"]) < 1e-4

    count, birth, duration = 14500, 6.6, 15.
    effective_hazard = birth*duration
    repetitions = []
    for cycles in (1, 100, 1000, 1000000):
        per_lineage = 1/(1+effective_hazard*cycles)
        log_poisson_extinction = -count*per_lineage
        log_fixed_extinction = count*np.log1p(-per_lineage)
        repetitions.append(dict(cycles=cycles,
            single_lineage_survival=per_lineage,
            poisson_initial_extinction=float(np.exp(log_poisson_extinction)),
            fixed_initial_extinction=float(np.exp(log_fixed_extinction)),
            poisson_log_extinction=float(log_poisson_extinction)))
    assert repetitions[0]["poisson_initial_extinction"] < 1e-60
    assert repetitions[1]["poisson_initial_extinction"] > .2
    assert repetitions[-1]["poisson_initial_extinction"] > .999
    reset_bound = 1000000*np.exp(-count/(1+effective_hazard))
    half_cycles = (count/np.log(2.)-1)/effective_hazard

    case = next(c for c in dormancy_experiments.design() if c.case_id == "dormancy_0024")
    p = dormancy_experiments.parameters(case)
    y = np.zeros(p.state_size)
    y[[0, 1, 2, 3, 5, -1]] = [500., 1e-4, 1e-4, 1e-3, 1e-4, .195]
    other = y.copy()
    other[5] *= 2
    old_flux, new_flux = dormancy.fluxes(y, p), dormancy.fluxes(other, p)
    old_rhs, new_rhs = dormancy.rhs(y, p), dormancy.rhs(other, p)
    rho = old_flux["rho_yr"][0, 1]
    active_change = new_rhs[2]-old_rhs[2]
    assert old_flux["methane_source_ratio_yr"] == new_flux["methane_source_ratio_yr"]
    assert rho > 0 and np.isclose(active_change, rho*(other[5]-y[5]), rtol=1e-13)
    step = y[2]*1e-5
    shifted = y.copy()
    shifted[2] += step
    methane_gradient = (dormancy.fluxes(shifted, p)["methane_source_ratio_yr"]
                        -old_flux["methane_source_ratio_yr"])/step
    assert methane_gradient > 0 and active_change > 0
    feedback = dict(scope="Synthetic positive in-domain state, not a new trajectory or a measured threshold effect",
        climate_flags=dormancy.temperature_flags(y, p),
        instantaneous_methane_source_equal=True,
        dormant_methanogen_change_gdw_l=float(other[5]-y[5]),
        waking_rate_yr=float(rho), active_derivative_change_gdw_l_yr=float(active_change),
        methane_source_gradient_per_active_gdw_l=float(methane_gradient),
        implied_methane_source_time_derivative_change=float(methane_gradient*active_change))

    result = dict(
        scope="Algebra, a scalar counterexample and an instantaneous model-dependency check; no repeated-cycle prediction for case0012",
        source_sha256={str(Path(m.__file__).relative_to(ROOT)):digest(m.__file__)
                       for m in (branching, dormancy, dormancy_experiments)},
        checker_sha256=digest(__file__),
        review_sha256=digest(HERE/"turnover-dormancy-claude-review-2026-11-11.md"),
        gaussian_check_sha256=digest(gaussian_path),
        seed_bank=dict(review_approximation_comparisons=threshold,
            half_life_fraction_given_coefficient=float(half_fraction),
            implied_log_population_ratio=float(loss*coefficient),
            original_f05_methanogen_lower_bound=.0025,
            scope="Approximate agreement of four brackets, not exact or general path invariance"),
        scalar_integrated_check=gaussian,
        scalar_periodic_counterexample=dict(initial_count=count,birth_yr=birth,
            death_yr=birth,active_years_per_cycle=duration,period_yr=443.,
            no_events_between_active_intervals=True,
            no_population_reset=True,results=repetitions,
            cycles_to_half_survival_poisson=float(half_cycles),
            restoration_scenario_million_cycle_union_bound=float(reset_bound)),
        indirect_dormant_feedback=feedback)
    HERE.joinpath("dormancy-interpretation-math-check-2026-11-11.json").write_text(
        json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps(dict(half_fraction=half_fraction,cycles_to_half=half_cycles,
        extinction_at100=repetitions[1]["poisson_initial_extinction"],
        extinction_at_million=repetitions[-1]["poisson_initial_extinction"],
        reset_union_bound=reset_bound,feedback=feedback),sort_keys=True))


if __name__ == "__main__":
    main()
