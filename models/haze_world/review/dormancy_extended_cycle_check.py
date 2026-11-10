"""Read-only analysis of the 0068/0069 invasion-history endpoints.

    uv run python models/haze_world/review/dormancy_extended_cycle_check.py

No forward integrations or changes to the native settling classifications.
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
from terra_prisca.haze_world import turnover_survival as profiles
from dormancy_spatial_cycle_check import envelope


def direct_root(seed, p):
    active = np.flatnonzero(p.weights > 0)
    n = len(active)
    values = np.r_[seed[6*active]/100., np.log(seed[p.biomass_indices[active]].ravel()/1e-3),
                   np.log(seed[6*active+3]/1e-3), seed[-1]/.2]
    supply = model.core.supply_h2(p.coupled)*model.core.HOURS_PER_YEAR
    loss = p.coupled.biology.loss_h*model.core.HOURS_PER_YEAR
    pressure_max = p.coupled.biology.atmosphere_pa+model.core.supply_h2(p.coupled)/p.coupled.biology.exchange_mol_l_h_pa

    def decode(z):
        y = np.zeros(p.state_size)
        y[6*active] = 100*z[:n]
        y[p.biomass_indices[active]] = 1e-3*np.exp(z[n:3*n]).reshape(n, 2)
        y[6*active+3] = 1e-3*np.exp(z[3*n:4*n])
        y[-1] = .2*z[-1]
        return dormancy_starts.dormant_balance(y, p)

    def equations(z):
        y = decode(z)
        dy = model.rhs(y, p, trial_extension=True)
        return np.r_[dy[6*active]*model.core.HENRY_30C_MOL_L_PA/supply,
            (dy[p.biomass_indices[active]]/(loss*y[p.biomass_indices[active]])).ravel(),
            dy[6*active+3]/(supply/4), dy[-1]/(model.core.inventory_to_ratio(p.coupled)*supply/4)]

    fit = least_squares(equations, values,
        bounds=(np.r_[np.zeros(n), np.full(3*n, -100.), 0.],
                np.r_[np.full(n, pressure_max/100.), np.full(3*n, 30.), 5.]),
        jac="3-point", x_scale="jac", ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=1000)
    y = decode(fit.x)
    residual = float(max(abs(equations(fit.x))))
    if residual > 1e-8 or "unsupported" in model.temperature_flags(y, p):
        raise ArithmeticError("The seeded mixed root did not qualify")
    indices = np.r_[np.concatenate([np.arange(6*j, 6*j+6) for j in active]), p.state_size-1]
    scales = np.r_[np.tile([100., 1e-3, 1e-3, 1e-3, 1e-3, 1e-3], p.n_patches), .2]
    spectra = []
    for delta in (1e-5, 1e-6, 1e-7, 1e-8):
        columns = []
        for k in indices:
            plus, minus = y.copy(), y.copy()
            plus[k] += delta*scales[k]
            minus[k] -= delta*scales[k]
            columns.append((model.rhs(plus, p)-model.rhs(minus, p))[indices]/(2*delta*scales[indices]))
        eig = np.linalg.eigvals(np.column_stack(columns))
        leading = eig[np.argsort(eig.real)[-4:]]
        spectra.append(dict(scaled_difference_step=delta, max_real_yr=float(max(eig.real)),
            leading_eigenvalues_yr=[dict(real=float(v.real), imag=float(v.imag)) for v in leading]))
    return dict(y=y.tolist(), temperature_k=float(model.core.temperature_k(y[-1], p.coupled.climate)),
        max_scaled_residual=residual, least_squares_evaluations=fit.nfev, spectra=spectra,
        active_state_indices=indices.tolist(),
        method="One direct positive mixed-root solve seeded by the recorded late mean; dormant pools eliminated by their linear balance. Inactive forced-zero habitat coordinates excluded from the physical Jacobian. Central differences use the mathematical RHS extension for negative perturbations; no trajectory is altered.",
        scope="Local stability of one recovered root; no basin enumeration or Hopf claim.")


def complete_cycle_mean(data, p, left=80000., right=100000.):
    use = (data["t"] >= left) & (data["t"] <= right)
    time = data["t"][use]
    temperature = np.asarray(model.core.temperature_k(data["y"][-1, use], p.coupled.climate))
    peaks, _ = find_peaks(temperature, prominence=.1*np.ptp(temperature))
    if len(peaks) < 3:
        return None
    a, b = peaks[0], peaks[-1]
    return dict(first_peak_time_yr=float(time[a]), last_peak_time_yr=float(time[b]),
        complete_sampled_peak_intervals=len(peaks)-1,
        temperature_k=float(np.trapezoid(temperature[a:b+1], time[a:b+1])/(time[b]-time[a])))


def main():
    records = profiles.records(experiments.RAW, "census")
    rows = []
    for case_id in ("dormancy_0068", "dormancy_0069"):
        record = records[case_id]
        data = profiles.load(record, experiments.RAW)
        for path, expected in record["protocol"]["source_sha256"].items():
            if sha256((experiments.e.ROOT/path).read_bytes()).hexdigest() != expected:
                raise RuntimeError("A recorded source dependency changed")
        p = experiments.parameters(experiments.Case(**record["protocol"]["case"]))
        late = data["t"] >= 80000.
        active = p.weights > 0
        conversion = data["metadata"]["global_log_cell_conversion"]
        global_logs = logsumexp(data["log_biomass"][active][:, :, late]+np.log(p.weights[active, None, None]), axis=0)
        volumes = p.coupled.habitat_l_cm2*record["protocol"]["census"]["surface_cm2"]*p.weights
        cell_mass = record["protocol"]["census"]["cell_mass_gdw"]
        floors = np.divide(cell_mass, volumes, out=np.zeros(p.n_patches), where=volumes > 0.)
        minimum = np.r_[np.array([[1., v, v, 1e-9, v, v] for v in floors]).ravel(), .001]
        sample = data["y"][:, late]
        scale = np.maximum(np.mean(abs(sample), axis=1), minimum)
        span = np.divide(np.ptp(sample, axis=1), scale, out=np.zeros(p.state_size), where=scale > 0.)
        labels = [f"{name}:{field}" for name in p.patch_names for field in ("hydrogen_pa", "active_a", "active_m", "acetate_mol_l", "dormant_a", "dormant_m")]+["methane_ratio"]
        span_rows = []
        for k in np.argsort(span)[::-1][:4]:
            item = dict(stock=labels[k], state_index=int(k), original_relative_span=float(span[k]),
                minimum=float(min(sample[k])), maximum=float(max(sample[k])))
            if k < p.state_size-1 and k % 6 in (1, 2, 4, 5):
                j = k//6
                at = int(np.argmax(sample[k]))
                total = float(np.sum(p.weights[:, None]*(sample[p.biomass_indices, at]+sample[p.dormant_indices, at])))
                item.update(maximum_cells=float(max(sample[k])*volumes[j]/cell_mass),
                    fraction_of_global_biomass_at_maximum=float(p.weights[j]*sample[k, at]/total))
            span_rows.append(item)
        switches = model.core.switch_temperatures(p.coupled.biology)
        windows = [envelope(data, p, a, b) for a, b in ((20000., 40000.), (40000., 60000.), (60000., 80000.), (80000., 100000.))]
        mean = complete_cycle_mean(data, p)
        event_keys = ("stage_coordinate_switches", "stage_source_restarts", "chemical_conditioning_events")
        events = json.loads(str(data["extinction_events"]))
        row = dict(case_id=case_id, fingerprint=record["fingerprint"], case=record["protocol"]["case"],
            raw_file=record["raw_file"], raw_sha256=record["raw_sha256"], source_sha256=record["protocol"]["source_sha256"],
            original_settling_status=record["summary"]["settling_status"], original_summary=record["summary"],
            largest_late_stock_spans=span_rows,
            windows=windows, complete_cycle_mean=mean, switch_temperatures_k=list(switches),
            late_sampled_minimum_global_log10_cells=((global_logs.min(axis=1)+conversion)/np.log(10)).tolist(),
            whole_trajectory_dense_minimum_global_log10_cells=((data["min_log_biomass"]+conversion)/np.log(10)).tolist(),
            late_patch_minimum_log10_cells=[dict(patch=p.patch_names[j], log10_cells=((data["log_biomass"][j, :, late].min(axis=0)+conversion+np.log(p.weights[j]))/np.log(10)).tolist()) for j in np.flatnonzero(active)],
            late_census_removals=[ev for ev in events if ev["time_yr"] >= 40000.],
            late_chart_events={name: [ev for ev in data["metadata"].get(name, []) if ev.get("time_yr", ev.get("accepted_time_yr", 0.)) >= 40000.] for name in event_keys},
            late_climate_domains=sorted(set(str(model.core.domain(r, p.coupled.climate)) for r in data["y"][-1, late])),
            late_physiology_domains=sorted(set(flag for y in data["y"][:, late].T[::20] for flag in model.temperature_flags(y, p))))
        if mean is not None and len(switches) == 1:
            row["complete_cycle_mean_minus_switch_k"] = mean["temperature_k"]-switches[0]
        if case_id == "dormancy_0068":
            ranges = [item["sampled_range_k"] for item in windows]
            row.update(interpretation="Persistent material-cycle candidate; unchanged unsettled status, no periodic-orbit proof",
                range_max_to_min_ratio=max(ranges)/min(ranges), period_max_to_min_ratio=max(item["period_yr"] for item in windows)/min(item["period_yr"] for item in windows))
            try:
                row["mixed_equilibrium"] = direct_root(np.mean(data["y"][:, late], axis=1), p)
            except Exception as error:
                row["mixed_equilibrium"] = dict(status="unresolved", error=repr(error))
        else:
            target = np.asarray(records["dormancy_0068"]["start"]["selected"]["y"])
            target_flux = model.fluxes(target, p)
            row["comparison_to_recorded_methanogen_resident_root"] = dict(
                target_temperature_k=float(model.core.temperature_k(target[-1], p.coupled.climate)),
                final_temperature_excess_k=float(model.core.temperature_k(data["y"][-1, -1], p.coupled.climate)-model.core.temperature_k(target[-1], p.coupled.climate)),
                target_dormant_m_gdw_l=target[p.dormant_indices[:, 1]].tolist(),
                final_dormant_m_gdw_l=data["y"][p.dormant_indices[:, 1], -1].tolist(),
                target_rare_active_acetogen_net_growth_yr=target_flux["net_growth_yr"][:, 0].tolist(),
                scope="Reuses the original0068 conditional resident root at the same parameters. The missing acetogen can grow in bulk if reintroduced; the finite censused guild-loss face is absorbing without immigration.")
            row["interpretation"] = "Reverse-invasion M-only censused outcome, with a monotone climate tail and changing microscopic dormant banks approaching the recorded resident root. No demonstration that this bank drift is numerical noise, or that the M-only state is stable to reintroduction. Its original unsettled status is retained."
        rows.append(row)
    proposal = [
        "Preserve every native settling status and record the exact failed criteria; diagnostics do not override acceptance.",
        "For material thermal nonstationarity (the existing0.01K threshold), compare successive equal windows: report peaks, periods, amplitude ratios, extrema trends and whole-guild minima. Repeated stable envelopes support a persistent-cycle candidate; contraction supports a damped-tail candidate; monotone drift supports a relaxation tail.",
        "When only stage-bank spans fail, report cell counts, global and guild biomass fractions, total-guild spans, occupancy and chart events. Compare normalized root-allocation scales to the recorded tolerance as context, never as a certified bound.",
        "Use precision-sensitive bank candidate only when an independent platform/resolution comparison supports that reading. Otherwise retain stage-bank nonstationarity unresolved. A tiny stage fraction alone cannot establish harmlessness when it is the last refuge of a nearly extinct guild.",
        "Use one bounded finer-resolution continuation for a new material cycle, then retain same-solver and finite-observation qualifications. Test basins or periodic-orbit stability separately when they matter scientifically.",
    ]
    result = dict(checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        envelope_checker_sha256=sha256(Path(__file__).with_name("dormancy_spatial_cycle_check.py").read_bytes()).hexdigest(), rows=rows,
        generic_nonstationarity_diagnostic_proposal=proposal,
        scope="Two current selected100k census records; numerical sampled extrema are not interval certified. No forward runs or alterations of prior cycle artifacts or native statuses.")
    output = Path(__file__).with_suffix(".json")
    output.write_text(experiments.e.dumps(result)+"\n")
    print(json.dumps([dict(case_id=row["case_id"], original_status=row["original_settling_status"], late=row["windows"][-1],
        complete_cycle_mean=row["complete_cycle_mean"], minimum_log10_cells=row["late_sampled_minimum_global_log10_cells"]) for row in rows], indent=2))


if __name__ == "__main__":
    main()
