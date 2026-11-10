"""Source-frozen buffered-refuge invasions and sensitivity comparisons."""

import argparse
from collections import Counter
import csv
from dataclasses import asdict, dataclass, replace
import gzip
from hashlib import sha256
import importlib.metadata
import io
import itertools
import json
from multiprocessing import Pool
from pathlib import Path
import platform

import numpy as np

from . import habitat_coupling as model
from . import habitat_equilibria as equilibria
from . import population_coupling as core
from .finite_experiments import clean, dumps
from .habitat_integration import Census, integrate_finite

ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/"local/haze/buffered_refuges"
OUTPUT=ROOT/"models/haze_world/figures/buffered_refuges"
GUILDS=("a","m")


@dataclass(frozen=True)
class Case:
    case_id: str
    fraction: float
    configuration: str
    dispersal_yr: float
    direction: str
    warm_k: float=286.
    cold_k: float=278.
    refuge_fraction: float=.02
    activity: str="fixed"
    years: float=100000.
    census_yr: float=10.


def parameters(case):
    if case.configuration not in ("none","warm","cold","both"):
        raise ValueError("Unknown refuge configuration")
    warm=case.refuge_fraction if case.configuration in ("warm","both") else 0.
    cold=case.refuge_fraction if case.configuration in ("cold","both") else 0.
    return model.Habitats(replace(core.reference(),acetate_fraction=case.fraction,activity_feedback=case.activity),
        (model.Patch("bulk",1-warm-cold),model.Patch("warm",warm,"buffered",case.warm_k),
         model.Patch("cold",cold,"buffered",case.cold_k)),case.dispersal_yr)


def design(stage="main",years=None):
    duration=(1000. if stage=="pilot" else 100000.) if years is None else float(years)
    cases=[]
    def add(f,configuration,d,direction,**kwargs):
        cases.append(Case("",f,configuration,d,direction,years=duration,**kwargs))
    if stage=="main":
        for row in itertools.product((0.,.5,.9),("none","warm","cold","both"),(1e-9,1e-6,.001,1.),("A_into_M","M_into_A")):
            add(*row)
    elif stage=="sensitivity":
        for f,warm,cold,d,direction in itertools.product((0.,.5,.9),(283.,292.),(277.15,280.),(1e-6,.001),("A_into_M","M_into_A")):
            add(f,"both",d,direction,warm_k=warm,cold_k=cold)
        for f,configuration,direction in itertools.product((0.,.5,.9),("warm","cold","both"),("A_into_M","M_into_A")):
            add(f,configuration,1e-6,direction,refuge_fraction=.005)
        for f,direction in itertools.product((0.,.5,.9),("A_into_M","M_into_A")):
            add(f,"both",1e-6,direction,activity="products")
    elif stage=="controls":
        for f,configuration,direction in itertools.product((0.,.5,.9),("none","warm","cold","both"),("A_into_M","M_into_A")):
            add(f,configuration,0.,direction)
    elif stage=="pilot":
        for row in ((.5,"both",1e-9,"A_into_M"),(.5,"both",1e-9,"M_into_A"),
                    (.5,"warm",1e-6,"M_into_A"),(.5,"cold",1e-6,"A_into_M"),(.9,"both",.001,"M_into_A")):
            add(*row)
        add(.5,"both",1e-6,"A_into_M",activity="products")
    else:
        raise ValueError("Unknown experiment stage")
    return [replace(c,case_id=f"{stage}_{i:04d}_t{duration:g}") for i,c in enumerate(cases)]


def source_hashes():
    names=("buffered_experiments.py","habitat_coupling.py","habitat_integration.py","habitat_equilibria.py",
           "population_coupling.py","methane_budget.py","darwinian.py","two_guilds.py","hydrogen_uptake.py",
           "woodii1998.py","finite_experiments.py","finite_populations.py")
    paths=[Path(__file__).with_name(name) for name in names]
    paths += [ROOT/name for name in ("src/terra_prisca/haze_response/arney2016.py",
        "models/haze_response/arney2016/cases.csv","models/haze_response/arney2016/figure4.csv",
        "models/haze_world/evidence/kotsyurbenko2001_table2.csv","models/haze_world/evidence/peters1998_chemostat.csv","uv.lock")]
    return {str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in paths}


def identity(case):
    protocol=dict(case=asdict(case),parameters=asdict(parameters(case)),census=asdict(Census(census_yr=case.census_yr)),
        source_sha256=source_hashes(),packages={s:importlib.metadata.version(s) for s in ("numpy","scipy")},
        python=platform.python_version(),conditional_grid=121,
        initialization="Highest-r stable conditional resident positive in all active patches; invader density1e-12gDW/L in each active patch; no external immigration")
    return sha256(dumps(protocol).encode()).hexdigest(),protocol


