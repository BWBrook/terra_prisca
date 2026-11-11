from types import SimpleNamespace

import numpy as np
import pytest
from numpy.polynomial import Polynomial

from terra_prisca.haze_world.dense_roots import exit_time, real_roots


def test_near_linear_root_is_scaled_and_residual_checked(monkeypatch):
    polynomial = Polynomial([.19499999999999987 - .1063948354764292,
                             .1405208862739409, -5.34291591203601e-18])
    expected = -polynomial.coef[0] / polynomial.coef[1]
    assert real_roots(polynomial, -1., 0.) == pytest.approx([expected], abs=1e-12)
    monkeypatch.setattr(Polynomial, "roots", lambda self: np.array([0.]))
    roots = real_roots(polynomial, -1., 0.)
    assert roots == pytest.approx([expected], abs=1e-12)
    assert abs(polynomial(roots[0])) < 1e-14


def test_bounded_roots_include_a_tangency_and_omit_external_roots():
    polynomial = Polynomial.fromroots([-2., -.5, -.5, .4, 3.])
    roots = real_roots(polynomial, -1., 1.)
    assert min(abs(np.asarray(roots) + .5)) < 1e-7
    assert min(abs(np.asarray(roots) - .4)) < 1e-10
    assert all(-1 <= value <= 1 and abs(polynomial(value)) < 1e-12 for value in roots)


def test_root_scaling_uses_requested_interval():
    polynomial = Polynomial([1., -2e-8, 1e-16])
    roots = real_roots(polynomial, 0., 2e8)
    assert roots == pytest.approx([1e8], rel=1e-7)


def test_domain_exit_backcheck_rejects_missing_root(monkeypatch):
    from terra_prisca.haze_world import dense_roots
    dense = SimpleNamespace(t=1., h=1., yh=np.array([[2.1, 2.]]))
    monkeypatch.setattr(dense_roots, "real_roots", lambda *args: [])
    with pytest.raises(RuntimeError, match="validated boundary"):
        exit_time(dense, 0., 1., [0., .5], 0)
