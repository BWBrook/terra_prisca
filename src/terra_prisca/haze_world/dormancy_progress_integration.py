"""Retry nonterminal native zero-time steps through the frozen driver.

The physical equations, coordinate conditioning and solver tolerances remain
those of the qualified analytic-Jacobian helper. Only its numerical constructor
is replaced in a private namespace; the original module is never modified.
"""

from hashlib import sha256
from math import isfinite
from types import FunctionType

from . import dormancy_jacobian_integration as qualified

Census = qualified.Census


class _ProgressLSODA(qualified._GuardedLSODA):
    def __init__(self, *args, progress_events, **kwargs):
        self._progress_events = progress_events
        super().__init__(*args, **kwargs)

    def step(self):
        left = float(self.t)
        accepted_hash = sha256(self.y.tobytes()).hexdigest()
        message = super().step()
        if self.status != "running" or self.t != left or left == self.t_bound:
            return message
        trial_time = float(self._last_trial_time)
        span = abs(trial_time-left)
        step = self.step_size
        candidates = [v for v in (self._nominal_max_step, span, step)
                      if v is not None and isfinite(v) and v > 0]
        limit = min(candidates)/2 if candidates else min(1e-6, self.t_bound-left)
        self._progress_events.append(dict(
            kind="native_nonterminal_zero_time", accepted_time_yr=left,
            native_return_time_yr=float(self.t), actual_rhs_trial_time_yr=trial_time,
            native_reported_step_size_yr=None if step is None else float(step),
            accepted_coordinate_sha256=accepted_hash,
            returned_coordinate_sha256=sha256(self.y.tobytes()).hexdigest(),
            driver_retry_limit_yr=float(limit),
            driver_retry_representable=bool(limit > 0 and left+limit != left),
            handler="unchanged_driver_failed_step_rollback"))
        self.status = "failed"
        return "Native solver returned without advancing at a nonterminal time"


def integrate(y0, p, years, **kwargs):
    events = []

    def constructor(*args, **options):
        return _ProgressLSODA(*args, progress_events=events, **options)

    namespace = qualified.integrate.__globals__.copy()
    namespace["_GuardedLSODA"] = constructor
    function = FunctionType(qualified.integrate.__code__, namespace,
                            qualified.integrate.__name__, qualified.integrate.__defaults__,
                            qualified.integrate.__closure__)
    function.__kwdefaults__ = qualified.integrate.__kwdefaults__
    try:
        result = function(y0, p, years, **kwargs)
    except RuntimeError as error:
        error.native_zero_time_events = events.copy()
        raise
    result.metadata.update(numerical_variant="analytic_switching_jacobian_progress_restart",
                           native_zero_time_retries=len(events), native_zero_time_events=events)
    return result


def integrate_finite(y0, p, years, process=Census(), **kwargs):
    return integrate(y0, p, years, census=process, **kwargs)
