"""Read-only precision audit of the matched 7046 Linux and Mac census pilots.

    uv run python models/haze_world/review/check_dormancy_platform_precision.py

No integrations, threshold changes or endpoint reclassifications are performed.
"""

from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_experiments as experiments
from terra_prisca.haze_world import turnover_assessment


ROOT = experiments.e.ROOT
RECEIPTS = (
    ROOT / "local/haze/dormancy_linux_pilot/dormancy_0010_census_t100000-c3721df26b697651.receipt.json",
    ROOT / "local/haze/dormancy/dormancy_0010_census_t100000-f7924ad5df000ba5.receipt.json",
)
FIELDS = ("hydrogen_pa", "active_a", "active_m", "acetate_mol_l", "dormant_a", "dormant_m")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    record = json.loads(path.read_text())
    if record["execution_status"] != "complete":
        raise RuntimeError("The matched pilot is incomplete")
    if sha256(experiments.e.dumps(record["protocol"]).encode()).hexdigest() != record["fingerprint"]:
        raise RuntimeError("Protocol fingerprint mismatch")
    raw = path.with_name(record["raw_file"])
    if digest(raw) != record["raw_sha256"]:
        raise RuntimeError("Payload checksum mismatch")
    for source, expected in record["protocol"]["source_sha256"].items():
        if digest(ROOT / source) != expected:
            raise RuntimeError(f"The recorded source changed: {source}")
    with np.load(raw) as values:
        data = {key: values[key] for key in values.files}
    data["metadata"] = json.loads(str(data["metadata"]))
    data["extinction_events"] = json.loads(str(data["extinction_events"]))
    provenance = dict(receipt=str(path.relative_to(ROOT)), receipt_sha256=digest(path),
        raw=str(raw.relative_to(ROOT)), raw_sha256=record["raw_sha256"], fingerprint=record["fingerprint"])
    return record, data, provenance


def audit(record, data, provenance):
    case = experiments.Case(**record["protocol"]["case"])
    p = experiments.parameters(case)
    process = record["protocol"]["census"]
    volume = p.coupled.habitat_l_cm2 * process["surface_cm2"] * p.weights
    floor = np.divide(process["cell_mass_gdw"], volume, out=np.zeros(p.n_patches), where=volume > 0.)
    minimum = np.r_[np.array([[1., v, v, 1e-9, v, v] for v in floor]).ravel(), .001]
    time, values = data["t"], data["y"]
    late = time >= 80000.
    sample = values[:, late]
    scale = np.maximum(np.mean(abs(sample), axis=1), minimum)
    span = np.divide(np.ptp(sample, axis=1), scale, out=np.zeros(p.state_size), where=scale > 0.)
    if not np.isclose(max(span), record["summary"]["late_max_relative_span"], rtol=1e-14):
        raise RuntimeError("The original settling statistic was not reproduced")
    labels = [f"{patch}:{field}" for patch in p.patch_names for field in FIELDS] + ["methane_ratio"]
    cell_rows = []
    for index in np.argsort(span)[::-1][:6]:
        row = dict(stock=labels[index], state_index=int(index), original_relative_span=float(span[index]),
            late_minimum=float(min(sample[index])), late_maximum=float(max(sample[index])),
            late_mean=float(np.mean(sample[index])), final=float(values[index, -1]))
        if index < p.state_size - 1 and index % 6 in (1, 2, 4, 5):
            j = index // 6
            at = np.flatnonzero(late)[int(np.argmax(sample[index]))]
            weighted = np.sum(p.weights[:, None] * (
                values[p.biomass_indices, at] + values[p.dormant_indices, at]), axis=0)
            mass = values[index, at] * volume[j]
            row.update(peak_time_yr=float(time[at]), peak_cells=float(mass / process["cell_mass_gdw"]),
                peak_mass_gdw=float(mass), one_cell_density_gdw_l=float(floor[j]),
                fraction_of_global_total_biomass_at_peak=float(p.weights[j] * values[index, at] / sum(weighted)))
            guild = 0 if index % 6 in (1, 4) else 1
            row["square_root_of_fraction_of_global_guild_biomass_at_peak"] = (
                float(np.sqrt(p.weights[j] * values[index, at] / weighted[guild])) if weighted[guild] > 0. else None)
        cell_rows.append(row)
    fluxes = [model.fluxes(y, p) for y in sample.T]
    net = np.array([f["net_growth_yr"] for f in fluxes])
    sigma = np.array([f["sigma_yr"] for f in fluxes])
    source = sigma * np.moveaxis(values[p.biomass_indices][:, :, late], -1, 0)
    temperature = np.asarray(model.core.temperature_k(values[-1], p.coupled.climate))
    windows = []
    for left, right in ((40000., 60000.), (60000., 80000.), (80000., 100000.)):
        use = (time >= left) & (time <= right)
        ts = temperature[use]
        windows.append(dict(interval_yr=[left, right], temperature_span_k=float(np.ptp(ts)),
            initial_temperature_k=float(ts[0]), final_temperature_k=float(ts[-1]),
            positive_temperature_increments=int(np.sum(np.diff(ts) > 0.)),
            negative_temperature_increments=int(np.sum(np.diff(ts) < 0.))))
    pressure_precision = []
    final = values[:, -1]
    for j, weight in enumerate(p.weights):
        if not weight:
            continue
        index = 6*j
        step = 1e-5 * max(abs(final[index]), 1.)
        plus, minus = final.copy(), final.copy()
        plus[index] += step
        minus[index] -= step
        gradient = (model.fluxes(plus, p)["net_growth_yr"][j, 1] - model.fluxes(minus, p)["net_growth_yr"][j, 1]) / (2*step)
        weight_pa = 1e-7 + case.rtol * abs(final[index])
        pressure_precision.append(dict(patch=p.patch_names[j], sampled_late_methanogen_net_growth_min_yr=float(min(net[:, j, 1])),
            sampled_late_methanogen_net_growth_max_yr=float(max(net[:, j, 1])),
            sampled_late_methanogen_sigma_max_yr=float(max(sigma[:, j, 1])),
            sampled_late_dormant_methanogen_production_max_gdw_l_yr=float(max(source[:, j, 1])),
            final_net_growth_pressure_derivative_yr_pa=float(gradient),
            requested_pressure_local_error_weight_pa=float(weight_pa),
            corresponding_net_growth_sensitivity_scale_yr=float(abs(gradient) * weight_pa)))
    metadata = data["metadata"]
    events = {key: [ev for ev in metadata[key] if ev.get("time_yr", ev.get("accepted_time_yr", 0.)) >= 80000.]
              for key in ("stage_coordinate_switches", "stage_source_restarts", "chemical_conditioning_events", "trial_guard_stage_conditioning_events")}
    stage_root_tolerance = metadata["positive_allocation_absolute_tolerance"]
    root_weights = []
    for index in (5, 11):
        j = index // 6
        total_at_end = np.sum(p.weights * (final[p.biomass_indices[:, 1]] + final[p.dormant_indices[:, 1]]))
        weight_cells = stage_root_tolerance**2 * total_at_end * sum(volume) / process["cell_mass_gdw"]
        root_weights.append(dict(stock=labels[index], square_of_root_absolute_tolerance=stage_root_tolerance**2,
            reference_cell_scale_at_unit_allocation_normalizer=float(weight_cells),
            scope="Coordinate-scale comparison only, not a certified cell error bound or an extinction threshold."))
    return dict(**provenance, protocol=record["protocol"], original_summary=record["summary"],
        reproduced_late_max_relative_span=float(max(span)), largest_late_spans=cell_rows,
        sampled_late_growth_and_sources=pressure_precision, temperature_windows=windows,
        late_events=events, stage_root_tolerance_reference=root_weights,
        late_census_removals=[ev for ev in data["extinction_events"] if ev["time_yr"] >= 80000.])


