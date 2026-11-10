from fractions import Fraction
from math import exp, log1p

import numpy as np
import pytest
from scipy.integrate._ivp.radau import RadauDenseOutput

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_terminal_integration as numerical
from terra_prisca.haze_world import habitat_coupling as habitat

upstream = numerical.upstream


def setup(shared=False, both=False):
    base = habitat.Habitats() if not shared else habitat.Habitats(
        patches=(habitat.Patch('bulk', .98), habitat.Patch('warm', .02, 'buffered', 286.)), dispersal_yr=.001)
    p = model.Dormancy(base, epsilon=.03)
    single = [30., 3e-4, 4e-4 if both else 0., 1e-4, .195]
    y = model.reference_state(single if not shared else habitat.embed_single(single, base), p)
    coords = numerical._Coordinates(y, p)
    state = coords.encode(y)
    coords.dense_census = numerical.Census()
    coords.terminal_census_active = True
    atol = np.r_[np.tile([1e-7, 1e-14, 1e-14, 1e-8, 1e-14, 1e-14], p.n_patches),
                  1e-11, np.full(len(coords.groups), 1e-8)]
    atol[:coords.m][coords.stage_positive] = 1e-12
    return p, y, coords, state, atol


def piece(state, amplitude=1e-27):
    Q = np.zeros((len(state), 3))
    Q[4] = [-.5*amplitude, amplitude, 0.]
    return RadauDenseOutput(10., 20., state.copy(), Q), state+Q.sum(axis=1)


def ratio(value):
    return Fraction(int(value['n'], 16), int(value['d'], 16))


def test_broader_budget_has_full_gate_proof_and_true_roundoff_metadata():
    p, y, coords, state, atol = setup()
    native, end = piece(state)
    before = (native.y_old.tobytes(), native.Q.tobytes(), end.tobytes())
    original_eps, original_unit, gamma = upstream._EPS, upstream._UNIT, upstream._gamma(100)
    dense = numerical._Dense(native, end, coords, atol)
    assert dense.repaired == [4]
    assert (native.y_old.tobytes(), native.Q.tobytes(), end.tobytes()) == before
    event = coords.positive_dense_stats['extensions'][0]
    proof = event['terminal_macro_certificate']
    assert ratio(proof['encoded_total_lower_exact']) >= -16
    assert ratio(proof['total_cells_lower_exact']) >= 10**16
    assert proof['active_habitats'] == proof['present_guilds'] == 1
    component = event['components'][0]
    assert component['dense_budget_kind'] == numerical.BUDGET_KIND
    assert 'epsilon_squared' not in component
    assert component['cap'] == component['root_atol_squared_budget'] == 1e-24
    assert component['defect_upper'] > component['machine_epsilon_squared']
    assert component['machine_epsilon_squared'] == float(original_eps**2)
    assert event['bound_inputs']['unit_roundoff'] == float(original_unit)
    assert upstream._EPS == original_eps and upstream._UNIT == original_unit and upstream._gamma(100) == gamma
    assert numerical._CHANGED_GLOBALS == ('_EPS',)
    assert numerical._CAP_GLOBALS['_UNIT'] is upstream._UNIT
    assert numerical._CAP_GLOBALS['_gamma'] is upstream._gamma
    assert numerical._CAP_GLOBALS['_normalizer_certificate'] is upstream._normalizer_certificate
    assert dense(10.).tobytes() == native.y_old.tobytes() and dense(20.).tobytes() == end.tobytes()
    assert np.all(dense(np.linspace(10., 20., 101))[4] >= 0.)


