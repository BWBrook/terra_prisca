"""Native Newton roundoff-stagnation qualification with existing strict guards.

The predictor and certified terminal-dense variants are composed unchanged.
Only a nonconverged native collocation solve can request one extra correction,
using its actual W/Z/LU. Acceptance requires the original Newton tolerance and
64-spacing bounds on both represented ODE stages and decoded physical stocks.
Native local-error, endpoint, domain, census and rollback checks still apply.
"""

import ast
from fractions import Fraction
from hashlib import sha256
import inspect
from types import FunctionType, SimpleNamespace

import numpy as np
from scipy.integrate import Radau
from scipy.integrate._ivp.radau import RadauDenseOutput

from . import dormancy_predictor_integration as predictor
from . import dormancy_terminal_integration as terminal

conditioned = predictor.conditioned
upstream = predictor.upstream
stage = predictor.stage
Census = predictor.Census
SPACING_MULTIPLIER = 64
NEWTON_QUALIFICATION = 'strict037_then_certified_terminal_dormant_absolute_v1'
ABSOLUTE_DORMANT_CAP = conditioned.LINEAR_ALLOCATION_CAP
_NATIVE_STEP = Radau._step_impl
_NATIVE_SOLVE = _NATIVE_STEP.__globals__['solve_collocation_system']
_NATIVE = _NATIVE_SOLVE.__globals__


class _Coordinates(predictor._Coordinates, terminal._Coordinates):
    def __init__(self, initial, p):
        super().__init__(initial, p)
        self.roundoff_stagnation_stats = dict(attempts=0, accepted=0, declined={},
            extra_correction_exceptions=0, accepted_events=[])
        self.absolute_resolution_stats = dict(attempts=0, qualified=0, declined={},
            summed_local_represented_cell_change_upper=0.,
            summed_local_represented_cell_change_exact=upstream._ratio(Fraction(0)))
        self._absolute_cell_change_sum = Fraction(0)


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


def _terminal_face(coords):
    if not getattr(coords, 'terminal_census_active', False):
        return False
    process = coords.dense_census
    if process.minimum_cells != 1. or process.census_yr != 10.:
        return False
    if np.count_nonzero(coords.p.weights > 0) != 1:
        return False
    return sum(bool(group['present']) for group in coords.groups) == 1


def _unit_coordinate_report(old, new):
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        magnitude = np.maximum(1., np.maximum(abs(old), abs(new)))
        spacing = np.spacing(magnitude)
        delta = abs(new-old)
        ratio = delta/spacing
    if not all(np.all(np.isfinite(value)) for value in (old, new, spacing, delta)):
        return False, dict(finite=False)
    at = np.unravel_index(np.argmax(ratio), ratio.shape)
    return bool(np.all(delta <= SPACING_MULTIPLIER*spacing)), dict(finite=True,
        worst_stage=int(at[0]), worst_index=int(at[1]), old_value=float(old[at]),
        new_value=float(new[at]), absolute_update=float(delta[at]),
        unit_scaled_machine_spacing=float(spacing[at]), maximum_update_spacings=float(ratio[at]))


def _log_report(old, new):
    if np.any(np.isnan(old) | np.isposinf(old) | np.isnan(new) | np.isposinf(new)):
        return False, dict(finite=False, finite_mask_unchanged=False)
    mask = np.isfinite(old)
    if not np.array_equal(mask, np.isfinite(new)):
        return False, dict(finite=True, finite_mask_unchanged=False)
    if not np.any(mask):
        return True, dict(finite=True, finite_mask_unchanged=True, maximum_update_spacings=0.)
    okay, report = _spacing_report(old[mask][None, :], new[mask][None, :])
    report['finite_mask_unchanged'] = True
    if report['finite']:
        report['worst_location'] = np.argwhere(mask)[report['worst_index']].tolist()
    return okay, report


def _exact_ratio(value):
    return Fraction(int(value['n'], 16), int(value['d'], 16))


