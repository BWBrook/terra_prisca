# Dormant-bank endpoint assessment

All 41 dormant-stock-only failures have stationary active stocks, chemistry,
climate, total guild biomass and census occupancy under the fixed criteria in
[the classification design](dormancy-tail-classification-design-2026-11-11.md).
They receive the descriptive class **macro state stationary; dormant bank
unresolved**. None qualifies as **settled up to dormant relaxation**: the
archived bank variation is not quantitatively explained by a frozen-root bank
forecast. This is a post-review amendment; the original 56 stationary and 72
unsettled labels remain intact.

The largest final-window relative span among active/chemical stocks is
0.000142, the largest total-guild span is 0.0000618, and the largest temperature
span is 0.000911 K. All are below their unchanged bounds (0.001 and 0.01 K).
There are no late census removals or changes of local one-cell occupancy.
Every case agrees with a nearby present-guild root at the macro tolerances.
Recorded resident roots have their stationary banks recomputed at the current
equation evaluation; mixed roots are refined from each observed late mean.

The additional pair comparison retains total active-plus-dormant biomass and
local/global one-cell occupancy. It compares observed macro states, not full
dormant banks or asymptotic attractors:

| Comparison of the 64 invasion pairs | Both qualify | Same state under that comparison |
|---|---:|---:|
| Original strict stationarity/full-stock test | 19 | 10 |
| Additional macro stationarity/macro-state test | 41 | 25 |

The bank check fails by more than a choice near the 0.001 tolerance: in every
case at least one failing bank has a prediction error exceeding 28% of its
observed late-window range. Two examples explain why the banks cannot all be
described as pure exponential tails:

- **Case 0004:** the bulk methanogen bank ranges from 8.14 to 8.99×10⁻²¹ gDW/L
  while its active-to-dormant source ranges from 7.14 to
  7.88×10⁻²¹ gDW/L/year. A much smaller warm-patch bank is supplied by
  migration. The two bank eigenvalues near −0.877/year describe rapid
  response to a slowly changing source, rather than a free 20,000-year
  decay. The frozen-root prediction misses 116% of the bank's observed
  range. The bulk bank still represents about 1.34 billion cells globally.
- **Case 0040:** the active/chemical relative span is only 4.55×10⁻⁷, but
  switching repeatedly turns the small dormant-entry sources on and off.
  The two banks vary nonmonotonically; their maximum entry sources are
  1.41×10⁻¹⁹ and 2.79×10⁻²⁰ gDW/L/year. The frozen-root sources are about
  10⁻³² and 10⁻³⁰, and the predictions miss 60–63% of the observed ranges.
  Small deviations near the switching boundary therefore matter to a bank
  even while the active climate/ecology is stationary at its stated precision.

These observations do not decide whether each residual source variation is
physical relaxation, numerical error, or both. Retained active-population logs
are checked before declaring a sampled entry source absent, so decoded
underflow cannot establish absence. Sampled source absence is not a proof
between saved observations. Failing banks reach as many as 1.05×10¹⁸ cells
worldwide; small biomass fractions do not imply demographic irrelevance.

The earlier diagnostic's 10 monotone and 31 nonmonotone bank paths, including
case 0056's failed retained-log source-free prediction, remain valid reasons
to withdraw the blanket exponential-decay interpretation. No new long
trajectories were integrated, and no original trajectory, receipt, summary,
strict pair flag or bottleneck probability was changed.

Reproduce the assessment and its 11 focused tests with:

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache MPLCONFIGDIR=/tmp/terra-prisca-mpl OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run python -W error -m terra_prisca.haze_world.dormancy_tail_assessment
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache MPLCONFIGDIR=/tmp/terra-prisca-mpl OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run pytest tests/test_dormancy_tail_assessment.py -q
```

The [machine-readable output](dormancy-tail-assessment-2026-11-11.json) pins
all 128 selected receipts, the existing diagnostic, the classification design,
the assessor and its source dependencies. It records the failed bank fits,
root provenance, original strict results and additional pair comparisons.
