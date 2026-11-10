"""Source-frozen active/dormant invasion experiments (T3)."""

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict,dataclass,replace
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import platform

import numpy as np
from scipy.special import logsumexp

from . import buffered_experiments as e
from . import dormancy as model
from . import dormancy_starts
from .dormancy_integration import Census,integrate_finite

RAW=e.ROOT/"local/haze/dormancy"
OUTPUT=e.ROOT/"models/haze_world/figures/dormancy"


@dataclass(frozen=True)
class Case:
    case_id:str
    group:str
    fraction:float
    epsilon:float
    configuration:str
    dispersal_yr:float
    direction:str
    loss_h:float=1e-3
    switching_factor:float=10.
    years:float=100000.
    census_yr:float=10.
    max_step_yr:float=10.
    rtol:float=2e-8
    ramp:str="cubic"


def design(years=100000.):
    cases=[]
    def add(group,f,eps,config,d,direction,**kw):
        cases.append(Case(f"dormancy_{len(cases):04d}",group,f,eps,config,d,direction,years=years,**kw))
    for f in (0.,.5):
        for eps in (.1,.03,.01,.003,.001,.0003,.0001):
            for config,d in (("none",0.),("warm",1e-9),("warm",1e-6),("both",1e-6)):
                for direction in ("A_into_M","M_into_A"):add("main",f,eps,config,d,direction)
    for f in (0.,.5):
        for eps in (.01,.001,.0001):
            for direction in ("A_into_M","M_into_A"):
                add("slow",f,eps,"none",0.,direction,switching_factor=1.)
    for eps in (.01,.001):
        for direction in ("A_into_M","M_into_A"):
            add("bistable",0.,eps,"none",0.,direction,loss_h=.002)
    return cases


def parameters(case):
    base=e.parameters(e.Case(case.case_id,case.fraction,case.configuration,case.dispersal_yr,case.direction,
                             years=case.years,census_yr=case.census_yr))
    base=replace(base,base=replace(base.base,biology=replace(base.base.biology,loss_h=case.loss_h)))
    return model.Dormancy(base,case.epsilon,case.switching_factor,ramp=case.ramp)


def sources():
    names=("dormancy.py","dormancy_integration.py","dormancy_starts.py","dormancy_experiments.py",
           "turnover_starts.py","bottleneck_integration.py")
    return e.source_hashes()|{str(Path(__file__).with_name(n).relative_to(e.ROOT)):
        sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in names}


def identity(case,mode):
    protocol=dict(case=asdict(case),mode=mode,parameters=asdict(parameters(case)),source_sha256=sources(),
        census=asdict(Census(minimum_cells=1. if mode=="census" else 0.,census_yr=case.census_yr if mode=="census" else 1.)),
        python=platform.python_version(),packages={n:importlib.metadata.version(n) for n in ("numpy","scipy")},
        initialization="Highest-r conditional resident root with its stationary dormant bank; active invader1e-12gDW/L and dormant invader0 in each active habitat")
    return sha256(e.dumps(protocol).encode()).hexdigest(),protocol


def paths(case,mode,fingerprint,raw=RAW):
    stem=f"{case.case_id}_{mode}_t{case.years:g}-{fingerprint[:16]}"
    return raw/(stem+".npz"),raw/(stem+".receipt.json")


def read_record(case,mode,raw=RAW):
    fingerprint,_=identity(case,mode);data,receipt=paths(case,mode,fingerprint,raw)
    if not receipt.exists():return None
    record=json.loads(receipt.read_text())
    if (record["execution_status"]!="complete" or record["fingerprint"]!=fingerprint
        or sha256(data.read_bytes()).hexdigest()!=record["raw_sha256"]):
        raise RuntimeError("Changed dormancy payload")
    return record


