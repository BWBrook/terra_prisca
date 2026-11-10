from dataclasses import replace

import numpy as np
import pytest
from scipy.optimize import brentq
from scipy.linalg import expm
from scipy.optimize import minimize_scalar

from terra_prisca.haze_world import population_coupling as single
from terra_prisca.haze_world import refuge_coupling as model
from terra_prisca.haze_world.refuge_integration import Census, integrate, integrate_finite


def mixed():
    return next(e["y"] for e in single.equilibrium_states(single.reference()) if e["kind"] == "mixed")


def toy(monkeypatch, p, growth, ratio_rate=0., acetate_decay=0., acetate_production_per_g=0.):
    def local_growth(y):
        value = growth(y) if callable(growth) else growth
        return np.asarray(value, dtype=float)

    def fluxes(y, params, **kwargs):
        g = local_growth(y)
        return {"local": [{"net_growth_yr": g[j],
                           "acetate_production_mol_l_yr": acetate_production_per_g*y[4*j+1],
                           "acetate_production_per_gdw_yr": acetate_production_per_g,
                           "k_rec_yr": 0., "k_other_yr": acetate_decay}
                          if w else None for j, w in enumerate(params.weights)]}

    def rhs(y, params, **kwargs):
        result = np.zeros(9)
        g = local_growth(y)
        stocks = np.asarray(y)[model.BIOMASS_INDICES]
        exchange = np.zeros((2, 2))
        if np.all(params.weights > 0):
            exchange[0] = params.dispersal_yr * params.weights[1] * (stocks[1] - stocks[0])
            exchange[1] = params.dispersal_yr * params.weights[0] * (stocks[0] - stocks[1])
        result[model.BIOMASS_INDICES] = stocks * g + exchange
        result[[3, 7]] = acetate_production_per_g*stocks[:, 0] - acetate_decay*np.asarray(y)[[3, 7]]
        result[8] = ratio_rate
        return result

    monkeypatch.setattr(model, "fluxes", fluxes)
    monkeypatch.setattr(model, "rhs", rhs)
    return p


def test_identical_habitats_follow_the_single_habitat_continuum():
    start = mixed() * [1.01, .99, 1.01, 1.001, 1.00001]
    for fraction, dispersal in ((.2, 0.), (.8, .1)):
        p = model.Refuge(warm_fraction=fraction, dispersal_yr=dispersal)
        result = integrate(model.embed_single(start, p), p, 20.)
        control = single.integrate(start, p.base, 20., sample_times=result.t)
        assert result.success and result.status == "completed"
        assert result.log_biomass.shape == (2, 2, len(result.t))
        assert result.temperatures_k.shape == result.physiology_domains.shape == (2, len(result.t))
        for j in (0, 1):
            np.testing.assert_allclose(np.vstack((result.y[4*j:4*j+4], result.y[8])), control.y,
                                       rtol=4e-6, atol=1e-9)


def test_one_active_habitat_reduces_to_the_single_habitat():
    start = mixed() * [1.01, .99, 1.01, 1.001, 1.00001]
    for fraction, active in ((0., 0), (1., 1)):
        p = model.Refuge(warm_fraction=fraction, contrast_k=20., dispersal_yr=1.)
        result = integrate(model.embed_single(start, p), p, 5.)
        control = single.integrate(start, p.base, 5., sample_times=result.t)
        np.testing.assert_allclose(np.vstack((result.y[4*active:4*active+4], result.y[8])), control.y,
                                   rtol=4e-6, atol=1e-9)
        assert np.all(result.y[4*(1-active):4*(1-active)+4] == 0)
        assert np.all(result.physiology_domains[1-active] == "inactive")


def test_dispersal_rescues_a_local_zero_but_cannot_create_a_globally_absent_guild(monkeypatch):
    p = toy(monkeypatch, model.Refuge(warm_fraction=.7, dispersal_yr=.1), [[0., 100.], [0., 100.]])
    start = np.array([30., 0., 0., .001, 30., .001, 0., .001, .195])
    result = integrate(start, p, 30.)
    total = .7 * .001
    expected_cold = total * (1 - np.exp(-p.dispersal_yr * result.t))
    np.testing.assert_allclose(result.y[1], expected_cold, rtol=3e-6, atol=1e-12)
    np.testing.assert_allclose(p.weights @ result.y[model.BIOMASS_INDICES[:, 0]], total, rtol=2e-12)
    assert np.all(result.y[[2, 6]] == 0)
    assert np.all(np.isneginf(result.log_biomass[:, 1]))
    assert result.y[1, -1] > 0
    assert result.metadata["external_immigration"] == "none"
    np.testing.assert_allclose(result.global_continuous_min_log_biomass[0], np.log(total), atol=1e-12)
    assert np.isneginf(result.global_continuous_min_log_biomass[1])


