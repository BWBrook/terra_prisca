# Finite-population bottleneck test: specification

Claude (Opus 5.5), 10 November 2026. Follows the
[buffered-refuge model](buffered-refuges.md) and its
[review](review/buffered-refuges-claude-review-2026-11-10.md). Codex builds it;
Claude reviews it. The [pilot](review/bottleneck_branching_pilot.py) already
runs the method on six cases.

## Question

Which outcomes of the refuge models are robust to how extinction is decided?
Every run so far removes a guild from a habitat when a ten-year census finds
it below one cell. That rule has three weaknesses:

- it ignores demographic noise, which decides survival near the minimum;
- the census interval can miss or catch a brief dip;
- the global cell count behind "one cell" is uncertain by orders of magnitude.

This test replaces the census with a survival probability and classifies each
outcome as robust or contingent.

## Method

**Uncensored trajectories.** Rerun with the removal floor at zero and 1-year
sampling. The densities, H₂, acetate and methane then follow the continuous
equations. Removal only ever changes them after the event.

**Rare-guild branching process.** While a guild is rare, it cannot alter its
environment. Below `N_lin` cells, treat it as a linear multitype birth–death
process in the uncensored trajectory's environment. Per-cell rates in
habitat `j` come from the existing metabolism, with `s = Y (q − m)` in each
habitat:

| Process | Rate |
|---|---|
| Birth | `b_j = max(s, 0)` |
| Death | `δ_j = L + max(−s, 0)` |
| Migration `j → k` | `m_jk = d w_k`, the cell-count form of the density exchange |

`b_j − δ_j` must equal the model's net growth; assert it. The probability
`u_j(t)` that one cell's lineage is alive at `t_out` solves, backwards from
`u_j(t_out) = 1`,

    du_j/dt = −b_j u_j (1 − u_j) + δ_j u_j + Σ_k m_jk (u_j − u_k).

The expected number of surviving lineages is `Λ = Σ_j N_j(t_in) u_j(t_in)`. The
guild survives with probability `P = 1 − exp(−Λ)`. The window `[t_in, t_out]`
brackets each excursion below `N_lin`. Use `N_lin = min(10¹⁶, 10⁸ N_min)`, where
the guild's uptake is below 10⁻¹⁰ of the total. A guild that never comes back
above `N_lin` within the horizon has `P = 0`. Report it as genuine exclusion,
with its final net growth rate. Solve in `log u`, because `u` reaches 10⁻³⁰.

**Cell-count scale.** Every count is `s` times the reference conversion (cell
mass 3×10⁻¹³ gDW, habitat volume 0.00897 L cm⁻², area 5.1×10¹⁸ cm²). The
densities do not depend on `s`, so `Λ` is exactly proportional to it. Classify
over `s` from 10⁻³ to 10³, a range covering cell mass, effective habitat
volume and Archean biosphere size:

- **robust loss:** `P < 0.01` at `s = 10³`;
- **robust persistence:** `P > 0.99` at `s = 10⁻³`;
- **contingent:** anything else. Report the `s` at which `P = 0.5`.

## Experiments

**E1. Planned runs.** Rerun every main, sensitivity and control case in which
any guild was removed in any habitat. Cases without a removal are already
uncensored. The horizon is 30,000 years, extended until each rare guild either
returns above `N_lin` or shows sustained negative net growth over the final
5,000 years. Report one row per run and guild. Include `N_min`, its time,
bottleneck width `sqrt(2π/κ)`, `b` and `δ` at the minimum, `Λ`, `P`, the class,
and the census-run outcome for comparison.

**E2. Exchange continuation.** Warm-only refuges, acetogens invading
methanogens, fixed activities:

- `f ∈ {0, 0.5}`;
- warm-refuge area `w_w ∈ {0.005, 0.02}`;
- `d` from 10⁻⁹ to 10⁻³/yr at eight values per decade.

That is 196 short runs, 3,000 to 6,000 years each. Report `log₁₀ N_min`, peak
global temperature and `P` against `d`. Mark where three criteria place the
transition: a one-cell floor with ten-year censuses, a one-cell floor with
one-year censuses, and `P = 0.5`. Apply the floors after the fact to the
uncensored global trajectory.

**E3. Independent check of the survival calculation.** Take `main_0010` at the
scale where `Λ ≈ 1` (`s ≈ 3,800`). Run 10⁴ stochastic replicates of the rare
guild from the time its expected count is 10⁵ cells. Use exact or
binomial-leap birth, death and migration events in the recorded environment.
The surviving fraction must match `P` within binomial error. Also check the
backward equation against two closed forms:

- with no births, `u = exp(−∫δ)`;
- with constant and equal birth and death rates, Kendall's `1/(1 + bt)`.

## Predictions

These are fixed before the runs.

- **K1. Almost everything is robust.** Every E1 loss outside the warm-only
  `f=0` overshoot is a robust loss: deep, monotone exclusion through the
  greenhouse peak or a cold start. Every census survivor is a robust survivor;
  none has a minimum below 10¹² cells. The only contingent planned run is
  `main_0010` (`Λ = 2.7×10⁻⁴`). `main_0008` and `sensitivity_0048` are robust
  losses.
- **K2. Bottleneck depth is log-linear in exchange.** At `f=0` and
  `w_w = 0.02`, `log₁₀ N_min` rises with `log₁₀ d` at a slope of 4.4 ± 0.3 up to
  at least 10⁻⁴/yr, then flattens once the bulk methanogen floor nears its
  dominant stock. 50% survival falls between 3×10⁻⁶ and 1.2×10⁻⁵/yr.
- **K3. The criterion moves the transition only slightly.** The one-cell and
  `P = 0.5` transitions differ by a factor of 2 to 5 in `d`. The two census
  intervals differ by less than that.
- **K4. Exchange acts through the resident's floor.** The `w_w = 0.005` and
  `0.02` curves nearly collapse when plotted against `d w_w`: within one
  decade of `N_min`. Large departures mean refuge density or bulk area matters
  separately; report them.
- **K5. `f=0.5` is never contingent.** Its minimum stays above 10¹² cells at
  every `d`. Acetate-derived methane limits the overshoot.

## Not in this test

Keep these as later named variants, so that their absence stays visible:

- **Turnover.** `L` sets the switch temperature, the exclusion rates and the
  demographic noise. There is no switch below about 3×10⁻⁴ h⁻¹. This needs its
  own stage, with refuges defined relative to `T_sw(L)`.
- **Dormancy.** Cells below their H₂ threshold with reduced loss would make
  every bottleneck shallower.
- **Environmental stochasticity and shared atmospheric H₂.**

## Outputs and stopping rule

- `figures/bottleneck/survival.csv` (E1).
- `figures/bottleneck/exchange_continuation.csv` and a figure (E2).
- `review/check_bottleneck_montecarlo.py` with its JSON (E3).
- A results section on a new page, `models/haze_world/bottleneck-test.md`. Add
  `P` and the class to the buffered-refuge tables by reference, not by
  rewriting the frozen outcomes.

Stop when K1 to K5 are each confirmed or refuted with a mechanism and E3
passes. If E3 fails, fix the survival calculation before E1 and E2 are
interpreted.
