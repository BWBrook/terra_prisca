import numpy as np
import pytest

from terra_prisca.haze_world import bottleneck_integration as variant
from terra_prisca.haze_world import habitat_coupling as model
from terra_prisca.haze_world import habitat_integration as legacy


def test_rejected_trial_restores_last_accepted_state_and_dense_output():
    failed = False
    restart_states = []

    def rhs(time, state):
        nonlocal failed
        if time == 0:
            restart_states.append(state.copy())
        if time > .1 and not failed:
            failed = True
            state[0] = 1e100
            raise RuntimeError(variant._OVERFLOW)
        return -state

    events = []
    solver = variant._RetryingLSODA(rhs, 0., np.array([1.]), 1., events=events,
                                   first_step=.5, max_step=.5, rtol=1e-9, atol=1e-11)
    while solver.status == "running":
        previous_time, previous_state = solver.t, solver.y.copy()
        solver.step()
        dense = solver.dense_output()
        np.testing.assert_allclose(dense(previous_time), previous_state, rtol=0, atol=2e-14)
    assert len(events) == 1 and events[0]["retry"]
    assert len(restart_states) >= 2
    np.testing.assert_array_equal(restart_states[0], restart_states[1])
    assert solver.y[0] == pytest.approx(np.exp(-1), rel=2e-8)


def test_unknown_errors_propagate_and_known_trial_retries_are_bounded():
    def unknown(time, state):
        if time > 0:
            raise RuntimeError("Different physical fault")
        return -state
    solver = variant._RetryingLSODA(unknown, 0., np.array([1.]), 1., events=[])
    with pytest.raises(RuntimeError, match="Different physical fault"):
        solver.step()

    def persistent(time, state):
        if time > 0:
            raise RuntimeError(variant._OVERFLOW)
        return -state
    events = []
    solver = variant._RetryingLSODA(persistent, 0., np.array([1.]), 1., events=events)
    with pytest.raises(RuntimeError, match="step refinement"):
        solver.step()
    assert len(events) == 21 and sum(e["retry"] for e in events) == 20


def test_no_retry_trajectory_and_accepted_bookkeeping_match_frozen_integrator():
    p = model.Habitats(patches=(model.Patch("bulk", .96), model.Patch("warm", .02, "buffered", 286.),
                               model.Patch("cold", .02, "buffered", 278.)), dispersal_yr=.001)
    initial = model.embed_single(np.array([25., .0003, .0005, .0005, .195]), p)
    process = legacy.Census(minimum_cells=0., census_yr=1.)
    control = legacy.integrate_finite(initial, p, 10., process, sample_every_censuses=1, max_step=10.)
    result = variant.integrate_finite(initial, p, 10., process, sample_every_censuses=1, max_step=10.)
    np.testing.assert_array_equal(result.t, control.t)
    for key in ("y", "log_biomass", "log_acetate", "global_continuous_min_log_biomass", "global_continuous_min_times_yr"):
        np.testing.assert_array_equal(getattr(result, key), getattr(control, key))
    for key in result.ledger:
        np.testing.assert_array_equal(result.ledger[key], control.ledger[key])
    assert result.extinction_events == control.extinction_events
    assert result.metadata["acetate_trial_retries"] == 0
    assert legacy.integrate.__globals__["LSODA"] is legacy.LSODA
