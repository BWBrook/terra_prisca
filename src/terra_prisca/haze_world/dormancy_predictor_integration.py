"""Zero-increment native stage guesses for present tiny linear allocations.

This variant extends the strict conditioned producer. It changes only Radau's
collocation initial guess on selected steps. The original machine-epsilon-
squared dense budget applies everywhere; no terminal-budget source is imported.
Native states, error history, Jacobian/LU, physical equations, tolerances and
accepted-step guards retain their original handling.
"""

from scipy.integrate import Radau

from . import dormancy_conditioned_integration as conditioned

upstream = conditioned.upstream
stage = conditioned.stage
Census = conditioned.Census
TINY_LINEAR_ALLOCATION_CAP = conditioned.LINEAR_ALLOCATION_CAP


class _Coordinates(conditioned._Coordinates):
    def __init__(self, initial, p):
        super().__init__(initial, p)
        self.zero_stage_predictor_stats = dict(native_step_calls=0, tiny_linear_step_calls=0,
            prior_dense_predictors_suppressed=0, native_successes=0,
            native_failures=0, native_exceptions=0,
            restored_prior_dense_on_failure=0, tiny_indices={})


def _tiny_linear_indices(state, coords):
    return [int(index) for group in coords.groups if group['present'] for index in group['indices']
            if not coords.stage_positive[index] and 0. <= state[index] <= TINY_LINEAR_ALLOCATION_CAP]


class _NativeRadau(Radau):
    def __init__(self, fun, *args, coordinates, **kwargs):
        self._predictor_coordinates = coordinates
        super().__init__(fun, *args, **kwargs)

    def _step_impl(self):
        coords = self._predictor_coordinates
        stats = coords.zero_stage_predictor_stats
        stats['native_step_calls'] += 1
        tiny = _tiny_linear_indices(self.y, coords)
        if tiny:
            stats['tiny_linear_step_calls'] += 1
            for index in tiny:
                stats['tiny_indices'][index] = stats['tiny_indices'].get(index, 0)+1
        previous = self.sol
        if tiny:
            stats['prior_dense_predictors_suppressed'] += int(previous is not None)
            self.sol = None
        try:
            success, message = super()._step_impl()
        except BaseException:
            stats['native_exceptions'] += 1
            if tiny:
                self.sol = previous
                stats['restored_prior_dense_on_failure'] += 1
            raise
        if success:
            stats['native_successes'] += 1
        else:
            stats['native_failures'] += 1
            if tiny:
                self.sol = previous
                stats['restored_prior_dense_on_failure'] += 1
        return success, message


class _InjectedNative(upstream._Radau):
    def _step_impl(self):
        def constructor(fun, *args, **kwargs):
            return _NativeRadau(fun, *args, coordinates=self.coordinates, **kwargs)

        namespace = upstream._Radau._step_impl.__globals__.copy()
        namespace['Radau'] = constructor
        function = stage.chemical._copied(upstream._Radau._step_impl, namespace)
        return function(self)


class _Radau(conditioned._Radau, _InjectedNative):
    pass


_MRO = _Radau.__mro__
if (_Radau._step_impl is not conditioned._Radau._step_impl
    or not _MRO.index(conditioned._Radau) < _MRO.index(_InjectedNative) < _MRO.index(upstream._Radau)
    or _Radau._dense_output_impl is not upstream._Radau._dense_output_impl):
    raise RuntimeError('Predictor adapter must preserve conditioned root guards and strict dense output')


def integrate(y0, p, years, **kwargs):
    instances = []

    def coordinates(initial, parameters):
        value = _Coordinates(initial, parameters)
        instances.append(value)
        return value

    namespace = conditioned.integrate.__globals__.copy()
    namespace.update(_Coordinates=coordinates, _Radau=_Radau)
    function = stage.chemical._copied(conditioned.integrate, namespace)
    try:
        result = function(y0, p, years, **kwargs)
    except RuntimeError as error:
        error.zero_stage_predictor_stats = [c.zero_stage_predictor_stats for c in instances]
        raise
    result.metadata.update(numerical_variant='radau_dormancy_zero_stage_predictor',
        upstream_numerical_variant='radau_dormancy_tolerance_conditioning',
        zero_stage_predictor_stats=[c.zero_stage_predictor_stats for c in instances],
        zero_stage_predictor_cap=TINY_LINEAR_ALLOCATION_CAP,
        zero_stage_predictor_mro=[c.__module__+'.'+c.__qualname__ for c in _MRO],
        zero_stage_predictor_scope='Native steps beginning with any present LINEAR0<=h<=1e-24 allocation use the maintained zero-increment collocation guess by temporarily setting native sol=None. New native dense output is retained on success; the prior dense object is restored on failure/exception. No native stock, error-history, Jacobian/LU, physical RHS, error tolerance, endpoint/domain/census guard or machine-epsilon-squared dense budget is changed. Conditioned accepted root guards and failed-trial counters/rollback remain in the verified MRO. No exact-flow, global-trajectory or rare-lineage accuracy guarantee.')
    return result


def integrate_finite(y0, p, years, process=Census(), **kwargs):
    return integrate(y0, p, years, census=process, **kwargs)
