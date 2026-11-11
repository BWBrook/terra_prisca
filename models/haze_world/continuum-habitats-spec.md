# Stage B′: continuum habitats and the local gain

Claude (Opus 5.5), 12 November 2026. Follows my
[review of B1 and B4](review/dynamic-realisation-claude-review-2026-11-12.md),
which found that the B1 habitat grids do not resolve the zone where each
habitat switches guild. That zone has a width proportional to cell exchange
`d`. This stage replaces those grids with a resolved calculation, sweeps `d`,
and introduces the local gain `G_loc`. Codex builds it; Claude reviews it.
B2 and B3 at `σ = 0` may run alongside.

## Model change (a named variant)

- **Weighted habitats.** Use nodes `δ_j` with weights `w_j`, where
  `Σ w_j = 1`, approximating the uniform distribution on `[−σ, σ]`.
  - Dispersal goes to the weighted mean biomass.
  - Methane production is the weighted sum.
  - The existing equal-weight midpoint grid is the special case
    `w_j = 1/N`, and must reproduce B1 exactly as a regression test.
- **Mesh.** Use composite Gauss–Legendre panels, with fixed order and at
  least four nodes per panel.
  - Refine panels adaptively until no panel's local acetogen share changes
    by more than 1 in logit units across it.
  - Then confirm by doubling the panel count inside the mixed zone.
- **Converged** means `S_c`, `S_0` and τ_c each change by less than 2% on
  doubling, with an absolute tolerance of 10⁻³ K for slopes near zero.
  Censored τ_c values must agree in classification.
- **Seeds.** Start from the homogeneous homotopy, as in B1, then interpolate
  the share profile onto the refined mesh.
- **Domain.** Apply the B1 support rules unchanged.

## Estimands (fixed before computing them)

All are reported per qualified equilibrium.

- **`S_c = dT*/d ln J`.** The raw community supply slope, by implicit
  differentiation.
- **`S_0`.** The same derivative with each habitat's ratio `X_A,j / X_M,j`
  frozen at equilibrium.
  - Implement it by replacing each habitat's two biomass equations with
    their weighted sum.
  - Check it by finite supply perturbation of the frozen-ratio system.
- **`G_loc = S_c / S_0`.**
  - Where the climate slope is zero, report the point as climate-insensitive.
  - At a corner, use one-sided derivatives.
  - The matched methanogen-only G remains a secondary column, with its B1
    statuses.
- **Critical lag τ_c.** Use the B1 lag grid and root-finding, with
  right-censoring at 10⁴ yr. Also report:
  - the leading eigenvalue at τ_T = 0;
  - the edge of the slow sink-population spectrum, `max_j` of the slowest
    local decay rate;
  - the width of the mixed zone, with local share between 1% and 99%.

## Independent check

A separate implementation computes τ_c for at least six settings by a
**characteristic-function route**.

- The linearised system is block-diagonal across habitats, coupled only
  through four quantities:
  - the weighted mean acetogen biomass;
  - the weighted mean methanogen biomass;
  - the methane ratio;
  - lagged temperature.
- Eliminate the local blocks by quadrature of `(λI − J_j)⁻¹`. That leaves a
  4×4 determinant `Δ(λ; τ_T)`.
- The critical lag is where `Δ(iω; τ_T) = 0` has a real solution `ω`.
- Choose the six settings to include `d = 10⁻⁴` and `σ = 6 K`.
- The check passes if both routes agree within 2%.

This route sees the continuum without eigen-decomposing a large matrix. It
also separates discrete roots from the sink-population continuum.

## Grid

**C1, the resolved map:**

| Factor | Values |
|---|---|
| Chemistry | fixed, products |
| `f` | 0, 0.5 |
| `σ` | 1, 3, 6 K |
| `d` | 10⁻⁴, 10⁻³, 10⁻², 10⁻¹ yr⁻¹ |
| Turnover and supply | reference |

That is 48 settings, plus one supply sweep at {0.24, 0.30, 0.36} for
`σ = 3 K` and every `d`.

**C0, the homogeneous gain.** Compute `G_loc` at every accepted `σ = 0` B1
equilibrium, across all four chemistries and the full f, L and supply grid.
This is cheap.

## Predictions (fixed before C0 and C1)

- **PC1. Resolution.** The adaptive mesh converges by the rule above in every
  setting inside the support domain, including `d = 10⁻⁴`.
- **PC2. The width of the zone.** The mixed-zone width is proportional to
  `d`, within a factor of 1.5 of linear from 10⁻⁴ to 10⁻², at each `σ` and
  chemistry.
- **PC3. The frontier (PB1 restated).** No resolved setting in C0 or C1 has
  `|G_loc| < 0.05` together with τ_c > 30 yr.
- **PC4. Connectivity buys robustness.** With fixed chemistry, τ_c does not
  decrease as `d` increases at any `σ`, and τ_c is finite (below 10⁴ yr) at
  `d = 10⁻⁴` for every `σ`.
  - The reason: re-seeding at rate `d` is how a habitat changes sides, so slow
    re-seeding acts as a lag on the proportional term.
- **PC5. Spread costs pinning.** With fixed chemistry, `G_loc` lies between
  0.05 and 1 for every `σ > 0`, and rises with `σ` at fixed `d`.
- **PC6. Spread does not undo acetate damping.** With products chemistry,
  τ_c is right-censored in every C1 setting, and `G_loc` is at least the
  homogeneous value.

## What follows

- **Frontier and connectivity both hold (PC3 and PC4).** The thesis is the
  pinning–robustness trade-off. Connectivity is the link to the
  invasion and memory results, because it sets both how fast spatial
  regulation acts and how a displaced guild returns. This is the candidate
  unifying story, and B3 then tests it directly.
- **PC3 fails.** The escaping setting is the paper, as before.
- **PC4 fails.** Spatial regulation is robust whatever the connectivity.
  Memory is then a separate, secondary result.

**B2 and B3 for `σ > 0`** run after C1. They use the two `d` values that C1
shows bracket the change in regime, together with the B3 pruning recorded in
my review.

**Stopping rule.** Stop when PC1–PC6 are each confirmed or refuted with a
mechanism. Add no new physics, demography or evolution.
