"""Read-only late-flow diagnostics for a pinned completed census snapshot.

No trajectories or probabilities are calculated. Native stationarity labels
are preserved. Reproduce the same selected receipts with --snapshot pointing
to the emitted JSON; omit it to inspect a new current snapshot deliberately.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks
from scipy.special import logsumexp

from terra_prisca.haze_world import buffered_experiments as e
from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_experiments as runner
from terra_prisca.haze_world import turnover_survival as survival


ROOT = e.ROOT
REVIEW = Path(__file__).parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def finite(value):
    return float(value) if np.isfinite(value) else None


def snapshot_records(raw, snapshot):
    planned = {c.case_id: c for c in runner.design()}
    if snapshot is None:
        chosen = survival.records(raw, "census")
        entries = []
        for case_id, record in sorted(chosen.items()):
            if case_id not in planned or record["protocol"]["case"]["years"] < planned[case_id].years:
                continue
            receipt = (raw/record["raw_file"]).with_suffix(".receipt.json")
            entries.append(dict(case_id=case_id, receipt_file=receipt.name, receipt_sha256=digest(receipt),
                **{k: record[k] for k in ("fingerprint", "raw_file", "raw_sha256")}))
        plan = raw/"receipt_selection.json"
        identity = dict(captured_utc=datetime.now(timezone.utc).isoformat(),
                        receipt_selection_sha256=digest(plan) if plan.exists() else None)
    else:
        prior = json.loads(snapshot.read_text())
        entries = prior["selected_receipts"]
        identity = dict(captured_utc=prior["captured_utc"], receipt_selection_sha256=prior.get("receipt_selection_sha256"),
                        snapshot_input_sha256=digest(snapshot))
    records = []
    physical = runner.sources()
    for entry in entries:
        receipt = raw/entry["receipt_file"]
        if digest(receipt) != entry["receipt_sha256"]:
            raise RuntimeError("Changed selected receipt: "+receipt.name)
        record = json.loads(receipt.read_text())
        protocol = record["protocol"]
        if (record["execution_status"] != "complete" or protocol["mode"] != "census"
                or record["fingerprint"] != entry["fingerprint"]
                or sha256(e.dumps(protocol).encode()).hexdigest() != record["fingerprint"]
                or any(record[k] != entry[k] for k in ("raw_file", "raw_sha256"))):
            raise RuntimeError("Invalid selected receipt: "+receipt.name)
        if any(protocol["source_sha256"].get(k) != v for k, v in physical.items()):
            raise RuntimeError("Physical analysis source differs from the selected epoch")
        records.append(record)
    return identity, entries, records


def reviewed_paths():
    paths = {}
    evidence = {}
    for name in ("dormancy_spatial_cycle_check.json", "dormancy_extended_cycle_check.json"):
        path = REVIEW/name
        data = json.loads(path.read_text())
        evidence[str(path.relative_to(ROOT))] = digest(path)
        for row in data["rows"]:
            if "Persistent" in row.get("interpretation", ""):
                paths[row["fingerprint"]] = dict(path=str(path.relative_to(ROOT)),
                    raw_sha256=row["raw_sha256"], kind="unculled_cycle_candidate", interpretation=row["interpretation"])
    path = REVIEW/"dormancy0012_cycle_compare.json"
    data = json.loads(path.read_text())
    paths[data["original_fingerprint"]] = dict(path=str(path.relative_to(ROOT)),
        raw_sha256=data["original_raw_sha256"], kind="finite_census_hybrid_cycle_candidate",
        interpretation=data["interpretation"])
    evidence[str(path.relative_to(ROOT))] = digest(path)
    for name in ("dormancy126_cycle_0024.json", "dormancy126_cycle_0126.json"):
        path = REVIEW/name
        data = json.loads(path.read_text())
        if data["status"] != "completed" or data["control_culls"]:
            raise RuntimeError("Unqualified nonspatial continuation")
        protocol = data["protocol"]
        paths[protocol["native_fingerprint"]] = dict(path=str(path.relative_to(ROOT)),
            raw_sha256=protocol["native_raw_sha256"], kind="unculled_cycle_candidate",
            interpretation="Persistent nonspatial recurrence reproduced by an independent maintained Radau continuation; no periodic-orbit or global-basin proof.")
        evidence[str(path.relative_to(ROOT))] = digest(path)
    return paths, evidence


def envelope(t, temperature, global_logs, events, left, right):
    use = (t >= left) & (t <= right)
    times, values = t[use], temperature[use]
    amplitude = float(np.ptp(values))
    peaks = find_peaks(values, prominence=max(1e-8, amplitude*.01))[0]
    fitted = float(np.polyfit(np.arange(len(peaks)), times[peaks], 1)[0]) if len(peaks) > 2 else None
    interpolated = []
    for k in peaks:
        if not 0 < k < len(times)-1:
            continue
        coefficients = np.polyfit(times[k-1:k+2]-times[k], values[k-1:k+2], 2)
        if coefficients[0] < 0:
            shift = -coefficients[1]/(2*coefficients[0])
            if times[k-1]-times[k] <= shift <= times[k+1]-times[k]:
                interpolated.append(times[k]+shift)
    variation = float(sum(abs(np.diff(values))))
    return dict(interval_yr=[float(times[0]), float(times[-1])], sampled_range_k=amplitude,
        minimum_temperature_k=float(min(values)), maximum_temperature_k=float(max(values)),
        mean_temperature_k=float(np.mean(values)), peaks=len(peaks), sampled_peak_fit_period_yr=fitted,
        interpolated_peak_fit_period_yr=float(np.polyfit(np.arange(len(interpolated)), interpolated, 1)[0]) if len(interpolated)>2 else None,
        net_change_fraction_of_total_variation=abs(float(values[-1]-values[0]))/variation if variation else 0.,
        global_log10_cells_ranges=[[finite(min(v[use])/np.log(10.)), finite(max(v[use])/np.log(10.))] for v in global_logs],
        census_removals=sum(left <= item["time_yr"] <= right for item in events))


def stock_evidence(k, y, data, p, late, span, cached_flux):
    patch, component = divmod(int(k), 6)
    names = ("H2_pa", "active_a_gdw_l", "active_m_gdw_l", "acetate_mol_l", "dormant_a_gdw_l", "dormant_m_gdw_l")
    row = dict(stock="methane_ratio" if k == p.state_size-1 else p.patch_names[patch]+":"+names[component],
               relative_span=float(span[k]), final_value=float(y[k,-1]),
               late_min=float(min(y[k,late])), late_max=float(max(y[k,late])))
    if k == p.state_size-1 or component not in (1,2,4,5):
        return row
    guild = component-1 if component < 3 else component-4
    logs = data["log_active" if component<3 else "log_dormant"][patch,guild]
    log_weight = np.log(p.weights[patch])
    conversion = data["metadata"]["global_log_cell_conversion"]
    global_total = logsumexp(data["log_biomass"][p.weights>0,guild]+np.log(p.weights[p.weights>0,None]),axis=0)
    use = late & np.isfinite(logs) & np.isfinite(global_total)
    fractions = logs[use]+log_weight-global_total[use]
    row.update(decoded_final_world_cells=float(y[k,-1]*np.exp(conversion)*p.weights[patch]),
        decoded_final_world_gdw=float(y[k,-1]*p.weights[patch]*p.coupled.habitat_l_cm2*runner.Census().surface_cm2),
        retained_final_log10_world_cells=finite((logs[-1]+log_weight+conversion)/np.log(10.)),
        retained_late_log10_world_cells_range=[finite(min(logs[late]+log_weight+conversion)/np.log(10.)),finite(max(logs[late]+log_weight+conversion)/np.log(10.))],
        max_late_fraction_of_global_guild=float(np.exp(max(fractions))) if len(fractions) else 0.)
    if np.all(np.isfinite(logs[late])):
        values = logs[late]
        variation = float(sum(abs(np.diff(values))))
        row["retained_late_log_net_change"] = float(values[-1]-values[0])
        row["retained_late_log_net_fraction_of_variation"] = abs(float(values[-1]-values[0]))/variation if variation else 0.
    if component < 4:
        return row
    indices = sorted(cached_flux)
    sources, losses, target_logs, entry_rates = [], [], [], []
    for index in indices:
        flux = cached_flux[index]
        terms = []
        sigma = flux["sigma_yr"][patch,guild]
        entry_rates.append(float(sigma))
        if sigma > 0:
            terms.append(np.log(sigma)+data["log_active"][patch,guild,index])
        for other, weight in enumerate(p.weights):
            if other != patch and weight and p.dispersal_yr > 0:
                terms.append(np.log(p.dispersal_yr*weight)+data["log_dormant"][other,guild,index])
        sources.append(float(logsumexp(terms)) if terms else -np.inf)
        losses.append(float(flux["rho_yr"][patch,guild]+flux["dormant_loss_yr"]+p.dispersal_yr*(1-p.weights[patch])))
        target_logs.append(float(data["log_dormant"][patch,guild,index]))
    final_flux = cached_flux[indices[-1]]
    final_ratio = np.exp(sources[-1]-target_logs[-1]) if np.isfinite(target_logs[-1]) else np.nan
    row["reevaluated_source_balance"] = dict(
        sampled_entry_sigma_yr_range=[min(entry_rates),max(entry_rates)],
        final_retained_incoming_per_stored_dormant_yr=finite(final_ratio),
        final_recomputed_log_rate_yr=finite(final_ratio-losses[-1]),
        sampled_retained_incoming_log_range=[finite(min(sources)), finite(max(sources))],
        sampled_no_retained_incoming_source=bool(all(np.isneginf(v) for v in sources)),
        final_sigma_yr=float(final_flux["sigma_yr"][patch,guild]),
        final_rho_yr=float(final_flux["rho_yr"][patch,guild]),
        dormant_death_yr=float(final_flux["dormant_loss_yr"]),
        final_total_loss_yr=losses[-1],
        final_entry_gdw_l_yr=float(final_flux["sigma_yr"][patch,guild]*y[p.biomass_indices[patch,guild],-1]),
        final_migration_gdw_l_yr=float(final_flux["dormant_exchange_gdw_l_yr"][patch,guild]),
        scope="Static current-platform reevaluation at 21 saved late states. Retained log sources are checked before any claim of sampled source absence; not a between-sample or cross-platform proof.")
    if all(np.isneginf(v) for v in sources) and all(np.isfinite(target_logs)):
        times = data["t"][indices]
        predicted = target_logs[0]-np.r_[0.,np.cumsum(np.diff(times)*(np.asarray(losses[:-1])+losses[1:])/2)]
        row["reevaluated_source_balance"]["source_free_prediction_max_log_error"] = float(max(abs(np.asarray(target_logs)-predicted)))
        row["reevaluated_source_balance"]["observed_late_log_change"] = float(target_logs[-1]-target_logs[0])
        row["reevaluated_source_balance"]["source_free_predicted_log_change"] = float(predicted[-1]-predicted[0])
    return row


def diagnose(record, data, known):
    case = runner.Case(**record["protocol"]["case"])
    p = runner.parameters(case)
    t, y, T = data["t"], data["y"], data["temperatures_k"][0]
    if float(t[-1]) != case.years:
        raise RuntimeError("Declared and actual horizons differ")
    late = t >= case.years-20000.
    conversion = data["metadata"]["global_log_cell_conversion"]
    floors = np.divide(np.exp(-conversion),p.weights,out=np.zeros(p.n_patches),where=p.weights>0)
    floor = np.r_[np.array([[1.,v,v,1e-9,v,v] for v in floors]).ravel(),.001]
    sample = y[:,late]
    denominator = np.maximum(np.mean(abs(sample),axis=1),floor)
    span = np.divide(np.ptp(sample,axis=1),denominator,out=np.zeros(p.state_size),where=denominator>0)
    if not np.isclose(max(span),record["summary"]["late_max_relative_span"],rtol=1e-10,atol=1e-12):
        raise RuntimeError("Recomputed stationarity span differs")
    global_logs = [logsumexp(data["log_biomass"][p.weights>0,g]+np.log(p.weights[p.weights>0,None]),axis=0)+conversion for g in (0,1)]
    events = json.loads(str(data["extinction_events"]))
    windows = [envelope(t,T,global_logs,events,case.years-offset-20000.,case.years-offset) for offset in (60000.,40000.,20000.,0.)]
    sample_indices = np.unique(np.linspace(np.flatnonzero(late)[0],len(t)-1,21).astype(int))
    fluxes = {int(index):model.fluxes(y[:,index],p,trial_extension=True) for index in sample_indices}
    failures = [int(k) for k in np.argsort(span)[::-1] if span[k] >= .001]
    stocks = [stock_evidence(k,y,data,p,late,span,fluxes) for k in failures]
    amplitudes = np.array([v["sampled_range_k"] for v in windows])
    material = float(amplitudes[-1]) >= .01
    persistent = bool(material and all(v["peaks"]>=3 for v in windows)
                      and max(amplitudes)/min(amplitudes)<1.2)
    known_path = known.get(record["fingerprint"])
    if known_path and known_path["raw_sha256"] != record["raw_sha256"]:
        raise RuntimeError("Cycle review raw checksum differs")
    dormant_only = bool(failures and all(k<p.state_size-1 and k%6 in (4,5) for k in failures)
                        and record["summary"]["late_temperature_span_k"]<.01)
    if known_path:
        category, followup = known_path["kind"], "No hold merely to force stationarity; retain the reviewed finite-observation and solver-family scope."
    elif persistent:
        category, followup = "unreviewed_persistent_material_oscillation", "Representative bounded precision continuation and root/stability evidence, rather than an equilibrium-seeking hold."
    elif material and windows[-1]["net_change_fraction_of_total_variation"]>.98:
        category, followup = "monotone_material_climate_relaxation", "A bounded physical hold can change material endpoint interpretation."
    elif material:
        category, followup = "material_oscillation_or_relaxation_unresolved", "Check envelope decay and bounded precision before deciding on an additional hold."
    elif dormant_only:
        category, followup = "dormant_stock_only_stationarity_failure", "No material-hold requirement established. Resolve decay/source balance or targeted precision only if strict full-stock equality is needed; smallness alone is not noise evidence."
    else:
        category, followup = "other_stock_stationarity_failure", "Inspect the reported physical stocks before assigning a hold or numerical explanation."
    return dict(case_id=case.case_id,case=record["protocol"]["case"],fingerprint=record["fingerprint"],raw_file=record["raw_file"],raw_sha256=record["raw_sha256"],
        native_settling_status=record["summary"]["settling_status"], native_endpoint_class=record["summary"]["endpoint_class"],
        classification=category, followup=followup, known_review=known_path,
        late_temperature_span_k=record["summary"]["late_temperature_span_k"],late_max_relative_span=record["summary"]["late_max_relative_span"],
        max_scaled_derivative=record["summary"]["max_scaled_derivative"],late_occupancy_changes=record["summary"]["late_occupancy_changes"],
        sampled_late_envelopes=windows, census_removals=len(events),late_census_removals=sum(v["time_yr"]>=case.years-20000 for v in events),
        changing_stocks=stocks,late_relative_span_tolerance=.001,
        dormant_tail_shape=("all_failing_banks_monotone_at_sampling" if all(s.get("retained_late_log_net_fraction_of_variation",0)>.98 for s in stocks)
                            else "at_least_one_failing_bank_nonmonotone_at_sampling") if dormant_only else None,
        population_scope="Contemporaneous global X+Z counts. Retained logs and decoded physical counts are shown separately; no demographic survival or asymptotic-attractor claim.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir",type=Path,default=runner.RAW)
    parser.add_argument("--snapshot",type=Path)
    parser.add_argument("--output",type=Path,default=Path(__file__).with_suffix(".json"))
    args = parser.parse_args()
    identity, entries, records = snapshot_records(args.raw_dir,args.snapshot)
    known, review_hashes = reviewed_paths()
    source_epochs, rows = {}, []
    statuses = Counter()
    for entry,record in zip(entries,records):
        protocol = record["protocol"]
        epoch = sha256(e.dumps(dict(solver=protocol.get("solver","native_frozen"),sources=protocol["source_sha256"])).encode()).hexdigest()
        if epoch not in source_epochs:
            source_epochs[epoch] = dict(solver=protocol.get("solver","native_frozen"),source_sha256=protocol["source_sha256"],
                current_source_mismatches=[name for name,value in protocol["source_sha256"].items() if not (ROOT/name).exists() or digest(ROOT/name)!=value])
        entry["source_epoch"] = epoch
        entry["declared_horizon_yr"] = protocol["case"]["years"]
        entry["native_settling_status"] = record["summary"]["settling_status"]
        statuses[entry["native_settling_status"]] += 1
        data = survival.load(record,args.raw_dir)
        if float(data["t"][-1]) != protocol["case"]["years"]:
            raise RuntimeError("Incomplete selected horizon")
        if entry["native_settling_status"] != "census_stationary":
            rows.append(diagnose(record,data,known))
        if digest(args.raw_dir/entry["raw_file"]) != entry["raw_sha256"] or digest(args.raw_dir/entry["receipt_file"]) != entry["receipt_sha256"]:
            raise RuntimeError("Selected input changed during the diagnostic pass")
    result = dict(schema="dormancy_endpoint_diagnostics_v1",**identity,
        scope="One completed planned-census snapshot; no integrations, probability calculations, threshold changes or new stationarity labels.",
        selected_receipts=entries,source_epochs=source_epochs,status_counts=dict(statuses),
        diagnostic_counts=dict(Counter(v["classification"] for v in rows)),review_sha256=review_hashes,
        source_sha256={str(path.relative_to(ROOT)):digest(path) for path in (Path(__file__),Path(model.__file__),Path(runner.__file__),Path(survival.__file__))},
        methods=dict(envelopes="Four 20,000-year windows with 10-year observations. Peak periods use sampled times and optional three-point parabolic interpolation; these are finite-resolution estimates.",
            persistent_candidate="At least 3 peaks per window, temperature range >= 0.01 K and all four ranges within 20%. This is a triage heuristic, not a stationarity or periodic-orbit test.",
            dormant_failure="Every failing stock is dormant, while temperature passes its original 0.01 K bound. Stock/cell fractions and 21 sampled current-platform source balances explain scale without diagnosing noise from smallness.",
            no_new_labels="Native summaries and physical/census rules remain unchanged. Source-free predictions are counterfactual diagnostics unless every sampled retained incoming source is absent; no between-sample absence proof is claimed."),rows=rows)
    payload=e.dumps(result)+"\n"
    if len(payload.encode())>=1000000:raise RuntimeError("Compact public diagnostic exceeds1MB")
    args.output.write_text(payload)
    print(e.dumps(dict(selected=len(entries),status=result["status_counts"],diagnostics=result["diagnostic_counts"],bytes=len(payload.encode()))))


if __name__ == "__main__":
    main()
