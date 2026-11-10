"""Qualification and paired-history comparisons for buffered-refuge receipts."""

import argparse
from collections import Counter
import csv
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from . import buffered_experiments as e
from . import habitat_equilibria as equilibria


def load(path,raw):
    manifest=json.loads(path.read_text())
    if manifest["source_sha256"]!=e.source_hashes():raise RuntimeError("Source differs from frozen batch")
    records=[]
    for item in manifest["receipts"]:
        record=json.loads((raw/item["raw_file"].replace(".json.gz",".receipt.json")).read_text())
        if (record["execution_status"]!="complete" or record["fingerprint"]!=item["fingerprint"]
            or record["raw_sha256"]!=item["raw_sha256"] or sha256((raw/item["raw_file"]).read_bytes()).hexdigest()!=item["raw_sha256"]):
            raise RuntimeError("Invalid qualified receipt")
        records.append(record)
    if len(records)!=manifest["cases"]:raise RuntimeError("Incomplete manifest")
    return records,dict(file=path.name,sha256=sha256(path.read_bytes()).hexdigest(),cases=len(records))


def key(record,exclude=("case_id","years")):
    return tuple((k,v) for k,v in record["protocol"]["case"].items() if k not in exclude)


def select(original,extensions):
    selected={key(r):r for r in original}
    for later in extensions:
        k=key(later)
        if k not in selected:raise RuntimeError("Extension lacks original case")
        earlier=selected[k]
        def comparable(r):
            p=dict(r["protocol"]);p["case"]={a:b for a,b in p["case"].items() if a not in ("case_id","years")}
            return e.dumps(p)
        if comparable(earlier)!=comparable(later):raise RuntimeError("Extension changed scientific protocol")
        if later["protocol"]["case"]["years"]>earlier["protocol"]["case"]["years"]:selected[k]=later
    return selected


def payload(record,raw):
    with gzip.open(raw/record["raw_file"],"rt") as stream:return json.load(stream)


def diagnose(record,base,raw):
    row=dict(record["summary"])
    case=e.Case(**record["protocol"]["case"]);p=e.parameters(case)
    row.update(base_case_id=base["protocol"]["case"]["case_id"],selected_case_id=case.case_id,selected_horizon_yr=case.years,
               raw_file=record["raw_file"],selected_raw_sha256=record["raw_sha256"])
    row["initial_global_temperature_k"]=float(e.core.temperature_k(row["conditional_selected_ratio"],p.base.climate))
    data=payload(record,raw);y=np.array(data["result"]["y"])[:,-1]
    row["final_y"]=y.tolist()
    if row["settling_status"]=="census_stationary":
        fit=equilibria.refine(y,p)
        row["refined_equilibrium_found"]=fit is not None
        if fit is not None:
            row.update(refined_temperature_k=fit["global_temperature_k"],refined_max_real_eigenvalue_yr=fit["max_real_yr"],
                       refined_stability=fit["stability"],refined_max_scaled_residual=fit["max_scaled_residual"])
        for g in e.GUILDS:
            minimum=row[f"global_pre_extinction_min_log_cells_{g}"]
            row[f"surviving_subcellular_{g}"]=bool(row[f"global_present_{g}"] and
                (row[f"global_pre_extinction_min_zero_{g}"] or minimum is not None and minimum<0))
    return row


def pairs(rows):
    grouped={}
    for row in rows:
        k=tuple((f,row[f]) for f in e.Case.__dataclass_fields__ if f not in ("case_id","direction","years"))
        grouped.setdefault(k,{})[row["direction"]]=row
    results=[]
    for k,values in grouped.items():
        if len(values)!=2:continue
        a,m=values["A_into_M"],values["M_into_A"]
        good=all(x["settling_status"]=="census_stationary" for x in (a,m))
        row=dict(k,both_stationary=good,case_a=a["base_case_id"],case_m=m["base_case_id"],
                 class_a=a["endpoint_class"],class_m=m["endpoint_class"])
        if good:
            y,z=np.array(a["final_y"]),np.array(m["final_y"])
            floor=np.r_[np.tile([1.,1e-20,1e-20,1e-9],3),.001]
            distance=float(max(abs(y-z)/np.maximum((abs(y)+abs(z))/2,floor)))
            occupancy=all(a[f"occupancy_{patch}"]==m[f"occupancy_{patch}"] for patch in ("bulk","warm","cold"))
            row.update(temperature_difference_k=abs(a["global_temperature_k"]-m["global_temperature_k"]),
                maximum_relative_stock_difference=distance,identical_occupancy=occupancy,
                matching_endpoint=bool(occupancy and distance<.001),both_coexist=all(x["endpoint_class"]=="coexistence" for x in (a,m)))
        results.append(row)
    return results


