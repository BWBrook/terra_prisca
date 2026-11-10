"""First-bottleneck diagnostics for turnover and active/dormant variants."""

import argparse
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.special import logsumexp

from . import branching, bottleneck
from . import buffered_experiments as e
from . import habitat_coupling as habitat
from . import population_coupling as core
from . import turnover_experiments as turnover


def counts(data,p,guild,dormant=False):
    active=np.flatnonzero(p.weights>0)
    conversion=data["metadata"]["global_log_cell_conversion"]
    local=data["log_biomass"][active,guild,:].T
    totals=logsumexp(local+np.log(p.weights[active])[None,:]+conversion,axis=1)
    if dormant:
        stages=np.stack((data["log_active"][active,guild,:].T,
                         data["log_dormant"][active,guild,:].T),axis=-1)
        types=(stages+np.log(p.weights[active])[None,:,None]+conversion).reshape(len(totals),-1)
    else:types=local+np.log(p.weights[active])[None,:]+conversion
    return totals,types


def uptake_shares(y,p,guild,indices,dormant=False):
    if dormant:
        from . import dormancy as model
    largest_local=largest_global=0.
    for k in indices:
        f=model.fluxes(y[:,k],p) if dormant else habitat.fluxes(y[:,k],p)
        used=np.zeros(2)
        for j,w in enumerate(p.weights):
            if not w:continue
            value=np.asarray(f["local"][j]["uptake_h2_mol_l_yr"])
            largest_local=max(largest_local,value[guild]/sum(value) if sum(value)>0 else 0.)
            used+=w*value
        largest_global=max(largest_global,used[guild]/sum(used) if sum(used)>0 else 0.)
    return float(largest_local),float(largest_global)


def first_window(t,y,total,p,guild,dormant=False):
    threshold=np.log(1e16)
    episodes=bottleneck.excursions(total,threshold)
    if not episodes:
        return dict(lo=0,hi=len(t)-1,anchor=int(np.argmin(total)),terminal=False,rare=False,
                    threshold=threshold,reductions=0,local=None,global_=None,
                    status="never_globally_rare")
    first_lo,first_hi,terminal=episodes[0]
    minima=[k for k in range(first_lo+1,first_hi) if total[k]<total[k-1] and total[k]<=total[k+1]]
    anchor=first_lo if total[first_lo]<=total[first_lo+1] else minima[0] if minima else first_hi
    maxima=[k for k in range(anchor+1,first_hi) if total[k]>total[k-1] and total[k]>=total[k+1]]
    if maxima:first_hi=maxima[0];terminal=False
    for reductions in range(1001):
        windows=bottleneck.excursions(total[first_lo:first_hi+1],threshold)
        windows=[(first_lo+a,first_lo+b,open_) for a,b,open_ in windows
                 if first_lo+a<=anchor<=first_lo+b and total[anchor]<threshold]
        if not windows:
            return dict(lo=first_lo,hi=first_hi,anchor=anchor,terminal=terminal,rare=False,
                        threshold=threshold,reductions=reductions,local=None,global_=None,
                        status="first_minimum_not_locally_linear")
        lo,hi,_=windows[0]
        local,global_=uptake_shares(y,p,guild,range(lo,hi+1),dormant)
        if max(local,global_)<=1e-10:
            return dict(lo=lo,hi=hi,anchor=anchor,terminal=terminal and hi==len(t)-1,rare=True,
                        threshold=threshold,reductions=reductions,local=local,global_=global_,
                        status="first_minimum_linear")
        threshold-=np.log(10.)
    raise ArithmeticError("No resolved first linear window")


