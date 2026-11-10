"""Reject invalid dormancy trials through the frozen integration driver.

The physical RHS, census, accepted-flow and minimum algorithms stay unchanged.
Only the private numerical constructor and coordinate conditioning are replaced.
No stocks, seeds, clipping or physical inventory resets are added.
"""

from hashlib import sha256
from types import FunctionType

import numpy as np

from . import dormancy_integration as frozen
from .bottleneck_integration import _OVERFLOW, _RetryingLSODA

Census = frozen.Census
_SQUARE_LIMIT = np.sqrt(np.finfo(float).max)


class _InvalidTrial(ArithmeticError):
    def __init__(self, kind, detail, indices=()):
        super().__init__(detail)
        self.kind, self.detail, self.indices = kind, detail, [int(i) for i in indices]


class _ChemicalCoordinates(frozen._Coordinates):
    def __init__(self, initial, p, *, events):
        super().__init__(initial, p)
        self._chemical_events = events
        self._pending_chemical = {}

    def request_linear_acetate(self, time, state):
        physical, stages = self.decode(state)
        fluxes = frozen.model.fluxes(physical, self.p, trial_extension=True)
        for patch, positive in enumerate(self.acetate_positive):
            if not positive:
                continue
            local = fluxes["local"][patch]
            production = local["acetate_production_mol_l_yr"]
            coefficient = local["acetate_production_per_gdw_yr"]
            log_production = (np.log(production) if production > 0 else
                np.log(coefficient)+stages[patch, 0, 0]
                if coefficient > 0 and np.isfinite(stages[patch, 0, 0]) else -np.inf)
            z = state[6*patch+3]
            difference = log_production-(np.log(frozen.old.ACETATE_SCALE)-np.logaddexp(0., -z))
            if difference > np.log(np.finfo(float).max):
                self._pending_chemical[patch] = float(time)

    def derivative(self, time, state):
        pending, self._pending_chemical = self._pending_chemical, {}
        for patch, trial_time in pending.items():
            if not self.acetate_positive[patch]:
                continue
            index = 6*patch+3
            old = float(state[index])
            amount = float(frozen.old.ACETATE_SCALE*np.logaddexp(0., old))
            event = dict(kind="acetate_chart_retained_positive", patch=patch,
                         accepted_time_yr=float(time), triggering_trial_time_yr=trial_time,
                         prior_log_acetate=float(frozen.old._log_softplus(old, frozen.old.ACETATE_SCALE)),
                         prior_decoded_acetate_mol_l=amount, replacement_acetate_mol_l=amount)
            if amount == 0.:
                before = self.decode(state)[0]
                state[index] = amount
                self.acetate_positive[patch] = False
                after = self.decode(state)[0]
                event.update(kind="acetate_underflow_linear_chart",
                             physical_state_bitwise_preserved=before.tobytes() == after.tobytes())
                if not event["physical_state_bitwise_preserved"]:
                    raise RuntimeError("Chemical chart conversion changed the decoded physical state")
            self._chemical_events.append(event)
        return super().derivative(time, state)


