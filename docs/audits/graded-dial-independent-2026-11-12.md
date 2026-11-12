# Independent review of the graded dials

Codex independent mathematical and numerical route, 12 November 2026.
Production modules and outputs remain owned by the parent and D1 delegate.
This audit owns the companion script/JSON and its regression tests. It
recounts C54, reviews the design before decisive runs, and checks selected
states from separately assembled physical derivatives.

## Design review before the new dials

The [method note](../../models/haze_world/graded-dial-methods.md), frozen as
`9b63b47`, incorporates the material qualifications below. I accept that
operationalisation of the original PD1–PD4; the predictions are preserved.

1. **D1 is one chosen path in model space.** The exponent dial is well-defined
   at positive acetate and recovers fixed/acetate-only endpoints. Its chemical
   derivative is `kappa*h_A/(4*C)`. Endpoint equality alone does not make it
   equivalent to interpolating the threshold multiplier. The standalone D1
   module correctly keeps the old source epoch unchanged.
2. **A sparse jump is not a mathematical discontinuity.** A tenfold change
   between sampled settings can refute PD1's finite-grid criterion without
   establishing that every nonzero graded term supplies robustness. If the
   equilibrium is regular and the first Hopf root is simple and transversal,
   implicit eigenvalue continuation supplies local continuity. Branch loss,
   mode switching, resolution failure and censoring are different events.
3. **PD2 does not define a linearity tolerance.** Its slope band is an
   assessable necessary clause. The fitted residuals and R-squared must remain
   descriptive; a new acceptance cutoff cannot be chosen after the results.
4. **PD3 needs a qualified bracket.** Interpolation through a kink, lost
   branch or censored endpoint would not locate the 30-year threshold. The
   frozen extra equilibrium/spectrum refinement supplies a direct check of
   the interpolation and retains the numerical bracket.
5. **PD4 names a particular mode.** The greatest-real complex pair need not
   remain the same pair as the dial increases, nor dominate real slow modes.
   Record competing modes and the crossing frequency. Do not replace a poor
   weak-mode prediction by selecting a different pair after seeing its error.

The scalar approximation is `tau_weak=2*gamma/omega^2`, with
`gamma=-Re(lambda)` and `omega=Im(lambda)` at zero thermal lag. This is an
approximation to the delayed feedback system, not an identity for a general
multispecies Jacobian. Its empirical factor-two prediction is tested as
written even if its weak-damping interpretation fails.

## C54 is correctly counted, with limited scope

The companion script reads the two committed C0/C1 CSVs directly and rejects
unknown spectral statuses instead of treating them as zero lag. With the
stated `3e-10 K` exact-pinning cutoff it independently obtains:

| Group | Count | Result |
|---|---:|---|
| Exactly pinned | 42 | 36 finite losses; 6 already unstable; maximum finite margin 7.07952 yr |
| Ordinary graded | 122 | 9 finite losses; 113 censored through 10,000 yr |
| Reversed frozen response | 6 | Every one is already unstable at zero lag |

The ordinary group's minimum absolute supply slope is 0.589645 K/e-fold and
its minimum finite margin is 331.426 yr. The nine spatial finite-margin
points have Spearman rank correlation 1 and OLS log–log slope 1.48212. The
original recount helper uses a looser `1e-6` classification threshold, but
this changes no current memberships: the largest pinned magnitude is
`2.2971e-10` and the next ordinary group begins far above it.

These results independently support C54 as a description of the committed
sample. They establish neither a universal causal trade-off nor a proved
singularity at zero grading. The nine finite spatial points pool different
supplies, acetate fractions and connectivity; their descriptive rank ordering
does not by itself identify one within-branch causal curve. The new dials
address that gap with controlled branches.

## The zero-dial Hopf is numerically regular

The checker reconstructs local physical flows independently from uptake,
growth, assimilation, export, recycling and methane loss. It differentiates
positive stock coordinates by a five-point logarithmic stencil, then applies
the weighted mean couplings and physical thermal row. It imports neither
production's weighted Jacobian nor the D1 variant's derivative routines.

