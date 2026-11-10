"""Regenerate the two-panel 0012 cycle comparison without integrations.

    uv run python models/haze_world/review/dormancy0012_cycle_figure.py
"""

from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator
import numpy as np
from scipy.special import logsumexp

from terra_prisca.haze_world import dormancy_experiments as experiments
from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import turnover_survival as profiles

ROOT = experiments.e.ROOT
HERE = Path(__file__).parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    audit_file = HERE/"dormancy0012_cycle_check.json"
    audit = json.loads(audit_file.read_text())
    receipt_file = ROOT/audit["full_receipt_file"]
    if digest(receipt_file) != audit["full_receipt_sha256"]:
        raise RuntimeError("The control receipt changed")
    receipt = json.loads(receipt_file.read_text())
    protocol = receipt["protocol"]
    if receipt["status"] != "completed" or not receipt["source_unchanged"]:
        raise RuntimeError("The 0012 continuation did not complete with frozen sources")
    comparison_file = HERE/"dormancy0012_cycle_compare.json"
    comparison = json.loads(comparison_file.read_text())
    if comparison["control_receipt_sha256"] != digest(receipt_file) or comparison["compact_audit_sha256"] != digest(audit_file):
        raise RuntimeError("The read-only comparison uses different inputs")
    if comparison["checker_sha256"] != digest(HERE/"dormancy0012_cycle_compare.py"):
        raise RuntimeError("The comparison checker changed")
    for path, expected in protocol["source_sha256"].items():
        if digest(ROOT/path) != expected:
            raise RuntimeError("A source dependency changed")
    if digest(HERE/"dormancy0012_cycle_check.py") != protocol["checker_sha256"]:
        raise RuntimeError("The control checker changed")
    original_file = ROOT/protocol["original_receipt"]
    if digest(original_file) != protocol["original_receipt_sha256"]:
        raise RuntimeError("The native receipt changed")
    original = json.loads(original_file.read_text())
    native = profiles.load(original, experiments.RAW)
    control_file = ROOT/receipt["raw_file"]
    if digest(control_file) != receipt["raw_sha256"]:
        raise RuntimeError("The control payload changed")
    with np.load(control_file) as data:
        control = {name: data[name] for name in ("t", "y", "log_biomass")}
    p = experiments.parameters(experiments.Case(**original["protocol"]["case"]))
    active = p.weights > 0
    conversion = receipt["metadata"]["global_log_cell_conversion"]
    fig, (climate, population) = plt.subplots(1, 2, figsize=(9.2, 4.1), layout="constrained")
    for label, data, color, marker in (("Native: 10-year samples", native, "#8c8c8c", "o"),
                                       ("Precision: annual samples", control, "#005a8d", None)):
        use = (data["t"] >= 80000.) & (data["t"] <= 82000.)
        time = data["t"][use]/1000.
        temperature = np.asarray(model.core.temperature_k(data["y"][-1, use], p.coupled.climate))
        logs = data["log_biomass"][active][:, 0, :][:, use]
        cells = np.exp(logsumexp(logs+np.log(p.weights[active, None]), axis=0)+conversion)
        style = dict(color=color, linewidth=1.1, label=label)
        if marker:
            style.update(marker=marker, markersize=2.2, markerfacecolor="white", markeredgewidth=.5)
        climate.plot(time, temperature, **style)
        population.plot(time, cells, **style)
    climate.axhline(receipt["mixed_equilibrium"]["temperature_k"], color="#a54720", linestyle="--", linewidth=1.,
                   label="Locally stable mixed equilibrium")
    culls = receipt["native_matched_culls"]["events"]
    cull_times = [event["time_yr"]/1000. for event in culls]
    population.plot(cull_times, np.full(len(culls), .025), linestyle="none", marker="|", markersize=7., color="#a54720",
                    transform=population.get_xaxis_transform(), label="28 warm-A removals: local one-cell census")
    climate.set(ylabel="Global temperature (K)")
    population.set(ylabel="Acetogens worldwide (cells)", yscale="log")
    population.yaxis.set_major_locator(LogLocator(base=10., numticks=7))
    climate.legend(fontsize=7., frameon=False, loc="lower right")
    population.legend(fontsize=7., frameon=False, loc="upper left")
    for axis in (climate, population):
        axis.set(xlim=(80., 82.), xlabel="Model time (kyr)")
        axis.grid(alpha=.2)
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(labelsize=8.)
    fig.suptitle("Case 0012: persistent finite-census cycle candidate", fontsize=12.)
    caption = ("Global acetogens fall to ≈14,500 cells; rug marks removals in the warm patch at its local one-cell census.\n"
               "A locally stable mixed equilibrium also exists. Same-solver precision control; no Hopf or global-basin proof.")
    fig.supxlabel(caption, fontsize=7.5)
    target = ROOT/"models/haze_world/figures/dormancy/cycle_0012.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=220)
    plt.close(fig)
    manifest = dict(regenerator_sha256=digest(Path(__file__)), figure=str(target.relative_to(ROOT)), figure_sha256=digest(target),
        input_sha256={str(path.relative_to(ROOT)): digest(path) for path in (
            audit_file, comparison_file, receipt_file, original_file, experiments.RAW/original["raw_file"], control_file)},
        source_sha256=protocol["source_sha256"], control_checker_sha256=protocol["checker_sha256"],
        original_fingerprint=original["fingerprint"], control_fingerprint=receipt["fingerprint"],
        initialization=dict(physical_start_yr=80000., relative_solver_start_yr=0.,
            coordinate_roundtrip_maximum_relative_error=protocol["initial_coordinate_roundtrip_maximum_relative_error"],
            finite_stage_log_mask_changes=protocol["initial_stage_log_finite_mask_changes"]), caption=caption,
        scope="Only recorded80–82k trajectories; no new integration. The rug encodes local cull timing, not a global extinction threshold.")
    Path(__file__).with_suffix(".json").write_text(experiments.e.dumps(manifest)+"\n")
    print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
