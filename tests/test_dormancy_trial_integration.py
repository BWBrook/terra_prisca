from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from terra_prisca.haze_world import dormancy as d
from terra_prisca.haze_world import dormancy_integration as frozen
from terra_prisca.haze_world import dormancy_trial_integration as trial
from terra_prisca.haze_world import habitat_coupling as h


def state():
    p = d.Dormancy(h.Habitats(), epsilon=.1)
    return p, d.reference_state([30., 3e-4, 4e-4, 1e-4, .195], p)


def test_nonretry_flow_and_minima_match_frozen_bitwise():
    p, initial = state()
    process = trial.Census(minimum_cells=0., census_yr=.25)
    a = frozen.integrate_finite(initial, p, 2., process, sample_every_censuses=1, max_step=1.)
    b = trial.integrate_finite(initial, p, 2., process, sample_every_censuses=1, max_step=1.)
    for name in ("t", "y", "log_biomass", "log_active", "log_dormant", "log_acetate",
                 "global_continuous_min_log_biomass", "global_continuous_min_times_yr"):
        assert np.array_equal(getattr(a, name), getattr(b, name))
    assert b.metadata["trial_guard_rejections"] == 0
    assert b.metadata["acetate_trial_retries"] == 0
    assert np.all([abs(d.redox_residual(y, p)) < 1e-16 for y in b.y.T])


def test_zero_switching_has_no_added_dormant_seed_and_matches_frozen_bitwise():
    p, initial = state()
    p = replace(p, switching_factor=0.)
    process = trial.Census(minimum_cells=0., census_yr=.5)
    a = frozen.integrate_finite(initial, p, 5., process, sample_every_censuses=1, max_step=1.)
    b = trial.integrate_finite(initial, p, 5., process, sample_every_censuses=1, max_step=1.)
    assert np.array_equal(a.y, b.y) and np.array_equal(a.log_biomass, b.log_biomass)
    assert np.all(b.y[p.dormant_indices] == 0.)
    assert np.all(np.isneginf(b.log_dormant))


def test_chemical_underflow_chart_preserves_decoded_stock_and_records_old_log():
    p, initial = state()
    events = []
    coordinates = trial._ChemicalCoordinates(initial, p, events=events)
    internal = coordinates.encode(initial)
    internal[3] = -1000.
    before = coordinates.decode(internal)[0]
    coordinates.request_linear_acetate(1., internal)
    rate = coordinates.derivative(0., internal)
    after = coordinates.decode(internal)[0]
    assert before.tobytes() == after.tobytes()
    assert internal[3] == 0 and not coordinates.acetate_positive[0]
    assert np.all(np.isfinite(rate))
    assert events[0]["prior_log_acetate"] < -1000
    assert events[0]["physical_state_bitwise_preserved"]


def test_positive_chemical_pool_is_never_reset_by_chart_request():
    p, initial = state()
    events = []
    coordinates = trial._ChemicalCoordinates(initial, p, events=events)
    internal = coordinates.encode(initial)
    internal[3] = frozen.old._inverse(1e-300/frozen.old.ACETATE_SCALE)
    before = internal.copy()
    coordinates._pending_chemical[0] = 1.
    coordinates.derivative(0., internal)
    assert np.array_equal(internal, before) and coordinates.acetate_positive[0]
    assert events[0]["kind"] == "acetate_chart_retained_positive"


