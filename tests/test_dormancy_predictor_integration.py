from dataclasses import replace

import numpy as np
import pytest
from scipy.integrate._ivp.radau import RadauDenseOutput

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_predictor_integration as numerical
from terra_prisca.haze_world import habitat_coupling as habitat

upstream = numerical.upstream
conditioned = numerical.conditioned


def setup():
    p = model.Dormancy(habitat.Habitats(), epsilon=.03)
    y = model.reference_state([30., 3e-4, 4e-4, 1e-4, .195], p)
    coords = numerical._Coordinates(y, p)
    state = coords.encode(y)
    coords.stage_positive[5] = True
    state[5] = .2
    state[4] = numerical.TINY_LINEAR_ALLOCATION_CAP/2
    return p, y, coords, state


def native(coords, state):
    return numerical._NativeRadau(lambda t, y: np.zeros_like(y), 0., state, 1.,
        coordinates=coords, rtol=2e-8, atol=1e-12, max_step=1., first_step=.01,
        jac=np.zeros((len(state), len(state))))


def backend(coords, state):
    atol = np.r_[[1e-7, 1e-12, 1e-12, 1e-8, 1e-14, 1e-12, 1e-11],
                  np.full(len(coords.groups), 1e-8)]
    return numerical._Radau(coords.derivative, 0., state, 1., nominal_max_step=1.,
        events=[], progress_events=[], max_step=1., first_step=1e-6, rtol=2e-8, atol=atol)


@pytest.mark.parametrize('outcome', ['success', 'failure', 'exception'])
def test_only_sol_changes_and_failure_or_exception_restores_prior_dense(monkeypatch, outcome):
    p, y, coords, state = setup()
    instance = native(coords, state)
    previous, new = object(), object()
    instance.sol = previous
    instance.h_abs_old = .3
    instance.error_norm_old = .012
    instance.LU_real, instance.LU_complex = object(), object()
    before = dict(y=instance.y.tobytes(), t=instance.t, h_abs=instance.h_abs,
                  h_abs_old=instance.h_abs_old, error_norm_old=instance.error_norm_old,
                  J=instance.J, LU_real=instance.LU_real, LU_complex=instance.LU_complex)
    def step(self):
        assert self.sol is None
        assert self.y.tobytes() == before['y'] and self.t == before['t']
        for key in ('h_abs','h_abs_old','error_norm_old'):
            assert getattr(self,key) == before[key]
        for key in ('J','LU_real','LU_complex'):
            assert getattr(self,key) is before[key]
        self.sol = new
        if outcome == 'exception':
            raise RuntimeError('injected native exception')
        return outcome == 'success', 'native message'
    monkeypatch.setattr(numerical.Radau, '_step_impl', step)
    if outcome == 'exception':
        with pytest.raises(RuntimeError, match='native exception'):
            instance._step_impl()
    else:
        assert instance._step_impl() == (outcome == 'success', 'native message')
    assert instance.sol is (new if outcome == 'success' else previous)
    assert instance.y.tobytes() == before['y'] and instance.t == before['t']
    stats = coords.zero_stage_predictor_stats
    assert stats['prior_dense_predictors_suppressed'] == 1
    assert stats['restored_prior_dense_on_failure'] == int(outcome != 'success')
    assert stats['native_exceptions'] == int(outcome == 'exception')


@pytest.mark.parametrize('kind', ['absent','negative','root','above_cap'])
def test_predicate_exclusions_preserve_original_guess(monkeypatch, kind):
    p, y, coords, state = setup()
    if kind == 'absent':
        coords.groups[0]['present'] = False
    elif kind == 'negative':
        state[4] = -1e-30
    elif kind == 'root':
        coords.stage_positive[4] = True
    else:
        state[4] = np.nextafter(numerical.TINY_LINEAR_ALLOCATION_CAP, np.inf)
    assert not numerical._tiny_linear_indices(state, coords)
    instance = native(coords, state)
    previous = object()
    instance.sol = previous
    def step(self):
        assert self.sol is previous
        return False, 'test failure'
    monkeypatch.setattr(numerical.Radau, '_step_impl', step)
    assert instance._step_impl()[0] is False and instance.sol is previous
    assert coords.zero_stage_predictor_stats['tiny_linear_step_calls'] == 0


@pytest.mark.parametrize('value', [0., 1e-40, conditioned.LINEAR_ALLOCATION_CAP])
def test_present_linear_predicate_includes_exact_boundaries_without_modifying_stock(value):
    p, y, coords, state = setup()
    state[4] = value
    before = state.tobytes()
    assert numerical._tiny_linear_indices(state, coords) == [4]
    assert state.tobytes() == before


def test_real_native_success_keeps_new_dense_output():
    p, y, coords, state = setup()
    instance = native(coords, state)
    old = object()
    instance.sol = old
    assert instance._step_impl()[0]
    assert instance.sol is not None and instance.sol is not old
    assert instance.sol(instance.t).tobytes() == instance.y.tobytes()


def test_mro_preserves_conditioned_root_request_before_native_construction(monkeypatch):
    p, y, coords, state = setup()
    coords.stage_positive[4] = True
    state[4] = 1e-20
    monkeypatch.setattr(numerical, '_NativeRadau', lambda *args, **kwargs: pytest.fail('Native constructor reached'))
    instance = backend(coords, state)
    assert numerical._Radau._step_impl is conditioned._Radau._step_impl
    order = numerical._Radau.__mro__
    assert order.index(conditioned._Radau) < order.index(numerical._InjectedNative) < order.index(upstream._Radau)
    assert numerical._Radau._dense_output_impl is upstream._Radau._dense_output_impl
    with pytest.raises(numerical.stage._StageSourceOverflow):
        instance._step_impl()
    assert instance._radau is None and instance.y.tobytes() == state.tobytes()
    assert coords.tolerance_conditioning_requests[0]['immutable_accepted_snapshot']


