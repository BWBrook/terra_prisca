"""Native Newton roundoff-stagnation qualification with existing strict guards.

The predictor and certified terminal-dense variants are composed unchanged.
Only a nonconverged native collocation solve can request one extra correction,
using its actual W/Z/LU. Acceptance requires the original Newton tolerance and
64-spacing bounds on both represented ODE stages and decoded physical stocks.
Native local-error, endpoint, domain, census and rollback checks still apply.
"""

import ast
from hashlib import sha256
import inspect
from types import FunctionType, SimpleNamespace

import numpy as np
from scipy.integrate import Radau

from . import dormancy_predictor_integration as predictor
from . import dormancy_terminal_integration as terminal

conditioned = predictor.conditioned
upstream = predictor.upstream
stage = predictor.stage
Census = predictor.Census
SPACING_MULTIPLIER = 64
_NATIVE_STEP = Radau._step_impl
_NATIVE_SOLVE = _NATIVE_STEP.__globals__['solve_collocation_system']
_NATIVE = _NATIVE_SOLVE.__globals__


class _Coordinates(predictor._Coordinates, terminal._Coordinates):
    def __init__(self, initial, p):
        super().__init__(initial, p)
        self.roundoff_stagnation_stats = dict(attempts=0, accepted=0, declined={},
            extra_correction_exceptions=0, accepted_events=[])


def _spacing_report(old, new):
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        magnitude = np.maximum(abs(old), abs(new))
        spacing = np.spacing(magnitude)
        spacing[magnitude == 0.] = np.nextafter(0., 1.)
        delta = abs(new-old)
        limit = SPACING_MULTIPLIER*spacing
        ratio = delta/spacing
    finite = all(np.all(np.isfinite(value)) for value in (old, new, spacing, delta, limit))
    if not finite:
        return False, dict(finite=False)
    at = np.unravel_index(np.argmax(ratio), ratio.shape)
    return bool(np.all(delta <= limit)), dict(finite=True, worst_stage=int(at[0]),
        worst_index=int(at[1]), old_value=float(old[at]), new_value=float(new[at]),
        absolute_update=float(delta[at]), machine_spacing=float(spacing[at]),
        maximum_update_spacings=float(ratio[at]))


def _qualify_update(y, Z, proposed_Z, dW, scale, tol, coords):
    if not np.isfinite(tol) or tol < 0 or np.any(scale <= 0):
        return False, 'invalid_native_tolerance_or_scale', {}
    if any(np.any(~np.isfinite(value)) for value in (y, Z, proposed_Z, dW, scale)):
        return False, 'nonfinite_correction_or_state', {}
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        correction_norm = float(_NATIVE['norm'](dW/scale))
    if not np.isfinite(correction_norm):
        return False, 'nonfinite_correction_norm', {}
    coordinate_ok, coordinate = _spacing_report(y+Z, y+proposed_Z)
    event = dict(correction_norm=correction_norm, native_newton_tolerance=float(tol),
                 coordinate_update=coordinate)
    if not coordinate['finite']:
        return False, 'nonfinite_represented_stages', event
    try:
        old_physical = np.asarray([coords.decode(y+z)[0] for z in Z])
        new_physical = np.asarray([coords.decode(y+z)[0] for z in proposed_Z])
    except (RuntimeError, ValueError, FloatingPointError):
        return False, 'physical_decode_error', event
    physical_ok, physical = _spacing_report(old_physical, new_physical)
    event['physical_update'] = physical
    if not physical['finite']:
        return False, 'nonfinite_decoded_physical_stages', event
    if correction_norm > tol:
        return False, 'native_absolute_norm', event
    if not coordinate_ok:
        return False, 'coordinate_spacing', event
    if not physical_ok:
        return False, 'physical_spacing', event
    return True, 'accepted_roundoff_stagnation', event


def _finish(coords, converged, iterations, Z, rate, fun, time, y, h, W, scale, tol,
            LU_real, LU_complex, solve_lu):
    original = (converged, iterations, Z, rate)
    if converged or iterations < 2:
        return original
    stats = coords.roundoff_stagnation_stats
    stats['attempts'] += 1

    def decline(reason):
        stats['declined'][reason] = stats['declined'].get(reason, 0)+1
        return original

    if (not np.isfinite(time) or not np.isfinite(h) or h == 0
        or rate is not None and not np.isfinite(rate)
        or any(np.any(~np.isfinite(value)) for value in (y, Z, W, scale))):
        return decline('nonfinite_native_state_or_step')
    try:
        F = np.asarray([fun(time+h*c, y+z) for c, z in zip(_NATIVE['C'], Z)])
        if np.any(~np.isfinite(F)):
            return decline('nonfinite_recomputed_rhs')
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            real_residual = F.T.dot(_NATIVE['TI_REAL'])-_NATIVE['MU_REAL']/h*W[0]
            complex_residual = F.T.dot(_NATIVE['TI_COMPLEX'])-_NATIVE['MU_COMPLEX']/h*(W[1]+1j*W[2])
            real = solve_lu(LU_real, real_residual)
            complex_ = solve_lu(LU_complex, complex_residual)
            dW = np.asarray([real, complex_.real, complex_.imag])
            proposed_Z = _NATIVE['T'].dot(W+dW)
    except BaseException:
        stats['extra_correction_exceptions'] += 1
        raise
    qualified, reason, event = _qualify_update(y, Z, proposed_Z, dW, scale, tol, coords)
    if not qualified:
        return decline(reason)
    stats['accepted'] += 1
    event.update(time_yr=float(time), step_yr=float(h), original_native_iterations=int(iterations),
                 original_native_rate=None if rate is None else float(rate),
                 accepted_native_iterations=int(iterations+1))
    stats['accepted_events'].append(event)
    return True, iterations+1, proposed_Z, rate