def paths(case,fingerprint,raw):
    stem=f"{case.case_id}-{fingerprint[:16]}"
    return raw/(stem+".json.gz"),raw/(stem+".receipt.json")


def read_record(case,raw):
    fingerprint,protocol=identity(case);data,receipt=paths(case,fingerprint,raw)
    if not receipt.exists():return None
    record=json.loads(receipt.read_text())
    if (record["fingerprint"]!=fingerprint or record["execution_status"]!="complete"
        or sha256(data.read_bytes()).hexdigest()!=record["raw_sha256"]):
        raise RuntimeError(f"Invalid receipt: {case.case_id}")
    return record


def seed_state(state,p,direction):
    if direction not in ("A_into_M","M_into_A"):raise ValueError("Unknown invasion direction")
    invader=0 if direction=="A_into_M" else 1
    y=state.copy()
    for j,w in enumerate(p.weights):
        y[4*j+1+invader]=1e-12 if w else 0.
    return y


def summarize(case,p,result,start):
    process=Census(census_yr=case.census_yr)
    row=dict(**asdict(case),attempt_status=result.status,terminal_time_yr=float(result.t[-1]),
        conditional_candidates=len(start["candidates"]),conditional_qualifying=len(start["qualifying"]),
        conditional_ambiguous=len(start["qualifying"])>1,conditional_selected_ratio=start["selected"]["r"],
        solver_nfev=result.metadata["nfev"],accepted_steps=result.metadata["accepted_steps"],
        solver_resets=result.metadata["solver_resets"],wall_seconds=result.metadata["wall_seconds"],
        path_min_global_temperature_k=result.metadata["global_min_temperature_k"],
        path_max_global_temperature_k=result.metadata["global_max_temperature_k"],
        maximum_abs_temperature_mean_departure_k=result.metadata["maximum_abs_temperature_mean_departure_k"],
        sampled_climate_domains="|".join(sorted(set(result.climate_domains))))
    volumes=p.base.habitat_l_cm2*process.surface_cm2*p.weights
    global_conversion=result.metadata["global_log_cell_conversion"]
    for name,values,times in (("global_continuous",result.global_continuous_min_log_biomass,result.global_continuous_min_times_yr),
        ("global_pre_extinction",result.global_pre_extinction_min_log_biomass,result.global_pre_extinction_min_times_yr),
        ("global_after_census",result.global_after_census_min_log_biomass,None)):
        for i,g in enumerate(GUILDS):
            row[f"{name}_min_log_cells_{g}"]=float(values[i]+global_conversion)
            row[f"{name}_min_zero_{g}"]=bool(np.isneginf(values[i]))
            if times is not None:row[f"{name}_min_time_{g}_yr"]=float(times[i])
    for j,patch in enumerate(p.patch_names):
        row[f"area_{patch}"]=float(p.weights[j])
        row[f"path_min_temperature_{patch}_k"]=result.metadata["patch_min_temperature_k"][j]
        row[f"path_max_temperature_{patch}_k"]=result.metadata["patch_max_temperature_k"][j]
        conversion=np.log(volumes[j]/process.cell_mass_gdw) if volumes[j] else -np.inf
        for i,g in enumerate(GUILDS):
            label=f"{patch}_{g}"
            for name,values in (("continuous",result.continuous_min_log_biomass),
                ("pre_removal",result.pre_removal_min_log_biomass),("after_census",result.after_census_min_log_biomass)):
                row[f"{name}_min_log_cells_{label}"]=float(values[j,i]+conversion)
                row[f"{name}_min_zero_{label}"]=bool(np.isneginf(values[j,i]))
            events=[e for e in result.extinction_events if e["patch"]==patch and e["guild"]==("acetogen" if i==0 else "methanogen")]
            row[f"culls_{label}"]=len(events)
            row[f"first_cull_{label}_yr"]=events[0]["time_yr"] if events else None
    if result.status!="completed":
        raise RuntimeError("Buffered layout unexpectedly left the declared physiological domain")
    y=result.y[:,-1];f=model.fluxes(y,p);dy=model.rhs(y,p)
    late=result.t>=max(0.,case.years-20000.)
    sample=result.y[:,late]
    floor=np.divide(process.cell_mass_gdw,volumes,out=np.zeros(p.n_patches),where=volumes>0)
    minimum=np.r_[np.array([[1.,x,x,1e-9] for x in floor]).ravel(),.001]
    scale=np.maximum(np.mean(abs(sample),axis=1),minimum)
    spans=np.divide(np.ptp(sample,axis=1),scale,out=np.zeros(p.state_size),where=scale>0)
    tspan=float(np.max(np.ptp(result.temperatures_k[p.weights>0][:,late],axis=1)))
    derivative=[abs(dy[-1])*p.base.loss.lifetime_yr/max(y[-1],.001)]
    shares=np.zeros(2);presence=[]
    hydraulic=core.HENRY_30C_MOL_L_PA/(p.base.biology.exchange_mol_l_h_pa*core.HOURS_PER_YEAR)
    for j,(patch,w,local) in enumerate(zip(p.patch_names,p.weights,f["local"])):
        if not w:
            row[f"occupancy_{patch}"]="inactive"
            for g in GUILDS:row[f"cells_{patch}_{g}"]=0.
            continue
        cells=y[4*j+1:4*j+3]*volumes[j]/process.cell_mass_gdw
        mask=[bool(x>=1-1e-10) for x in cells];presence.append(mask)
        row[f"occupancy_{patch}"]=("empty","acetogen","methanogen","both")[int(mask[0])+2*int(mask[1])]
        row[f"temperature_{patch}_k"]=float(f["temperatures_k"][j])
        row[f"physiology_{patch}"]=f["physiology_domains"][j]
        row[f"pressure_{patch}_pa"]=float(y[4*j]);row[f"acetate_{patch}_mol_l"]=float(y[4*j+3])
        cat=np.asarray(local["catabolic_h2_mol_l_yr"]);shares+=w*cat
        local_shares=cat/sum(cat) if sum(cat)>0 else np.zeros(2)
        derivative += [abs(dy[4*j])*hydraulic/max(y[4*j],1.),abs(dy[4*j+3])*p.base.acetate_lifetime_yr/max(y[4*j+3],1e-9)]
        for i,g in enumerate(GUILDS):
            row[f"cells_{patch}_{g}"]=float(cells[i]);row[f"catabolic_share_{patch}_{g}"]=float(local_shares[i])
            row[f"net_growth_{patch}_{g}_yr"]=float(local["net_growth_yr"][i])
            row[f"exchange_{patch}_{g}_gdw_l_yr"]=float(f["exchange_gdw_l_yr"][j,i])
            if mask[i]:derivative.append(abs(dy[4*j+1+i])/max(y[4*j+1+i],floor[j])/(p.base.biology.loss_h*core.HOURS_PER_YEAR))
    late_activity=result.census_activity[result.census_times>=max(0.,case.years-20000.)]
    changes=int(np.sum(late_activity[1:]!=late_activity[:-1]))
    stationary=case.years>=100000 and max(spans)<.001 and tspan<.01 and max(derivative)<.001 and changes==0
    present=np.any(presence,axis=0);share=shares/sum(shares) if sum(shares)>0 else np.zeros(2)
    row.update(settling_status="census_stationary" if stationary else "unsettled" if case.years>=100000 else "pilot_only",
        endpoint_class=("coexistence" if all(present) else "acetogen_only" if present[0] else "methanogen_only" if present[1] else "empty") if stationary else None,
        global_temperature_k=f["global_temperature_k"],mean_habitat_temperature_k=float(p.weights@f["temperatures_k"]),
        methane_ratio=float(y[-1]),climate_domain=f["climate_domain"],global_present_a=bool(present[0]),global_present_m=bool(present[1]),
        global_catabolic_share_a=float(share[0]),global_catabolic_share_m=float(share[1]),material_both=bool(min(share)>=.01),
        late_max_relative_span=float(max(spans)),late_temperature_span_k=tspan,max_scaled_derivative=float(max(derivative)),late_occupancy_changes=changes)
    return clean(row)


