from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import continuum_core as weighted
from terra_prisca.haze_world import dynamic_core as original
from terra_prisca.haze_world import graded_acetate as dial


def seed(fraction=.5):
    p = dial.parameters(0., fraction)
    q = original.DynamicParams(p.base, 'fixed')
    return next(r['y'] for r in original.equilibrium_states(q) if r['kind'] == 'mixed')


@pytest.mark.parametrize('kappa,chemistry', [(0., 'fixed'), (1., 'acetate_only')])
@pytest.mark.parametrize('fraction', [0., .5])
def test_endpoints_recover_existing_flow_matrix_and_response(kappa, chemistry, fraction):
    p = dial.parameters(kappa, fraction)
    q = weighted.WeightedParams(p.base, chemistry)
    old = original.DynamicParams(p.base, chemistry)
    y = next(r['y'] for r in original.equilibrium_states(old) if r['kind'] == 'mixed')
    np.testing.assert_allclose(dial.physical_rhs(y, p), weighted.physical_rhs(y, q), atol=1e-17, rtol=1e-11)
    scale = original.state_scales(y, p)
    actual = weighted.dense_matrix(y, p, blocks=dial.blocks(y, p))*scale[None, :]/scale[:, None]
    expected = weighted.dense_matrix(y, q)*scale[None, :]/scale[:, None]
    np.testing.assert_allclose(actual, expected, atol=3e-9, rtol=1e-8)
    for key in ('Sc', 'S0'):
        assert dial.slopes(y, p)[key] == pytest.approx(weighted.slopes(y, q)[key], rel=1e-7, abs=2e-8)


@pytest.mark.parametrize('kappa', [.0001, .03, .5])
def test_partial_exponent_jacobian_matches_independent_physical_difference(kappa):
    p = dial.parameters(kappa, .5)
    y = np.array([50., 1e-4, 3e-4, 1e-5, .2])
    scale = original.state_scales(y, p)
    matrix = weighted.dense_matrix(y, p, blocks=dial.blocks(y, p))
    numerical = np.zeros((5, 5))
    for j in range(5):
        h = 1e-5*scale[j]
        delta = np.eye(5)[j]*h
        numerical[:, j] = (dial.physical_rhs(y-2*delta, p)-8*dial.physical_rhs(y-delta, p)
                          +8*dial.physical_rhs(y+delta, p)-dial.physical_rhs(y+2*delta, p))/(12*h)
    np.testing.assert_allclose(matrix*scale[None, :]/scale[:, None], numerical*scale[None, :]/scale[:, None],
                               rtol=5e-7, atol=2e-7)


def test_frozen_composition_supply_check_uses_the_same_ratio():
    p = dial.parameters(.01, .5)
    found = dial.equilibrium(seed(), p)
    assert found is not None
    assert max(abs(dial.per_capita(found['y'], p))) < 1e-9
    result = dial.slopes(found['y'], p)
    check = dial.frozen_supply_check(found['y'], p, step=1e-5)
    assert check['status'] == 'passed'
    assert check['S0_finite_difference'] == pytest.approx(result['S0'], rel=2e-5)
    assert max(row['maximum_ratio_error'] for row in check['points']) < 1e-14


def test_partial_exponent_derivative_scales_with_kappa():
    p = dial.parameters(.1, .5)
    y = np.array([50., 1e-4, 3e-4, 1e-5, .2])
    t = original.temperature(y[-1], p)
    threshold = dial.pair(y, t, p)[0].threshold_pa
    h = y[3]*1e-5
    lo, hi = y.copy(), y.copy(); lo[3] -= h; hi[3] += h
    numerical = (dial.pair(hi, t, p)[0].threshold_pa-dial.pair(lo, t, p)[0].threshold_pa)/(2*h)
    assert numerical == pytest.approx(p.kappa*threshold/(4*y[3]), rel=1e-8)


def test_zero_product_has_finite_flow_but_singular_partial_exponent_derivative():
    p = dial.parameters(.1, .5)
    y = np.array([50., 1e-4, 3e-4, 0., .2])
    assert np.all(np.isfinite(dial.physical_rhs(y, p)))
    with pytest.raises(ValueError, match='positive product stock'):
        dial.blocks(y, p)


def test_invalid_dials_and_geometries_are_rejected():
    with pytest.raises(ValueError):
        dial.parameters(-.001, .5)
    with pytest.raises(ValueError):
        replace(dial.parameters(.1, .5), sigma_k=1.)