@pytest.mark.parametrize("kind", ["nonfinite_rhs", "acetate_source_overflow"])
def test_rejected_trial_rolls_back_and_restores_nominal_ceiling(monkeypatch, kind):
    original = trial._GuardedLSODA
    fired = [False]

    class Injected(original):
        def __init__(self, fun, *args, **kwargs):
            def inject(time, value):
                if time > .0001 and not fired[0]:
                    fired[0] = True
                    if kind == "acetate_source_overflow":
                        raise RuntimeError(trial._OVERFLOW)
                    return np.full_like(value, np.nan)
                return fun(time, value)
            super().__init__(inject, *args, **kwargs)

    p, initial = state()
    process = trial.Census(minimum_cells=0., census_yr=.25)
    reference = frozen.integrate_finite(initial, p, 1., process, sample_every_censuses=1, max_step=1.)
    monkeypatch.setattr(trial, "_GuardedLSODA", Injected)
    result = trial.integrate_finite(initial, p, 1., process, sample_every_censuses=1, max_step=1.)
    assert result.status == "completed" and fired[0]
    assert np.allclose(result.y, reference.y, rtol=3e-6, atol=2e-11)
    assert np.all(result.y >= 0)
    events = result.metadata["trial_guard_events"]
    acetate = result.metadata["acetate_trial_retry_events"]
    if kind == "acetate_source_overflow":
        assert events == [] and len(acetate) == 1
        assert acetate[0]["kind"] == kind
    else:
        assert acetate == [] and len(events) == 1
        assert events[0]["kind"] == kind
    ceilings = [v["max_step_yr"] for v in result.metadata["trial_guard_solver_constructions"]]
    reduced = next(i for i, value in enumerate(ceilings) if value < 1.)
    assert 1. in ceilings[reduced+1:]
    assert np.all(result.global_continuous_min_log_biomass <= np.min(result.log_biomass, axis=(0, 2))+1e-10)


def solver(fun):
    events, rejected = [], []
    instance = trial._GuardedLSODA(fun, 0., np.ones(1), 2., events=events,
                                    rejected=rejected, nominal_max_step=1., max_step=1.)
    return instance, events, rejected


@pytest.mark.parametrize("kind", ["rhs_floating_point", "nonfinite_rhs"])
def test_invalid_rhs_trials_are_failed_steps_without_clipping(monkeypatch, kind):
    class Coordinates:
        stage_positive = np.array([kind == "stage_square_overflow"])
        def derivative(self, time, value):
            if value[0] > 10:
                return np.exp(value) if kind == "rhs_floating_point" else np.full_like(value, np.nan)
            return -value
    instance, _, rejected = solver(Coordinates().derivative)
    def bad_step(self):
        self.fun(1., np.array([1e200]))
    monkeypatch.setattr(trial._RetryingLSODA, "step", bad_step)
    instance.step()
    assert instance.status == "failed" and rejected[0]["kind"] == kind
    assert instance.y[0] == 1.


def test_squared_stage_trial_uses_existing_exact_conditioning_path(monkeypatch):
    class Coordinates:
        stage_positive = np.array([True])
        def derivative(self, time, value):
            return -value
    instance, _, rejected = solver(Coordinates().derivative)
    monkeypatch.setattr(trial._RetryingLSODA, "step", lambda self: self.fun(1., np.array([1e200])))
    with pytest.raises(frozen._StageSourceOverflow) as error:
        instance.step()
    assert error.value.index == 0
    assert rejected == [] and instance.y[0] == 1.
    assert instance._conditioned[0]["accepted_linear_allocation"] == 1.


@pytest.mark.parametrize("failure", ["failed", "no_progress"])
def test_finite_stage_trial_conditions_only_after_native_failure(monkeypatch, failure):
    class Coordinates:
        stage_positive = np.array([True])
        def derivative(self, time, value):
            return value*1e9 if time > .5 else -value
    instance, _, rejected = solver(Coordinates().derivative)
    def unsuccessful(self):
        self.fun(1., self.y)
        if failure == "failed":
            self.status = "failed"
    monkeypatch.setattr(trial._RetryingLSODA, "step", unsuccessful)
    with pytest.raises(frozen._StageSourceOverflow):
        instance.step()
    assert rejected == []
    assert instance._conditioned[0]["kind"] == ("failed_native_finite_stage_rate" if failure == "failed" else "no_progress_finite_stage_rate")
    assert instance._conditioned[0]["conditioning_rate_yr"] == frozen.STAGE_LINEAR_RATE_YR


