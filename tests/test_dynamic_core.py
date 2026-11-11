from dataclasses import replace

import numpy as np
import pytest
from scipy.optimize import brentq

from terra_prisca.haze_world import dynamic_core as dynamic
from terra_prisca.haze_world import population_coupling as core


@pytest.mark.parametrize("chemistry", ("fixed", "products"))
def test_homogeneous_equilibria_and_flows_recover_named_reference(chemistry):
    base = replace(core.reference(), activity_feedback=chemistry)
    p = dynamic.DynamicParams(base, chemistry)
    original = core.equilibrium_states(base)
    current = dynamic.equilibrium_states(p)
    for expected in original:
        if expected["kind"] == "lifeless":
            continue
        actual = next(e for e in current if e["kind"] == expected["kind"] and abs(e["r"]-expected["r"]) < 1e-6)
        np.testing.assert_allclose(actual["y"], expected["y"], rtol=1e-7, atol=1e-11)
        np.testing.assert_allclose(dynamic.physical_rhs(actual["y"], p), core.rhs(actual["y"], base), atol=1e-8)


@pytest.mark.parametrize("chemistry", dynamic.CHEMISTRIES)
def test_analytic_state_jacobian_agrees_with_independent_differences(chemistry):
    p = dynamic.DynamicParams(core.reference(), chemistry)
    y = next(e["y"] for e in dynamic.equilibrium_states(p) if e["kind"] == "mixed")
    matrix, _, _ = dynamic.jacobian_blocks(y, p)
    scale = dynamic.state_scales(y, p)
    numerical = np.empty_like(matrix)
    for j in range(len(y)):
        delta = np.eye(len(y))[j]*scale[j]*1e-5
        numerical[:, j] = (dynamic.physical_rhs(y+delta, p, dynamic.temperature(y[-1], p))-
                            dynamic.physical_rhs(y-delta, p, dynamic.temperature(y[-1], p)))/(2*scale[j]*1e-5)
    matrix = matrix*scale[None, :]/scale[:, None]
    numerical = numerical*scale[None, :]/scale[:, None]
    np.testing.assert_allclose(matrix, numerical, rtol=1e-6, atol=5e-5)


def test_lag_block_recovers_independent_critical_lag_and_implicit_gain():
    p = dynamic.DynamicParams(replace(core.reference(), acetate_fraction=0.), "fixed")
    y = next(e["y"] for e in dynamic.equilibrium_states(p) if e["kind"] == "mixed")
    leading = lambda tau: max(np.linalg.eigvals(dynamic.thermal_matrix(y, p, tau)).real)
    assert brentq(leading, .1, .3) == pytest.approx(.1492142601, rel=2e-6)
    assert abs(dynamic.implicit_response(y, p)["dtemperature_dlog_supply"]) < 1e-8
    assert max(np.linalg.eigvals(dynamic.thermal_matrix(y, p, 0.)).real) < 0


def test_uniform_quantiles_and_full_support_domain_are_distinct():
    p = dynamic.DynamicParams(core.reference(), sigma_k=5.5, n_habitats=9)
    np.testing.assert_allclose(p.offsets, np.linspace(-44/9, 44/9, 9))
    ratio = brentq(lambda r: dynamic.temperature(r, p)-278.4, .19, .21)
    y = np.r_[np.tile([20., .001, .001, .001], p.n), ratio]
    status = dynamic.temperature_status(y, p)
    assert status["local_min_k"] > 273.
    assert status["support_min_k"] < 273.
    assert status["physiology_status"] == "domain_censored"


def test_spread_equilibrium_preserves_biomass_exchange_and_state_balance():
    p = dynamic.DynamicParams(replace(core.reference(), acetate_fraction=0.), sigma_k=3., n_habitats=9)
    records = dynamic.equilibrium_states(p)
    assert records
    state = records[0]["y"]
    stocks = state[:-1].reshape(p.n, 4)
    assert np.all(stocks[:, 1:3] > 0)
    exchange = p.dispersal_yr*(stocks[:, 1:3].mean(axis=0)-stocks[:, 1:3])
    np.testing.assert_allclose(exchange.sum(axis=0), 0., atol=1e-20)
    assert records[0]["residual"] < 1e-6
    assert 282. < records[0]["t_k"] < 284.


def test_two_layer_temperature_block_is_explicit_energy_balance_realisation():
    p = dynamic.DynamicParams(core.reference())
    state = next(e["y"] for e in dynamic.equilibrium_states(p) if e["kind"] == "mixed")
    matrix = dynamic.thermal_matrix(state, p, 3., two_layer=True)
    np.testing.assert_allclose(matrix[-2:, -2:], [[-2/3, 1/3], [1/300, -1/300]])
    assert matrix.shape == (7, 7)


def test_cached_jacobian_blocks_cannot_be_modified_by_spectrum_callers():
    p = dynamic.DynamicParams(core.reference())
    state = next(e["y"] for e in dynamic.equilibrium_states(p) if e["kind"] == "mixed")
    expected = dynamic.reduced_matrix(state, p)
    matrix, column, _ = dynamic.jacobian_blocks(state, p)
    matrix[:] = np.nan; column[:] = np.nan
    np.testing.assert_array_equal(dynamic.reduced_matrix(state, p), expected)
    assert np.all(np.isfinite(dynamic.thermal_matrix(state, p, 3.)))


def test_tiny_guild_cannot_pass_a_mixed_root_check_with_nonzero_per_capita_growth():
    base = core.reference(.36)
    base = replace(base, acetate_fraction=0., biology=replace(base.biology, loss_h=.002))
    p = dynamic.DynamicParams(base, "products", sigma_k=3., n_habitats=9)
    acetogen_only = replace(p, base=replace(base, enabled=(True, False)))
    resident = dynamic.equilibrium_states(acetogen_only)[0]["y"].copy()
    resident[2:-1:4] = 1e-40
    assert np.max(np.abs(dynamic.physical_rhs(resident, p)/dynamic.state_scales(resident, p))) < 1e-6
    assert np.max(np.abs(dynamic.biomass_per_capita(resident, p)[:, 1])) > .1
    corrected = dynamic.continue_equilibrium(resident, p)
    if corrected is not None:
        assert corrected["biomass_per_capita_residual_yr"] < 1e-7
    records = dynamic.equilibrium_states(p)
    assert records
    assert all(e["biomass_per_capita_residual_yr"] < 1e-7 for e in records)
    assert all(abs(e["t_k"]-283.19877678579377) > .01 for e in records)
    assert any(e["t_k"] == pytest.approx(287.0336604574322, abs=1e-7) for e in records)


def test_per_capita_residual_does_not_treat_tiny_balanced_sinks_as_extinct():
    p = dynamic.DynamicParams(core.reference(), "fixed", sigma_k=3., n_habitats=9)
    y = dynamic.equilibrium_states(p)[0]["y"].copy()
    before = dynamic.biomass_per_capita(y, p)
    y[1:-1:4] *= 1e-100
    # Fixed chemistry makes net growth and the migration mean/stock ratios
    # invariant to this diagnostic rescaling of one complete guild.
    np.testing.assert_allclose(dynamic.biomass_per_capita(y, p)[:, 0], before[:, 0], atol=1e-15)
    assert min(y[1:-1:4]) < 1e-100