def analyze(data,p,guild,dormant=False,rate_stride=1.,max_step=1.):
    t,y=data["t"],data["y"]
    total,types=counts(data,p,guild,dormant)
    window=first_window(t,y,total,p,guild,dormant)
    lo,hi=window["lo"],window["hi"]
    stride=max(1,int(np.ceil(rate_stride/np.median(np.diff(t)))))
    indices=np.unique(np.r_[np.arange(lo,hi+1,stride),hi]).astype(int)
    if len(indices)<2:raise ArithmeticError("Unresolved probability window")
    probability_step=max_step if window["rare"] else max(10.,max_step)
    if dormant:
        from . import dormancy_branching as db
        _,birth,death,q=db.trajectory_rates(t[indices],y[:,indices],p,guild)
        logu=db.backward_survival(t[indices],birth,death,q,max_step=probability_step)
    else:
        pairs=[branching.per_cell_rates(y[:,i],p,guild) for i in indices]
        birth=np.array([v[1] for v in pairs]);death=np.array([v[2] for v in pairs])
        logu=branching.backward_survival(t[indices],birth,death,branching.migration_matrix(p),max_step=probability_step)
    probability=branching.lineages(types[lo],logu)
    climate=(p.coupled if dormant else p.base).climate
    temperatures=core.temperature_k(y[-1,lo:hi+1],climate)
    k=window["anchor"]
    curvature=bottleneck._curvature(t[lo:hi+1],total[lo:hi+1],k-lo)
    interior=lo+2<=k<=hi-2 and curvature is not None
    width=float(np.sqrt(2*np.pi/curvature)) if interior else None
    weights=np.exp(types[k]-total[k])
    if dormant:
        from . import dormancy_branching as db
        _,bmin,dmin,_=db.per_cell_rates(y[:,k],p,guild)
    else:_,bmin,dmin=branching.per_cell_rates(y[:,k],p,guild)
    mortality=float(weights@dmin)
    exact_log=total[k]+probability["log_scale_for_half_survival"]
    approx=np.log(2.)*mortality*width if width is not None and window["rare"] else None
    row=dict(guild=e.GUILDS[guild],start_yr=float(t[lo]),end_yr=float(t[hi]),
        terminal_window=bool(window["terminal"]),rare_window=window["rare"],
        probability_scope="first_linear_excursion" if window["rare"] else "nonrare_recorded_environment_prefix",
        window_status=window["status"],
        minimum_time_yr=float(t[k]),log_min_cells=float(total[k]),log10_min_cells=float(total[k]/np.log(10.)),
        log_threshold_cells=window["threshold"],threshold_reductions=window["reductions"],
        maximum_local_uptake_fraction=window["local"],maximum_global_uptake_fraction=window["global_"],
        rate_max_spacing_yr=float(max(np.diff(t[indices]))),rate_samples=len(indices),
        probability_max_step_yr=float(probability_step),
        sampled_window_climate_domains="|".join(sorted(set(core.domain(y[-1,lo:hi+1],climate)))),
        sampled_window_min_temperature_k=float(min(temperatures)),sampled_window_max_temperature_k=float(max(temperatures)),
        interior_minimum=bool(interior),curvature_yr2=curvature if interior else None,
        gaussian_candidate=bool(interior and window["rare"]),
        bottleneck_width_yr=width,weighted_death_at_min_yr=mortality,
        log_cells_for_half_survival_at_min=float(exact_log),
        cells_for_half_survival_at_min=bottleneck._exp(exact_log),
        gaussian_cells_for_half_survival=approx,
        gaussian_relative_error=None if approx is None else float(np.expm1(np.log(approx)-exact_log)),
        log_entry_cells=types[lo].tolist(),log_type_survival=logu.tolist(),**probability)
    return row


def load(record,raw):
    path=raw/record["raw_file"]
    if sha256(path.read_bytes()).hexdigest()!=record["raw_sha256"]:raise RuntimeError("Changed profile checksum")
    with np.load(path,allow_pickle=False) as source:data={k:source[k] for k in source.files}
    data["metadata"]=json.loads(str(data["metadata"]))
    return data


def records(raw,mode):
    selection_path=raw/"receipt_selection.json"
    overrides={}
    if selection_path.exists():
        plan=json.loads(selection_path.read_text())
        if plan.get("schema")!="turnover_dormancy_receipt_selection_v1":
            raise RuntimeError("Unknown receipt selection schema")
        overrides=plan["selections"].get(mode,{})
    selected={}
    for path in raw.glob("*.receipt.json"):
        record=json.loads(path.read_text());protocol=record["protocol"]
        if record["execution_status"]!="complete" or protocol["mode"]!=mode:continue
        if sha256(e.dumps(protocol).encode()).hexdigest()!=record["fingerprint"]:raise RuntimeError("Changed protocol")
        case=protocol["case"];key=case["case_id"]
        if key in overrides and record["fingerprint"]!=overrides[key]:continue
        priority=(case["years"],-case["max_step_yr"],-case.get("rtol",2e-8))
        if key not in selected or priority>selected[key][0]:selected[key]=(priority,record)
        elif priority==selected[key][0] and protocol!=selected[key][1]["protocol"]:
            raise RuntimeError("Ambiguous protocol for "+key)
    result={key:v[1] for key,v in selected.items()}
    if missing:=set(overrides)-set(result):
        raise RuntimeError("Selected receipts are missing: "+", ".join(sorted(missing)))
    for record in result.values():
        for name,digest in record["protocol"]["source_sha256"].items():
            if sha256((e.ROOT/name).read_bytes()).hexdigest()!=digest:raise RuntimeError("Physical source differs: "+name)
    return result


