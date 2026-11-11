"""Compare dormant mortality with the measured active deficit in the overshoot."""

import csv
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from terra_prisca.haze_world import buffered_experiments as reference
from terra_prisca.haze_world import habitat_coupling as habitat


ROOT = reference.ROOT
HERE = Path(__file__).parent
OUTPUT = ROOT/"models/haze_world/figures/dormancy"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    table = ROOT/"models/haze_world/figures/bottleneck/survival.csv"
    baseline = [r for r in csv.DictReader(table.open())
                if r["case_id"] in ("main_0008_t100000", "main_0010_t100000") and r["guild"] == "a"]
    scored_table = OUTPUT/"first_survival.csv"
    scored = [r for r in csv.DictReader(scored_table.open())
              if r["configuration"] == "warm" and float(r["fraction"]) == 0.
              and r["direction"] == "A_into_M" and r["guild"] == "a"
              and float(r["dispersal_yr"]) in (1e-9, 1e-6)]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    records = []
    for row, color in zip(sorted(baseline, key=lambda r: float(r["dispersal_yr"])), ("#98643e", "#40798c")):
        payload = ROOT/"local/haze/bottleneck"/row["source_raw_file"]
        receipt = payload.with_suffix(".receipt.json")
        record = json.loads(receipt.read_text())
        assert digest(payload) == row["source_raw_sha256"] == record["raw_sha256"]
        p = reference.parameters(reference.Case(**record["protocol"]["case"]))
        with np.load(payload) as data:
            use = (data["t"] >= 1000.) & (data["t"] <= 1600.)
            time, states = data["t"][use], data["y"][:, use]
        loss = p.base.biology.loss_h*reference.core.HOURS_PER_YEAR
        net = np.array([habitat.fluxes(y, p)["local"][0]["net_growth_yr"][0] for y in states.T])
        deficit = -net/loss
        label = f"Exchange {p.dispersal_yr:g}/yr"
        axes[0].plot(time, deficit, color=color, label=label)
        chosen = sorted((r for r in scored if float(r["dispersal_yr"]) == p.dispersal_yr),
                        key=lambda r: float(r["epsilon"]))
        axes[1].plot([float(r["epsilon"]) for r in chosen],
                     [float(r["log10_min_cells"]) for r in chosen], "o-", color=color, label=label)
        axes[1].axhline(float(row["log10_min_cells"]), color=color, ls="--", lw=1)
        middle = (time >= 1200.) & (time <= 1400.)
        records.append(dict(case_id=row["case_id"], dispersal_yr=p.dispersal_yr,
            raw_file=str(payload.relative_to(ROOT)), raw_sha256=digest(payload),
            receipt_sha256=digest(receipt), loss_yr=loss,
            review_interval_yr=[1200., 1400.],
            mean_normalized_bulk_deficit=float(np.trapezoid(deficit[middle], time[middle])/200.),
            deficit_range=[float(min(deficit[middle])), float(max(deficit[middle]))],
            fraction_samples_deficit_below_point1=float(np.mean(deficit[middle] < .1)),
            no_dormancy_log10_minimum=float(row["log10_min_cells"]),
            dormancy_points=[dict(case_id=r["case_id"], epsilon=float(r["epsilon"]),
                first_log10_minimum=float(r["log10_min_cells"]),
                probability=float(r["survival_probability"]), classification=r["classification"])
                for r in chosen]))
    for epsilon, style in ((.01, ":"), (.03, "--"), (.1, "-.")):
        axes[0].axhline(epsilon, color=".4", ls=style, lw=1, label=f"Dormant loss fraction {epsilon:g}")
    axes[0].axhline(0., color=".7", lw=.6)
    axes[0].set(xlabel="Years after invasion", ylabel="Bulk active deficit (L − g) / L")
    axes[0].legend(frameon=False, fontsize=7)
    axes[1].set(xscale="log", xlabel="Dormant / active loss ratio epsilon",
                ylabel="Uncensored first minimum (log₁₀ cells)")
    axes[1].text(.03, .04, "Dashed: corresponding no-dormancy minimum", transform=axes[1].transAxes, fontsize=7)
    axes[1].legend(frameon=False, fontsize=7)
    for ax in axes:
        ax.grid(alpha=.15)
    fig.suptitle("A dormant compartment can die faster than mildly disadvantaged active cells")
    target = OUTPUT/"active_deficit.png"
    fig.savefig(target, dpi=170)
    plt.close(fig)
    result = dict(records=records,
        allocation_identity="At a fixed local environment, d(X+Z)/dt minus the all-active net rate is ((L-g)-epsilon*L)*Z; conversion cancels. Migration and changing environments require separate treatment.",
        interpretation="The instantaneous allocation condition epsilon < (L-g)/L explains the direction of a mortality cost. It is not a universal threshold for the coupled trajectory, and minima below one cell are continuum expectations.",
        source_sha256={str(Path(m.__file__).relative_to(ROOT)):digest(Path(m.__file__))
                       for m in (reference, habitat, reference.core)},
        inputs={str(p.relative_to(ROOT)):digest(p) for p in (table, scored_table)},
        checker_sha256=digest(Path(__file__)), figure_sha256=digest(target))
    HERE.joinpath("dormancy-deficit-check-2026-11-11.json").write_text(reference.dumps(result)+"\n")
    print(reference.dumps(records))


if __name__ == "__main__":
    main()
