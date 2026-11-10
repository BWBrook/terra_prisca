"""Read-only analysis of four recorded spatial-dormancy oscillation candidates.

    uv run python models/haze_world/review/dormancy_spatial_cycle_check.py

No forward integrations are run. Stationary dormant pools are eliminated
through their linear balance; the physical Jacobian is checked at four scales.
"""

from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.signal import find_peaks
from scipy.special import logsumexp

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_experiments as experiments
from terra_prisca.haze_world import dormancy_starts
from terra_prisca.haze_world import habitat_equilibria
from terra_prisca.haze_world import turnover_survival as profiles


def mixed_root(seed,p):
    reference=habitat_equilibria.refine(model.active_state(seed,p),p.base)
    if reference is None:raise ArithmeticError("Reference mixed root was not recovered")
    initial=model.reference_state(reference["y"],p)
    active=np.flatnonzero(p.weights>0);n=len(active)
    values=np.r_[initial[6*active]/100.,np.log(initial[p.biomass_indices[active]].ravel()/1e-3),
                 np.log(initial[6*active+3]/1e-3),initial[-1]/.2]
    pressure_max=p.coupled.biology.atmosphere_pa+model.core.supply_h2(p.coupled)/p.coupled.biology.exchange_mol_l_h_pa
    lower=np.r_[np.zeros(n),np.full(3*n,-100.),0.]
    upper=np.r_[np.full(n,pressure_max/100.),np.full(3*n,30.),5.]
    supply=model.core.supply_h2(p.coupled)*model.core.HOURS_PER_YEAR
    loss=p.coupled.biology.loss_h*model.core.HOURS_PER_YEAR
    def decode(z):
        y=np.zeros(p.state_size);y[6*active]=100*z[:n]
        y[p.biomass_indices[active]]=1e-3*np.exp(z[n:3*n]).reshape(n,2)
        y[6*active+3]=1e-3*np.exp(z[3*n:4*n]);y[-1]=.2*z[-1]
        return dormancy_starts.dormant_balance(y,p)
    def equations(z):
        y=decode(z);dy=model.rhs(y,p,trial_extension=True)
        return np.r_[dy[6*active]*model.core.HENRY_30C_MOL_L_PA/supply,
                     (dy[p.biomass_indices[active]]/(loss*y[p.biomass_indices[active]])).ravel(),
                     dy[6*active+3]/(supply/4),
                     dy[-1]/(model.core.inventory_to_ratio(p.coupled)*supply/4)]
    fit=least_squares(equations,values,bounds=(lower,upper),jac="3-point",x_scale="jac",
                      ftol=1e-12,xtol=1e-12,gtol=1e-12,max_nfev=1000)
    y=decode(fit.x);residual=float(max(abs(equations(fit.x))))
    if residual>1e-8 or "unsupported" in model.temperature_flags(y,p):
        raise ArithmeticError("Dormancy mixed root did not qualify")
    scales=np.r_[np.tile([100.,1e-3,1e-3,1e-3,1e-3,1e-3],p.n_patches),.2]
    spectra=[]
    for delta in (1e-5,1e-6,1e-7,1e-8):
        columns=[]
        for k in range(p.state_size):
            plus=y.copy();minus=y.copy();plus[k]+=delta*scales[k];minus[k]-=delta*scales[k]
            columns.append((model.rhs(plus,p)-model.rhs(minus,p))/(2*delta*scales))
        eig=np.linalg.eigvals(np.column_stack(columns));leading=eig[np.argsort(eig.real)[-4:]]
        spectra.append(dict(scaled_difference_step=delta,
            leading_eigenvalues_yr=[dict(real=float(v.real),imag=float(v.imag)) for v in leading],
            max_real_yr=float(max(eig.real))))
    return dict(y=y.tolist(),temperature_k=float(model.core.temperature_k(y[-1],p.coupled.climate)),
        max_scaled_residual=residual,max_absolute_dormant_balance=float(max(abs(model.rhs(y,p)[p.dormant_indices]).ravel())),
        reference_max_real_yr=reference["max_real_yr"],spectra=spectra,
        spectrum_scope="Central differences of the physical RHS in scaled stocks. Negative biomass/dormant perturbations use its linear mathematical extension; no trajectory is altered.")


