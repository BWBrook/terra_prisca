import ast
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import inspect
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.integrate import Radau as ScipyRadau
from scipy.integrate._ivp.radau import RadauDenseOutput

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_conditioned_integration as numerical
from terra_prisca.haze_world import dormancy_radau_integration as upstream
from terra_prisca.haze_world import habitat_coupling as habitat


def setup(shared=False):
    base = habitat.Habitats() if not shared else habitat.Habitats(
        patches=(habitat.Patch('bulk', .96), habitat.Patch('warm', .02, 'buffered', 286.),
                 habitat.Patch('cold', .02, 'buffered', 278.)), dispersal_yr=.001)
    p = model.Dormancy(base, epsilon=.03)
    initial = [30., 3e-4, 4e-4, 1e-4, .195]
    y = model.reference_state(initial if not shared else habitat.embed_single(initial, base), p)
    coords = numerical._Coordinates(y, p)
    state = coords.encode(y)
    return p, y, coords, state


def backend(coords, state, bound=1.):
    atol = np.r_[np.tile([1e-7, 1e-14, 1e-14, 1e-8, 1e-14, 1e-14], coords.p.n_patches),
                  1e-11, np.full(len(coords.groups), 1e-8)]
    atol[:coords.m][coords.stage_positive] = numerical.ROOT_ABSOLUTE_TOLERANCE
    return numerical._Radau(coords.derivative, 0., state, bound, nominal_max_step=1.,
        events=[], progress_events=[], max_step=1., first_step=1e-6, rtol=2e-8, atol=atol)


@pytest.mark.parametrize('shared', [False, True])
def test_physical_rhs_and_ordinary_newton_matrix_are_bitwise_unchanged(shared):
    p, y, coords, state = setup(shared)
    frozen = upstream._Coordinates(y, p)
    original = frozen.encode(y)
    assert state.tobytes() == original.tobytes()
    assert coords.derivative(0., state).tobytes() == frozen.derivative(0., original).tobytes()
    for group in coords.groups:
        for index in group['indices']:
            coords.stage_positive[index] = True
            frozen.stage_positive[index] = True
            state[index] = .2
    original = state.copy()
    expected = upstream.face.coordinate_jacobian(0., original, frozen)
    actual = backend(coords, state)._chemical_jacobian(0., state)
    assert actual.tobytes() == expected.tobytes()
    assert coords.tolerance_conditioning_stats['face_visits'] == 0
    assert coords.derivative(0., state).tobytes() == frozen.derivative(0., original).tobytes()


@pytest.mark.parametrize('root', [0., 1e-20, -1e-20, numerical.ROOT_ABSOLUTE_TOLERANCE])
@pytest.mark.parametrize('index', [1, 4, 8, 11])
def test_existing_chart_map_preserves_every_decoded_stock_and_total_bit(root, index):
    p, y, coords, state = setup(True)
    coords.stage_positive[index] = True
    state[index] = root
    before = coords.decode(state)[0].copy()
    total = state[coords.m:].copy()
    global_before = coords.global_logs(state).copy()
    event = coords.condition_stage(state, 2., index, 'test_accepted_map')
    assert coords.decode(state)[0].tobytes() == before.tobytes()
    assert state[coords.m:].tobytes() == total.tobytes()
    assert coords.global_logs(state).tobytes() == global_before.tobytes()
    assert event['physical_state_bitwise_preserved'] and event['total_coordinates_bitwise_preserved']
    assert event['global_guild_logs_bitwise_preserved']


def gate_state(monkeypatch):
    p, y, coords, state = setup()
    state[4] = numerical.LINEAR_ALLOCATION_CAP/2
    coords.stage_positive[5] = True
    state[5] = .2
    flux = dict(net_growth_yr=np.zeros((1, 2)), dormant_loss_yr=0.,
                sigma_yr=np.zeros((1, 2)), rho_yr=np.zeros((1, 2)))
    monkeypatch.setattr(numerical.stage.model, 'fluxes', lambda *args, **kwargs: flux)
    matrix = np.arange(len(state)**2, dtype=float).reshape(len(state), -1)+1.
    return coords, state, flux, matrix


