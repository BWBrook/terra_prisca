from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world.methane_budget import AVOGADRO, atmosphere
from terra_prisca.haze_world.population_coupling import (
    HOURS_PER_YEAR, equilibrium_states, fluxes, integrate, inventory_to_ratio,
    recycling_rates, redox_residual, reference, rhs, supply_h2,
)
from terra_prisca.haze_world.two_guilds import HENRY_30C_MOL_L_PA, equilibrium, guilds


def test_local_supply_and_atmospheric_column_have_one_consistent_conversion():
    baseline = reference(.3)
    for potential in (.12, .3, .6):
        p = reference(potential)
        assert p.habitat_l_cm2 == baseline.habitat_l_cm2
        assert p.biology.exchange_mol_l_h_pa == baseline.biology.exchange_mol_l_h_pa
        assert supply_h2(p) == pytest.approx(1e-6 * potential / .3)
        local = inventory_to_ratio(p) * HOURS_PER_YEAR * supply_h2(p) / 4
        column = atmosphere(p.climate.case)["flux_to_ratio_per_yr"] * p.climate.donor_flux
        assert local == pytest.approx(column)


def test_combined_redox_inventory_includes_starvation_and_external_exports():
    p = reference()
    for variant in ("constant", "cold_limited"):
        q = replace(p, recycling_variant=variant)
        for pressure in (.01, 30., 1000.):
            y = np.array([pressure, .001, .0007, .002, .195])
            f, dy = fluxes(y, q), rhs(y, q)
            a = np.array([g.assimilation_mol_g for g in guilds(f["temperature_k"] - 273.15, q.biology)])
            total = HENRY_30C_MOL_L_PA * dy[0] + a @ dy[1:3] + 4 * dy[3] + 4 * dy[4] / inventory_to_ratio(q)
            external = (f["supply_h2_mol_l_yr"] - f["outlet_h2_mol_l_yr"] -
                        4 * f["acetate_export_mol_l_yr"] - sum(f["biomass_export_h2_mol_l_yr"]) +
                        4 * (f["abiotic_ratio_yr"] - f["methane_loss_ratio_yr"]) / inventory_to_ratio(q))
            assert total == pytest.approx(external, abs=1e-14)
            assert abs(redox_residual(y, q)) < 1e-14
            if pressure == .01:
                ordinary_loss = a * q.biology.loss_h * y[1:3] * HOURS_PER_YEAR
                assert np.all(f["biomass_export_h2_mol_l_yr"] > ordinary_loss)


def test_acetate_lag_uses_years_and_recycling_enters_methane_once():
    p = replace(reference(), acetate_lifetime_yr=100.)
    y = np.array([30., .001, .001, .002, .195])
    delta = np.array([0., 0., 0., 1e-4, 0.])
    change = (rhs(y + delta, p) - rhs(y, p)) / delta[3]
    assert change[3] == pytest.approx(-1 / 100)
    assert change[4] == pytest.approx(inventory_to_ratio(p) * .5 / 100)
    assert np.all(change[:3] == 0)


def test_cold_inhibition_changes_fraction_and_lag_with_the_correct_endmember():
    p = replace(reference(), recycling_variant="cold_limited", acetate_fraction=.5)
    warm, cold = recycling_rates(290., p), recycling_rates(273., p)
    assert cold[0] / sum(cold) < warm[0] / sum(warm)
    assert 1 / sum(cold) > 1 / sum(warm)
    p = replace(p, acetate_fraction=1.)
    rec, other = recycling_rates(273., p)
    assert other == 0 and rec > 0
    assert rec / (rec + other) == 1.
    assert 1 / rec > p.acetate_lifetime_yr


def test_equilibria_share_the_fixed_temperature_resource_model_and_close_all_stocks():
    p = reference()
    states = equilibrium_states(p)
    mixed = next(e for e in states if e["kind"] == "mixed")
    assert mixed["t_k"] == pytest.approx(281.5348228, abs=1e-6)
    assert mixed["stable"]
    for e in states:
        y = e["y"]
        rates = rhs(y, p)
        assert abs(rates[0]) < 1e-6
        assert np.max(np.abs(rates[1:])) < 1e-10
        assert abs(e["redox_residual"]) < 1e-14
        if e["kind"] in ("acetogen", "methanogen"):
            enabled = (True, False) if e["kind"] == "acetogen" else (False, True)
            fixed = equilibrium(e["t_k"] - 273.15, p.biology, supply_h2(p), enabled=enabled)
            assert fixed["pressure_pa"] == pytest.approx(y[0])
            assert fixed["biomass_g_l"] == pytest.approx(y[1:3])


