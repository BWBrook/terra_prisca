# Two-habitat refuge coupling: specification

Claude (Opus 5.5), 10 November 2026. Design for the next build, following
[finite-populations.md](finite-populations.md) and its
[review](review/finite-populations-claude-review-2026-11-10.md). Codex builds
it; Claude reviews it.

## Why this model

In one well-mixed habitat, the invader drives the resident below any
plausible floor 10² to 10³ times faster than the climate can respond
(Pi = 137 to 2,089, [refuge_scoping.json](review/refuge_scoping.json)). At
`f ≤ 0.5` both pure states can be invaded by the missing guild, so the mixture
is the only deterministic attractor. A single sealed habitat cannot reach it,
yet one immigrant cell per decade restores it. The open question is whether the
biosphere itself can supply that rescue: whether some habitat stays on the
loser's side of the competitive switch while the methane inventory relaxes over
about 10⁴ years.

The model asks two questions:

1. **Attainability.** Does an explicit refuge, with no external immigration,
   make the warm mixture reachable from both invasion directions?
2. **Climate state.** Does spatial structure change the climate itself? In two
   habitats, each guild can win its own patch. That spatial partition need not be
   pinned at the switch temperature, and it can exist where the well-mixed
   model has none (`f=0.9`).

## State and equations

There are two habitats, cold `c` and warm `w`, with area fractions `w_c + w_w = 1`
and the same effective habitat volume per area as the
[full model](population-coupling.md). Local temperatures are

    T_j = T(r) + delta_j,     delta_c = -w_w Delta,  delta_w = w_c Delta,

so the area-weighted mean is Arney's global temperature `T(r)` and `Delta`
is the patch contrast. Each habitat carries `p_j, X_Aj, X_Mj, A_j`. The two
habitats share the methane ratio `r`. There are nine states.

    kappa dp_j/dt  = J_j - sum_i q_i(p_j, T_j, products_j) X_ij - k_ex (p_j - p_atm)
    dX_ic/dt       = mu_i(p_c, T_c, products_c) X_ic + d w_w (X_iw - X_ic)
    dX_iw/dt       = mu_i(p_w, T_w, products_w) X_iw + d w_c (X_ic - X_iw)
    dA_j/dt        = P_j - (k_rec(T_j) + k_other) A_j
    dr/dt          = conversion * sum_j w_j M_j + abiotic - L(r)

All local fluxes reuse `population_coupling.fluxes` evaluated at `T_j`.
Dispersal conserves total biomass, `sum_j w_j dX_ij/dt|_disp = 0`, and `d`
(yr⁻¹) is the exchange rate. Acetate and H₂ stay local. `p_atm` stays fixed, so
the habitats exchange hydrogen only with a fixed reservoir, not with each other.
The methane activity term uses the shared `p_CH4(r)`, and the acetate term uses
the local `A_j`.

### Interpretive choices to record

- **Constant offsets.** A haze world's meridional gradient would itself depend
  on the haze. Stage 1 prescribes `Delta`; a later stage can derive it from a 1-D
  diffusive energy balance. A modern equator-to-pole contrast of about 40 K
  bounds the sweep; a hydrothermal refuge would be small and much warmer.
- **Supply per area is uniform** (`J_j = J`). A concentrated-supply refuge,
  `J_w = phi J / w_w`, is a later variant.
- **Measured physiology spans 4 to 30 °C** (277.15 to 303.15 K). Flag every
  patch that leaves that range. Small-area refuges keep both patches nearer
  the measured range than symmetric halves do. For example, a 10% cold refuge
  13 K below a 294.4 K world leaves the bulk patch only 1.4 K warmer.
- **Shared atmospheric H₂** (a dynamic `p_atm`) would couple the patches
  competitively through hydrogen. It is deferred and named here so its absence
  stays visible.

## Limits the code must pass

1. **Identical habitats.** With `Delta = 0`, uniform supply and symmetric
   initial states, trajectories equal the single-habitat model for any `d` and
   `w`, to integrator tolerance.
2. **One habitat.** With `w_c = 1`, the model reduces to the single-habitat
   model.
3. **Conservation.** Dispersal conserves biomass exactly, and the summed redox
   residual (`population_coupling.redox_residual`, area-weighted) is zero.
