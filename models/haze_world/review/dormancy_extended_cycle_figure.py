"""Validate and plot the completed 0068 precision continuation; no new runs.

    uv run python models/haze_world/review/dormancy_extended_cycle_figure.py
"""

from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
from scipy.special import logsumexp

from terra_prisca.haze_world import dormancy_experiments as experiments
from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import turnover_survival as profiles

ROOT = experiments.e.ROOT
HERE = Path(__file__).parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def refined_period(time, temperature):
    peaks, _ = find_peaks(temperature, prominence=.1*np.ptp(temperature))
    refined = []
    for k in peaks:
        if time[k]-time[k-1] != time[k+1]-time[k]:
            raise ArithmeticError("Parabolic peak interpolation requires equally spaced samples")
        denominator = temperature[k-1]-2*temperature[k]+temperature[k+1]
        shift = .5*(temperature[k-1]-temperature[k+1])/denominator
        refined.append(float(time[k]+shift*(time[k+1]-time[k])))
    return dict(sampled_peak_times_yr=time[peaks].tolist(), interpolated_peak_times_yr=refined,
        fitted_period_yr=float(np.polyfit(np.arange(len(refined)), refined, 1)[0]),
        scope="Three-point parabolic peak interpolation of recorded samples; a sampling diagnostic, not a continuous-orbit proof.")


def main():
    review_file = HERE / "dormancy_extended_cycle_check.json"
    review = json.loads(review_file.read_text())
    if digest(HERE / "dormancy_extended_cycle_check.py") != review["checker_sha256"]:
        raise RuntimeError("The extended review checker changed")
    files = list((ROOT / "local/haze/dormancy_extended_cycle_precision").glob("*.receipt.json"))
    if len(files) != 1:
        raise RuntimeError("Missing or ambiguous precision receipt")
    receipt_file = files[0]
    receipt = json.loads(receipt_file.read_text())
    if receipt["status"] != "completed" or not receipt["source_unchanged"] or not receipt["nonnegative_stocks"]:
        raise RuntimeError("The precision continuation did not qualify")
    protocol = receipt["protocol"]
    for source, expected in protocol["source_sha256"].items():
        if digest(ROOT / source) != expected:
            raise RuntimeError(f"The recorded source changed: {source}")
    if digest(HERE / "dormancy_extended_cycle_precision.py") != protocol["checker_sha256"]:
        raise RuntimeError("The precision checker changed")
    if digest(HERE / "dormancy_spatial_cycle_check.py") != protocol["envelope_checker_sha256"]:
        raise RuntimeError("The envelope checker changed")
    if sha256(experiments.e.dumps(protocol).encode()).hexdigest() != receipt["fingerprint"]:
        raise RuntimeError("The precision fingerprint changed")
    payload = ROOT / receipt["raw_file"]
    if digest(payload) != receipt["raw_sha256"]:
        raise RuntimeError("The precision payload changed")
    original = profiles.records(experiments.RAW, "census")["dormancy_0068"]
    if original["fingerprint"] != protocol["original_fingerprint"] or original["raw_sha256"] != protocol["original_raw_sha256"]:
        raise RuntimeError("The native input record changed")
    native = profiles.load(original, experiments.RAW)
    with np.load(payload) as values:
        control = {name: values[name] for name in ("t", "y", "log_active", "log_dormant")}
    initial = native["y"][:, np.flatnonzero(native["t"] == 80000.)[0]]
    if not np.array_equal(initial, np.asarray(protocol["initial_y"])):
        raise RuntimeError("The control did not use the exact native start")
    p = experiments.parameters(experiments.Case(**original["protocol"]["case"]))
    row = next(item for item in review["rows"] if item["case_id"] == "dormancy_0068")
    root = row["mixed_equilibrium"]
    active = p.weights > 0
    conversion = receipt["metadata"]["global_log_cell_conversion"]
    fig, (temperature_axis, phase_axis) = plt.subplots(1, 2, figsize=(9., 4.2), layout="constrained")
    periods = {}
    for label, data, color, marker in (("Native: 10-year samples", native, "#8c8c8c", "o"),
                                       ("Precision: annual samples", control, "#005a8d", None)):
        use = (data["t"] >= 80000.) & (data["t"] <= 82000.)
        time = data["t"][use]
        temperature = np.asarray(model.core.temperature_k(data["y"][-1, use], p.coupled.climate))
        periods[label] = refined_period(time, temperature)
        show = time <= 81800.
        kwargs = dict(color=color, lw=1.1, label=label)
        if marker:
            kwargs.update(marker=marker, markersize=2.2, markerfacecolor="white", markeredgewidth=.5)
        temperature_axis.plot(time[show]-80000., temperature[show], **kwargs)
        stage_counts = []
        for name in ("log_active", "log_dormant"):
            logs = data[name][active][:, 0, :][:, use][:, show]
            stage_counts.append((logsumexp(logs+np.log(p.weights[active, None]), axis=0)+conversion)/np.log(10))
        phase_axis.plot(*stage_counts, **kwargs)
    root_y = np.array(root["y"])
    root_counts = [np.log10(float(p.weights @ root_y[index[:, 0]]))+conversion/np.log(10)
                   for index in (p.biomass_indices, p.dormant_indices)]
    temperature_axis.axhline(root["temperature_k"], ls="--", color="#a54720", lw=1., label="Locally stable mixed root")
    phase_axis.plot(*root_counts, "*", color="#a54720", markersize=11., zorder=4)
    temperature_axis.set(xlabel="Years after recorded 80k-year start", ylabel="Global temperature (K)", xlim=(0., 1800.))
    phase_axis.set(xlabel="Global active acetogens (log₁₀ cells)", ylabel="Global dormant acetogens (log₁₀ cells)")
    temperature_axis.legend(fontsize=7., frameon=False, loc="lower left")
    for axis in (temperature_axis, phase_axis):
        axis.grid(alpha=.2)
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(labelsize=8.)
    fig.suptitle("Warm refuge, 50% acetate recycling: persistent climate oscillations", fontsize=11.)
    caption = ("A locally stable mixed equilibrium also exists; no Hopf or global-attractor claim.\n"
               "The 2,000-year continuation uses the same LSODA family at tighter tolerance; fewest acetogens ≈ 9.45 × 10¹² cells.")
    fig.supxlabel(caption, fontsize=7.5)
    target = ROOT / "models/haze_world/figures/dormancy/extended_cycle_0068.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=220)
    plt.close(fig)
    result = dict(checker_sha256=digest(Path(__file__)), review_file=str(review_file.relative_to(ROOT)), review_sha256=digest(review_file),
        receipt_file=str(receipt_file.relative_to(ROOT)), receipt_sha256=digest(receipt_file),
        precision_receipt=receipt, matched_window_peak_interpolation=periods,
        interpolated_period_relative_difference=periods["Precision: annual samples"]["fitted_period_yr"]/periods["Native: 10-year samples"]["fitted_period_yr"]-1,
        figure=str(target.relative_to(ROOT)), figure_sha256=digest(target), mixed_equilibrium=root,
        interpretation="Precision-supported finite-amplitude cycle candidate alongside a locally stable mixed root. Same-solver, finite-observation and unenumerated-basin qualifications remain; native0068 and0069 settling statuses stay unchanged.",
        caption=caption)
    output = HERE / "dormancy_extended_cycle_precision.json"
    output.write_text(experiments.e.dumps(result)+"\n")
    print(json.dumps(dict(figure=result["figure"], interpolated_period_relative_difference=result["interpolated_period_relative_difference"], periods=periods), indent=2))


if __name__ == "__main__":
    main()
