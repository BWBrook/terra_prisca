# Stage B design and independent numerical review

Codex independent subagent, 12 November 2026. This reviews the
[Stage B specification](../../models/haze_world/dynamic-realisation-spec.md)
before its decisive B1/B4 calculations. The original PB1–PB7 predictions are
retained. This note separates a meaningful test from the interpretation of
its result; no universal controller theorem is assumed.

## Design findings before numerical results

1. **The integral-control description is local and conditional.** In the
   homogeneous positive community, the exact identity is
   `d ln(X_A/X_M)/dt = n_A − n_M`. The difference in net growth depends on
   hydrogen, temperature, products and the fixed physiology. Only after
   resource elimination and local expansion can this act like an integral
   of temperature error. Atmospheric methane obeys `dr/dt = source − loss(r)`;
   its linear response has a loss term. It is not a second ideal integrator.
   Exact pinning follows from a supply-independent break-even crossing when
   coexistence is feasible. It does not itself prove a universal relation
   between static gain and delay margin. PB1 is a falsifiable model-family
   hypothesis, not an acceptance criterion deduced from control theory.
2. **The matched M-only control is useful, with a restricted interpretation.**
   Hold supply, geometry, chemistry and transport fixed, disable acetogens,
   and evaluate both equilibria on named branches. This measures the effect
   of adding acetogens relative to that biological control. The control can
   occupy a different climate segment, so its slope can differ for geometric
   reasons. Report `dT/d ln Phi` for both states along with their ratio, branch
   and stability. A zero control derivative makes the ratio undefined; do not
   call a zero-over-zero ratio perfect regulation. An absent or unsupported
   control makes the comparison unavailable. Negative ratios are allowed
   algebraically and must not be ranked as stronger attenuation without
   stating that the response changes sign. The static derivative exists for
   an unstable equilibrium, but it is not an attained static climate response.
3. **Delay-margin statuses need censoring.** No crossing found below 10,000
   years is `not detected through 10000`, not mathematical infinity. A state
   already unstable at zero thermal lag has no positive stable delay margin.
   Multiple crossings should be retained; the first loss of the stable branch
   is different from a later restabilisation. Finite bracketing is not proof
   that a narrow stability interval cannot occur between grid points.
4. **B4 has no unique ordinary equilibrium Jacobian under the stated linear
   ramp.** Entry uses `max(-n,0)`, waking uses `max(n,0)`, and the mixed
   equilibrium has `n=0`, dormant biomass zero and active biomass positive.
   To first order with switching factor k and active biomass X,

       delta X' = X delta n - k X max(-delta n,0)
       delta D' = k X max(-delta n,0) - epsilon L delta D.

   The positive- and negative-growth directional derivatives differ. A
   centered numerical Jacobian averages these branches and has no unique
   physical justification. Sector matrices can be useful diagnostics, but
   their individual spectra do not establish the stability of the switched
   system or a smooth Hopf bifurcation. Cubic entry has zero first derivative
   at the switching boundary and therefore a different local structure. A
   bank is not equivalent to a scalar thermal lag simply because both retain
   state. The bank residence time must use L in years, not its input in hours.
5. **Two-layer dynamics are under-specified.** A deep fraction and a ratio
   of time constants do not uniquely define a coupled thermal model. State
   equations, the temperature seen by microbes, coupling normalization and
   equilibrium relation must be fixed before the comparison. A parallel
   weighted two-mode response is distinct from an energy-conserving coupled
   two-box heat balance; do not label one as the other.
6. **PB1's two clauses need separate verdicts.** A failure of the chemistry
   ranking does not necessarily produce a near-pinning long-delay escape.
   Conversely, `|G| < .05` is approximate pinning, not exact pinning. A
   right-censored margin beyond 10,000 is sufficient to assess the 30-year
   threshold, but not to claim stability for arbitrarily long delays. The
   thesis rule must use the actual clause that fails.
7. **Convergence and mixed-state definitions need explicit handling.** An
   implicit derivative at a climate corner is one-sided. A 5% relative error
   at G=0 is undefined; a small absolute tolerance should be fixed. With
   nonzero exchange a guild can occur as a sink in patches where it cannot
   sustain itself, so positive biomass in every patch is not local autonomous
   coexistence. Whole-community presence, local sink stocks and regulation
   are distinct. Grid quantiles may approach physiology-domain boundaries
   as N changes, so support must be checked at each resolution.

These clarifications preserve the stated experimental scope and predictions.
They avoid interpreting a numerical absence, undefined comparison or
nondifferentiable operator as a physical result. B2/B3 remain outside this
initial static audit.

## Independent numerical checks

Pending the implementation-method freeze and production core. The planned
checks use equations assembled independently of the new solver, selected
roots/spectra, finite-supply or implicit-derivative comparisons, and source
hashes. No decisive grid result has been generated for this note yet.