def test_initial_cull_exports_mass_and_redox_and_distinguishes_the_jump_minimum():
    p = model.Refuge(base=replace(single.reference(), habitat_l_cm2=1.), warm_fraction=.7,
                     dispersal_yr=.1)
    start = model.embed_single(mixed(), p)
    start[1], start[5] = .5 / p.weights[0], 2. / p.weights[1]
    start[[2, 6]] = 0
    process = Census(cell_mass_gdw=1., surface_cm2=1.)
    result = integrate_finite(start, p, 0., process)
    assert len(result.extinction_events) == 1
    assert result.extinction_events[0]["patch"] == "cold"
    assert result.extinction_events[0]["removed_cells"] == pytest.approx(.5)
    assert result.y[1, -1] == 0
    assert result.pre_removal_min_log_biomass[0, 0] == pytest.approx(np.log(start[1]))
    assert np.isneginf(result.after_census_min_log_biomass[0, 0])
    jump = model.inventory(start, p) - model.inventory(result.y[:, -1], p)
    assert result.ledger["inventory_jump_h2_mol_l"].sum() == pytest.approx(jump, abs=1e-12)
    assert result.ledger["culled_gdw"].sum() == pytest.approx(.5)
    assert result.ledger["culled_h2_mol"].sum() == pytest.approx(.5 * single.ASSIMILATION_A)


def test_culled_local_lineage_can_return_from_the_other_habitat(monkeypatch):
    p = model.Refuge(base=replace(single.reference(), habitat_l_cm2=1.), warm_fraction=.7,
                     dispersal_yr=.1)
    p = toy(monkeypatch, p, [[0., 0.], [0., 0.]])
    start = np.array([30., .5/p.weights[0], 0., .001,
                      30., 100./p.weights[1], 0., .001, .195])
    process = Census(cell_mass_gdw=1., surface_cm2=1.)
    result = integrate_finite(start, p, 20., process, sample_every_censuses=1)
    assert len(result.extinction_events) == 1
    assert result.extinction_events[0]["time_yr"] == 0
    assert not result.census_activity[0] & 1
    assert result.census_activity[1] & 1
    assert result.y[1, -1] > 0
    assert p.weights @ result.y[[1, 5], -1] == pytest.approx(100., rel=2e-12)
    assert result.ledger["culled_cells"].sum() == pytest.approx(.5)
    assert np.isneginf(result.continuous_min_log_biomass[0, 0])
    assert np.isfinite(result.pre_removal_min_log_biomass[0, 0])
    assert result.global_pre_extinction_min_log_biomass[0] == pytest.approx(np.log(100.), abs=2e-12)
    assert result.global_continuous_min_log_biomass[0] == pytest.approx(np.log(100.), abs=2e-12)
    assert result.global_after_census_min_log_biomass[0] == pytest.approx(np.log(100.), abs=2e-12)


def test_dense_minimum_finds_an_interior_dip_missed_by_censuses(monkeypatch):
    p = model.Refuge(base=replace(single.reference(), habitat_l_cm2=1.))
    p = toy(monkeypatch, p, lambda y: np.array([[20*(y[8]-.195), 0.],
                                               [20*(y[8]-.195), 0.]]), ratio_rate=.001)
    start = np.array([30., 8., 0., .001, 30., 8., 0., .001, .19])
    result = integrate_finite(start, p, 10., Census(minimum_cells=3.5, cell_mass_gdw=1., surface_cm2=1.),
                              sample_every_censuses=1, max_step=.2)
    assert result.extinction_events == []
    np.testing.assert_allclose(result.continuous_min_times_yr[:, 0], 5., atol=2e-5)
    np.testing.assert_allclose(result.continuous_min_log_biomass[:, 0], np.log(8.)-.25, atol=2e-6)
    assert np.all(result.continuous_min_log_biomass[:, 0] < result.after_census_min_log_biomass[:, 0])
    assert result.metadata["solver_resets"] == 0


