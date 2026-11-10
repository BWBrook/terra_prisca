"""Read qualified finite-run receipts without changing frozen batch identities.

uv run python -m terra_prisca.haze_world.finite_analysis [--extension-dir PATH]
"""

import argparse
import csv
from dataclasses import replace
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from .darwinian import Loss
from .finite_experiments import OUTPUT, RAW, clean, dumps, write_csv
from .methane_budget import Params
from .population_coupling import Coupled, fluxes
from .two_guilds import Competition

FUNCTIONAL_SHARE = .01
GROWTH_TOLERANCE_YR = 1e-4


def load_runs(directory, raw_dir):
    manifest_path = directory / "main_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    root = Path(__file__).resolve().parents[3]
    for name, expected in manifest["sources"].items():
        if sha256((root / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Frozen source no longer matches batch: {name}")
    result = []
    for entry in manifest["receipts"]:
        receipt_path = raw_dir / entry["raw_file"].replace(".json.gz", ".receipt.json")
        receipt = json.loads(receipt_path.read_text())
        data = raw_dir / entry["raw_file"]
        if (receipt["fingerprint"] != entry["fingerprint"] or
                sha256(data.read_bytes()).hexdigest() != entry["raw_sha256"]):
            raise RuntimeError(f"Qualified raw/receipt mismatch: {entry['case_id']}")
        result.append((receipt, data))
    return result, dict(file=manifest_path.name, sha256=sha256(manifest_path.read_bytes()).hexdigest(),
                        cases=len(result), source_sha256=manifest["sources"])


def key(summary):
    return tuple(summary[name] for name in ("activity", "fraction", "minimum_cells",
                                            "relative_immigration_yr", "direction", "census_yr"))


def choose_runs(original, extensions):
    selected = {key(receipt["summary"]): (receipt, data) for receipt, data in original}
    for receipt, data in extensions:
        k = key(receipt["summary"])
        if k not in selected:
            raise RuntimeError("Extension has no matching original protocol")
        current = selected[k][0]
        comparable = []
        for record in (current, receipt):
            protocol = dict(record["protocol"])
            protocol["case"] = {name: value for name, value in protocol["case"].items()
                                if name not in ("case_id", "years")}
            comparable.append(dumps(protocol))
        if comparable[0] != comparable[1]:
            raise RuntimeError("Extension changed more than the duration")
        if receipt["summary"]["years"] > current["summary"]["years"]:
            selected[k] = receipt, data
    return selected


def restore(parameters):
    values = dict(parameters)
    values["climate"] = Params(**values["climate"])
    values["biology"] = Competition(**values["biology"])
    values["loss"] = Loss(**values["loss"])
    values["enabled"] = tuple(values["enabled"])
    return Coupled(**values)


def functional_record(main_receipt, selected_receipt, data):
    row = dict(selected_receipt["summary"])
    with gzip.open(data, "rt") as handle:
        raw = json.load(handle)
    p = restore(selected_receipt["protocol"]["parameters"])
    times, states = np.asarray(raw["result"]["t"]), np.asarray(raw["result"]["y"])
    index = int(np.flatnonzero(times <= row["analysis_year"] + 1e-8)[-1])
    f = fluxes(states[:, index], p)
    uptake = np.asarray(f["catabolic_h2_mol_l_yr"])
    total = float(sum(uptake))
    shares = uptake / total if total > 0 else np.zeros(2)
    if total <= 0:
        role = "empty"
    elif shares[0] >= FUNCTIONAL_SHARE and shares[1] >= FUNCTIONAL_SHARE:
        role = "two_material_guilds"
    else:
        role = "acetogen_dominated" if shares[0] > shares[1] else "methanogen_dominated"
    row.update(base_case_id=main_receipt["summary"]["case_id"],
               base_horizon_yr=main_receipt["summary"]["years"],
               selected_case_id=selected_receipt["summary"]["case_id"],
               selected_horizon_yr=row["years"],
               selection_reason="later_qualified_extension" if row["years"] > main_receipt["summary"]["years"] else "original_horizon",
               selected_raw_sha256=selected_receipt["raw_sha256"],
               census_occupancy_label="both_retained" if row["occupancy"] == "both" else row["occupancy"],
               catabolic_share_a=float(shares[0]), catabolic_share_m=float(shares[1]),
               instantaneous_functional_role=role,
               attained_functional_role=role if row["settling_status"] == "census_stationary" else "unsettled")
    for i, suffix in enumerate(("a", "m")):
        growth = float(f["net_growth_yr"][i])
        present = row["cells_" + suffix] >= row["minimum_cells"] * (1 - 1e-10)
        row["without_import_growth_" + suffix] = ("shrinking" if growth < -GROWTH_TOLERANCE_YR else
                                                  "growing" if growth > GROWTH_TOLERANCE_YR else "near_balance")
        row["immigration_supported_sink_" + suffix] = bool(present and growth < -GROWTH_TOLERANCE_YR
            and selected_receipt["protocol"]["cell_process"]["immigration_cells_yr"][i] > 0)
    return clean(row)


def plot(rows, output, functional):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from matplotlib.patches import Patch
    labels = (("acetogen_dominated", "methanogen_dominated", "two_material_guilds", "empty", "unsettled")
              if functional else ("acetogen_only", "methanogen_only", "both_retained", "empty", "unsettled"))
    names = (("acetogens dominate", "methanogens dominate", "both ≥1% catabolism", "empty", "unsettled")
             if functional else ("acetogens only", "methanogens only", "both retained", "empty", "unsettled"))
    colors = ("#dc8f38", "#4679b4", "#3f8b60", "#dedede", "#8b7499")
    for direction in ("A_into_M", "M_into_A"):
        fig, axes = plt.subplots(2, 3, figsize=(10, 5), sharex=True, sharey=True, layout="constrained")
        for i, activity in enumerate(("fixed", "products")):
            for j, fraction in enumerate((0., .5, .9)):
                ax = axes[i, j]
                subset = [r for r in rows if r["direction"] == direction and r["activity"] == activity and r["fraction"] == fraction]
                matrix = np.empty((3, 4))
                for iy, floor in enumerate((1., 1e6, 1e12)):
                    for ix, immigration in enumerate((0., .1, 1., 100.)):
                        r = next(r for r in subset if r["minimum_cells"] == floor and r["relative_immigration_yr"] == immigration)
                        label = r["attained_functional_role"] if functional else (r["census_occupancy_label"] if r["settling_status"] == "census_stationary" else "unsettled")
                        matrix[iy, ix] = labels.index(label)
                        if r["immigration_supported_sink_a"] or r["immigration_supported_sink_m"]:
                            ax.text(ix, iy, "i", ha="center", va="center", fontsize=12, color="#111111")
                ax.imshow(matrix, origin="lower", aspect="auto", cmap=ListedColormap(colors), norm=BoundaryNorm(np.arange(6) - .5, 5))
                ax.set_xticks(range(4), ("0", "0.1", "1", "100"))
                ax.set_yticks(range(3), ("1", "10⁶", "10¹²"))
                ax.set_title(f"{activity} activities; f={fraction:g}", fontsize=10)
                if i == 1:
                    ax.set_xlabel("Mean immigration / floor (yr⁻¹)")
                if j == 0:
                    ax.set_ylabel("Removal floor (global cells)")
        fig.suptitle(("Functional contribution: " if functional else "Census occupancy: ") +
                     ("A introduced into M" if direction == "A_into_M" else "M introduced into A"))
        fig.legend(handles=[Patch(color=c, label=n) for c, n in zip(colors, names)], loc="outside lower center", ncol=3, frameon=False)
        fig.savefig(output / f"{'functional' if functional else 'retained'}_{direction}.png", dpi=145)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=OUTPUT)
    parser.add_argument("--raw-dir", type=Path, default=RAW)
    parser.add_argument("--extension-dir", type=Path)
    parser.add_argument("--extension-raw-dir", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    original, main_provenance = load_runs(args.input_dir, args.raw_dir)
    extensions = []
    extension_provenance = None
    if args.extension_dir:
        extensions, extension_provenance = load_runs(args.extension_dir, args.extension_raw_dir or args.raw_dir)
    selected = choose_runs(original, extensions)
    rows = [functional_record(receipt, *selected[key(receipt["summary"])]) for receipt, _ in original]
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "attained_endpoints.csv", rows)
    for functional in (False, True):
        plot(rows, args.output, functional)
    manifest = dict(main=main_provenance, extensions=extension_provenance, cases=len(rows),
                    later_horizon_selected=sum(r["selection_reason"] == "later_qualified_extension" for r in rows),
                    functional_fraction=FUNCTIONAL_SHARE, growth_tolerance_per_year=GROWTH_TOLERANCE_YR,
                    source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                    scope="Metabolic shares and actual biological net growth at qualified census endpoints; no autonomous coexistence claim from occupancy alone",
                    original_tables_preserved=True)
    (args.output / "analysis_manifest.json").write_text(dumps(manifest) + "\n")
    if any(p.stat().st_size >= 1_000_000 for p in args.output.iterdir()):
        raise RuntimeError("Public output exceeded1MB")
    print(dumps(manifest))


if __name__ == "__main__":
    main()
