# Dormancy switching and chemical-chart numerical review

Codex, 11 November 2026. The qualified numerical helper is
[`dormancy_jacobian_integration.py`](../../../src/terra_prisca/haze_world/dormancy_jacobian_integration.py),
SHA256 `7046fc9baa47022fff7e700ea79f8e72e2c3195a77b9bd5f71e272d6a1c34310`.
The [qualification receipt](dormancy-jacobian-qualification-2026-11-11.json)
records the full source graph, inputs and raw hashes. The frozen physical
model, old integration modules and original T3 receipts remain unchanged.
This is a numerical repair, with a separately identified experiment runner.

## Cause and repair

The warm-refuge invasion `dormancy_0010` stalled during its first acetogen
bottleneck. Repeated matrix construction dominated; the maximum step remained
ten years, and no coordinate-condition/rejection loop explained the initial
slowdown. Native finite differences perturb pressure and methane across a
microbe's growth boundary. Near that boundary the cubic waking response is
quadratic, so its true first derivative vanishes. A finite perturbation still
creates a quadratic waking source, which the square-root allocation equation
divides by an extremely small root. The resulting Newton matrix can be
arbitrarily misleading. Making only the root-coordinate perturbations
relative did not fix the forcing columns and made the control slower.

The new matrix differentiates allocation, weighted mean growth, migration and
active/dormant switching algebraically. For the cubic response its slope is
`6x(1-x)` inside the ramp and zero outside, including the growth boundary.
Primitive net-growth and nonallocation gradients still use numerical
differencing. This is an approximate Newton matrix used by the solver;
the physical RHS is unchanged. Directional checks on separate spatial states
agreed to about `1.3e-8` relative error.

A second failure arose when an acetogen allocation had to become linear while
its extremely small acetate pool remained logarithmic. The mixed charts gave
an enormous chemical-source derivative. The helper converts that producer's
chemical pool to its existing physical amount at the same accepted state.
Every recorded conversion preserves all decoded physical stocks bitwise and
the inventory exactly. Chemical promotion requires the producer's positive
chart, plus the existing `1e-6 yr` entry-age criterion; an absent producer does
not block promotion. Actual large accepted chemical/stage rates can also
request conditioning. Disposable finite Jacobian trials alone cannot.

The driver is a named copy of the frozen function for those explicit chart
and promotion hooks. It retains the census, accepted-flow accounting,
positivity checks, minimum calculations, error tolerances and biological
rules. The earlier [trial guard](dormancy-trial-integration-review-2026-11-11.md)
still rejects invalid trials and is imported without modification.

An exactly zero, source-free square-root allocation needs a finite diagonal
Newton limit. The physical RHS already permits it while retaining the global
guild log. The new matrix uses that limit and records its use; a real incoming
source instead requests the existing linear chart. This fixes the control in
which an active stage underflows while dormant guild stock remains in log
coordinates. It adds no cells.

## Qualification

| Check | Result |
|---|---|
| Twelve focused tests | Pass, including independent physical-Radau flow, source-free and source-bearing zero roots, absent types, zero switching, a genuine delayed source onset, positive-pool conversion, census/minimum and redox checks. |
| Original no-refuge `0000`, uncensored 3,000 yr | Completes in 15.80 s; 6,299 accepted pieces. |
| Original warm-refuge `0010`, uncensored 3,000 yr | Completes in 93.40 s; 20,608 accepted pieces. |
| `0010`, census 100,000 yr, final source | Completes in 70.30 s; 21,152 accepted pieces. The measured endpoint passes the existing census-stationary criterion. |
| Exact valid native `0010` checkpoint at 1,303.621869 yr | From the original start, maximum temperature difference `7.14e-6 K`; bulk hydrogen-pressure difference `1.54e-5 Pa`. Acetogen guild logs differ by at most `3.82e-4`; methanogen logs by `1.3e-8`. |

