from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import finite_populations as finite


def toy_model(monkeypatch, growth):
    growth = np.asarray(growth, dtype=float)
    monkeypatch.setattr(finite.core, "rhs", lambda y, p: np.r_[0., y[1:3] * growth, 0., 0.])
    monkeypatch.setattr(finite.core, "fluxes", lambda y, p: {"net_growth_yr": growth})
    return replace(finite.core.reference(), habitat_l_cm2=1.)


def process(**kwargs):
    return finite.CellProcess(cell_mass_gdw=1., surface_cm2=1., census_yr=1., **kwargs)


def test_census_removes_exact_mass_and_absence_is_permanent_without_immigration(monkeypatch):
    p = toy_model(monkeypatch, [-np.log(2.), 0.])
    result = finite.integrate_finite([30., 8., 0., 0., .19], p, 3.,
                                   process(minimum_cells=3.), sample_every_censuses=1)
    assert result.first_extinction_yr == 2.
    assert result.first_extinction_by_guild_yr == (2., None)
    assert len(result.extinction_events) == 1
    event = result.extinction_events[0]
    assert event["removed_cells"] == pytest.approx(2., rel=2e-6)
    assert event["removed_gdw"] == pytest.approx(2., rel=2e-6)
    assert event["removed_h2_mol"] == pytest.approx(2. * finite.core.ASSIMILATION_A, rel=2e-6)
    assert np.array_equal(result.census_activity, [1, 1, 0, 0])
    assert np.all(result.y[1, result.t >= 2] == 0)
    assert result.metadata["solver_resets"] == 1
    assert result.arrival_events == []


def test_immigration_recolonizes_zero_and_uses_a_mean_mass_import(monkeypatch):
    growth = np.log(4.)
    p = toy_model(monkeypatch, [growth, 0.])
    result = finite.integrate_finite([30., 0., 0., 0., .19], p, 2.,
                                   process(minimum_cells=3., immigration_cells_yr=(2., 0.)),
                                   sample_every_censuses=1)
    expected = 2. / growth * (np.exp(growth * result.t) - 1)
    assert result.y[1] == pytest.approx(expected, rel=2e-6)
    assert result.arrival_events[0]["time_yr"] == 1.
    assert result.arrival_events[0]["retained_cells"] == pytest.approx(expected[1], rel=2e-6)
    assert result.first_extinction_yr is None
    assert result.ledger["immigrant_cells"] == pytest.approx([4., 0.])
    assert result.ledger["immigrant_h2_mol"][0] == pytest.approx(4. * finite.core.ASSIMILATION_A)
    assert result.metadata["solver_resets"] == 0


def test_repeated_culls_export_the_continuous_immigrant_input(monkeypatch):
    p = toy_model(monkeypatch, [0., 0.])
    result = finite.integrate_finite([30., 0., 0., 0., .19], p, 3.,
                                   process(minimum_cells=3., immigration_cells_yr=(2., 0.)),
                                   sample_every_censuses=1)
    assert len(result.extinction_events) == 3
    assert result.metadata["solver_resets"] == 3
    assert result.ledger["culled_cells"] == pytest.approx(result.ledger["immigrant_cells"])
    assert result.ledger["culled_gdw"] == pytest.approx(result.ledger["immigrant_gdw"])
    assert result.ledger["culled_h2_mol"] == pytest.approx(result.ledger["immigrant_h2_mol"])
    assert np.all(result.y[1] == 0)
    assert result.arrival_events == []


def test_initial_floor_and_partial_interval_are_explicit(monkeypatch):
    p = toy_model(monkeypatch, [0., 0.])
    result = finite.integrate_finite([30., .5, 1., 0., .19], p, .5,
                                   process(minimum_cells=1.), sample_every_censuses=100)
    assert result.first_extinction_by_guild_yr == (0., None)
    assert result.extinction_events[0]["reason"] == "initial_below_floor"
    assert np.array_equal(result.t, [0., .5])
    assert len(result.census_activity) == 1
    assert result.y[1, -1] == 0 and result.y[2, -1] == pytest.approx(1.)
    assert result.metadata["n_censuses"] == 1


def test_no_culls_preserve_the_continuum_model_and_keep_solver_history():
    p = finite.core.reference()
    target = next(e for e in finite.core.equilibrium_states(p) if e["kind"] == "mixed")
    y0 = target["y"] * [1.01, 1.001, .999, 1.002, 1.00001]
    ordinary = finite.core.integrate(y0, p, 30.)
    sampled = finite.integrate_finite(y0, p, 30., finite.CellProcess(minimum_cells=0, census_yr=1),
                                    sample_every_censuses=7)
    assert sampled.y[:, -1] == pytest.approx(ordinary.y[:, -1], rel=3e-6, abs=1e-9)
    assert sampled.metadata["solver_resets"] == 0
    assert sampled.metadata["n_censuses"] == 31
    assert sampled.t[-1] == 30.
    assert len(sampled.t) == 6


def test_reference_invasion_hits_the_first_scheduled_census_after_one_cell():
    p = finite.core.reference()
    control = next(e for e in finite.core.equilibrium_states(replace(p, enabled=(False, True)))
                   if e["kind"] == "methanogen" and e["stable"])
    y0 = control["y"].copy()
    y0[1] = 1e-12
    result = finite.integrate_finite(y0, p, 30., finite.CellProcess(census_yr=1),
                                   sample_every_censuses=1)
    assert result.first_extinction_by_guild_yr == (None, 19.)
    assert result.extinction_events[0]["removed_cells"] < 1
    assert np.all(result.y[2, result.t >= 19.] == 0)
    assert result.ledger["culled_h2_mol"][1] > 0
    assert result.ledger["immigrant_gdw"].sum() == 0


def test_invalid_process_and_disabled_immigration_are_rejected():
    with pytest.raises(ValueError):
        finite.CellProcess(census_yr=0)
    with pytest.raises(ValueError):
        finite.CellProcess(immigration_cells_yr=(-1., 0.))
    p = replace(finite.core.reference(), enabled=(True, False))
    with pytest.raises(ValueError, match="Disabled"):
        finite.integrate_finite([30., .001, 0., 0., .19], p, 1.,
                                finite.CellProcess(immigration_cells_yr=(0., 1.)))