def assess_main(rows,comparisons):
    target=[r for r in rows if r["configuration"]=="both" and r["fraction"]<=.5 and 0<r["dispersal_yr"]<=.001]
    target_pairs=[r for r in comparisons if r["configuration"]=="both" and r["fraction"]<=.5 and 0<r["dispersal_yr"]<=.001]
    persistent=[not r["global_after_census_min_zero_a"] and not r["global_after_census_min_zero_m"] for r in target]
    settled=all(r["settling_status"]=="census_stationary" for r in target)
    b1=len(target)==12 and all(persistent)
    b2=(len(target_pairs)==6 and all(r.get("matching_endpoint",False) and r.get("both_coexist",False) for r in target_pairs))
    return dict(B1_cases=len(target),B1_pass=b1,B2_pairs=len(target_pairs),B2_settled=settled,B2_pass=b2,
                sensitivity_gate="proceed" if b1 and settled and b2 else "characterize_before_sensitivities")


def climate_comparisons(rows):
    for row in rows:
        same=[r for r in rows if all(r[f]==row[f] for f in ("fraction","configuration","dispersal_yr","warm_k","cold_k","refuge_fraction","activity","census_yr"))]
        a=next((r for r in same if r["direction"]=="M_into_A"),None)
        if a is not None:
            row["matched_acetogen_only_temperature_k"]=a["initial_global_temperature_k"]
            row["community_temperature_contrast_k"]=row["global_temperature_k"]-a["initial_global_temperature_k"]
        none=next((r for r in rows if r["configuration"]=="none" and all(r[f]==row[f] for f in
                   ("fraction","dispersal_yr","direction","activity","census_yr"))),None)
        if none is not None and none["settling_status"]=="census_stationary":
            row["no_refuge_temperature_k"]=none["global_temperature_k"]
            row["total_refuge_temperature_contrast_k"]=row["global_temperature_k"]-none["global_temperature_k"]


def zero_refuge_checks(rows,path):
    with path.open() as stream:old=list(csv.DictReader(stream))
    results=[]
    for r in rows:
        if r["configuration"]!="none" or r["settling_status"]!="census_stationary":continue
        matches=[x for x in old if float(x["fraction"])==r["fraction"] and x["activity"]==r["activity"]
            and x["direction"]==r["direction"] and float(x["minimum_cells"])==1
            and float(x["relative_immigration_yr"])==0 and float(x["census_yr"])==r["census_yr"]]
        if len(matches)!=1:raise RuntimeError("Need unique single-habitat comparison")
        x=matches[0]
        dt=abs(r["global_temperature_k"]-float(x["temperature_k"]))
        dr=abs(r["methane_ratio"]-float(x["methane_ratio"]))
        difference=max(abs(r[f"cells_bulk_{g}"]-float(x[f"cells_{g}"]))/
            max((r[f"cells_bulk_{g}"]+float(x[f"cells_{g}"]))/2,1.) for g in e.GUILDS)
        results.append(dict(case_id=r["base_case_id"],single_case_id=x["selected_case_id"],
            temperature_difference_k=dt,methane_ratio_difference=dr,maximum_relative_cell_difference=difference,
            matching_endpoint=bool(dt<.001 and dr<1e-6 and difference<.001)))
    return results


