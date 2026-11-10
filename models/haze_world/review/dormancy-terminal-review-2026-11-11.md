# Certified terminal-face dense budget

The separate terminal-face variant removes an interpolation bottleneck at the
recorded 2065-year state of case 0125. The frozen helper and 24 tests have passed
independent read-only review. The parent experiment's original-start full run
and complete producer reconciliation remain separate qualification gates.

The helper is `src/terra_prisca/haze_world/dormancy_terminal_integration.py`,
SHA-256
`8a6672dc11b5152da733f2a8d2a24393e297c5b45caf3aa340c2894ec98a33b4`.
Its flag is `radau_dormancy_terminal_dense_budget`. The exact source extension
has 15 files: the conditioned producer's 13 plus this helper and its separately
owned runner. The preceding helpers remain unchanged at `39024878…` and
`09be346c…`; their existing receipts retain their original numerical epochs.

The broader interpolation budget is
`min(original_component_atol, frozen_root_atol**2)`, with root absolute tolerance
10⁻¹². It applies only to a piece with all these properties:

- An **actual** one-cell census at ten-year intervals is active.
- Exactly one habitat is active and exactly one guild is present.
- All native start, end and polynomial-coefficient arrays are finite.
- A full-piece lower bound on the encoded guild total is at least −16.
- The model's exact habitat-volume and cell-mass conversion certifies at least
  10¹⁶ cells throughout the piece.

The encoded-total lower bound is the exact rational constant coefficient minus
the L1 norm of the remaining coefficients and the inherited outward evaluation
error margin. It includes the native endpoint anchor discrepancy. Large
endpoints alone are insufficient: the tests explicitly reject an interior total
dip below −16. For a qualifying bound, `softplus(z) >= 1/2**25` gives a
conservative biomass bound `SCALE/2**25`. Exact rational arithmetic then converts
that density to cells using the actual habitat volume, one habitat's weight and
census cell mass. The published event contains all bound coefficients, margins,
conversion factors and exact rational lower bounds.

Every ineligible piece invokes the original Radau dense constructor exactly.
That includes implicit `integrate(census=None)` runs, explicit uncensored
protocols, two-guild communities, multiple habitats and uncertified rare states.
Actual census presence is tracked separately because the older interpolation
utility supplies a default Census object even when a run has no actual census.

Only a private copy of the dense constructor's `_EPS` global changes, solely for
the cap computation. `_UNIT`, `_gamma`, normalizer certificates and all actual
roundoff bounds retain their original machine constants. Broader extension
metadata names `root_atol_squared_budget` and separately records the true
`machine_epsilon_squared`. No array is clipped, seeded or reset. The physical
RHS, error tolerances, native endpoint and domain-prefix checks, census,
inventory ledger and minimum algorithms remain unchanged. Every broader-budget
extension carries its gate proof; eligible pieces needing no extension contribute
only aggregate counts and conservative minima.

The 24 targeted tests pass in 1.19 seconds. They cover every gate exclusion,
exact original-constructor fallback, nonfinite arrays, conservative whole-piece
and volume bounds, unchanged source constants, native endpoints, census and
climate vertices, domain prefixes, contemporaneous combined minima, and strict
uncensored/rare paths. Independent review reran all 24 tests and reconstructed
20 additional polynomial cases: 12 certified and eight declined, with 257 exact
rational grid checks for each certificate.

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache \
MPLCONFIGDIR=/tmp/terra-prisca-mpl \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
uv run pytest -q tests/test_dormancy_terminal_integration.py
```

The final helper replayed the pinned state at 2065.124455 years for 100 years in
0.0818 seconds: 17 accepted pieces, 120 RHS evaluations, one Jacobian and one
backend construction. There were no resets, positivity refinements, declined
defects, native failures or negative native endpoints. All 17 pieces met the
gate. The minimum certified encoded-total bound was −0.145458615, with a
conservative cell lower bound of 4.5449 × 10¹⁸.

Two pieces used the broader budget. Their outward defect bounds were
1.6422 × 10⁻³¹ and 4.3411 × 10⁻²⁸, both below 10⁻²⁴. Their local normalized-curve
redistribution bounds were 0.0000501 and 0.132404 cells. The minimum certified
normalizer lower bound was 0.9999999999999615. The final physical stocks and
accepted work counts are bitwise identical to the preceding scratch control.
Temperature, hydrogen pressure and active acetogen biomass remain unchanged;
acetate changes by 2.17 × 10⁻¹⁹ M and the methane ratio by 3.20 × 10⁻¹⁷.

This is a pinned accepted-state diagnostic with exact saved charts and no
initial recensus, rather than a canonical full-horizon receipt. Its certificate
bounds the local declared interpolation curve. It establishes neither an
exact-flow or global-trajectory error bound nor rare-lineage or extinction-
probability accuracy. A macroscopic single guild avoids a census occupancy
ambiguity here; dormant-stage numbers are not separately certified.

The [review receipt](dormancy-terminal-review-2026-11-11.json) records source,
input, raw, controller and independent-review hashes, the exact protocol,
certificates and work counters. Raw controls are in the ignored
`local/haze/dormancy_terminal_review/`. The ignored controller
`local/haze/dormancy_trial_review/production_terminal0125_probe.py` accepts a
fresh `--output-dir` and refuses to overwrite an existing receipt.
