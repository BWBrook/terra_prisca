# Applied Issue 2 changes: Codex review

Codex (GPT-6), 14 November 2026. Reviews `2e9c0c3` and pressure-test post
3428. An independent ledger/evidence check reran the three existing bounded
checks; I reviewed the applied prose, equation and tables. No producer grid
or new experimental stage was run. The adopted main message was not reopened.

**Decision:** accept the numerical findings, scientific reconciliation and
C62–C64 evidence. Add the two short scope qualifications below, with two
minor sampling-label clarifications. These are wording changes, not reasons
for more modelling or another numerical review cycle.

## What passes

- The three local/window/scope check scripts pass. Their output contents
  reproduce the committed receipts after excluding run metadata/timing.
  All 20 recorded input-hash entries match the current source files.
- The independent total-source elasticities, local warming derivatives and
  shared normalized gain match the new text. The ESM distinguishes this
  gain from the frozen-composition comparator and does not infer E from
  the identity being checked.
- Fixed-product pinning is explained by R-star equality; the singular
  closure and methane-feedback exception are stated separately. The latter
  is 1.9165e-4 K per K, appropriately rounded to 0.02% in the main text.
- The Kelvin feasibility interval, positive boundary biomasses, stable
  sampled interiors and nonsmooth-corner caveat are correctly separated.
  The margin changes and 0.14–8.3% graded range match the receipts.
- Case C's 1.26–7.20-year range is correct. Case D's absence is restricted
  to the extracted curve, with the assumed-bridge counterexample disclosed.
  The unsupported residual scaling with k has been removed.
- The Arney solar secant is kept only as a rough discussion scale, with the
  different background and spectrum/haze caveats. The abstract stays in
  Kelvin, the AR6 route and age/persistence extrapolation are absent, and
  the introduction calls the shift a controlled surrogate.
- C62–C64 values, evidence stamps and section links agree. The claims check
  reports **64 claims, 30 cited, zero errors and 29 uncited-claim warnings**.
  There is no stale-evidence warning for the new claims.

## Two scope qualifications

1. **Abstract, full draft lines 31–33.** Change "exact states held
   temperature" to **"fixed-product exact states held temperature"**.
   The main text and ESM already make this distinction, but the abstract
   otherwise appears to include the methane-feedback states just shown to
   move slightly. The range and adopted main message need no change.

2. **Equation (3.2), S12 and C62's limit.** State explicitly that the
   relation concerns the **cooling branch and a regular, locally
   single-valued fixed-temperature methane-source closure**. The ESM
   already lists linear removal and no direct methane-product dependence,
   and separately excludes singular fixed-product coexistence. Carry the
   cooling/regularity conditions into its opening sentence and C62's limit;
   identify the eligible graded states in the main-text lead-in.

   With k defined as an absolute climate slope, the displayed signs and
   denominator are not the warming-branch formula. Calling M(P,T) a function
   without the regularity qualification also leaves its applicability to
   exact coexistence unnecessarily ambiguous. A short lead-in is enough:
   "For regular graded states on the cooling branch, linearising the steady
   state gives ... (ESM)." Use the local k at the operating state.

These qualifications preserve the content Barry approved; they do not alter
the main message or reopen the sunlight-calibration decision.

## Two small sampling labels

- ESM line 378: there are **30 forcing values per recycling fraction**, or
  60 sampled states. Replace "all 30 sampled interior states" with "the
  30 sampled forcing values for each recycling fraction".
- Table S9's caption, line 385: say **"sampled margins"** stay within 7%.
  The main text's nearby statement should be understood with the same
  sampling qualification; no continuous interval proof was added.

The table's endpoint forcing labels are rounded coordinates of interior
samples, distinct from the exact corners discussed above it. The underlying
values and their interpretation otherwise pass.

## Verification and hand-off

The bounded commands are those already committed with the Issue 2 review:

```sh
uv run python docs/audits/probe-issue2-local-check-2026-11-14.py --output /tmp/terra-issue2-local.json
uv run python docs/audits/probe-issue2-window-check-2026-11-14.py --output /tmp/terra-issue2-window.json
uv run python docs/audits/probe-issue2-scope-check-2026-11-14.py --output /tmp/terra-issue2-scope.json
uv run python tools/claims.py check models/haze_world/synthesis/claims.csv models/haze_world/paper/03c-full-draft.md models/haze_world/paper/esm/esm.md
```

No manuscript, figure, production model or original receipt was edited in
this review. Claude can apply the short qualifications, update the C62
section-table rendering if needed, and close Issue 2. No new numerical
stage or change to the adopted main message is requested.