def main():
    loaded = [read(path) for path in RECEIPTS]
    first, second = (item[0] for item in loaded)
    differences = [key for key in first["protocol"] if first["protocol"][key] != second["protocol"][key]]
    if sorted(differences) != ["architecture", "operating_system"]:
        raise RuntimeError("The matched pilots differ beyond their execution platforms")
    rows = [audit(*item) for item in loaded]
    a, b = (item[1] for item in loaded)
    common, ia, ib = np.intersect1d(a["t"], b["t"], return_indices=True)
    p = experiments.parameters(experiments.Case(**first["protocol"]["case"]))
    temperatures = [np.asarray(model.core.temperature_k(d["y"][-1, index], p.coupled.climate)) for d, index in ((a, ia), (b, ib))]
    comparison = turnover_assessment.compare(first, second, a, b, dormant=True)
    result = dict(checker_sha256=digest(Path(__file__)), protocol_differences=differences,
        common_samples=int(len(common)), common_time_maximum_temperature_difference_k=float(max(abs(temperatures[0]-temperatures[1]))),
        unchanged_endpoint_comparison=comparison, platforms=rows,
        diagnosis="The Linux stationarity failure is confined to two short dormant-methanogen bursts associated with zero/underflow stage conditioning. Their sampled warm-patch peak is about1000cells and about1e-23 of global biomass. The climate follows the same monotone decaying tail on both platforms; this is not evidence of a material climate cycle.",
        source_limit="All late census-sampled methanogen net growth rates are positive and all sampled dormancy entry rates are zero. The full accepted-step source history is not stored, so the precise transient source cannot be reconstructed. Net growth at break-even is much smaller than its sensitivity to the requested donor-pressure local-error weight; that scale is not a rigorous global error bound.",
        record_policy="Retain the already preselected Mac formal run as canonical and archive the Linux pilot independently with its original unsettled flag. The Linux result remains part of this cross-platform audit; no stationarity criterion or record status is changed.",
        gate_assessment="Scoped numerical pass for continuing the climate/community sweep with unchanged acceptance criteria. This matched case establishes macrostate and census-occupancy reproducibility; it does not establish a reproducible near-zero dormant bank, stationary status, or universal numerical qualification. Preserve the Linux unsettled classification, record such flags, and assess material cycles separately.",
        precision_limit="Near-zero stage allocations can differ by hundreds or thousands of worldwide cells while representing about1e-23 of total biomass. Stage-level stationarity on a one-cell scale is therefore not cross-platform reproducible at this solver tolerance. No criteria were relaxed or endpoints reclassified.")
    output = Path(__file__).with_suffix(".json")
    output.write_text(experiments.e.dumps(result) + "\n")
    print(json.dumps(dict(protocol_differences=differences, maximum_temperature_difference_k=result["common_time_maximum_temperature_difference_k"],
        original_stationarity=[row["original_summary"]["settling_status"] for row in rows],
        largest_stock=[row["largest_late_spans"][0] for row in rows]), indent=2))


if __name__ == "__main__":
    main()
