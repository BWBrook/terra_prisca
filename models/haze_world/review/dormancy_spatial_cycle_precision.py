"""Bounded 2k-year precision continuations of recorded dormancy cycles.

    uv run python models/haze_world/review/dormancy_spatial_cycle_precision.py --case-id dormancy_0030
    uv run python models/haze_world/review/dormancy_spatial_cycle_precision.py --case-id dormancy_0038

The ten-year, one-cell census is unchanged. Annual samples are observations
of accepted dense pieces, with official post-census snapshots taking priority.
"""

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import platform
from time import perf_counter
from types import FunctionType,SimpleNamespace

import numpy as np
from scipy.special import logsumexp

from terra_prisca.haze_world import dormancy_experiments as experiments
from terra_prisca.haze_world import dormancy_integration as frozen
from terra_prisca.haze_world import dormancy_trial_integration as numerical
from terra_prisca.haze_world import turnover_survival as profiles
from dormancy_spatial_cycle_check import envelope

GUARD_SHA256="b5c0d208454c8f55b4da865a387ea592f117e28700bb13d1025efe4a4e92ef18"
RAW=experiments.e.ROOT/"local/haze/dormancy_spatial_cycle_precision"


def copied(function,namespace):
    result=FunctionType(function.__code__,namespace,function.__name__,function.__defaults__,function.__closure__)
    result.__kwdefaults__=function.__kwdefaults__
    return result


