"""Tolerance-scaled chart and Newton conditioning of the frozen Radau variant.

Physical equations, error tolerances, accepted stock accounting, census and
native endpoint checks are unchanged. The matrix face is an approximate Newton
matrix, not a modification of the returned ODE or an accuracy bound for rare
lineages. All earlier numerical producers remain separate and unchanged.
"""

import ast
from copy import deepcopy
from hashlib import sha256
import inspect
from types import SimpleNamespace

import numpy as np

from . import dormancy_radau_integration as upstream

Census = upstream.Census
stage = upstream.stage
ROOT_ABSOLUTE_TOLERANCE = 1e-12
LINEAR_ALLOCATION_CAP = ROOT_ABSOLUTE_TOLERANCE**2
REFERENCE_MAX_STEP_YR = 10.
LINEAR_RATE_CAP_YR = LINEAR_ALLOCATION_CAP/REFERENCE_MAX_STEP_YR


class _Coordinates(upstream._Coordinates):
    def __init__(self, initial, p):
        super().__init__(initial, p)
        self.tolerance_conditioning_requests = []
        self.tolerance_conditioning_stats = dict(
            jacobian_calls=0, face_visits=0, faces={},
            promotion_gate_calls=0, suppressed_promotions=0,
            suppressed_by_index={})


def _promotion_allowed(coords, state, index, time):
    stats = coords.tolerance_conditioning_stats
    stats['promotion_gate_calls'] += 1
    if state[index] > LINEAR_ALLOCATION_CAP:
        return True
    stats['suppressed_promotions'] += 1
    entry = stats['suppressed_by_index'].setdefault(int(index), dict(
        calls=0, first_time_yr=float(time)))
    entry.update(calls=entry['calls']+1, last_time_yr=float(time),
                 last_linear_allocation=float(state[index]))
    return False


def _promotion_target(tree):
    return [node for node in ast.walk(tree) if isinstance(node, ast.If)
            and len(node.body) == 1 and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Call)
            and ast.unparse(node.body[0].value) == 'stage_promotions.append(index)']


def _conditioned_driver(function):
    source = inspect.getsource(function)
    original = ast.parse(source)
    modified = deepcopy(original)
    targets = _promotion_target(modified)
    if len(targets) != 1:
        raise RuntimeError('Expected exactly one frozen stage-promotion predicate')
    target = targets[0]
    old_predicate = ast.dump(target.test, include_attributes=False)
    target.test = ast.BoolOp(op=ast.And(), values=[target.test,
        ast.Call(func=ast.Name(id='_promotion_allowed', ctx=ast.Load()),
                 args=[ast.Name(id=name, ctx=ast.Load())
                       for name in ('coords', 'accepted', 'index', 'end')], keywords=[])])
    ast.fix_missing_locations(modified)
    restored = deepcopy(modified)
    _promotion_target(restored)[0].test = _promotion_target(restored)[0].test.values[0]
    if ast.dump(restored, include_attributes=False) != ast.dump(original, include_attributes=False):
        raise RuntimeError('Conditioned driver changed more than one predicate')
    original_dump = ast.dump(original, include_attributes=False)
    modified_dump = ast.dump(modified, include_attributes=False)
    provenance = dict(transformation='one_stage_promotion_predicate_and_linear_cap',
        target_count=1, restored_ast_identical=True,
        frozen_source_sha256=sha256(source.encode()).hexdigest(),
        frozen_ast_sha256=sha256(original_dump.encode()).hexdigest(),
        conditioned_ast_sha256=sha256(modified_dump.encode()).hexdigest(),
        old_predicate=old_predicate,
        conditioned_predicate=ast.dump(target.test, include_attributes=False))
    namespace = function.__globals__.copy()
    namespace['_promotion_allowed'] = _promotion_allowed
    exec(compile(modified, '<dormancy_tolerance_conditioned_driver>', 'exec'), namespace)
    return namespace[function.__name__], provenance


def _condition_matrix(time, state, coords, matrix):
    stats = coords.tolerance_conditioning_stats
    stats['jacobian_calls'] += 1
    physical, _ = coords.decode(state)
    flux = stage.model.fluxes(physical, coords.p, trial_extension=True)
    for group in coords.groups:
        if not group['present']:
            continue
        h, _ = coords.allocations(state, group)
        growth = np.array([flux['net_growth_yr'][j, group['guild']] if s == 0
                           else -flux['dormant_loss_yr'] for j, s in group['nodes']])
        mean = float(h@growth/sum(h))
        q = group['migration'].copy()
        for a, (j, s) in enumerate(group['nodes']):
            for b, (k, other) in enumerate(group['nodes']):
                if j == k and s != other:
                    q[a, b] = flux['sigma_yr'][j, group['guild']] if s == 0 else flux['rho_yr'][j, group['guild']]
        rates = h*(growth-mean)+q.T@h-q.sum(axis=1)*h
        for a, index in enumerate(group['indices']):
            if coords.stage_positive[index] or not (0. <= h[a] <= LINEAR_ALLOCATION_CAP
                                                    and abs(rates[a]) <= LINEAR_RATE_CAP_YR):
                continue
            diagonal = matrix[index, index]
            removed = max(float(np.max(abs(np.delete(matrix[index, :], index)))),
                          float(np.max(abs(np.delete(matrix[:, index], index)))))
            matrix[index, :] = 0.
            matrix[:, index] = 0.
            matrix[index, index] = diagonal
            stats['face_visits'] += 1
            entry = stats['faces'].setdefault(int(index), dict(
                calls=0, first_time_yr=float(time), maximum_removed_offdiagonal=0.))
            entry.update(calls=entry['calls']+1, last_time_yr=float(time),
                last_linear_allocation=float(h[a]), last_pure_linear_rate_yr=float(rates[a]),
                last_retained_diagonal=float(diagonal),
                maximum_removed_offdiagonal=max(entry['maximum_removed_offdiagonal'], removed))
    return matrix


