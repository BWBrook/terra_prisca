import numpy as np
import pytest

from terra_prisca.haze_world.darwinian import (
    KB_EV,
    Constraint,
    biotic,
    control_params,
    convergence_slope,
    evolved,
    full_max_real_eigenvalue,
    gradient,
    invades_lifeless,
    reference,
    strain,
    supply_sensitivity,
)
from terra_prisca.haze_world.experiments import cold_edge_k

P, LOSSES = reference()
LINEAR, LOG = LOSSES[2], LOSSES[4]


def test_loss_family_is_anchored_and_invertible():
    for loss in LOSSES:
        a = loss.anchor_ratio
        assert loss.rate(a) == pytest.approx(a / loss.lifetime_yr, rel=1e-12)
        assert loss.inverse(float(loss.rate(0.05))) == pytest.approx(0.05, rel=1e-9)
        assert np.all(np.diff(loss.rate(np.linspace(0, 0.3, 50))) > 0)


@pytest.mark.parametrize("loss", LOSSES, ids=lambda x: x.label)
def test_unconstrained_evolution_reproduces_the_control_with_no_thermal_feedback(loss):
    e = evolved(P, Constraint(), loss)
    control = biotic(control_params(P), loss)
    assert e["theta_k"] == pytest.approx(e["t_k"]) and e["rho_realized"] == pytest.approx(10.0)
    assert e["t_k"] == pytest.approx(control["t_k"], abs=1e-9) and e["domain"] == "arney"
    s = supply_sensitivity(P, Constraint(), loss, e)
    assert s["evolutionary"] == pytest.approx(s["matched_control"], rel=1e-6)


def test_hotter_is_better_singularity_is_uninvadable_and_convergence_stable():
    c = Constraint(energy_ev=0.65)
    e = evolved(P, c, LINEAR)
    x, w = e["theta_k"] - e["t_k"], 20.0
    assert c.energy_ev / (KB_EV * e["theta_k"] ** 2) == pytest.approx(2 * x / (w**2 - x**2), rel=1e-8)
    curvature = -2 * c.energy_ev / (KB_EV * e["theta_k"] ** 3) - 2 * (w**2 + x**2) / (w**2 - x**2) ** 2
    assert curvature < 0 and convergence_slope(P, c, LINEAR, e["theta_k"]) < 0


def test_loss_shape_counterexample_reproduces_the_independent_review():
    c = Constraint(energy_ev=0.65)
    t_control = biotic(control_params(P), LINEAR)["t_k"]
    assert evolved(P, c, LINEAR)["t_k"] - t_control == pytest.approx(0.3202, abs=1e-4)
    assert evolved(P, c, LOG)["t_k"] - t_control == pytest.approx(4.6102, abs=1e-4)


def test_a_high_floor_restores_edge_regulation():
    c = Constraint(floor_k=295.0)
    e = evolved(P, c, LINEAR)
    q = strain(P, e["theta_k"], c)
    assert e["at_floor"] and e["theta_k"] == 295.0 and gradient(e["t_k"], 295.0, c) < 0
    assert cold_edge_k(q) < e["t_k"] < cold_edge_k(q) + 1.0
    s = supply_sensitivity(P, c, LINEAR, e)
    assert s["ecological"] / s["matched_control"] < 0.1


def test_persistence_is_distinct_from_reinvasion_of_the_lifeless_state():
    c = Constraint(energy_ev=0.65)
    e = evolved(P, c, LINEAR)
    q = strain(P, e["theta_k"], c)
    assert full_max_real_eigenvalue(q, LINEAR, e) < 0
    assert not invades_lifeless(q, LINEAR, 265.0)
    assert invades_lifeless(q, LINEAR, 283.0)
    unconstrained = evolved(P, Constraint(), LINEAR)
    assert invades_lifeless(strain(P, unconstrained["theta_k"], Constraint()), LINEAR, 265.0)


def test_floor_below_the_unconstrained_optimum_is_inactive():
    e = evolved(P, Constraint(floor_k=270.0), LINEAR)
    assert not e["at_floor"] and e["t_k"] == pytest.approx(evolved(P, Constraint(), LINEAR)["t_k"])