The [native checkpoint](dormancy_native_1303_checkpoint.json) stores its
coordinates and chart flags. No interpolation across the steep rare-population
decline was used. The no-refuge comparison through its closed first resident
window differs from the qualified trial guard by at most `2.02e-6 K`; the
methanogen minimum differs by `1.20e-4` natural-log biomass units and
`0.000136 yr`. Its robust first-window loss classification is unchanged.
Both prefixes have nonnegative stocks, finite present-guild logs, dense minima
bounded by their samples and sampled redox residuals below `2.7e-18`.

The 100,000-year pilot uses the formal new runner. Its receipt fingerprint is
`f7924ad5df000ba57bec68f55f16cf6803fc0957ddffb99741cf8bb125ad164c`,
and its raw SHA256 is
`58e100fcf7dc558e189305c7b1d9cae41b0519cada0efa9057b95f392fee8202`.
The receipt preserves eleven positivity refinements, three solver retries and
two bitwise-preserving chemical conversions. It is one qualified census run,
not evidence that the whole grid has completed or converged. An earlier
100,000-year pilot used source `e0e3846d` and is retained only as historical
runtime evidence.

A matching Linux pilot completes with the same physical source and packages.
Its climate agrees with the Mac trajectory within `1.3e-6 K`, but its strict
stationarity flag differs because a warm dormant pool briefly reaches about
996 cells, only `1.13e-23` of the global biomass. The
[platform precision audit](check_dormancy_platform_precision.json) preserves
both classifications and the independently stored Linux receipt. This
supports continuing the macrostate/community sweep; it does not establish
reproducible stationarity of every microscopic dormant bank at this tolerance.

## Rejected tolerance experiment and regression

Making tiny linear-stock tolerances proportional to their current stock and
first derivative failed. A source can arrive through an upstream stage with
nonzero acceleration even when its present amount and first derivative are
tiny. At the saved 1,399.067-year state, those tolerances implied startup times
of approximately `6.2e-23 yr` for the warm acetogen allocation and `4.0e-22 yr`
for bulk acetate. Both are far below the `2.27e-13 yr` spacing of the absolute
time coordinate. The original tolerances, together with the corrected charts
and matrix, advance the same state by one year in about 0.25 seconds. No
dynamic-tolerance experiment remains in the qualified source.

The [captured state](dormancy_1399_regression.json) is retained as a numerical
regression input. Its test checks positive dense flow and bounded progress at
the original absolute time. It is a diagnostic from an unqualified trial,
not a scientific endpoint. The temporary diagnostic reused its output name;
the failed receipt was overwritten, but its full accepted-state values,
chart flags, absolute time and source identity were independently corroborated
against the contemporaneous read-only inspection. The old helper identity was
`cfbcf12bc51e7246ebf808104179dd67b2f18d7a6b597d23cbd63f9801f0d439`.
This fixture makes that input permanent; qualified runs use distinct hashed
receipts.

## Scope and reproduction

```sh
uv run pytest -q tests/test_dormancy_jacobian_integration.py
uv run python -m terra_prisca.haze_world.dormancy_jacobian_experiments \
  --mode uncensored --years 3000 --case-id dormancy_0000 --case-id dormancy_0010 \
  --workers 2 --raw-dir local/haze/dormancy_jacobian_review
uv run python -m terra_prisca.haze_world.dormancy_jacobian_experiments \
  --mode census --years 100000 --case-id dormancy_0010 \
  --workers 1 --raw-dir local/haze/dormancy_jacobian_review
```

Global guild logs remain available through physical underflow. Individual
stage allocations can underflow, as in the frozen implementation; conversion
and migration are their only replenishment. The matrix repair does not make
later continuum regrowth from subcell fractions a finite-population result.
Score each group's first relevant bottleneck before interpreting subsequent
conditional dynamics. This qualification supports the two checked prefixes
and the census pilot; it does not promise bounded runtime for every parameter
combination or settle long-lived oscillations.
