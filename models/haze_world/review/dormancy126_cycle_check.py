"""Bounded cross-solver continuations of unculled, nonspatial dormancy cycles.

    uv run python models/haze_world/review/dormancy126_cycle_check.py --case 0126
    uv run python models/haze_world/review/dormancy126_cycle_check.py --case 0024

Start from the recorded80k physical state, retain the absolute native clock
and ten-year one-cell census, and observe annual accepted flow. No seeds,
clipping or frozen source edits. A180-second limit preserves useful partials.
"""
import argparse
from hashlib import sha256
import inspect,json,signal
from pathlib import Path
import platform
from time import perf_counter
from types import SimpleNamespace

import numpy as np
from scipy.special import logsumexp

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_radau_integration as numerical
from terra_prisca.haze_world import dormancy_radau_experiments as runner
from terra_prisca.haze_world import turnover
from dormancy_spatial_cycle_check import envelope
from dormancy_extended_cycle_check import direct_root,complete_cycle_mean

ROOT=runner.base.e.ROOT
HERE=Path(__file__).parent
RAW=ROOT/'local/haze/dormancy_nonspatial_cycle_precision'
INPUTS={'0126':'63c9913eb7d9f246','0024':'97955acfab647868'}
HELPER_SHA='09be346c90c0fcb65ed6409f2de47ea1e4d3e2d542f3d6291eb7ae85a0bf6d2b'


def digest(path):return sha256(Path(path).read_bytes()).hexdigest()


def counts(data,p,conversion,left,right):
    use=(data['t']>=left)&(data['t']<=right);active=p.weights>0
    logs=logsumexp(data['log_biomass'][active][:,:,use]+np.log(p.weights[active,None,None]),axis=0)
    return ((logs.min(axis=1)+conversion)/np.log(10.)).tolist()


