from dataclasses import replace

import numpy as np
import pytest
from scipy.optimize import brentq

from terra_prisca.haze_world.hydrogen_uptake import ACETOGEN, MSB, MSP, parameters
from terra_prisca.haze_world.two_guilds import (
    ASSIMILATION_A, Competition, FIRST_ORDER_LIMIT_MOL_L, HENRY_30C_MOL_L_PA,
    delivery, equilibrium, guilds, integrate, parameter_grid, shape, thresholds,
)


def test_source_shapes_and_transfer_anchor_are_distinct():
    pair = guilds(30)
    assert pair[0].rate_scale == pytest.approx(.024 / 1.7 + .0016)
    assert pair[1].rate_scale / pair[0].rate_scale == pytest.approx(.74)
    for strain in (ACETOGEN, MSB, MSP):
        for t in (4., 10., 15., 20., 25., 30.):
            ratio, km = shape(t, strain)
            assert ratio == pytest.approx(parameters(t, strain).vmax_nmol_h / parameters(30, strain).vmax_nmol_h)
            assert km == parameters(t, strain).km_pa
    with pytest.raises(ValueError, match="4–30"):
        guilds(31.)


def test_break_even_roots_against_independent_scalar_growth_solutions():
    for form in ("saturating", "first_order"):
        for t in (4., 15., 30.):
            c = Competition(kinetics=form)
            for g in guilds(t, c):
                numerical = brentq(lambda p: g.net_growth(p, c.loss_h), 0, 1e6)
                assert g.rstar(c.loss_h) == pytest.approx(numerical, rel=1e-10)


def test_independent_scoping_reconstruction_and_invasion_signs():
    cold = []
    for c in parameter_grid(MSB):
        warm = equilibrium(30, c)
        if warm["winner"] == "methanogen":
            cold.append(equilibrium(4, c))
        for t in (4., 30.):
            eq = equilibrium(t, c)
            if eq["status"] == "living":
                assert eq["invader_growth_h"] < 0
                i = ("acetogen", "methanogen").index(eq["winner"])
                assert guilds(t, c)[i].net_growth(eq["pressure_pa"], c.loss_h) == pytest.approx(0, abs=1e-14)
    assert len(cold) == 167
    assert [sum(r["winner"] == w for r in cold) for w in ("acetogen", "methanogen", "no_consumer")] == [33, 107, 27]


def test_fixed_energy_scaling_contains_cessation_energy_and_msp_anomaly():
    c = Competition(threshold_shape="fixed_energy", methanogen=MSP, msp_threshold_4c=200)
    a4, m4 = thresholds(4, c)
    assert m4 == pytest.approx(200.)
    assert thresholds(30, c) == pytest.approx((20., 1.))
    assert a4 < 20
    # Independent threshold energy rearrangement, at fixed non-H2 activities.
    expected = 20 * np.exp((-270700 + 24000) / (4 * 8.314) * (1 / 277.15 - 1 / 303.15))
    assert a4 == pytest.approx(expected)
    assert a4 != pytest.approx(20 * np.exp(-270700 / (4 * 8.314) * (1 / 277.15 - 1 / 303.15)))


def test_first_order_is_a_structural_alternative_with_declared_domain():
    c = Competition(loss_h=.01)
    assert equilibrium(4, c)["status"] == "no_consumer"
    linear = replace(c, kinetics="first_order")
    assert equilibrium(4, linear)["status"] == "living"
    excessive = replace(linear, loss_h=100.)
    eq = equilibrium(4, excessive)
    assert eq["status"] == "outside_first_order_domain"
    assert eq["pressure_pa"] * HENRY_30C_MOL_L_PA > FIRST_ORDER_LIMIT_MOL_L
    sat, lin = guilds(30, c)[0], guilds(30, linear)[0]
    assert guilds(30, linear)[1].kinetics == "saturating"
    p = sat.threshold_pa + 1e-5 * sat.km_pa
    assert lin.uptake(p) / sat.uptake(p) == pytest.approx(1 + 1e-5)


def test_routing_conserves_hydrogen_and_distinguishes_input_conversion():
    c = Competition()
    eq = equilibrium(4, c)
    assert eq["winner"] == "acetogen"
    for fac in (0., .37, 1.):
        flow = delivery(eq["pressure_pa"], eq["biomass_g_l"], 4, c, fac)
        consumed = np.sum(flow["uptake_h2_mol_l_h"])
        assert consumed == pytest.approx(1e-6)
        assert np.sum(flow["biomass_h2_mol_l_h"]) + 4 * (
            flow["methane_mol_l_h"] + flow["nonmethane_acetate_mol_l_h"]) == pytest.approx(consumed)
        assert flow["routing_factor"] == pytest.approx(1 - (1 - fac) * flow["acetogen_catabolic_share"])
    assert flow["routing_factor"] == pytest.approx(1.)
    assert 4 * flow["methane_mol_l_h"] / 1e-6 < 1.
    assert flow["biomass_h2_mol_l_h"][0] == pytest.approx(ASSIMILATION_A * c.loss_h * eq["biomass_g_l"][0])
    empty = delivery(1., [0., 0.], 4, c, 1.)
    assert np.isnan(empty["routing_factor"])


@pytest.mark.parametrize("temperature,loss,form", [(4., .001, "saturating"), (30., .001, "saturating"), (4., .01, "first_order")])
def test_full_population_dynamics_reach_predicted_exclusion(temperature, loss, form):
    c = Competition(loss_h=loss, kinetics=form)
    eq = equilibrium(temperature, c)
    result = integrate(temperature, c, 100., [1e-4, 1e-4], 100000.)
    endpoint_p = result.y[0, -1]
    endpoint_b = np.exp(result.y[1:, -1])
    assert np.min(result.y[0]) >= 0
    assert endpoint_p == pytest.approx(eq["pressure_pa"], rel=1e-6)
    assert endpoint_b == pytest.approx(eq["biomass_g_l"], rel=1e-6, abs=1e-10)
    assert all(np.isfinite(result.y[1:, -1]))
    assert np.sum(delivery(endpoint_p, endpoint_b, temperature, c)["uptake_h2_mol_l_h"]) == pytest.approx(1e-6, rel=1e-6)


def test_supply_sets_biomass_not_resource_winner():
    a, b = equilibrium(15, supply=1e-6), equilibrium(15, supply=7e-6)
    assert a["winner"] == b["winner"]
    assert a["pressure_pa"] == b["pressure_pa"]
    assert b["biomass_g_l"] == pytest.approx(7 * a["biomass_g_l"])
    with pytest.raises(ValueError, match="Biomass synthesis"):
        Competition(assimilation_m=10)
