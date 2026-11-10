"""Read qualified refuge receipts and emit endpoint, comparison and map artifacts."""

import argparse
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from . import refuge_coupling as model
from . import refuge_experiments as experiments
from .finite_experiments import clean, dumps


def load_manifest(path, raw_dir):
    manifest = json.loads(path.read_text())
    if manifest["source_sha256"] != experiments.source_hashes():
        raise RuntimeError(f"Source differs from qualified batch: {path.name}")
    records = []
    for entry in manifest["receipts"]:
        receipt = raw_dir / entry["raw_file"].replace(".json.gz", ".receipt.json")
        record = json.loads(receipt.read_text())
        raw = raw_dir / entry["raw_file"]
        if (record["execution_status"] != "complete" or record["fingerprint"] != entry["fingerprint"]
                or record["raw_sha256"] != entry["raw_sha256"]
                or sha256(raw.read_bytes()).hexdigest() != entry["raw_sha256"]):
            raise RuntimeError(f"Unqualified refuge receipt: {entry['case_id']}")
        records.append(record)
    if len(records) != manifest["cases"]:
        raise RuntimeError("Incomplete manifest")
    return records, dict(file=path.name, sha256=sha256(path.read_bytes()).hexdigest(), cases=len(records))


def case_key(record):
    return tuple((key, value) for key, value in record["protocol"]["case"].items()
                 if key not in ("case_id", "years"))


def choose_extensions(original, extensions):
    selected = {case_key(record): record for record in original}
    for record in extensions:
        key = case_key(record)
        if key not in selected:
            raise RuntimeError("Extension has no original case")
        current = selected[key]
        def comparable(item):
            value = dict(item["protocol"])
            value["case"] = {k: v for k, v in value["case"].items() if k not in ("case_id", "years")}
            return dumps(value)
        if comparable(current) != comparable(record):
            raise RuntimeError("Extension changed more than its duration")
        if record["protocol"]["case"]["years"] > current["protocol"]["case"]["years"]:
            selected[key] = record
    return selected


def physical_state(row, p):
    volume = p.base.habitat_l_cm2 * 5.1e18 * p.weights
    result = np.zeros(9)
    for j, patch in enumerate(("cold", "warm")):
        result[4*j] = row[f"pressure_{patch}_pa"]
        for i, guild in enumerate(("a", "m")):
            result[4*j+1+i] = row[f"cells_{patch}_{guild}"] * 3e-13 / volume[j]
        result[4*j+3] = row[f"acetate_{patch}_mol_l"]
    result[8] = row["methane_ratio"]
    return result


def diagnose(record, base_record):
    row = dict(record["summary"])
    case = experiments.Case(**record["protocol"]["case"])
    p = experiments.parameters(case)
    row.update(base_case_id=base_record["protocol"]["case"]["case_id"],
               selected_case_id=case.case_id, selected_horizon_yr=case.years,
               selected_raw_sha256=record["raw_sha256"],
               later_horizon=case.years > base_record["protocol"]["case"]["years"])
    if row["conditional_selected_ratio"] is not None:
        initial_temperature = float(model.core.temperature_k(row["conditional_selected_ratio"], p.base.climate))
        row["initial_global_temperature_k"] = initial_temperature
        row["initial_cold_temperature_k"], row["initial_warm_temperature_k"] = initial_temperature + p.offsets
        if case.activity == "fixed":
            resident = 1 if case.direction == "A_into_M" else 0
            advantages = []
            for temperature in initial_temperature + p.offsets:
                pair = model.core.guilds(float(temperature - 273.15), p.base.biology)
                advantages.append(pair[resident].rstar(p.base.biology.loss_h) < pair[1-resident].rstar(p.base.biology.loss_h))
            row["resident_favorable_patch_initially"] = any(advantages)
            row["resident_favorable_cold_initially"], row["resident_favorable_warm_initially"] = advantages
    if row["settling_status"] != "census_stationary":
        return clean(row)
    y = physical_state(row, p)
    f = model.fluxes(y, p)
    linearization=experiments.equilibria.describe(y,p)
    row["terminal_linearization_max_real_yr"]=linearization["max_real_yr"]
    row["terminal_scaled_rhs_residual"]=linearization["max_scaled_residual"]
    for i, guild in enumerate(("a", "m")):
        growth = np.array([local["net_growth_yr"][i] for local in f["local"]])
        migration = p.dispersal_yr * np.array([[-p.weights[1], p.weights[1]], [p.weights[0], -p.weights[0]]])
        matrix = np.diag(growth) + migration
        row[f"instantaneous_rare_growth_{guild}_yr"] = float(max(np.linalg.eigvals(matrix).real))
        row[f"global_present_{guild}"] = any(row[f"cells_{patch}_{guild}"] > 0 for patch in ("cold", "warm"))
        minimum = row.get(f"global_pre_extinction_min_log_cells_{guild}")
        row[f"surviving_subcellular_excursion_{guild}"] = bool(row[f"global_present_{guild}"] and
            (row.get(f"global_pre_extinction_min_zero_{guild}", False) or minimum is not None and minimum < 0))
    row["protected_partition"] = bool(case.activity == "fixed" and case.dispersal_yr == 0
        and row["endpoint_class"] == "pure_partition"
        and f["local"][0]["net_growth_yr"][1] < 0 and f["local"][1]["net_growth_yr"][0] < 0)
    row["native_partition_99percent"] = bool(row["catabolic_share_cold_a"] >= .99 and row["catabolic_share_warm_m"] >= .99)
    row["biomass_contrast_relative"] = float(max(abs(y[[1,2]]-y[[5,6]]) /
        np.maximum((y[[1,2]]+y[[5,6]])/2, 1e-30)))
    return clean(row)