def run_case(case,raw=RAW,expected_sources=None):
    fingerprint,protocol=identity(case)
    if expected_sources is not None and protocol["source_sha256"]!=expected_sources:raise RuntimeError("Source changed after freeze")
    reused=read_record(case,raw)
    if reused is not None:return reused
    p=parameters(case);guild=1 if case.direction=="A_into_M" else 0
    candidates=equilibria.conditional_states(p,guild)
    qualifying=[s for s in candidates if s["stability"]=="stable" and all(s["y"][4*j+1+guild]>0 for j,w in enumerate(p.weights) if w)]
    if not qualifying:raise RuntimeError(f"{case.case_id}: no stable supported conditional start found")
    selected=max(qualifying,key=lambda x:x["r"]);start=dict(candidates=candidates,qualifying=qualifying,selected=selected)
    initial=seed_state(selected["y"],p,case.direction)
    result=integrate_finite(initial,p,case.years,Census(census_yr=case.census_yr),sample_every_censuses=1)
    if np.any(~np.isfinite(result.y)) or np.any(result.y<0) or np.any(np.isnan(result.log_biomass)):
        raise RuntimeError(f"{case.case_id}: invalid accepted trajectory")
    summary=summarize(case,p,result,start)
    if identity(case)[0]!=fingerprint:raise RuntimeError("Source changed during case")
    data,receipt=paths(case,fingerprint,raw);raw.mkdir(parents=True,exist_ok=True)
    payload=dict(protocol=protocol,summary=summary,start=start,initial=initial,result=asdict(result))
    temporary=data.with_suffix(".tmp")
    with temporary.open("wb") as binary,gzip.GzipFile(filename="",mode="wb",fileobj=binary,mtime=0) as compressed,io.TextIOWrapper(compressed) as stream:
        stream.write(dumps(payload))
    temporary.replace(data)
    record=dict(execution_status="complete",fingerprint=fingerprint,protocol=protocol,summary=summary,raw_file=data.name,raw_sha256=sha256(data.read_bytes()).hexdigest())
    temporary=receipt.with_suffix(".tmp");temporary.write_text(dumps(record)+"\n");temporary.replace(receipt)
    return record


