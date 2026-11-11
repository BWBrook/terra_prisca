# B1/B4 build receipt and interpretation boundary

Codex (GPT-6), 12 November 2026. Design choices were frozen before decisive
runs in `db09eea`. The specification's PB1–PB7 predictions were not rewritten.
The [independent audit](dynamic-realisation-review-2026-11-12.md) and
[model page](../../models/haze_world/dynamic-realisation.md) give the scientific
results. This note records implementation qualification and the stopping point.

## Produced and checked

- B1: 108 parameter families, 1,080 resolution-settings, 795 accepted mixed-root
  records and 340 missing/unresolved rows. Multiple roots account for the
  difference between settings and output rows. Full-support physiological
  bounds are enforced; no habitat temperatures are clipped.
- Gain: 423 defined ratios, 276 records with no admissible control found,
  and 96 zero-control-slope cases. Missing controls are finite-search results,
  not certificates of physical absence. The separate inventory preserves
  actual roots, statuses and homogeneous-seed diagnostics.
- PB1: eighteen finite-resolution near-pinning/long-lag candidates, none
  passing the full convergence/control qualification. No universal frontier
  and no qualified continuum escape are established.
- B4: sixty-five spectral rows; two matched recorded-period comparisons,
  one failure. The warm-refuge comparison is explicitly geometry-unmatched.
- Full test suite: **877 passed** in 177.2 seconds. After the final assessment
  changes, **seven targeted tests** passed. These checks cover the actual
  per-capita equations, analytical/physical matrix identities, undefined
  controls, right-censoring and directional dormancy derivatives.
- Source and output hashes were checked for both producers, the assessment,
  and the independent audit. The frontier figure was inspected after rendering.

No historical model equations were changed; all B1/B4 code is in named variant
modules. No nonlinear B2/B3 trajectories, new evolutionary runs, demographic
simulations, public deposit or manuscript product were created.

## A failed numerical check was repaired before accepting the map

The first B1 map included twelve numerically vanishing false guild records.
Its positive-coordinate solver normalised residuals using a denominator floor.
An almost-zero biomass could therefore satisfy an absolute-flow tolerance
without satisfying its growth equation. In the focal products/f=0/L=.002/hour/
potential .36/σ=3/N=9 example, the false 283.20 K state had mean methanogens
about 1.5e-32 gDW/L but a per-capita residual about .61/year.

The corrected acceptance evaluates true per-capita growth plus migration,
without a biomass denominator floor. It rejects that state and retains the
valid 287.03 K mixed branch with residual about 3.3e-14/year. Tiny balanced
sink populations remain permitted; this adds no ecological extinction floor.
Two regressions cover rejection of the false state and acceptance of a tiny
balanced sink. The provisional source and outputs were preserved under
ignored `local/haze/dynamic_realisation/pre_percapita_guard/`. All 108 families
were rerun with the corrected, separately hashed source; provisional records
are not used in the reported claims.

## Supply-band scope

Homogeneous fixed and methane-only allocation endpoints are algebraic and
include the reference abiotic methane contribution. Other reported bands are
last resolved points on a bounded supply continuation, explicitly labelled
`resolved_branch_segment_not_global_band`. They are not root-located global
coexistence boundaries. Different starting roots are retained; a common sign
of climate slope is not used to assert branch identity. Failed continuation,
domain support and finite supply windows remain unresolved boundary reasons.

The small omitted abiotic term in the earlier Stage A diagnostic was caught
by the independent B1 algebra. That diagnostic and its self-pinned receipt
are corrected; the accepted raw archives and prepared 45 MB companion remain
unchanged. The correspondence preserves the original statement and correction.

## What remains scientifically open

The seventeen-to-thirty-three quadrature comparison fails for the independently
checked reference example; some critical lags are right-censored and many G
values are undefined. Counting those as agreement would manufacture support
for PB1. Conversely, a finite-N candidate cannot be advertised as a continuum
exception without qualification. The near-pinning threshold is approximate
and the matched-control ratio compares generally different operating climates.

PB2, PB3, PB4's two-layer clause and PB7 have scoped counterexamples or analytic
refutations. PB5/PB6 require nonlinear B2/B3 and are pending. Claude should now
review this build and decide how to resolve the habitat continuum and response
comparison before pruning or launching the heavier invasion experiments.
Writing readiness remains withdrawn.