def plots(rows,raw,output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    for f in (0.,.5,.9):
        fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True,layout="constrained")
        for ax,direction in zip(axes,("A_into_M","M_into_A")):
            for configuration,color in zip(("none","warm","cold","both"),("#777777","#c56d36","#4c91a3","#7140a0")):
                group=sorted([r for r in rows if r["fraction"]==f and r["direction"]==direction and r["configuration"]==configuration],key=lambda r:r["dispersal_yr"])
                for r in group:
                    if r["settling_status"]!="census_stationary":continue
                    filled=r["endpoint_class"]=="coexistence"
                    ax.scatter(r["dispersal_yr"],r["global_temperature_k"],s=50,facecolor=color if filled else "white",edgecolor=color,
                        marker="o" if r["climate_domain"]=="arney" else "s")
                ax.plot([r["dispersal_yr"] for r in group],[r["global_temperature_k"] if r["settling_status"]=="census_stationary" else np.nan for r in group],color=color,label=configuration,alpha=.7)
            ax.set_xscale("log");ax.set_title(direction.replace("_"," "));ax.grid(alpha=.15);ax.set_xlabel("Cell exchange (per year)")
            ax.axhline(281.534823,color=".7",linestyle=":",linewidth=.8)
        axes[0].set_ylabel("Global temperature (K)")
        fig.suptitle(f"Buffered refuges; acetate conversion {f:g}")
        handles=[Line2D([],[],color=c,label=l) for l,c in zip(("none","warm","cold","both"),("#777777","#c56d36","#4c91a3","#7140a0"))]
        handles+=[Line2D([],[],color=".3",marker="o",linestyle="",label="filled: coexistence")]
        fig.legend(handles=handles,loc="outside lower center",ncol=5,frameon=False,fontsize=8)
        fig.savefig(output/f"main_f{f:g}.png",dpi=145);plt.close(fig)
    exemplars=[r for r in rows if r["configuration"]=="both" and r["fraction"]==.5 and r["dispersal_yr"]==1e-6]
    fig,axes=plt.subplots(2,2,figsize=(10,7),layout="constrained")
    for col,row in enumerate(sorted(exemplars,key=lambda r:r["direction"])):
        with gzip.open(raw/row["raw_file"],"rt") as stream:data=json.load(stream)["result"]
        t=np.asarray(data["t"]);ys=np.asarray(data["y"])
        p=e.parameters(e.Case(**{k:row[k] for k in e.Case.__dataclass_fields__}))
        axes[0,col].plot(t,[e.core.temperature_k(r,p.base.climate) for r in ys[-1]],color="#7140a0")
        logs=np.asarray(data["log_biomass"],dtype=float);logs=np.where(np.isnan(logs),-np.inf,logs)
        from scipy.special import logsumexp
        for i,g in enumerate(e.GUILDS):
            values=(logsumexp(logs[:,i,:]+np.log(p.weights[:,None]),axis=0)+data["metadata"]["global_log_cell_conversion"])/np.log(10.)
            axes[1,col].plot(t,values,label="acetogens" if g=="a" else "methanogens")
        for ax in axes[:,col]:ax.set_xscale("symlog",linthresh=20);ax.grid(alpha=.15)
        axes[0,col].set_title(row["direction"].replace("_"," "));axes[1,col].set_xlabel("Years after inoculation")
    axes[0,0].set_ylabel("Global temperature (K)");axes[1,0].set_ylabel("log₁₀ global cells");axes[1,0].legend(frameon=False)
    fig.suptitle("Two invasion histories; both 2% refuges; exchange 10⁻⁶/year")
    fig.savefig(output/"paired_trajectories.png",dpi=145);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=e.OUTPUT);parser.add_argument("--raw-dir",type=Path,default=e.RAW)
    parser.add_argument("--extension-manifest",type=Path,action="append",default=[]);parser.add_argument("--main-only",action="store_true")
    args=parser.parse_args();original=[];proof={}
    stages=("main",) if args.main_only else ("main","controls","sensitivity")
    for stage in stages:
        records,receipt=load(args.input/(stage+"_manifest.json"),args.raw_dir);original+=records;proof[stage]=receipt
    extensions=[]
    for path in args.extension_manifest:
        records,receipt=load(path,args.raw_dir);extensions+=records;proof[path.name]=receipt
    selected=select(original,extensions)
    rows=[diagnose(selected[key(r)],r,args.raw_dir) for r in original]
    climate_comparisons(rows);comp=pairs(rows)
    main_ids={c.case_id for c in e.design("main")}
    main_rows=[r for r in rows if r["base_case_id"] in main_ids]
    main_comp=pairs(main_rows);gate=assess_main(main_rows,main_comp)
    legacy=e.ROOT/"models/haze_world/figures/finite_populations/attained_endpoints.csv"
    checks=zero_refuge_checks(rows,legacy)
    e.table(args.input/"zero_refuge_checks.csv",checks)
    proof["single_habitat_controls"]=dict(file=str(legacy.relative_to(e.ROOT)),sha256=sha256(legacy.read_bytes()).hexdigest())
    for stage in stages:
        ids={c.case_id for c in e.design(stage)}
        e.table(args.input/f"selected_{stage}.csv",[{k:v for k,v in r.items() if k!="final_y"} for r in rows if r["base_case_id"] in ids])
    e.table(args.input/"direction_comparisons.csv",comp)
    summary=dict(inputs=proof,selected=len(rows),settling=dict(Counter(r["settling_status"] for r in rows)),
        classes=dict(Counter(r["endpoint_class"] or "unsettled" for r in rows)),**gate,
        matching_pairs=sum(bool(r.get("matching_endpoint")) for r in comp),
        coexisting_matching_pairs=sum(bool(r.get("matching_endpoint")) and bool(r.get("both_coexist")) for r in comp),
        domain_exits=sum(r["attempt_status"]!="completed" for r in rows),
        zero_refuge_controls=len(checks),matching_zero_refuge_controls=sum(r["matching_endpoint"] for r in checks),
        maximum_abs_temperature_mean_departure_k=max(r["maximum_abs_temperature_mean_departure_k"] for r in rows),
        surviving_subcellular_excursions=sum(bool(r.get("surviving_subcellular_"+g)) for r in rows for g in e.GUILDS),
        B5_max_abs_matched_community_contrast_k=max(abs(r["community_temperature_contrast_k"]) for r in rows
            if r["fraction"]==.9 and r["configuration"] in ("warm","both") and r["settling_status"]=="census_stationary"),
        source_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    (args.input/"reporting_manifest.json").write_text(e.dumps(summary)+"\n")
    plots(main_rows,args.raw_dir,args.input)
    print(e.dumps(summary))


if __name__=="__main__":main()
