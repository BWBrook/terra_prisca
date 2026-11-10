"""Validate cycle precision receipts and plot their recorded trajectories.

    uv run python models/haze_world/review/dormancy_spatial_cycle_figure.py

This reads completed controls only; it runs no forward integrations.
"""

from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_experiments as experiments
from terra_prisca.haze_world import turnover_survival as profiles


ROOT = experiments.e.ROOT
HERE = Path(__file__).parent
RAW = ROOT / "local/haze/dormancy_spatial_cycle_precision"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def aligned(data, p):
    use = (data["t"] >= 80000.) & (data["t"] <= 82000.)
    time = data["t"][use]
    state = data["y"][:, use]
    temperature = np.asarray(model.core.temperature_k(state[-1], p.coupled.climate))
    peaks, _ = find_peaks(temperature, prominence=.1 * np.ptp(temperature))
    if len(peaks) < 4:
        raise ArithmeticError("The recorded continuation does not contain four peaks")
    relative = time - time[peaks[0]]
    show = (relative >= 0.) & (relative <= 500.)
    return relative[show], state[:, show], temperature[show], float(time[peaks[0]])


def main():
    review_path = HERE / "dormancy_spatial_cycle_check.json"
    review = json.loads(review_path.read_text())
    if digest(HERE / "dormancy_spatial_cycle_check.py") != review["checker_sha256"]:
        raise RuntimeError("The equilibrium review checker changed")
    records = profiles.records(experiments.RAW, "census")
    fig, axes = plt.subplots(2, 2, figsize=(8.2, 6.1), layout="constrained")
    rows = []
    for index, case_id in enumerate(("dormancy_0030", "dormancy_0038")):
        files = list(RAW.glob(f"{case_id}_precision2000-*.receipt.json"))
        if len(files) != 1:
            raise RuntimeError("Missing or ambiguous precision-control receipt")
        receipt_path = files[0]
        receipt = json.loads(receipt_path.read_text())
        protocol = receipt["protocol"]
        if receipt["status"] != "completed" or not receipt["source_unchanged"] or not receipt["nonnegative_stocks"]:
            raise RuntimeError("The precision control did not qualify")
        if protocol["rtol"] != 2e-9 or protocol["max_step_yr"] != 1. or protocol["output_stride_yr"] != 1.:
            raise RuntimeError("Unexpected numerical-control protocol")
        if protocol["census"]["census_yr"] != 10. or protocol["census"]["minimum_cells"] != 1.:
            raise RuntimeError("The ten-year one-cell census changed")
        for source, expected in protocol["source_sha256"].items():
            if digest(ROOT / source) != expected:
                raise RuntimeError(f"Source graph changed: {source}")
        if digest(HERE / "dormancy_spatial_cycle_precision.py") != protocol["checker_sha256"]:
            raise RuntimeError("The precision-control checker changed")
        if protocol["summary_checker_sha256"] != review["checker_sha256"]:
            raise RuntimeError("The two reviews use different equilibrium checkers")
        payload = ROOT / receipt["raw_file"]
        if digest(payload) != receipt["raw_sha256"]:
            raise RuntimeError("Precision-control payload checksum failed")
        record = records[case_id]
        if protocol["original_fingerprint"] != record["fingerprint"] or protocol["original_raw_sha256"] != record["raw_sha256"]:
            raise RuntimeError("The precision control started from a different native path")
        native = profiles.load(record, experiments.RAW)
        with np.load(payload) as values:
            control = {key: values[key] for key in ("t", "y")}
        if not np.array_equal(control["t"], np.arange(80000., 82001.)):
            raise RuntimeError("The annual accepted-flow observations are incomplete")
        native_start = np.flatnonzero(native["t"] == 80000.)
        initial = np.array(protocol["initial_y"])
        if len(native_start) != 1 or not np.array_equal(initial, native["y"][:, native_start[0]]):
            raise RuntimeError("The control did not preserve the recorded 80k-year start")
        if not np.allclose(control["y"][:, 0], initial, rtol=8*np.finfo(float).eps, atol=0.):
            raise RuntimeError("The initial coordinate round trip exceeds floating-point roundoff")
        initial_roundtrip_error = float(np.max(np.divide(abs(control["y"][:, 0] - initial), abs(initial),
                                                        out=np.zeros_like(initial), where=initial != 0.)))
        row = next(item for item in review["rows"] if item["case_id"] == case_id)
        p = experiments.parameters(experiments.Case(**record["protocol"]["case"]))
        equilibrium = row["mixed_equilibrium"]
        root = np.array(equilibrium["y"])
        axis_t, axis_xz = axes[index]
        first_peaks = {}
        for label, data, color, marker in (
            ("Native: 10-year samples", native, "#8c8c8c", "o"),
            ("Precision: annual samples", control, "#005a8d", None),
        ):
            time, state, temperature, first_peak = aligned(data, p)
            first_peaks[label] = first_peak
            kwargs = dict(color=color, lw=1.2, label=label, zorder=2 if marker else 3)
            if marker:
                kwargs.update(marker=marker, markersize=2.7, markerfacecolor="white", markeredgewidth=.6)
            axis_t.plot(time, temperature, **kwargs)
            axis_xz.plot(state[1] * 1000., state[4] * 1000., **kwargs)
        axis_t.axhline(equilibrium["temperature_k"], color="#a54720", ls="--", lw=1., label="Locally stable mixed root")
        axis_xz.plot(root[1] * 1000., root[4] * 1000., "*", color="#a54720", markersize=11.,
                     label="Locally stable mixed root", zorder=4)
        axis_t.set(xlim=(0., 500.), xlabel="Years after each first recorded peak", ylabel="Global temperature (K)")
        axis_xz.set(xlabel="Active acetogens (mg dry mass/L)", ylabel="Dormant acetogens (mg dry mass/L)")
        axis_xz.set_ylim(bottom=-.004)
        axis_t.set_title(f"Dormant loss / active loss: ε = {p.epsilon:g}", fontsize=10.)
        axis_xz.set_title("Bulk active–dormant phase portrait", fontsize=10.)
        for axis in (axis_t, axis_xz):
            axis.tick_params(labelsize=8.)
            axis.grid(alpha=.18)
            axis.spines[["top", "right"]].set_visible(False)
        if index == 0:
            axis_t.legend(fontsize=7., loc="lower right", frameon=False)
        native_use = (native["t"] >= 80000.) & (native["t"] <= 82000.)
        common, native_index, control_index = np.intersect1d(native["t"][native_use], control["t"], return_indices=True)
        native_state = native["y"][:, native_use][:, native_index]
        control_state = control["y"][:, control_index]
        common_temperature_difference = np.asarray(model.core.temperature_k(native_state[-1], p.coupled.climate)) - np.asarray(model.core.temperature_k(control_state[-1], p.coupled.climate))
        rows.append(dict(case_id=case_id, epsilon=p.epsilon,
            receipt_file=str(receipt_path.relative_to(ROOT)), receipt_sha256=digest(receipt_path),
            raw_file=receipt["raw_file"], raw_sha256=receipt["raw_sha256"],
            native_fingerprint=record["fingerprint"], native_raw_file=record["raw_file"], native_raw_sha256=record["raw_sha256"],
            verified_protocol=protocol, wall_seconds=receipt["wall_seconds"], accepted_steps=receipt["metadata"]["accepted_steps"],
            nonnegative_stocks=receipt["nonnegative_stocks"],
            numerical_events={key: receipt["metadata"][key] for key in (
                "trial_guard_rejections", "trial_guard_stage_conditionings", "trial_guard_chemical_conditionings")},
            initial_coordinate_roundtrip_maximum_relative_error=initial_roundtrip_error,
            first_peak_absolute_yr=first_peaks, plotted_duration_yr=500.,
            control=receipt["control"], native=receipt["native"],
            period_relative_difference=receipt["period_relative_difference"],
            sampled_range_relative_difference=receipt["sampled_range_relative_difference"],
            common_unaligned_times=int(len(common)), common_time_maximum_temperature_difference_k=float(max(abs(common_temperature_difference))),
            control_dense_global_min_log10_cells=receipt["control_dense_global_min_log10_cells"],
            native_sampled_global_min_log10_cells=receipt["native_sampled_global_min_log10_cells"],
            census_removals=receipt["census_removals"], mixed_equilibrium=equilibrium))
    caption = ("Persistent finite-amplitude cycle candidates coexist with a locally stable mixed root; no Hopf claim.\n"
               "Tighter continuation uses the same stiff-solver family. All four recorded paths remain classified as unsettled.")
    fig.suptitle("Spatial dormancy: persistent cycles and a stable mixed equilibrium", fontsize=12.)
    fig.supxlabel(caption, fontsize=8.)
    target = ROOT / "models/haze_world/figures/dormancy/spatial_cycles.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=220)
    plt.close(fig)
    result = dict(checker_sha256=digest(Path(__file__)), equilibrium_review_sha256=digest(review_path),
        figure=str(target.relative_to(ROOT)), figure_sha256=digest(target), rows=rows,
        source_verification="All selected source, checker, original-payload and precision-payload hashes verified live. Inputs exactly equal the recorded 80k-year states; initial coordinate round-trip errors are recorded separately.",
        interpretation="Finite-amplitude persistent-cycle / multiple-attractor candidates alongside locally stable mixed equilibria, not linear destabilization of those roots.",
        physical_population_scope="Both whole-guild minima exceed 10^24 cells in the continued windows; neither control has a census removal. Active–dormant phase loops are material biomass, not ghost recovery.",
        solver_scope="Both resolution controls use the named b5c guarded LSODA variant, rtol2e-9 and max_step1yr; no independent-solver or rigorous periodic-orbit proof.",
        caption=caption)
    output = HERE / "dormancy_spatial_cycle_precision.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
