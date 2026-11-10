"""Endpoint agreement and probability links for the turnover/dormancy stage."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from . import buffered_experiments as e
from . import turnover_survival as survival


def methane_tail(data,p):
    """Check the exact abiotic relaxation after methanogens are absent."""
    late=np.asarray(data["t"])>=max(0.,float(data["t"][-1])-20000.)
    sample=np.asarray(data["y"])[:,late];times=np.asarray(data["t"])[late]
    if (p.base.acetate_fraction!=0 or p.base.loss.kind!="power" or p.base.loss.elasticity!=1
        or np.any(sample[p.biomass_indices[:,1]]!=0)):
        return dict(kind="not_an_exact_abiotic_tail")
    from . import habitat_coupling as habitat
    forcing=habitat.fluxes(sample[:,-1],p)["abiotic_ratio_yr"]
    tau=p.base.loss.lifetime_yr;equilibrium=forcing*tau
    expected=equilibrium+(sample[-1,0]-equilibrium)*np.exp(-(times-times[0])/tau)
    return dict(kind="exact_abiotic_relaxation",time_constant_yr=tau,equilibrium_methane_ratio=equilibrium,
        late_window_start_yr=float(times[0]),maximum_methane_ratio_residual=float(max(abs(sample[-1]-expected))),
        final_methane_ratio_excess=float(sample[-1,-1]-equilibrium),
        mechanism="With no methanogens and no acetate recycling, methane has constant abiotic input and linear loss. The remaining drift decays exponentially on this absorbing population face.")


def refuge_forcing(y,p):
    """Climate response to the endpoint's refuge flux, with bulk methane omitted."""
    if p.base.acetate_fraction!=0 or not np.any(p.weights[1:]>0):return None
    from . import habitat_coupling as habitat,habitat_equilibria as equilibria
    from . import population_coupling as core
    flows=habitat.fluxes(y,p)
    source=flows["abiotic_ratio_yr"]+core.inventory_to_ratio(p.base)*sum(
        w*f["methane_local_mol_l_yr"] for j,(w,f) in enumerate(zip(p.weights,flows["local"])) if j and f is not None)
    ratio=p.base.loss.inverse(source);temperature=float(core.temperature_k(ratio,p.base.climate))
    resident=equilibria.local_resident(ratio,temperature,p.base,0)
    growth=None if resident is None else float(core.fluxes_at_temperature(resident,p.base,temperature)["net_growth_yr"][1])
    return dict(methane_ratio=ratio,temperature_k=temperature,methanogen_growth_on_local_acetogen_resident_yr=growth,
        scope="Hold the recorded refuge methane flux fixed and omit bulk methane. This is a forcing/invasion diagnostic, not a separately solved spatial equilibrium.")


def compare(a,b,pa,pb,dormant=False):
    sa,sb=a["summary"],b["summary"]
    ya,yb=pa["y"][:,-1],pb["y"][:,-1]
    n=(len(ya)-1)//(6 if dormant else 4)
    parameters=a["protocol"]["parameters"]
    if dormant:parameters=parameters["base"]
    weights=np.array([v["weight"] for v in parameters["patches"]])
    other=b["protocol"]["parameters"]
    if dormant:other=other["base"]
    if weights.tolist()!=[v["weight"] for v in other["patches"]]:
        raise ValueError("Endpoint pairs require the same habitat geometry")
    density_floors=[]
    for profile in (pa,pb):
        one_cell=np.exp(-profile["metadata"]["global_log_cell_conversion"])
        density_floors.append(np.divide(one_cell,weights,out=np.full(n,np.inf),where=weights>0))
    density_floor=np.maximum(*density_floors)
    floor=np.r_[np.array([[1.,v,v,1e-9,v,v] if dormant else [1.,v,v,1e-9] for v in density_floor]).ravel(),.001]
    differences=abs(ya-yb)/np.maximum.reduce([abs(ya),abs(yb),floor])
    relative=float(max(differences))
    stationary=all(s["settling_status"]=="census_stationary" for s in (sa,sb))
    stride=6 if dormant else 4
    stocks=[v[:-1].reshape(n,stride)[:,1:3].copy() for v in (ya,yb)]
    if dormant:
        for v,stock in zip((ya,yb),stocks):stock+=v[:-1].reshape(n,stride)[:,4:6]
    occupancy=[(stock>=limit[:,None]*(1.-1e-10))&(weights[:,None]>0)
               for stock,limit in zip(stocks,density_floors)]
    local_presence=bool(np.array_equal(*occupancy))
    presence=bool(np.array_equal(np.any(occupancy[0],axis=0),np.any(occupancy[1],axis=0)))
    temperature="temperature_k" if dormant else "global_temperature_k"
    difference=abs(sa[temperature]-sb[temperature])
    fields=("hydrogen_pa","active_a","active_m","acetate_mol_l","dormant_a","dormant_m") if dormant else ("hydrogen_pa","active_a","active_m","acetate_mol_l")
    labels=[f"{patch.get('name',str(j))}:{field}" for j,patch in enumerate(parameters["patches"]) for field in fields]+["methane_ratio"]
    return dict(both_stationary=stationary,same_global_occupancy=presence,same_local_occupancy=local_presence,
                local_occupancy_first=";".join("".join("1" if x else "0" for x in row) for row in occupancy[0]),
                local_occupancy_second=";".join("".join("1" if x else "0" for x in row) for row in occupancy[1]),
                temperature_difference_k=difference,maximum_relative_stock_difference=relative,
                largest_difference_stock=labels[int(np.argmax(differences))],
                methane_ratio_relative_difference=float(differences[-1]),
                same_endpoint=bool(stationary and presence and local_presence and difference<.01 and relative<.001))