def test_gate_changes_only_selected_offdiagonals_and_calls_no_side_effectful_rhs(monkeypatch):
    coords, state, flux, matrix = gate_state(monkeypatch)
    monkeypatch.setattr(coords, 'derivative', lambda *args: pytest.fail('Derivative has side effects'))
    before = state.tobytes()
    expected = matrix.copy()
    diagonal = matrix[4, 4]
    expected[4, :] = 0.
    expected[:, 4] = 0.
    expected[4, 4] = diagonal
    actual = numerical._condition_matrix(1., state, coords, matrix.copy())
    assert actual.tobytes() == expected.tobytes() and state.tobytes() == before
    stats = coords.tolerance_conditioning_stats
    assert stats['face_visits'] == 1 and stats['faces'][4]['last_retained_diagonal'] == diagonal
    assert stats['faces'][4]['last_pure_linear_rate_yr'] == 0.


@pytest.mark.parametrize('reason', ['absent', 'negative', 'root', 'above_allocation', 'above_source'])
def test_gate_rejects_every_out_of_scope_coordinate(monkeypatch, reason):
    coords, state, flux, matrix = gate_state(monkeypatch)
    if reason == 'absent':
        coords.groups[0]['present'] = False
    elif reason == 'negative':
        state[4] = -numerical.LINEAR_ALLOCATION_CAP/2
    elif reason == 'root':
        coords.stage_positive[4] = True
    elif reason == 'above_allocation':
        state[4] = 2*numerical.LINEAR_ALLOCATION_CAP
    else:
        flux['sigma_yr'][0, 0] = 2*numerical.LINEAR_RATE_CAP_YR
    actual = numerical._condition_matrix(1., state, coords, matrix.copy())
    assert actual.tobytes() == matrix.tobytes()
    assert coords.tolerance_conditioning_stats['face_visits'] == 0


def test_gate_includes_exact_cap_and_original_own_diagonal(monkeypatch):
    coords, state, flux, matrix = gate_state(monkeypatch)
    state[4] = numerical.LINEAR_ALLOCATION_CAP
    flux['sigma_yr'][0, 0] = numerical.LINEAR_RATE_CAP_YR
    actual = numerical._condition_matrix(0., state, coords, matrix.copy())
    assert coords.tolerance_conditioning_stats['face_visits'] == 1
    assert actual[4, 4] == matrix[4, 4]
    assert np.count_nonzero(actual[4]) == np.count_nonzero(actual[:, 4]) == 1
    assert numerical.LINEAR_ALLOCATION_CAP == numerical.ROOT_ABSOLUTE_TOLERANCE**2
    assert numerical.LINEAR_RATE_CAP_YR == numerical.LINEAR_ALLOCATION_CAP/10.


def test_only_one_verified_ast_predicate_is_changed():
    function, provenance = numerical._conditioned_driver(numerical.stage._accepted_integrate)
    original = ast.parse(inspect.getsource(numerical.stage._accepted_integrate))
    expected = deepcopy(original)
    target = numerical._promotion_target(expected)[0]
    target.test = ast.BoolOp(op=ast.And(), values=[target.test,
        ast.Call(func=ast.Name(id='_promotion_allowed', ctx=ast.Load()),
                 args=[ast.Name(id=name, ctx=ast.Load()) for name in ('coords','accepted','index','end')], keywords=[])])
    expected_hash = sha256(ast.dump(expected, include_attributes=False).encode()).hexdigest()
    assert provenance['conditioned_ast_sha256'] == expected_hash
    assert provenance['target_count'] == 1 and provenance['restored_ast_identical']
    assert function.__code__.co_filename == '<dormancy_tolerance_conditioned_driver>'
    assert function.__globals__['_promotion_allowed'] is numerical._promotion_allowed


def no_target():
    return None


def two_targets():
    if True:
        stage_promotions.append(index)
    if False:
        stage_promotions.append(index)


@pytest.mark.parametrize('function', [no_target, two_targets])
def test_driver_transform_rejects_upstream_shape_drift(function):
    with pytest.raises(RuntimeError, match='exactly one'):
        numerical._conditioned_driver(function)


