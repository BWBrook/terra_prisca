# Stage B″: crossing the gap between exact and graded regulation

Claude (Opus 5.5), 12 November 2026. Follows my
[review of Stage B′](review/continuum-habitats-claude-review-2026-11-12.md).
Among the resolved states:

- every exactly pinned state (`S_c = 0`) loses stability at τ_c ≤ 7.1 yr;
- every ordinary graded state has `|S_c| ≥ 0.59` K per e-fold and
  τ_c ≥ 331 yr.

Nothing lies between, because each tested mechanism is either on or off. This
stage turns two mechanisms up continuously from zero. It decides whether
robustness rises continuously out of the exact limit, or appears all at once.
Codex builds it; Claude reviews it.

## Dials (named variants; the reference is unchanged)

1. **Product-feedback strength, D1.**
   - **Change:** the acetogen threshold becomes
     `h_A · (acetate/acetate_ref)^(κ/4)`. Methane activity stays fixed. At
     κ = 0 this is `fixed` chemistry, and at κ = 1 it is `acetate_only`.
   - **Values:** κ ∈ {0, 10⁻⁴, 3×10⁻⁴, 10⁻³, 3×10⁻³, 10⁻², 3×10⁻², 0.1,
     0.3, 1}.
   - **Setting:** homogeneous, f ∈ {0, 0.5}, reference L and supply.
2. **Spread width, D2.**
   - **Change:** fixed chemistry.
   - **Values:** σ ∈ {0.003, 0.01, 0.03, 0.1, 0.3, 1} K.
   - **Setting:** f = 0.5, d ∈ {10⁻⁴, 10⁻³} yr⁻¹, reference L and supply.
   - **Method:** the Stage B′ adaptive mesh and convergence rule. At
     σ ≪ the mixed-zone width, the mesh must still pass doubling.

That gives 32 settings. Follow each branch by continuation in the dial from
the exact-pinning state, and record any fold or branch loss.

**Report for each setting:**

- `S_c`, `S_0` and `G_loc`;
- τ_c on the B1 lag grid with root-finding;
- at τ_T = 0, the frequency of the leading complex pair and its damping time
  `t_d = −1/Re λ`;
- the frequency at the critical lag.

## Predictions (fixed before running)

- **PD1. Continuity.** Along every dial branch, τ_c is non-decreasing in the
  dial. It rises from the exact-pinning value without a jump. Between
  adjacent dial values, τ_c changes by less than a factor of 10, until
  right-censoring.
- **PD2. Shape.** Where 2 yr < τ_c < 10³ yr, `ln τ_c` against `ln |S_c|` is
  close to linear, with slope between 1 and 2.5, on every dial branch.
- **PD3. The price of 30 years.** On every dial branch, interpolate the
  `|S_c|` at which τ_c reaches 30 yr. It lies between 0.05 and 0.5 K per
  e-fold of supply.
- **PD4. Weak-mode theory.** For every point with τ_c < 100 yr, the formula
  `τ_c ≈ P²/(2π² t_d)` agrees with the computed τ_c within a factor of 2.
  P and `t_d` are the τ_T = 0 period and damping time.

## What follows

- **PD1–PD3 hold: "cheap but not free" robustness.** The paper's
  regulation result is the curve. Exact competitive pinning is a fragile
  singular limit, and a small, calculable residual sensitivity buys lag
  robustness.
  - PD4 then supplies the analytic explanation through damping time and
    period.
  - The homogeneous B2 result supplies the cost of fragility: about 1 K
    oscillation just past τ_c, and extinction at decadal lags.
- **PD1 fails by a jump.** Robustness is effectively free: any graded term
  suffices. The paper then says exact pinning is a non-generic limit, and
  regulation in practice is graded.
- **Either way,** the assembly result (PB6, invasion-order endpoints) and
  the earlier memory stages form the second part. Uniform-spread spatial
  invasions are dropped, for the reasons in the review.

**Stopping rule.** Stop when PD1–PD4 are each confirmed or refuted. After
this stage, Claude and Codex assess writing readiness together. If they
agree, Claude reports "ready to write" to Barry.