def _absolute_qualification(y, Z, proposed_Z, scale, tol, coords, time, h,
                            component_atol, strict, candidates):
    stats = coords.absolute_resolution_stats
    stats['attempts'] += 1

    def decline(reason):
        stats['declined'][reason] = stats['declined'].get(reason, 0)+1
        return strict

    if not np.isfinite(time) or not np.isfinite(h) or h <= 0 or time+h == time:
        return decline('invalid_step_context')
    if component_atol is None:
        return decline('native_component_atol_unavailable')
    if strict[2]['correction_norm'] > tol:
        return decline('native_absolute_norm')
    old_coordinates, new_coordinates = y+Z, y+proposed_Z
    coordinate_ok, coordinate = _unit_coordinate_report(old_coordinates, new_coordinates)
    if not coordinate_ok:
        return decline('unit_scaled_coordinate_spacing')
    try:
        old_decoded = [coords.decode(value) for value in old_coordinates]
        new_decoded = [coords.decode(value) for value in new_coordinates]
    except (RuntimeError, ValueError, FloatingPointError):
        return decline('physical_decode_error')
    old_physical = np.asarray([value[0] for value in old_decoded])
    new_physical = np.asarray([value[0] for value in new_decoded])
    old_logs = np.asarray([value[1] for value in old_decoded])
    new_logs = np.asarray([value[1] for value in new_decoded])
    if (np.any(~np.isfinite(old_physical)) or np.any(~np.isfinite(new_physical))
        or np.any(np.isnan(old_logs) | np.isposinf(old_logs) | np.isnan(new_logs) | np.isposinf(new_logs))):
        return decline('nonfinite_decoded_stock_or_log')
    mask = np.isfinite(old_logs)
    if not np.array_equal(mask, np.isfinite(new_logs)):
        return decline('finite_stage_log_mask_changed')
    proofs = []
    for values in (Z, proposed_Z):
        native = RadauDenseOutput(time, time+h, y.copy(), values.T.dot(_NATIVE['P']))
        proof, reason = terminal._terminal_certificate(native, y+values[-1], coords)
        if proof is None:
            return decline('macro_certificate_'+reason)
        proofs.append(proof)
    conversion = _exact_ratio(proofs[0]['volume_conversion_exact'])
    if conversion != _exact_ratio(proofs[1]['volume_conversion_exact']):
        return decline('volume_conversion_mismatch')
    atol = np.broadcast_to(np.asarray(component_atol), y.shape)
    exemptions = []
    local_bound = Fraction(0)
    for index, patch, guild, differences, old_h, new_h, group in candidates:
        if not np.all(mask[:, patch, guild, 1]):
            continue
        if not np.isfinite(atol[index]) or atol[index] <= 0:
            continue
        declared = upstream._f(atol[index])
        physical_delta = [abs(upstream._f(b)-upstream._f(a))
                          for a, b in zip(old_physical[:, index], new_physical[:, index])]
        converted, cell_scales = [], []
        position = list(group['indices']).index(index)
        for a in range(3):
            density = []
            for values, represented in ((old_coordinates, old_physical), (new_coordinates, new_physical)):
                raw = coords.allocations(values[a], group)[0]
                normalizer = sum(map(upstream._f, raw), Fraction(0))
                total = sum((upstream._f(w)*upstream._f(represented[a, ix])
                             for w, ix in zip(group['weights'], group['indices'])), Fraction(0))
                if normalizer <= 0 or total <= 0:
                    return decline('invalid_composition_scale')
                density.append(total/normalizer/upstream._f(group['weights'][position]))
            converted.append(declared*min(density))
            cell_scales.append(upstream._f(ABSOLUTE_DORMANT_CAP)*max(density)*conversion)
        if not all(delta <= declared and delta <= limit for delta, limit in zip(physical_delta, converted)):
            continue
        cell_delta = [delta*conversion for delta in physical_delta]
        local_bound += max(cell_delta)
        exemptions.append(dict(index=index, patch=patch, guild=guild, pool='dormant',
            old_raw_allocations=old_h.tolist(), new_raw_allocations=new_h.tolist(),
            allocation_correction_exact=[upstream._ratio(delta) for delta in differences],
            allocation_correction_upper=[upstream._upper(delta) for delta in differences],
            frozen_root_atol_squared_exact=upstream._ratio(upstream._f(ABSOLUTE_DORMANT_CAP)),
            native_component_atol_numeric=float(atol[index]),
            native_component_atol_units='normalized allocation coordinate',
            requested_numeric_physical_bound_exact=upstream._ratio(declared),
            conservatively_converted_physical_atol_exact=[upstream._ratio(value) for value in converted],
            represented_physical_cell_change_exact=[upstream._ratio(value) for value in cell_delta],
            represented_physical_cell_change_upper=[upstream._upper(value) for value in cell_delta],
            root_cap_composition_cell_scale_upper=[upstream._upper(value) for value in cell_scales],
            abundance_and_own_stage_log_precision='unresolved_absolute_composition'))
    if not exemptions:
        return decline('no_dormant_pool_passes_physical_atol')
    exempt = {entry['index'] for entry in exemptions}
    resolved = [index for index in range(coords.m) if index not in exempt]
    physical_ok, physical = _spacing_report(old_physical[:, resolved], new_physical[:, resolved])
    if not physical_ok:
        return decline('resolved_physical_spacing')
    physical['worst_resolved_physical_index'] = resolved[physical['worst_index']]
    resolved_mask = mask.copy()
    for entry in exemptions:
        resolved_mask[:, entry['patch'], entry['guild'], 1] = False
    if np.any(resolved_mask):
        log_ok, logs = _spacing_report(old_logs[resolved_mask][None, :], new_logs[resolved_mask][None, :])
        if not log_ok:
            return decline('resolved_stage_log_spacing')
        logs['worst_location'] = np.argwhere(resolved_mask)[logs['worst_index']].tolist()
    else:
        logs = dict(finite=True, maximum_update_spacings=0.)
    old_global = np.asarray([[np.dot(coords.p.weights, value[coords.p.biomass_indices[:, guild]]+
                                      value[coords.p.dormant_indices[:, guild]]) for guild in range(2)] for value in old_physical])
    new_global = np.asarray([[np.dot(coords.p.weights, value[coords.p.biomass_indices[:, guild]]+
                                      value[coords.p.dormant_indices[:, guild]]) for guild in range(2)] for value in new_physical])
    global_ok, global_mass = _spacing_report(old_global, new_global)
    if not global_ok:
        return decline('global_biomass_spacing')
    global_log_ok, global_logs = _log_report(
        np.asarray([coords.global_logs(value) for value in old_coordinates]),
        np.asarray([coords.global_logs(value) for value in new_coordinates]))
    if not global_log_ok:
        return decline('global_log_spacing_or_mask')
    event = dict(correction_norm=strict[2]['correction_norm'], native_newton_tolerance=float(tol),
        coordinate_update=coordinate, physical_update=physical, retained_log_update=logs,
        global_biomass_update=global_mass, global_log_update=global_logs,
        dormant_composition_exemptions=exemptions,
        current_and_proposed_macro_certificates=proofs,
        local_represented_cell_change_bound_exact=upstream._ratio(local_bound),
        local_represented_cell_change_bound_upper=upstream._upper(local_bound),
        newton_qualification=NEWTON_QUALIFICATION,
        original_strict037_decline=strict[1])
    stats['qualified'] += 1
    coords._absolute_cell_change_sum += local_bound
    stats['summed_local_represented_cell_change_exact'] = upstream._ratio(coords._absolute_cell_change_sum)
    stats['summed_local_represented_cell_change_upper'] = upstream._upper(coords._absolute_cell_change_sum)
    return True, 'accepted_terminal_dormant_absolute_resolution', event


