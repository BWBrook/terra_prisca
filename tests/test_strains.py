import numpy as np
import pytest

from terra_prisca.haze_world.darwinian import Constraint, reference
from terra_prisca.haze_world.experiments import flux_for_potential
from dataclasses import replace

from terra_prisca.haze_world.strains import Run, StrainModel, rescue, seed_escape, viability_threshold

P, LOSSES = reference()
LINEAR = LOSSES[2]


def test_mutation_moves_births_without_changing_methane_production():
    model = StrainModel(P, Run(Constraint(), LINEAR, mutation=1e-2))
    phi = float(flux_for_potential(0.22, P))
    y, _ = model.resident_state(phi)
    y[2:] = np.where(np.abs(model.theta - 273.5) < 2.1, y[2:].max(), 0.0)
    rates = model.rhs(0.0, y, lambda t: phi)
    births = rates[2:] + model.run.death * y[2:]
    u_total = rates[1] - model.c * P.abiotic_flux + float(LINEAR.rate(y[1]))
    assert births.sum() == pytest.approx(u_total, rel=1e-10)


def test_single_bin_resident_state_is_the_stage_one_equilibrium():
    model = StrainModel(P, Run(Constraint(), LINEAR, mutation=0.0))
    phi = float(flux_for_potential(0.22, P))
    y, e = model.resident_state(phi)
    rates = model.rhs(0.0, y, lambda t: phi)
    assert abs(rates[1]) < 1e-3 * float(LINEAR.rate(y[1]))
    assert np.max(np.abs(rates[2:])) < 1e-3 * y[2:].max()


def test_a_strain_that_cannot_divide_produces_no_mutants():
    model = StrainModel(P, Run(Constraint(), LINEAR, mutation=1e-2))
    t_k = 265.6
    warm_zero = model.theta[(model.rho(t_k) == 0.0) & (model.theta > t_k)]
    assert warm_zero.min() > t_k + 19.9
    r = seed_escape(P, Run(Constraint(), LINEAR, mutation=1e-2, b_min_rel=1e-9), seed_theta_k=287.0, years=200.0)
    assert not r["alive_at_end"]


def test_mutation_rescues_a_declining_clone_that_can_still_divide():
    run = Run(Constraint(), LINEAR, mutation=1e-2, b_min_rel=1e-9, check_yr=1.0)
    rescued = seed_escape(P, run, seed_theta_k=285.5, years=2e3)
    clone = seed_escape(P, replace(run, mutation=0.0), seed_theta_k=285.5, years=2e3)
    assert rescued["initial_net_growth_per_yr"] < 0 and rescued["steps_to_viable"] > 0
    assert rescued["alive_at_end"] and not clone["alive_at_end"]


def test_final_supply_viability_threshold_matches_the_independent_check():
    h = Constraint(energy_ev=0.65)
    q = replace(P, t_zero_k=265.0)
    assert viability_threshold(q, h, LINEAR)["potential"] == pytest.approx(0.02087893, abs=2e-7)
    assert viability_threshold(q, h, LINEAR, 285.5)["potential"] == pytest.approx(0.02088523, abs=2e-7)
    assert viability_threshold(q, Constraint(), LINEAR)["potential"] < 0.001


def test_mutation_below_the_census_threshold_cannot_track_the_haze_loss_warming():
    run = Run(Constraint(), LINEAR, mutation=1e-8, b_min_rel=1e-6, check_yr=10.0)
    r = rescue(P, run, decline_yr=1e3, after_yr=6e3)
    assert not r["survived"] and r["max_abs_lag_k"] > 18
    fast = rescue(P, Run(Constraint(), LINEAR, mutation=1e-4, b_min_rel=1e-6, check_yr=10.0),
                  decline_yr=1e3, after_yr=6e3)
    assert fast["survived"]