def test_promotion_cap_does_not_modify_a_stock():
    p, y, coords, state = setup()
    for value, allowed in [(0., False), (numerical.LINEAR_ALLOCATION_CAP, False),
                           (2*numerical.LINEAR_ALLOCATION_CAP, True)]:
        state[4] = value
        before = state.tobytes()
        assert numerical._promotion_allowed(coords, state, 4, 1.) == allowed
        assert state.tobytes() == before


def test_small_root_request_uses_immutable_accepted_state_before_any_native_work():
    p, y, coords, state = setup()
    coords.stage_positive[4] = True
    state[4] = 1e-20
    instance = backend(coords, state)
    before = instance.y.tobytes()
    with pytest.raises(numerical.stage._StageSourceOverflow) as raised:
        instance._step_impl()
    assert instance.t == 0. and instance.y.tobytes() == before and instance._radau is None
    request = raised.value.stage_cause
    assert request['immutable_accepted_snapshot']
    assert request['accepted_coordinate_sha256'] == sha256(state.tobytes()).hexdigest()
    assert coords.radau_work['constructors'] == coords.radau_work['rhs_evaluations'] == 0
    event = coords.condition_stage(state, 0., raised.value.index, 'native_step', raised.value)
    assert event['physical_state_bitwise_preserved'] and event['total_coordinates_bitwise_preserved']


def test_trial_roots_never_trigger_accepted_chart_conditioning(monkeypatch):
    class Trial:
        def __init__(self, fun, time, state, bound, **kwargs):
            self.t = time
            self.y = state.copy()
            self.nfev = self.njev = self.nlu = 0
        def _step_impl(self):
            self.y[1] = 1e-30
            self.t += .1
            raise RuntimeError('native trial error')
    monkeypatch.setattr(upstream, 'Radau', Trial)
    p, y, coords, state = setup()
    instance = backend(coords, state)
    with pytest.raises(RuntimeError, match='native trial error'):
        instance._step_impl()
    assert not coords.tolerance_conditioning_requests
    assert instance.y.tobytes() == state.tobytes() and instance.t == 0.


def test_negative_native_endpoint_is_still_rejected_in_composed_driver(monkeypatch):
    fired = []
    class NegativeOnce(ScipyRadau):
        def _step_impl(self):
            result = super()._step_impl()
            if result[0] and not fired:
                fired.append(True)
                self.y[4] = -1e-50
            return result
    monkeypatch.setattr(upstream, 'Radau', NegativeOnce)
    p, y, coords, state = setup()
    result = numerical.integrate_finite(y, p, .01, numerical.Census(minimum_cells=0., census_yr=.001),
                                       sample_every_censuses=1, max_step=.001)
    assert result.status == 'completed' and result.metadata['allocation_positivity_retries'] >= 1
    stats = result.metadata['positive_dense_stats'][0]
    assert stats['negative_native_endpoint_rejections'] >= 1 and np.all(result.y >= 0.)


def test_census_ledger_and_rare_log_stock_remain_distinct_from_absence():
    p, y, coords, state = setup()
    p = replace(p, switching_factor=0.)
    y[1] = 0.
    y[2] = np.nextafter(0., 1.)
    result = numerical.integrate_finite(y, p, .1, numerical.Census(minimum_cells=0., census_yr=.01),
                                       sample_every_censuses=1, max_step=.01)
    assert result.status == 'completed' and np.all(result.y[1] == 0.)
    assert np.all(np.isneginf(result.log_biomass[:, 0])) and np.all(np.isfinite(result.log_biomass[:, 1]))
    assert result.global_continuous_min_log_biomass[1] < -740
    assert result.metadata['numerical_variant'] == 'radau_dormancy_tolerance_conditioning'
    assert result.metadata['tolerance_conditioning_ast']['target_count'] == 1
    assert 'radau_work' in result.metadata and 'positive_dense_stats' in result.metadata
    assert not result.extinction_events and not np.any(result.ledger['culled_cells'])


def test_census_removal_and_inventory_jump_are_preserved():
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