def _qualified_update(y, Z, proposed_Z, dW, scale, tol, coords, time, h, component_atol):
    strict = _qualify_update(y, Z, proposed_Z, dW, scale, tol, coords)
    if strict[0] or strict[1] not in ('coordinate_spacing', 'physical_spacing'):
        return strict
    if not _terminal_face(coords):
        return strict
    old, new = y+Z, y+proposed_Z
    cap = upstream._f(ABSOLUTE_DORMANT_CAP)
    candidates = []
    for group in coords.groups:
        if not group['present']:
            continue
        for index, (patch, pool) in zip(group['indices'], group['nodes']):
            if pool != 1 or coords.stage_positive[index]:
                continue
            a, b = old[:, index], new[:, index]
            if not (np.all(a > 0.) and np.all(b > 0.) and np.all(a <= ABSOLUTE_DORMANT_CAP)
                    and np.all(b <= ABSOLUTE_DORMANT_CAP)):
                continue
            differences = [abs(upstream._f(v)-upstream._f(u)) for u, v in zip(a, b)]
            if all(value <= cap for value in differences):
                candidates.append((int(index), patch, group['guild'], differences, a, b, group))
    if not candidates:
        return strict
    return _absolute_qualification(y, Z, proposed_Z, scale, tol, coords, time, h,
                                    component_atol, strict, candidates)


