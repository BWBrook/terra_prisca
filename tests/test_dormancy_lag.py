import itertools

import numpy as np
import pytest

from terra_prisca.haze_world import dormancy
from terra_prisca.haze_world import dormancy_lag as lag


@pytest.fixture(scope='module')
def data():
    base, state = lag.mixed_reference()
    return lag.coefficients(base, state)


def test_linear_directional_derivative_is_not_an_ordinary_jacobian(data):
    direction = np.array([1., 0., 0., 0., 0., 0., 0.])
    forward = lag.directional_derivative(data, direction, .01)
    backward = lag.directional_derivative(data, -direction, .01)
    assert np.linalg.norm((forward+backward)[lag.BANK]) > .1
    cubic = (lag.directional_derivative(data, direction, .01, ramp='cubic')
             + lag.directional_derivative(data, -direction, .01, ramp='cubic'))
    assert cubic == pytest.approx(np.zeros(7), abs=1e-12)


@pytest.mark.parametrize('entering', list(itertools.product((False, True), repeat=2)))
def test_linear_sector_matches_physical_one_sided_derivative(data, entering):
    gradient = data['net_gradient'][:, [0, 4]]
    target = np.array([-1. if value else 1. for value in entering])
    active_direction = np.zeros(5)
    active_direction[[0, 4]] = np.linalg.solve(gradient, target)
    direction = np.zeros(7)
    direction[lag.ACTIVE] = active_direction
    physical, scales = lag.scaled_physical_state(data)
    parameters = lag.dormancy_parameters(data['base'], .01)
    original = dormancy.rhs(physical, parameters)/scales
    expected = lag.directional_derivative(data, direction, .01)
    step = 1e-6
    actual = (dormancy.rhs(physical+step*direction*scales, parameters)/scales-original)/step
    assert actual == pytest.approx(expected, rel=2e-4, abs=2e-6)


def test_epsilon_only_changes_two_real_bank_modes(data):
    for entering in itertools.product((False, True), repeat=2):
        matrices = [lag.sector_matrix(data, epsilon, entering) for epsilon in (1e-4, .1)]
        assert matrices[0][np.ix_(lag.ACTIVE, lag.ACTIVE)] == pytest.approx(matrices[1][np.ix_(lag.ACTIVE, lag.ACTIVE)])
        assert matrices[0][np.ix_(lag.ACTIVE, lag.BANK)] == pytest.approx(np.zeros((5, 2)))
        for epsilon, matrix in zip((1e-4, .1), matrices):
            assert np.diag(matrix)[lag.BANK] == pytest.approx(np.full(2, -epsilon*.001*lag.core.HOURS_PER_YEAR))
            active = np.linalg.eigvals(matrix[np.ix_(lag.ACTIVE, lag.ACTIVE)])
            complete = np.linalg.eigvals(matrix)
            expected = np.r_[active, [-epsilon*.001*lag.core.HOURS_PER_YEAR]*2]
            for value in expected:
                assert min(abs(complete-value)) < 1e-8


def test_cubic_is_reference_active_matrix_plus_bank_decay(data):
    matrix = lag.sector_matrix(data, .01, ramp='cubic')
    assert matrix[np.ix_(lag.ACTIVE, lag.ACTIVE)] == pytest.approx(data['jacobian'])
    assert matrix[np.ix_(lag.BANK, lag.ACTIVE)] == pytest.approx(np.zeros((2, 5)))
    assert 1/(.01*.001*lag.core.HOURS_PER_YEAR) == pytest.approx(11.407711613050423)

