# Turnover and dormancy: specification

Claude (Opus 5.5), 10 November 2026. Follows the
[bottleneck test](bottleneck-test.md) and its
[review](review/bottleneck-test-claude-review-2026-11-10.md). Codex builds it;
Claude reviews it. The [regime preview](review/turnover_regime_preview.py)
already maps the well-mixed equilibria on a coarse grid.

## Questions

1. How does cell turnover `L` set the haze-world thermostat: its existence,
   its set point and its uniqueness?
2. Do the buffered-refuge results hold away from `L = 10⁻³ h⁻¹`, with refuges
   fixed in temperature, or with refuges fixed relative to `T_sw(L)`?
3. Can a dormant seed bank do what the refuges did? Does it give two-way
   rescue without spatial structure, and how long must dormant cells last?

## What the preview already shows

Well-mixed, full local stability, 43 values of `L` from 2×10⁻⁴ to 5×10⁻³
h⁻¹:

- Below `L = 2.44×10⁻⁴ h⁻¹` there is no switch. Methanogens win at every
  temperature and the planet is hazy at 274.0 K.
- From 2.44×10⁻⁴ to 1.24×10⁻³ h⁻¹, at `f = 0` and `0.5`, one stable mixed state
  regulates the climate at `T_sw(L)`, from 274.5 to 283.2 K.
- At `f = 0` above 1.24×10⁻³ h⁻¹, `T_sw` exceeds the 283.2 K of the
  acetogen-only world (abiotic methane only). That state becomes stable as
  well, so the system is bistable. At `f = 0.5` bistability begins near
  3.0×10⁻³ h⁻¹.
- At `f = 0.9` the stable state is acetogen-only from 2.44×10⁻⁴ to about
  3×10⁻³ h⁻¹.
- Above about 4.3×10⁻³ h⁻¹, acetogens win everywhere.
- `T_sw` crosses the absolute refuge temperatures at `L = 4.34×10⁻⁴` (278 K)
  and `1.88×10⁻³ h⁻¹` (286 K).

## Experiments

### T1. Regime map (deterministic, well-mixed)

- `L` from 10⁻⁴ to 10⁻² h⁻¹ at 24 values per decade, and
  `f ∈ {0, 0.25, 0.5, 0.75, 0.9}`.
- Report every equilibrium with its stability and temperature, and the regime
  class.
- Locate each bifurcation in `L` by root-finding, not by grid.
- Where two states are stable, check basins by integration. Run the
  resident-plus-invader start in both directions with the planned doses.
  Also perturb the mixed state by ±1% in each guild.
- Explain the mechanism. Plot `R*_A(T)` and `R*_M(T)` at three values of `L`,
  and say which guild properties make the switch rise with turnover: yield,
  maintenance, kinetic constants or thermodynamic threshold. The rise comes
  through the required uptake `m + L/Y`.

### T2. Refuges across turnover

- `L ∈ {3, 5, 7, 10, 15, 20, 30} × 10⁻⁴ h⁻¹`, `f ∈ {0, 0.5}`, both invasion
  directions, the existing doses and the 100,000-year protocol with
  stationarity checks.
- Configurations:
  - **none**: 28 runs;
  - **both, absolute**: 278 and 286 K, 2% each;
  - **both, relative**: `T_sw(L) − 3.535 K` and `T_sw(L) + 4.465 K`, 2% each,
    the same offsets as the reference;
  - **warm only, relative**: 2%.
- Refuged runs use `d ∈ {10⁻⁶, 10⁻³}/yr`, which gives 168 runs. The total is
  196.
- **Outcome rule.** Keep the one-cell, ten-year census so that results stay
  comparable with every earlier stage. Classify each census removal by its
  first-window survival probability with the existing bottleneck module:
  robust loss, contingent or robust persistence over `s = 10⁻³–10³`.
  Report later windows as conditional only, for the reason in review §2.

### T3. Dormancy (named variant `dormancy`)

Each guild in each habitat has active cells `X` and dormant cells `Z`. With
synthesis `g = Y(q − m)` per hour, as in the reference:

    dX/dt = (g − L) X − σ X + ρ Z + exchange
    dZ/dt = σ X − ρ Z − εL Z + exchange
    σ = σ_max · c((L − g)/L),   ρ = ρ_max · c((g − L)/L)

- `c` is a continuous ramp from 0 at 0 to 1 at 1; a smooth version is
  acceptable if it is documented.
- Cells enter dormancy only while the active population is shrinking, and
  wake only while it would grow.
- Dormant cells take up no H₂, need no maintenance, make no products and
  exchange at the same `d`. Census and survival count `X + Z`.
- At any equilibrium where a guild is resident, `g = L`, so `σ = ρ = 0`.
  **The variant therefore leaves every equilibrium, `T_sw` and the T1 map
  unchanged.** Assert this.
- **Grid.** `L = 10⁻³ h⁻¹`, `f ∈ {0, 0.5}`, both directions, and
  `ε ∈ {10⁻¹, 3×10⁻², 10⁻², 3×10⁻³, 10⁻³, 3×10⁻⁴, 10⁻⁴}`, with
  `σ_max = ρ_max = 10 L`.
  - Configurations: none; warm only, 2%, at `d ∈ {10⁻⁹, 10⁻⁶}`; and both,
    2%, at `d = 10⁻⁶`. That gives 112 runs.
  - Slow switching (`σ_max = ρ_max = L`), no refuges, `ε ∈ {10⁻², 10⁻³,
    10⁻⁴}`: 12 runs.
  - A bistable check at `L = 2×10⁻³`, `f = 0`, no refuges,
    `ε ∈ {10⁻², 10⁻³}`, both directions: 4 runs.