def direction_pairs(rows):
    groups = {}
    for row in rows:
        case = {name: row[name] for name in experiments.Case.__dataclass_fields__}
        key = tuple((k,v) for k,v in case.items() if k not in ("case_id", "years", "direction"))
        groups.setdefault(key, {})[row["direction"]] = row
    result = []
    for key, pair in groups.items():
        if len(pair) != 2:
            continue
        first, second = pair["A_into_M"], pair["M_into_A"]
        qualified = all(r["settling_status"] == "census_stationary" for r in (first,second))
        item = dict(key, both_stationary=qualified, case_a=first["base_case_id"], case_m=second["base_case_id"],
                    status_a=first["attempt_status"], status_m=second["attempt_status"],
                    class_a=first["endpoint_class"],class_m=second["endpoint_class"],
                    both_initially_favorable=all(r.get("resident_favorable_patch_initially",False) for r in (first,second)))
        if qualified:
            p = experiments.parameters(experiments.Case(**{name:first[name] for name in experiments.Case.__dataclass_fields__}))
            a,b = physical_state(first,p),physical_state(second,p)
            scales = np.maximum((abs(a)+abs(b))/2,[1.,1e-20,1e-20,1e-9,1.,1e-20,1e-20,1e-9,.001])
            difference = float(max(abs(a-b)/scales))
            occupancy = all(first["occupancy_"+patch] == second["occupancy_"+patch] for patch in ("cold","warm"))
            item.update(global_temperature_difference_k=abs(first["global_temperature_k"]-second["global_temperature_k"]),
                        maximum_relative_stock_difference=difference, identical_occupancy=occupancy,
                        matching_endpoint=bool(occupancy and difference<.001))
        result.append(clean(item))
    return result


def zero_contrast_checks(rows, path):
    with path.open() as stream:
        legacy=list(csv.DictReader(stream))
    result=[]
    for row in rows:
        if row["contrast_k"]!=0 or row["settling_status"]!="census_stationary":
            continue
        matches=[old for old in legacy if old["activity"]==row["activity"]
                 and float(old["fraction"])==row["fraction"] and old["direction"]==row["direction"]
                 and float(old["minimum_cells"])==1 and float(old["relative_immigration_yr"])==0
                 and float(old["census_yr"])==row["census_yr"]]
        if len(matches)!=1:
            raise RuntimeError("Zero-contrast check needs a unique single-habitat control")
        old=matches[0]
        item=dict(case_id=row["base_case_id"],single_case_id=old["selected_case_id"],
                  temperature_difference_k=abs(row["global_temperature_k"]-float(old["temperature_k"])),
                  methane_ratio_difference=abs(row["methane_ratio"]-float(old["methane_ratio"])))
        cell_errors=[]
        for guild in ("a","m"):
            cells=sum(row[f"cells_{patch}_{guild}"] for patch in ("cold","warm"))
            previous=float(old[f"cells_{guild}"])
            cell_errors.append(abs(cells-previous)/max((cells+previous)/2,1.))
            first=[row[f"first_cull_{patch}_{guild}_yr"] for patch in ("cold","warm")]
            item[f"first_cull_{guild}_yr_single"]=float(old[f"first_cull_{guild}_yr"]) if old[f"first_cull_{guild}_yr"] else None
            item[f"first_cull_{guild}_yr_cold"],item[f"first_cull_{guild}_yr_warm"]=first
        item["maximum_relative_cell_difference"]=max(cell_errors)
        item["matching_endpoint"]=(item["temperature_difference_k"]<.001 and item["methane_ratio_difference"]<1e-6
                                    and max(cell_errors)<.001)
        result.append(clean(item))
    return result