_STRICT037_IDENTITY = dict(source_commit='0455d15',
    helper_sha256='037761c4293b103eb44dee0a798a02d2c91b48faf53a03fdde47fb5b0f8f2369',
    qualifier_source_sha256='415ae2c8bd1681bf61eb358de82ea9c72c5b3b1a25212183a061cdf48335573b',
    spacing_source_sha256='0f59eda1636a4a12b990412559c0a4f990a739fce1c70b2d1a4afe9ff42abfbc')
if (sha256(inspect.getsource(_qualify_update).encode()).hexdigest() != _STRICT037_IDENTITY['qualifier_source_sha256']
    or sha256(inspect.getsource(_spacing_report).encode()).hexdigest() != _STRICT037_IDENTITY['spacing_source_sha256']):
    raise RuntimeError('Pinned037 strict qualification source changed')


def _finish(coords, converged, iterations, Z, rate, fun, time, y, h, W, scale, tol,
            LU_real, LU_complex, solve_lu, *, component_atol=None):
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
    qualified, reason, event = _qualified_update(y, Z, proposed_Z, dW, scale, tol, coords,
                                               time, h, component_atol)
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
        namespace['_finish'] = lambda *args: _finish(self._predictor_coordinates, *args,
                                                    component_atol=self.atol)
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
        newton_qualification=NEWTON_QUALIFICATION,
        strict037_source_identity=_STRICT037_IDENTITY.copy(),
        absolute_resolution_stats=[c.absolute_resolution_stats for c in instances],
        roundoff_stagnation_transform=_TRANSFORM,
        roundoff_stagnation_native_mro=[c.__module__+'.'+c.__qualname__ for c in _NativeRoundoff.__mro__],
        roundoff_stagnation_backend_mro=[c.__module__+'.'+c.__qualname__ for c in _Radau.__mro__],
        roundoff_stagnation_scope='The pinned037 strict qualifier runs first and remains source-identical. Only its relative-spacing declines can try the separately named certified macroterminal dormant absolute-resolution rule. Canonical1cell/10yr, onehabitat/onepresentguild, positive tiny LINEAR dormant stage and both current/proposed whole-piece>=1e16cell proofs are required. Uncensored/two-guild/multihabitat paths exit before any additional decode/proof/RHS/state work. Native correction tolerance is unchanged; unit-scaled coordinate spacing plus all resolved physical/stage-log/global biomass/global-log64actual-spacing gates remain. Only the exempt dormant pool and own stage log are unresolved at existing root-atol² composition scale, with exact raw correction and native component-atol plus conservative physical-unit bounds. No physical/native-error/census/endpoint logic changes. Events and summed local represented-cell bounds include trial corrections later rejected/truncated and are not global or accumulated ODE error bounds. No root, exact-flow, global-trajectory or rare-lineage guarantee.')
    return result


def integrate_finite(y0, p, years, process=Census(), **kwargs):
    return integrate(y0, p, years, census=process, **kwargs)
