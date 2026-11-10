# Accepted-stage chart conditioning

Codex, 11 November 2026. This review concerns the named numerical variant
[`dormancy_stage_integration.py`](../../../src/terra_prisca/haze_world/dormancy_stage_integration.py),
SHA256 `19b7909fda2feb47b767ec7a81050fd8c935f59b1aa25149b8159722597130eb`.
It leaves the physical model and all earlier numerical epochs unchanged.
Long-run controls are recorded separately from the bounded checks below.

## Two observed failures

The frozen chemical variant failed in census case 0107 at the accepted dense
endpoint **4550.071294205805 yr**. A post-step derivative used for coordinate
promotion encountered an exactly zero warm active-acetogen root with a finite
retained incoming log source. That call lay outside the driver's existing
stage-source handler. The [saved accepted state](dormancy_4550_regression.json)
reproduces the failure. Converting that root also exposes an unrepresentable
allocation-Newton row at the bulk active-acetogen root.

There is a separate reason for the allocation matrix to overflow even when
all physical stocks and RHS values are finite. For a receiving root `z`, an
incoming allocation `I` contributes `I/(2z)` to its rate and
`-I/(2z²)` to the own derivative. The derivative can exceed floating range
before the rate does. The bounded waking control has an allocation of
`1e-307` and a waking rate of about 38 per year: its RHS is finite, but the
source diagonal exceeds the largest double. A source-free receiver with root
`1e-320` gives another exact example through its derivative with respect to a
linear donor allocation. Reducing the time step does not make such a matrix
representable in that chart.

## Numerical change

The new matrix labels nonrepresentable positive-allocation rows with the
existing stage-conditioning exception. The accepted driver converts the
**saved accepted** root to its already decoded linear allocation, records the
triggering trial separately, and restarts from that accepted state. It never
copies a failed trial population into the accepted state.

The accepted-step driver is copied from `7046fc9b` with tightly bounded changes:
its existing construction/native-stage conversions share one checked mapping;
post-step derivative calls now handle stage conditioning explicitly; any such
post-step mapping forces a solver restart, even when no ordinary promotion
would have restarted it. Dense-flow/minimum accounting, censuses, domain and
positivity checks, tolerances and promotion ages retain their original code.
The analytic chemical rows from `75c538cb` and progress handling from `ee65a5d0`
are reused in private namespaces.

Every conversion asserts that the **whole decoded physical vector** and
encoded total-guild coordinates are bitwise unchanged. Metadata retains the
accepted hash, trial hash/time where applicable, old root and stage log,
linear allocation, incoming log source, inventory comparison and phase.
Recomputed global-guild log diagnostics can differ by roundoff; their equality
flag is recorded without a universal assertion. If squaring an extremely
small root already decodes to zero, its finite stage log is recorded but is
not propagated after the linear conversion. This retains the existing stage
underflow limitation. No population seed, clipping, stock reset or change to
physical migration or waking is introduced.

## Bounded qualification

The ten focused tests pass. They cover finite-RHS/unrepresentable-Jacobian
examples, hypothetical trial root zero against a positive accepted root,
explicit post-step restart, directional derivatives in unequal habitats,
ordinary flow/census/minima equality, nonzero census removal, zero switching
and native terminal notifications. The saved 4550-year state advances another
ten years through both required chart changes with finite nonnegative stocks
and unchanged inventories at each change. The stage, chemical and progress
regression set passes **32 tests**. The parent also completed the full suite:
**494 tests passed**.

Independent branching review reran the 32 tests and found no consequential
defect. Its injected post-step control counted 250 positive contiguous dense
intervals over 0–0.2 yr exactly once, with the expected census and sample times.
In 300 static maps all physical vectors and encoded totals were bitwise
preserved; the largest recomputed global-log difference was `1.776e-15`.

The original-start **case-0107 census control reaches 5,000 yr in 13.41 s**
(3,234 accepted pieces, 5,361 RHS evaluations). Its fingerprint is
`344273173197598f81160da5cb0168fa978d911d2fd22c186ea7325040570335`.
It crosses the old Linux failure horizon with nonnegative stocks, finite
present-guild total logs, no census removals, minima below the sampled values
and sampled redox residual at most `2.61e-18`. Three numerical-failure retries
are retained; there are no positivity refinements or zero-time restarts.

This Mac control makes one stock-preserving native-stage conversion at year
1,457.175, before the later Linux post-step failure. It does not reproduce the
identical Linux step sequence. Across 456 shared accepted sample times through
year 4,550, its maximum temperature difference from the old Linux partial
trajectory is `5.17e-8 K`; maximum biomass difference is `1.44e-11 gDW/L`.
The saved-state regression separately exercises the exact later singular
state and required post-step mapping. The
[qualification JSON](dormancy-stage-qualification-2026-11-11.json) retains
source, protocol, receipt, payload and observer hashes and these comparisons.

The helper/runner/contract snapshot is committed as `b7e39c8`. A formal Linux
100,000-year case-0107 control remains pending. The completed 5,000-year run is
a numerical recovery control, not a settled ecological endpoint or a claim
that the remaining grid is complete.

```sh
uv run pytest -q tests/test_dormancy_stage_integration.py
```

Two separate Linux 100,000-year requests used a 300-second observational
wall guard. Case0107 advanced to92,298 years; case0085 passed its former
440-year stall but progressed slowly at2,241 years. Neither returned a
complete receipt before the guard, so neither qualifies an endpoint. Their
accepted states and diagnostics remain in the qualification JSON. The latter
case exposes a separate scaling problem: disposable zero-producer Newton
excursions can overwhelm a tiny chemical pool although the current RHS is
finite. It is not resolved by declaring a population extinct or changing the
physical census rule.
