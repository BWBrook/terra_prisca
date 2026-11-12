import numpy as np
import pytest

from terra_prisca.haze_world import graded_spread as spread


def test_zero_spread_recovers_reference_homogeneous_margin():
    result = spread.solve_sigma(0., .001)
    assert result['status'] == 'homogeneous_control'
    assert abs(result['Sc']) < 1e-7
    assert result['lag']['tau_c'] == pytest.approx(1.102760078, rel=1e-6)
    assert result['per_cell_balance_residual_yr'] < 1e-8


def test_normalised_habitat_labels_and_weights_survive_continuation():
    previous = spread._starting_state(.001)
    y, p = spread._target_seed(previous, 1.)
    previous = spread._saved_state(y, p)
    next_y, next_p = spread._target_seed(previous, 3.)
    np.testing.assert_allclose(next_p.offsets, 3 * p.offsets)
    np.testing.assert_array_equal(next_p.weights, p.weights)
    np.testing.assert_array_equal(next_y, y)
    with pytest.raises(ValueError, match='lower dial'):
        spread._target_seed(previous, .5)


def test_failed_numerical_correction_does_not_assert_a_fold(monkeypatch):
    previous = spread._starting_state(.001)
    monkeypatch.setattr(spread.model, 'equilibrium', lambda *args, **kwargs: None)
    history = []
    assert spread._advance(previous, .1, history, max_depth=2) is None
    assert len(history) == 3
    assert not any(r['correction_accepted'] for r in history)


def test_previous_doubling_does_not_force_mesh_growth_at_each_dial():
    initial = spread._starting_state(.001)
    mesh = spread.model.gauss_mesh(1., np.linspace(-1., 1., 9))
    p = spread.parameters(1., .001, mesh)
    y = np.r_[np.tile(initial['y'][:4], p.n), initial['y'][-1]]
    previous = dict(spread._saved_state(y, p), status='converged')
    seed, target = spread._target_seed(previous, 3.)
    assert p.n == 32 and target.n == 16
    assert seed.shape == (target.state_size,)
    assert sum(target.weights) == pytest.approx(1.)
    np.testing.assert_allclose(seed[:-1].reshape(target.n, 4), np.tile(initial['y'][:4], target.n).reshape(target.n, 4))


def test_resolved_sigma_one_endpoint_reproduces_previous_continuum_result():
    result = spread.solve_sigma(1., .001)
    assert result['status'] == 'converged'
    assert result['Sc'] == pytest.approx(-2.91158279596, rel=.002)
    assert result['lag']['tau_c'] == pytest.approx(842.24079853, rel=.002)
    assert result['doubling_history'][-1]['slopes_agree']
    assert result['doubling_history'][-1]['lag_agrees']
    assert result['gain']['frozen_fd_agrees']
    assert result['per_cell_balance_residual_yr'] < 1e-8
