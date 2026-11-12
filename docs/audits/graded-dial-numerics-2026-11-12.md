# Graded-dial numerical review

Codex delegate, 12 November 2026. Read-only review of the primary D1/D2 driver,
its numerical routes and the completed prescribed-grid outputs. The reviewer
implemented the standalone D1 kernel, so this is independent review of the
parent's driver and numerical qualification, **not** a second independent
physical model implementation. The separate characteristic/physical audit
provides that check.

**Verdict:** accept the primary driver and the sampled numerical results,
with the explicit postprocessing qualification below. No producer, grid,
state or prediction was changed during this review.

## Variant dispatch and counterfactuals

The D1 parameter class carries the physical exponent strength separately from
its inherited `acetate_only` label. Calling the old weighted block builder on
such a parameter would silently apply the full quarter-power derivative.
The primary driver avoids that error:

- D1 equilibrium, physical flows, per-cell rates and supply responses use
  `graded_acetate` throughout.
- Both the full delay spectrum and frozen spectrum receive the explicit
  exponent-aware blocks. The generic weighted matrix builder therefore never
  substitutes its default block calculation.
- Frozen biomass projection is applied to those same blocks, preserving the
  operating point and summed biomass equation.
- D1 positive-input perturbations reconstruct the same exponent and freeze
  the original share only for `S_0`; raw `S_c` perturbations let the mix change.

The dispatch regression makes the old weighted block builder raise and still
completes a partial-exponent point. Endpoint and partial-exponent derivative
tests are in the separate kernel test file. I found no incorrect full-strength
Jacobian path in D1.

D2 keeps fixed chemistry, its branch's connectivity, uniform quadrature and
full support. Dial advancement corrects the preceding positive state; bounded
step subdivision is recorded if correction fails. Refinement then uses the
continued state, without restarting the branch search. Coarsening used only
for a subsequent seed is followed by profile refinement and doubling again.
Failures retain unresolved labels rather than being called folds. Success
on a finite dial grid does not prove absence of a fold everywhere between it.

All twelve nonzero D2 prescribed states pass actual panel doubling. The
largest relative difference in `S_c` is about 4.2e-6; the largest finite-margin
difference is about 7.6e-6. Thus the absolute slope tolerance did not conceal
a poorly resolved small slope in this sample.

## Six unresolved raw finite-input checks

The primary driver correctly retained six raw-supply verification failures as
`unresolved`, even though their equilibrium/frozen-response statuses were
accepted. Those rows must not be described as having passed the original raw
check. They are:

| Branch | Dial |
|---|---:|
| D1, f=0 | kappa=0.0003 |
| D1, f=.5 | kappa=1 |
| D2, d=1e-4/year | sigma=.1 K and 1 K |
| D2, d=1e-3/year | sigma=.03 K and .3 K |

The [postprocessing script](graded-dial-numerics-2026-11-12.py) leaves the
producer and states untouched. It verifies all primary source/input/output
hashes, then repeats only those six checks at log-input steps 0.001 and 0.0003.
The Newton stopping tolerance is explicitly changed from 1e-10 to 1e-9/year.
Both actual per-cell and scaled physical-flow residuals remain recorded;
this change is a numerical stopping rule, not a biological parameter change.
Four exact zero-dial controls receive the same check and the declared absolute
error criterion rather than an ill-defined relative error around zero.

All ten points pass at both steps. The largest actual root/scaled-flow
residual is 2.53e-10/year, while the largest per-cell residual is below
2.60e-13/year. The dominant residual therefore comes from the chemical balance,
not a small-stock population being mistaken for equilibrium. Among nonzero
slopes the largest relative finite-input discrepancy is 2.79e-5, and the
largest absolute discrepancy is 8.18e-5 K/e-fold. Every nonzero check improves
when the step is reduced. The zero-dial finite differences are exactly zero
at retained floating precision at both steps.

The source-pinned [qualification receipt](graded-dial-numerics-2026-11-12.json)
contains each side's temperature, support, residuals, positive-stock minimum,
both finite differences and their errors. These are additional numerical
qualifications; the original six unresolved statuses remain in `dials.csv`.
They are not an independent derivation of the physical Jacobian.

Reproduce without altering primary outputs:

```sh
uv run python docs/audits/graded-dial-numerics-2026-11-12.py \
  --output /tmp/terra-graded-numerical-qualification.json
```

## Mode selection and delay loss

The primary calculation uses the full similarity-scaled matrix spectrum at
these collocation sizes. Every reported complex pair retains its eigenpair
residual; the maximum in the prescribed outputs is about 2.9e-15 under the
reported normwise normalization. At the first finite lag crossing the
selected complex pair is separately retained with its critical frequency.
The inherited finite lag scan is still a finite bracketing search, not a
proof covering every imaginable narrow instability window.

All nonzero D2 states have a real dominant eigenvalue at zero lag, while the
selected complex pair is the complex pair with greatest real part. The
driver keeps these separate, as the methods require. It does not substitute
the slower real sink-population decay into the weak-oscillation formula.

At the full-strength D1 endpoint there is no retained complex pair; frequency,
period and damping-time fields are correctly absent. At kappa=.3 the formula
would predict approximately 48 or 71 years, although no delay loss is detected
through 10,000 years. Those points are outside PD4's stated eligibility
`tau_c<100 years`. They demonstrate why agreement inside the eligible range
must not be generalized to every strongly damped or censored state.

## Provenance and interpretation

The driver freezes all source/input bytes before launching branches, retains
source epochs and partial branch histories, and verifies the source mapping
again after production. The main outputs contain 32 prescribed states plus
two D2 zero-dial controls. Cache identities depend on the complete declared
source mapping; no source mutations were made during the completed pool.

The larger adjacent-sample margin ratios, any fitted slope and a finite
continuation history do not establish a mathematical discontinuity or a
universal power law. Censoring is a bound, not a finite estimate. The parent
assesses PD1–PD4 against the frozen methods, including additional qualified
30-year brackets. This numerical review adds no claim about nonlinear basins,
joint finite extinction, all possible dial paths or writing readiness.