- **Branching.** Extend the backward equation to two types per habitat.
  - The active type has birth `b`, death `δ` and conversion `σ` to dormancy.
  - The dormant type has death `εL` and conversion `ρ` back to active.
  - Recheck the closed-form controls. Check that `σ = ρ = 0` reproduces the
    reference probabilities exactly.

## Predictions

These are fixed before the runs. Numbers marked as preview values come from
[turnover_regime_preview.json](review/turnover_regime_preview.json).

- **KT1. Turnover sets the thermostat** (T1).
  - The regime boundaries fall within 2% of the preview values: 2.44×10⁻⁴,
    1.24×10⁻³ (`f = 0` bistability), and about 3.0×10⁻³ h⁻¹ (`f = 0.5`
    bistability).
  - In the bistable range, basin checks reach both attractors. Acetogens
    invading a methanogen world reach the mixed state. Methanogens cannot
    invade the 283.2 K acetogen world, which is colder than `T_sw`.
  - The set point rises monotonically with `L` wherever the mixed state
    exists, by about 20 K over a 16-fold range of turnover.
- **KT2. Absolute refuges rescue only in a window** (T2).
  - Two-way rescue to one mixed state requires `278 K < T_sw(L) < 286 K` and
    no stable alternative state. That means `L` from 4.34×10⁻⁴ to 1.24×10⁻³
    h⁻¹ at `f = 0` (grid points 5, 7 and 10 × 10⁻⁴), and from 4.34×10⁻⁴ to
    1.88×10⁻³ h⁻¹ at `f = 0.5` (adding 15 × 10⁻⁴).
  - At `L = 3×10⁻⁴`, both refuges favour methanogens. Acetogens displaced from
    their own world are lost as they are without refuges.
  - At `f = 0` and `L ≥ 1.5×10⁻³`, a methanogen invasion leaves the bulk
    acetogen-only, with methanogens confined to the warm refuge.
- **KT3. Relative refuges keep the geometry, not the outcome** (T2).
  - Two-way rescue holds at every grid `L` where the mixed state is the only
    stable bulk state.
  - It fails at `f = 0` for `L ≥ 1.5×10⁻³`, as in KT2. With both refuges in
    place, history dependence returns through climate bistability.
- **KT4. The demographic threshold has a closed form.** For every census
  removal with a single minimum, `N₅₀ = ln 2 · δ_min · W` matches the exact
  first-window value within 10%. Report `W` against `L`.
- **KD1. Dormancy leaves the stationary states alone.** The equilibria and
  `T_sw` match the reference to solver tolerance. Wherever the reference run
  had no census removal, the 100,000-year endpoints match.
- **KD2. Dormancy removes the overshoot loss.** With warm-only refuges at
  `f = 0`, `d = 10⁻⁹` and `ε ≤ 10⁻¹`, the acetogen minimum stays above 10¹³
  cells, robust persistence. The reference reaches 10^−14.25. Dormant decay
  at `εL` replaces the 31-decade active decline.
- **KD3. A seed bank replaces refuges, but asymmetrically.**
  - Without refuges, the displaced resident survives if
    `εLτ < ln(N₀/N₅₀)`.
  - `τ` is the time to the reference minimum, and `N₀ ≈ 10^25.9` cells. That
    gives `ε* ≈ 6.2/τ`, with `τ` in years.
  - From the bottleneck-test rows, the predicted thresholds are:

    | Displaced resident | `f = 0` | `f = 0.5` |
    |---|---:|---:|
    | Methanogens (`τ` = 1,029 and 2,501 yr) | 6.0×10⁻³ | 2.5×10⁻³ |
    | Acetogens (`τ` = 13,459 and 7,498 yr) | 4.6×10⁻⁴ | 8.2×10⁻⁴ |

  - These are lower bounds: a larger surviving stock regrows sooner and so
    shortens the climate swing. The measured `ε*` lies between 1
    and 3 times each value.
  - Two-way rescue without refuges therefore needs dormant half-lives of
    roughly 170 years or more at `f = 0`. The acetogen resident, whose
    suppression spans the greenhouse peak, sets the requirement.
- **KD4. Switching speed hardly matters.** Slow switching moves `ε*` by less
  than a factor of 3. The dormant pool's decay rate, not entry speed, sets
  the depth.
- **KD5. Dormancy cannot remove bistability.** At `L = 2×10⁻³` and `f = 0`, a
  methanogen invasion leaves an acetogen-only bulk at every `ε`. This follows
  from KD1.

## Not in this stage

- Temperature- or habitat-dependent turnover, and different `L` for the two
  guilds. Name these if T1 shows that the switch depends mainly on the ratio
  of the guilds' effective losses.
- Environmental stochasticity, shared atmospheric H₂ and evolution of `L`.
- A coupled stochastic climate–ecosystem model. Joint endpoint probabilities
  remain out of reach; see review §2.

## Outputs and stopping rule

- `figures/turnover/regimes.csv` and a regime-map figure of `L` against `f`
  (T1).
- `figures/turnover/refuges.csv` (T2) and `figures/dormancy/dormancy.csv`
  (T3), with first-window classes.
- New pages `models/haze_world/turnover.md` and
  `models/haze_world/dormancy.md`, or one page if they read better together.
- Keep the frozen buffered-refuge and bottleneck outputs unchanged. Refer to
  them by case ID.

Stop when KT1 to KT4 and KD1 to KD5 are each confirmed or refuted with a
mechanism. If the T1 basin checks disagree with the local-stability
classification, resolve that before interpreting T2 or T3.

## Reference

Hoehler, T. M. & Jørgensen, B. B. (2013). Microbial life under extreme
energy limitation. *Nature Reviews Microbiology* 11, 83–94.
doi:10.1038/nrmicro2939
