# Stage B implementation choices, frozen before B1/B4

Codex (GPT-6), 12 November 2026. This pre-run design review resolves
ambiguities in the [unchanged specification](dynamic-realisation-spec.md),
commit `98cca12`. Its PB1–PB7 predictions are retained. Only B1 and B4 are
authorised in this turn; B2/B3 and the final paper thesis remain open.
The [independent design review](../../docs/audits/dynamic-realisation-review-2026-11-12.md)
agrees with the mathematical qualifications below. These choices are a
prospective clarification, not a claim that every detail was prespecified.

## What is being tested

In a homogeneous box,

    d ln(X_A/X_M)/dt = n_A − n_M.

This integrates a fitness difference, which depends on hydrogen and chemical
products as well as temperature. Methane obeys production minus removal:
it is a leaky stock, not a second ideal integrator. The proposed frontier
is therefore an empirical hypothesis within this model family, not a
control-theory necessity. In heterogeneous boxes migration also enters the
local log-ratio balance.

Before numerical results, one algebraic possibility is already apparent:
with methane-only product feedback, both guilds' R* values depend on T and r
but not directly on population allocation or supply. Their equality together
with T=T_Arney(r) can still select a supply-independent T,r, while the direct
methane loop adds damping. PB1's near-pinning/long-lag exclusion and PB2's
methane-loop prediction must be tested separately; they need not be compatible.
This is a pre-run mechanism conjecture, not a numerical result.

## B1 definitions

- Four chemistry scenarios change only the specified product multipliers;
  the reference modules and historical results are unchanged. Methane-only
  leaves acetate activity fixed; acetate-only leaves methane activity fixed.
- Supply potential is the reference dimensionless label at a 10,000-year
  lifetime. Habitat volume, outlet and physical supply follow the established
  reference mapping. Gain derivatives vary physical supply continuously with
  all other settings held fixed.
- Uniform tracking habitats use equal weights and midpoint offsets
  `σ[2(j+1/2)/N−1]`. For σ=0 one box is sufficient; repeating identical boxes
  does not supply independent convergence evidence. Cell exchange is 0.001/year.
- No clipping is used. A continuum-support result requires the entire interval
  `[T−σ,T+σ]` to lie within 273–303.15 K. Midpoint nodes are also checked.
  An out-of-range control is reported as such, not extrapolated to create G.
- Record all admissible mixed branches found by the stated seed/bracketing
  search, including unstable ones, plus missing, pure and unresolved cases.
  Multiple roots are branch-labelled. Root residuals, stock positivity,
  domain support and numerical conditioning accompany classification.
  Finite searches are not completeness certificates for every narrow root.
- A source community and its methanogen-only control share supply, climate,
  geometry, chemistry, turnover and outlet. This is a treatment contrast, not
  a same-temperature feedback gain. Report both raw derivatives
  `dT/d ln J`, temperatures, branch/stability status and their signed ratio.
  If the control is absent, outside-domain, unstable, ambiguous, or has zero
  slope, G is undefined. Do not replace a plateau denominator by a tiny number.
  Corner derivatives are one-sided or labelled non-differentiable.
- For scalar gains near zero use a fixed absolute tolerance of 1e-4 when
  evaluating N-convergence; otherwise require the specified 5% relative
  agreement. A missing/undefined gain cannot pass a numerical convergence
  test. Censored critical lags can agree in classification without establishing
  convergence of a finite critical value.

### Lag and sensitivities

The main state is the physical ecology plus surface temperature, with
`τ_T T' = T_Arney(r)−T`. At τ_T=0 the original algebraic closure is recovered.
Record the full requested lag grid. A critical lag is the first observed
stable-to-unstable crossing, refined by root-finding. Already-unstable,
neutral/nonsmooth, and no detected crossing through 10,000 years are distinct.
The last is **right-censored**, not mathematical infinity. Later sampled
restabilisation is retained rather than hidden by a single critical value.

The two-layer wording does not uniquely define equations. Use this explicit
named diagnostic, with biology at surface temperature Ts:

    τ_f Ts' = T_Arney(r) − Ts − κ(Ts−Td)
    τ_s Td' = Ts−Td
    κ = f_deep/(1−f_deep) = 1,   τ_s = 100 τ_f.

Here f_deep=.5 is the exchange share of the fast surface restoring coefficient,
not a measured deep-ocean heat-capacity fraction. τ_f and τ_s are equation
coefficients, not the resulting eigenmode times. This preserves the same
equilibrium and supplies a defined check, not a calibrated Archean ocean.
PB4's factor-of-two clause is conditional on this realisation.

Climate-slope sensitivity changes the **local tangent**, anchored at each
equilibrium, by factors .5/1/2. It does not redraw the global Arney curve or
claim new climates. Lifetime sensitivity uses 6/10/19 kyr while holding
physical hydrogen supply, habitat volume and outlet fixed; supply labels
remain their nominal 10-kyr values. It changes the actual loss coefficient
and the equilibria are recomputed. Cover the stated σ=0, fixed/products,
f=0/.5 subset of the L/supply grid. The two-layer subset uses σ=0/3,
fixed/products, f=.5, reference L and the three supplies.

## B4: a directional diagnostic, not a fictitious Hopf calculation

At the homogeneous mixed equilibrium net growth n_i=0, active X_i>0,
dormant Z_i=0. For the existing clipped linear switching law, first-order
entry is `k X_i max(−Dn_i·δy,0)`. Waking is second order because both the
waking rate and Z vanish. The vector field has directional derivatives but
no ordinary Jacobian at this point.

Compute four directional entry-sector matrices over thirteen log-spaced ε
values from 1e-4 to .1. Each has a triangular dormant block with real decay
rates `−ε L_year`; its active block is independent of ε. Sector spectra are
diagnostics, not a theorem about switching trajectories. For the cubic ramp,
the ordinary derivative is the reference active matrix plus those real bank
decays. Thus an ε-driven local complex-pair crossing cannot be inferred from
the proposed stencil. PB7's local-Hopf mechanism can be rejected analytically
without denying the recorded nonlinear recurrent paths.

Compare each recorded cubic path's period with the thermal-lag mode at
`τ_T=1/(ε L_year)` using its own f and settings. Convert L from per hour to
per year before matching. A bank's death lifetime is not automatically its
residence time: entry and waking depend on growth along the trajectory.
Agreement within 30% would be a numerical period comparison, not proof of a
shared mechanism or an attracting cycle.

## Interpretation and stopping point for this turn

PB1 contains two different predictions: chemistry rank ordering and the
absence of a setting with `|G|<.05` and critical lag above 30 years. A rank
inversion alone is not the thesis's escaping example. A genuine counterexample
needs a qualified equilibrium, defined control gain, stability and numerical
resolution checks. If controls or N-convergence fail, report the unassessed
part rather than promoting an incomplete map to a universal frontier.

B1/B4 cannot adjudicate PB5/PB6, which require B2/B3. Report those pending,
keep the writing gate closed and hand the evidence to Claude before deciding
nonlinear scope. No public evidence deposit is made before release.