class _GuardedLSODA(_RetryingLSODA):
    def __init__(self, fun, t0, y0, t_bound, *, rejected, nominal_max_step,
                 events, conditioned=None, finite_trials=None, **kwargs):
        self._rejected = rejected
        self._conditioned = [] if conditioned is None else conditioned
        self._nominal_max_step = nominal_max_step
        self._finite_trials = [0] if finite_trials is None else finite_trials
        self._finite_targets = set()
        coordinates = getattr(fun, "__self__", None)

        def guarded(time, state):
            bad = np.flatnonzero(~np.isfinite(state))
            if len(bad):
                raise _InvalidTrial("nonfinite_trial_coordinates", "Nonfinite RHS trial coordinates", bad)
            positive = getattr(coordinates, "stage_positive", None)
            if positive is not None:
                indices = np.flatnonzero(positive)
                bad = indices[abs(state[indices]) > _SQUARE_LIMIT]
                if len(bad):
                    self._condition_stage(bad, time, y0, t0, "squared_stage_trial_overflow")
            try:
                with np.errstate(over="raise", invalid="raise"):
                    value = fun(time, state)
            except FloatingPointError as error:
                if str(error).startswith(("overflow encountered", "invalid value encountered")):
                    raise _InvalidTrial("rhs_floating_point", str(error)) from error
                raise
            except RuntimeError as error:
                if str(error) == _OVERFLOW:
                    if isinstance(coordinates, _ChemicalCoordinates):
                        coordinates.request_linear_acetate(time, state)
                    raise _InvalidTrial("acetate_source_overflow", str(error)) from error
                raise
            bad = np.flatnonzero(~np.isfinite(value))
            if len(bad):
                raise _InvalidTrial("nonfinite_rhs", "RHS returned nonfinite values", bad)
            if positive is not None:
                indices = np.flatnonzero(positive)
                targets = indices[value[indices]*np.sign(state[indices])
                    > frozen.STAGE_LINEAR_RATE_YR*abs(state[indices])]
                if len(targets):
                    self._finite_targets.update(map(int, targets))
                    self._finite_trials[0] += 1
            return value

        super().__init__(guarded, t0, y0, t_bound, events=events, **kwargs)

    def _condition_stage(self, indices, time, initial, initial_time, kind):
        accepted = getattr(self, "_guard_start", np.asarray(initial))
        index = int(min(indices, key=lambda i: abs(accepted[i])))
        value = float(accepted[index])
        if not np.isfinite(value) or abs(value) > _SQUARE_LIMIT:
            raise _InvalidTrial("stage_square_overflow", "Accepted stage allocation cannot be conditioned", indices)
        self._conditioned.append(dict(
            kind=kind, state_index=index,
            accepted_time_yr=float(getattr(self, "_guard_left", initial_time)), trial_time_yr=float(time),
            accepted_root_coordinate=value, accepted_linear_allocation=value**2,
            accepted_log_allocation=float(2*np.log(abs(value))) if value else None,
            conditioning_rate_yr=frozen.STAGE_LINEAR_RATE_YR,
            handler="frozen_stage_conditioning_path"))
        raise frozen._StageSourceOverflow(index)

    def _fail(self, left, initial_hash, error):
        span = abs(self._last_trial_time-left)
        candidates = [v for v in (self._nominal_max_step, span, self.step_size)
                      if v is not None and np.isfinite(v) and v > 0]
        limit = min(candidates)/2 if candidates else min(1e-6, self.t_bound-left)
        attempt = 1+sum(e["accepted_time_yr"] == left for e in self._rejected+self._retry_events)
        event = dict(kind=error.kind, detail=error.detail, nonfinite_or_overflow_indices=error.indices,
                     accepted_time_yr=left,
                     trial_time_yr=float(self._last_trial_time) if np.isfinite(self._last_trial_time) else None,
                     accepted_coordinate_sha256=initial_hash, attempt=attempt,
                     retry=bool(attempt <= 20 and limit > 0 and left+limit != left),
                     retry_max_step_yr=float(limit), handler="unchanged_driver_failure_path")
        if error.kind == "acetate_source_overflow":
            self._retry_events.append(event)
        else:
            self._rejected.append(event)
        self.status = "failed"
        return "Rejected dormancy numerical trial: "+error.detail

    def step(self):
        left = float(self.t)
        self._guard_left, self._guard_start = left, self.y.copy()
        self._finite_targets.clear()
        initial_hash = sha256(self._guard_start.tobytes()).hexdigest()
        try:
            message = super().step()
            if self.status == "failed":
                if self._finite_targets:
                    self._condition_stage(self._finite_targets, self._last_trial_time, self._guard_start, left,
                                          "failed_native_finite_stage_rate")
                return message
            bad = np.flatnonzero(~np.isfinite(self.y))
            if not np.isfinite(self.t) or len(bad):
                raise _InvalidTrial("nonfinite_accepted_coordinates", "Solver returned nonfinite coordinates", bad)
            if self.t == left:
                if left != self.t_bound and self._finite_targets:
                    self._condition_stage(self._finite_targets, self._last_trial_time, self._guard_start, left,
                                          "no_progress_finite_stage_rate")
                return message
            dense = super().dense_output()
            bad = np.flatnonzero(~np.isfinite(dense.yh))
            if not np.isfinite(dense.h) or len(bad):
                raise _InvalidTrial("nonfinite_dense_coefficients", "Solver returned nonfinite dense coefficients", bad)
            return message
        except _InvalidTrial as error:
            return self._fail(left, initial_hash, error)





def integrate(y0, p, years, **kwargs):
    rejected, conditioned, chemical, constructions, finite_trials = [], [], [], [], [0]
    nominal_max_step = kwargs.get("max_step", np.inf)

    def constructor(fun, time, state, bound, **options):
        constructions.append(dict(time_yr=float(time), max_step_yr=float(options.get("max_step", np.inf))))
        return _GuardedLSODA(fun, time, state, bound, rejected=rejected,
                             nominal_max_step=nominal_max_step, conditioned=conditioned,
                             finite_trials=finite_trials, **options)

    namespace = frozen.integrate.__globals__.copy()
    namespace["_RetryingLSODA"] = constructor
    namespace["_Coordinates"] = lambda initial, params: _ChemicalCoordinates(initial, params, events=chemical)
    function = FunctionType(frozen.integrate.__code__, namespace, frozen.integrate.__name__,
                            frozen.integrate.__defaults__, frozen.integrate.__closure__)
    function.__kwdefaults__ = frozen.integrate.__kwdefaults__
    result = function(y0, p, years, **kwargs)
    result.metadata.update(
        numerical_variant="Invalid dormancy trial rejection and accepted-state coordinate conditioning; frozen physical equations",
        trial_guard_rejections=len(rejected), trial_guard_events=rejected,
        trial_guard_stage_conditionings=len(conditioned), trial_guard_stage_conditioning_events=conditioned,
        trial_guard_finite_trial_observations=finite_trials[0],
        trial_guard_chemical_conditionings=sum(e["kind"] == "acetate_underflow_linear_chart" for e in chemical),
        trial_guard_chemical_chart_events=chemical,
        trial_guard_solver_constructions=constructions,
        trial_guard_scope="Nonfinite RHS coordinates/values, floating over/invalid, or nonfinite accepted coordinates/dense polynomial use the frozen rollback/refine/restore path. Squared-stage overflow uses the inherited accepted-allocation conditioning path. Finite trial rates beyond the existing conditioning threshold are recorded without intervention unless the native solver fails or cannot advance. Ordinary stage promotion is unchanged; no clipping, seeds or inventory changes.",
        trial_guard_underflow_scope="Global guild log stocks are retained. Stage conditioning preserves decoded allocation and records its prior log; a subfloat stage log can be lost, as in the frozen conditioning path, and replenishment is only physical conversion/migration. Acetate chart conversion is allowed only for exactly zero decoded stock, preserves the physical state bitwise, and records the prior chemical log; positive pools are unchanged.",
        acetate_trial_scope="Only actual named acetate-source overflows; failed-step retry handled by the frozen driver with ceiling restoration")
    return result


def integrate_finite(y0, p, years, process=Census(), **kwargs):
    return integrate(y0, p, years, census=process, **kwargs)