def _collocation_template():
    source = inspect.getsource(_NATIVE_SOLVE)
    original = ast.parse(source)
    tree = ast.parse(source)
    returns = [node for node in ast.walk(tree) if isinstance(node, ast.Return)]
    if len(returns) != 1 or ast.unparse(returns[0].value) != '(converged, k + 1, Z, rate)':
        raise RuntimeError('Frozen collocation return changed')
    old_value = returns[0].value
    returns[0].value = ast.Call(func=ast.Name(id='_finish', ctx=ast.Load()),
        args=[ast.Name(id='converged', ctx=ast.Load()),
              ast.BinOp(left=ast.Name(id='k', ctx=ast.Load()), op=ast.Add(), right=ast.Constant(1)),
              *[ast.Name(id=name, ctx=ast.Load()) for name in
                ('Z','rate','fun','t','y','h','W','scale','tol','LU_real','LU_complex','solve_lu')]], keywords=[])
    ast.fix_missing_locations(tree)
    transformed = ast.dump(tree, include_attributes=False)
    replacement = returns[0].value
    returns[0].value = old_value
    if ast.dump(tree, include_attributes=False) != ast.dump(original, include_attributes=False):
        raise RuntimeError('Collocation transform changed more than one return')
    returns[0].value = replacement
    namespace = _NATIVE.copy()
    exec(compile(tree, '<dormancy_roundoff_collocation_return>', 'exec'), namespace)
    return namespace[_NATIVE_SOLVE.__name__], dict(return_count=1, restored_ast_identical=True,
        frozen_source_sha256=sha256(source.encode()).hexdigest(),
        transformed_ast_sha256=sha256(transformed.encode()).hexdigest())


_TEMPLATE, _TRANSFORM = _collocation_template()


class _CollocationInjected(Radau):
    def _step_impl(self):
        namespace = _TEMPLATE.__globals__.copy()
        namespace['_finish'] = lambda *args: _finish(self._predictor_coordinates, *args)
        solver = stage.chemical._copied(_TEMPLATE, namespace)
        namespace = _NATIVE_STEP.__globals__.copy()
        namespace['solve_collocation_system'] = solver
        return stage.chemical._copied(_NATIVE_STEP, namespace)(self)


class _NativeRoundoff(predictor._NativeRadau, _CollocationInjected):
    pass


_INJECTED_GLOBALS = predictor._InjectedNative._step_impl.__globals__.copy()
_INJECTED_GLOBALS['_NativeRadau'] = _NativeRoundoff


class _InjectedBackend(upstream._Radau):
    _step_impl = FunctionType(predictor._InjectedNative._step_impl.__code__, _INJECTED_GLOBALS,
        predictor._InjectedNative._step_impl.__name__, predictor._InjectedNative._step_impl.__defaults__,
        predictor._InjectedNative._step_impl.__closure__)


class _Radau(conditioned._Radau, _InjectedBackend):
    _dense_output_impl = terminal._Radau._dense_output_impl


if (_NativeRoundoff._step_impl is not predictor._NativeRadau._step_impl
    or not _NativeRoundoff.__mro__.index(predictor._NativeRadau) < _NativeRoundoff.__mro__.index(_CollocationInjected) < _NativeRoundoff.__mro__.index(Radau)
    or _Radau._step_impl is not conditioned._Radau._step_impl
    or not _Radau.__mro__.index(conditioned._Radau) < _Radau.__mro__.index(_InjectedBackend) < _Radau.__mro__.index(upstream._Radau)):
    raise RuntimeError('Roundoff adapter must retain predictor and accepted-root guards')


def integrate(y0, p, years, **kwargs):
    instances = []

    def coordinates(initial, parameters):
        value = _Coordinates(initial, parameters)
        instances.append(value)
        return value

    namespace = terminal.integrate.__globals__.copy()
    namespace.update(conditioned=SimpleNamespace(integrate=predictor.integrate),
                     _Coordinates=coordinates, _Radau=_Radau)
    function = stage.chemical._copied(terminal.integrate, namespace)
    try:
        result = function(y0, p, years, **kwargs)
    except RuntimeError as error:
        error.roundoff_stagnation_stats = [c.roundoff_stagnation_stats for c in instances]
        raise
    result.metadata.update(numerical_variant='radau_dormancy_roundoff_stagnation',
        upstream_numerical_variant='radau_dormancy_zero_stage_predictor',
        terminal_budget_variant='radau_dormancy_terminal_dense_budget',
        roundoff_stagnation_stats=[c.roundoff_stagnation_stats for c in instances],
        roundoff_stagnation_transform=_TRANSFORM,
        roundoff_stagnation_native_mro=[c.__module__+'.'+c.__qualname__ for c in _NativeRoundoff.__mro__],
        roundoff_stagnation_backend_mro=[c.__module__+'.'+c.__qualname__ for c in _Radau.__mro__],
        roundoff_stagnation_scope='Only nonconverged native solves after>=2 iterations attempt one correction with actual W/Z/LU/state/scale. Acceptance requires native correction norm<=unchanged Newton tolerance and every represented ODE stage coordinate and decoded physical-stock update<=64 machine spacings; nonfinite values never qualify. Original return objects are retained otherwise. Events count qualified collocation corrections, including trials later rejected or truncated. Native local-error, endpoint, domain/census, error-history and rollback logic remain unchanged. Predictor and reviewed terminal budget compose without relaxing any rare/uncensored/two-guild dense bound. No root, exact-flow, global-trajectory or rare-lineage error guarantee.')
    return result


def integrate_finite(y0, p, years, process=Census(), **kwargs):
    return integrate(y0, p, years, census=process, **kwargs)
