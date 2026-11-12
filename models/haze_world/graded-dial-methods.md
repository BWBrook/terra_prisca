# D1/D2: design review and pre-run implementation choices

Codex (GPT-6), 12 November 2026. Operationalises the
[Stage B″ specification](graded-dial-spec.md), frozen there as `e941a92`.
PD1–PD4 and the 32 prescribed settings remain unchanged. This note precedes
the decisive dial runs. Endpoint regression checks against existing variants
and algebraic design checks are permitted before production.

## Named variants and continuation

D1 multiplies the acetogen's thermodynamic threshold by
`(C/C_ref)^(kappa/4)`. Its derivative with respect to positive acetate is
`h_A*kappa/(4*C)`. Methane-product activity stays fixed. Exponent
interpolation is an explicit path in model space; endpoint equality alone
does not distinguish it from interpolating the multiplier. No claim here is
invariant to all possible interpolation paths. A separate homogeneous module
keeps the old reference equations and source epochs unchanged.

D2 keeps fixed chemistry and the existing weighted uniform distribution,
with reference turnover, donor input and Arney case-B climate. The symbol L
in the preceding stage denotes cell loss/turnover, not solar luminosity;
these experiments do not vary solar luminosity.

Continue each of four dial branches forward from its exact homogeneous mixed
state: D1 at f=0 and .5; D2 at f=.5 and d=1e-4 and 1e-3/year. Correct the
previous positive equilibrium at the next dial value, interpolating or
rescaling the habitat mesh where needed. Halve failed continuation steps
within a bounded retry; keep the failure history. A failed nonlinear solve
does not establish a fold or branch disappearance. Record residuals, domain
and Jacobian conditioning. A supported positive branch cannot be replaced
silently with a different root or pure community.

Use D2's existing adaptive profile rule, followed by mixed-panel doubling
until both supply slopes agree within `max(.001 K, 2%)` and critical lags
agree within 2% or in right-censoring classification. Check the entire
temperature support without clipping, actual per-cell balances, and the
frozen-ratio finite-input response. Narrow distributions still require the
doubling comparison. Numerical limits are at most 4,096 nodes and 32 profile
refinement levels, with explicit unresolved status if exhausted.

## Slopes and spectra

S_c in K per e-fold of donor input is primary. S_0 freezes each habitat's
local guild ratio while retaining its total biomass equation, chemistry and
spatial redistribution. G_loc is the signed ratio where defined; it is not
given a new threshold. Preserve denominator and frozen-system stability
qualifications from Stage B′.

Use full similarity-scaled collocation spectra at the planned matrix sizes,
the B1 lag grid augmented by the existing logarithmic grid through 10,000
years, and bracket/refine every detected sign change. Record finite loss,
already unstable, neutral, unresolved and right-censored states separately.
Validate a reported root with the physical scaled eigenpair residual.
One-sided climate derivatives apply at a genuine piecewise-curve corner.

At zero lag, report the complex conjugate pair with greatest real part,
selecting its positive-imaginary member. Report every competing complex pair,
the dominant eigenvalue including real modes, and the pair's frequency,
period and damping time. Frequencies are angular frequencies in rad/year;
period is `2*pi/omega`, damping time is `-1/Re(lambda)` only for negative real
part. A missing, neutral or numerically near-real pair is unassessed, not an
invented oscillation. Record the critical crossing frequency separately;
mode changes must remain visible.

## Assessment of the four predictions

**PD1.** Assess non-decreasing margins and the specified adjacent factor-ten
criterion on the prescribed grid, with numerical-convergence tolerances.
Right-censoring yields bounds, not finite estimates. A large sampled ratio
refutes the sampling criterion; it does not establish a mathematical jump.
Conversely a finite grid cannot prove continuity. For a regular positive
equilibrium and simple transversal Hopf, implicit eigenvalue continuation
already gives local continuity near the zero-dial state. Check those
conditions rather than inferring a singular discontinuity from sparse data.

**PD2.** On each branch select only finite points with `2<tau_c<1000` years
and nonzero S_c. Fit ordinary least squares to `ln(tau_c)` versus
`ln(abs(S_c))`, report the slope, residuals, R-squared and number of points.
The stated slope band 1–2.5 is a testable necessary clause. The specification
gives no tolerance for "close to linear": do not invent one after seeing
the results. Linearity remains descriptive, with too few points explicitly
unassessed. Do not pool mechanisms or connectivity branches to fit this test.

**PD3.** Bracket tau_c=30 years along each continued branch. The logarithmic
dial interpolant is the specified interpolation summary; additionally refine
the dial bracket with new equilibrium/spectral solves until S_c differs by
less than 2% across the bracket (or .001 K absolutely). Interpolate only
within a qualified bracket, retaining its endpoints, all extra evaluations
and any nonmonotonicity. Values at zero dial are handled in linear dial
coordinates, because log zero is undefined. This is a threshold refinement
within the stated question, not an expanded parameter survey.

**PD4.** Compute the stated formula from the selected zero-lag pair as
`2*(-Re(lambda))/Im(lambda)^2`. Compare it with the first physical delay loss
for each eligible point below 100 years. Report formula/computed ratio,
mode identity and the finite-count pass/fail result. Missing or unstable
pairs cannot count as agreement. The weak-mode formula is an approximation;
if its assumptions fail, retain the failure rather than redefining the
chosen pair to improve it.

Selected states near zero, near the 30-year threshold and near each endpoint
receive separately assembled physical-derivative/characteristic checks.
Recheck representative D2 states on an additional mesh where a prediction
verdict could depend on numerical error. Recheck small nonzero slopes with
finite supply perturbations, without changing the equilibrium guild ratios
in the frozen comparison.

## Interpretation, provenance and stopping

C54 is a descriptive recount of the old on/off sample, not a universal or
causal trade-off theorem. Its exact and ordinary groups and six reversed
frozen-response exclusions remain explicit. New dials test the gap without
retrospectively changing that comparison.

The uncensored B2 paths can fall below one cell for both guilds, but after
the first physical loss the later environment includes impossible regrowth.
They do not establish joint finite extinction. The loss of the exact mixed
regulator and the separately censused B3 invasion-order outcomes are supported
estimands. Retain finite-record oscillations without an attracting-cycle
claim. Accept dropping the planned spatial invasions under the support gate;
linear stability does not establish a basin for a specified finite kick.

Keep source/input hashes, branch and mesh histories and selected complete
states; do not overwrite old C0/C1 or transient evidence. Archive bulky owned
data on shared project storage if needed, without a public deposit. Stop
when PD1–PD4 have qualified verdicts and an independent check. Then reconcile
scientific readiness with Claude; no manuscript drafting or automatic thesis
selection is authorised by these model runs.
