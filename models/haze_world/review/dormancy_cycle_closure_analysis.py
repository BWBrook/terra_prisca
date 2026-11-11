"""Summarise the bounded dormancy cycle controls and their source identities."""

from dataclasses import replace
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks

from terra_prisca.haze_world import dormancy_cycle_closure as closure


OUT = closure.REVIEW/"cycle-closure-results-2026-11-11.json"
FIG = closure.REVIEW/"cycle-closure-2026-11-11.png"


def peak_mode(time, temperature, root_temperature, left=5000., right=25000.):
    time, values = np.asarray(time), np.asarray(temperature)-root_temperature
    peaks = find_peaks(values)[0]
    peaks = peaks[(peaks>0)&(peaks<len(time)-1)]
    t, amplitude = [], []
    for i in peaks:
        x = time[i-1:i+2]-time[i]
        a, b, c = np.polyfit(x, values[i-1:i+2], 2)
        offset = -b/(2*a)
        if a >= 0 or not x[0] <= offset <= x[-1]:
            continue
        height = c+b*offset+a*offset**2
        peak_time = time[i]+offset
        if height > 1e-11 and left <= peak_time <= right:
            t.append(float(peak_time)); amplitude.append(float(height))
    if len(t) < 4:
        return dict(status="insufficient_resolved_peaks", peaks=len(t))
    t, amplitude = np.asarray(t), np.asarray(amplitude)
    period = np.polyfit(np.arange(len(t)), t, 1)[0]
    slope, intercept = np.polyfit(t, np.log(amplitude), 1)
    error = np.log(amplitude)-(slope*t+intercept)
    variance = np.sum((np.log(amplitude)-np.mean(np.log(amplitude)))**2)
    return dict(status="resolved", peaks=len(t), fit_interval_yr=[left, right],
        period_yr=float(period), log_amplitude_slope_yr=float(slope),
        damping_time_yr=float(-1/slope) if slope<0 else None,
        log_amplitude_fit_r_squared=float(1-np.sum(error**2)/variance) if variance else None,
        first_peak_amplitude_k=float(amplitude[0]), last_peak_amplitude_k=float(amplitude[-1]))


def receipt_record(path, p, root_temperature=None):
    receipt = json.loads(path.read_text())
    row = dict(receipt=str(path.relative_to(closure.ROOT)), receipt_sha256=closure.digest(path),
        fingerprint=receipt["fingerprint"], status=receipt["status"],
        protocol=receipt["protocol"], sources_unchanged=receipt["sources_unchanged"])
    if receipt["status"] != "completed":
        start=receipt["protocol"].get("absolute_start_yr",0.)
        return row | dict(error=receipt.get("error"), actual_start_yr=start,
            actual_horizon_yr=receipt.get("actual_horizon_yr",start),completed_duration_yr=0.,
            scope="No returned continuation flow; absolute input time is not completed linear-law integration")
    raw = closure.ROOT/receipt["raw_file"]
    if closure.digest(raw) != receipt["raw_sha256"]:
        raise ArithmeticError("Raw identity mismatch")
    with np.load(raw) as data:
        time, stocks = data["t"], data["y"]
    temperature = np.asarray(closure.model.core.temperature_k(stocks[-1], p.coupled.climate))
    domain = sorted({flag for y in stocks.T for flag in closure.model.temperature_flags(y, p)})
    if np.any(~np.isfinite(stocks)) or np.min(stocks)<0 or "unsupported" in domain:
        raise ArithmeticError("Recorded stocks fail positivity/domain check")
    width = min(5000.,(time[-1]-time[0])/4)
    conversion=p.coupled.habitat_l_cm2*closure.face.Census().surface_cm2/closure.face.Census().cell_mass_gdw
    counts=np.einsum("p,pgs->gs",p.weights,stocks[p.biomass_indices]+stocks[p.dormant_indices])*conversion
    windows = []
    for right in np.arange(time[0]+width, time[-1]+width/10, width):
        use = (time>=right-width)&(time<=right)
        if np.count_nonzero(use)<2:
            continue
        peaks=find_peaks(temperature[use])[0]
        peak_times=time[use][peaks]
        windows.append(dict(left_yr=float(right-width), right_yr=float(right),
            temperature_span_k=float(np.ptp(temperature[use])), mean_temperature_k=float(np.mean(temperature[use])),
            sampled_period_yr=float(np.polyfit(np.arange(len(peaks)),peak_times,1)[0]) if len(peaks)>2 else None))
    row.update(raw_file=receipt["raw_file"], raw_sha256=receipt["raw_sha256"],
        actual_start_yr=float(time[0]),actual_horizon_yr=float(time[-1]),completed_duration_yr=float(time[-1]-time[0]), samples=len(time), all_observed_stocks_finite_nonnegative=True,
        all_observed_climates_supported=True, physiology_domains=domain,
        minimum_observed_global_cells=counts.min(axis=1).tolist(),
        windows=windows, late_to_previous_span_ratio=(windows[-1]["temperature_span_k"]/windows[-2]["temperature_span_k"] if len(windows)>1 else None),
        final_temperature_k=float(temperature[-1]),
        census_events=receipt.get("extinction_events",receipt.get("startup_extinction_events",[])))
    if root_temperature is not None:
        row["mode"] = peak_mode(time,temperature,root_temperature,right=min(25000.,time[-1]))
    return row