def _worker(task):
    case,raw,sources=task
    try:return run_case(case,raw,sources)
    except Exception as error:raise RuntimeError(f"Buffered case {case.case_id}: {error}") from error


def run_many(cases,raw=RAW,workers=4):
    tasks=[(c,raw,source_hashes()) for c in cases]
    if workers==1:
        for task in tasks:_worker(task)
    else:
        with Pool(workers) as pool:
            for i,r in enumerate(pool.imap_unordered(_worker,tasks,chunksize=1),1):
                if i%12==0:print(i,len(cases),r["summary"]["settling_status"],flush=True)


def table(path,rows):
    names=sorted(set().union(*(r.keys() for r in rows)))
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=names,lineterminator="\n")
    writer.writeheader();writer.writerows(rows);text=stream.getvalue()
    if len(text.encode())>=1000000:raise RuntimeError("Derived table exceeds public size boundary")
    path.write_text(text)


def collect(cases,raw,output,stage):
    records=[read_record(c,raw) for c in cases]
    if any(r is None for r in records):raise RuntimeError("Incomplete buffered batch")
    output.mkdir(parents=True,exist_ok=True)
    table(output/(stage+"_summary.csv"),[r["summary"] for r in records])
    manifest=dict(stage=stage,cases=len(cases),source_sha256=source_hashes(),
        settling_counts=dict(Counter(r["summary"]["settling_status"] for r in records)),
        receipts=[{k:r[k] for k in ("fingerprint","raw_file","raw_sha256")} | {"case_id":r["protocol"]["case"]["case_id"]} for r in records],
        minima="Accepted dense-flow searches, not interval certified; simultaneous weighted global stocks; pre-removal/global-extinction and post-census zeros separate",
        infinity_encoding="Infinite negative log minima are null/blank with min_zero=true; inactive habitats have no local stock",
        stationarity="At least100kyr; last20kyr stock spans<0.001, Tspan<0.01K, scaledderivative<0.001, unchanged census occupancy")
    (output/(stage+"_manifest.json")).write_text(dumps(manifest)+"\n")
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage",choices=("pilot","main","sensitivity","controls"),default="main")
    parser.add_argument("--workers",type=int,default=4);parser.add_argument("--years",type=float)
    parser.add_argument("--raw-dir",type=Path,default=RAW);parser.add_argument("--output",type=Path,default=OUTPUT)
    parser.add_argument("--case-id",action="append");parser.add_argument("--collect-only",action="store_true")
    args=parser.parse_args();cases=design(args.stage,args.years)
    if args.workers<1:parser.error("Use positive workers")
    ids=set(args.case_id or ())
    if ids:
        cases=[c for c in cases if c.case_id in ids]
        if len(cases)!=len(ids):parser.error("Unknown selected case")
    if not args.collect_only:run_many(cases,args.raw_dir,args.workers)
    stage=args.stage+("_selection_"+sha256(dumps(sorted(ids)).encode()).hexdigest()[:8] if ids else "")
    m=collect(cases,args.raw_dir,args.output,stage)
    print(dumps(dict(stage=stage,cases=m["cases"],settling=m["settling_counts"])))


if __name__=="__main__":main()