def _task(task):
    record,census,raw,dormant,stride=task
    if dormant:
        from . import dormancy_experiments as runner
    else:runner=turnover
    case=runner.Case(**record["protocol"]["case"]);p=runner.parameters(case);data=load(record,raw)
    results=[analyze(data,p,g,dormant,stride) for g in (0,1)]
    events=json.loads(str(load(census,raw)["extinction_events"]))
    for g,row in enumerate(results):
        removals=[v for v in events if v["guild"]==("acetogen" if g==0 else "methanogen")]
        other=results[1-g]
        other_total,_=counts(data,p,1-g,dormant)
        subcell=np.flatnonzero(other_total<0.)
        row.update(case_id=case.case_id,**{k:v for k,v in record["protocol"]["case"].items() if k!="case_id"},
            source_raw_file=record["raw_file"],source_raw_sha256=record["raw_sha256"],
            census_fingerprint=census["fingerprint"],local_census_removals=len(removals),
            first_local_census_removal_yr=min((v["time_yr"] for v in removals),default=None),
            other_guild_first_sampled_subcell_yr=float(data["t"][subcell[0]]) if subcell.size else None,
            overlaps_other_guild_likely_loss_window=bool(other["survival_probability"]<.5 and other["start_yr"]<row["end_yr"]),
            downstream_of_other_guild_subcell_bound=bool(subcell.size and data["t"][subcell[0]]<row["start_yr"]))
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant",choices=("turnover","dormancy"),required=True)
    parser.add_argument("--raw-dir",type=Path)
    parser.add_argument("--workers",type=int,default=4)
    parser.add_argument("--rate-stride",type=float,default=1.)
    parser.add_argument("--case-id",action="append")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args();dormant=args.variant=="dormancy"
    if dormant:
        from . import dormancy_experiments as runner
    else:runner=turnover
    raw=args.raw_dir or runner.RAW;output=args.output or runner.OUTPUT
    census=records(raw,"census");uncensored=records(raw,"uncensored")
    tasks=[]
    for key,baseline in sorted(census.items()):
        if args.case_id and key not in args.case_id:continue
        baseline_data=load(baseline,raw)
        events=json.loads(str(baseline_data["extinction_events"]))
        dense=baseline_data["min_log_biomass"]+baseline_data["metadata"]["global_log_cell_conversion"]
        requires_annual=bool(events or np.any(dense<np.log(1e16)))
        profile=uncensored.get(key, None if requires_annual else baseline)
        if profile is None:raise RuntimeError("Missing uncensored profile for "+key)
        tasks.append((profile,baseline,raw,dormant,args.rate_stride))
    if args.case_id and len(tasks)!=len(args.case_id):raise RuntimeError("Missing selected case")
    rows=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i,result in enumerate(pool.map(_task,tasks),1):
            rows.extend(result);print(i,len(tasks),result[0]["case_id"],flush=True)
    output.mkdir(parents=True,exist_ok=True)
    name="first_survival"+("_selection" if args.case_id else "")
    e.table(output/(name+".csv"),[e.clean({k:v for k,v in row.items() if k not in ("log_entry_cells","log_type_survival")}) for row in rows])
    payload=json.dumps(e.clean(rows),sort_keys=True,separators=(",",":"),allow_nan=False)+"\n"
    if len(payload.encode())>=1000000:raise RuntimeError("Public survival table exceeds size boundary")
    (output/(name+".json")).write_text(payload)
    sources=[Path(__file__),Path(branching.__file__),Path(bottleneck.__file__)]
    if dormant:
        from . import dormancy_branching
        sources.append(Path(dormancy_branching.__file__))
    (output/(name+"_manifest.json")).write_text(e.dumps(dict(profiles=len(tasks),rows=len(rows),
        source_sha256={str(v.relative_to(e.ROOT)):sha256(v.read_bytes()).hexdigest() for v in sources},
        receipt_selection_sha256=sha256((raw/"receipt_selection.json").read_bytes()).hexdigest()
            if (raw/"receipt_selection.json").exists() else None,
        rate_stride_yr=args.rate_stride,
        gaussian_scope="Local curvature estimate; scalar reduction, Gaussian shape and slow mortality not assumed valid",
        interpretation="Each guild's first bottleneck only; later windows excluded; per-guild conditional diagnostics, not local occupancy or joint community survival probabilities"))+"\n")


if __name__=="__main__":main()