def test_disposable_finite_stage_trial_does_not_condition_a_successful_step(monkeypatch):
    class Coordinates:
        stage_positive = np.array([True])
        def derivative(self, time, value):
            return value*1e9 if time > .5 else -value
    instance, _, rejected = solver(Coordinates().derivative)
    def successful(self):
        self.fun(1., self.y)
        self.t_old, self.t = 0., .25
    monkeypatch.setattr(trial._RetryingLSODA, "step", successful)
    monkeypatch.setattr(trial._RetryingLSODA, "dense_output", lambda self: SimpleNamespace(h=.25, yh=np.ones((1, 2))))
    assert instance.step() is None
    assert rejected == [] and instance._conditioned == []


@pytest.mark.parametrize("where", ["coordinates", "dense"])
def test_nonfinite_native_result_is_rejected_before_dense_bookkeeping(monkeypatch, where):
    instance, _, rejected = solver(lambda t, y: -y)
    def completed(self):
        self.t_old, self.t = 0., .25
        if where == "coordinates":
            self.y[:] = np.nan
    monkeypatch.setattr(trial._RetryingLSODA, "step", completed)
    monkeypatch.setattr(trial._RetryingLSODA, "dense_output",
                        lambda self: SimpleNamespace(h=.25, yh=np.full((1, 2), np.nan)))
    instance.step()
    assert instance.status == "failed"
    assert rejected[0]["kind"] == "nonfinite_accepted_coordinates" if where == "coordinates" else rejected[0]["kind"] == "nonfinite_dense_coefficients"


def test_unrelated_rhs_errors_propagate(monkeypatch):
    def fun(t, y):
        if t > .5:
            raise ValueError("Unrelated model error")
        return -y
    instance, _, rejected = solver(fun)
    monkeypatch.setattr(trial._RetryingLSODA, "step", lambda self: self.fun(1., self.y))
    with pytest.raises(ValueError, match="Unrelated model error"):
        instance.step()
    assert rejected == []


def test_valid_zero_time_terminal_notification_needs_no_polynomial(monkeypatch):
    instance, _, rejected = solver(lambda t, y: -y)
    instance.t = instance.t_bound
    def terminal(self):
        self.t_old = self.t
        self.status = "finished"
    monkeypatch.setattr(trial._RetryingLSODA, "step", terminal)
    monkeypatch.setattr(trial._RetryingLSODA, "dense_output", lambda self: SimpleNamespace())
    assert instance.step() is None
    assert instance.status == "finished" and rejected == []


def test_zero_time_nonterminal_notification_reaches_frozen_progress_check(monkeypatch):
    instance, _, rejected = solver(lambda t, y: -y)
    monkeypatch.setattr(trial._RetryingLSODA, "step", lambda self: None)
    monkeypatch.setattr(trial._RetryingLSODA, "dense_output", lambda self: SimpleNamespace())
    assert instance.step() is None
    assert instance.status == "running" and rejected == []


def test_zero_time_notification_still_rejects_nonfinite_coordinates(monkeypatch):
    instance, _, rejected = solver(lambda t, y: -y)
    def invalid(self):
        self.y[:] = np.nan
    monkeypatch.setattr(trial._RetryingLSODA, "step", invalid)
    instance.step()
    assert instance.status == "failed"
    assert rejected[0]["kind"] == "nonfinite_accepted_coordinates"


def test_rare_per_capita_stock_remains_finite_without_seeding_absent_guild():
    base = h.Habitats()
    base = replace(base, base=replace(base.base, enabled=(True, False),
                   biology=replace(base.base.biology, loss_h=.02)))
    p = d.Dormancy(base, epsilon=.1)
    initial = d.reference_state([30., 1e-300, 0., 0., .195], p)
    result = trial.integrate_finite(initial, p, 5., trial.Census(minimum_cells=0., census_yr=1.),
                                    sample_every_censuses=1, max_step=1.)
    assert result.status == "completed" and np.all(result.y >= 0)
    assert np.all(np.isfinite(result.log_biomass[:, 0]))
    assert result.log_biomass[0, 0, -1] < -745
    assert np.all(np.isneginf(result.log_biomass[:, 1]))
    assert np.all(result.y[p.biomass_indices[:, 1]] == 0)
    assert np.all(result.y[p.dormant_indices[:, 1]] == 0)
