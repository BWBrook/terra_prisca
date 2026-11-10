"""Verify the fixed chemical-Jacobian prefix snapshot without new trajectories.

The raw directory must contain the named canonical prefixes and case0012.
The platform-control directory supplies the independent Linux case0010.
Recorded execution/result sidecars must also be restored under
local/haze/dormancy_trial_review. This verifies the canonical Mac snapshot's
hashes, stocks, minima, sampled redox and bounded zero-root counterexample.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import warnings

import numpy as np
from scipy.special import logsumexp

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_chemical_experiments as runner
from terra_prisca.haze_world import dormancy_chemical_integration as chemical
from terra_prisca.haze_world import dormancy_jacobian_integration as frozen
from terra_prisca.haze_world import habitat_coupling as habitat

HELPER_SHA256='75c538cb2bfabf0e8b497d6f7b60e8714ab2a69880d8836ec5201ac05b626cd1'
PREFIXES=((25,3000.,'1fc0915fecdc3ba79b632755dea21ad8383c6b47e06e49328205d863665e3842'),
          (41,15000.,'13bd6b59e5767b9ca64f40bc7080e7a8929394214632fd117a2e487459e0227d'))


def digest(path):return sha256(path.read_bytes()).hexdigest()


def synthetic():
    p=model.Dormancy(habitat.Habitats(),epsilon=.03)
    initial=model.reference_state([21.,0.,4e-4,1e-4,.195],p);initial[4]=1e-4
    c=chemical._Coordinates(initial,p);state=c.encode(initial)
    c.stage_positive[1]=True;state[1]=0.;state[3]=-3000.
    rate=frozen.frozen._Coordinates.derivative(c,0.,state)
    assert np.all(np.isfinite(rate)) and rate[1]==0. and rate[3]==-1.
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        try:frozen.coordinate_jacobian(0.,state,c)
        except frozen.guarded._InvalidTrial as error:legacy_error=repr(error)
        else:raise AssertionError('Frozen counterexample unexpectedly became finite')
    with np.errstate(over='raise',invalid='raise'):
        matrix=chemical.coordinate_jacobian(0.,state,c)
    assert np.all(np.isfinite(matrix)) and matrix[3,1]==0.
    return dict(exact_rhs_finite=True,exact_chemical_rate=float(rate[3]),
        zero_root_chemical_derivative=float(matrix[3,1]),new_matrix_finite=True,
        frozen_matrix_error=legacy_error,frozen_warning_count=len(captured))


def census_control(raw, index, fingerprint):
    case=runner.base.design()[index]
    receipt=raw/f'{case.case_id}_census_t100000-{fingerprint[:16]}.receipt.json'
    record=json.loads(receipt.read_text())
    assert record['execution_status']=='complete' and record['fingerprint']==fingerprint
    assert sha256(runner.base.e.dumps(record['protocol']).encode()).hexdigest()==fingerprint
    assert record['protocol']['source_sha256']==runner.sources()
    assert record['protocol']['solver']=='analytic_dormancy_chemical_jacobian'
    payload=raw/record['raw_file'];assert digest(payload)==record['raw_sha256']
    with np.load(payload) as data:
        metadata=json.loads(str(data['metadata']));p=runner.base.parameters(case);active=p.weights>0
        total=logsumexp(data['log_biomass'][active]+np.log(p.weights[active])[:,None,None],axis=0)
        bounds=bool(np.all(data['min_log_biomass']<=np.min(total,axis=1)+1e-10))
        nonnegative=bool(np.all(data['y']>=0.) and np.all(np.isfinite(data['y'])))
        residual=float(max(abs(model.redox_residual(y,p)) for y in data['y'][:,::100].T))
        conversions=metadata['chemical_conditioning_events']
        stocks=bool(all(e['physical_state_bitwise_preserved'] and e['inventory_before']==e['inventory_after'] for e in conversions))
        assert nonnegative and bounds and stocks and residual<1e-16 and data['t'][-1]==100000.
        return dict(status='completed_flow_control',case_id=case.case_id,years=100000,
            fingerprint=fingerprint,receipt=receipt.name,receipt_sha256=digest(receipt),
            raw_file=payload.name,raw_sha256=record['raw_sha256'],
            execution_platform={k:record['protocol'][k] for k in ('architecture','operating_system','python','packages')},
            settling_status=record['summary']['settling_status'],summary=record['summary'],
            wall_seconds=metadata['wall_seconds'],accepted_steps=metadata['accepted_steps'],nfev=metadata['nfev'],
            matrix_evaluations=metadata['newton_evaluations'],solver_failure_retries=metadata['solver_failure_retries'],
            positivity_retries=metadata['allocation_positivity_retries'],progress_restarts=metadata['native_zero_time_retries'],
            chemical_conversions=len(conversions),chemical_newton_or_arrival_requests=len(metadata['chemical_conditioning_requests']),
            stage_source_restarts=len(metadata['stage_source_restarts']),census_removals=len(json.loads(str(data['extinction_events']))),
            nonnegative_finite_stocks=nonnegative,dense_minima_bound_samples=bounds,
            all_chemical_conversions_bitwise_stock_and_inventory_preserving=stocks,max_sampled_redox_residual=residual)


def platform_comparison(raw, platform_control, linux):
    fingerprint='f7924ad5df000ba5'
    receipt=raw/f'dormancy_0010_census_t100000-{fingerprint}.receipt.json'
    historical=json.loads(receipt.read_text())
    assert historical['execution_status']=='complete'
    assert sha256(runner.base.e.dumps(historical['protocol']).encode()).hexdigest()==historical['fingerprint']
    payload=raw/historical['raw_file'];assert digest(payload)==historical['raw_sha256']
    with np.load(payload) as old_data, np.load(platform_control/linux['raw_file']) as new_data:
        common,old_ix,new_ix=np.intersect1d(old_data['t'],new_data['t'],return_indices=True)
        p=runner.base.parameters(runner.base.design()[10])
        old_t=model.core.temperature_k(old_data['y'][-1,old_ix],p.coupled.climate)
        new_t=model.core.temperature_k(new_data['y'][-1,new_ix],p.coupled.climate)
        return dict(historical_selected_fingerprint=historical['fingerprint'],historical_receipt=receipt.name,
            historical_receipt_sha256=digest(receipt),historical_raw_sha256=historical['raw_sha256'],
            historical_settling_status=historical['summary']['settling_status'],common_sample_count=len(common),
            maximum_common_temperature_difference_k=float(np.max(abs(new_t-old_t))),
            maximum_absolute_final_stock_difference=float(np.max(abs(new_data['y'][:,-1]-old_data['y'][:,-1]))),
            scope='Separate completed Linux chemical control; existing selected7046Mac receipt is retained. Strict all-stock stationarity differs; no new equilibrium claim.')


def verify(raw, platform_control):
    assert digest(Path(chemical.__file__))==HELPER_SHA256
    source=runner.sources();records=[]
    for index,years,fingerprint in PREFIXES:
        case=runner.base.design(years)[index]
        receipt=raw/f'{case.case_id}_uncensored_t{years:g}-{fingerprint[:16]}.receipt.json'
        record=json.loads(receipt.read_text())
        assert record['execution_status']=='complete' and record['fingerprint']==fingerprint
        assert sha256(runner.base.e.dumps(record['protocol']).encode()).hexdigest()==fingerprint
        assert record['protocol']['source_sha256']==source
        assert record['protocol']['solver']=='analytic_dormancy_chemical_jacobian'
        payload=raw/record['raw_file'];assert digest(payload)==record['raw_sha256']
        sidecar=runner.base.e.ROOT/'local/haze/dormancy_trial_review'/f'chemical_acceptance_{case.case_id}_uncensored_{years:g}_{fingerprint[:16]}.execution.json'
        execution=json.loads(sidecar.read_text());assert execution['fingerprint']==fingerprint
        result_sidecar=sidecar.with_name(sidecar.name.replace('.execution.json','.result.json'))
        execution_result=json.loads(result_sidecar.read_text())
        assert execution_result['status']=='completed' and execution_result['fingerprint']==fingerprint
        assert execution_result['raw_sha256']==record['raw_sha256']
        with np.load(payload) as data:
            metadata=json.loads(str(data['metadata']))
            p=runner.base.parameters(case);active=p.weights>0
            total=logsumexp(data['log_biomass'][active]+np.log(p.weights[active])[:,None,None],axis=0)
            nonnegative=bool(np.all(data['y']>=0.))
            finite=bool(np.all(np.isfinite(data['log_biomass'][active])))
            bounds=bool(np.all(data['min_log_biomass']<=np.min(total,axis=1)+1e-10))
            residual=float(max(abs(model.redox_residual(y,p)) for y in data['y'][:,::100].T))
            assert nonnegative and finite and bounds and residual<1e-16
            requests=metadata['chemical_conditioning_requests']
            charts=metadata['chemical_conditioning_events']
            assert all(e['physical_state_bitwise_preserved'] and e['inventory_before']==e['inventory_after'] for e in charts)
            records.append(dict(case_id=case.case_id,years=years,fingerprint=fingerprint,
                receipt=receipt.name,receipt_sha256=digest(receipt),
                raw_file=payload.name,raw_sha256=record['raw_sha256'],
                execution_sidecar=sidecar.name,execution_sidecar_sha256=digest(sidecar),result_sidecar=result_sidecar.name,result_sidecar_sha256=digest(result_sidecar),observer_controller_sha256=execution['controller_sha256'],controller_wall_seconds=execution_result['wall_seconds'],
                execution_platform={k:record['protocol'][k] for k in ('architecture','operating_system','python','packages')},
                wall_seconds=record['summary']['wall_seconds'],accepted_steps=metadata['accepted_steps'],
                nfev=metadata['nfev'],matrix_evaluations=metadata['newton_evaluations'],
                solver_failure_retries=metadata['solver_failure_retries'],positivity_retries=metadata['allocation_positivity_retries'],
                progress_restarts=metadata['native_zero_time_retries'],chemical_conditioning_requests=requests,
                nonnegative_stocks=nonnegative,finite_present_guild_logs=finite,dense_minima_bound_samples=bounds,
                max_sampled_redox_residual=residual,min_log_biomass=data['min_log_biomass'].tolist(),
                min_times_yr=data['min_times'].tolist(),min_log_cells=(data['min_log_biomass']+metadata['global_log_cell_conversion']).tolist()))
    pilot=census_control(raw,12,'14f5c49a3088e852d97f80363fccb5c42ba6988ea03778e4ebf7c140c0430d2a')
    full=census_control(platform_control,10,'02158faa467fa03b43b8361b339e0d35a15e23982c22da44373746160eef71ed')
    stem=runner.base.e.ROOT/'local/haze/dormancy_trial_review'/'chemical_acceptance_dormancy_0012_census_100000_14f5c49a3088e852'
    execution_path=stem.with_suffix('.execution.json');result_path=stem.with_suffix('.result.json')
    execution=json.loads(execution_path.read_text());result=json.loads(result_path.read_text())
    assert execution['fingerprint']==pilot['fingerprint'] and result['status']=='completed' and result['raw_sha256']==pilot['raw_sha256']
    pilot.update(execution_sidecar=execution_path.name,execution_sidecar_sha256=digest(execution_path),
        result_sidecar=result_path.name,result_sidecar_sha256=digest(result_path),
        observer_controller_sha256=execution['controller_sha256'],controller_wall_seconds=result['wall_seconds'])
    full['comparison_with_selected_mac']=platform_comparison(raw,platform_control,full)
    return dict(status='prefix_and_full_flow_controls_qualified_ecological_settling_unresolved',
        helper_sha256=HELPER_SHA256,source_sha256=source,checker_sha256=digest(Path(__file__)),raw_directory_layout='Receipt/payload names resolve relative to --raw-dir; execution sidecars are under local/haze/dormancy_trial_review.',synthetic_counterexample=synthetic(),prefixes=records,
        focused_tests=dict(command='uv run pytest -q tests/test_dormancy_chemical_integration.py',passed=15,
                           test_source_sha256=digest(runner.base.e.ROOT/'tests/test_dormancy_chemical_integration.py')),
        independent_review=dict(helper_sha256=HELPER_SHA256,tests_passed=15,finding='No consequential issue found in factored gauge, true linear-zero overflow, private driver composition, accepted-state cause logging or threshold-free arrival hook.'),
        census_pilot=pilot,independent_platform_census_control=full,
        scope='Two uncensored prefixes, bounded numerical controls and two completed100000-year census flows. Both chemical full-case records retain strictunsettled status; no equilibrium or grid-completion claim.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir',type=Path,default=runner.RAW)
    parser.add_argument('--platform-control-dir',type=Path,default=runner.base.e.ROOT/'local/haze/dormancy_chemical_platform_control')
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('dormancy-chemical-qualification-2026-11-11.json'))
    args=parser.parse_args();result=verify(args.raw_dir,args.platform_control_dir)
    args.output.write_text(runner.base.e.dumps(result)+'\n')
    print(json.dumps(dict(status=result['status'],verified_prefixes=len(result['prefixes']))))

if __name__=='__main__':main()