@pytest.mark.parametrize('reason', ['habitats', 'two_guilds', 'absent', 'uncensored', 'no_census', 'census_interval', 'rare', 'volume'])
def test_every_gate_exclusion_uses_exact_frozen_constructor(monkeypatch, reason):
    p, y, coords, state, atol = setup(shared=reason == 'habitats', both=reason == 'two_guilds')
    if reason == 'absent':
        coords.groups[0]['present'] = False
    elif reason == 'uncensored':
        coords.dense_census = numerical.Census(minimum_cells=0., census_yr=1.)
    elif reason == 'no_census':
        coords.terminal_census_active = False
    elif reason == 'census_interval':
        coords.dense_census = numerical.Census(census_yr=1.)
    elif reason == 'rare':
        state[coords.m] = -900.
    elif reason == 'volume':
        coords.dense_census = numerical.Census(surface_cm2=1.)
    native, end = piece(state)
    expected = upstream._Dense(native, end, coords, atol)
    old_stats = coords.positive_dense_stats.copy()
    coords.positive_dense_stats = upstream._statistics()
    called = []
    original = upstream._Dense.__init__
    def observed(self, *args):
        called.append(True)
        return original(self, *args)
    monkeypatch.setattr(upstream._Dense, '__init__', observed)
    monkeypatch.setattr(numerical, '_CAP_CONSTRUCTOR', lambda *args: pytest.fail('Broader constructor entered'))
    actual = numerical._Dense(native, end, coords, atol)
    assert called == [True]
    assert actual.yh.tobytes() == expected.yh.tobytes() and actual.repaired == expected.repaired
    assert actual.native_start.tobytes() == expected.native_start.tobytes()
    assert actual.native_end.tobytes() == expected.native_end.tobytes()
    assert actual.negative_start == expected.negative_start and actual.negative_end == expected.negative_end
    assert coords.positive_dense_stats == old_stats
    assert coords.terminal_dense_stats['strict_budget_pieces'] == 1
    assert coords.terminal_dense_stats['broader_budget_pieces'] == 0


@pytest.mark.parametrize('array', ['start', 'Q', 'end'])
def test_nonfinite_native_arrays_use_original_rejection(array):
    p, y, coords, state, atol = setup()
    native, end = piece(state)
    if array == 'start':
        native.y_old[0] = np.nan
    elif array == 'Q':
        native.Q[0, 0] = np.inf
    else:
        end[0] = np.nan
    certificate, reason = numerical._terminal_certificate(native, end, coords)
    assert certificate is None and reason == 'nonfinite_native_arrays'
    with pytest.raises(upstream.stage.guarded._InvalidTrial, match='nonfinite'):
        numerical._Dense(native, end, coords, atol)


def test_whole_piece_bound_excludes_interior_total_dip_despite_large_endpoints():
    p, y, coords, state, atol = setup()
    state[coords.m] = 0.
    native, end = piece(state)
    native.Q[coords.m] = [-80., 80., 0.]
    end[coords.m] = 0.
    assert native.y_old[coords.m] > -16 and end[coords.m] > -16
    assert native(15.)[coords.m] == -20.
    certificate, reason = numerical._terminal_certificate(native, end, coords)
    assert certificate is None and reason == 'encoded_total_lower'
    dense = numerical._Dense(native, end, coords, atol)
    assert not dense.repaired and coords.terminal_dense_stats['strict_budget_pieces'] == 1


def test_exact_polynomial_and_volume_lower_bounds_are_conservative():
    p, y, coords, state, atol = setup()
    state[coords.m] = 1.
    native, end = piece(state)
    native.Q[coords.m] = [-.8, .4, -.1]
    end[coords.m] = state[coords.m]+sum(native.Q[coords.m])
    proof, reason = numerical._terminal_certificate(native, end, coords)
    assert reason is None
    polynomial = list(map(ratio, proof['encoded_total_polynomial_exact']))
    lower = ratio(proof['encoded_total_lower_exact'])
    for numerator in range(101):
        u = Fraction(numerator, 100)
        assert lower <= sum(coefficient*u**k for k, coefficient in enumerate(polynomial))
    conversion = (Fraction.from_float(p.coupled.habitat_l_cm2)
                  *Fraction.from_float(coords.dense_census.surface_cm2)
                  /Fraction.from_float(coords.dense_census.cell_mass_gdw))
    assert ratio(proof['volume_conversion_exact']) == conversion
    assert ratio(proof['total_cells_lower_exact']) == Fraction.from_float(numerical.stage.SCALE)/2**25*conversion
    assert exp(16) < 2**24 and log1p(exp(-16)) >= 1/2**25


@pytest.mark.parametrize('index', [0, 3, 4, 6])
def test_negative_native_endpoints_remain_hard_rejections(index):
    p, y, coords, state, atol = setup()
    coords.acetate_positive[0] = False
    state[3] = 1e-4
    native, end = piece(state)
    end[index] = -1e-30
    dense = numerical._Dense(native, end, coords, atol)
    assert index in dense.negative_end
    assert not upstream._positive_piece(dense, 10., 20., coords, state)
    assert coords.positive_dense_stats['negative_native_endpoint_rejections'] == 1
    if index == 4:
        assert index not in dense.repaired


