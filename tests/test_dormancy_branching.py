import numpy as np
import pytest
from scipy.integrate import quad, solve_ivp
from scipy.linalg import expm
from scipy.special import gammainc

from terra_prisca.haze_world import branching as old
from terra_prisca.haze_world import dormancy_branching as d


def test_zero_switching_recovers_active_reference_exactly():
    times = np.linspace(0., 12., 25)
    active_birth = np.column_stack((.8+.1*np.sin(times), .4+.05*np.cos(times)))
    active_death = np.column_stack((np.full(len(times), .6), np.full(len(times), .9)))
    migration = np.array([[0., .03], [.07, 0.]])
    birth, death = np.zeros((len(times), 4)), np.zeros((len(times), 4))
    birth[:, ::2], death[:, ::2], death[:, 1::2] = active_birth, active_death, .01
    transitions = np.zeros((4, 4))
    transitions[np.ix_([0, 2], [0, 2])] = transitions[np.ix_([1, 3], [1, 3])] = migration
    expected = old.backward_survival(times, active_birth, active_death, migration, max_step=.5)
    actual = d.backward_survival(times, birth, death, transitions, max_step=.5)
    assert np.array_equal(actual[::2], expected)
    assert np.allclose(actual[1::2], -.01*times[-1], rtol=1e-10, atol=1e-12)


def test_one_way_dormancy_closed_form_and_origin_row_orientation():
    duration, sigma, active_death, dormant_death = 15., .4, .7, .02
    times = np.array([0., duration])
    birth = np.zeros((2, 2)); death = np.tile([active_death, dormant_death], (2, 1))
    transitions = np.array([[0., sigma], [0., 0.]])
    actual = np.exp(d.backward_survival(times, birth, death, transitions))
    a = active_death+sigma
    expected_active = np.exp(-a*duration)+sigma/(a-dormant_death)*(np.exp(-dormant_death*duration)-np.exp(-a*duration))
    assert actual == pytest.approx([expected_active, np.exp(-dormant_death*duration)], rel=2e-9)
    generator = transitions-np.diag(transitions.sum(axis=1)+death[0])
    assert actual == pytest.approx(expm(generator*duration)@np.ones(2), rel=2e-9)


def test_variable_conversion_and_common_pure_death_integral():
    times = np.array([0., 1., 4., 10.])
    transition = np.zeros((len(times), 2, 2))
    transition[:, 0, 1] = [.3, .7, 0., 1.]
    transition[:, 1, 0] = [0., .2, .8, .1]
    delta = np.array([.02, .03, .04, .01])
    actual = d.backward_survival(times, np.zeros((4, 2)), np.tile(delta[:, None], (1, 2)), transition, max_step=.25)
    expected = -np.trapezoid(delta, times)
    assert actual == pytest.approx(np.full(2, expected), rel=1e-8, abs=1e-10)


def test_variable_transitions_match_independent_forward_no_birth_process():
    times = np.linspace(0., 8., 17)
    transition = np.zeros((len(times), 4, 4))
    for i, t in enumerate(times):
        transition[i, 0, 1] = .2+.1*np.sin(t)
        transition[i, 1, 0] = .1+.05*np.cos(t)
        transition[i, 2, 3] = .3+.1*np.cos(t)
        transition[i, 3, 2] = .15
        transition[i, 0, 2] = transition[i, 1, 3] = .04
        transition[i, 2, 0] = transition[i, 3, 1] = .02
    death = np.tile([.6, .02, .4, .03], (len(times), 1))
    birth = np.zeros_like(death)

    def forward(time, flat):
        q = np.array([[np.interp(time, times, transition[:, i, j]) for j in range(4)] for i in range(4)])
        operator = q.T-np.diag(q.sum(axis=1)+death[0])
        return (operator@flat.reshape(4, 4)).ravel()

    independent = solve_ivp(forward, (times[0], times[-1]), np.eye(4).ravel(), method="DOP853",
                            rtol=2e-12, atol=1e-14, max_step=.1)
    expected = np.sum(independent.y[:, -1].reshape(4, 4), axis=0)
    actual = np.exp(d.backward_survival(times, birth, death, transition, max_step=.25))
    assert actual == pytest.approx(expected, rel=2e-8, abs=1e-10)