def test_constant_recycling_lag_changes_stocks_and_stability_not_equilibrium_fluxes():
    p = reference()
    short = equilibrium_states(p)
    long = equilibrium_states(replace(p, acetate_lifetime_yr=100.))
    assert [e["kind"] for e in short] == [e["kind"] for e in long]
    for a, b in zip(short, long):
        assert a["r"] == pytest.approx(b["r"], abs=1e-9)
        assert a["y"][:3] == pytest.approx(b["y"][:3])
        assert b["y"][3] == pytest.approx(100 * a["y"][3])


def test_population_dynamics_reach_the_predicted_mixed_equilibrium():
    p = reference()
    target = next(e for e in equilibrium_states(p) if e["kind"] == "mixed")
    y0 = target["y"] * [1.1, 1.05, .95, .9, 1.001]
    result = integrate(y0, p, 20000.)
    assert np.min(result.y) >= -1e-12
    assert result.y[:, -1] == pytest.approx(target["y"], rel=1e-5, abs=1e-9)


def test_disabled_population_is_absent_and_its_zero_coordinate_is_not_a_mode():
    p = replace(reference(), enabled=(False, True))
    target = next(e for e in equilibrium_states(p) if e["kind"] == "methanogen" and e["stable"])
    assert len(target["eigenvalues"]) == 4
    result = integrate(target["y"], p, 1.)
    assert np.all(result.y[1] == 0)
    with pytest.raises(ValueError, match="Disabled"):
        integrate(target["y"] + [0., .001, 0., 0., 0.], p, 1.)


def test_rare_invasion_retains_finite_coordinates_through_deep_population_declines():
    p = reference()
    control = replace(p, enabled=(False, True))
    start = next(e for e in equilibrium_states(control) if e["kind"] == "methanogen" and e["stable"])["y"].copy()
    start[1] = 1e-12
    result = integrate(start, p, 20000.)
    assert result.success
    assert np.all(np.isfinite(result.positive_coordinates))
    assert np.all(np.isfinite(result.log_biomass))
    assert np.min(result.log_biomass) < -1000
    assert np.min(result.y) >= -1e-10
    # No convergence or finite-population survival is inferred from this test.


def test_full_population_finder_keeps_a_mixed_state_at_a_climate_vertex():
    p = reference()
    r, t = .19445499, 282.005
    a, m = guilds(t - 273.15, replace(p.biology, capacity_ratio=1.))
    pressure = a.rstar(p.biology.loss_h)
    qm = m.maintenance + p.biology.loss_h / m.yield_g_mol
    capacity = qm * (1 + m.km_pa / (pressure - m.threshold_pa))
    biology = replace(p.biology, capacity_ratio=capacity / m.rate_scale)
    pair = guilds(t - 273.15, biology)
    required = np.array([g.maintenance + biology.loss_h / g.yield_g_mol for g in pair])
    b = 1 - np.array([g.assimilation_mol_g for g in pair]) * biology.loss_h / required
    kr, ko = recycling_rates(t, p)
    endpoint_average = (b[1] + kr / (kr + ko) * b[0]) / 2
    abiotic = atmosphere(p.climate.case)["flux_to_ratio_per_yr"] * p.climate.abiotic_flux
    captured = 4 * (float(p.loss.rate(r)) - abiotic) / (inventory_to_ratio(p) * HOURS_PER_YEAR * endpoint_average)
    local_supply = captured + biology.exchange_mol_l_h_pa * (pressure - biology.atmosphere_pa)
    flux = local_supply * AVOGADRO * p.habitat_l_cm2 / (4 * 3600)
    p = replace(p, biology=biology, climate=replace(p.climate, donor_flux=flux))
    states = [e for e in equilibrium_states(p) if e["kind"] == "mixed" and abs(e["r"] - r) < 1e-8]
    assert len(states) == 1
    assert states[0]["t_k"] == pytest.approx(t, abs=1e-8)
    assert len(states[0]["eigenvalues"]) == 10
