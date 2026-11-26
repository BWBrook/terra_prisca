"""Check the growth-advantage wording against the 24 saved finite censuses.

Run with `uv run python docs/audits/haze-world-invasion-wording-2026-11-25.py`.
The native census archives listed in transient_archive_manifest.json are required.
"""

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "models/haze_world/figures/dynamic_realisation"


def main():
    manifest = json.loads((ARCHIVE / "transient_archive_manifest.json").read_text())
    digests = {entry["path"]: entry["sha256"] for entry in manifest["canonical_raw"]}
    with (ARCHIVE / "invasions.csv").open() as handle:
        runs = list(csv.DictReader(handle))

    runs_with_reversal = 0
    for run in runs:
        invader = {"A_into_M": 0, "M_into_A": 1}[run["direction"]]
        resident = 1 - invader
        (event,) = json.loads(run["census_events"])
        assert event["guild"] == resident
        path = ROOT / run["census_raw"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == run["census_sha256"] == digests[run["census_raw"]]

        with np.load(path) as data:
            time = data["t"]
            logs = data["log_biomass"]
            assert np.isfinite(logs[invader, -1]) and np.isneginf(logs[resident, -1])
            before_removal = time < event["time_yr"]
            t = time[before_removal]
            # A falling ratio means the resident grew faster over that interval.
            log_ratio = logs[invader, before_removal] - logs[resident, before_removal]
            changes = np.diff(log_ratio)
            reversals = np.flatnonzero(changes < 0)
            if reversals.size:
                runs_with_reversal += 1
                intervals = ", ".join(f"{t[i]:g}–{t[i + 1]:g}" for i in reversals)
                print(
                    f"{run['case_id']} had reversals over years {intervals}. "
                    f"Resident removed at {event['time_yr']:g} yr."
                )

    print(
        f"{len(runs)} invader-only endpoints. "
        f"{runs_with_reversal} runs had a growth reversal before removal."
    )


if __name__ == "__main__":
    main()
