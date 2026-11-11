"""Bounded frozen-Radau continuation where the macroscopic guard declines."""

import argparse
from dataclasses import replace
from hashlib import sha256
import json
import signal
from time import perf_counter

import numpy as np

from terra_prisca.haze_world import dormancy_cycle_closure as closure


def run(key, input_file, absolute_start=2000., years=8000., wall_limit=180.):
    source=closure.ROOT/input_file
    with np.load(source) as data:
        initial=data["y"][:, -1].copy()
    case=replace(closure.cycle_case(key),ramp="linear")
    p=closure.experiments.parameters(case)
    protocol=dict(kind="linear_frozen_positive_continuation",case=vars(case),
        input_file=input_file,input_sha256=closure.digest(source),
        absolute_start_yr=absolute_start,requested_duration_yr=years,
        rtol=2e-9,max_step_yr=10.,wall_limit_seconds=wall_limit,
        source_sha256=closure.sources(),controller_sha256=closure.digest(__file__),
        scope="Existing frozen positive-coordinate Radau producer; fresh numerical history at an accepted census time. Physical stocks unchanged.")
    fingerprint=sha256(closure.experiments.e.dumps(protocol).encode()).hexdigest()
    receipt=closure.RAW/f"linear_positive_{key}_{fingerprint[:12]}.json"
    if receipt.exists():
        old=json.loads(receipt.read_text())
        if old["status"]=="completed" and closure.digest(closure.ROOT/old["raw_file"])==old["raw_sha256"]:
            return old
        raise RuntimeError("Preserve unsuccessful bounded continuation")
    record=dict(protocol=protocol,fingerprint=fingerprint)
    started=perf_counter()
    def timeout(signum,frame):
        raise TimeoutError("Bounded positive-coordinate continuation exceeded its wall limit")
    old_handler=signal.signal(signal.SIGALRM,timeout)
    signal.setitimer(signal.ITIMER_REAL,wall_limit)
    try:
        result=closure.radau.integrate_finite(initial,p,years,sample_every_censuses=1,
            rtol=2e-9,max_step=10.)
        raw=receipt.with_suffix(".npz")
        np.savez_compressed(raw,t=result.t+absolute_start,y=result.y,initial=initial)
        record.update(status=result.status,raw_file=str(raw.relative_to(closure.ROOT)),
            raw_sha256=closure.digest(raw),actual_horizon_yr=float(result.t[-1]+absolute_start),
            work=result.metadata,extinction_events=result.extinction_events,
            envelopes=closure.envelopes(dict(t=result.t,y=result.y),p,years))
    except Exception as error:
        record.update(status="failed",error=repr(error),actual_horizon_yr=absolute_start,
            partial_flow_retained=False)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,old_handler)
    record.update(wall_seconds=perf_counter()-started,
        sources_unchanged=closure.sources()==protocol["source_sha256"] and closure.digest(__file__)==protocol["controller_sha256"])
    receipt.write_text(closure.experiments.e.dumps(record)+"\n")
    return record


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case",choices=("0012","0068"))
    parser.add_argument("input_file")
    parser.add_argument("--absolute-start",type=float,default=2000.)
    parser.add_argument("--years",type=float,default=8000.)
    args=parser.parse_args()
    record=run(args.case,args.input_file,args.absolute_start,args.years)
    print(json.dumps({k:v for k,v in record.items() if k not in ("protocol","work")}),flush=True)