def test_conversion_opening_recovers_an_underflowed_probability_without_losing_tail():
    terminal = 1000.
    times = np.array([0., 1., terminal])
    birth = np.tile([1., 0.], (3, 1))
    death = np.ones((3, 2))
    transition = np.zeros((3, 2, 2)); transition[0, 1, 0] = 1.
    expected_active = 1/(1+terminal)
    expected_dormant = quad(lambda s: np.exp(-2*s+s*s/2)*(1-s)/(1+terminal-s), 0., 1.,
                             epsabs=1e-14, epsrel=1e-12)[0]+np.exp(-terminal-.5)
    result = d.backward_survival(times, birth, death, transition, max_step=10., return_solution=True)
    tight = d.backward_survival(times, birth, death, transition, rtol=1e-10, atol=1e-12, max_step=1.)
    assert result.conversion_opening_steps > 0
    assert np.exp(result.initial_log_survival) == pytest.approx([expected_active, expected_dormant], rel=3e-7)
    assert result.initial_log_survival == pytest.approx(tight, rel=2e-8, abs=1e-9)
    recovered = d._birth_death_step(np.array([-1000.]), np.array([1.]), np.array([0.]), 1000.)
    assert recovered == pytest.approx([-np.log(2.)], abs=1e-12)


def test_no_death_never_extinguishes_even_with_variable_conversions():
    times = np.array([0., 2., 10.]); birth = np.tile([.2, 0.], (3, 1))
    transition = np.zeros((3, 2, 2)); transition[:, 0, 1] = [.5, 0., .7]
    transition[:, 1, 0] = [.2, .3, 0.]
    assert np.array_equal(d.backward_survival(times, birth, np.zeros_like(birth), transition), [0., 0.])


def test_opening_wake_edge_preserves_a_new_two_hop_migration_path():
    times = np.array([0., 1., 1000.])
    transitions = np.zeros((3, 3, 3))
    transitions[0, 1, 0] = 1.
    transitions[:, 2, 1] = 1e-9
    birth = np.zeros((3, 3)); death = np.tile([0., 1., 1.], (3, 1))

    def forward(time, flat):
        q = np.array([[0., 0., 0.], [1-time, 0., 0.], [0., 1e-9, 0.]])
        generator = q.T-np.diag(q.sum(axis=1)+death[0])
        return (generator@flat.reshape(3, 3)).ravel()

    independent = solve_ivp(forward, (0., 1.), np.eye(3).ravel(), method="DOP853",
                            rtol=1e-12, atol=1e-24, max_step=.01)
    expected = independent.y[:, -1].reshape(3, 3)[0]
    result = d.backward_survival(times, birth, death, transitions, max_step=10., return_solution=True)
    assert result.conversion_opening_steps > 0
    assert np.exp(result.initial_log_survival) == pytest.approx(expected, rel=5e-7, abs=1e-20)
    assert result.initial_log_survival[2] > -100.


def test_stiff_conversion_kernel_keeps_positive_rare_migration_and_probability_mass():
    transition = np.array([[0., 87., 1e-9, 0.], [.02, 0., 0., 1e-9],
                           [2e-9, 0., 0., 60.], [0., 2e-9, .01, 0.]])
    actual = d._conversion_kernel(transition, 1000.)
    expected = expm((transition-np.diag(transition.sum(axis=1)))*1000.)
    assert np.all(actual >= 0)
    assert actual.sum(axis=1) == pytest.approx(np.ones(4), abs=3e-16)
    assert actual == pytest.approx(expected, rel=1e-9, abs=5e-12)
    assert actual[0, 2] > 0


