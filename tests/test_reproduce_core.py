from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import pytest


SPEC = spec_from_file_location("reproduce_core_test", Path(__file__).resolve().parents[1] / "tools/reproduce_core.py")
CHECK = module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


def test_replay_cannot_overwrite_tracked_or_existing_outputs(tmp_path):
    root = tmp_path / "checkout"
    root.mkdir()
    for output in (root, root / "models/generated", root / "src/generated"):
        with pytest.raises(ValueError, match="outside the checkout"):
            CHECK.validate_output(root, output)
    CHECK.validate_output(root, root / "local/check")
    existing = tmp_path / "check"
    existing.mkdir()
    receipt = existing / "receipt.json"
    receipt.write_text("retained")
    with pytest.raises(ValueError, match="empty"):
        CHECK.validate_output(root, existing)
    assert receipt.read_text() == "retained"


def test_payload_verification_rejects_corruption_and_escape(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("original")
    row = {"path": "input.csv", "bytes": source.stat().st_size, "sha256": CHECK.digest(source)}
    manifest = tmp_path / "core_payload_manifest.json"
    manifest.write_text(json.dumps({"files": [row]}))
    assert CHECK.verify_payload(tmp_path)["verified_files"] == 1
    source.write_text("corrupt!")
    with pytest.raises(ValueError, match="checksum"):
        CHECK.verify_payload(tmp_path)
    row["path"] = "../outside"
    manifest.write_text(json.dumps({"files": [row]}))
    with pytest.raises(ValueError, match="Unsafe"):
        CHECK.verify_payload(tmp_path)


def test_scientific_comparison_preserves_counts_and_ignores_source_epoch_hashes():
    reference = {"count": 41, "temperature": 281.5348, "source_sha256": {"old.py": "old"}}
    actual = {"count": 41, "temperature": 281.534800001, "source_sha256": {"old.py": "new"}}
    assert CHECK.scientific_comparison(actual, reference) == []
    actual["count"] = 40
    assert CHECK.scientific_comparison(actual, reference) == ["/count: numerical difference"]


def test_legacy_auditor_write_is_redirected_without_changing_input_paths(tmp_path):
    root, output = tmp_path / "tree", tmp_path / "out"
    source = root / "models/haze_world/review/synthesis-core-audit-2026-11-11.py"
    source.parent.mkdir(parents=True)
    output.mkdir()
    source.write_text("from pathlib import Path\nHERE=Path(__file__).parent\ndef main():\n    HERE.joinpath('synthesis-core-audit-2026-11-11.json').write_text('{\"count\":41}')\n")
    original = source.with_suffix(".json")
    original.write_text('{"count":41}')
    before = original.read_bytes()
    result = CHECK.replay_audit(root, output, "core")
    assert result["status"] == "passed"
    assert original.read_bytes() == before
    assert (output / original.name).read_bytes() == before


def test_evolution_table_reassessment_preserves_committed_inputs(tmp_path):
    root = Path(__file__).resolve().parents[1]
    folder = root / "models/haze_world/figures/competitive_evolution"
    paths = list(folder.glob("*.csv")) + list(folder.glob("*.json")) + list(folder.glob("*.png"))
    before = {path: CHECK.digest(path) for path in paths}
    result = CHECK.reassess_evolution(root, tmp_path)
    assert result["status"] == "passed", result
    assert {path: CHECK.digest(path) for path in paths} == before
    assert (tmp_path / "evolution/prediction_assessment.json").exists()
