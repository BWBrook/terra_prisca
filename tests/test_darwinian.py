from dataclasses import replace

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
    local_regulation,
    reinvasion_window,
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
        h = 1e-7
        assert loss.slope(0.2) == pytest.approx(float(loss.rate(0.2 + h) - loss.rate(0.2 - h)) / (2 * h), rel=1e-6)


@pytest.mark.parametrize("loss", LOSSES, ids=lambda x: x.label)
def test_unconstrained_evolution_reproduces_the_control_with_no_thermal_feedback(loss):
    e = evolved(P, Constraint(), loss)
    control = biotic(control_params(P), loss)
    assert e["theta_k"] == pytest.approx(e["t_k"]) and e["rho_realized"] == pytest.approx(10.0)
    assert e["t_k"] == pytest.approx(control["t_k"], abs=1e-9) and e["domain"] == "arney"
    assert local_regulation(strain(P, e["theta_k"], Constraint()), loss, e)["right"]["ratio"] == 1.0


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
    assert local_regulation(q, LINEAR, e)["right"]["ratio"] < 0.1


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


@pytest.mark.parametrize("c,loss_index,expected", [
    (Constraint(floor_k=290.0), 4, 0.808476),
    (Constraint(energy_ev=0.6), 1, 0.898970),
    (Constraint(energy_ev=0.65), 4, 0.295431),
])
def test_local_regulation_matches_a_converged_finite_difference(c, loss_index, expected):
    loss = LOSSES[loss_index]
    e = evolved(P, c, loss)
    q = strain(P, e["theta_k"], c)
    reg = local_regulation(q, loss, e)
    assert not reg["at_vertex"] and reg["right"]["ratio"] == pytest.approx(expected, abs=2e-6)
    eps = 1e-6
    ts = {}
    for name, base in (("thermal", q), ("matched", control_params(P, e["rho_realized"]))):
        ts[name] = [biotic(replace(base, donor_flux=P.donor_flux * f), loss)["t_k"] for f in (1 - eps, 1 + eps)]
    fd = (ts["thermal"][1] - ts["thermal"][0]) / (ts["matched"][1] - ts["matched"][0])
    assert fd == pytest.approx(expected, rel=1e-3)


def test_reinvasion_threshold_is_the_bridge_endpoint_that_reaches_the_net_growth_edge():
    c = Constraint(floor_k=300.0)
    e = evolved(P, c, LINEAR)
    q = strain(P, e["theta_k"], c)
    w = reinvasion_window(q, LINEAR)
    assert w["t0_min_k"] == pytest.approx(280.817723, abs=1e-5)
    assert cold_edge_k(q) < e["t_k"]
    assert invades_lifeless(q, LINEAR, w["t0_min_k"] + 0.05) and not invades_lifeless(q, LINEAR, w["t0_min_k"] - 0.05)
    assert invades_lifeless(q, LINEAR, 280.9) and 280.9 < e["t_k"]


def test_vertex_flag_uses_response_geometry_not_finite_differences():
    from terra_prisca.haze_world.darwinian import climate_slopes
    from terra_prisca.haze_world.methane_budget import temperature_k
    from terra_prisca.haze_world.methane_budget import response
    c = Constraint(floor_k=289.0)
    e = evolved(P, c, LOSSES[0])
    q = strain(P, e["theta_k"], c)
    reg = local_regulation(q, LOSSES[0], e)
    assert not reg["at_vertex"] and reg["left"] == reg["right"]
    h = 1e-7
    fd = (temperature_k(e["r"] + h, q) - temperature_k(e["r"] - h, q)) / (2 * h)
    assert climate_slopes(e["r"], q)[0] == pytest.approx(fd, rel=1e-6)
    resp = response(P.case)
    r, t = float(resp.ratios[5]), float(resp.temperatures_k[5])
    vertex = local_regulation(replace(P, t_opt_k=t), LINEAR, {"r": r, "t_k": t})
    assert vertex["at_vertex"] and vertex["left"]["dT_dlnS"] != vertex["right"]["dT_dlnS"]
    for r0 in (0.3 * resp.ratios[0], resp.ratios[0]):
        assert climate_slopes(r0, P)[0] == pytest.approx(
            (temperature_k(r0, P) - temperature_k(r0 - 1e-9, P)) / 1e-9, rel=1e-5)
