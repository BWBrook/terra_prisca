from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world.methane_budget import domain, temperature_k
from terra_prisca.haze_world.two_guilds import HENRY_30C_MOL_L_PA, guilds


def test_zero_temperature_offset_preserves_every_flux_field():
    state = np.array([30., .001, .0007, .002, .195])
    for activity in ("fixed", "products"):
        for recycling in ("constant", "cold_limited"):
            p = replace(core.reference(), activity_feedback=activity, recycling_variant=recycling)
            default = core.fluxes(state, p)
            explicit = core.fluxes_at_temperature(state, p, float(temperature_k(state[4], p.climate)))
            assert default.keys() == explicit.keys()
            for name in default:
                if isinstance(default[name], str):
                    assert default[name] == explicit[name]
                else:
                    np.testing.assert_array_equal(default[name], explicit[name])


def test_local_temperature_controls_physiology_and_recycling_with_shared_r():
    p = replace(core.reference(), recycling_variant="cold_limited", activity_feedback="products")
    state = np.array([30., .001, .0007, .002, .195])
    cold, warm = (core.fluxes_at_temperature(state, p, t) for t in (278.15, 294.15))
    for t, f in ((278.15, cold), (294.15, warm)):
        base = guilds(t - 273.15, p.biology)
        factors = ((state[3] / p.acetate_reference_mol_l) ** .25,
                   (state[4] * core.co2_pressure_pa(p.climate.case) / p.methane_reference_pa) ** .25)
        expected = tuple(replace(g, threshold_pa=g.threshold_pa * factor) for g, factor in zip(base, factors))
        q = np.array([g.uptake(state[0]) for g in expected])
        growth = np.array([g.yield_g_mol * (u - g.maintenance) - p.biology.loss_h
                           for g, u in zip(expected, q)]) * core.HOURS_PER_YEAR
        assert f["temperature_k"] == t
        assert f["climate_domain"] == str(domain(state[4], p.climate))
        assert f["uptake_h2_mol_l_yr"] == pytest.approx(q * state[1:3] * core.HOURS_PER_YEAR)
        assert f["net_growth_yr"] == pytest.approx(growth)
        assert f["k_rec_yr"] == pytest.approx(core.recycling_rates(t, p)[0])
    assert warm["k_rec_yr"] > cold["k_rec_yr"]
    assert not np.allclose(warm["net_growth_yr"], cold["net_growth_yr"])
    assert warm["methane_loss_ratio_yr"] == cold["methane_loss_ratio_yr"]
    assert warm["abiotic_ratio_yr"] == cold["abiotic_ratio_yr"]


def test_product_feedback_uses_local_acetate_and_shared_methane_at_supplied_temperature():
    p = replace(core.reference(), activity_feedback="products")
    state = np.array([30., .001, .001, p.acetate_reference_mol_l,
                      p.methane_reference_pa / core.co2_pressure_pa("B")])
    baseline = core.activity_guilds_at_temperature(state, p, 288.15)
    changed = state.copy()
    changed[3] *= 16
    local_product = core.activity_guilds_at_temperature(changed, p, 288.15)
    assert local_product[0].threshold_pa == pytest.approx(2 * baseline[0].threshold_pa)
    assert local_product[1] == baseline[1]
    changed = state.copy()
    changed[4] /= 16
    shared_product = core.activity_guilds_at_temperature(changed, p, 288.15)
    assert shared_product[1].threshold_pa == pytest.approx(.5 * baseline[1].threshold_pa)
    assert shared_product[0] == baseline[0]


def test_local_temperature_obeys_existing_supported_physiology_domain():
    p = core.reference()
    state = np.array([30., .001, .001, .001, .195])
    assert core.fluxes_at_temperature(state, p, 273.)["temperature_k"] == 273.
    measured_only = replace(p, biology=replace(p.biology, low_temperature_variant="none"))
    with pytest.raises(ValueError, match="4–30 C"):
        core.fluxes_at_temperature(state, measured_only, 276.)
    for bad in (272., 304., np.nan):
        with pytest.raises(ValueError, match="4–30 C"):
            core.fluxes_at_temperature(state, p, bad)


def test_local_temperature_fluxes_preserve_the_combined_redox_identity():
    for activity in ("fixed", "products"):
        p = replace(core.reference(), activity_feedback=activity, recycling_variant="cold_limited")
        conversion = core.inventory_to_ratio(p)
        for t in (277.15, 282., 300.):
            allocation = np.array([g.assimilation_mol_g for g in guilds(t - 273.15, p.biology)])
            for pressure in (.01, 30., 1000.):
                state = np.array([pressure, .001, .0007, .002, .195])
                f = core.fluxes_at_temperature(state, p, t)
                dp = (f["supply_h2_mol_l_yr"] - sum(f["uptake_h2_mol_l_yr"]) - f["outlet_h2_mol_l_yr"]) / HENRY_30C_MOL_L_PA
                dx = state[1:3] * f["net_growth_yr"]
                da = f["acetate_production_mol_l_yr"] - f["acetate_recycling_mol_l_yr"] - f["acetate_export_mol_l_yr"]
                dr = f["methane_source_ratio_yr"] - f["methane_loss_ratio_yr"]
                stored = HENRY_30C_MOL_L_PA * dp + allocation @ dx + 4 * da + 4 * dr / conversion
                external = (f["supply_h2_mol_l_yr"] - f["outlet_h2_mol_l_yr"] -
                            4 * f["acetate_export_mol_l_yr"] - sum(f["biomass_export_h2_mol_l_yr"]) +
                            4 * (f["abiotic_ratio_yr"] - f["methane_loss_ratio_yr"]) / conversion)
                assert stored == pytest.approx(external, abs=1e-14)


def test_acetate_production_coefficient_remains_defined_at_zero_producer_stock():
    p = replace(core.reference(), activity_feedback="products")
    initial = np.array([30., 0., .001, .0008, .195])
    empty = core.fluxes_at_temperature(initial, p, 282.)
    present = initial.copy()
    present[1] = .001
    occupied = core.fluxes_at_temperature(present, p, 282.)
    assert empty["acetate_production_mol_l_yr"] == 0.
    assert empty["acetate_production_per_gdw_yr"] > 0.
    assert empty["acetate_production_per_gdw_yr"] == occupied["acetate_production_per_gdw_yr"]
    assert occupied["acetate_production_mol_l_yr"] == pytest.approx(
        present[1] * occupied["acetate_production_per_gdw_yr"])
