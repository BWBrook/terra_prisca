from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import dynamic_realisation as run


def test_lag_status_does_not_invent_infinity_or_margin_for_unstable_state():
    stable = run.lag_spectrum(lambda tau: np.array([[-1/(1+tau)]]))
    assert stable['critical_lag_status'] == 'not_detected_through_10000'
    assert stable['critical_lag_yr'] is None
    assert stable['lambda_real_tau_10000'] < 0
    unstable = run.lag_spectrum(lambda tau: np.array([[1.]]))
    assert unstable['critical_lag_status'] == 'already_unstable'
    assert unstable['critical_lag_yr'] == 0
    crossing = run.lag_spectrum(lambda tau: np.array([[tau-2.]]))
    assert crossing['critical_lag_yr'] == pytest.approx(2.)


def test_gain_is_undefined_on_flat_control_and_not_forced_to_zero():
    p = run.parameters('fixed', .5, .001, .36)
    e = next(r for r in run.model.equilibrium_states(p) if r['kind'] == 'mixed')
    c, controls = run.control_records(p)
    result = run.gain_record(e, p, c, controls)
    assert result['gain_status'] == 'zero_control_slope'
    assert result['gain'] is None
    assert result['community_slope_k'] == pytest.approx(0., abs=1e-8)


def test_fixed_band_includes_abiotic_source_and_endpoints_zero_one_stock():
    p = run.parameters('fixed', .5, .001, .3)
    e = next(r for r in run.model.equilibrium_states(p) if r['kind'] == 'mixed')
    band = run.exact_homogeneous_band(p, e['y'])
    assert band['abiotic_ratio_yr'] > 0
    assert band['lower_potential'] == pytest.approx(.22917760653374644, rel=1e-10)
    assert band['upper_potential'] == pytest.approx(.45732696540265555, rel=1e-10)
    for key, absent in (('lower_potential', 1), ('upper_potential', 2)):
        q = run.parameters('fixed', .5, .001, band[key])
        y = run.model._single_mixture(e['r'], q)
        assert abs(y[absent]) < 1e-12
        assert np.max(abs(run.model.physical_rhs(y, q))) < 1e-6


def test_two_layer_equation_matches_core_and_zero_lag_limit():
    p = run.parameters('products', .5, .001, .3)
    e = next(r for r in run.model.equilibrium_states(p) if r['kind'] == 'mixed')
    builder = run.thermal_builder(e['y'], p, two_layer=True)
    assert np.allclose(builder(0), run.model.reduced_matrix(e['y'], p))
    assert np.allclose(builder(3.), run.model.thermal_matrix(e['y'], p, 3., two_layer=True))
