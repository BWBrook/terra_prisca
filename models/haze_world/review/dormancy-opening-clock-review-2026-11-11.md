# A consistent clock for probability-opening steps

The earlier [opening-kernel repair](dormancy-opening-kernel-review-2026-11-11.md)
fixed independently demonstrated probability arithmetic, but the fresh
expanded-grid scoring still failed for cases `0006`, `0007`, `0062` and `0063`.
An official uninstrumented case-0006 task then captured the actual exception.
The failure was a finite coarse/fine discrepancy, not a positive or nonfinite
probability.

At the exact sample knot `95130 yr`, the final attempted duration was
`1.0387200421e-10 yr`, or about 7.138 clock spacings. The coarse endpoint rounded
to seven spacings before the start. The two absolute-clock half steps ended
eight spacings before it. An opening wake edge was therefore integrated over
different intervals. The affected dormant log probabilities differed by
`0.13354`, close to `log(8/7)`. The normalized error remained `1.50e6` after
all 30 refinements. Every probability log was finite and nonpositive.

The predecessor is source
`c754e3feac7baf81feb8bf2ffb353f488e06632586b06bb82f96c7969f6293df`
at commit `c5568cf81b53156cac7dc5aa1f8d6649ca697e8c`. The repaired source is
`93f5c2bd47824186ad24d12400f63218e2ff1c16edc4c3e9627914dc98226f62`.

## Numerical change

Each bootstrap trial first chooses a representable full-step endpoint and
sets its duration to the actual clock difference. If nearest rounding would
exceed the requested duration, the endpoint moves one spacing toward the
start. The original maximum-step and inverse-rate caps therefore remain
upper bounds. An unrepresentable positive step still fails explicitly.

Both approximations then use local offsets over that same duration. Affine
rate interpolation uses the distances to the two source knots directly,
avoiding both large-clock midpoint cancellation and subtraction of a fraction
from one near an opening edge. The fine path ends at the same local endpoint
as the coarse path. The native LSODA clock, recorded rates, probability
equations, 30-attempt limit, error norm, tolerances, probability-domain checks
and first-window classifications are unchanged.

## Verification and scope

The [checker](dormancy-opening-clock-review-2026-11-11.py) verifies the captured
failure report and recovered-rate archive by checksum. It reproduces the
predecessor's final coarse and fine vectors bitwise. The repaired opening
passes on attempt 17 at `h = 4.25454346e-7 yr`, with normalized error
`0.642689882`. Local rates are bitwise unchanged when the fixture clock is
translated from `95130 yr` to zero. Endpoint-cap and lost-resolution tests
cover the representability contract.

All 49 related branching and turnover-survival tests pass. An independent
read-only review cleared the same source and test hashes and reran those
tests. The [control JSON](dormancy-opening-clock-review-2026-11-11.json)
retains source, controller, actual-failure and rate-archive identities.

One complete official case-0006 task finished in 254.24 seconds. It used the
selected physical profile without a new physical simulation. Both complete
guild rows, four scoring-source hashes, profile and census identities, and
the unchanged receipt selector are retained. Both guilds are classified as
never globally rare over the recorded 0–100,000-year window, with represented
conditional probabilities rounding to one. These are conditional recorded-
environment diagnostics, not joint endpoint probabilities. Full expanded-grid
rescoring under the repaired source remains a separate completion gate.
This clock correction supplies no general entrywise-tail or global survival
accuracy guarantee beyond the stated controls.

```sh
uv run pytest -q tests/test_dormancy_branching.py tests/test_branching.py tests/test_turnover_survival.py
uv run python models/haze_world/review/dormancy-opening-clock-review-2026-11-11.py
```