4. **Partition existence (fixed activities).** A pure spatial partition (A only
   in `c`, M only in `w`) exists only if `T_g + delta_c < T_sw < T_g + delta_w`
   at its own climate `T_g`, with `T_sw = 281.535 K`. Check this against the
   equilibrium solver.

## Predictions to test (fixed activities, small `d`)

These are first-order predictions from `|T_start − T_sw|`
([refuge_scoping.json](review/refuge_scoping.json)), set before the runs. The
two-habitat starts will differ slightly from the single-habitat ones.

| Invasion | Start | Loser needs | Condition |
|---|---:|---|---|
| A into M, any `f` | 273.517 K | warm refuge | `w_c Delta > 8.02 K` |
| M into A, `f=0.5` | 294.403 K | cold refuge | `w_w Delta > 12.87 K` |
| M into A, `f=0` | 283.199 K | cold refuge | `w_w Delta > 1.66 K` |

- **P1. Thresholds.** Below the condition, the loser goes extinct in both
  patches during the transient, and the endpoint matches the single-habitat
  result. Above it, the loser survives in its refuge.
- **P2. History independence.** Wherever both directions meet their
  conditions, both directions reach the same endpoint at `f ≤ 0.5`.
- **P3. New coexistence at `f=0.9`.** A warm patch above T_sw holds
  methanogens permanently, because the climate stays near 273.5 K whatever the
  acetogens do. The well-mixed model never has this coexistence.
- **P4. Unpinned climate.** A pure partition's global temperature varies with
  `w` and `Delta` instead of sitting at T_sw. Where the partition condition fails
  on one side, expect one patch to be mixed and locally pinned
  (`T_g = T_sw − delta_j`). Classify every endpoint as pure partition,
  locally pinned, or single guild.
- **P5. Dispersal.** For `d` well below the exclusion rates (1 to 12 yr⁻¹),
  the partition holds, with sink populations of about `d X / |lambda|`. As `d`
  approaches those rates the patches homogenize toward a well-mixed community at
  the area-mean conditions.

## Experiments

1. **Continuum equilibria.** For `f = 0, 0.5, 0.9`, map all equilibria and
   their stability on a (`w_w`, `Delta`) grid at `d = 0` and `d = 1e-3`:
   global and patch temperatures, class, and the climate domain of each patch.
2. **Invasion matrix**, fixed activities:
   - `f ∈ {0, 0.5, 0.9}`;
   - `w_w ∈ {0.1, 0.5, 0.9}`: small warm refuge, halves, small cold refuge;
   - `Delta ∈ {0, 5, 10, 15, 20, 30} K`;
   - `d ∈ {0, 1e-6, 1e-3, 1} yr⁻¹`;
   - both invasion directions.

   That is 432 runs. Each starts at the two-habitat conditional pure-guild
   equilibrium (resident in both patches) and seeds the invader at
   10⁻¹² gDW/L in both patches. There is no external immigration. Floors are
   one cell per habitat, censused every 10 years. Report the continuous
   minimum log stock per guild per habitat. The `Delta = 0` slice must
   reproduce the existing zero-immigration endpoints.
3. **Seed origin.** For a subset near the P1 thresholds, seed the invader in
   one patch only.
4. **Product feedback.** Repeat the threshold-bracketing subset with product
   activities.
5. **Census check.** Repeat a threshold-bracketing subset with 1-year censuses.

Output an endpoint table in the style of `attained_endpoints.csv`, with
per-habitat occupancy, catabolic shares, local temperatures and domain flags.
Also map global temperature against `Delta` for each `f`, `w_w` and direction,
with the P1 thresholds marked.

## Build order and stopping rule

1. Two-habitat right-hand side, passing limits 1 to 3.
2. Equilibrium solver and classification, passing limit 4.
3. Invasion matrix.
4. The seed-origin, product and census subsets.
5. The model page: `models/haze_world/refuge-coupling.md`.

Stop when P1 to P5 are each confirmed or refuted with a mechanism. A refuted
prediction is a result, not a defect. If the equilibrium map shows that the
partition is never self-consistent inside the measured temperature range, report
that and stop before the full matrix.