def test_permanent_global_loss_is_absorbing_and_pre_removal_minima_freeze(monkeypatch):
    p = model.Refuge(base=replace(single.reference(), habitat_l_cm2=1.))
    p = toy(monkeypatch, p, [[-1., 0.], [-1., 0.]])
    start = np.array([30., 4., 0., .001, 30., 4., 0., .001, .195])
    result = integrate_finite(start, p, 3., Census(census_yr=1., cell_mass_gdw=1., surface_cm2=1.),
                              sample_every_censuses=1)
    assert len(result.extinction_events) == 2
    assert all(e["time_yr"] == 1 for e in result.extinction_events)
    assert np.all(result.y[[1, 5]][:, result.t >= 1] == 0)
    np.testing.assert_allclose(result.pre_removal_min_log_biomass[:, 0], np.log(4)-1, atol=2e-6)
    assert np.all(np.isneginf(result.continuous_min_log_biomass[:, 0]))
    assert result.metadata["solver_resets"] == 1
    assert result.global_pre_extinction_min_log_biomass[0] == pytest.approx(np.log(4)-1, abs=2e-6)
    assert np.isneginf(result.global_after_census_min_log_biomass[0])
    assert np.isneginf(result.global_continuous_min_log_biomass[0])


def test_domain_exit_is_found_even_if_temperature_reenters_before_step_endpoint(monkeypatch):
    p = toy(monkeypatch, model.Refuge(warm_fraction=.1, contrast_k=10.), [[0., 0.], [0., 0.]], ratio_rate=.01)
    start = np.array([30., .001, 0., .001, 30., .001, 0., .001, .01])
    root = brentq(lambda r: single.temperature_k(r, p.base.climate)+p.offsets[1]-303.15, .01, .12)
    assert all(flag != "unsupported" for flag in model.temperature_flags(start, p))
    unbounded_end = start.copy(); unbounded_end[8] += .01 * 18.5
    assert all(flag != "unsupported" for flag in model.temperature_flags(unbounded_end, p))
    result = integrate(start, p, 18.5)
    assert not result.success and result.status == "domain_exit"
    assert result.t[-1] == pytest.approx((root-.01)/.01, abs=1e-7)
    assert result.temperatures_k[1, -1] == pytest.approx(303.15, abs=1e-8)
    assert result.metadata["last_physical_time_yr"] == result.t[-1]


def test_shared_guild_rare_minimum_matches_a_linear_population_solution(monkeypatch):
    p = toy(monkeypatch, model.Refuge(warm_fraction=.4, dispersal_yr=.01), [[-2., 0.], [1., 0.]])
    start = np.array([30., 1e-20, 0., .001, 30., 1e-20, 0., .001, .195])
    result = integrate(start, p, 10.)
    matrix = np.array([[-2.-.01*p.weights[1], .01*p.weights[1]],
                       [.01*p.weights[0], 1.-.01*p.weights[0]]])
    expected = np.array([expm(matrix*t) @ np.array([1e-20, 1e-20]) for t in result.t]).T
    np.testing.assert_allclose(result.y[[1, 5]], expected, rtol=4e-6, atol=1e-40)
    minimum = minimize_scalar(lambda t: np.log((expm(matrix*t) @ [1e-20, 1e-20])[0]),
                              bounds=(0., 10.), method="bounded")
    assert result.continuous_min_log_biomass[0, 0] == pytest.approx(minimum.fun, abs=2e-6)
    assert result.continuous_min_times_yr[0, 0] == pytest.approx(minimum.x, abs=2e-5)
    global_minimum = minimize_scalar(lambda t: np.log(p.weights @ (expm(matrix*t) @ [1e-20, 1e-20])),
                                     bounds=(0., 10.), method="bounded")
    assert result.global_continuous_min_log_biomass[0] == pytest.approx(global_minimum.fun, abs=2e-6)
    assert result.global_continuous_min_times_yr[0] == pytest.approx(global_minimum.x, abs=2e-5)


