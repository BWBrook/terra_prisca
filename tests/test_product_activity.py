from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world.methane_budget import temperature_k
from terra_prisca.haze_world.population_coupling import (
    activity_guilds, co2_pressure_pa, equilibrium_states, fluxes, redox_residual,
    reference, rhs,
)
from terra_prisca.haze_world.two_guilds import guilds


def test_product_references_restore_temperature_only_cutoffs_without_co2_retuning():
    p = replace(reference(), activity_feedback="products")
    assert co2_pressure_pa("B") == pytest.approx(1800.)
    ratio = p.methane_reference_pa / co2_pressure_pa("B")
    y = np.array([30., .001, .001, p.acetate_reference_mol_l, ratio])
    actual = activity_guilds(y, p)
    base = guilds(float(temperature_k(ratio, p.climate)) - 273.15, p.biology)
    assert [g.threshold_pa for g in actual] == pytest.approx([g.threshold_pa for g in base])


@pytest.mark.parametrize("factor", (0., 1/16, 1., 16.))
def test_positive_quarter_power_changes_only_product_cutoffs(factor):
    p = replace(reference(), activity_feedback="products")
    r = factor * p.methane_reference_pa / co2_pressure_pa("B")
    y = np.array([30., .001, .001, factor * p.acetate_reference_mol_l, r])
    pair = activity_guilds(y, p)
    base = guilds(float(temperature_k(r, p.climate)) - 273.15, p.biology)
    for actual, original in zip(pair, base):
        assert actual.threshold_pa == pytest.approx(original.threshold_pa * factor ** .25)
        assert actual.rate_scale == original.rate_scale
        assert actual.maintenance == original.maintenance
        assert actual.km_pa == original.km_pa


def test_fixed_activity_variant_and_combined_inventory_remain_explicit():
    p = reference()
    y = np.array([30., .001, .001, .01, .195])
    unchanged = activity_guilds(y, p)
    base = guilds(float(temperature_k(y[4], p.climate)) - 273.15, p.biology)
    assert unchanged == base
    changed = replace(p, activity_feedback="products")
    assert abs(redox_residual(y, changed)) < 1e-14
    assert fluxes(y, changed)["uptake_h2_mol_l_yr"][0] < fluxes(y, p)["uptake_h2_mol_l_yr"][0]


def test_product_equilibria_use_actual_acetate_and_methane_in_growth_and_budget():
    p = replace(reference(), activity_feedback="products")
    states = equilibrium_states(p)
    mixed = next(e for e in states if e["kind"] == "mixed")
    assert mixed["stable"]
    assert mixed["t_k"] == pytest.approx(281.2848267, abs=1e-5)
    assert mixed["t_k"] != pytest.approx(281.5348228, abs=.01)
    for e in states:
        f, dy = fluxes(e["y"], p), rhs(e["y"], p)
        assert abs(dy[0]) < 1e-6
        assert max(abs(dy[1:])) < 1e-9
        assert abs(e["redox_residual"]) < 1e-14
        actual = activity_guilds(e["y"], p)
        for i in (0, 1):
            if e["y"][i + 1] > 0:
                assert actual[i].net_growth(e["y"][0], p.biology.loss_h) == pytest.approx(0., abs=1e-12)


def test_product_correction_is_not_a_hard_acetate_cap():
    p = replace(reference(), activity_feedback="products", acetate_lifetime_yr=10000.)
    states = equilibrium_states(p)
    assert states
    # The normalized Nernst law limits viability, not molarity by definition.
    assert any(e["stable"] and e["y"][3] > .01 for e in states)


def test_product_reference_values_must_be_positive():
    with pytest.raises(ValueError, match="Product reference"):
        replace(reference(), acetate_reference_mol_l=0.)