@pytest.mark.parametrize("duration", [1e-6, 1e-8, 1e-10])
@pytest.mark.parametrize("affine", [False, True])
def test_five_hop_leading_path_survives_absolute_poisson_truncation(duration, affine):
    transition = np.zeros((6, 6))
    for index in range(1, 6):
        transition[index, index-1] = 1.
    factor = (lambda time: .5+.5*time/duration) if affine else (lambda time: 1.)
    interpolate = lambda time: (np.zeros(6), np.zeros(6), transition*factor(time))
    initial = np.r_[0., np.full(5, -1000.)]
    coarse = d._positive_step(initial, duration, duration, interpolate)
    half = d._positive_step(initial, duration, duration/2, interpolate)
    fine = d._positive_step(half, duration/2, duration/2, interpolate)
    integrated_rate = duration*(.75 if affine else 1.)
    probability = gammainc(np.arange(1, 6), integrated_rate)
    expected = np.r_[0., np.logaddexp(np.log(probability), np.log1p(-probability)-1000.)]
    assert np.all(np.isfinite(coarse)) and np.all(coarse <= 0.)
    assert coarse[-1] > -200. and fine[-1] > -200.
    assert coarse == pytest.approx(expected, abs=2*duration)
    assert fine == pytest.approx(expected, abs=2*duration)
    kernel = d._timevarying_kernel(interpolate(duration)[2], interpolate(0.)[2], duration)
    assert kernel[-1, 0] > 0.
    assert kernel[-1, 0] == pytest.approx(probability[-1], rel=2*duration)


@pytest.mark.parametrize("death", [0., 1e-20, 1e-8, .1])
def test_conversion_mixture_preserves_tiny_common_death_without_positive_log_roundoff(death):
    random = np.random.default_rng(831)
    for _ in range(2):
        start, end = random.random((6, 6)), random.random((6, 6))
        np.fill_diagonal(start, 0.); np.fill_diagonal(end, 0.)
    duration = .3/max(start.sum(axis=1).max(), end.sum(axis=1).max())
    interpolate = lambda time: (np.zeros(6), np.full(6, death),
                               start+(time/duration)*(end-start))
    actual = d._positive_step(np.zeros(6), duration, duration, interpolate)
    assert np.all(actual <= 0.)
    assert actual == pytest.approx(np.full(6, -death*duration), rel=2e-14, abs=0.)
    if death == 0.:
        assert np.array_equal(actual, np.zeros(6))


@pytest.mark.parametrize("birth,duration", [(3.1622776601683794e-12, 1e-12),
                                             (1., 1e-12), (1., 1.), (1e6, .001)])
def test_scalar_survival_one_is_exact_for_zero_death(birth, duration):
    actual = d._birth_death_step(np.zeros(1), np.array([birth]), np.zeros(1), duration)
    assert np.array_equal(actual, np.zeros(1))


def test_scalar_pure_death_retains_tiny_decay_and_deep_probability_tail():
    death = np.array([0., 1e-20, 1e-8, .01, 1000.])
    for initial in (np.zeros(5), np.full(5, -1000.)):
        actual = d._birth_death_step(initial, np.zeros(5), death, .01)
        assert np.all(np.isfinite(actual)) and np.all(actual <= 0.)
        assert actual == pytest.approx(initial-death*.01, rel=2e-14, abs=1e-13 if initial[0] else 0.)


def failed_opening_fixture():
    """Captured0006 methanogen opening at95130yr; no physical rerun."""
    birth = np.array([[8.766000506555727, 0., 8.765999980207246, 0., 6.216469585132422, 0.],
                      [8.765999651891617, 0., 8.765999980206562, 0., 6.216469585132852, 0.]])
    death = np.tile([8.766, .8766, 8.766, .8766, 8.766, .8766], (2, 1))
    transition = np.zeros((2, 6, 6))
    for origin, destination in [(0, 2), (0, 4), (1, 3), (1, 5),
                                (2, 4), (3, 5), (4, 2), (5, 3)]:
        transition[:, origin, destination] = 2e-8
    for origin, destination in [(2, 0), (3, 1), (4, 0), (5, 1)]:
        transition[:, origin, destination] = 9.6e-7
    transition[0, 1, 0] = 8.781611726785461e-13
    transition[1, 0, 1] = 4.1471404295948384e-13
    transition[:, 2, 3] = [1.3407018928681627e-15, 1.3407945988470027e-15]
    transition[:, 4, 5] = [17.932118106913848, 17.932118106908522]
    accepted = np.array([-12.427758354585496, -111.53647417567319, -10.661280941617102,
                         -102.994634949518, -29.188612368692255, -116.43466013090202])
    return np.array([95120., 95130.]), (birth, death, transition), accepted