def summarize(case,p,result):
    process=Census(census_yr=case.census_yr);conversion=result.metadata["global_log_cell_conversion"]
    y=result.y[:,-1];dy=model.rhs(y,p);f=model.fluxes(y,p)
    active=p.weights>0;volumes=p.coupled.habitat_l_cm2*process.surface_cm2*p.weights
    floors=np.divide(process.cell_mass_gdw,volumes,out=np.zeros(p.n_patches),where=volumes>0)
    minimum=np.r_[np.array([[1.,v,v,1e-9,v,v] for v in floors]).ravel(),.001]
    late=result.t>=max(0.,case.years-20000.);sample=result.y[:,late]
    scale=np.maximum(np.mean(abs(sample),axis=1),minimum)
    span=np.divide(np.ptp(sample,axis=1),scale,out=np.zeros(p.state_size),where=scale>0)
    ts=float(np.max(np.ptp(result.temperatures_k[active][:,late],axis=1)))
    rate=p.coupled.biology.loss_h*model.core.HOURS_PER_YEAR
    hydraulic=model.core.HENRY_30C_MOL_L_PA/(p.coupled.biology.exchange_mol_l_h_pa*model.core.HOURS_PER_YEAR)
    derivative=[abs(dy[-1])*p.coupled.loss.lifetime_yr/max(y[-1],.001)]
    cells=np.zeros((p.n_patches,2));shares=np.zeros(2)
    row=dict(**asdict(case),attempt_status=result.status,terminal_time_yr=float(result.t[-1]),
             temperature_k=float(f["global_temperature_k"]),methane_ratio=float(y[-1]),
             wall_seconds=result.metadata["wall_seconds"],accepted_steps=result.metadata["accepted_steps"])
    for j,w in enumerate(p.weights):
        if not w:continue
        total=y[6*j+1:6*j+3]+y[6*j+4:6*j+6]
        cells[j]=total*volumes[j]/process.cell_mass_gdw
        derivative += [abs(dy[6*j])*hydraulic/max(y[6*j],1.),abs(dy[6*j+3])*p.coupled.acetate_lifetime_yr/max(y[6*j+3],1e-9)]
        derivative += [abs(dy[6*j+k])/max(y[6*j+k],floors[j])/rate for k in (1,2,4,5)]
        shares+=w*np.asarray(f["local"][j]["catabolic_h2_mol_l_yr"])
        row[f"temperature_{p.patch_names[j]}_k"]=float(f["temperatures_k"][j])
        for i,g in enumerate(e.GUILDS):
            events=[v for v in result.extinction_events if v["patch"]==p.patch_names[j] and v["guild"]==("acetogen" if i==0 else "methanogen")]
            row[f"culls_{p.patch_names[j]}_{g}"]=len(events)
            row[f"cells_{p.patch_names[j]}_{g}"]=float(cells[j,i])
            row[f"active_{p.patch_names[j]}_{g}_gdw_l"]=float(y[6*j+1+i])
            row[f"dormant_{p.patch_names[j]}_{g}_gdw_l"]=float(y[6*j+4+i])
    activity=result.census_activity[result.census_times>=max(0.,case.years-20000.)]
    occupancy_changes=int(np.sum(activity[1:]!=activity[:-1]))
    settled=case.years>=100000 and max(span)<.001 and ts<.01 and max(derivative)<.001 and occupancy_changes==0
    presence=np.any(cells>=1.-1e-10,axis=0)
    row.update(settling_status="census_stationary" if settled else "unsettled" if case.years>=100000 else "pilot_only",
        endpoint_class=("coexistence" if all(presence) else "acetogen_only" if presence[0] else "methanogen_only" if presence[1] else "empty") if settled else None,
        global_present_a=bool(presence[0]),global_present_m=bool(presence[1]),
        late_max_relative_span=float(max(span)),late_temperature_span_k=ts,max_scaled_derivative=float(max(derivative)),
        late_occupancy_changes=occupancy_changes,global_catabolic_share_a=float(shares[0]/sum(shares)) if sum(shares) else 0.,
        global_catabolic_share_m=float(shares[1]/sum(shares)) if sum(shares) else 0.)
    for i,g in enumerate(e.GUILDS):
        for name,values in (("continuous",result.global_continuous_min_log_biomass),
                            ("pre_extinction",result.global_pre_extinction_min_log_biomass),
                            ("after_census",result.global_after_census_min_log_biomass)):
            row[f"global_{name}_min_log_cells_{g}"]=float(values[i]+conversion)
            row[f"global_{name}_min_zero_{g}"]=bool(np.isneginf(values[i]))
    return e.clean(row)


