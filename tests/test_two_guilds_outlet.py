from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import methane_budget
from terra_prisca.haze_world.two_guilds import (
    ASSIMILATION_A, Competition, delivery, equilibrium, guilds, integrate, shape,
    thresholds, counts,
)
from terra_prisca.haze_world.hydrogen_uptake import ACETOGEN, MSB, MSP


@pytest.mark.parametrize("temperature,loss,form", [(4., .001, "saturating"), (30., .001, "saturating"), (4., .01, "first_order")])
def test_finite_outlet_equilibria_and_population_dynamics(temperature, loss, form):
    supply = 1e-6
    c = Competition(loss_h=loss, kinetics=form, exchange_mol_l_h_pa=supply / 300)
    eq = equilibrium(temperature, c, supply)
    assert eq["status"] == "living"
    assert eq["pressure_pa"] < eq["lifeless_pressure_pa"]
    flow = delivery(eq["pressure_pa"], eq["biomass_g_l"], temperature, c, 1.)
    assert sum(flow["uptake_h2_mol_l_h"]) + eq["outlet_h2_mol_l_h"] == pytest.approx(supply)
    result = integrate(temperature, c, 100., [1e-4, 1e-4], 100000, supply=supply)
    assert result.y[0, -1] == pytest.approx(eq["pressure_pa"], rel=1e-6)
    assert np.exp(result.y[1:, -1]) == pytest.approx(eq["biomass_g_l"], rel=1e-6, abs=1e-10)


def test_outlet_produces_finite_lifeless_state_and_limits_first_order_survival():
    supply = 1e-6
    sat = Competition(loss_h=.01, exchange_mol_l_h_pa=supply / 50)
    linear = replace(sat, kinetics="first_order")
    for c in (sat, linear):
        eq = equilibrium(4, c, supply)
        assert eq["status"] == "lifeless"
        assert eq["pressure_pa"] == pytest.approx(50.)
        assert eq["capture_fraction"] == 0.
        assert eq["outlet_h2_mol_l_h"] == pytest.approx(supply)
        assert max(g.net_growth(50, c.loss_h) for g in guilds(4, c)) < 0
    summarized = counts([equilibrium(4, c) for c in (sat, linear)])
    assert summarized["lifeless"] == sum(summarized.values()) == 2
    trajectory = integrate(4, sat, 10., [1e-4, 1e-4], 100000, supply=supply)
    assert trajectory.y[0, -1] == pytest.approx(50., rel=1e-7)
    assert max(np.exp(trajectory.y[1:, -1])) < 1e-15
    assert equilibrium(4, replace(linear, exchange_mol_l_h_pa=supply / 300))["status"] == "living"


def test_atmospheric_inflow_is_counted_instead_of_clipping_capture():
    c = Competition(exchange_mol_l_h_pa=1e-8, atmosphere_pa=100.)
    eq = equilibrium(30, c)
    assert eq["status"] == "living"
    assert eq["outlet_h2_mol_l_h"] < 0
    assert eq["capture_fraction"] > 1
    flux = sum(delivery(eq["pressure_pa"], eq["biomass_g_l"], 30, c)["uptake_h2_mol_l_h"])
    assert flux == pytest.approx(1e-6 - eq["outlet_h2_mol_l_h"])
    absent = equilibrium(30, c, enabled=(False, False))
    assert absent["status"] == "lifeless"
    assert absent["pressure_pa"] == pytest.approx(200.)


def test_methanogen_only_exactly_reduces_to_existing_capture_closure():
    # One common conversion maps molar H2 to CH4-equivalent surface flux.
    # Its value cancels; it does not calibrate a habitat depth or atmosphere.
    conversion = 1e17 / 4
    for t in (4., 15., 30.):
        for gamma in (.01, .1, .74):
            for supply in (1e-8, 1e-6, 1e-4):
                c = Competition(capacity_ratio=gamma, maintenance_m30=0., threshold_m30=0.,
                                exchange_mol_l_h_pa=1e-8)
                m = guilds(t, c)[1]
                rho = c.yield_m * m.rate_scale / c.loss_h
                old = methane_budget.Params(thermal=False, growth_ratio_max=rho,
                    donor_flux=conversion * supply,
                    maintenance_flux=conversion * c.exchange_mol_l_h_pa * m.km_pa)
                expected = float(methane_budget.capture_efficiency(t + 273.15, old))
                eq = equilibrium(t, c, supply, enabled=(False, True))
                assert eq["capture_fraction"] == pytest.approx(expected, abs=1e-14)
                assert eq["biomass_g_l"][0] == 0
                if eq["status"] == "living":
                    methane = delivery(eq["pressure_pa"], eq["biomass_g_l"], t, c)["methane_mol_l_h"]
                    assert 4 * methane / supply == pytest.approx(expected)