def plots(rows, equilibrium_rows, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    colors = dict(zip((0.,1e-6,1e-3,1.),("#202020","#377eb8","#4d9b67","#c87537")))
    domains = {"arney":"o","bridge":"s","plateau":"^"}
    for direction in ("A_into_M","M_into_A"):
        fig,axes=plt.subplots(3,3,figsize=(11,8),sharex=True,sharey=True,layout="constrained")
        for i,fraction in enumerate((0.,.5,.9)):
            for j,warm in enumerate((.1,.5,.9)):
                ax=axes[i,j]
                for d,color in colors.items():
                    selected=sorted([r for r in rows if r["fraction"]==fraction and r["warm_fraction"]==warm
                                     and r["dispersal_yr"]==d and r["direction"]==direction],key=lambda r:r["contrast_k"])
                    ax.plot([r["contrast_k"] for r in selected],
                            [r["global_temperature_k"] if r["settling_status"]=="census_stationary" else np.nan for r in selected],
                            color=color,linewidth=1,alpha=.8)
                    for r in selected:
                        if r["settling_status"]=="census_stationary":
                            measured=all(r["physiology_"+p]=="measured" for p in ("cold","warm"))
                            ax.scatter(r["contrast_k"],r["global_temperature_k"],marker=domains.get(r["climate_domain"],"D"),
                                       edgecolor=color,facecolor=color if measured else "white",s=28,zorder=4)
                        else:
                            ax.plot(r["contrast_k"],.025+.022*list(colors).index(d),marker="x",color=color,
                                    transform=ax.get_xaxis_transform(),markersize=4)
                threshold=(8.02/(1-warm) if direction=="A_into_M" else
                           (12.87/warm if fraction==.5 else 1.66/warm if fraction==0 else None))
                if threshold is not None and threshold<=30:
                    ax.axvline(threshold,color=".65",linestyle=":",linewidth=1)
                ax.set_title(f"f={fraction:g}; warm area={warm:g}",fontsize=10)
                ax.set_xticks((0,10,20,30));ax.grid(alpha=.15)
                if i==2:ax.set_xlabel("Patch contrast (K)")
                if j==0:ax.set_ylabel("Global temperature (K)")
        fig.suptitle("Acetogens invade methanogens" if direction=="A_into_M" else "Methanogens invade acetogens")
        handles=[Line2D([],[],color=c,label=f"exchange {d:g}/yr") for d,c in colors.items()]
        handles += [Line2D([],[],marker=m,color=".4",linestyle="",label=name) for name,m in domains.items()]
        handles += [Line2D([],[],marker="o",markerfacecolor="white",color=".4",linestyle="",label="cold continuation"),
                    Line2D([],[],marker="x",color=".4",linestyle="",label="no qualified endpoint")]
        fig.legend(handles=handles,loc="outside lower center",ncol=5,frameon=False,fontsize=8)
        fig.savefig(output/f"invasion_{direction}.png",dpi=145);plt.close(fig)
    if equilibrium_rows:
        fig,axes=plt.subplots(3,2,figsize=(10,9),layout="constrained",sharex=True,sharey=True)
        scatter=None
        for i,fraction in enumerate((0.,.5,.9)):
            for j,d in enumerate((0.,.001)):
                ax=axes[i,j]
                selected=[r for r in equilibrium_rows if r["fraction"]==fraction and r["dispersal_yr"]==d and r["stability"]=="stable"]
                for measured,marker in ((True,"o"),(False,"^")):
                    group=[r for r in selected if r["measured"]==measured]
                    if group:
                        scatter=ax.scatter([r["warm_fraction"] for r in group],[r["contrast_k"] for r in group],
                            c=[r["global_temperature_k"] for r in group],cmap="viridis",vmin=273,vmax=297,marker=marker,s=32)
                ax.set_title(f"f={fraction:g}; exchange={d:g}/yr",fontsize=10)
                ax.set_ylim(-1,31);ax.set_yticks((0,5,10,15,20,30))
                if i==2:ax.set_xlabel("Warm area fraction")
                if j==0:ax.set_ylabel("Contrast (K)")
                ax.grid(alpha=.15)
        if scatter is not None:fig.colorbar(scatter,ax=axes,label="Global temperature (K)",shrink=.8)
        fig.suptitle("Detected locally stable equilibria: circles measured; triangles cold continuation")
        fig.savefig(output/"stable_equilibria.png",dpi=145);plt.close(fig)


def rescue_plot(records, raw_dir, output):
    import gzip
    import matplotlib.pyplot as plt
    from scipy.special import logsumexp
    fig,axes=plt.subplots(3,2,figsize=(10,8),layout="constrained")
    for i,fraction in enumerate((0.,.5,.9)):
        for contrast,color in ((8.4,"#777777"),(8.6,"#336b9d")):
            selected=[r for r in records if all(r["protocol"]["case"][k]==v for k,v in
                dict(fraction=fraction,warm_fraction=.05,contrast_k=contrast,dispersal_yr=.001,
                     direction="A_into_M",activity="fixed",seed_origin="both",census_yr=10.).items())]
            if len(selected)!=1:
                raise RuntimeError("Rescue figure requires one qualified record per frozen comparison")
            record=selected[0]
            with gzip.open(raw_dir/record["raw_file"],"rt") as stream:
                result=json.load(stream)["result"]
            if result is None:
                continue
            t=np.asarray(result["t"])
            y=np.asarray(result["y"])
            p=experiments.parameters(experiments.Case(**record["protocol"]["case"]))
            temperature=np.array([model.core.temperature_k(r,p.base.climate) for r in y[8]])
            logs=np.asarray(result["log_biomass"],dtype=float)[:,1,:]
            logs=np.where(np.isnan(logs),-np.inf,logs)
            total=logsumexp(logs+np.log(p.weights[:,None]),axis=0)
            log_cells=(total+result["metadata"]["global_log_cell_conversion"])/np.log(10.)
            axes[i,0].plot(t,temperature,color=color,label=f"contrast {contrast:g} K")
            axes[i,1].plot(t,np.where(np.isfinite(log_cells),log_cells,np.nan),color=color)
            minimum=record["summary"].get("global_pre_extinction_min_log_cells_m")
            if minimum is not None:
                axes[i,1].scatter(record["summary"]["global_pre_extinction_min_time_m_yr"],
                                  minimum/np.log(10.),marker="D",s=20,color=color,zorder=4)
            if result["status"]=="domain_exit":
                axes[i,0].plot(t[-1],temperature[-1],marker="x",color=color)
            if np.isneginf(total[-1]):
                axes[i,1].text(.98,.08 if contrast==8.4 else .17,f"{contrast:g} K: M removed",
                               transform=axes[i,1].transAxes,ha="right",color=color,fontsize=8)
        for ax in axes[i]:
            ax.set_xscale("symlog",linthresh=20)
            ax.set_title(f"Acetate fraction {fraction:g}",fontsize=10)
            ax.grid(alpha=.15)
            if i==2:ax.set_xlabel("Years after acetogen inoculation")
        axes[i,0].set_ylabel("Global temperature (K)")
        axes[i,1].set_ylabel("log₁₀ global methanogen cells")
        axes[i,1].axhline(0,color=".6",linewidth=.7,linestyle=":")
    axes[0,0].legend(frameon=False,fontsize=8)
    fig.suptitle("A small warm refuge: 5% warm area; exchange 0.001/year")
    fig.savefig(output/"warm_refuge_rescue.png",dpi=145);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=experiments.OUTPUT)
    parser.add_argument("--raw-dir",type=Path,default=experiments.RAW)
    parser.add_argument("--output",type=Path,default=experiments.OUTPUT)
    parser.add_argument("--extension-manifest",action="append",type=Path,default=[])
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    stages={};provenance={}
    for stage in ("main","subsets","equilibria"):
        stages[stage],provenance[stage]=load_manifest(args.input/f"{stage}_manifest.json",args.raw_dir)
    original=stages["main"]+stages["subsets"]
    extensions=[]
    for path in args.extension_manifest:
        records,proof=load_manifest(path,args.raw_dir);extensions.extend(records);provenance[str(path.name)]=proof
    selected=choose_extensions(original,extensions)
    rows=[diagnose(selected[case_key(record)],record) for record in original]
    for stage in ("main","subsets"):
        ids={r["protocol"]["case"]["case_id"] for r in stages[stage]}
        experiments.public_table(args.output,f"selected_{stage}.csv",[r for r in rows if r["base_case_id"] in ids])
    subset_ids={r["protocol"]["case"]["case_id"] for r in stages["subsets"]}
    fields=[*experiments.Case.__dataclass_fields__,"selected_case_id","selected_horizon_yr",
            "attempt_status","settling_status","endpoint_class","global_temperature_k","climate_domain",
            "temperature_cold_k","temperature_warm_k","physiology_cold","physiology_warm",
            "occupancy_cold","occupancy_warm","global_catabolic_share_a","global_catabolic_share_m",
            "global_pre_extinction_min_log_cells_a","global_pre_extinction_min_log_cells_m",
            "global_after_census_min_zero_a","global_after_census_min_zero_m",
            "path_min_temperature_cold_k","path_max_temperature_warm_k","domain_exit_time_yr",
            "resident_favorable_patch_initially","surviving_subcellular_excursion_a","surviving_subcellular_excursion_m"]
    fields += ["protected_partition","terminal_linearization_max_real_yr","terminal_scaled_rhs_residual"]
    experiments.public_table(args.output,"sensitivity_overview.csv",
                             [{k:r.get(k) for k in fields} for r in rows if r["base_case_id"] in subset_ids])
    pairs=direction_pairs(rows);experiments.public_table(args.output,"direction_comparisons.csv",pairs)
    legacy=experiments.ROOT/"models/haze_world/figures/finite_populations/attained_endpoints.csv"
    controls=zero_contrast_checks(rows,legacy)
    experiments.public_table(args.output,"zero_contrast_checks.csv",controls)
    provenance["single_habitat_controls"]=dict(file=str(legacy.relative_to(experiments.ROOT)),sha256=sha256(legacy.read_bytes()).hexdigest())
    equilibrium_rows=[]
    for record in stages["equilibria"]:
        with __import__("gzip").open(args.raw_dir/record["raw_file"],"rt") as stream:
            payload=json.load(stream)
        equilibrium_rows.extend(dict(**record["protocol"]["case"],**{k:v for k,v in e.items() if k!="y"}) for e in payload["candidates"])
    main_ids={r["protocol"]["case"]["case_id"] for r in stages["main"]}
    plots([r for r in rows if r["base_case_id"] in main_ids],equilibrium_rows,args.output)
    rescue_plot(list(selected.values()),args.raw_dir,args.output)
    summary=dict(inputs=provenance,selected=len(rows),later_horizons=sum(r["later_horizon"] for r in rows),
        statuses=dict(Counter(r["attempt_status"] for r in rows)),settling=dict(Counter(r["settling_status"] for r in rows)),
        classes=dict(Counter(r["endpoint_class"] or "no_qualified_endpoint" for r in rows)),
        qualified_direction_pairs=sum(r["both_stationary"] for r in pairs),
        matching_direction_pairs=sum(bool(r.get("matching_endpoint")) for r in pairs),
        qualified_zero_contrast_controls=len(controls),matching_zero_contrast_controls=sum(r["matching_endpoint"] for r in controls),
        initially_favorable_pairs_f_le_half=sum(r["fraction"]<=.5 and r["both_initially_favorable"] for r in pairs),
        surviving_subcellular_excursions=sum(bool(r.get("surviving_subcellular_excursion_"+g)) for r in rows for g in ("a","m")),
        stationary_by_fraction={str(f):dict(Counter(r["endpoint_class"] for r in rows
            if r["fraction"]==f and r["settling_status"]=="census_stationary")) for f in (0.,.5,.9)},
        source_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    (args.output/"reporting_manifest.json").write_text(dumps(summary)+"\n")
    print(dumps(summary))


if __name__=="__main__":
    main()
