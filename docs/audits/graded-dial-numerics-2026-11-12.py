"""Postprocessing qualification of tight-Newton finite-input checks; no producer edits."""

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world import continuum_core as weighted
from terra_prisca.haze_world import dynamic_core as physical
from terra_prisca.haze_world import graded_acetate as acetate
from terra_prisca.haze_world import graded_dials as primary


ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def qualify(record, step, tolerance=1e-9):
    p = primary.reconstruct(record)
    y = np.asarray(record['y'])
    points = []
    for offset in (-step, step):
        climate = replace(p.base.climate, donor_flux=p.base.climate.donor_flux*np.exp(offset))
        q = replace(p, base=replace(p.base, climate=climate))
        producer = acetate if record['stage'] == 'D1' else weighted
        found = producer.equilibrium(y, q, tolerance=tolerance)
        if found is None:
            return dict(status='unresolved', step=step, solver_tolerance=tolerance, points=points)
        state = found['y']
        points.append(dict(log_input_offset=offset, temperature_k=found['t_k'],
                           root_residual=found['residual'],
                           maximum_actual_per_cell_residual=float(np.max(abs(producer.per_capita(state, q)))),
                           scaled_physical_flow_residual=float(np.max(abs(producer.physical_rhs(state, q)/physical.state_scales(state, q)))),
                           support_min_k=found['support_min_k'], support_max_k=found['support_max_k'],
                           minimum_positive_stock=float(np.min(state))))
    finite = (points[1]['temperature_k']-points[0]['temperature_k'])/(2*step)
    error = abs(finite-record['Sc'])
    return dict(status='passed' if error <= max(1e-7, .02*abs(record['Sc'])) else 'disagrees',
                step=step, solver_tolerance=tolerance, finite_Sc=finite, absolute_error=error,
                relative_error=error/abs(record['Sc']) if abs(record['Sc']) > 1e-10 else None,
                exact_zero_uses_absolute_tolerance=abs(record['Sc']) <= 1e-10, points=points)


def run(output):
    folder = ROOT/'models/haze_world/figures/graded_dials'
    manifest_path = folder/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for name, expected in manifest['source_sha256'].items():
        if digest(ROOT/name) != expected:
            raise ArithmeticError('Primary source changed: '+name)
    for name, expected in manifest['output_sha256'].items():
        if digest(folder/name) != expected:
            raise ArithmeticError('Primary output changed: '+name)
    records = json.loads((folder/'states.json').read_text())
    selected = [r for r in records if r['supply_check_status'] == 'unresolved' or r['dial'] == 0]
    rows = []
    for record in selected:
        checks = [qualify(record, step) for step in (1e-3, 3e-4)]
        rows.append(dict(branch_id=record['branch_id'], stage=record['stage'], dial=record['dial'],
                         role='zero_dial_control' if record['dial'] == 0 else 'previously_unresolved_raw_supply_check',
                         primary_supply_check_status=record['supply_check_status'], implicit_Sc=record['Sc'],
                         status='qualified_by_two_steps' if all(c['status'] == 'passed' for c in checks) else 'unresolved',
                         checks=checks))
    value = dict(scope='Postprocessing numerical qualification only; primary producer, states and predictions unchanged.',
                 original_unresolved=sum(r['supply_check_status'] == 'unresolved' for r in records),
                 checked_points=len(rows), checked_zero_dial_controls=sum(r['dial'] == 0 for r in rows),
                 qualified=sum(r['status'] == 'qualified_by_two_steps' for r in rows), records=rows,
                 source_sha256={**manifest['source_sha256'], str(Path(__file__).relative_to(ROOT)):digest(Path(__file__))},
                 input_sha256={str(manifest_path.relative_to(ROOT)):digest(manifest_path),
                               str((folder/'states.json').relative_to(ROOT)):digest(folder/'states.json')},
                 limitation='Loosening the solver stopping tolerance is explicit. Actual residuals are reported; this is not a new scientific parameter or a substitute for independent physical derivatives.')
    output.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:value[k] for k in ('original_unresolved','checked_points','checked_zero_dial_controls','qualified')}))
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_suffix('.json'))
    run(parser.parse_args().output)