def test_general_methanogen_capture_retains_maintenance_and_threshold():
    c = Competition(exchange_mol_l_h_pa=1e-8)
    eq = equilibrium(30, c, enabled=(False, True))
    m = guilds(30, c)[1]
    required = m.maintenance + c.loss_h / m.yield_g_mol
    rho_effective = m.rate_scale / required
    root = m.threshold_pa + m.km_pa / (rho_effective - 1)
    expected = max(0., 1 - c.exchange_mol_l_h_pa * (root - c.atmosphere_pa) / 1e-6)
    assert eq["capture_fraction"] == pytest.approx(expected)
    old_rho = m.yield_g_mol * m.rate_scale / c.loss_h
    naive = max(0., 1 - c.exchange_mol_l_h_pa * m.km_pa / (1e-6 * (old_rho - 1)))
    assert eq["capture_fraction"] != pytest.approx(naive, abs=1e-3)


def test_affinity_and_cessation_brackets_preserve_their_reference_anchors():
    c = Competition(threshold_shape="fixed_energy")
    for scale_a, scale_m in ((1/3, 1/3), (1/7, 1), (1, 1)):
        changed = replace(c, km_scale_a=scale_a, km_scale_m=scale_m)
        for before, after, factor in zip(guilds(30, c), guilds(30, changed), (scale_a, scale_m)):
            assert after.km_pa == pytest.approx(before.km_pa * factor)
            assert after.rate_scale == before.rate_scale
            assert after.threshold_pa == before.threshold_pa
    for a in (-20000., -24000., -28000.):
        for m in (-24000., -28000., -32000.):
            changed = replace(c, cessation_energy_a_j=a, cessation_energy_m_j=m)
            assert thresholds(30, changed) == pytest.approx((20., 1.))
            assert all(np.array(thresholds(4, changed)) < (20., 1.))


def test_named_cold_continuations_are_continuous_and_keep_source_values():
    for strain in (ACETOGEN, MSB, MSP):
        source = shape(4, strain)
        for mode in ("constant_shape", "arrhenius_continuation"):
            assert shape(4, strain, mode) == source
            assert shape(4 - 1e-8, strain, mode) == pytest.approx(source, rel=1e-8)
            assert shape(20, strain, mode) == shape(20, strain)
        assert shape(0, strain, "constant_shape") == source
        assert shape(0, strain, "arrhenius_continuation")[0] < source[0]
        with pytest.raises(ValueError, match="named continuation"):
            shape(0, strain)
        for mode in ("constant_shape", "arrhenius_continuation"):
            assert all(np.isfinite(shape(273 - 273.15, strain, mode)))
            assert all(np.isfinite(shape(-.15, strain, mode)))


def test_symmetric_assimilation_changes_products_but_not_competition():
    a = Competition(exchange_mol_l_h_pa=1e-6 / 300)
    b = replace(a, assimilation_m=ASSIMILATION_A)
    ea, eb = equilibrium(30, a), equilibrium(30, b)
    assert ea["winner"] == eb["winner"] == "methanogen"
    assert ea["pressure_pa"] == eb["pressure_pa"]
    fa = delivery(ea["pressure_pa"], ea["biomass_g_l"], 30, a, 1.)
    fb = delivery(eb["pressure_pa"], eb["biomass_g_l"], 30, b, 1.)
    assert fb["methane_mol_l_h"] < fa["methane_mol_l_h"]
    assert 4 * fb["methane_mol_l_h"] + sum(fb["biomass_h2_mol_l_h"]) == pytest.approx(eb["captured_h2_mol_l_h"])
