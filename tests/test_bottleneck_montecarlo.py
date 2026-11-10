from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pytest


spec = spec_from_file_location("bottleneck_montecarlo", Path(__file__).resolve().parents[1] /
                              "models/haze_world/review/check_bottleneck_montecarlo.py")
mc = module_from_spec(spec)
spec.loader.exec_module(mc)


def test_exact_step_limits_and_mean():
    assert mc.transition_parameters(0, 1, 50)[0] == pytest.approx(np.exp(-50), rel=1e-14)
    assert mc.transition_parameters(3, 3, 2) == pytest.approx((1 / 7, 1 / 7))
    for birth, death in [(2, 1), (1, 2), (0, 2), (2, 0)]:
        survival, geometric = mc.transition_parameters(birth, death, .7)
        assert survival / geometric == pytest.approx(np.exp((birth - death) * .7))


def test_exact_critical_transition_has_branching_variance():
    counts = np.full((20000, 1), 1000, dtype=np.int64)
    result = mc.birth_death_step(counts, np.array([2.]), np.array([2.]), 1., np.random.default_rng(709))
    assert abs(result.mean() - 1000) < 5 * np.sqrt(4000 / 20000)
    assert result.var() == pytest.approx(4000, rel=.04)


def test_migration_is_row_oriented_and_conservative():
    rates = np.array([[0., .4, .1], [.2, 0., .3], [.7, .1, 0.]])
    matrix = mc.migration_matrix(rates, 2)
    counts = np.tile([500, 0, 0], (10000, 1))
    result = mc.migration_step(counts, matrix, np.random.default_rng(710))
    assert np.array_equal(result.sum(axis=1), counts.sum(axis=1))
    assert np.max(abs(result.mean(axis=0) - 500 * matrix[0])) < .5