def linear_selection(key):
    paths = []
    for prefix in (f"linear_segments_{key}_*.json",f"linear_positive_{key}_*.json",f"linear_{key}_*.json"):
        paths.extend(closure.RAW.glob(prefix))
    paths=[path for path in paths if "fingerprint" in json.loads(path.read_text()) and "cubic80k" not in json.loads(path.read_text())["protocol"].get("input_file","")]
    if not paths:
        raise ArithmeticError(f"No retained linear attempt for {key}")
    def rank(path):
        row=json.loads(path.read_text())
        horizon=row.get("actual_horizon_yr",row["protocol"].get("case",{}).get("years",0.))
        return (row["status"]=="completed",horizon)
    return max(paths,key=rank)


def main():
    root, p, proof = closure.mixed_root()
    root_t = float(closure.model.core.temperature_k(root[-1],p.coupled.climate))
    rows = []
    for guild in (0,1):
        for fraction in (-.1,-.001,.001,.1):
            matches = []
            for path in closure.RAW.glob("amplitude_*.json"):
                r = json.loads(path.read_text()); protocol=r["protocol"]
                if protocol["years"]==30000 and protocol["guild"]==guild and protocol["fraction"]==fraction and r["status"]=="completed":
                    matches.append(path)
            if len(matches)!=1:
                raise ArithmeticError("Expected exactly one completed amplitude per fixed start")
            rows.append(receipt_record(matches[0],p,root_t))
    linear = []
    for key in ("0024","0032","0126","0012","0068"):
        case=replace(closure.cycle_case(key),ramp="linear")
        lp=closure.experiments.parameters(case)
        record=receipt_record(linear_selection(key),lp)
        record["nonsmooth_stability_status"]="unqualified; original-start trajectory evidence only"
        linear.append(record)
    directions=[]
    for path in sorted(closure.RAW.glob("linear_root_*.json")):
        r=json.loads(path.read_text())
        if r["status"]=="completed":
            directions.append(receipt_record(path,replace(p,ramp="linear"),root_t))
    switches=[]
    for path in sorted(closure.RAW.glob("linear_positive_*.json")):
        r=json.loads(path.read_text());protocol=r["protocol"]
        if "cubic80k" not in protocol["input_file"]:
            continue
        case=replace(closure.cycle_case(protocol["case"]["case_id"].split("_")[-1]),ramp="linear")
        lp=closure.experiments.parameters(case)
        row=receipt_record(path,lp)
        row["comparison_scope"]="Switch-only response from a recorded cubic80k-cycle state; no original-start basin-equivalence claim"
        row["initial_provenance_file"]=str((closure.ROOT/protocol["input_file"]).with_suffix(".json").relative_to(closure.ROOT))
        row["initial_provenance_sha256"]=closure.digest(closure.ROOT/row["initial_provenance_file"])
        switches.append(row)
    failures=[]
    for path in closure.RAW.glob("*.json"):
        r=json.loads(path.read_text())
        if r.get("status", "completed") not in ("completed",):
            failures.append(dict(receipt=str(path.relative_to(closure.ROOT)),receipt_sha256=closure.digest(path),
                status=r["status"],error=r.get("error"),protocol=r.get("protocol"),
                actual_start_yr=r.get("protocol",{}).get("absolute_start_yr",0.),
                actual_horizon_yr=r.get("actual_horizon_yr",r.get("protocol",{}).get("absolute_start_yr",0.)),
                completed_duration_yr=0.))
    smoke=[]
    for backend in ("macro","radau"):
        found=[]
        for path in closure.RAW.glob("amplitude_*.json"):
            r=json.loads(path.read_text());q=r["protocol"]
            if r["status"]=="completed" and q["years"]==1000. and q["guild"]==0 and q["fraction"]==.001 and q["backend"]==backend and q["source_sha256"]==closure.sources():
                found.append(path)
        if len(found)!=1:
            raise ArithmeticError("Ambiguous current-source smoke comparison")
        smoke.append(receipt_record(found[0],p,root_t))
    a,b=[np.load(closure.ROOT/r["raw_file"]) for r in smoke]
    if not np.array_equal(a["t"],b["t"]):
        raise ArithmeticError("Smoke sample times differ")
    delta=abs(a["y"]-b["y"])
    smoke_comparison=dict(records=smoke,common_samples=len(a["t"]),
        maximum_absolute_methane_ratio_difference=float(delta[-1].max()),
        maximum_absolute_hydrogen_pressure_difference_pa=float(delta[0].max()),
        maximum_absolute_temperature_difference_k=float(max(abs(closure.model.core.temperature_k(a["y"][-1],p.coupled.climate)-closure.model.core.temperature_k(b["y"][-1],p.coupled.climate)))))
    a.close();b.close()
    data=dict(design="models/haze_world/review/cycle-closure-design-2026-11-11.md",
        design_sha256=closure.digest(closure.REVIEW/"cycle-closure-design-2026-11-11.md"),
        analysis_sha256=closure.digest(__file__),mixed_root=proof,
        reference_period_yr=2*np.pi/.05254893926050499,reference_damping_time_yr=1/.00020601947125469504,
        amplitude=rows,linear=linear,linear_cycle_switch=switches,linear_directional=directions,failed_trials=failures,
        cross_solver_smoke=smoke_comparison,
        scope="Bounded trajectory and local-mode evidence. No Floquet, basin, global uniqueness or nonsmooth stability certificate. Earlier native outputs and labels remain frozen.")
    OUT.write_text(closure.experiments.e.dumps(data)+"\n")
    figure,axes=plt.subplots(2,1,figsize=(8,7),constrained_layout=True)
    for row in rows:
        with np.load(closure.ROOT/row["raw_file"]) as flow:
            time=flow["t"];temp=np.asarray(closure.model.core.temperature_k(flow["y"][-1],p.coupled.climate))
        centres=[];spans=[]
        for left in np.arange(0.,30000.,500.):
            use=(time>=left)&(time<left+500.)
            centres.append(left+250.);spans.append(np.ptp(temp[use]))
        protocol=row["protocol"]
        axes[0].semilogy(centres,spans,label=f"{'A' if protocol['guild']==0 else 'M'}{protocol['fraction']:+.1%}",alpha=.85)
    axes[0].set(ylabel="500 yr temperature span (K)",xlabel="Years after root perturbation",title="Every fixed cubic perturbation decays")
    axes[0].legend(ncol=4,fontsize=8)
    for row in linear:
        if row["status"]!="completed" or not row["windows"]:
            continue
        centres=[(w["left_yr"]+w["right_yr"])/2 for w in row["windows"]]
        spans=[w["temperature_span_k"] for w in row["windows"]]
        axes[1].semilogy(centres,spans,"o-",label=row["protocol"]["case"]["case_id"].split("_")[-1]+f" ({row['actual_horizon_yr']/1000:g} kyr)")
    axes[1].set(ylabel="Window temperature span (K)",xlabel="Years after original linear-ramp invasion",title="Linear controls: 5 kyr windows (0.5 kyr for 2 kyr startup)")
    axes[1].legend(ncol=5,fontsize=8)
    figure.savefig(FIG,dpi=160)
    plt.close(figure)
    print(json.dumps(dict(output=str(OUT),figure=str(FIG),amplitudes=len(rows),linear=len(linear),directional=len(directions))),flush=True)


if __name__=="__main__":
    main()