def run(case,mode="census",raw=RAW,expected_sources=None):
    fingerprint,protocol=identity(case,mode)
    if expected_sources is not None and protocol["source_sha256"]!=expected_sources:raise RuntimeError("Dormancy source changed after freeze")
    cached=read_record(case,mode,raw)
    if cached is not None:return cached
    p=parameters(case);resident=1 if case.direction=="A_into_M" else 0
    start=dormancy_starts.conditional_states(p,resident)
    if start["selected"] is None:raise RuntimeError(f"No stationary dormancy resident:{case.case_id}")
    initial=np.asarray(start["selected"]["y"]).copy();invader=1-resident
    for j,w in enumerate(p.weights):
        if w:initial[6*j+1+invader]=1e-12;initial[6*j+4+invader]=0.
    result=integrate_finite(initial,p,case.years,Census(**protocol["census"]),
                            sample_every_censuses=1,max_step=case.max_step_yr,rtol=case.rtol)
    if result.status!="completed" or np.any(~np.isfinite(result.y)) or np.any(result.y<0):raise RuntimeError(f"Invalid dormancy trajectory:{case.case_id}/{result.status}")
    summary=summarize(case,p,result)
    if sources()!=protocol["source_sha256"]:raise RuntimeError("Dormancy source changed during run")
    data,receipt=paths(case,mode,fingerprint,raw);raw.mkdir(parents=True,exist_ok=True);temporary=data.with_suffix(".tmp")
    with temporary.open("wb") as stream:
        np.savez_compressed(stream,t=result.t,y=result.y,log_biomass=result.log_biomass,log_active=result.log_active,
            log_dormant=result.log_dormant,temperatures_k=result.temperatures_k,initial=initial,
            min_log_biomass=result.global_continuous_min_log_biomass,min_times=result.global_continuous_min_times_yr,
            metadata=e.dumps(result.metadata),extinction_events=e.dumps(result.extinction_events))
    temporary.replace(data)
    record=dict(execution_status="complete",fingerprint=fingerprint,protocol=protocol,summary=summary,start=e.clean(start),
                raw_file=data.name,raw_sha256=sha256(data.read_bytes()).hexdigest())
    temporary=receipt.with_suffix(".tmp");temporary.write_text(e.dumps(record)+"\n");temporary.replace(receipt)
    return record


def _worker(task):return run(*task)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=("census","uncensored"),default="census")
    parser.add_argument("--years",type=float);parser.add_argument("--max-step",type=float,default=10.)
    parser.add_argument("--rtol",type=float,default=2e-8);parser.add_argument("--workers",type=int,default=4)
    parser.add_argument("--case-id",action="append");parser.add_argument("--raw-dir",type=Path,default=RAW)
    parser.add_argument("--epsilon",type=float);parser.add_argument("--output",type=Path,default=OUTPUT)
    parser.add_argument("--ramp",choices=("cubic","linear"),default="cubic")
    parser.add_argument("--collect-only",action="store_true")
    args=parser.parse_args();cases=[replace(c,max_step_yr=args.max_step,rtol=args.rtol,ramp=args.ramp) for c in design(args.years or (100000. if args.mode=="census" else 30000.))]
    if args.case_id:
        cases=[c for c in cases if c.case_id in args.case_id]
        if len(cases)!=len(args.case_id):raise ValueError("Unknown case selection")
    if args.epsilon is not None:
        if not args.case_id:raise ValueError("An epsilon refinement must select its base cases")
        cases=[replace(c,case_id=f"{c.case_id}_eps{args.epsilon:g}",epsilon=args.epsilon) for c in cases]
    frozen=sources();records=[]
    if args.collect_only:
        for c in cases:
            record=read_record(c,args.mode,args.raw_dir)
            if record is None:raise RuntimeError("Incomplete dormancy batch")
            records.append(record)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for i,r in enumerate(pool.map(_worker,[(c,args.mode,args.raw_dir,frozen) for c in cases]),1):
                records.append(r);print(i,len(cases),r["protocol"]["case"]["case_id"],flush=True)
    args.output.mkdir(parents=True,exist_ok=True);name="dormancy" if args.mode=="census" else "dormancy_uncensored"
    if args.case_id:name+="_selection_"+sha256(e.dumps(sorted(args.case_id)).encode()).hexdigest()[:8]
    if args.years:name+=f"_t{args.years:g}"
    if args.epsilon is not None:name+=f"_eps{args.epsilon:g}"
    if args.ramp!="cubic":name+="_"+args.ramp
    e.table(args.output/(name+".csv"),[r["summary"] for r in records])
    (args.output/(name+"_manifest.json")).write_text(e.dumps(dict(profiles=len(records),mode=args.mode,source_sha256=frozen,
        receipts=[{k:r[k] for k in ("raw_file","raw_sha256","fingerprint")} for r in records]))+"\n")


if __name__=="__main__":main()