def test_constructor_injection_does_not_mutate_globals_and_failed_state_is_not_adopted(monkeypatch):
    p, y, coords, state = setup()
    original_native = numerical._NativeRadau
    original_scipy = upstream._Radau._step_impl.__globals__['Radau']
    original_eps, original_unit = upstream._EPS, upstream._UNIT
    class Fail(original_native):
        def _step_impl(self):
            self.fun(self.t+.001, self.y)
            self.y = self.y*1.01
            self.t += .001
            return False, 'native failure'
    monkeypatch.setattr(numerical, '_NativeRadau', Fail)
    instance = backend(coords, state)
    instance.step()
    assert instance.status == 'failed' and instance.t == 0.
    assert instance.y.tobytes() == state.tobytes()
    assert instance.nfev == coords.radau_work['rhs_evaluations'] > 0
    assert upstream._Radau._step_impl.__globals__['Radau'] is original_scipy
    assert upstream._EPS is original_eps and upstream._UNIT is original_unit


class FakeNative:
    def __init__(self, fun, time, state, bound, *, coordinates, **options):
        self.t = time
        self.y = state.copy()
        self.bound = bound
        self.nfev = self.njev = self.nlu = 0
        self.sol = None
    def _step_impl(self):
        old = self.y.copy()
        left = self.t
        self.t = min(self.bound, left+1.)
        Q = np.zeros((len(old), 3))
        Q[0, 0] = -32.
        Q[6, 0] = -.25
        Q[4] = [-.5e-50, 1e-50, 0.]
        self.y = old+Q.sum(axis=1)
        self.sol = RadauDenseOutput(left, self.t, old, Q)
        return True, None


def test_domain_prefix_and_strict_dense_certificate_remain_composed(monkeypatch):
    monkeypatch.setattr(numerical, '_NativeRadau', FakeNative)
    p, y, coords, state = setup()
    y[-1] = .125
    result = numerical.integrate(y, p, 1., max_step=1.)
    assert result.status == 'domain_exit' and result.t[-1] == pytest.approx(.5)
    assert result.y[-1, -1] == 0. and result.y[0, -1] == pytest.approx(14.)
    stats = result.metadata['positive_dense_stats'][0]
    assert stats['negative_native_endpoint_pieces'] == 1 and stats['negative_native_endpoint_rejections'] == 0
    assert stats['extended_pieces'] == 1
    for event in stats['extensions']:
        assert 'terminal_macro_certificate' not in event
        for component in event['components']:
            assert component['epsilon_squared'] == float(upstream._EPS**2)
            assert 'root_atol_squared_budget' not in component
    assert 'terminal_dense_stats' not in result.metadata and np.all(result.y >= 0.)


def test_census_ledger_and_stock_preserving_conditioning_are_retained():
    base = habitat.Habitats(patches=(habitat.Patch('bulk', 1., 'buffered', 286.),))
    p = model.Dormancy(base, epsilon=.03)
    process = numerical.Census(census_yr=.5)
    conversion = p.coupled.habitat_l_cm2*process.surface_cm2/process.cell_mass_gdw
    y = model.reference_state([21., 2./conversion, 4e-4, 1e-4, .195], p)
    result = numerical.integrate_finite(y, p, 4., process, sample_every_censuses=1, max_step=.5)
    assert result.status == 'completed' and result.extinction_events
    assert result.ledger['inventory_jump_h2_mol_l'].sum() == sum(
        event['inventory_jump_h2_mol_l'] for event in result.extinction_events)
    assert np.array_equal(result.census_times, np.arange(0., 4.1, .5)) and np.all(result.y >= 0.)
    assert all(event['physical_state_bitwise_preserved'] and event['total_coordinates_bitwise_preserved']
               for event in result.metadata['stage_conditioning_events'])


def test_rare_retained_logs_and_absence_remain_distinct():
    p, y, coords, state = setup()
    p = replace(p, switching_factor=0.)
    y[1] = 0.
    y[2] = np.nextafter(0., 1.)
    result = numerical.integrate_finite(y, p, .1, numerical.Census(minimum_cells=0., census_yr=.01),
                                       sample_every_censuses=1, max_step=.01)
    assert result.status == 'completed' and np.all(result.y[1] == 0.)
    assert np.all(np.isneginf(result.log_biomass[:, 0])) and np.all(np.isfinite(result.log_biomass[:, 1]))
    assert result.global_continuous_min_log_biomass[1] < -740
    assert result.metadata['numerical_variant'] == 'radau_dormancy_zero_stage_predictor'
    assert 'terminal_dense_stats' not in result.metadata


def test_ordinary_physical_flow_and_rhs_match_conditioned_parent():
    p, y, coords, state = setup()
    frozen = conditioned._Coordinates(y, p)
    original = frozen.encode(y)
    actual = coords.encode(y)
    assert coords.derivative(0., actual).tobytes() == frozen.derivative(0., original).tobytes()
    process = numerical.Census(minimum_cells=0., census_yr=.01)
    result = numerical.integrate_finite(y, p, .1, process, sample_every_censuses=1, max_step=.01)
    reference = conditioned.integrate_finite(y, p, .1, process, sample_every_censuses=1, max_step=.01)
    assert result.status == reference.status == 'completed'
    assert np.allclose(result.y, reference.y, rtol=2e-6, atol=2e-11)
    assert max(abs(model.redox_residual(v, p)) for v in result.y.T) < 1e-16
    assert numerical._Radau._dense_output_impl.__globals__['_Dense'] is upstream._Dense
