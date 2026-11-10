# Zero linear allocations in the Newton matrix

Codex, 11 November 2026. The named numerical variant is
[`dormancy_face_integration.py`](../../../src/terra_prisca/haze_world/dormancy_face_integration.py),
SHA256 `6a758528247493428459d250a0cd000ae678c9e59c05a09947f94628ed1672ce`.
It changes an approximate Newton matrix, leaving the exact frozen RHS,
physical stocks, coordinate charts, census rules and tolerances unchanged.

## Observed scaling failure

The stage variant passed case 0085's earlier allocation singularity, but a
bounded Linux census run advanced only about one year during its last
80 seconds near year 2241. The [saved accepted state](dormancy_2241_regression.json)
has a finite RHS and matrix. Its largest matrix entry is nevertheless
`6.39e184`: a zero warm linear active-acetogen allocation couples into a very
small retained bulk root. The chemical row has a derivative of `6.59e81`
with respect to that same zero linear allocation. The two chemical pools are
`2.61e-119` and `1.27e-109 mol/L`, with accepted log-coordinate rates exactly
−1. Replaying the saved state reproduces disposable acetate-source overflow
trials and repeated rollback/refinement. Both BDF and Radau also fail to
advance a 0.1-year phase with those same coordinates and tolerances; that is
a bounded diagnostic, not a general comparison of the solvers.

The warm linear population's **returned floating-point rate is zero**, while
its retained incoming log source is **−897.846**. The latter is below floating
range. Thus this is not an algebraically source-free population, an extinction
criterion, or a proof that a mathematical invariant face exists.

## Approximate Newton matrix

At each matrix evaluation the helper selects a stage only when its guild is
present, its allocation uses the linear chart, its coordinate equals zero
exactly and its unchanged returned floating-point allocation RHS equals zero
exactly. It zeros that stage's Newton row and column couplings and retains
its original own diagonal. There is no numerical threshold or `isclose` test.
Any positive coordinate or representable positive source prevents selection.
Couplings incident to another selected zero stage can still be removed.

The gate evaluates the frozen linear-allocation algebra from decoded stocks
and pure fluxes. It does not call the coordinate derivative, which could
consume a pending accepted-state chemical-chart request. State vectors,
chart flags, pending requests and all physical equations remain untouched.
Statistics count matrix evaluations and their trial times, not biological
removal or accepted-flow events. Retained incoming log sources are reported.

The helper privately composes the frozen stage driver and its existing
chemical and progress handling. It adds no accepted-driver copy, clipping,
seed, physical source removal, census modification or tolerance change.
Inherited stage-underflow limitations remain explicit in the upstream driver.

## Bounded qualification

All **12 focused tests pass**. They cover the actual saved state, subnormal
positive sources, positive coordinates down to the smallest floating value,
per-evaluation source restoration, unchanged pending requests/stocks/charts,
a genuine later waking source, nongated bitwise flow, physical-Radau precision,
population minima, nonzero censuses and zero switching.

The saved-state scratch control advances **0.1 yr in 0.099 s**, using 38 accepted
steps and 65 RHS evaluations, with nonnegative accepted dense flow and no acetate
overflow. An initially absent active population later grows to
`5.88e-5 gDW/L` when hydrogen changes; that entry control agrees bitwise with
the upstream physical trajectory over 0.01 yr. At a representable waking
source, the stage is not selected for the approximation.

Independent read-only review reran all 12 tests against the final source and
found no consequential blocker. It verified the gate arithmetic and operation
order against the frozen RHS, request/state preservation, source restoration
and unchanged accepted-driver accounting.

The original-start **case-0085 census control completes 3,000 yr in 96.89 s**
with 15,599 accepted pieces and 30,487 RHS evaluations. Its fingerprint is
`3d581d3e2ae5109952681ce5954f58fb00d976ddebc10f7a7cd93ca4bc5b8d96`.
Stocks remain finite and nonnegative, dense minima bound the samples and the
sampled redox residual is at most `2.61e-18`. One acetate overflow/refinement
is retained, with no positivity refinements or zero-time restarts. The last
acetogen census removal occurs at **year 2270**, after the former stall near
2241; the 3,000-year state has only methanogens and retains its `pilot_only`
label. It is not yet a settled climate endpoint.

Across 225 shared accepted sample times through year 2240, the new Mac control
and the earlier valid Linux stage partial differ by at most `1.50e-5 K` in
temperature and `2.25e-10 gDW/L` in biomass. Their numerical step sequences and
retained subfloat stages are not asserted equal. The
[qualification JSON](dormancy-face-qualification-2026-11-11.json) records these
comparisons and all source, protocol, payload, receipt and controller hashes.

The full 100,000-year control remains pending. These completed bounded checks
do not establish an ecological endpoint or completion of the experimental
grid.

```sh
uv run pytest -q tests/test_dormancy_face_integration.py
```
