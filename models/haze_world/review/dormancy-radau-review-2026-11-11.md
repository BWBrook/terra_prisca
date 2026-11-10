# Radau and a bounded positive dense extension

Codex, 11 November 2026. The separately named numerical helper is
[`dormancy_radau_integration.py`](../../../src/terra_prisca/haze_world/dormancy_radau_integration.py),
SHA256 `09be346c90c0fcb65ed6409f2de47ea1e4d3e2d542f3d6291eb7ae85a0bf6d2b`.
The [qualification record](dormancy-radau-qualification-2026-11-11.json)
records its tests, independent review, completed bounded timing control and
ordinary native-solver failure. The older physical and numerical sources are
unchanged.

## Numerical method

The maintained SciPy Radau backend reuses the frozen accepted-step driver,
physical RHS, charts, census, positivity checks and tolerances. Backend
initialization is deferred until `step()`, placing constructor Jacobian
conditioning requests inside the existing accepted-state handler. Native
failures never adopt trial coordinates. Counters retain failed RHS work and
separately count constructor Jacobian attempts and failures.

A Radau cubic can have a tiny negative allocation between nonnegative native
endpoints. Only a **present linear allocation** can replace that cubic by its
native-endpoint chord. Root charts, absent groups, chemicals and other fields
cannot receive this extension. Exact-rational coefficient arithmetic and
outward rounding certify an interpolation difference no larger than the
smaller of the original component tolerance and machine epsilon squared
(`4.93e-32` in normalized allocation). Native negative constrained endpoints
remain rejected. An endpoint beyond an earlier valid domain exit does not
invalidate that truncated flow.

Allocation-normalizer bounds use component norms before cancellation and
include construction/evaluation rounding. Each extension archives its native
Q, old/end arrays, exact normalizer and difference coefficients, component
tolerance and bound inputs for read-only reconstruction. One cached extension
serves calls, polynomial metadata, minima and censuses; barycentric and power
representations agree up to the stated rounding bounds.

Native endpoint arrays remain unchanged for each fixed piece. An interior
census can restart the solver from the new interpolation, so later trajectory
endpoints need not be identical. The local cell-redistribution certificate
concerns normalized represented curves in real arithmetic. It does not bound
ordinary decoded-float rounding, exact-ODE error, accumulated trajectory
error, lineage survival or log probability. Those quantities still require
trajectory controls. No stock clipping, population seed or physical floor is
introduced.

## Verification

All **23 focused tests pass**. They cover reconstructible certificates,
large-defect refusal, all constrained native endpoint classes, absent/root/
chemical exclusions, domain truncation, climate vertices, native failure and
constructor-Jacobian accounting, census-interior restart, rare retained logs,
shared-habitat minima and independent physical-Radau agreement. Independent
read-only review reran those tests and reconstructed the recorded exact
normalizer/difference inputs without finding a consequential blocker within
this scope.

The production helper advances the exact saved case-0125 state from year
36,731.522 through another **100 years in 14.94 s**, using 1,434 accepted
pieces. It constructs one extension with defect bound `1.05e-48`, positive
normalizer lower bound `0.9999999999999615` and local cell-curve redistribution
bound `3.19e-22`. One larger-defect cubic is refused and refined by the old
driver. There are no negative native endpoints. Full certificate inputs,
source hashes and native work counters are retained in the ignored control
archive named by the JSON.

The cost of that steady-state replay is primarily native Newton convergence:
a read-only profile reproduces its final state and counts bitwise, records
4,925 collocation nonconvergences and zero error-estimate rejections, while the
accepted driver constructs only four backends. This is a measured numerical
cost, not evidence of physical change or a general solver speed comparison.

## Original-start limits

The original-start uncensored case 0000 completes 3,000 years with a valid
receipt. An original-start case **0010 fails near year 1399.07**, returning
Radau's required-step-size-below-spacing error. The generic worker retained
the failure log and ledger, but no fresh failed-state artifact; its detailed
cause is not established here. The qualified Face case-0010 record remains
canonical. The new variant contains no automatic fallback or relaxed guard.

The original-start case-0125 full census run is a separate control and remains
pending in this review. These bounded checks do not qualify every original
trajectory or establish completion of the experimental grid.

```sh
uv run pytest -q tests/test_dormancy_radau_integration.py
```
