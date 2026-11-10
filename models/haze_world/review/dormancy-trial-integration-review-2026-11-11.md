# Dormancy trial guard: qualification and limits

Codex, 11 November 2026. The named numerical variant is
[`dormancy_trial_integration.py`](../../../src/terra_prisca/haze_world/dormancy_trial_integration.py).
Its frozen SHA256 is
`b5c0d208454c8f55b4da865a387ea592f117e28700bb13d1025efe4a4e92ef18`.

The physical-model source graph matches the earlier prefix controller exactly.
Neither `dormancy_integration.py` nor `bottleneck_integration.py` was edited.
The frozen T3 census experiment retains its original source and identity.

## Numerical changes

The variant reuses the frozen integration function through a private namespace.
It preserves its census, accepted-flow, dense-minimum and step-refinement code.

- Nonfinite trial coordinates, floating overflow/invalid results, nonfinite RHS
  values, or nonfinite returned coordinates/dense coefficients become failed
  numerical steps. The frozen driver rolls back to its saved valid state,
  refines the step and restores the nominal ceiling after successful flow.
- An overflowing square-root allocation uses the existing stage-conditioning
  path to express the accepted allocation in linear coordinates. Finite trial
  rates above the existing `10^8 /yr` conditioning criterion are observed but
  cause no intervention unless the native solver actually fails or cannot
  advance. A disposable Jacobian trial is not sufficient reason to change a
  successful trajectory's chart.
- A named acetate-source overflow can request a chart change at the next
  accepted restart. It is allowed only when the accepted decoded chemical
  stock is already exactly zero. The conversion preserves the entire decoded
  physical state bitwise; a positive pool is never reset.

Actual acetate overflows remain in the inherited acetate-specific event list.
Other rejected trials and stage/chemical conditioning have separate typed
records. Unrelated model errors propagate.

Global guild log stocks remain available through physical underflow. A stage
chart conversion can lose a subfloat *stage* log while retaining its decoded
allocation; the prior log is recorded. As in the frozen implementation,
replenishment is by physical conversion or migration. Likewise, an underflowed
chemical log is retained in the chart-change event rather than propagated as
an unobservable chemical tail. These limitations should not be described as
exact retention of every type's logarithm.

## Actual `dormancy_0000` checks

The checks use the original no-refuge, `f = 0`, `epsilon = 0.1`, acetogen-into-
methanogen start, uncensored annual sampling and the nominal ten-year maximum
step. Input/source identities and raw hashes are in the linked reports.

| Horizon | Result |
|---|---|
| [1,000 years](dormancy_trial_recovery_1000.json) | Bitwise agreement with the frozen function in times, physical stocks, active/dormant/guild logs, global minima and their times; no conditioning events. |
| [3,000 years](dormancy_trial_recovery_3000.json) | Completes in 16.47 seconds, with 54,540 RHS evaluations and 6,847 accepted pieces. Two stage conditionings and one chemical-chart conversion; no nonfinite-step rejection. |
| [30,000-year attempt](dormancy_trial_recovery_30000.json) | Bounded at 180 seconds, reaching 4,517.962 years. Native steps become very small. This horizon is **not qualified**. |

The 3,000-year profile has nonnegative stocks, finite present-guild total logs,
dense minima bounded by its samples and maximum sampled redox residual
`1.31e-18`. Its chemical conversion at 2,722.467 years preserves decoded
acetate `0 mol/L` bitwise and records the former log concentration
`-1194.377`. The first stage conversion at 2,460.880 years preserves decoded
allocation zero and records its former log allocation `-887.471`.

Nineteen focused tests cover ordinary bitwise fidelity, zero switching,
per-capita stocks below physical underflow, absent types, redox/minimum checks,
rollback and ceiling restoration, separate acetate accounting, unrelated
errors, dense-result validation and zero-time terminal notifications.

## Why the bounded tail does not block this first-window result

The resident methanogen minimum occurs at 1,039.422 years, before any new
conditioning. Its natural log biomass density, measured in gDW/L, is
`-914.969`. With the model's cell conversion, this is log expected
cell count `-847.772`. Under the project's fixed-path branching interpretation,
survival beyond this bottleneck is bounded above by its expected cell count.
Even at the largest tested count scaling, `s = 1000`, that bound is below
`10^-365`.

Thus the later numerical tail is unnecessary for classifying this first
resident window as robust loss. The later acetogen minimum is conditional on
continuing a methanogen lineage whose first-window expected survivors were
astronomically below one cell. It is not an unconditional second extinction
claim for a finite world. The production assessment separately establishes
the first window's closure; the helper is qualified here for the relevant
3,000-year prefix, not for arbitrary long horizons or all census cases.

Two more aggressive numerical alternatives were rejected. Conditioning every
large finite Jacobian trial caused repeated chart changes. Keeping every
conditioned stage permanently linear replaced that with positivity-refinement
work for tiny allocations. Neither justifies a new production contract.

## Reproduction

```sh
uv run pytest -q tests/test_dormancy_trial_integration.py
uv run python models/haze_world/review/dormancy_trial_recovery_check.py --years 1000
uv run python models/haze_world/review/dormancy_trial_recovery_check.py --years 3000
uv run python models/haze_world/review/dormancy_trial_recovery_check.py --years 30000 --wall-seconds 180
```

The last command reproduces the bounded negative qualification. Detailed
receipts, raw profiles and numerical source snapshots stay under
`local/haze/dormancy_trial_review/`; the small public reports retain their
hashes. Further work should target genuine unresolved first windows or census
stalls rather than extend this already decisive loss window through its
conditional continuum recovery.