At the two homogeneous fixed-chemistry reference states, this separate route
gives:

| f | Zero-lag complex pair | Critical lag, yr | Hopf frequency, rad/yr | Re(dlambda/dtau), per yr squared |
|---:|---|---:|---:|---:|
| 0 | −0.000206019 + 0.05254894 i | 0.1492143 | 0.05254895 | 0.00138057 |
| .5 | −0.000926010 + 0.04094346 i | 1.1027601 | 0.04095162 | 0.000837815 |

The stocks are positive and the static matrices are nonsingular numerically.
Their smallest singular values are about `2e-5`; large condition numbers
around `2.5e10` reflect the stiff resource-versus-atmosphere timescales and
are retained in the receipt. The critical eigenvalues are isolated and have
positive crossing speed. Full-system residuals are below `4e-12` under the
declared scaling. These are finite-precision checks of the regularity
conditions, not an interval certificate.

Consequently, exact pinning is a special boundary property along this chosen
path, but it is not evidence of a singular equilibrium Jacobian or a
discontinuous spectral limit. For any fixed positive mixing rate, the
finite-quadrature spatial equations can be written on a fixed normalized
offset coordinate; sufficiently narrow spreads remain inside the same smooth
physiological pieces. Their coefficients vary smoothly with spread. The
continuum limit additionally needs the declared mesh checks; no general
functional-analytic theorem is inferred from the collocation sample.

## Correct the joint-extinction interpretation

Claude's latest report calls the B2 10–100-year paths extinction of both
guilds. Those B2 trajectories are uncensored. Once the first guild drops
below one global cell, later recovery from fractional expectations changes
the subsequent environment. A later subcell minimum of the other guild does
not establish its fate in a finite system where the first has been removed.
The supported statement is loss of the exact mixed regulator along these
uncensored trajectories, with per-guild minima explicitly scoped. The B3
census endpoints are separate evidence for invasion-history dependence.
The parent accepted this correction in the frozen methods.

## Selected independent state checks

Before viewing the new grid, the selected controls were D1 at both acetate
fractions with kappa `0, .01, 1`, plus D2 at `(sigma,d)=(.1,1e-4)` and
`(1,1e-3)`. Any additional 30-year threshold roots are selected diagnostic
checks, not new prospective predictions.

The checker builds the local derivatives anew, reduces them to the
four-variable characteristic determinant, and validates pole distance,
smallest singular value and full back-substitution residual. It separately
projects the instantaneous matrix to fixed local guild shares for S_0.
The 721/1441-point frequency comparisons are finite search checks, not a proof
of complete root enumeration or infinite-delay stability.

All eight originally selected controls agree with the primary route:

| Stage | f | Dial | d, per yr | Independent first loss, yr |
|---|---:|---:|---:|---:|
| D1 | 0 | kappa=0 | .001 | 0.1492143 |
| D1 | 0 | kappa=.01 | .001 | 1.0998900 |
| D1 | 0 | kappa=1 | .001 | no crossing through 10,000 |
| D1 | .5 | kappa=0 | .001 | 1.1027601 |
| D1 | .5 | kappa=.01 | .001 | 2.0564803 |
| D1 | .5 | kappa=1 | .001 | no crossing through 10,000 |
| D2 | .5 | sigma=.1 K | .0001 | 115.920194 |
| D2 | .5 | sigma=1 K | .001 | 842.240462 |

I additionally checked both D1 final 30-year bracket endpoints and the upper
endpoint of each D2 bracket. The D1 first losses lie at 29.976/30.417 yr and
29.958/30.288 yr, while the D2 upper losses are 30.163 and 30.312 yr. These
confirm the first-loss brackets; no recovery root precedes those losses.

Two already-computed refinement points exposed failures of PD4 and were then
selected for independent diagnostic checks. Across all **16** checked states,
the largest absolute S_c difference is `1.13e-10 K`, the largest S_0 relative
difference is `8.2e-11`, and the largest finite critical-lag relative difference
is `4.7e-7`. Frequency doubling changes finite roots by at most `1.1e-11`
relatively. All back-substitution residuals are below `4.6e-12`. The two
censored endpoint classifications agree. Every independently projected
frozen system is locally stable.

