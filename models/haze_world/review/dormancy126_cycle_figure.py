"""Plot the two checksum-verified, nonspatial cross-solver continuations."""

from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from terra_prisca.haze_world import dormancy_experiments as experiments
from terra_prisca.haze_world import population_coupling as climate
from terra_prisca.haze_world import turnover_survival as profiles

ROOT = experiments.e.ROOT
HERE = Path(__file__).parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    fig, axes = plt.subplots(2, 1, figsize=(8, 5.6), sharex=True, layout="constrained")
    inputs = {}
    for ax, key in zip(axes, ("0024", "0126")):
        compact_path = HERE/f"dormancy126_cycle_{key}.json"
        compact = json.loads(compact_path.read_text())
        receipt_path = ROOT/compact["full_receipt"]
        if digest(receipt_path) != compact["full_receipt_sha256"]:
            raise RuntimeError("Changed cycle-control receipt")
        control = json.loads(receipt_path.read_text())
        if control["status"] != "completed":
            raise RuntimeError("Incomplete cycle continuation")
        protocol = control["protocol"]
        native_path = ROOT/protocol["native_receipt"]
        if digest(native_path) != protocol["native_receipt_sha256"]:
            raise RuntimeError("Changed original cycle receipt")
        native = json.loads(native_path.read_text())
        if native["fingerprint"] != protocol["native_fingerprint"]:
            raise RuntimeError("Changed original cycle protocol")
        data = profiles.load(native, experiments.RAW)
        payload = ROOT/control["raw_file"]
        if digest(payload) != control["raw_sha256"]:
            raise RuntimeError("Changed cycle-control payload")
        p = experiments.parameters(experiments.Case(**protocol["case"]))
        with np.load(payload) as source:
            t, y = source["t"], source["y"]
        selected = (t >= 80000.) & (t <= 80600.)
        ax.plot(t[selected]-80000., climate.temperature_k(y[-1, selected], p.coupled.climate),
                color="#39728d", linewidth=1.5, label="Radau: annual precision control")
        selected = (data["t"] >= 80000.) & (data["t"] <= 80600.)
        ax.plot(data["t"][selected]-80000., climate.temperature_k(data["y"][-1, selected], p.coupled.climate),
                ".", color="#242424", markersize=3, label="Original: ten-year samples")
        ax.axhline(control["mixed_equilibrium"]["temperature_k"], color=".55", linewidth=.8,
                   linestyle="--", label="Locally stable mixed equilibrium")
        case = protocol["case"]
        ax.set_title(f"No refuges; loss {case['loss_h']:g}/hour; dormant loss fraction {case['epsilon']:g}")
        ax.set_ylabel("Global temperature (K)")
        ax.grid(alpha=.15)
        for path in (compact_path, receipt_path, native_path, payload, experiments.RAW/native["raw_file"]):
            inputs[str(path.relative_to(ROOT))] = digest(path)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=8, ncol=3, loc="outside upper center")
    axes[-1].set_xlabel("Years after the recorded year-80,000 state")
    target = experiments.OUTPUT/"nonspatial_cycles.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=180)
    plt.close(fig)
    result = dict(checker_sha256=digest(Path(__file__)), inputs=inputs,
                  figure=str(target.relative_to(ROOT)), figure_sha256=digest(target),
                  scope="Finite recurrent paths reproduced by a second solver. Local equilibrium stability does not prove cycle stability or global basins.")
    HERE.joinpath("dormancy126_cycle_figure.json").write_text(experiments.e.dumps(result)+"\n")


if __name__ == "__main__":
    main()