class FakeRadau:
    mode = 'corner'
    def __init__(self, fun, time, state, bound, **kwargs):
        self.t = time
        self.y = state.copy()
        self.bound = bound
        self.nfev = self.njev = self.nlu = 0
        self.sol = None
    def _step_impl(self):
        old = self.y.copy()
        left = self.t
        self.t = min(self.bound, left+10.)
        Q = np.zeros((len(old), 3))
        Q[4] = [-.5e-27, 1e-27, 0.]
        if self.mode == 'exit':
            Q[0, 0] = -32.
            Q[6, 0] = -.25
        else:
            Q[6, 0] = .08
        self.y = old+Q.sum(axis=1)
        self.sol = RadauDenseOutput(left, self.t, old, Q)
        return True, None


def test_domain_prefix_precedes_later_negative_native_endpoint(monkeypatch):
    class Exit(FakeRadau):
        mode = 'exit'
    monkeypatch.setattr(upstream, 'Radau', Exit)
    p, y, coords, state, atol = setup()
    y[-1] = .125
    result = numerical.integrate_finite(y, p, 10., numerical.Census(), max_step=10.)
    assert result.status == 'domain_exit' and result.t[-1] == pytest.approx(5.)
    assert result.y[-1, -1] == 0. and result.y[0, -1] == pytest.approx(14.)
    stats = result.metadata['positive_dense_stats'][0]
    assert stats['negative_native_endpoint_pieces'] == 1 and stats['negative_native_endpoint_rejections'] == 0
    assert result.metadata['terminal_dense_stats'][0]['broader_budget_extensions'] == 1
    assert np.all(result.y >= 0.)


def test_census_vertices_and_contemporaneous_combined_minima_use_declared_dense_curve(monkeypatch):
    monkeypatch.setattr(upstream, 'Radau', FakeRadau)
    p, y, coords, state, atol = setup()
    y[-1] = .12
    result = numerical.integrate_finite(y, p, 10., numerical.Census(), sample_every_censuses=1, max_step=10.)
    assert result.status == 'completed' and np.array_equal(result.census_times, [0., 10.])
    response = model.core.response(p.coupled.climate.case)
    points = np.r_[.12, .20, response.ratios[(response.ratios >= .12)&(response.ratios <= .20)]]
    assert result.metadata['global_max_temperature_k'] == max(model.core.temperature_k(points, p.coupled.climate))
    assert result.global_continuous_min_log_biomass[0] == pytest.approx(np.log(y[1]), abs=1e-12)
    assert not result.extinction_events and not np.any(result.ledger['culled_cells'])
    assert result.metadata['terminal_dense_stats'][0]['broader_budget_extensions'] == 1
    event = result.metadata['positive_dense_stats'][0]['extensions'][0]
    assert 'terminal_macro_certificate' in event and np.all(result.y >= 0.)


@pytest.mark.parametrize('kind', ['uncensored', 'implicit_uncensored', 'rare_census'])
def test_actual_uncensored_and_rare_paths_never_use_broader_budget(kind):
    p, y, coords, state, atol = setup()
    if kind in ('uncensored', 'implicit_uncensored'):
        process = numerical.Census(minimum_cells=0., census_yr=.01)
    else:
        process = numerical.Census()
        conversion = p.coupled.habitat_l_cm2*process.surface_cm2/process.cell_mass_gdw
        y[1] = 1000./conversion
    result = (numerical.integrate(y, p, .01, max_step=.001) if kind == 'implicit_uncensored'
              else numerical.integrate_finite(y, p, .01, process, sample_every_censuses=1, max_step=.001))
    assert result.status == 'completed'
    stats = result.metadata['terminal_dense_stats'][0]
    assert stats['pieces'] > 0 and stats['broader_budget_pieces'] == 0
    assert stats['strict_budget_pieces'] == stats['pieces']
    for event in result.metadata['positive_dense_stats'][0]['extensions']:
        assert 'terminal_macro_certificate' not in event
        assert all(row['epsilon_squared'] == float(upstream._EPS**2) for row in event['components'])


def test_physical_rhs_and_all_native_source_constants_are_unchanged():
    p, y, coords, state, atol = setup()
    frozen = numerical.conditioned._Coordinates(y, p)
    old = frozen.encode(y)
    assert state.tobytes() == old.tobytes()
    assert coords.derivative(0., state).tobytes() == frozen.derivative(0., old).tobytes()
    assert numerical._CAP_CONSTRUCTOR.__code__ is upstream._Dense.__init__.__code__
    assert numerical._CAP_GLOBALS['_EPS'] == Fraction.from_float(1e-12)
    assert upstream._EPS == Fraction.from_float(np.finfo(float).eps)
    assert upstream._UNIT == upstream._EPS/2
    assert numerical._CAP_GLOBALS['_gamma'].__globals__['_UNIT'] is upstream._UNIT
