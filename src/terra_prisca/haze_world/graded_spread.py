"""D2: continue resolved fixed-chemistry habitats from zero spread."""

from dataclasses import replace

import numpy as np

from . import continuum_core as model
from . import continuum_experiments as measurements


def parameters(sigma, dispersal, mesh=None):
    if sigma < 0 or dispersal <= 0:
        raise ValueError('D2 uses nonnegative spread and positive dispersal')
    return measurements.parameters('fixed', .5, float(sigma), float(dispersal),
                                   mesh=mesh)


def parameters_from_record(record):
    mesh = model.Mesh(tuple(record['offsets']), tuple(record['weights']),
                      tuple(record['panels']))
    return parameters(record['sigma_k'], record['dispersal_yr'], mesh)


def _saved_state(y, p):
    return dict(y=np.asarray(y), sigma_k=p.sigma_k, dispersal_yr=p.dispersal_yr,
                offsets=p.mesh.nodes, weights=p.mesh.weights, panels=p.mesh.panels)


def _starting_state(dispersal):
    p = parameters(0., dispersal)
    choices = model.homogeneous_seeds(p)
    if len(choices) != 1:
        raise ArithmeticError('D2 needs one qualified reference mixed equilibrium')
    return _saved_state(choices[0]['y'], p)


def _target_seed(previous, target):
    old = parameters_from_record(previous)
    if target < old.sigma_k:
        raise ValueError('D2 continuation must advance from the lower dial value')
    y = np.asarray(previous['y'], float)
    if old.sigma_k == 0:
        p = parameters(target, old.dispersal_yr)
        seed = np.r_[np.tile(y[:4], p.n), y[-1]]
    else:
        if previous.get('status') == 'converged' and len(old.mesh.panels) > 5:
            edges = np.asarray(old.mesh.panels)
            mesh = model.gauss_mesh(old.sigma_k, np.unique(np.r_[edges[::2], edges[-1]]), old.mesh.order)
            coarse = replace(old, mesh=mesh)
            y = model.interpolate_state(y, old, coarse)
            old = coarse
        ratio = target / old.sigma_k
        mesh = model.Mesh(tuple(np.asarray(old.mesh.nodes) * ratio), old.mesh.weights,
                          tuple(np.asarray(old.mesh.panels) * ratio), old.mesh.order)
        p = parameters(target, old.dispersal_yr, mesh)
        seed = y.copy()
    return seed, p


def _advance(previous, target, history, depth=0, max_depth=14):
    seed, p = _target_seed(previous, target)
    found = model.equilibrium(seed, p)
    history.append(dict(from_sigma_k=float(previous['sigma_k']), to_sigma_k=target,
                        depth=depth, correction_accepted=found is not None,
                        nodes_from=len(previous['weights']), nodes_to=p.n,
                        mesh_coarsened_for_seed=p.n < len(previous['weights']),
                        residual=None if found is None else found['residual']))
    if found is not None:
        return _saved_state(found['y'], p)
    gap = target - float(previous['sigma_k'])
    if depth >= max_depth or gap <= 1e-8:
        return None
    midpoint = float(previous['sigma_k']) + gap / 2
    middle = _advance(previous, midpoint, history, depth + 1, max_depth)
    return None if middle is None else _advance(middle, target, history, depth + 1, max_depth)


def _refined_equilibrium(y, p, mesh):
    q = replace(p, mesh=mesh)
    predictor = model.interpolate_state(y, p, q)
    found = model.equilibrium(predictor, q)
    corrected = False
    if found is None:
        means = p.weights @ np.asarray(y[:-1]).reshape(p.n, 4)[:, 1:3]
        predictor = model.local_profile_correction(predictor, q, means)
        corrected = predictor is not None
        found = model.equilibrium(predictor, q) if predictor is not None else None
    return found, q, corrected


def solve_sigma(sigma, dispersal, previous_record=None):
    sigma, dispersal = float(sigma), float(dispersal)
    previous_record = _starting_state(dispersal) if previous_record is None else previous_record
    if not np.isclose(previous_record['dispersal_yr'], dispersal, rtol=0., atol=0.):
        raise ValueError('A D2 branch keeps dispersal fixed')
    common = dict(stage='D2', chemistry='fixed', fraction=.5, sigma_k=sigma,
                  dispersal_yr=dispersal, nominal_potential=.3)
    continuation = []
    continued = _advance(previous_record, sigma, continuation)
    if continued is None:
        return dict(common, status='continuation_unresolved', continuation_history=continuation,
                    branch_status='Numerical correction failed; no fold or branch loss established')
    p = parameters_from_record(continued)
    if sigma == 0:
        return dict(common, status='homogeneous_control', **measurements.measure(continued['y'], p),
                    **{k: v for k, v in continued.items() if k not in common},
                    mesh_history=[], doubling_history=[], continuation_history=continuation)
    result = model.adaptive_equilibrium(p, seed=continued['y'], max_levels=32, max_nodes=4096)
    if result.get('status') != 'logit_resolved':
        return dict(common, status='profile_unresolved', reason=result.get('status'),
                    continuation_history=continuation, mesh_history=result.get('history', []),
                    branch_status='Unresolved profile; no fold or branch loss established')
    p, y = result['p'], result['y']
    measured = measurements.measure(y, p)
    history = []
    converged = False
    reason = 'doubling_limit'
    for iteration in range(7):
        mesh, _ = model.refine_panels(y, p, force_mixed=True)
        if len(mesh.nodes) == p.n:
            edges = np.asarray(p.mesh.panels)
            mesh = model.gauss_mesh(sigma, np.sort(np.r_[edges, (edges[:-1] + edges[1:]) / 2]))
        if len(mesh.nodes) > 4096:
            reason = 'node_limit'
            break
        found, q, corrected = _refined_equilibrium(y, p, mesh)
        if found is None:
            reason = 'doubling_root_unresolved'
            break
        _, profile = model.refine_panels(found['y'], q)
        if profile['status'] != 'logit_resolved':
            found = model.adaptive_equilibrium(q, seed=found['y'], max_levels=32, max_nodes=4096)
            if found.get('status') != 'logit_resolved':
                reason = found.get('status')
                break
            q = found['p']
        current = measurements.measure(found['y'], q)
        entry = dict(iteration=iteration, nodes_before=p.n, nodes_after=q.n,
                     local_profile_correction=corrected,
                     slopes_agree=measurements.slopes_agree(measured, current),
                     lag_agrees=measurements.lag_agrees(measured['lag'], current['lag']),
                     before=measured, after=current)
        history.append(entry)
        p, y, measured = q, found['y'], current
        if entry['slopes_agree'] and entry['lag_agrees'] and current['gain'].get('frozen_fd_agrees', False):
            converged, reason = True, 'qualified'
            break
    _, zone = model.refine_panels(y, p)
    return dict(common, status='converged' if converged else 'doubling_unresolved', reason=reason,
                **measured, mixed_width_k=zone.get('mixed_width_k'),
                **{k: v for k, v in _saved_state(y, p).items() if k not in common},
                mesh_history=result.get('history', []), doubling_history=history,
                continuation_history=continuation)
