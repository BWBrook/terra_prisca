"""Bounded haze-world checks; write every regenerated artifact outside tracked paths."""

from __future__ import annotations

import argparse
import contextlib
import csv
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import platform
import shutil
import sys
import traceback
from unittest.mock import patch


AUDITS = ("precursors", "core", "communities", "turnover")


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def validate_output(root: Path, output: Path) -> None:
    root, output = root.resolve(), output.resolve()
    if output == root or (root in output.parents and root / "local" not in output.parents):
        raise ValueError("Write outside the checkout, or beneath its ignored local/ directory")
    if output.exists() and any(output.iterdir()):
        raise ValueError("The output directory must be empty; prior checks are never overwritten")


def verify_payload(root: Path) -> dict | None:
    path = root / "core_payload_manifest.json"
    if not path.exists():
        return None
    manifest = json.loads(path.read_text())
    for row in manifest["files"]:
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe payload path")
        source = root / relative
        if source.stat().st_size != row["bytes"] or digest(source) != row["sha256"]:
            raise ValueError(f"Payload checksum failed: {relative}")
    return {"manifest_sha256": digest(path), "verified_files": len(manifest["files"])}


def scientific_comparison(actual, expected, path="") -> list[str]:
    ignored = {"checker_sha256", "source_sha256", "inputs", "inputs_sha256", "input_sha256"}
    if isinstance(actual, dict) and isinstance(expected, dict):
        return [issue for key in sorted(set(actual) | set(expected)) if key not in ignored
                for issue in scientific_comparison(actual.get(key), expected.get(key), f"{path}/{key}")]
    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            return [f"{path}: different list lengths"]
        return [issue for i, (a, b) in enumerate(zip(actual, expected))
                for issue in scientific_comparison(a, b, f"{path}/{i}")]
    if isinstance(actual, int) and isinstance(expected, int):
        return [] if actual == expected else [f"{path}: numerical difference"]
    if isinstance(actual, (int, float)) and not isinstance(actual, bool) and isinstance(expected, (int, float)):
        return [] if math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-8) else [f"{path}: numerical difference"]
    return [] if actual == expected else [f"{path}: different value"]


def replay_audit(root: Path, output: Path, label: str) -> dict:
    stem = f"synthesis-{label}-audit-2026-11-11"
    relative = f"models/haze_world/review/{stem}.py"
    source = root / relative
    row = {"audit": label, "script": relative, "script_sha256": digest(source)}
    with (output / f"{label}.log").open("w") as stream, contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        try:
            specification = importlib.util.spec_from_file_location(f"reproduce_core_{label}", source)
            module = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(module)
            module.ROOT = root
            if hasattr(module, "FIG"):
                module.FIG = root / "models/haze_world/figures"
            result_path = output / f"{stem}.json"
            expected_path = source.with_suffix(".json")
            original_write = Path.write_text

            def redirected_write(path, data, *args, **kwargs):
                if path.resolve() != expected_path.resolve():
                    raise RuntimeError(f"Auditor attempted an unregistered write: {path}")
                return original_write(result_path, data, *args, **kwargs)

            with patch.object(Path, "write_text", redirected_write):
                module.main()
            differences = scientific_comparison(json.loads(result_path.read_text()), json.loads(expected_path.read_text()))
            row.update(status="passed" if not differences else "different", scientific_differences=differences,
                       output_sha256=digest(result_path), reference_sha256=digest(expected_path))
        except FileNotFoundError as error:
            row.update(status="missing_data", message=str(error))
            traceback.print_exc()
        except Exception as error:
            row.update(status="failed", error=type(error).__name__, message=str(error))
            traceback.print_exc()
    return row


