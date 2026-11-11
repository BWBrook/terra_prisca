from dataclasses import replace

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from terra_prisca.haze_world.experiments import cold_edge_k, domain_invariant, flux_for_potential, t_opt_for_edge
from terra_prisca.haze_world.methane_budget import (
    Params,
    atmosphere,
    capture_efficiency,
    equilibria,
    full_derivatives,
    integrate_full,
    ratio_for_flux,
    response,
    temperature_k,
    tendency,
)

P = Params()
HIGH = replace(P, donor_flux=float(flux_for_potential(0.3, P)))


def test_closure_is_continuous_and_labels_assumptions():
    resp = response("B")
    r1, r_end = resp.ratios[0], resp.ratios[-1]
    assert temperature_k(0.0, P) == pytest.approx(P.t_zero_k)
    assert temperature_k(r1 - 1e-12, P) == pytest.approx(resp.temperatures_k[0], abs=1e-6)
    assert temperature_k(0.5, P) == resp.temperatures_k[-1]
    assert np.all(np.diff(temperature_k(np.linspace(0, r1, 200), P)) > 0)
    with pytest.raises(ValueError):
        temperature_k(0.05, P, extend=False)


def test_column_conversion_for_one_bar():
    assert atmosphere("B")["column"] == pytest.approx(2.19e25, rel=0.01)
    assert atmosphere("D")["column"] == pytest.approx(0.5 * atmosphere("B")["column"])


def test_capture_efficiency_matches_quasi_steady_algebra():
    t = np.array([P.t_opt_k, P.t_opt_k - 10.0])
    rho = P.growth_ratio_max * (1 - ((t - P.t_opt_k) / P.t_halfwidth_k) ** 2)
    np.testing.assert_allclose(capture_efficiency(t, P), 1 - P.maintenance_flux / (P.donor_flux * (rho - 1)))
    edge = cold_edge_k(P)
    assert capture_efficiency(edge - 1e-6, P) == 0.0 < capture_efficiency(edge + 1e-3, P)
    flat = replace(P, thermal=False)
    assert np.ptp(capture_efficiency(np.linspace(250, 300, 11), flat)) == 0.0


def test_lifeless_planet_holds_only_abiotic_methane():
    e = equilibria(replace(P, donor_flux=0.0))
    assert len(e) == 1 and e[0]["stable"] and e[0]["eta"] == 0.0
    assert e[0]["r"] == pytest.approx(ratio_for_flux(P.abiotic_flux, P), rel=1e-9)
    assert e[0]["domain"] == "bridge"  # abiotic methane alone never reaches Arney's domain


def test_full_three_variable_model_settles_on_the_reduced_equilibrium():
    warm = [e for e in equilibria(HIGH) if e["stable"] and e["eta"] > 0][-1]
    c = atmosphere("B")["flux_to_ratio_per_yr"]
    y = integrate_full(np.array([c * HIGH.donor_flux / 0.1, 1e-6, 0.15]), HIGH, 3e5)
    assert y[2] == pytest.approx(warm["r"], rel=1e-4)


def test_positive_biomass_recovers_after_a_long_cold_interval():
    warm = [e for e in equilibria(HIGH) if e["stable"] and e["eta"] > 0][-1]
    c = atmosphere("B")["flux_to_ratio_per_yr"]
    y = integrate_full(np.array([c * HIGH.donor_flux / 0.1, 1e-6, response("B").ratios[-1]]), HIGH, 3e5)
    assert y[1] > 0
    assert y[2] == pytest.approx(warm["r"], rel=1e-4)


def test_success_status_does_not_hide_nonfinite_accepted_state(monkeypatch):
    from types import SimpleNamespace
    from terra_prisca.haze_world import methane_budget

    monkeypatch.setattr(methane_budget, "solve_ivp", lambda *args, **kwargs:
                        SimpleNamespace(success=True, y=np.full((3, 1), np.nan)))
    with pytest.raises(RuntimeError, match="nonfinite internal"):
        integrate_full(np.array([1e-5, 1e-6, .2]), HIGH, 10.)


def test_reduced_interval_invariance_does_not_imply_full_state_invariance():
    lo = response("B").ratios[0]
    c = atmosphere("B")["flux_to_ratio_per_yr"]
    assert domain_invariant(HIGH) and tendency(lo, HIGH) > 0
    rates = full_derivatives(np.array([c * HIGH.donor_flux / 0.1, 1e-12, lo]), HIGH)
    assert rates[2] < 0


def test_exactly_absent_biomass_is_not_automatically_reseeded():
    c = atmosphere("B")["flux_to_ratio_per_yr"]
    y = integrate_full(np.array([c * HIGH.donor_flux / 0.1, 0.0, 0.2]), HIGH, 1e5)
    assert y[1] == 0
    assert y[2] == pytest.approx(ratio_for_flux(HIGH.abiotic_flux, HIGH), rel=0.02)


def test_stability_labels_agree_with_the_reduced_flow():
    for e in equilibria(HIGH):
        for dr in (-2e-4, 2e-4):
            sol = solve_ivp(lambda _t, r: tendency(r, HIGH), (0, 2e5), [e["r"] + dr], rtol=1e-10, atol=1e-14)
            assert (abs(sol.y[0, -1] - e["r"]) < 1e-5) == e["stable"]


@pytest.mark.parametrize("case,edge", [("A", 270.0), ("B", 281.0), ("C", 275.0), ("D", 260.0)])
def test_high_supply_pins_temperature_at_the_cold_edge_inside_arneys_domain(case, edge):
    q = replace(P, case=case)
    q = replace(q, donor_flux=float(flux_for_potential(0.3 * response(case).ratios[-1] / 0.2333, q)))
    q = replace(q, t_opt_k=t_opt_for_edge(edge, q))
    assert domain_invariant(q)
    warm = [e for e in equilibria(q) if e["stable"] and e["eta"] > 0][-1]
    assert warm["domain"] == "arney"
    assert edge < warm["t_k"] < edge + 0.1  # approached from above as supply rises
    passive = [e for e in equilibria(replace(q, thermal=False)) if e["stable"]][-1]
    assert passive["t_k"] < edge - 5


def test_cold_trap_bistability_when_zero_methane_climate_is_below_the_edge():
    stable = [e for e in equilibria(HIGH) if e["stable"]]
    assert [e["eta"] > 0 for e in stable] == [False, True]
    warm_world = replace(HIGH, t_zero_k=cold_edge_k(HIGH) + 3.0)
    assert all(e["eta"] > 0 for e in equilibria(warm_world) if e["stable"])