def check(case_id,wall_limit):
    guard_file=Path(numerical.__file__)
    if sha256(guard_file.read_bytes()).hexdigest()!=GUARD_SHA256:
        raise RuntimeError("The requested b5c guard has changed")
    record=profiles.records(experiments.RAW,"census")[case_id]
    data=profiles.load(record,experiments.RAW)
    case=experiments.Case(**record["protocol"]["case"]);p=experiments.parameters(case)
    start_index=np.flatnonzero(data["t"]==80000.)
    if len(start_index)!=1:raise RuntimeError("The recorded80k start is absent or ambiguous")
    initial=data["y"][:,start_index[0]].copy();process=numerical.Census(census_yr=case.census_yr)
    source=experiments.sources()|{str(guard_file.relative_to(experiments.e.ROOT)):GUARD_SHA256}
    protocol=dict(case=record["protocol"]["case"],source_sha256=source,
        checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        summary_checker_sha256=sha256(Path(__file__).with_name("dormancy_spatial_cycle_check.py").read_bytes()).hexdigest(),
        original_fingerprint=record["fingerprint"],original_raw_file=record["raw_file"],
        original_raw_sha256=record["raw_sha256"],absolute_start_yr=80000.,duration_yr=2000.,
        initial_y=initial.tolist(),census=asdict(process),output_stride_yr=1.,rtol=2e-9,max_step_yr=1.,
        wall_limit_seconds=wall_limit,architecture=platform.machine(),operating_system=platform.system(),
        sampling="Observe only accepted dense pieces; official post-census snapshots override their annual observations")
    fingerprint=sha256(experiments.e.dumps(protocol).encode()).hexdigest();RAW.mkdir(exist_ok=True)
    started=perf_counter();accepted=[0.];samples={};next_sample=[0]
    class ReviewLimit(RuntimeError):pass
    class Bounded(numerical._GuardedLSODA):
        def _initialize(self,time,state,bound,options):
            original=self._physical_rhs
            def observed(t,y):
                if perf_counter()-started>wall_limit:raise ReviewLimit("Bounded cycle precision control reached its wall limit")
                return original(t,y)
            self._physical_rhs=observed
            return super()._initialize(time,state,bound,options)
    native_minima=frozen._dense_minima
    def sample_dense(dense,left,right,coordinates,start,previous=None):
        result=native_minima(dense,left,right,coordinates,start,previous)
        accepted[0]=float(right)
        while next_sample[0]<=right+16*np.finfo(float).eps*max(1.,right):
            time=float(min(next_sample[0],right))
            if time>=left:
                internal=start.copy() if time==left else dense(time)
                physical,stages=coordinates.decode(internal)
                samples[next_sample[0]]=(physical.copy(),stages.copy())
            next_sample[0]+=1
        return result
    frozen_namespace=frozen.integrate.__globals__.copy();frozen_namespace["_dense_minima"]=sample_dense
    guarded_namespace=numerical.integrate.__globals__.copy()
    guarded_namespace.update(_GuardedLSODA=Bounded,frozen=SimpleNamespace(integrate=copied(frozen.integrate,frozen_namespace)))
    function=copied(numerical.integrate,guarded_namespace)
    answer=dict(protocol=protocol,fingerprint=fingerprint)
    try:
        result=function(initial,p,2000.,census=process,sample_every_censuses=1,max_step=1.,rtol=2e-9)
        if result.status!="completed":raise RuntimeError("Precision control left its supported domain")
        for k,time in enumerate(result.t):
            if time!=round(time):raise RuntimeError("Nonannual official snapshot")
            stages=np.stack((result.log_active[:,:,k],result.log_dormant[:,:,k]),axis=2)
            samples[int(time)]=(result.y[:,k].copy(),stages)
        times=np.array(sorted(samples),dtype=float)
        if not np.array_equal(times,np.arange(2001.)):raise RuntimeError("Annual observer missed accepted samples")
        values=np.column_stack([samples[int(t)][0] for t in times])
        stages=np.stack([samples[int(t)][1] for t in times],axis=-1)
        logs=logsumexp(stages,axis=2);conversion=result.metadata["global_log_cell_conversion"]
        active=p.weights>0
        global_sampled=logsumexp(logs[active]+np.log(p.weights[active,None,None]),axis=0)
        native_global=logsumexp(data["log_biomass"][active][:,:,data["t"]>=80000.]
                                +np.log(p.weights[active,None,None]),axis=0)
        control=envelope(dict(t=times,y=values),p,0.,2000.)
        native=envelope(data,p,80000.,100000.)
        payload=RAW/f"{case_id}_precision2000-{fingerprint[:16]}.npz"
        np.savez_compressed(payload,t=times+80000.,y=values,log_biomass=logs,
                            log_active=stages[:,:,0],log_dormant=stages[:,:,1])
        answer.update(status="completed",raw_file=str(payload.relative_to(experiments.e.ROOT)),
            raw_sha256=sha256(payload.read_bytes()).hexdigest(),metadata=experiments.e.clean(result.metadata),
            control=control,native=native,
            period_relative_difference=control["period_yr"]/native["period_yr"]-1,
            sampled_range_relative_difference=control["sampled_range_k"]/native["sampled_range_k"]-1,
            control_sampled_global_min_log10_cells=((np.min(global_sampled,axis=1)+conversion)/np.log(10)).tolist(),
            control_dense_global_min_log10_cells=((result.global_continuous_min_log_biomass+conversion)/np.log(10)).tolist(),
            native_sampled_global_min_log10_cells=((np.min(native_global,axis=1)+conversion)/np.log(10)).tolist(),
            nonnegative_stocks=bool(np.all(values>=0)),census_removals=len(result.extinction_events),
            candidate_scope="Same LSODA family with tighter tolerance and smaller step; not an independent-solver proof or a settled endpoint")
    except ReviewLimit as error:answer.update(status="review_wall_limit",error=str(error))
    except Exception as error:answer.update(status="review_failed",error=repr(error))
    answer.update(wall_seconds=perf_counter()-started,accepted_duration_yr=accepted[0],
        source_unchanged=experiments.sources()==record["protocol"]["source_sha256"]
            and sha256(guard_file.read_bytes()).hexdigest()==GUARD_SHA256)
    receipt=RAW/f"{case_id}_precision2000-{fingerprint[:16]}.receipt.json"
    receipt.write_text(experiments.e.dumps(answer)+"\n")
    print(json.dumps({k:answer[k] for k in ("status","wall_seconds","accepted_duration_yr")}),flush=True)
    return answer


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id",choices=("dormancy_0030","dormancy_0038"),required=True)
    parser.add_argument("--wall-seconds",type=float,default=120.)
    args=parser.parse_args();check(args.case_id,args.wall_seconds)