def fresh_prefix(root: Path, output: Path) -> dict:
    import numpy as np
    from terra_prisca.haze_world.finite_populations import CellProcess, integrate_finite
    from terra_prisca.haze_world.population_coupling import reference, temperature_k

    source = root / "models/haze_world/figures/finite_populations/c07_transient.csv"
    with source.open() as stream:
        rows = list(csv.DictReader(stream))
    columns = ["hydrogen_pa", "acetogens_gdw_l", "methanogens_gdw_l", "acetate_mol_l", "methane_ratio"]
    initial = np.array([float(rows[0][column]) for column in columns])
    parameters = reference()
    run = integrate_finite(initial, parameters, 30., CellProcess(), sample_every_censuses=1)
    maximum_error = np.zeros(5)
    samples = []
    for j, time in enumerate(run.t):
        expected_row = next(row for row in rows if float(row["time_yr"]) == time)
        expected = np.array([float(expected_row[column]) for column in columns])
        error = abs(run.y[:, j] - expected)
        maximum_error = np.maximum(maximum_error, error)
        if not np.allclose(run.y[:, j], expected, rtol=2e-4, atol=[1e-7, 1e-15, 1e-15, 1e-12, 1e-10]):
            raise AssertionError(f"Fresh C07 stock mismatch at {time} years")
        samples.append({"time_yr": float(time), "y": run.y[:, j].tolist(),
                        "temperature_k": float(temperature_k(run.y[-1, j], parameters.climate))})
    if run.first_extinction_by_guild_yr[1] != 20.:
        raise AssertionError("Fresh C07 methanogen removal did not occur at year 20")
    result = {"status": "passed", "input_sha256": digest(source), "samples": samples,
              "maximum_absolute_stock_errors": maximum_error.tolist(), "extinction_events": run.extinction_events,
              "scope": "Fresh 30-year model integration, not a rerun of the 100,000-year endpoint or a stochastic calculation."}
    (output / "c07_prefix.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def reassess_evolution(root: Path, output: Path) -> dict:
    from terra_prisca.haze_world import competitive_assessment as assessor

    source = root / "models/haze_world/figures/competitive_evolution"
    target = output / "evolution"
    target.mkdir()
    for name in ("best_response.csv", "anchors.csv", "communities.csv", "equilibria.csv", "invasions.csv",
                 "paths.csv", "adapted_single.csv", "best_response_manifest.json", "communities_manifest.json"):
        shutil.copyfile(source / name, target / name)
    previous_root, previous_output = assessor.ROOT, assessor.OUT
    assessor.ROOT, assessor.OUT = root, target
    record = {"audit": "evolution_tables", "scope": "L1 compact-table assessment and selected local derivative evaluation using current replay code; not independent mathematical review or historical producer regeneration. The accepted source-epoch check remains required for the separate math audit."}
    with (output / "evolution_tables.log").open("w") as stream, contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        try:
            assessor.main()
            actual = json.loads((target / "prediction_assessment.json").read_text())
            expected_path = source / "prediction_assessment.json"
            expected = json.loads(expected_path.read_text())
            for result in (actual, expected):
                result.pop("figure_sha256", None)
            differences = scientific_comparison(actual, expected)
            record.update(status="passed" if not differences else "different", scientific_differences=differences,
                          assessor_sha256=digest(Path(assessor.__file__)), reference_sha256=digest(expected_path),
                          output_sha256=digest(target / "prediction_assessment.json"))
        except Exception as error:
            record.update(status="failed", error=type(error).__name__, message=str(error))
            traceback.print_exc()
        finally:
            assessor.ROOT, assessor.OUT = previous_root, previous_output
    return record


def run(root: Path, output: Path, level: str) -> dict:
    root, output = root.resolve(), output.resolve()
    validate_output(root, output)
    payload = verify_payload(root)
    output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root / "src"))
    import numpy
    import scipy
    import terra_prisca
    source = Path(terra_prisca.__file__).resolve()
    if root / "src" not in source.parents:
        raise RuntimeError("Model imports do not resolve to the selected evidence tree")
    labels = () if level == "evolution" else AUDITS if level == "archive" else AUDITS[:2]
    audits = [replay_audit(root, output, label) for label in labels]
    if level == "evolution":
        audits.append(reassess_evolution(root, output))
    with (output / "c07_prefix.log").open("w") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        try:
            prefix = fresh_prefix(root, output)
        except Exception as error:
            prefix = {"status": "failed", "error": type(error).__name__, "message": str(error)}
            traceback.print_exc()
    result = {"level": level, "status": "passed" if all(row["status"] == "passed" for row in audits + [prefix]) else "incomplete_or_failed",
              "payload": payload, "audits": audits, "fresh_c07_prefix": {key: value for key, value in prefix.items() if key != "samples"},
              "environment": {"python": platform.python_version(), "numpy": numpy.__version__, "scipy": scipy.__version__},
              "model_source_sha256": {str(path.relative_to(root)): digest(path) for path in sorted((root / "src/terra_prisca").rglob("*.py"))},
              "scope": "Bounded algebra, frozen-output recounts, and one fresh short simulation. No long producer is started. Archive mode needs the curated raw companion. Comparisons omit provenance hashes and use relative 1e-6/absolute 1e-8 tolerance; each auditor also executes its original scientific assertions."}
    (output / "reproduction_receipt.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--level", choices=("compact", "archive", "evolution"), default="compact")
    args = parser.parse_args()
    result = run(args.root, args.output, args.level)
    print(json.dumps({"status": result["status"], "level": result["level"], "audits": [{"audit": row["audit"], "status": row["status"]} for row in result["audits"]], "fresh_c07_prefix": result["fresh_c07_prefix"]["status"]}, indent=2))
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