def plot_pairs(rows,output):
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap,BoundaryNorm
    from matplotlib.patches import Patch
    layouts=(("none",0.),("both_absolute",1e-6),("both_absolute",.001),
             ("both_relative",1e-6),("both_relative",.001),("warm_relative",1e-6),("warm_relative",.001))
    losses=sorted({v["loss_h"] for v in rows});fractions=sorted({v["fraction"] for v in rows})
    colors=["#cbd5e1","#e8a16c","#70b6a1"]
    fig,axes=plt.subplots(1,len(fractions),figsize=(11.5,4.8),sharey=True,squeeze=False)
    for ax,fraction in zip(axes[0],fractions):
        values=np.full((len(losses),len(layouts)),np.nan)
        for row in rows:
            if row["fraction"]!=fraction:continue
            i,j=losses.index(row["loss_h"]),layouts.index((row["layout"],row["dispersal_yr"]))
            values[i,j]=0 if not row["both_stationary"] else 2 if row["same_endpoint"] else 1
            tag={"coexistence":"C","acetogen_only":"A","methanogen_only":"M","empty":"0"}.get(row["a_into_m_endpoint"],"")
            text="?" if not row["both_stationary"] else "="+tag if row["same_endpoint"] else "≠"
            ax.text(j,i,text,ha="center",va="center",fontsize=12)
        ax.imshow(values,cmap=ListedColormap(colors),norm=BoundaryNorm([-.5,.5,1.5,2.5],3),aspect="auto",origin="lower")
        ax.set_xticks(range(len(layouts)),["none","absolute\n10⁻⁶","absolute\n10⁻³","relative\n10⁻⁶","relative\n10⁻³","warm\nrelative\n10⁻⁶","warm\nrelative\n10⁻³"],fontsize=8)
        ax.set_yticks(range(len(losses)),[f"{v*1e4:g}" for v in losses])
        ax.set_title(f"Acetate recycling f = {fraction:g}")
        ax.set_xlabel("Refuge layout and exchange rate (yr⁻¹)")
    axes[0,0].set_ylabel("Cell loss L (10⁻⁴ h⁻¹)")
    fig.legend(handles=[Patch(color=colors[2],label="Same complete endpoint"),Patch(color=colors[1],label="Different endpoints"),Patch(color=colors[0],label="Not both stationary")],loc="lower center",ncol=3,frameon=False)
    fig.suptitle("Opposite invasion histories: climate, occupancy and every stock\nC: both guilds globally; A/M: one guild globally",fontsize=12)
    fig.tight_layout(rect=(0,.08,1,.95));fig.savefig(output/"endpoint_pairs.png",dpi=180);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant",choices=("turnover","dormancy"),required=True)
    parser.add_argument("--raw-dir",type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args();dormant=args.variant=="dormancy"
    if dormant:
        from . import dormancy_experiments as runner
    else:
        from . import turnover_experiments as runner
    raw=args.raw_dir or runner.RAW;output=args.output or runner.OUTPUT
    gate_path=e.ROOT/"models/haze_world/figures/turnover/basins_gate.json"
    gate=json.loads(gate_path.read_text())
    if not gate["gate_passed"] or any(sha256((e.ROOT/name).read_bytes()).hexdigest()!=digest
                                      for name,digest in gate["source_sha256"].items()):
        raise RuntimeError("The preceding T1 gate is not current")
    records=survival.records(raw,"census")
    designed=runner.design()
    missing=[c.case_id for c in designed if c.case_id not in records or records[c.case_id]["protocol"]["case"]["years"]<c.years]
    if missing:raise RuntimeError("Missing planned census horizons: "+", ".join(missing))
    groups={};summaries=[];endpoint_details=[]
    for case in designed:
        record=records[case.case_id]
        names=("group","fraction","epsilon","configuration","dispersal_yr","loss_h","switching_factor","ramp") if dormant else ("loss_h","fraction","layout","dispersal_yr")
        key=tuple(getattr(case,n) for n in names)
        groups.setdefault(key,{})[case.direction]=record
        summaries.append(record["summary"])
    paired=[]
    for key,group in sorted(groups.items()):
        a,b=(group[name] for name in ("A_into_M","M_into_A"))
        profiles=[survival.load(record,raw) for record in (a,b)]
        for record,profile in zip((a,b),profiles):
            params=record["protocol"]["parameters"]
            if dormant:params=params["base"]
            detail=dict(case_id=record["protocol"]["case"]["case_id"],
                horizon_yr=record["protocol"]["case"]["years"],
                state_order="Per patch: H2[Pa], activeA[gDW/L], activeM[gDW/L], acetate[M]"+
                    (", dormantA[gDW/L], dormantM[gDW/L]" if dormant else "")+"; then CH4/CO2 ratio",
                patches=[v["name"] for v in params["patches"]],weights=[v["weight"] for v in params["patches"]],
                y=profile["y"][:,-1].tolist(),global_log_cell_conversion=profile["metadata"]["global_log_cell_conversion"],
                summary={k:v for k,v in record["summary"].items() if k.startswith(("occupancy_","cells_","net_growth_","exchange_","catabolic_share_"))})
            if not dormant:
                p=runner.parameters(runner.Case(**record["protocol"]["case"]))
                detail["refuge_flux_diagnostic"]=refuge_forcing(profile["y"][:,-1],p)
            endpoint_details.append(detail)
        row=dict(zip(names,key));row.update(case_a_into_m=a["protocol"]["case"]["case_id"],
            case_m_into_a=b["protocol"]["case"]["case_id"],
            horizon_a_into_m_yr=a["protocol"]["case"]["years"],horizon_m_into_a_yr=b["protocol"]["case"]["years"],
            a_into_m_endpoint=a["summary"]["endpoint_class"],m_into_a_endpoint=b["summary"]["endpoint_class"],
            temperature_a_into_m_k=a["summary"]["temperature_k" if dormant else "global_temperature_k"],
            temperature_m_into_a_k=b["summary"]["temperature_k" if dormant else "global_temperature_k"],
            **compare(a,b,*profiles,dormant))
        for prefix,record in (("a_into_m",a),("m_into_a",b)):
            summary=record["summary"]
            row[prefix+"_bulk_occupancy"]=summary.get("occupancy_bulk")
            for guild in e.GUILDS:
                row[prefix+"_bulk_share_"+guild]=summary.get("catabolic_share_bulk_"+guild)
                row[prefix+"_global_share_"+guild]=summary.get("global_catabolic_share_"+guild)
            shares=[row[prefix+"_bulk_share_"+g] for g in e.GUILDS]
            row[prefix+"_bulk_materially_mixed"]=all(v is not None and v>=.01 for v in shares)
            switches=summary.get("switch_temperatures_k",[])
            temperature=summary["temperature_k" if dormant else "global_temperature_k"]
            row[prefix+"_temperature_minus_switch_k"]=temperature-switches[0] if len(switches)==1 else None
        paired.append(row)
    output.mkdir(parents=True,exist_ok=True)
    e.table(output/"endpoint_pairs.csv",paired)
    if not dormant:plot_pairs(paired,output)
    canonical="dormancy.csv" if dormant else "refuges.csv"
    e.table(output/canonical,summaries)
    manifest=dict(planned_cases=len(designed),endpoint_pairs=len(paired),
        preceding_gate_sha256=sha256(gate_path.read_bytes()).hexdigest(),
        preceding_gate_scope=gate["scope_for_following_stages"],
        stationarity_counts=dict(Counter(v["settling_status"] for v in summaries)),
        endpoints=dict(Counter(v["endpoint_class"] for v in summaries)),
        pair_counts=dict(Counter("same" if v["same_endpoint"] else "unsettled" if not v["both_stationary"] else "different" for v in paired)),
        receipts=[dict(case_id=c.case_id,**{k:records[c.case_id][k] for k in ("fingerprint","raw_file","raw_sha256")}) for c in designed],
        pair_comparisons=paired,endpoint_states=endpoint_details,
        physical_source_sha256=runner.sources(),
        selected_numerical_protocols=[dict(case_id=c.case_id,fingerprint=records[c.case_id]["fingerprint"],
            solver=records[c.case_id]["protocol"].get("solver","native_frozen"),
            numerical_source_sha256={k:v for k,v in records[c.case_id]["protocol"]["source_sha256"].items()
                                    if k not in runner.sources()}) for c in designed],
        receipt_selection_sha256=sha256((raw/"receipt_selection.json").read_bytes()).hexdigest()
            if (raw/"receipt_selection.json").exists() else None,
        source_sha256={str(Path(__file__).relative_to(e.ROOT)):sha256(Path(__file__).read_bytes()).hexdigest()},
        agreement="Both census-stationary; same local and global guild occupancy at the actual one-cell floor, delta T<0.01K, every stock relative difference<0.001. Biomass floors are the larger actual one-cell density of the two profiles; pressure1Pa, acetate1e-9M, methane ratio0.001. Same temperature alone does not imply the same community.")
    (output/"endpoint_assessment.json").write_text(e.dumps(manifest)+"\n")


if __name__=="__main__":main()
