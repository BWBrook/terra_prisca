"""Exploratory no-removal counterfactual for a warm-only refuge overshoot.

uv run python models/haze_world/review/check_buffered_overshoot.py

One 10,000-year trajectory changes only the removal floor of main0010 to zero.
One mixed equilibrium is refined from main0012 at the lower exchange rate.
"""

from dataclasses import asdict, replace
from hashlib import sha256
import gzip
import io
import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world import buffered_experiments as experiments
from terra_prisca.haze_world import habitat_equilibria as equilibria
from terra_prisca.haze_world import habitat_integration as integration

ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'local/haze/buffered_refuges/overshoot'
YEARS=10000.


def baseline(case_id):
    case=next(case for case in experiments.design('main') if case.case_id==case_id)
    record=experiments.read_record(case,experiments.RAW)
    if record is None:raise RuntimeError(f'Qualified baseline record missing: {case_id}')
    with gzip.open(experiments.RAW/record['raw_file'],'rt') as stream:
        payload=json.load(stream)
    return case,record,payload


def main():
    sources=experiments.source_hashes()
    case,base_record,base_data=baseline('main_0010_t100000')
    p=experiments.parameters(case)
    initial=np.asarray(base_data['initial'])
    _,seed_record,seed_data=baseline('main_0012_t100000')
    seed=np.asarray(seed_data['result']['y'])[:,-1]
    mixed=equilibria.refine(seed,p)
    root_search=dict(direct_target_succeeded=mixed is not None,continuation=[])
    if mixed is None:
        current=seed
        for d in (1e-4,1e-5,1e-6):
            candidate=equilibria.refine(current,replace(p,dispersal_yr=d))
            root_search['continuation'].append(dict(dispersal_yr=d,succeeded=candidate is not None))
            if candidate is None:break
            current=candidate['y']
        else:mixed=candidate
    m_only=equilibria.describe(np.asarray(base_data['start']['selected']['y']),p)
    process=integration.Census(minimum_cells=0.,census_yr=10.)
    protocol=dict(scope='Post-main warm-only overshoot counterfactual; no removal, not a prespecified-grid case',
        original_case=asdict(case),years=YEARS,parameters=asdict(p),census=asdict(process),
        source_sha256=sources,baseline_fingerprint=base_record['fingerprint'],
        baseline_raw_sha256=base_record['raw_sha256'],initial_y=initial.tolist())
    fingerprint=sha256(experiments.dumps(protocol).encode()).hexdigest()
    RAW.mkdir(parents=True,exist_ok=True)
    path=RAW/f'overshoot_floor0_t10000-{fingerprint[:16]}.json.gz'
    receipt=path.with_name(path.name.replace('.json.gz','.receipt.json'))
    if receipt.exists():
        proof=json.loads(receipt.read_text())
        assert proof['fingerprint']==fingerprint and sha256(path.read_bytes()).hexdigest()==proof['raw_sha256']
        with gzip.open(path,'rt') as stream:result=json.load(stream)['result']
    else:
        observed=integration.integrate_finite(initial,p,YEARS,process,sample_every_censuses=1)
        if observed.status!='completed':raise RuntimeError(f'Counterfactual failed: {observed.status}')
        if observed.extinction_events:raise RuntimeError('Floor-zero counterfactual unexpectedly removed a lineage')
        result=experiments.clean(asdict(observed))
        temporary=path.with_suffix('.tmp')
        with temporary.open('wb') as binary,gzip.GzipFile(filename='',mode='wb',fileobj=binary,mtime=0) as compressed,io.TextIOWrapper(compressed) as stream:
            stream.write(experiments.dumps(dict(protocol=protocol,result=result)))
        temporary.replace(path)
        proof=dict(execution_status='complete',fingerprint=fingerprint,raw_file=str(path.relative_to(ROOT)),
                   raw_sha256=sha256(path.read_bytes()).hexdigest(),protocol=protocol)
        receipt.write_text(experiments.dumps(proof)+'\n')
    conversion=float(result['metadata']['global_log_cell_conversion'])
    logs=np.asarray(result['log_biomass'],dtype=float)
    if np.any(~np.isfinite(result['y'])) or np.any(np.asarray(result['y'])<0):
        raise RuntimeError('Uncensored trajectory contains invalid accepted physical stocks')
    if np.any(~np.isfinite(logs[p.weights>0])):
        raise RuntimeError('Initially positive uncensored lineages lack finite retained logarithms')
    logs=np.where(np.isnan(logs),-np.inf,logs)
    from scipy.special import logsumexp
    active=p.weights>0
    global_logs=logsumexp(logs[active]+np.log(p.weights[active,None,None]),axis=0)+conversion
    times=np.asarray(result['t'])
    measurements={}
    for i,guild in enumerate(('a','m')):
        minimum=float(result['global_continuous_min_log_biomass'][i]+conversion)
        at=float(result['global_continuous_min_times_yr'][i])
        after=(times>at)&(global_logs[i]>0)
        measurements[guild]=dict(continuous_min_log_global_cells=minimum,
            continuous_min_log10_global_cells=minimum/np.log(10.),continuous_min_time_yr=at,
            terminal_log_global_cells=float(global_logs[i,-1]),terminal_log10_global_cells=float(global_logs[i,-1]/np.log(10.)),
            first_sampled_recovery_above_one_cell_yr=float(times[np.flatnonzero(after)[0]]) if minimum<0 and np.any(after) else None)
    compare={}
    for t in (1280.,1320.,2000.,5000.,10000.):
        index=int(np.argmin(abs(times-t)))
        compare[str(t)]=dict(time_yr=float(times[index]),global_log10_cells_a=float(global_logs[0,index]/np.log(10.)),
            global_log10_cells_m=float(global_logs[1,index]/np.log(10.)),
            global_temperature_k=float(experiments.core.temperature_k(result['y'][-1][index],p.base.climate)))
    if experiments.source_hashes()!=sources:raise RuntimeError('Inputs changed during the counterfactual')
    report=dict(scope='One post-main no-removal trajectory and one refined mixed root; retained subcellular continuum populations are not evidence of finite-population survival',
        source_sha256=sources,checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        baseline_case=asdict(case),baseline_fingerprint=base_record['fingerprint'],
        mixed_seed_case='main_0012_t100000',mixed_seed_raw_sha256=seed_record['raw_sha256'],
        counterfactual_protocol=protocol,mixed_equilibrium=mixed,root_search=root_search,
        methanogen_only_start_full_community_spectrum=m_only,
        global_minima=measurements,sampled_comparisons=compare,
        original_finite_global_A_removal_yr=base_record['summary']['global_pre_extinction_min_time_a_yr'],
        no_removal_events=len(result['extinction_events']),metadata=result['metadata'],
        raw_file=str(path.relative_to(ROOT)),raw_sha256=proof['raw_sha256'])
    Path(__file__).with_name('buffered_overshoot_check.json').write_text(experiments.dumps(report)+'\n')
    print(experiments.dumps(dict(mixed_temperature_k=mixed['global_temperature_k'] if mixed else None,mixed_max_real_yr=mixed['max_real_yr'] if mixed else None,
        boundary_max_real_yr=m_only['max_real_yr'],global_minima=measurements,sampled_comparisons=compare,
        no_removal_events=len(result['extinction_events']))))


if __name__=='__main__':main()
