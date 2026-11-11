"""Prepare the owned, decision-relevant haze-world replay payload; never upload it."""

from __future__ import annotations

import argparse
from hashlib import sha256
import gzip
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[1]
AUDITS = ("precursors", "core", "communities", "turnover")


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def raw_selection(root: Path) -> dict[str, str]:
    selected = {"local/haze/finite_populations/final_raw/main_0024_t100000-ce9c0899cdf042d0.json.gz": "C07 first extinction and full focal record"}
    review = root / "models/haze_world/review"
    for case in ("0024", "0126", "0012"):
        name = "dormancy0012_cycle_check.json" if case == "0012" else f"dormancy126_cycle_{case}.json"
        summary = json.loads((review / name).read_text())
        receipt_path = summary.get("full_receipt", summary.get("full_receipt_file"))
        receipt = json.loads((root / receipt_path).read_text())
        if digest(root / receipt_path) != summary["full_receipt_sha256"]:
            raise ValueError(f"Receipt identity failed: {receipt_path}")
        if digest(root / receipt["raw_file"]) != receipt["raw_sha256"]:
            raise ValueError(f"Raw identity failed: {receipt['raw_file']}")
        selected[receipt_path] = selected[receipt["raw_file"]] = f"C21 cubic finite-record control {case}"
    closure = json.loads((review / "cycle-closure-results-2026-11-11.json").read_text())
    for row in closure["linear"]:
        if row["status"] == "completed" and row["actual_horizon_yr"] >= 20000:
            path = row["raw_file"]
            if digest(root / path) != row["raw_sha256"]:
                raise ValueError(f"Linear control identity failed: {path}")
            selected[path] = "C22 completed linear switching-law control"
            receipt = (root / path).with_suffix(".receipt.json")
            if receipt.exists():
                selected[str(receipt.relative_to(root))] = "C22 linear control receipt"
    assessment = json.loads((review / "dormancy-tail-assessment-2026-11-11.json").read_text())
    for row in assessment["rows"]:
        if row["additional_class"] != "macro_stationary_bank_unresolved":
            continue
        path = "local/haze/dormancy/" + row["raw_file"]
        if digest(root / path) != row["raw_sha256"]:
            raise ValueError(f"Dormant-tail identity failed: {path}")
        selected[path] = "C23 independent frozen-bank forecast"
        receipt = next(r["receipt_file"] for r in assessment["selected_receipts"] if r["case_id"] == row["case_id"])
        selected["local/haze/dormancy/" + receipt] = "C23 selected-case receipt"
    return selected


def tracked_selection(root: Path) -> dict[str, str]:
    paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    selected = {}
    review_names = {f"synthesis-{label}-audit-2026-11-11{suffix}" for label in AUDITS for suffix in (".py", ".json")}
    review_names |= {"check_turnover_gaussian.json", "cycle-closure-results-2026-11-11.json",
                     "dormancy0012_cycle_check.json", "dormancy126_cycle_0024.json", "dormancy126_cycle_0126.json",
                     "dormancy-tail-assessment-2026-11-11.json", "competitive-evolution-math-review-2026-11-11.py",
                     "competitive-evolution-math-review-2026-11-11.json", "competitive_evolution_preview.py"}
    for name in paths:
        path = Path(name)
        if not name:
            continue
        if ((name.startswith("src/terra_prisca/") and path.suffix == ".py")
                or (name.startswith(("models/haze_world/figures/", "models/haze_world/evidence/", "models/haze_response/")) and path.suffix in (".json", ".csv"))
                or (name.startswith("models/haze_world/review/") and path.name in review_names)
                or name in {"pyproject.toml", "uv.lock", "LICENSE", "LICENSE-CONTENT", "models/haze_world/competitive-evolution-spec.md",
                            "models/haze_world/figures/bottleneck/main_0010_environment.npz"}):
            selected[name] = "Current source or committed compact evidence"
    selected["tools/reproduce_core.py"] = "Non-mutating bounded reproduction entry point"
    selected["tools/package_haze_core.py"] = "Preparation script from the owning checkout; no upload or publication"
    for path in (root / "src/terra_prisca").rglob("*.py"):
        selected[str(path.relative_to(root))] = "Current replay source, including Stage A repairs"
    for path in (root / "docs/audits").glob("external-review-*-2026-11-11.*"):
        if path.suffix in {".py", ".json", ".md"}:
            selected[str(path.relative_to(root))] = "Independent external-review finding check; outside the four legacy replay auditors"
    return selected


