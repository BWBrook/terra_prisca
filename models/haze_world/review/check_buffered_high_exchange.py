"""Two exploratory 100-year finite prefixes at fast cell exchange.

uv run python models/haze_world/review/check_buffered_high_exchange.py

Post-main mechanistic controls, not part of the prespecified 96-run matrix.
Uses the existing conditional-start, seed and finite-census protocol unchanged.
"""

from dataclasses import asdict
from hashlib import sha256
import gzip
import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world import buffered_experiments as experiments
from terra_prisca.haze_world import habitat_equilibria as equilibria

ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'local/haze/buffered_refuges/high_exchange'


def check_case(case,sources):
    p=experiments.parameters(case)
    resident=1 if case.direction=='A_into_M' else 0
    candidates=equilibria.conditional_states(p,resident)
    qualifying=[e for e in candidates if e['stability']=='stable' and
                all(e['y'][4*j+1+resident]>0 for j,w in enumerate(p.weights) if w)]
    if not qualifying:
        return dict(case=asdict(case),status='no_supported_stable_conditional_start_found',
                    conditional_candidates=len(candidates),conditional_qualifying=0)
    record=experiments.run_case(case,raw=RAW,expected_sources=sources)
    data=RAW/record['raw_file']
    with gzip.open(data,'rt') as stream:
        raw=json.load(stream)
    result=raw['result'];summary=record['summary']
    activity=result['census_activity'];times=result['census_times']
    loss={}
    for i,guild in enumerate(('a','m')):
        absent=[float(t) for t,mask in zip(times,activity) if not any(int(mask)&(1<<(2*j+i))
                for j,w in enumerate(p.weights) if w)]
        when=min(absent) if absent else None
        temperatures=None
        local_growth=None
        invasion_rate=None
        if when is not None:
            index=int(np.flatnonzero(np.isclose(result['t'],when,rtol=0,atol=1e-8))[0])
            temperatures=[row[index] for row in result['temperatures_k']]
            at_loss=np.asarray(result['y'])[:,index]
            flows=experiments.model.fluxes(at_loss,p)
            local_growth=np.array([local['net_growth_yr'][i] for local in flows['local']])
            operator=np.diag(local_growth-case.dispersal_yr)+case.dispersal_yr*np.ones((3,1))*p.weights[None,:]
            invasion_rate=float(max(np.linalg.eigvals(operator).real))
        loss[guild]=dict(first_global_absence_census_yr=when,temperatures_at_loss_k=temperatures,
            global_pre_extinction_min_log_cells=summary[f'global_pre_extinction_min_log_cells_{guild}'],
            global_after_census_min_zero=summary[f'global_after_census_min_zero_{guild}'],
            present_at_100yr=summary[f'global_present_{guild}'],
            local_biological_growth_at_loss_yr=None if local_growth is None else local_growth.tolist(),
            dominant_rare_growth_operator_at_loss_yr=invasion_rate)
    m=result['metadata']
    return dict(case=asdict(case),parameters=asdict(p),status='completed_prefix',
        selected_conditional_ratio=summary['conditional_selected_ratio'],
        conditional_candidates=len(candidates),conditional_qualifying=len(qualifying),
        start_global_temperature_k=float(experiments.core.temperature_k(raw['initial'][-1],p.base.climate)),
        terminal_global_temperature_k=summary['global_temperature_k'],
        settling_status=summary['settling_status'],global_loss=loss,
        all_accepted_stocks_finite_nonnegative=bool(np.all(np.isfinite(result['y'])) and np.all(np.array(result['y'])>=0)),
        allocation_absolute_tolerance=m['allocation_absolute_tolerance'],relative_tolerance=m['relative_tolerance'],
        allocation_positivity_retries=m['allocation_positivity_retries'],acetate_positivity_retries=m['acetate_positivity_retries'],
        census_solver_resets=m['census_solver_resets'],solver_resets=m['solver_resets'],
        nfev=m['nfev'],accepted_steps=m['accepted_steps'],wall_seconds=m['wall_seconds'],
        extinction_events=result['extinction_events'],fingerprint=record['fingerprint'],
        raw_file=str(data.relative_to(ROOT)),raw_sha256=record['raw_sha256'])


def main():
    sources=experiments.source_hashes()
    cases=[experiments.Case('high_exchange_A_into_M_t100',.5,'both',100.,'A_into_M',years=100.),
           experiments.Case('high_exchange_M_into_A_t100',.5,'both',100.,'M_into_A',years=100.)]
    results=[]
    for case in cases:
        output=check_case(case,sources);results.append(output)
        if output['status']!='completed_prefix':
            break
    if experiments.source_hashes()!=sources:
        raise RuntimeError('Sources changed during the exploratory controls')
    report=dict(scope='Post-main exploratory fast-exchange controls; 100-year finite prefixes only, not settled endpoints or a universal dispersal threshold',
        source_sha256=sources,checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),cases=results)
    Path(__file__).with_name('buffered_high_exchange_check.json').write_text(experiments.dumps(report)+'\n')
    for output in results:
        print(experiments.dumps({k:output[k] for k in ('case','status','global_loss','terminal_global_temperature_k') if k in output}))


if __name__=='__main__':main()
