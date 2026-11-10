"""Check KT4's first-minimum counterexample on a finer physical output grid."""

from dataclasses import asdict
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import platform

import numpy as np

from terra_prisca.haze_world import turnover_experiments as run
from terra_prisca.haze_world import turnover_survival as score


if __name__=="__main__":
    record=score.records(run.RAW,"uncensored")["refuges_0002"]
    original=score.load(record,run.RAW)
    case=run.Case(**record["protocol"]["case"]);p=run.parameters(case)
    protocol=dict(case=asdict(case),initial_raw_sha256=record["raw_sha256"],
        source_sha256=run.sources(),years=5000.,census_minimum_cells=0.,sampling_yr=.5,
        max_step_yr=10.,rtol=2e-8)
    folder=run.RAW/"controls";folder.mkdir(exist_ok=True)
    path=folder/"refuges_0002_halfyear.npz";receipt=path.with_suffix(".receipt.json")
    if receipt.exists():
        saved=json.loads(receipt.read_text())
        if saved["protocol"]!=protocol or sha256(path.read_bytes()).hexdigest()!=saved["raw_sha256"]:
            raise RuntimeError("Changed numerical control")
    else:
        result=run.integrate_finite(original["initial"],p,5000.,run.Census(minimum_cells=0.,census_yr=.5),
                                    sample_every_censuses=1,max_step=10.,rtol=2e-8)
        if result.status!="completed":raise RuntimeError("Incomplete half-year control")
        np.savez_compressed(path,t=result.t,y=result.y,log_biomass=result.log_biomass,
                            metadata=run.e.dumps(result.metadata))
        saved=dict(protocol=protocol,raw_file=str(path.relative_to(run.e.ROOT)),
                   raw_sha256=sha256(path.read_bytes()).hexdigest())
        receipt.write_text(run.e.dumps(saved)+"\n")
    with np.load(path,allow_pickle=False) as data:
        finer={k:data[k] for k in data.files}
    finer["metadata"]=json.loads(str(finer["metadata"]))
    checks=[]
    for label,data,stride,step in (("annual",original,1.,1.),("two_year_rates",original,2.,.5),
                                   ("four_year_rates",original,4.,.5),("half_year_physical",finer,.5,.25)):
        value=score.analyze(data,p,0,rate_stride=stride,max_step=step)
        checks.append(dict(label=label,**value))
    fields=("survival_probability","cells_for_half_survival_at_min","curvature_yr2")
    changes={key:checks[-1][key]/checks[0][key]-1 for key in fields}
    last=checks[-1];times=finer["t"]
    indices=np.flatnonzero((times>=last["start_yr"])&(times<=last["end_yr"]))
    total,types=score.counts(finer,p,0)
    death=np.array([score.branching.per_cell_rates(finer["y"][:,k],p,0)[2] for k in indices])
    mean_death=np.sum(np.exp(types[indices]-total[indices,None])*death,axis=1)
    shape=np.exp(last["log_min_cells"]-total[indices])
    scalar_n50=np.log(2.)*(shape[0]+np.trapezoid(mean_death*shape,times[indices]))
    shape_diagnostic=dict(inverse_population_width_yr=float(np.trapezoid(shape,times[indices])),
        local_gaussian_width_yr=last["bottleneck_width_yr"],
        scalar_hazard_cells_for_half_survival=float(scalar_n50),
        exact_multitype_cells_for_half_survival=last["cells_for_half_survival_at_min"],
        scalar_relative_difference=float(scalar_n50/last["cells_for_half_survival_at_min"]-1),
        weighted_death_range_yr=[float(min(mean_death)),float(max(mean_death))],
        scope="Scalar hazard identity on the recorded mean path is a diagnostic; agreement with the multitype result must be checked rather than assumed")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    centered=times[indices]-last["minimum_time_yr"]
    quadratic=.5*last["curvature_yr2"]*centered**2
    fig,axes=plt.subplots(1,2,figsize=(10,3.7),constrained_layout=True)
    axes[0].plot(centered,(total[indices]-last["log_min_cells"])/np.log(10.),label="Recorded population")
    axes[0].plot(centered,quadratic/np.log(10.),"--",color=".35",label="Local quadratic")
    axes[0].set_ylim(0,15);axes[0].set_ylabel("log₁₀(N / minimum N)");axes[0].legend(frameon=False)
    axes[1].plot(centered,shape,label=f"Recorded width {shape_diagnostic['inverse_population_width_yr']:.1f} yr")
    axes[1].plot(centered,np.exp(-quadratic),"--",color=".35",label=f"Gaussian width {last['bottleneck_width_yr']:.1f} yr")
    axes[1].set_ylabel("Minimum N / N");axes[1].legend(frameon=False)
    for ax in axes:ax.set_xlabel("Years from first population minimum");ax.grid(alpha=.2)
    fig.suptitle("A single minimum can have non-Gaussian tails: KT4 counterexample")
    fig.savefig(run.OUTPUT/"gaussian_counterexample.png",dpi=160);plt.close(fig)
    answer=dict(physical_control=saved,analysis_source_sha256={
        str(v.relative_to(run.e.ROOT)):sha256(v.read_bytes()).hexdigest()
        for v in (Path(__file__),Path(score.__file__))},checks=checks,
        halfyear_relative_changes=changes,
        shape_diagnostic=shape_diagnostic,
        gaussian_error_difference=checks[-1]["gaussian_relative_error"]-checks[0]["gaussian_relative_error"],
        physical_execution_environment=dict(architecture=platform.machine(),operating_system=platform.system(),python=platform.python_version()),
        scope="Same initial physical stocks, frozen equations and tolerances; independent half-year sampled physical integration through the first recovered excursion, not a Gaussian-shape assumption")
    table=run.OUTPUT/"first_survival.json"
    if table.exists():
        manifest=run.OUTPUT/"first_survival_manifest.json"
        for name,digest in json.loads(manifest.read_text())["source_sha256"].items():
            if sha256((run.e.ROOT/name).read_bytes()).hexdigest()!=digest:raise RuntimeError("Changed scoring source")
        rows=json.loads(table.read_text());removed=[r for r in rows if r["local_census_removals"]>0]
        candidates=[r for r in removed if r["rare_window"] and r["interior_minimum"]]
        closed=[r for r in candidates if not r["terminal_window"]]
        answer["full_table"]=dict(table_sha256=sha256(table.read_bytes()).hexdigest(),
            manifest_sha256=sha256(manifest.read_bytes()).hexdigest(),guild_rows=len(rows),
            guild_rows_with_local_removal=len(removed),
            first_window_classes=dict(Counter(r["classification"] for r in removed)),
            resolved_interior_rare_minima=len(closed),
            gaussian_within_ten_percent=sum(abs(r["gaussian_relative_error"])<=.1 for r in closed),
            first_windows_overlapping_other_likely_loss=sum(r["overlaps_other_guild_likely_loss_window"] for r in removed),
            scope="Guild-level conditional diagnostics linked to local removals; no local-occupancy or joint-community probability")
        fig,axes=plt.subplots(1,2,figsize=(10,3.7),constrained_layout=True)
        for guild,label,color in (("a","Acetogens","C0"),("m","Methanogens","C1")):
            group=[r for r in candidates if r["guild"]==guild]
            axes[0].scatter([r["loss_h"]*1e4 for r in group],[r["bottleneck_width_yr"] for r in group],s=22,alpha=.65,color=color,label=label)
            group=[r for r in closed if r["guild"]==guild]
            axes[1].scatter([r["loss_h"]*1e4 for r in group],[100*r["gaussian_relative_error"] for r in group],s=22,alpha=.65,color=color)
        axes[0].set_yscale("log");axes[0].set_ylabel("Local Gaussian width W (years)");axes[0].legend(frameon=False)
        axes[1].set_ylabel("Gaussian N₅₀ relative error (%)")
        for value in (-10.,10.):axes[1].axhline(value,color=".5",ls=":",lw=1)
        for ax in axes:ax.set_xlabel("Active loss L (10⁻⁴ per hour)");ax.grid(alpha=.2)
        fig.suptitle("First bottlenecks linked to census removals: widths and approximation error")
        fig.savefig(run.OUTPUT/"bottleneck_widths.png",dpi=160);plt.close(fig)
    Path(__file__).with_suffix(".json").write_text(run.e.dumps(answer)+"\n")
    print(run.e.dumps(dict(changes=changes,gaussian_relative_error=checks[-1]["gaussian_relative_error"])))
