"""Turnover-dependent buffered-refuge experiments (T2)."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import platform

import numpy as np

from . import buffered_experiments as e
from . import habitat_equilibria as eq
from . import population_coupling as core
from . import turnover_starts
from .bottleneck_integration import Census, integrate_finite

RAW = e.ROOT/"local/haze/turnover"
OUTPUT = e.ROOT/"models/haze_world/figures/turnover"


@dataclass(frozen=True)
class Case:
    case_id: str
    fraction: float
    loss_h: float
    layout: str
    dispersal_yr: float
    direction: str
    years: float = 100000.
    census_yr: float = 10.
    max_step_yr: float = 10.


def design(years=100000.):
    cases = []
    for loss in (3e-4, 5e-4, 7e-4, 1e-3, 1.5e-3, 2e-3, 3e-3):
        for fraction in (0., .5):
            for layout in ("none", "both_absolute", "both_relative", "warm_relative"):
                for d in ((0.,) if layout == "none" else (1e-6, .001)):
                    for direction in ("A_into_M", "M_into_A"):
                        cases.append(Case(f"refuges_{len(cases):04d}",fraction,loss,layout,d,direction,years))
    return cases


def parameters(case):
    switch = core.switch_temperatures(replace(core.reference().biology, loss_h=case.loss_h))
    if "relative" in case.layout:
        if len(switch) != 1:
            raise ValueError("Relative refuges require a unique supported physiological switch")
        cold, warm = switch[0]-3.535, switch[0]+4.465
    else:
        cold, warm = 278., 286.
    configuration = "none" if case.layout == "none" else "warm" if case.layout == "warm_relative" else "both"
    p = e.parameters(e.Case(case.case_id,case.fraction,configuration,case.dispersal_yr,case.direction,
                            warm_k=warm,cold_k=cold,years=case.years,census_yr=case.census_yr))
    return replace(p,base=replace(p.base,biology=replace(p.base.biology,loss_h=case.loss_h)))


def sources():
    names = ("turnover_experiments.py", "turnover_starts.py", "bottleneck_integration.py")
    return e.source_hashes() | {str(Path(__file__).with_name(n).relative_to(e.ROOT)):
        sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in names}


def identity(case, mode):
    protocol = dict(case=asdict(case),mode=mode,parameters=asdict(parameters(case)),source_sha256=sources(),
        census=asdict(Census(minimum_cells=1. if mode == "census" else 0.,census_yr=case.census_yr if mode == "census" else 1.)),
        python=platform.python_version(),packages={n:importlib.metadata.version(n) for n in ("numpy","scipy")},
        initialization="Highest-r supported stable conditional resident;1e-12gDW/L invader in each active habitat")
    return sha256(e.dumps(protocol).encode()).hexdigest(), protocol


def paths(case, mode, fingerprint, raw=RAW):
    stem=f"{case.case_id}_{mode}_t{case.years:g}-{fingerprint[:16]}"
    return raw/(stem+".npz"),raw/(stem+".receipt.json")


def read_record(case,mode,raw=RAW):
    fingerprint,_=identity(case,mode);data,receipt=paths(case,mode,fingerprint,raw)
    if not receipt.exists():return None
    record=json.loads(receipt.read_text())
    if (record["execution_status"]!="complete" or record["fingerprint"]!=fingerprint
            or sha256(data.read_bytes()).hexdigest()!=record["raw_sha256"]):
        raise RuntimeError("Changed turnover payload")
    return record


def run(case, mode="census", raw=RAW, expected_sources=None):
    fingerprint, protocol = identity(case,mode)
    if expected_sources is not None and protocol["source_sha256"] != expected_sources:
        raise RuntimeError("Turnover source changed after freeze")
    data, receipt = paths(case,mode,fingerprint,raw)
    cached=read_record(case,mode,raw)
    if cached is not None:return cached
    p=parameters(case);resident=1 if case.direction=="A_into_M" else 0
    start=turnover_starts.conditional_states(p,resident)
    if start["selected"] is None:
        raise RuntimeError(f"No qualifying conditional start: {case.case_id}")
    initial=e.seed_state(start["selected"]["y"],p,case.direction)
    process=Census(**protocol["census"])
    result=integrate_finite(initial,p,case.years,process,sample_every_censuses=1,max_step=case.max_step_yr)
    if result.status != "completed":
        raise RuntimeError(f"Unsupported trajectory: {case.case_id}/{result.status}")
    if np.any(~np.isfinite(result.y)) or np.any(result.y<0):
        raise RuntimeError("Invalid physical stocks")
    summary=e.summarize(case,p,result,start)
    summary.update(switch_temperatures_k=list(core.switch_temperatures(p.base.biology)),
        numerical_trial_retries=result.metadata.get("acetate_trial_retries",0),
        initial_temperature_k=float(core.temperature_k(initial[-1],p.base.climate)))
    if mode=="census" and summary["settling_status"]=="census_stationary":
        fit=eq.refine(result.y[:,-1],p)
        summary.update(refined_equilibrium_found=fit is not None,
            refined_stability=None if fit is None else fit["stability"],
            refined_max_real_eigenvalue_yr=None if fit is None else fit["max_real_yr"])
    if sources()!=protocol["source_sha256"]:
        raise RuntimeError("Turnover source changed during run")
    raw.mkdir(parents=True,exist_ok=True);temporary=data.with_suffix(".tmp")
    with temporary.open("wb") as stream:
        np.savez_compressed(stream,t=result.t,y=result.y,log_biomass=result.log_biomass,
            temperatures_k=result.temperatures_k,initial=initial,
            min_log_biomass=result.global_continuous_min_log_biomass,
            min_times=result.global_continuous_min_times_yr,metadata=e.dumps(result.metadata),
            extinction_events=e.dumps(result.extinction_events),
            local_pre_removal_min_log=result.pre_removal_min_log_biomass,
            local_pre_removal_min_times=result.pre_removal_min_times_yr)
    temporary.replace(data)
    record=dict(execution_status="complete",fingerprint=fingerprint,protocol=protocol,summary=summary,
                start=e.clean(start),raw_file=data.name,raw_sha256=sha256(data.read_bytes()).hexdigest())
    temporary=receipt.with_suffix(".tmp");temporary.write_text(e.dumps(record)+"\n");temporary.replace(receipt)
    return record


def _worker(task):
    return run(*task)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=("census","uncensored"),default="census")
    parser.add_argument("--years",type=float)
    parser.add_argument("--max-step",type=float,default=10.)
    parser.add_argument("--workers",type=int,default=4)
    parser.add_argument("--case-id",action="append")
    parser.add_argument("--raw-dir",type=Path,default=RAW)
    parser.add_argument("--collect-only",action="store_true")
    args=parser.parse_args();cases=design(args.years or (100000. if args.mode=="census" else 30000.))
    cases=[replace(c,max_step_yr=args.max_step) for c in cases]
    if args.case_id:
        cases=[c for c in cases if c.case_id in args.case_id]
        if len(cases)!=len(args.case_id):raise ValueError("Unknown case selection")
    frozen=sources();tasks=[(c,args.mode,args.raw_dir,frozen) for c in cases];records=[]
    if args.collect_only:
        for c in cases:
            record=read_record(c,args.mode,args.raw_dir)
            if record is None:raise RuntimeError("Incomplete turnover batch")
            records.append(record)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for i,record in enumerate(pool.map(_worker,tasks),1):
                records.append(record);print(i,len(cases),record["protocol"]["case"]["case_id"],flush=True)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    name="refuges" if args.mode=="census" else "refuges_uncensored"
    if args.case_id:name+="_selection_"+sha256(e.dumps(sorted(args.case_id)).encode()).hexdigest()[:8]
    if args.years:name+=f"_t{args.years:g}"
    e.table(OUTPUT/(name+".csv"),[r["summary"] for r in records])
    (OUTPUT/(name+"_manifest.json")).write_text(e.dumps(dict(profiles=len(records),source_sha256=frozen,
        mode=args.mode,receipts=[{k:r[k] for k in ("raw_file","raw_sha256","fingerprint")} for r in records]))+"\n")


if __name__=="__main__":main()