def test_local_affine_rates_and_probability_step_are_clock_translation_invariant():
    times, arrays, accepted = failed_opening_fixture()
    start = times[-1]
    endpoint, duration = d._backward_interval(start, 1.0387200420669981e-10)
    assert start-endpoint == duration and duration == 7*np.spacing(start)
    absolute = d._local_rates(times, arrays, 0, start)
    translated = d._local_rates(times-start, arrays, 0, 0.)
    for offset in (0., -duration/4, -duration/2, -3*duration/4, -duration):
        for actual, expected in zip(absolute(offset), translated(offset)):
            assert np.array_equal(actual, expected)
    assert np.array_equal(d._positive_step(accepted, 0., duration, absolute),
                          d._positive_step(accepted, 0., duration, translated))
    opening = absolute(-duration/2)[2][1, 0]
    assert opening == pytest.approx(arrays[2][0, 1, 0]*duration/20., rel=2e-16)


def test_actual_failed_opening_resolves_without_changing_adaptive_criteria():
    times, arrays, accepted = failed_opening_fixture()
    start = times[-1]
    interpolate = d._local_rates(times, arrays, 0, start)
    rate = max(q.sum(axis=1).max() for q in arrays[2])
    duration = min(10., 1/rate)
    for _ in range(30):
        endpoint, duration = d._backward_interval(start, duration)
        coarse = d._positive_step(accepted, 0., duration, interpolate)
        half = d._positive_step(accepted, 0., duration/2, interpolate)
        fine = d._positive_step(half, -duration/2, duration/2, interpolate)
        error = max(abs(fine-coarse)/(1e-11+1e-9*np.maximum(1., abs(fine))))
        if error <= 1. and np.all(fine <= 0.):
            break
        duration /= 2
    else:
        pytest.fail('Captured opening failed the unchanged30-attempt bootstrap')
    assert np.all(np.isfinite(fine)) and duration > 100*np.spacing(start)
    assert start-endpoint == duration


@pytest.mark.parametrize("duration", [1.0387200420669981e-10, .055765853, 1., 10.])
def test_backward_endpoint_is_representable_without_exceeding_requested_step(duration):
    start = 95130.
    endpoint, actual = d._backward_interval(start, duration)
    assert actual == start-endpoint and 0. < actual <= duration


def test_unrepresentable_backward_interval_fails_explicitly():
    with pytest.raises(ArithmeticError, match="lost time resolution"):
        d._backward_interval(95130., np.spacing(95130.)/4)


def test_invalid_transition_rates_are_rejected():
    with pytest.raises(ValueError, match="zero diagonal"):
        d.backward_survival([0., 1.], np.zeros((2, 2)), np.zeros((2, 2)), np.eye(2))
    with pytest.raises(ValueError, match="nonnegative"):
        d.backward_survival([0., 1.], np.zeros((2, 2)), np.zeros((2, 2)), [[0., -1.], [0., 0.]])


@pytest.mark.parametrize("ramp", ("linear", "cubic"))
def test_branching_mean_matches_both_physical_pools_and_conservative_exchange(ramp):
    from terra_prisca.haze_world import dormancy as model, habitat_coupling as habitat
    p = model.Dormancy(habitat.Habitats(patches=(habitat.Patch("bulk", .98),
        habitat.Patch("warm", .02, "buffered", 286.), habitat.Patch("inactive", 0.)), dispersal_yr=.003), ramp=ramp)
    y = np.array([10., 1e-5, 2e-5, 1e-4, 3e-5, 4e-5,
                  25., 4e-5, 1e-5, 2e-4, 1e-5, 3e-5,
                  0., 0., 0., 0., 0., 0., .195])
    rates = model.rhs(y, p)
    for guild in (0, 1):
        active, birth, death, transition = d.per_cell_rates(y, p, guild)
        count = np.column_stack((y[p.biomass_indices[active, guild]],
                                 y[p.dormant_indices[active, guild]]))*p.weights[active, None]
        physical = np.column_stack((rates[p.biomass_indices[active, guild]],
                                    rates[p.dormant_indices[active, guild]]))*p.weights[active, None]
        operator = np.diag(birth-death-transition.sum(axis=1))+transition.T
        assert operator@count.ravel() == pytest.approx(physical.ravel(), rel=1e-12, abs=1e-16)
        expected = old.per_cell_rates(model.active_state(y, p), p.base, guild)
        assert np.array_equal(birth[::2], expected[1])
        assert np.array_equal(death[::2], expected[2])
