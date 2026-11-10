# Buffered refuges: specification

Claude (Opus 5.5), 10 November 2026. Next build after the
[two-habitat refuge model](refuge-coupling.md) and its
[review](review/refuge-coupling-claude-review-2026-11-10.md). Codex builds it;
Claude reviews it.

## Question

Can a biosphere rescue **both** guilds from **both** invasion directions,
using only supported physiology? The two-habitat model could not test this. Its
refuges tracked the global temperature at fixed offsets. Clearing the 297 K
greenhouse peak then forced the cold refuge below 273 K after the haze cooled
the planet. Any warm refuge also pushed the bulk of the methanogen world below
the 273 K floor.

This build gives refuges **buffered temperatures**. Hydrothermal mixing zones,
and deep or ice-covered water, are held by heat sources and phase or density
limits, largely independent of surface climate. The bulk tracks Arney's curve
with no offset.

## Habitats

Generalize `refuge_coupling` to N patches. Each patch has an area weight and a
temperature rule:

- `tracking(delta)`: `T_j = T(r) + delta`. The existing two-habitat model is
  the special case of two tracking patches with offsets whose area mean is zero.
- `buffered(T_fixed)`: `T_j = T_fixed`.

The main configuration has three patches:

| Patch | Area | Temperature |
|---|---|---|
| Bulk | `1 − w_c − w_w` | `T(r)`, no offset |
| Warm refuge | `w_w` | fixed `T_w` above T_sw |
| Cold refuge | `w_c` | fixed `T_c` below T_sw |

Everything else is unchanged from the two-habitat model: local H₂, biomass and
acetate; conservative exchange; shared `r`; fixed `p_atm`; no external
immigration; uniform supply per area. Exchange generalizes to an all-to-all
rate `d`, with `E_ij = d sum_k w_k (X_ik − X_ij)`. This conserves
`sum_j w_j X_ij` exactly.

### Supported domain

The bulk's path stays within 273.39 to 297.00 K, the range of Arney's curve.
That is the support the single-habitat model already uses, including the named
273 to 277 K continuation. Refuge temperatures lie inside the measured window
by construction, so no domain exit should occur. Any exit is a defect to report,
not an endpoint.

### Interpretive choices to record

- **Refuge temperatures are fixed.** The default warm refuge is 286 K and the
  cold refuge 278 K. Both are about 4 K from the 281.535 K switch and inside
  277.15 to 303.15 K.
- **The area-mean temperature is not conserved.** Refuges are buffered, not
  heated by the redistribution of solar heat. With refuges of 2% or less, the
  biosphere's area-mean temperature departs from `T(r)` by less than 1 K along any
  path (2% × 19 K at the greenhouse peak, per refuge); report the exact value.
- **Supply per area is uniform.** Enhanced hydrothermal supply is a later
  variant.

## Limits the code must pass

1. **Two-habitat regression.** Two tracking patches reproduce the two-habitat
   model: right-hand side exactly, and the selected trajectories of the
   published cases within the existing tolerances.
2. **Refuge areas of zero** reproduce the single-habitat model.
3. **Conservation.** Exchange conserves biomass, and the area-weighted redox
   residual is zero.
4. **Fixed refuges.** A buffered patch's temperature does not depend on `r`,
   both in the right-hand side and in the Jacobian.

## Predictions

These are fixed before the runs.

- **B1. Mutual protection.** With both refuges, `d ≤ 10⁻³ yr⁻¹` and
  `f ≤ 0.5`, neither guild is lost globally in either direction. Each refuge
  stays on its own guild's side of the switch throughout, which is the
  sufficient condition of the review: 46 of 46 cases so far.
- **B2. History independence.** Under B1's conditions, opposite invasions reach
  the same endpoint: a mixed bulk near the switch, global T near 281.5 to 282 K.
  This is the P2 test the previous geometry could not support.
- **B3. One-sided refuges keep one-sided history.** A warm refuge alone rescues
  methanogens when acetogens invade, but not acetogens in the reverse direction,
  where they are lost at the greenhouse peak. A cold refuge alone gives the
  mirror image. Early Earth almost certainly had hydrothermal warm refuges; cold
  buffered habitats need ice cover or stratified water. If B3 holds, which
  refuges existed decides the history.
- **B4. Rescue is not supply-limited.** From the census barrier in
  [finite-populations.md](finite-populations.md), a 2% refuge of about 10²⁴ cells
  exports about `d × 10²⁴` cells per year, so `d ≳ 10⁻²⁵ yr⁻¹` delivers the 0.1 floor per year that a
  ten-year census requires. Rescue should therefore succeed at every tested
  `d`, including 10⁻⁹. The failure mode at large `d` is the reverse: refuges
  homogenize with the bulk and lose their protection.
- **B5. 90% conversion.** A warm refuge supports methanogens, as in the
  two-habitat build, and the climate effect stays below 0.1 K.

## Experiments

**Main grid, fixed activities.** 96 runs:

- `f ∈ {0, 0.5, 0.9}`;
- refuge configuration ∈ {none, warm only, cold only, both}, each refuge at 2%
  of the area;
- `d ∈ {10⁻⁹, 10⁻⁶, 10⁻³, 1} yr⁻¹`;
- both directions.

The starts, seed dose, one-cell floor per patch, ten-year census and
stationarity rules are the two-habitat model's. Report endpoints, global and
local minima, catabolic shares and patch temperatures in the existing table
format.

**Sensitivity runs.**

- Refuge temperatures, for "both" at `d ∈ {10⁻⁶, 10⁻³}`:
  `T_w ∈ {283, 292}` K and `T_c ∈ {277.15, 280}` K, crossed (48 runs).
- 0.5% refuge areas, for each refuge configuration except "none", at
  `d = 10⁻⁶` (18 runs).
- Product activities, for "both" at `d = 10⁻⁶` (6 runs).

**Controls.** Zero-area and two-tracking-patch regressions, plus one `d = 0`
control per configuration to show census isolation explicitly.

## Stopping rule

Stop when B1 to B5 are each confirmed or refuted with a mechanism. If B2 fails
under B1's conditions, characterize the distinct endpoints and their basins
before running the sensitivity grid. Distinct endpoints would mean genuine
multistability of the coupled system, a stronger result than census history.