def test_continuum_logs_survive_physical_underflow_without_an_extinction_event(monkeypatch):
    p = toy(monkeypatch, model.Refuge(), [[-2., 0.], [-2., 0.]])
    start = np.array([30., 1e-20, 0., .001, 30., 1e-20, 0., .001, .195])
    result = integrate(start, p, 500.)
    assert np.all(result.y[[1, 5], -1] == 0)
    np.testing.assert_allclose(result.log_biomass[:, 0, -1], np.log(1e-20)-1000., atol=1e-7)
    assert result.extinction_events == []
    assert np.all(np.isfinite(result.continuous_min_log_biomass[:, 0]))
    assert result.global_continuous_min_log_biomass[0] == pytest.approx(np.log(1e-20)-1000., abs=1e-7)


def test_global_minimum_is_not_the_weighted_sum_of_asynchronous_local_minima(monkeypatch):
    def growth(y):
        time = (y[8]-.19)/.001
        return [[.2*(time-2), 0.], [.2*(time-8), 0.]]
    p = toy(monkeypatch, model.Refuge(), growth, ratio_rate=.001)
    scale = 1e-20
    start = np.array([30., scale*np.exp(.4), 0., .001,
                      30., scale*np.exp(6.4), 0., .001, .19])
    result = integrate(start, p, 10., max_step=.2)
    np.testing.assert_allclose(result.continuous_min_times_yr[:, 0], [2., 8.], atol=3e-5)
    assert result.global_continuous_min_times_yr[0] == pytest.approx(5., abs=3e-5)
    assert result.global_continuous_min_log_biomass[0] == pytest.approx(np.log(scale)+.9, abs=2e-6)
    incorrect_sum = p.weights @ np.exp(result.continuous_min_log_biomass[:, 0])
    assert np.exp(result.global_continuous_min_log_biomass[0]) > 2*incorrect_sum
    assert result.global_pre_extinction_min_log_biomass[0] == result.global_continuous_min_log_biomass[0]


def test_unsupported_initial_habitat_is_reported_without_a_trial_trajectory():
    p = model.Refuge(contrast_k=40.)
    result = integrate(model.embed_single(mixed(), p), p, 10.)
    assert result.status == "initial_unsupported" and not result.success
    assert np.array_equal(result.t, [0.])
    assert result.metadata["nfev"] == 0


def test_zero_acetate_start_switches_coordinates_without_an_inventory_seed(monkeypatch):
    p = toy(monkeypatch, model.Refuge(), [[0., 0.], [0., 0.]],
            acetate_decay=1., acetate_production_per_g=.01)
    start = np.array([30., .001, 0., 0., 30., .001, 0., 0., .195])
    result = integrate(start, p, 20.)
    expected = 1e-5*(-np.expm1(-result.t))
    np.testing.assert_allclose(result.y[[3, 7]], np.vstack((expected, expected)), rtol=3e-6, atol=1e-13)
    assert np.all(result.y >= 0)
    assert np.all(result.y[[3, 7], 0] == 0)
    assert len(result.metadata["acetate_coordinate_switches"]) == 2
    assert result.metadata["acetate_coordinate_resets"] >= 1
    assert result.metadata["census_solver_resets"] == 0


def test_acetate_log_production_uses_producer_logs_beyond_physical_underflow(monkeypatch):
    p = toy(monkeypatch, model.Refuge(), [[-1., 0.], [-1., 0.]],
            acetate_decay=2., acetate_production_per_g=1.)
    start = np.array([30., 1e-20, 0., 1e-20, 30., 1e-20, 0., 1e-20, .195])
    result = integrate(start, p, 1000.)
    expected = np.log(1e-20)-result.t
    np.testing.assert_allclose(result.log_acetate, np.vstack((expected, expected)), atol=2e-6)
    assert np.all(result.y[[1, 3, 5, 7], -1] == 0)
    assert np.all(np.isfinite(result.log_acetate))


def test_acetate_underflow_log_survives_a_later_biomass_census_reset(monkeypatch):
    p = model.Refuge(base=replace(single.reference(), habitat_l_cm2=1.))
    p = toy(monkeypatch, p, [[0., -.001], [0., -.001]], acetate_decay=1.)
    count_density = 2*np.exp(.8005)
    start = np.array([30., 0., count_density, .001, 30., 0., count_density, .001, .195])
    process = Census(census_yr=1., cell_mass_gdw=1., surface_cm2=1.)
    result = integrate_finite(start, p, 1000., process, sample_every_censuses=1)
    assert all(e["time_yr"] == 801 for e in result.extinction_events)
    assert result.metadata["census_solver_resets"] == 1
    assert np.all(result.y[[3, 7], -1] == 0)
    np.testing.assert_allclose(result.log_acetate[:, -1], np.log(.001)-1000., atol=2e-6)


