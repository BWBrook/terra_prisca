# Haze-world: bounded evidence reproduction

Stage A, 11 November 2026. These checks reproduce historical results under
their stated instantaneous-climate assumptions. External review withdrew
writing readiness; successful replay does not restore it.

## From Git alone

From the repository root, run:

```sh
uv sync --locked
uv run python tools/reproduce_core.py --level compact --output /tmp/terra-core-compact
```

The output directory must be empty. Every regenerated JSON and log goes there.
An output directory inside the checkout is allowed only beneath ignored
`local/`. No long trajectory producer starts. The command runs the precursor
and core synthesis auditors, then freshly integrates the first 30 years of
C07. That fresh integration checks methanogen removal at year 20 against the
committed transient export. It does not regenerate the 100,000-year endpoint.

The receipt records the interpreter and library versions, every current model
source hash, auditor/reference hashes, output hashes, scientific comparisons
and individual pass/failure statuses. Auditors retain their original assertions.
Their legacy writes are redirected to the named output directory; their input
paths remain unchanged. Missing data are reported as missing, never replaced
by compact summaries.

Scientific comparisons omit provenance-hash fields and use relative tolerance
`1e-6` and absolute tolerance `1e-8`; this only compares the old and recomputed
audit outputs. It does not change the assertions inside an auditor or qualify
the underlying model against observations.

## Curated raw companion

The prepared archive is under ignored
`local/haze/core-release/stage-a-final/haze-world-core.tar.gz`. It has **not been
deposited**: no DOI or stable download URL exists yet. A public Git clone can
run compact mode, but cannot run archive mode until this companion is made
available. The preparation closes the local packaging task; public raw-data
availability remains open.

The [preparation receipt](haze-world-core-receipt.json) pins the archive:
44,895,551 compressed bytes, 60,975,535 payload bytes, 579 files, including
92 raw/receipt objects. The compressed SHA-256 is
`f022d1e192f564fb318e879298cede6efc169a97cdcd655574d625c93a00881e`.
An empty-directory extraction passed all four auditors, evolution-table
assessment and the fresh C07 prefix; all 579 payload hashes remained unchanged
afterward. Five targeted tests cover output preservation, tamper rejection
and the safe assessment route.

The package contains:

- The complete focal C07 raw record.
- Three selected cubic switching-law records and their receipts.
- Three completed linear switching-law control records.
- The 41 raw/receipt pairs used in the independent dormant-bank forecast.
- The recorded bottleneck environment for the demographic-splitting check.
- Locked dependency files, required uptake/climate tables, compact evidence,
  audit scripts, current replay source, and frozen producer source epochs.

Restoration preserves each original repository-relative `local/` path. Source
epochs stay separate: current replay code is not substituted for the code
that generated historical trajectories. The eight source files named by the
competitive-evolution manifest are included exactly from `6ebb9eb`. The old
evolution auditor enforces those hashes; the Stage A precursor repair changes
one, so that historical auditor must run in its historical checkout. This
package does not waive its source check or requalify the evolution producer.

After obtaining the archive, extract it to an empty directory and use its
self-contained tree:

```sh
mkdir /tmp/terra-core-extracted
tar -xzf haze-world-core.tar.gz -C /tmp/terra-core-extracted
cd /tmp/terra-core-extracted/haze-world-core
uv sync --locked
uv run python tools/reproduce_core.py --level archive --output /tmp/terra-core-archive-check
```

Archive mode adds the communities and turnover auditors. It verifies every
payload object's size and SHA-256 before importing the selected source tree.
The import origin is checked; an installed copy elsewhere cannot silently
supply the model. The outer receipt pins the compressed archive, and the
inner manifest pins all payload files except itself. Code is MIT; original
text and simulation data are CC BY-SA 4.0. Source PDFs, article text,
correspondence and infrastructure records are excluded.

To prepare a fresh package from the owning checkout, without overwriting one:

```sh
uv run python tools/package_haze_core.py --output local/haze/core-release/new-preparation
```

The builder verifies selected historical raw hashes and receipts before
copying them. It retains accepted parent-archive manifest hashes, the current
Git commit, and exact packaged source hashes. If the working tree differs
from the commit, the file hashes describe the package. The package is a
reviewable preparation; this command neither uploads nor publishes it.

## Reproduction levels for the ledger

| Claims | Bounded route | What is recomputed |
|---|---|---|
| C01–C04 | Compact, precursor auditor | Closed-form roots, derivatives and committed-table recounts |
| C05–C11 | Archive, communities auditor | Independent resource/climate algebra and spectra, compact refuge/bottleneck recounts, focal C07 raw chronology |
| C12–C15, C21–C23 | Archive, turnover auditor | Turnover boundaries, refuge flux diagnostics, selected cycle records and 41 frozen-bank forecasts |
| C16–C20, C24 | Compact, core auditor | Branching identity, stored first-window summaries, seed-bank arithmetic, local modes and repeated-cycle counterexample |
| C25–C28 | Historical superseded/refuted records | Retain the failed claims; use the cited replacement/control evidence rather than interpreting them as current predictions |
| C29–C37 | Evolution mode; separate historical audit | Compact table assessment and selected derivative evaluation. The independent math audit requires its accepted source epoch; it is outside `reproduce_core` |

These are algebra/recount and selected-raw replay levels, not full model
regeneration. Most trajectories in the larger research archive are omitted.
Recounting every compact row does not validate every omitted trajectory from
raw states. Full long-run regeneration still requires the original producer
protocols, their frozen source/dependency epochs, and explicit compute time.

The evolution table check also runs from Git alone:

```sh
uv run python tools/reproduce_core.py --level evolution --output /tmp/terra-evolution-tables
```

It copies the assessment inputs into the output directory before running the
assessor there. Scientific comparisons exclude figure hashes because rendering
can vary by platform. This is an L1 assessment with current code, not an
independent replay of the evolutionary producer or its source-epoch audit.

The legacy commands that directly run
`synthesis-*-audit-2026-11-11.py` overwrite their adjacent committed JSON on
success. Use this wrapper for review. The evolution assessment module also
writes its assessment and figures; its existing command is a producer, not a
non-mutating check.
