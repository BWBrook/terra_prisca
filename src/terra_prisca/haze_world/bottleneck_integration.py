"""Retry rejected acetate-coordinate trials without changing accepted stocks.

The buffered-refuge integrator is frozen. This named numerical variant reuses
its function code with a private LSODA constructor; no module globals change.
Only its explicit acetate-source coordinate overflow is retried. Biomass and
chemical coordinates restart from the last accepted state, without seeds,
clipping or inventory jumps.
"""

from types import FunctionType

import numpy as np
from scipy.integrate import LSODA

from . import habitat_integration as legacy

Census = legacy.Census
_OVERFLOW = "Acetate source exceeds the representable coordinate range"


class _RetryingLSODA(LSODA):
    def __init__(self, fun, t0, y0, t_bound, *, events, **kwargs):
        self._physical_rhs = fun
        self._restart_options = kwargs.copy()
        self._retry_events = events
        self._last_trial_time = float(t0)
        self._initialize(t0, y0, t_bound, kwargs)

    def _initialize(self, time, state, bound, options):
        def observed(time, state):
            self._last_trial_time = float(time)
            return self._physical_rhs(time, state)
        LSODA.__init__(self, observed, time, state.copy(), bound, **options)

    def step(self):
        start_time, start_state = float(self.t), self.y.copy()
        previous_step = self.step_size
        ceiling = float(self._restart_options.get("max_step", np.inf))
        for attempt in range(21):
            try:
                return super().step()
            except RuntimeError as error:
                if str(error) != _OVERFLOW:
                    raise
                span = abs(self._last_trial_time - start_time)
                available = [v for v in (ceiling, span, previous_step) if v is not None and np.isfinite(v) and v > 0]
                retry_step = min(available) / 2 if available else 0.
                representable = start_time + self.direction * retry_step != start_time
                retry = attempt < 20 and retry_step > 0 and representable
                self._retry_events.append(dict(accepted_time_yr=start_time, trial_time_yr=self._last_trial_time,
                    attempt=attempt + 1, retry=retry, retry_max_step_yr=retry_step))
                if not retry:
                    raise RuntimeError("Cannot resolve rejected acetate-coordinate trial by step refinement") from error
                spent = self.nfev
                options = self._restart_options.copy()
                options["max_step"] = ceiling = retry_step
                if options.get("first_step") is not None:
                    options["first_step"] = min(options["first_step"], retry_step)
                self._initialize(start_time, start_state, self.t_bound, options)
                self.nfev += spent


def integrate(y0, p, years, **kwargs):
    events = []

    def constructor(*args, **options):
        return _RetryingLSODA(*args, events=events, **options)

    namespace = legacy.integrate.__globals__.copy()
    namespace["LSODA"] = constructor
    function = FunctionType(legacy.integrate.__code__, namespace, legacy.integrate.__name__,
                            legacy.integrate.__defaults__, legacy.integrate.__closure__)
    function.__kwdefaults__ = legacy.integrate.__kwdefaults__
    result = function(y0, p, years, **kwargs)
    result.metadata.update(numerical_variant="Rejected acetate-coordinate trial step refinement; frozen accepted-flow algorithm",
        acetate_trial_overflows=len(events), acetate_trial_retries=sum(event["retry"] for event in events),
        acetate_trial_retry_events=events,
        acetate_trial_retry_scope="Only the named derivative-trial overflow; restart all coordinates at the last accepted state; at most20 refinements per step; no inventory reset")
    return result


def integrate_finite(y0, p, years, process=Census(), **kwargs):
    return integrate(y0, p, years, census=process, **kwargs)