def build(root: Path, output: Path) -> dict:
    root, output = root.resolve(), output.resolve()
    allowed = root / "local/haze/core-release"
    if output != allowed and allowed not in output.parents:
        raise ValueError("Stage packages beneath ignored local/haze/core-release/")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Choose a fresh output directory; existing packages are preserved")
    payload = output / "haze-world-core"
    payload.mkdir(parents=True)
    selected = tracked_selection(root) | raw_selection(root)
    entries = []
    for relative, purpose in sorted(selected.items()):
        source, target = root / relative, payload / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        entries.append({"path": relative, "bytes": source.stat().st_size, "sha256": digest(source), "purpose": purpose})
    archives = ("turnover-dormancy-archive", "dormancy-closure-archive")
    producer_manifests = {}
    for archive in archives:
        base = root / "local/haze" / archive
        manifest = base / "archive_manifest.json"
        producer_manifests[archive] = digest(manifest)
        for source in sorted(base.rglob("*.py")):
            relative = source.relative_to(base)
            if not any(part in ("source", "source_epochs") for part in relative.parts):
                continue
            dest_relative = Path("producer_epochs") / archive / relative
            target = payload / dest_relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            entries.append({"path": str(dest_relative), "bytes": source.stat().st_size, "sha256": digest(source),
                            "purpose": "Frozen producer source, retained separately from current replay code"})
    evolution = json.loads((root / "models/haze_world/figures/competitive_evolution/communities_manifest.json").read_text())
    for name, expected in evolution["source_sha256"].items():
        data = subprocess.check_output(["git", "show", f"6ebb9eb:{name}"], cwd=root)
        if sha256(data).hexdigest() != expected:
            raise ValueError(f"Evolution producer epoch does not match its accepted manifest: {name}")
        relative = Path("producer_epochs/competitive_evolution_6ebb9eb") / name
        target = payload / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append({"path": str(relative), "bytes": len(data), "sha256": expected,
                        "purpose": "Exact manifest-named source from accepted competitive-evolution producer commit 6ebb9eb"})
    readme = """Haze-world bounded evidence replay payload, Stage A, 11 November 2026

This preparation is not a Zenodo deposit or a scientific release. No DOI is
assigned. The source and model-conditional historical evidence are retained
despite the external review's withdrawal of physical writing readiness.

The tree is self-contained for the four short synthesis auditors and a fresh
30-year C07 prefix. Run with the locked project environment:
  uv sync --locked
  uv run python tools/reproduce_core.py --level archive --output /tmp/haze-core-check
  uv run python tools/reproduce_core.py --level evolution --output /tmp/haze-evolution-tables
All regenerated files go to the named EMPTY output directory. No long
trajectory producer runs. Its JSON receipt reports assertions, comparisons,
environment and every replay status. Output evidence is never overwritten.
Evolution mode only reassesses compact tables and selected local derivatives;
it does not execute the separate historical-source independent math auditor.

Every local/ path is restored at its original repository-relative location.
The same tree can be overlaid onto the matching checkout. This includes the
full focal C07 record, three selected cubic-cycle records, three completed
linear controls, and the 41 raw/receipt pairs used by the frozen-bank audit.
producer_epochs/ holds frozen source copies. Current src/ is the replay
implementation, not a claim that old records were generated with current code.
The eight manifest-named competitive-evolution source files are retained from
6ebb9eb. Its independent math auditor is NOT part of this replay: Stage A's
precursor repair changes a source hash that auditor deliberately enforces.
Replaying that historical auditor requires the matching historical checkout;
the source check is not waived or silently redirected to another epoch.

core_payload_manifest.json pins bytes and hashes, current commit and parent
archive manifests; its file list excludes itself. The companion outer receipt
pins the compressed archive. Validate all listed hashes before replay.

Scope: historical instantaneous-climate, fixed assumptions. The replay does
not establish realistic thermal stability, a limit cycle, joint stochastic
survival, or full long-run regeneration. Most trajectories in the 700 MB
research archive are deliberately excluded. Recounting all compact rows does
not validate every omitted trajectory from raw states.

Code: MIT (LICENSE). Original text and simulation data: CC BY-SA 4.0
(LICENSE-CONTENT). Digitised Arney values are factual model outputs; cite
Arney et al. (2016), DOI 10.1089/ast.2015.1422. No publisher PDF, third-party
article text, correspondence, infrastructure record or credentials included.
"""
    (payload / "README.txt").write_text(readme)
    entries.append({"path": "README.txt", "bytes": (payload / "README.txt").stat().st_size,
                    "sha256": digest(payload / "README.txt"), "purpose": "Restoration, provenance, scope and licensing"})
    entries.sort(key=lambda row: row["path"])
    manifest = {"schema": "terra-prisca-haze-core-v1", "files": entries,
                "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                "source_identity": "The manifest's exact file hashes control the packaged tree; current working-tree source may differ from the commit during Stage A preparation.",
                "parent_archive_manifests_sha256": producer_manifests,
                "licenses": {"code": "MIT", "original_text_and_simulation_data": "CC-BY-SA-4.0"},
                "scope": "Curated historical raw evidence and bounded replays, prepared for review before a Zenodo deposit."}
    (payload / "core_payload_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    archive_path = output / "haze-world-core.tar.gz"
    with archive_path.open("wb") as stream, gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as compressed, tarfile.open(fileobj=compressed, mode="w") as tar:
        for source in sorted(payload.rglob("*")):
            if source.is_file():
                data = source.read_bytes()
                info = tarfile.TarInfo(str(Path("haze-world-core") / source.relative_to(payload)))
                info.size, info.mtime, info.mode = len(data), 0, 0o644
                tar.addfile(info, io.BytesIO(data))
    receipt = {"schema": "terra-prisca-haze-core-receipt-v1", "archive": archive_path.name,
               "archive_bytes": archive_path.stat().st_size, "archive_sha256": digest(archive_path),
               "manifest_sha256": digest(payload / "core_payload_manifest.json"), "files": len(entries),
               "payload_bytes_excluding_manifest": sum(row["bytes"] for row in entries),
               "raw_files": sum(row["path"].startswith("local/") for row in entries),
               "source_commit": manifest["source_commit"], "deposited": False, "doi": None}
    (output / "payload_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(ROOT, args.output), indent=2))


if __name__ == "__main__":
    main()
