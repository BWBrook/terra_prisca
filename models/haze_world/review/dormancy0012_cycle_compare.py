"""Verify and compare the completed 0012 control; no forward integrations.

    uv run python models/haze_world/review/dormancy0012_cycle_compare.py
"""

from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.special import logsumexp

from terra_prisca.haze_world import dormancy_experiments as experiments
from terra_prisca.haze_world import turnover_survival as profiles

ROOT = experiments.e.ROOT
HERE = Path(__file__).parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    compact_file = HERE/"dormancy0012_cycle_check.json"
    compact = json.loads(compact_file.read_text())
    full_file = ROOT/compact["full_receipt_file"]
    if digest(full_file) != compact["full_receipt_sha256"]:
        raise RuntimeError("The completed control receipt changed")
    result = json.loads(full_file.read_text())
    protocol = result["protocol"]
    if result["status"] != "completed" or not result["source_unchanged"] or not result["nonnegative_stocks"]:
        raise RuntimeError("The full control is not qualified for comparison")
    if digest(HERE/"dormancy0012_cycle_check.py") != protocol["checker_sha256"]:
        raise RuntimeError("The control checker changed")
    for source, expected in protocol["source_sha256"].items():
        if digest(ROOT/source) != expected:
            raise RuntimeError("A recorded source dependency changed")
    for source, expected in protocol["imported_review_sha256"].items():
        if digest(HERE/source) != expected:
            raise RuntimeError("An imported review dependency changed")
    native_file = ROOT/protocol["original_receipt"]
    if digest(native_file) != protocol["original_receipt_sha256"]:
        raise RuntimeError("The native receipt changed")
    record = json.loads(native_file.read_text())
    native = profiles.load(record, experiments.RAW)
    payload = ROOT/result["raw_file"]
    if digest(payload) != result["raw_sha256"]:
        raise RuntimeError("The control payload changed")
    with np.load(payload) as values:
        control = {key: values[key] for key in values.files}
    p = experiments.parameters(experiments.Case(**record["protocol"]["case"]))
    active = p.weights > 0
    common, a, b = np.intersect1d(native["t"], control["t"], return_indices=True)
    weights = np.log(p.weights[active, None, None])
    global_logs = [logsumexp(data["log_biomass"][active][:, :, index]+weights, axis=0)
                   for data, index in ((native, a), (control, b))]
    conversion = result["metadata"]["global_log_cell_conversion"]
    occupied = []
    for data, index in ((native, a), (control, b)):
        log_cells = data["log_biomass"][active][:, :, index]+weights+conversion
        occupied.append(log_cells >= -1e-10)
    native_culls = result["native_matched_culls"]["events"]
    control_culls = result["control_culls"]["events"]
    native_keys = [(event["time_yr"], event["patch"], event["guild"]) for event in native_culls]
    control_keys = [(event["time_yr"]+80000., event["patch"], event["guild"]) for event in control_culls]
    same_culls = native_keys == control_keys
    difference = (max(abs(a["removed_cells"]-b["removed_cells"]) for a, b in zip(native_culls, control_culls))
                  if same_culls and native_culls else None)
    summary = dict(checker_sha256=digest(Path(__file__)), control_receipt=str(full_file.relative_to(ROOT)),
        control_receipt_sha256=digest(full_file), compact_audit_sha256=digest(compact_file),
        original_fingerprint=record["fingerprint"], original_raw_sha256=record["raw_sha256"],
        control_raw_file=result["raw_file"], control_raw_sha256=result["raw_sha256"], common_samples=int(len(common)),
        common_time_maximum_temperature_difference_k=result["common_time_maximum_temperature_difference_k"],
        common_time_maximum_global_log10_count_difference=(np.max(abs(global_logs[0]-global_logs[1]), axis=1)/np.log(10)).tolist(),
        identical_local_census_occupancy=bool(np.array_equal(*occupied)),
        identical_global_census_occupancy=bool(np.array_equal(np.any(occupied[0], axis=0), np.any(occupied[1], axis=0))),
        identical_cull_times_patches_and_guilds=same_culls, matched_culls=len(control_culls),
        maximum_paired_cull_cell_difference=difference,
        native_late_period_yr=result["native_windows"][-1]["period_yr"], control_period_yr=result["control_window"]["period_yr"],
        period_relative_difference_from_long_native_fit=result["control_window"]["period_yr"]/result["native_windows"][-1]["period_yr"]-1,
        period_scope="The matched native2k window has only four ten-year-sampled peaks and its440yr fit is quantized. The longer native45-peak fit is442.602yr; the annual four-peak control fit is442.6yr.",
        native_matched_sampled_range_k=result["native_matched_window"]["sampled_range_k"],
        native_late_sampled_range_k=result["native_windows"][-1]["sampled_range_k"], control_sampled_range_k=result["control_window"]["sampled_range_k"],
        control_dense_minimum_global_log10_cells=result["control_dense_minimum_global_log10_cells"],
        interpretation="Precision-supported persistent finite-census hybrid-cycle candidate. Local warm-acetogen culls recur, both guilds remain globally present, and a locally stable mixed continuous equilibrium also exists. No global-basin, Hopf or stochastic-survival claim.",
        finite_population_limit="The deterministic control reaches only about14500acetogens worldwide. This is not the macroscopic minimum seen in0068; robustness to demographic randomness, repeated bottlenecks or global cell-count calibration is not established by this continuation.",
        source_and_initialization_scope="Same75c helper; all source/payload/checker hashes verified. Exact physical80k start, no stage-log mask changes, fresh solver/charts and relative clock; no seeds or physical stock reset.")
    Path(__file__).with_suffix(".json").write_text(experiments.e.dumps(summary)+"\n")
    print(json.dumps({key: summary[key] for key in ("identical_cull_times_patches_and_guilds", "identical_local_census_occupancy", "common_time_maximum_global_log10_count_difference", "maximum_paired_cull_cell_difference")}, indent=2))


if __name__ == "__main__":
    main()
