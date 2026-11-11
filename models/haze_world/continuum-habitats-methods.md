# C0/C1 and homogeneous B2/B3: pre-run implementation choices

Codex (GPT-6), 12 November 2026. This reviews and operationalises the
[Stage B′ specification](continuum-habitats-spec.md), commit `1077f03`.
PC1–PC6 and PB5/PB6 remain unchanged. These clarifications precede the new
decisive maps and trajectories; prototype identities and mathematical review
are not empirical confirmations of the predictions.

## Frozen local composition

For habitat j define B_j=X_A,j+X_M,j and c_j=X_A,j/B_j at the original
equilibrium. Freeze c_j, lift X_A,j=c_j B_j and X_M,j=(1−c_j)B_j, and use
the **sum** of the original two biomass flows as B_j'. This sum includes
immigration/emigration. Quadrature weights enter habitat means and global
production, not a rescaling of each habitat's time derivative.

If E lifts reduced perturbations and P sums the original biomass rows, the
frozen Jacobian is P J E. The original equilibrium is preserved, and hydrogen,
total biomass, acetate, methane and temperature can still respond. The result
is an intervention-defined counterfactual, not a naturally evolved community.

This removes within-habitat sorting, but global composition may still change
through redistribution of B_j among habitats having different fixed c_j.
It therefore does **not** remove all geographical composition feedback.
Freezing only the global share would leave compensating local sorting and
would be a different counterfactual; it is not substituted here.

Report S_c, S_0 and their signed ratio separately. A shared operating point
does not prove that the projected Jacobian is invertible or S_0 nonzero.
Plateaus are climate-insensitive; singular, nearly singular, zero-denominator
and corner cases retain explicit statuses. Report frozen-system stability
separately. An algebraic derivative at an unstable counterfactual is not an
attained steady-climate response. Finite supply checks keep each original c_j
fixed and use symmetric log-input perturbations, with a smaller perturbation
control when slopes disagree. They do not recompute the frozen ratios.

## Weighted continuum and resolution

Use order-four Gauss–Legendre quadrature on panels in [−σ,σ], normalised
to the uniform distribution. Weights sum to one; exchange is
d(Σ_k w_k X_i,k−X_i,j), and global methane flux is the weighted mean.
Equal-weight midpoint nodes must recover the existing B1 equations and
derivatives without modifying that source epoch.

Adapt panels where local logit(c) changes by more than one. Evaluate panel
endpoints as well as quadrature nodes so a narrow transition cannot hide
between all four interior nodes. Retain rare positive stocks logarithmically
and enforce actual per-capita residuals; a small absolute biomass flow does
not establish an equilibrium. No ecological extinction floor enters C0/C1.

The static panel rule is necessary numerical guidance, not proof of dynamic
resolution. Re-solve after doubling the panels in the mixed zone. Slopes must
agree within max(0.001 K, 0.02 times their magnitude), finite critical lags
within 2%, and censored values in classification. Mark a failed or resource-
limited check unresolved. The full distribution support, not only its nodes,
must remain in 273–303.15 K under the named cold continuation; do not clip.

The mixed zone is the union of offsets with 0.01<c<0.99; report its total
length and any disconnected components. PC2 compares widths to the linear
extrapolation from d=1e-4 at fixed chemistry/f/σ, with the stated factor1.5.
If the zone is absent, zero-width or saturates the support, report that
structure rather than silently fitting a power law through it.

## Stability and independent characteristic check

The primary route uses the full weighted linearised operator, with structured
local-block solves rather than an unbounded dense matrix. Recover small-node
full dense identities and monitor the local-block sink-spectrum edge. Search
the specified lag grid and refine detected crossings. Already unstable,
neutral, finite crossing, no detected crossing through 10,000 years and solver
failure are distinct statuses; finite scans do not prove infinite stability.

The independent implementation eliminates each local four-stock block and
forms a four-by-four characteristic matrix for mean acetogens, mean
methanogens, shared methane and temperature. It reconstructs physical
derivatives independently. Validate singular-value residuals, local-block
poles and backsubstituted full eigenvectors. A determinant zero produced by
a pole is not an eigenvalue. Frequency-range and frequency-grid sensitivity
are recorded, and unresolved meshes do not count as successful independent
checks.

The six prescribed checks, at reference turnover/input, are:

| Chemistry | f | σ, K | d, year⁻¹ |
|---|---:|---:|---:|
| fixed | .5 | 1 | 1e-4 |
| fixed | .5 | 3 | 1e-4 |
| fixed | .5 | 6 | 1e-4 |
| fixed | 0 | 3 | 1e-3 |
| fixed | .5 | 3 | 1e-2 |
| products | .5 | 6 | 1e-4 |

Finite margins must agree within 2%. For right-censored cases compare both
classifications and selected full-operator spectra, without claiming a
finite margin agreement. The main C1 grid has 48 settings; the σ=3 supply
sweep crosses both chemistries and f values, adding32 distinct settings at
inputs .24 and .36. Multiple supported branches remain separate records.

## Homogeneous nonlinear runs

B2 uses the instability-qualified homogeneous settings in the original B1
grid, with a 0.001 log-acetogen kick, a30,000-year horizon and no census.
B3 has24 cases: two directions, f=0/.5, τ=0/3/30 and fixed/products.
Residents and the1e-12 gDW/L invader dose follow the existing reference
protocol. Each has an uncensored trajectory and a separate one-cell,
ten-year-census trajectory, to100,000 years unless stationarity is qualified.
Use explicit biological temperature under finite lag; do not recompute T(r)
inside the per-cell birth/death rates.

Checked accepted-step dense minima, thermal/chemical domain checks, tight-step
controls and retained rare-population logs distinguish numerical failure from
finite-population loss. Report finite oscillation envelopes, continued growth
and subcell minima without claiming an attracting cycle from a finite record.

For conditional first-window survival reuse the current bottleneck criterion:
N_lin=min(1e16,1e8 N_min), reduced by decades until the guild's local/global
uptake is at most1e-10 of the total. Use the first declining excursion and
existing birth/death split. A terminal excursion is horizon-censored, not
automatic proof of permanent exclusion or exactly zero survival. Flag other-
guild likely loss and later continuum regrowth; an exogenous first-window
probability is not joint community recovery or a coupled extinction result.

## Claims and stopping point

PC3 tests the new local-gain estimand, not a retrospective confirmation of
old matched-control PB1. Near-zero gain is not exact pinning. A valid escape
needs qualified slopes, supported equilibrium, resolved quadrature and the
independent stability check. Unsupported/undefined cases cannot support a
universal frontier. Likewise, failure of PC4's monotonicity does not logically
imply that spatial regulation is robust at every connectivity.

Keep connectivity, local chemical self-limitation, steady-state regulation,
finite assembly and finite survival as separate quantities until the evidence
connects them. Do not select the paper thesis mechanically from an unresolved
or numerically ill-conditioned case. Writing readiness stays withdrawn, and
no manuscript products or public deposit are authorised by this build.
