"""Read-only synthesis of the two completed nonspatial cycle controls."""
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
from terra_prisca.haze_world import dormancy_radau_experiments as runner
from dormancy_extended_cycle_check import complete_cycle_mean

HERE=Path(__file__).parent
ROOT=runner.base.e.ROOT


def digest(path):return sha256(Path(path).read_bytes()).hexdigest()


def main():
    rows=[]
    for key in ('0126','0024'):
        compact_path=HERE/f'dormancy126_cycle_{key}.json';compact=json.loads(compact_path.read_text());receipt=ROOT/compact['full_receipt']
        if digest(receipt)!=compact['full_receipt_sha256']:raise RuntimeError('Changed full continuation receipt')
        record=json.loads(receipt.read_text());payload=ROOT/record['raw_file']
        if digest(payload)!=record['raw_sha256'] or record['status']!='completed':raise RuntimeError('Changed or incomplete continuation')
        if record['protocol']['source_sha256']!=runner.sources():raise RuntimeError('Changed continuation sources')
        p=runner.base.parameters(runner.base.Case(**record['protocol']['case']))
        with np.load(payload) as d:data={k:d[k].copy() for k in ('t','y')}
        metadata=record['metadata'];stats=metadata['positive_dense_stats'][0]
        root=record['mixed_equilibrium'];row=dict(case_id=f'dormancy_{key}',case=record['protocol']['case'],status=record['status'],wall_seconds=record['wall_seconds'],receipt=str(receipt.relative_to(ROOT)),receipt_sha256=digest(receipt),payload_sha256=digest(payload),native_settling_status=record['native_settling_status'],native_windows=record['native_windows'],control_window=record['control_window'],matched_cadence_control=record['control_matched_cadence_window'],native_matched_window=record['native_matched_window'],maximum_common_temperature_difference_k=record['maximum_common_temperature_difference_k'],rms_common_temperature_difference_k=record['rms_common_temperature_difference_k'],control_minimum_log10_cells=record['control_minimum_log10_cells'],control_culls=len(record['control_culls']),dense_extensions=stats['extended_pieces'],native_failures=metadata['solver_failure_retries'],positivity_retries=metadata['allocation_positivity_retries'],stage_promotions=len(metadata['stage_coordinate_switches']),stage_conditionings=len(metadata['stage_source_restarts']),chemical_conditionings=len(metadata['chemical_conditioning_events']),zero_face_evaluation_counts=metadata['zero_face_newton_stats'],initial_log_mask_loss=record['protocol']['lost_stage_log_masks'],complete_cycle_mean=complete_cycle_mean(data,p,80000.,82000.),mixed_root=root,scope='One no-refuge autonomous continuation at tighter tolerance and smaller maximum step with an independent maintained solver. No culls or interpolation extensions in the completed control. Local root stability and finite recurrence are distinct from a periodic-orbit/basin proof.')
        assert row['control_culls']==row['dense_extensions']==row['native_failures']==row['positivity_retries']==0
        assert not row['initial_log_mask_loss']
        rows.append(row)
    result=dict(checker_sha256=digest(__file__),imported_cycle_analysis_sha256=digest(HERE/'dormancy_extended_cycle_check.py'),source_sha256=runner.sources(),rows=rows,scope='Two independently continued nonspatial cycle candidates, at L=.002/h and L=.001/h. Native labels remain unsettled; no global basin, Hopf, Floquet or asymptotic limit-cycle claim.')
    HERE.joinpath('dormancy126_cycle_comparison.json').write_text(runner.base.e.dumps(result)+'\n')
    print(json.dumps([dict(case_id=r['case_id'],cycle_mean=r['complete_cycle_mean'],span=r['control_window']['sampled_range_k'],period=r['control_window']['period_yr'],difference=r['maximum_common_temperature_difference_k'],root_temperature=r['mixed_root']['temperature_k']) for r in rows],indent=2))


if __name__=='__main__':main()