def test_dense_temperature_range_includes_an_unsampled_radiative_peak(monkeypatch):
    p = toy(monkeypatch, model.Refuge(), [[0., 0.], [0., 0.]], ratio_rate=.01)
    start = np.array([30., .001, 0., .001, 30., .001, 0., .001, .01])
    result = integrate_finite(start, p, 18.5, Census(), sample_every_censuses=100)
    expected_peak = max(single.response(p.base.climate.case).temperatures_k)
    assert result.success
    assert result.metadata["global_max_temperature_k"] == expected_peak
    assert result.metadata["global_max_temperature_k"] > max(result.temperatures_k[0])+.1
    np.testing.assert_allclose(result.metadata["patch_max_temperature_k"], expected_peak)


def test_product_feedback_and_one_patch_seeds_keep_zero_initial_acetate_nonnegative():
    base = replace(single.reference(), activity_feedback="products")
    start = next(e["y"] for e in single.equilibrium_states(replace(base, enabled=(False, True)))
                 if e["kind"] == "methanogen" and e["stable"])
    for origin in (0, 1):
        p = model.Refuge(base=base, warm_fraction=.3, dispersal_yr=.001)
        y = model.embed_single(start, p)
        y[model.BIOMASS_INDICES[origin, 0]] = 1e-12/p.weights[origin]
        assert np.all(y[[3, 7]] == 0)
        result = integrate_finite(y, p, 30., Census(), sample_every_censuses=1)
        assert result.success and np.all(result.y >= 0)
        assert len(result.metadata["acetate_coordinate_switches"]) == 2
        assert np.all(np.isfinite(result.log_acetate[:, -1]))


def test_formerly_negative_acetate_pilot_reaches_its_domain_boundary_nonnegative():
    from terra_prisca.haze_world.refuge_experiments import conditional_start, design, parameters, seed_state
    case = design("pilot")[2]
    p = parameters(case)
    resident, _ = conditional_start(p, 0, 201)
    assert resident is not None
    y, _ = seed_state(case, resident["y"])
    result = integrate_finite(y, p, case.years, Census(census_yr=case.census_yr), sample_every_censuses=1)
    assert result.status == "domain_exit"
    assert 700 < result.t[-1] < 900
    assert result.temperatures_k[1, -1] == pytest.approx(303.15, abs=1e-7)
    assert np.all(np.isfinite(result.y)) and np.all(result.y >= 0)
    assert np.all(np.isfinite(result.log_acetate[:, -1]))


def test_dense_allocation_anchors_the_exact_left_state_but_rejects_an_interior_excursion():
    from terra_prisca.haze_world.refuge_integration import _Coordinates, _dense_minima

    p = model.Refuge(warm_fraction=.05, dispersal_yr=.001)
    physical = np.array([30., .001, 0., .001, 30., .001, .001, .001, .195])
    coordinates = _Coordinates(physical, p)
    accepted_start = coordinates.encode(physical)

    class Dense:
        t_old, t, h = 1030., 1030. + 7.4432294e-6, 7.4432294e-6

        def __init__(self, allocation):
            self.yh = np.zeros((9, 3))
            self.yh[:, 0] = accepted_start
            self.yh[6, :len(allocation)] = allocation

        def __call__(self, time):
            return np.polynomial.polynomial.polyval((time-self.t)/self.h, self.yh.T)

    dense = Dense([7.07087986e-9, 7.07087996e-9])
    assert dense(dense.t_old)[6] < 0
    minima, at = _dense_minima(dense, dense.t_old, dense.t, coordinates, accepted_start)
    assert np.isneginf(minima[0, 1]) and at[0, 1] == dense.t_old
    assert np.isfinite(minima[1, 1])

    accepted_start[6] = .1
    dense = Dense([.1, .8, .8])
    with pytest.raises(RuntimeError, match="Accepted dense allocation left the physical interval"):
        _dense_minima(dense, dense.t_old, dense.t, coordinates, accepted_start)