def envelope(data,p,left,right):
    use=(data["t"]>=left)&(data["t"]<=right);time=data["t"][use]
    temperature=np.asarray(model.core.temperature_k(data["y"][-1,use],p.coupled.climate))
    amplitude=float(np.ptp(temperature))
    peaks,_=find_peaks(temperature,prominence=.1*amplitude)
    troughs,_=find_peaks(-temperature,prominence=.1*amplitude)
    period=float(np.polyfit(np.arange(len(peaks)),time[peaks],1)[0]) if len(peaks)>2 else None
    return dict(interval_yr=[left,right],samples=len(time),minimum_temperature_k=float(min(temperature)),
        maximum_temperature_k=float(max(temperature)),sampled_range_k=amplitude,
        mean_temperature_k=float(np.mean(temperature)),peaks=len(peaks),period_yr=period,
        positive_peak_slope_k_yr=float(np.polyfit(time[peaks],temperature[peaks],1)[0]) if len(peaks)>2 else None,
        negative_peak_slope_k_yr=float(np.polyfit(time[troughs],temperature[troughs],1)[0]) if len(troughs)>2 else None)


def main():
    records=profiles.records(experiments.RAW,"census");source=experiments.sources();rows=[];roots={}
    for key in ("dormancy_0030","dormancy_0031","dormancy_0038","dormancy_0039"):
        record=records[key];data=profiles.load(record,experiments.RAW)
        p=experiments.parameters(experiments.Case(**record["protocol"]["case"]))
        if record["protocol"]["source_sha256"]!=source:raise RuntimeError("Different physical source graph")
        late=data["t"]>=80000.;mean=np.mean(data["y"][:,late],axis=1)
        if p.epsilon not in roots:roots[p.epsilon]=mixed_root(mean,p)
        events=json.loads(str(data["extinction_events"]))
        active=p.weights>0
        logs=logsumexp(data["log_biomass"][active][:,:,late]+np.log(p.weights[active,None,None]),axis=0)
        conversion=data["metadata"]["global_log_cell_conversion"]
        metadata=data["metadata"]
        windows=[envelope(data,p,a,b) for a,b in ((40000.,60000.),(60000.,80000.),(80000.,100000.))]
        rows.append(dict(case_id=key,case=record["protocol"]["case"],fingerprint=record["fingerprint"],
            raw_file=record["raw_file"],raw_sha256=record["raw_sha256"],
            recorded_settling_status=record["summary"]["settling_status"],
            interpretation="Persistent sampled oscillation candidate; no stationary endpoint or global attractor proof claimed",
            windows=windows,late_minimum_global_log10_cells=((np.min(logs,axis=1)+conversion)/np.log(10)).tolist(),
            late_census_removals=sum(e["time_yr"]>=40000. for e in events),
            late_stage_chart_promotions=sum(e["time_yr"]>=40000. for e in metadata["stage_coordinate_switches"]),
            late_stage_source_restarts=sum(e["time_yr"]>=40000. for e in metadata["stage_source_restarts"]),
            late_max_redox_residual=float(max(abs(model.redox_residual(y,p)) for y in data["y"][:,np.flatnonzero(late)[::20]].T)),
            mixed_equilibrium=roots[p.epsilon]))
    if experiments.sources()!=source:raise RuntimeError("Physical sources changed during review")
    result=dict(source_sha256=source,checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows,
        scope="Four frozen100k census paths, sampled every10years; envelope extrema are sampled lower bounds. No new forward runs, no reclassification as settled, no proof of a periodic orbit.")
    target=Path(__file__).with_suffix(".json");target.write_text(json.dumps(result,indent=2)+"\n")
    for row in rows:
        last=row["windows"][-1]
        print(row["case_id"],last["minimum_temperature_k"],last["maximum_temperature_k"],last["period_yr"],
              [s["max_real_yr"] for s in row["mixed_equilibrium"]["spectra"]],flush=True)


if __name__=="__main__":main()