def root_check(seed,p):
    result=direct_root(seed,p)
    spectra=result['spectra'];last=[s['max_real_yr'] for s in spectra[-2:]];spread=max(last)-min(last)
    result['last_pair_max_real_spread_yr']=spread
    result['last_pair_local_class']=('stable' if max(last)<-max(1e-9,5*spread) else 'unstable' if min(last)>max(1e-9,5*spread) else 'unresolved')
    ratio=result['y'][-1];knots=turnover.nonsmooth_ratios(p.coupled.climate)
    result['nearest_known_climate_or_kinetic_corner_ratio_distance']=float(min(abs(knots-ratio)))
    if result['nearest_known_climate_or_kinetic_corner_ratio_distance']<1e-10:result['last_pair_local_class']='unresolved_corner'
    if np.count_nonzero(p.weights)==1 and p.patches[0].rule=='tracking' and p.patches[0].value==0:
        y=np.asarray(result['y']);active_state=np.r_[y[:4],y[-1]];block=[]
        for step in (1e-5,1e-6,1e-7,1e-8):
            values,_=turnover.stability_spectrum(active_state,p.coupled,step)
            values=np.r_[values,[-p.epsilon*p.coupled.biology.loss_h*model.core.HOURS_PER_YEAR]*2]
            block.append(dict(step=step,max_real_yr=float(max(values.real)),eigenvalues_yr=[[float(v.real),float(v.imag)] for v in values]))
        result['zero_dormant_cubic_block_check']=dict(spectra=block,scope='At the exact mixed root gA=gM=0,D=0, cubic switching has zero first derivative; the active5-state block and two negative dormant-loss eigenvalues give the linear spectrum. Numerical root residual and corner qualifications remain.')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',choices=INPUTS,default='0126');args=parser.parse_args()
    if digest(numerical.__file__)!=HELPER_SHA:raise RuntimeError('The qualified Radau helper changed')
    prefix=INPUTS[args.case];receipt=runner.RAW/f'dormancy_{args.case}_census_t100000-{prefix}.receipt.json';native_record=json.loads(receipt.read_text())
    native_fp=native_record['fingerprint']
    if native_record['execution_status']!='complete' or sha256(runner.base.e.dumps(native_record['protocol']).encode()).hexdigest()!=native_fp:raise RuntimeError('Invalid native receipt')
    native_payload=runner.RAW/native_record['raw_file']
    if digest(native_payload)!=native_record['raw_sha256']:raise RuntimeError('Changed native payload')
    sources=runner.sources()
    if not all(digest(ROOT/k)==v for k,v in native_record['protocol']['source_sha256'].items()):raise RuntimeError('A native source dependency changed')
    case=runner.base.Case(**native_record['protocol']['case']);p=runner.base.parameters(case)
    if case.configuration!='none' or p.dispersal_yr!=0. or np.count_nonzero(p.weights)!=1:raise RuntimeError('Expected the no-refuge control')
    with np.load(native_payload) as data:
        native={k:data[k].copy() for k in ('t','y','log_biomass','log_active','log_dormant')};native_meta=json.loads(str(data['metadata']));native_events=json.loads(str(data['extinction_events']))
    at=np.flatnonzero(native['t']==80000.)
    if len(at)!=1:raise RuntimeError('Missing or ambiguous80k state')
    initial=native['y'][:,at[0]].copy();process=numerical.Census(**native_record['protocol']['census'])
    if process.minimum_cells!=1. or process.census_yr!=10.:raise RuntimeError('Unexpected census')
    c=numerical._Coordinates(initial,p);roundtrip,stage_logs=c.decode(c.encode(initial))
    original_logs=np.stack((native['log_active'][:,:,at[0]],native['log_dormant'][:,:,at[0]]),axis=2)
    lost=np.isfinite(original_logs)&~np.isfinite(stage_logs);added=~np.isfinite(original_logs)&np.isfinite(stage_logs)
    if np.any(added):raise RuntimeError('Coordinate initialization added a represented stage')
    relative=np.divide(abs(roundtrip-initial),abs(initial),out=np.zeros_like(initial),where=initial!=0.)
    if max(relative)>8*np.finfo(float).eps:raise RuntimeError('Initial roundtrip exceeds floating roundoff')
    protocol=dict(case=vars(case),absolute_start_yr=80000.,duration_yr=2000.,rtol=2e-9,max_step_yr=1.,wall_limit_seconds=180.,annual_accepted_flow=True,
        census=vars(process),source_sha256=sources,checker_sha256=digest(__file__),native_receipt=str(receipt.relative_to(ROOT)),native_receipt_sha256=digest(receipt),native_fingerprint=native_fp,native_raw_sha256=digest(native_payload),
        imported_review_sha256={name:digest(HERE/name) for name in ('dormancy_spatial_cycle_check.py','dormancy_extended_cycle_check.py')},turnover_source_sha256=digest(turnover.__file__),initial_physical=initial.tolist(),
        initial_roundtrip_max_relative_error=float(max(relative)),lost_stage_log_masks=[dict(patch=int(j),guild=int(i),stage=int(s),old_log_gdw_l=float(original_logs[j,i,s])) for j,i,s in zip(*np.where(lost))],
        architecture=platform.machine(),operating_system=platform.system(),initialization_scope='Exact recorded physical input with fresh numerical history/charts. Any finite below-float stage-log loss is recorded; no seed or physical stock reset.')
    fp=sha256(runner.base.e.dumps(protocol).encode()).hexdigest();RAW.mkdir(parents=True,exist_ok=True)
    result=dict(protocol=protocol,fingerprint=fp,native_settling_status=native_record['summary']['settling_status'],native_summary=native_record['summary'],
        native_windows=[envelope(native,p,a,b) for a,b in ((20000.,40000.),(40000.,60000.),(60000.,80000.),(80000.,100000.))],native_matched_window=envelope(native,p,80000.,82000.),
        native_matched_culls=[e for e in native_events if 80000.<e['time_yr']<=82000.],native_late_culls=sum(e['time_yr']>=20000. for e in native_events),native_minimum_log10_cells=counts(native,p,native_meta['global_log_cell_conversion'],80000.,82000.))
    samples={};next_year=[80000];accepted=[80000.];original_minima=numerical.stage._dense_minima
    def observe(dense,left,right,coords,state,previous=None):
        answer=original_minima(dense,left,right,coords,state,previous);accepted[0]=float(right)
        while next_year[0]<=right:
            time=float(next_year[0])
            if time>=left:
                internal=state.copy() if time==left else dense(time);physical,stages=coords.decode(internal);samples[next_year[0]]=physical.copy(),stages.copy()
            next_year[0]+=1
        return answer
    text=inspect.getsource(numerical.stage._accepted_integrate)
    for old,new in [('continuum_time,pre_time = np.zeros_like(total_logs),np.zeros_like(total_logs)','continuum_time,pre_time = np.full_like(total_logs,_START),np.full_like(total_logs,_START)'),('global_time,global_pre_time = np.zeros(2),np.zeros(2)','global_time,global_pre_time = np.full(2,_START),np.full(2,_START)'),('if census is not None:cull(0.,state)','if False:cull(0.,state)'),('append(0.,state); solver=make_solver(state,0.) if years else None','append(_START,state); solver=make_solver(state,_START) if years>_START else None'),('next_census=census.census_yr if census is not None else np.inf;census_number=1;','next_census=(np.floor(_START/census.census_yr)+1)*census.census_yr if census is not None else np.inf;census_number=int(np.floor(_START/census.census_yr))+1 if census is not None else 1;')]:
        if old not in text:raise RuntimeError('Frozen diagnostic clock patch no longer applies')
        text=text.replace(old,new)
    namespace=numerical.stage._accepted_integrate.__globals__.copy();namespace.update(_START=80000.,_dense_minima=observe);exec(compile(text,'<absolute_clock_cycle_control>','exec'),namespace)
    proxy=SimpleNamespace(_accepted_integrate=namespace['_accepted_integrate'],integrate=numerical.stage.integrate,chemical=numerical.stage.chemical)
    namespace=numerical.integrate.__globals__.copy();namespace['stage']=proxy;integrate=numerical.stage.chemical._copied(numerical.integrate,namespace)
    result['private_clock_driver_sha256']=sha256(text.encode()).hexdigest();started=perf_counter()
    class Wall(RuntimeError):pass
    def stop(*unused):raise Wall('The2000-year cross-solver cycle control reached180seconds')
    signal.signal(signal.SIGALRM,stop);signal.alarm(180)
    flow=None
    try:
        flow=integrate(initial,p,82000.,census=process,sample_every_censuses=1,rtol=2e-9,max_step=1.)
        result.update(status=flow.status,metadata=flow.metadata,control_culls=flow.extinction_events,control_dense_minimum_log10_cells=((flow.global_continuous_min_log_biomass+native_meta['global_log_cell_conversion'])/np.log(10)).tolist())
        for k,time in enumerate(flow.t):
            if time==round(time):samples[int(time)]=flow.y[:,k].copy(),np.stack((flow.log_active[:,:,k],flow.log_dormant[:,:,k]),axis=2)
    except Exception as error:
        result.update(status='wall_limit' if isinstance(error,Wall) else 'failed',error=repr(error),positive_dense_stats=getattr(error,'positive_dense_stats',[]),radau_work=getattr(error,'radau_work',[]))
        tb=error.__traceback__
        while tb:
            if tb.tb_frame.f_code.co_name=='_accepted_integrate':
                loc=tb.tb_frame.f_locals;result['failure_context']={k:runner.base.e.clean(loc[k]) for k in ('left','right','steps','retries','failure_retries') if k in loc}
            tb=tb.tb_next
    finally:signal.alarm(0)
    result.update(wall_seconds=perf_counter()-started,accepted_duration_yr=accepted[0]-80000.,sources_unchanged=runner.sources()==sources)
    if samples:
        time=np.array(sorted(samples),dtype=float);values=np.column_stack([samples[int(t)][0] for t in time]);stages=np.stack([samples[int(t)][1] for t in time],axis=-1);logs=logsumexp(stages,axis=2)
        payload=RAW/f'dormancy{args.case}-{fp[:16]}.npz';np.savez_compressed(payload,t=time,y=values,log_biomass=logs,log_active=stages[:,:,0],log_dormant=stages[:,:,1])
        result.update(raw_file=str(payload.relative_to(ROOT)),raw_sha256=digest(payload),nonnegative_finite=bool(np.all(values>=0.) and np.all(np.isfinite(values))))
        if result['status']=='completed':
            if not np.array_equal(time,np.arange(80000.,82001.)):raise RuntimeError('Incomplete annual accepted-flow observation')
            control=dict(t=time,y=values,log_biomass=logs);common,ni,ci=np.intersect1d(native['t'],time,return_indices=True)
            native_t=model.core.temperature_k(native['y'][-1,ni],p.coupled.climate);control_t=model.core.temperature_k(values[-1,ci],p.coupled.climate)
            result.update(control_window=envelope(control,p,80000.,82000.),control_matched_cadence_window=envelope(dict(t=common,y=values[:,ci]),p,80000.,82000.),common_samples=len(common),maximum_common_temperature_difference_k=float(max(abs(native_t-control_t))),rms_common_temperature_difference_k=float(np.sqrt(np.mean((native_t-control_t)**2))),control_minimum_log10_cells=counts(control,p,native_meta['global_log_cell_conversion'],80000.,82000.),maximum_sampled_redox_residual=float(max(abs(model.redox_residual(y,p)) for y in values.T[::10])))
    try:result['mixed_equilibrium']=root_check(np.mean(native['y'][:,native['t']>=80000.],axis=1),p)
    except Exception as error:result['mixed_equilibrium']=dict(status='unresolved',error=repr(error))
    result['scope']='Cross-solver precision continuation of one recorded unculled nonspatial candidate. Native settling labels unchanged; no global basin, Floquet, Hopf or asymptotic periodic-orbit proof.'
    full=RAW/f'dormancy{args.case}-{fp[:16]}.receipt.json';full.write_text(runner.base.e.dumps(result)+'\n');compact=dict(result);compact.pop('metadata',None);compact.update(full_receipt=str(full.relative_to(ROOT)),full_receipt_sha256=digest(full))
    (HERE/f'dormancy126_cycle_{args.case}.json').write_text(runner.base.e.dumps(compact)+'\n')
    print(runner.base.e.dumps({k:result.get(k) for k in ('status','wall_seconds','accepted_duration_yr','maximum_common_temperature_difference_k','control_window','mixed_equilibrium')}),flush=True)


if __name__=='__main__':main()
