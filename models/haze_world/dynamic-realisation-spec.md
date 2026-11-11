# Stage B: dynamic realisation of the competitive thermostat

Claude (Opus 5.5), 12 November 2026. This specification answers findings
X1–X3, X15 and X16 of the
[external-review triage](../../docs/audits/haze-world-external-review-triage-2026-11-11.md),
as amended by [Codex's reconciliation](../../docs/audits/haze-world-external-review-codex-2026-11-11.md).
Codex builds it; Claude reviews it. **The outcome decides the paper's
thesis.**

## The idea under test

The reviews found three things:

- a thermal lag destabilises the reference mixture;
- product chemistry keeps it stable but gives up exact pinning;
- habitat spread helps at short lags but not at long ones.

One hypothesis explains all three. **Competitive exclusion is integral
control.** At a fixed temperature away from the switch, the guild share
`s` keeps changing until temperature returns exactly to `T_sw`, so `s`
integrates the temperature error.

- Methane then integrates `s`, and temperature follows methane.
- That double integration gives zero steady-state error, so the set point
  is exactly pinned. It also gives a weakly damped loop (Q ≈ 128) with
  almost no phase margin to spend on a lag.
- Any mechanism that makes the share a *graded* function of temperature
  adds proportional action. That trades pinning for phase margin. Two such
  mechanisms are present:
  - **Product feedback.** Each guild's threshold rises with its own product,
    so it limits itself.
  - **Habitat spread.** Each habitat flips at a different global
    temperature.

Control theory predicts a **trade-off frontier**. Exact pinning comes with a
short critical lag, and robustness to lag comes with a non-zero static gain
against supply. Stage B maps that frontier and tests whether any setting in
this model escapes it.

One detail of the product variant needs separating out. Under
`activity_feedback="products"`:

- the acetogen threshold scales with local acetate to the power ¼;
- the methanogen threshold scales with **atmospheric methane** to the power
  ¼.

The second is a thermodynamic loop from methane straight back to methane
production. It bypasses temperature, so no thermal lag can delay it.
Stage B must find out how much of the product variant's stability comes
from that loop rather than from proportional *climate* regulation.

## Model additions (named variants; the reference stays unchanged)

1. **Thermal response.** Add one state:

       dT/dt = [T_Arney(r) − T]/τ_T

   Every biological flux uses `T`, and every equilibrium is unchanged. Also
   run a two-layer check: a fast surface layer `τ_f` coupled to a slow deep
   layer, with deep fraction 0.5 and `τ_s = 100 τ_f`, at the settings named
   in B1.
2. **Habitat spread.** Use `N` tracking habitats of equal weight, with
   offsets `δ_j` at the midpoint quantiles of a uniform distribution on
   `[−σ, σ]`. Local temperature is `T + δ_j`. Hydrogen and acetate stay
   local, methane is shared, and cells exchange at `d = 10⁻³ yr⁻¹`.
   - **Convergence.** Use `N = 9`, then check with `N = 17` and `N = 33`.
     Treat results as converged when the critical lag and gain change by
     less than 5% between 17 and 33.
   - **Temperature domain.** Use no clipping. Within the declared physiology,
     273.0–303.15 K including the named continuation, every habitat must stay
     in range. Report any setting or trajectory that leaves it as
     domain-censored. `σ ≥ 10 K` appears only as a flagged, clipped
     diagnostic.
3. **Product chemistry decomposition.** Run four chemistry variants:
   - `fixed`;
   - `products`;
   - `acetate_only`: only the acetogen threshold responds;
   - `methane_only`: only the methanogen threshold responds.

## Experiments

Each experiment yields four outcomes, kept separate as Codex asked:

- **(S)** fixed-point stability;
- **(G)** static gain against supply;
- **(O)** bounded finite oscillation;
- **(F)** finite invasion survival.

### B1. Stability and gain map (static; cheap)

**Grid:**

| Factor | Values |
|---|---|
| Chemistry | the four variants above |
| `σ` | 0, 1, 3, 6 K |
| `f` | 0, 0.5, 0.9 |
| `L` | 5×10⁻⁴, 10⁻³, 2×10⁻³ h⁻¹ |
| Supply potential | 0.24, 0.30, 0.36 |

**At every mixed equilibrium that exists, report:**

- **(S)** The leading eigenvalues of the lagged system at `τ_T` = 0, 0.03,
  0.1, 0.3, 1, 3, 10, 30, 100, 300 and 1000 yr.
- **(S)** The critical lag `τ_c`, located by root-finding. Report `∞` when no
  crossing occurs up to 10⁴ yr.
- **(G)** The static gain
  `G = (dT*/d ln Φ)_community / (dT*/d ln Φ)_matched methanogen-only control`,
  by implicit differentiation. The control uses the same chemistry and `σ`.
  `G = 0` is perfect pinning and `G = 1` is no regulation.
- **(G)** The supply band over which the mixed state exists.

**Climate-closure sensitivity.** For `σ = 0`, at `f` = 0 and 0.5, `fixed`
and `products` chemistry:

- local segment slope × 0.5, 1 and 2;
- methane lifetime 6, 10 and 19 kyr.

**Two-layer check.** Run it at `σ` = 0 and 3 K, `fixed` and `products`,
`f` = 0.5 and the reference `L`.

### B2. Bounded oscillation (nonlinear; moderate)

**Where.** Wherever B1 finds instability at `τ_T` ∈ {1, 10, 100} yr, for
`σ` ∈ {0, 3, 6} K and `f` ∈ {0, 0.5}, at the reference `L` and supply.

**How.** Integrate for 30 kyr from a 0.1% kick in log acetogen biomass.
Use the qualified positive-coordinate solver, with the one-cell ten-year
census switched off.

**Report:**

- the final-window temperature span;
- the per-guild global minimum cell counts;
- whether the envelope still grows, is bounded, or crosses below one cell.

### B3. Finite invasion survival (nonlinear; heaviest)

**Grid:**

- both invasion directions, with the existing doses;
- `f` ∈ {0, 0.5};
- `τ_T` ∈ {0, 3, 30} yr;
- `σ` ∈ {0, 3, 6} K;
- `fixed` and `products` chemistry;
- reference `L` and supply.

That gives 72 runs, each 100 kyr long or until stationary.

**Report:**

- the global minimum of the displaced guild, uncensored;
- the first-window survival probability, using the existing branching
  module and the X13 caveat;
- the endpoint class with the one-cell census switched on.

### B4. Dormancy cycles as a lag (X15, R13; cheap)

**Linear analysis.** Take the well-mixed mixed state at `f = 0` and the
reference `L`, with instantaneous temperature. Use the **linear** switching
ramp, whose slope at `g = L` is non-zero. Compute the leading eigenvalues for
`ε` from 10⁻⁴ to 10⁻¹. Report whether a complex pair destabilises as the
bank lifetime `1/(εL)` grows.

**Comparison with the recorded cycles.** Compare the recorded cubic-ramp
cycle periods with the lagged-system periods at `τ_T ≈ 1/(εL)`.

## Predictions (fixed before B1–B4)

Three numbers here come from earlier checks: the critical lags of 0.149 and
1.10 yr, the product-variant gain of 0.14, and the nine-box eigenvalues.
Everything else is untested.

- **PB1. A pinning–robustness frontier.** Within each `σ`, ranking
  chemistries by `G` also ranks them by `τ_c`. No setting combines
  `|G| < 0.05` with `τ_c > 30 yr` in any chemistry variant, at any `σ`, `f`
  or `L`.
- **PB2. The methane loop does most of the stabilising.**
  - `methane_only` is stable at every lag on the grid wherever its mixed
    state exists.
  - `acetate_only` has a finite `τ_c` at `f = 0`, at least ten times the
    `fixed` value.
  - The full `products` variant has `G` between 0.05 and 0.4 throughout.
- **PB3. Spread helps at short lags only.** With `fixed` chemistry, `τ_c`
  rises with `σ` but stays below 30 yr for `σ ≤ 6 K`. `G` rises with `σ`,
  above 0.2 at `σ = 6 K`. N-convergence holds at `N = 33`.
- **PB4. Sensitivity of the critical lag.** With `fixed` chemistry and
  `σ = 0`:
  - `τ_c` stays below 5 yr for every combination of slope and lifetime at
    `f ≤ 0.5`;
  - `τ_c` falls as the slope steepens;
  - the two-layer check agrees within a factor of 2 with the one-box `τ_c`,
    using `τ_f` as the lag.
- **PB5. Instability under a lag crashes populations.** With `fixed`
  chemistry, `σ = 0` and `τ_T ≥ 1 yr` at `f = 0`, B2 trajectories drive a
  guild below one global cell within 20 kyr. With `σ = 6 K` at
  `τ_T = 100 yr`, the oscillation stays bounded with both guilds above
  10¹⁰ cells.
- **PB6. Invasion bottlenecks survive realism.** In B3, at least one
  invasion direction reaches a displaced-guild minimum below one global cell
  in every `σ ≤ 6 K` setting, with or without product feedback and with or
  without a lag. Exclusion near the resident world is fast whatever happens
  at the switch.
- **PB7. The dormant bank acts as a lag.** Under linear switching, the
  dormancy mixed state has a complex pair that destabilises once `ε` falls
  below 10⁻². Recorded cycle periods fall within 30% of the lagged-system
  periods at the matched `τ_T`.

## How the thesis is chosen

- **If PB1 holds,** the paper's core is the **pinning–robustness trade-off
  of competitive climate regulation**. Exclusion supplies integral control
  and exact pinning. Graded mechanisms (product thermodynamics, habitat
  heterogeneity) buy stability by giving up pinning. The existence
  conditions come from Stage C, and evolution is a section.
  - If PB6 also holds, finite invasion and "memory" stay as a secondary
    result about assembly, independent of the frontier.
  - If PB6 fails, memory drops to the supplement.
- **If PB1 fails,** a setting combines exact pinning with long-lag
  robustness. That setting becomes the paper, and we find out why it
  escapes the frontier.
- **If PB2 shows the methane loop does nearly all the stabilising,** the
  stable regulator is largely chemical. The paper must then say so and
  quantify the share of buffering that passes through temperature.

## Outputs and stopping rule

- **Outputs:**
  - `figures/dynamic_realisation/`, containing `stability_gain.csv` (B1),
    `oscillations.csv` (B2), `invasions.csv` (B3), `dormancy_lag.csv` (B4)
    and manifests;
  - a frontier figure of `G` against `τ_c`, coloured by mechanism;
  - a page, `models/haze_world/dynamic-realisation.md`;
  - ledger rows for PB1–PB7;
  - estimands updated to mark stability claims as lag-qualified.
- **Order.** Run B1 and B4 first and report them before B3. If B1 already
  decides PB1 and PB2 clearly, B3 can drop the `σ = 1` setting and any
  chemistry B1 has made irrelevant. Record any such change before B3 runs.
- **Stopping rule.** Stop when PB1–PB7 are each confirmed or refuted with a
  mechanism. Do not add stochastic demography, evolution, or new
  photochemistry or ocean physics in this stage.