### Weak-mode counterexamples are real

All 23 eligible prescribed points and both zero-spread controls satisfy the
factor-two criterion. But two of the 29 already-computed threshold refinement
points do not. They are not a new parameter survey or an omitted negative
result:

| D1 f=0 kappa | Independent tau_c, yr | Weak estimate, yr | Estimate / actual | Zero-lag gamma/omega | Critical omega, rad/yr |
|---:|---:|---:|---:|---:|---:|
| .150980365 | 35.637143 | 16.909220 | .474483 | .418217 | .03413577 |
| .173205081 | 78.592400 | 20.504677 | .260899 | .494346 | .02472649 |

The first margins match primary values to better than `3.1e-9` relatively.
The selected pair has not been changed to create these counterexamples. At
zero lag the angular frequencies are .0494662 and .0482179 rad/yr; thermal
lag lowers them substantially by the critical point. Their damping ratios
are no longer small. A leading-order weak-damping approximation therefore
underestimates the margin. PD4 cannot be stated as a general rule for all
points with tau_c below 100 yr; its success on the prescribed grid is retained
separately from these authorised-refinement counterexamples.

### Loss and recovery boundaries are different

D1 f=0 also has validated high-lag recovery roots. Near the final 30-year
bracket the two recoveries are about 8,576 and 8,414 yr. At the counterexample
points above, they are about 6,866 and 2,696 yr. Thus stability need not remain
lost after the first crossing. The reported margin is specifically the
**first loss** from zero lag. A narrowing instability interval or disappearance
of its two boundaries at positive kappa would not establish a jump at zero
grading. No full continuation of that high-lag boundary is claimed here.

## Semantic and prediction recount

I read the scorer and independently recounted its public records. The final
assessment's source and input hashes match. Its scoped dispositions are
accepted:

- **PD1:** the 26 finite adjacent pairs increase and have ratios below ten.
  The two first censored transitions have lower ratio bounds of about 771
  and 783, and are explicitly excluded from the finite-pair reading of
  "until right-censoring". That reading is not support for global continuity
  or a proof of no jump anywhere along the path. Local zero-dial continuity
  instead rests on the regularity conditions above.
- **PD2:** the half-recycling D1 slope is .796568, outside the prescribed
  band. The low-connectivity D2 fitted slope is .985198, also below it; the
  parent's extra mesh checks make its numerical difference much smaller
  than the discrepancy. The two-point D1 f=0 fit cannot test linearity.
  No new residual or R-squared cutoff has been introduced.
- **PD3:** all four qualified price brackets lie within .05–.5 K/e-fold.
  They are retained as ranges, not high-precision threshold point estimates.
- **PD4:** prescribed-grid agreement and the two refinement counterexamples
  are both retained. The assessor correctly records refutation by authorised
  refinement rather than discarding those points.

The scorer's right-censored horizontal marker originally pointed left; the
parent changed it to point right, consistent with a lower bound on tau_c.
No numerical state, spectrum or prediction value changed in that repair.

No new nonlinear invasion or long trajectory was run for this audit. The
model stage is numerically accepted within these limits. This audit does not
close the remaining scientific scope/literature triage or itself authorise
paper drafting or a writing-readiness declaration.

## Reproduction

```sh
uv run python docs/audits/graded-dial-independent-2026-11-12.py \
  --states models/haze_world/figures/graded_dials/states.json \
  --threshold-states models/haze_world/figures/graded_dials/threshold_refinement/states.json \
  --threshold-brackets models/haze_world/figures/graded_dials/threshold_refinement/thresholds.json \
  --assessment models/haze_world/figures/graded_dials/prediction_assessment.json
uv run pytest -q tests/test_graded_dial_audit.py
```

Four tests cover the independent physical derivative matrices and slopes
against both existing endpoints, the C54 unstable/censored group recount,
and retention of the censored-transition ratio bound. Full endpoint equality
is a regression control, not the independent new-dial comparison itself.