class _Radau(upstream._Radau):
    def _chemical_jacobian(self, time, state):
        return _condition_matrix(time, state, self.coordinates,
                                 super()._chemical_jacobian(time, state))

    def _step_impl(self):
        accepted = self.y.copy()
        accepted.setflags(write=False)
        accepted_time = float(self.t)
        for group in self.coordinates.groups:
            if not group['present']:
                continue
            for index in group['indices']:
                if self.coordinates.stage_positive[index] and abs(accepted[index]) <= ROOT_ABSOLUTE_TOLERANCE:
                    error = stage._StageSourceOverflow(int(index))
                    error.stage_cause = dict(kind='accepted_root_at_or_below_frozen_root_atol',
                        state_index=int(index), accepted_time_yr=accepted_time,
                        accepted_coordinate_sha256=sha256(accepted.tobytes()).hexdigest(),
                        accepted_root=float(accepted[index]),
                        frozen_root_absolute_tolerance=ROOT_ABSOLUTE_TOLERANCE,
                        immutable_accepted_snapshot=True,
                        handler='unchanged_accepted_driver_condition_stage')
                    self.coordinates.tolerance_conditioning_requests.append(error.stage_cause)
                    raise error
        return super()._step_impl()


def integrate(y0, p, years, **kwargs):
    accepted_driver, provenance = _conditioned_driver(stage._accepted_integrate)
    proxy = SimpleNamespace(_accepted_integrate=accepted_driver,
                            integrate=stage.integrate, chemical=stage.chemical)
    instances = []

    def coordinates(initial, parameters):
        value = _Coordinates(initial, parameters)
        instances.append(value)
        return value

    namespace = upstream.integrate.__globals__.copy()
    namespace.update(stage=proxy, _Coordinates=coordinates, _Radau=_Radau)
    function = stage.chemical._copied(upstream.integrate, namespace)
    try:
        result = function(y0, p, years, **kwargs)
    except RuntimeError as error:
        error.tolerance_conditioning_stats = [c.tolerance_conditioning_stats for c in instances]
        error.tolerance_conditioning_requests = [c.tolerance_conditioning_requests for c in instances]
        error.tolerance_conditioning_ast = provenance
        raise
    prior_scope = result.metadata['positive_dense_scope']
    scope_prefix = 'Maintained Radau; unchanged frozen RHS/driver/charts/census/tolerances.'
    assert prior_scope.startswith(scope_prefix)
    result.metadata.update(
        numerical_variant='radau_dormancy_tolerance_conditioning',
        upstream_numerical_variant='radau_dormancy_positive_dense',
        tolerance_conditioning_stats=[c.tolerance_conditioning_stats for c in instances],
        tolerance_conditioning_requests=[c.tolerance_conditioning_requests for c in instances],
        tolerance_conditioning_ast=provenance,
        tolerance_conditioning_constants=dict(
            frozen_root_absolute_tolerance=ROOT_ABSOLUTE_TOLERANCE,
            linear_allocation_cap=LINEAR_ALLOCATION_CAP,
            original_grid_max_step_yr=REFERENCE_MAX_STEP_YR,
            pure_linear_rate_cap_yr=LINEAR_RATE_CAP_YR),
        tolerance_conditioning_scope='Fixed tolerance-scaled chart selection and approximate Newton matrix only. Present linear0<=h<=1e-24 and abs(pure returned linear float rate)<=1e-25/yr gates zero offdiagonal row/column couplings and retain own diagonal. No physical source, stock floor, error-tolerance or census change. Existing typed chart conversion acts on immutable accepted pre-step snapshots; all stock-preservation events retain the frozen ledger. No universal reliability, rare-lineage or log-probability accuracy claim.',
        upstream_positive_dense_scope=prior_scope,
        positive_dense_scope='Maintained Radau; unchanged frozen RHS/census/tolerances, native endpoint checks and positive-dense certificates; charts and approximate Newton matrix use the separately recorded tolerance-conditioning rule.'+prior_scope[len(scope_prefix):])
    return result


def integrate_finite(y0, p, years, process=Census(), **kwargs):
    return integrate(y0, p, years, census=process, **kwargs)
