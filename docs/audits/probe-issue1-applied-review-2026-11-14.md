# Applied Issue 1 changes: Codex review

Codex (GPT-6), 14 November 2026. Reviews `9e2977f`, `9e5d881` and
`7318f4c`, following pressure-test post 3385. Two independent checks covered
the figure/export and numerical/ledger provenance; I reviewed the new prose,
equation and rendered figure. The adopted main message was not reconsidered.

**Decision:** accept Figure 3b, the finite-response numbers and the reporting
repair. A few scope statements and C60's evidence stamp still need correction
before closing Issue 1. No new experiment is needed. This review changes no
manuscript, figure, ledger, production model or original evidence file.

## What passes

- All 150 exported Figure 3b rows match the selected source rows, including
  eight open endpoint markers. The shaded supply interval is correct; the
  partial sigma=6/8 branches are visibly partial. There is no M-only overlay
  or proposed planetary placement. The PDF was rendered and inspected, and
  the PNG was checked independently.
- The fixed-interval spans are 1.911145634 K and 5.408743251 K for sigma=1
  and 3 K. Their sampled finite-margin minima are 833.198941 and 3506.487177
  years, supporting the text's 830/3500 lower bounds. Each has four accepted
  lag samples; sigma=3/P=0.24 remains right-censored at 10,000 years.
- The two 30-year spread brackets are 0.023591252–0.023999710 K and
  0.057952286–0.058499959 K. The 0.02–0.06 K annotation and Figure 3a/b
  correspondence at sigma=1/P=0.30 are correct.
- The metadata repair preserves all physical rows, lag records, summaries
  and homogeneous comparator values. Only `branch_ends` changed. All eight
  stops now agree with the last accepted bisection progress. `failed_target`
  is still the outer requested step, not a located boundary bracket.
- The adopted message is present in the closing paragraph and Step 1
  records. Habitat timescale pairings and the claimed surface/deep planetary
  locations were removed. C61's qualified numerical findings pass review.

## Corrections needed

### 1. The abstract still confuses threshold widths with whole branches

At full-draft lines 28–30, "which on these branches was a few hundredths of
a kelvin" reads as a description of the tested habitat spreads. D2 runs
from sigma=0 to 1 K; only the **30-year threshold** is at a few hundredths.
The preceding "four tested branches" also includes two acetate branches,
which do not vary habitat spread.

Tie the number to its estimand: for example, "On the two habitat-spread
branches, the 30-year margin was reached at half-widths of 0.02–0.06 K;
with weak exchange, sensitivity grows with habitat spread." Results and
the Figure 3 annotation already make the right distinction.

### 2. Faster exchange does not always lower sensitivity

Full-draft lines 373–374 and C60's ledger limit say faster exchange lowers
|S| below the relation. The stored data contain a counterexample at f=0,
P=0.24, sigma=3 K:

| Exchange/year | Sensitivity magnitude (K per e-fold) |
|---:|---:|
| 0.0001 | 5.724615 |
| 0.001 | 5.723265 |
| 0.01 | 5.743099 |
| 0.1 | 5.889504 |

The approximation predicts 5.505304 throughout. At d=0.1 the ratio is
1.069787, rather than below one. The all-state maximum in C60's own value
already records this. Stronger mixing **can** lower sensitivity substantially;
it does not invariably do so. Use that conditional wording in the main
text and ledger, and show both ends of the strong-mixing comparison where
needed: 0.705–1.070 at d=0.1.

### 3. Name the near-reference approximation in equations 3.1/S11

The reduced uniform closure before the reference approximation has

`|S_geo| = 2*sigma*(r/r_star)*(P_lo/P)*Q/(Q-1)`.

The displayed form drops `r/r_star` and fixes k at the reference methane
ratio. ESM line 207 calls the result an identity without explicitly naming
that approximation. State **r approximately r_star**, call the displayed
relation a near-reference weak-mixing approximation, and retain the outlet/
endpoint-Q caveat. The observed agreement within roughly 6% is supported;
an exact production-model or finite-branch identity is not. This was already
specified in the earlier review and does not require a new derivation or run.

### 4. Keep the interpretation conditional outside the measured examples

The new discussion is improved, but two sentences still imply a broader
result than the examples establish:

- Lines 425–426 say a community holds temperature "within its habitat
  spread" whenever habitats differ. Describe the computed weakly connected
  branches instead: they traverse approximately T_star +/- sigma. This is
  not a general bound for other connectivity, distributions or chemistry.
- Lines 448–455 move from environmental contrasts directly to a
  "correspondingly larger residual sensitivity." Those source contrasts
  set an illustrative scale; inferring a sensitivity additionally requires
  that they describe active, resource-fed habitats with the assumed
  distribution and coupling. Make that condition explicit rather than
  suggesting the full environmental range already supplies it.

These qualifications preserve Barry's adopted directional message and the
intended contrast between narrow test cases and an uncalibrated planet.

### 5. Two small bounds need their scope or precision corrected

- Conditions lines 486–487: the roughly 8-K limit applies **around the
  reference temperature**, not to all possible model states. The actual
  condition is `[T-sigma,T+sigma]` inside `[273,303.15]` K. For example,
  T=285 K and sigma=10 K satisfy it. Name the reference-state scope.
- ESM line 209 says both wide branches end within 0.03 K of the 273-K floor.
  The sigma=8 cold edge is 273.03231668 K. Use "within 0.04 K" or report
  the individual gaps. This does not affect any finite span or lag result.

### 6. C60 has a stale evidence stamp

The claims command returns zero errors, but also warns:

`C60: evidence changed since 9e2977f; reverify, then stamp`.

C60 cites the reconciliation document, which changed in `7318f4c`. Reverify
the corrected scope, stamp C60 against its current evidence, and regenerate
the S9 stamp. The remaining warnings concern claims outside the selected
paper/ESM documents. C61 has no corresponding stale-evidence warning.

The old independent receipt is correctly historical: its JSON/script input
hashes match the pre-metadata-fix versions. Preserve it. Its physical findings
remain valid because those sections are unchanged; its eight recorded stop
mismatches describe the earlier defect, not the current artifact.

## Checks and hand-off

A fresh compact recount with the existing independent script is saved as
`probe-issue1-applied-check-2026-11-14.json`. It records current source hashes
and **zero** stop-metadata mismatches, while preserving the earlier receipt:

```sh
uv run python docs/audits/probe-issue1-codex-check-2026-11-14.py --output /tmp/terra-issue1-applied.json
```

Additional bounded checks compared the exported rows, threshold brackets,
physical JSON sections across commits, sampled lag records and the evidence
stamps. The main/ESM claims check reports 61 claims, 27 cited, zero errors
and 30 warnings, including the actionable C60 warning above. No equilibrium,
transient or lag sweep, full figure rebuild, or general test suite was rerun.

Claude should make these limited corrections and reconcile them. No change
to the adopted main message, Figure 3b or numerical conclusions is requested.
Issue 2 remains outside this review.
