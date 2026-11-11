# Competitive evolution: specification

Claude (Opus 5.5), 11 November 2026. Answers open question 1 of the
[synthesis](synthesis/synthesis.md) and the bounded stage proposed in
Codex's [readiness note](synthesis/readiness.md). Codex builds and checks
it; Claude reviews it. A [static preview](review/competitive_evolution_preview.py)
([reference decomposition](review/competitive_evolution_preview.json),
[best responses](review/competitive_evolution_preview_evolved.json)) was run
before the predictions below were fixed. The predictions say which numbers
come from it.

## Question

In the single-guild precursor, unconstrained evolution of the thermal
optimum erased the tolerance-edge thermostat (C02). Does selection on the
guilds' thermal physiology also erase the competitive set point, or does
it only move it?

## What the preview shows

The coupled reference physiology is `population_coupling.reference()`, with
`threshold_shape = "fixed_energy"` and the `constant_shape` continuation
below 4 °C. Its switch temperature is

    R*_i(T) = h_i(T) + K_i(T) q_i(T) / (V_i(T) − q_i(T)),   q_i = m_i(T) + L/Y_i

Three temperature dependences enter it:

- **Measured kinetic shapes**, `V_i(T)` and `K_i(T)`. These are strain
  properties, interpolated linearly between the six measured temperatures
  from 4 to 30 °C.
- **Cessation thresholds**, `h_i(T)`. These hold the energy available at
  cessation fixed, so they follow the reaction thermodynamics. They run from
  1.36 to 20 Pa for acetogens and from 0.086 to 1.0 Pa for methanogens
  between 0 and 30 °C.
- **Maintenance**, `m_i(T)`. Both guilds share one Arrhenius factor, so
  maintenance at 4 °C is 0.077 of its 30 °C value.

The preview reproduces the reference switch at 281.535 K for
`L = 10⁻³ h⁻¹`. It then gives each guild a heritable **kinetic position**
`t_k`: the strain behaves at local temperature `T` like the reference strain
at `t_k`, with `t_k` confined to the measured range. A hotter-is-better
factor `exp[−(E/k_B)(1/T − 1/t_k)]` multiplies `V`. Each guild's best
response minimises its own `R*` at `T`. Thresholds, maintenance and yield do
not evolve.

| `L` (h⁻¹) | Reference switch | Evolved, `E = 0` | `E = 0.2 eV` | `E = 0.45 eV` | `E = 0.65 eV` |
|---|---:|---:|---:|---:|---:|
| 3×10⁻⁴ | 277.15 K (at the 4 °C data edge) | none: methanogens win everywhere | none | 273.18 K | 275.04 K |
| 10⁻³ | 281.54 K | 277.96 K | 280.37 K | 283.75 K | 283.84 K |
| 3×10⁻³ | 291.92 K | 293.95 K | 297.51 K | 294.44 K | 292.16 K |

Every crossing keeps the reference orientation: acetogens win on the cold
side. In this static calculation, then, evolution of the uptake kinetics
**moves the competitive set point by a few kelvin**. It removes the set
point only at the lowest turnover, where the reference crossing already sits
on the edge of the data.

The likely reason is that the thermodynamic thresholds and the shared
maintenance cost keep a temperature-dependent `R*` ordering that kinetic
adaptation cannot remove. Selection can tune enzymes, not reaction
thermodynamics. The single-guild tolerance edge had no such anchor. This
explanation is a hypothesis for S2 to test.

Two qualifications apply to the preview:

- The best kinetic positions fall on measured temperature nodes (10 °C and
  25 °C). Along a piecewise-linear interpolation, that is expected. A smooth
  interpolation may move them.
- The best responses are computed at fixed temperature. They are not yet a
  joint evolutionary equilibrium with the climate.

## Experiments

### S1. Best-response map (static)

- **Grid.** Recompute the preview independently on a finer grid:
  - `L` from 2×10⁻⁴ to 5×10⁻³ h⁻¹, 12 values per decade;
  - `E ∈ {0, 0.1, 0.2, 0.3, 0.45, 0.65} eV`;
  - kinetic positions every 0.01 °C.
- **Interpolation variant.** Add a named alternative, `smooth_shape`: a
  shape-preserving monotone cubic interpolation (PCHIP) of `ln V` and
  `ln K` through the six measured temperatures.
- **Report:** every evolved crossing, its orientation and the best kinetic
  positions. Also report where the crossing leaves the Arney case-B cooling
  branch (273.39–297.008 K).

### S2. What anchors the evolved switch

At `L ∈ {3×10⁻⁴, 10⁻³, 3×10⁻³}` and `E ∈ {0, 0.65}`, recompute the evolved
crossing with each of these held at its 30 °C value, one at a time:

- `h_A(T)` and `h_M(T)` together;
- the shared maintenance factor;
- both.

Report which removal destroys the crossing or moves it by more than 2 K.

### S3. Joint evolutionary and climate equilibrium

An evolved community is a set `(t_kA*, t_kM*, T*)` that meets two conditions:

- each `t_k*` minimises its guild's `R*` at `T*`;
- `T*` is the mixed equilibrium of the full coupled model with those traits
  frozen.

The procedure:

- Map the traits into the population-coupling physiology as a named
  variant, `evolved_kinetics`. Leave the reference unchanged.
- Cover `f ∈ {0, 0.5}`, `L ∈ {3×10⁻⁴, 10⁻³, 3×10⁻³}`, every `E` in S1 and
  both interpolations.
- For each evolved community, report:
  - `T*` and whether it lies on the cooling branch;
  - the five-stock ecological Jacobian with traits frozen, including the
    complex pair (period, damping time and Q);
  - every other stable equilibrium with the same traits, as in the T1 map.
- **Convergence stability.** Use the canonical-equation Jacobian, with
  climate re-equilibrated at each trait value and equal mutational supply
  per cell. Repeat with a supply ratio of 0.1 and 10. The ratio cannot move
  a joint equilibrium, but it can change its convergence stability.

### S4. Invasion check

At each S3 community, rare mutants at every kinetic position on the S1 grid
grow in the resident environment, with `p` and `T` fixed. Confirm that none
has positive net growth beyond solver tolerance.

### S5. Evolutionary path (conditional)

Run S5 only if S3 finds a community that is not convergence stable, or a
setting with no joint equilibrium on the branch. Integrate the canonical
equation from the reference strains, with climate re-equilibrated, and
report whether either guild is excluded along the way.

Do not add spatial genetics, stochastic mutation, dormancy or new
photochemistry in this stage.

## Predictions

These are fixed before S1–S5. KE1, KE3 and KE4 rest on the preview; KE2,
KE5 and KE6 do not.

- **KE1. Evolution moves the set point but does not remove it.**
  - At `L = 10⁻³` and `E = 0`, the evolved crossing lies within 0.5 K of
    277.96 K with the linear interpolation.
  - The evolved mixed equilibrium is locally stable at `f = 0` and `0.5`
    and lies on the cooling branch.
- **KE2. The orientation never inverts.** No setting in S1 or S3 gives a
  methanogen-cold crossing, which would be a destabilising switch on the
  haze-cooling branch.
- **KE3. Evolution erases the switch at low turnover.** At `L = 3×10⁻⁴` and
  `E ≤ 0.2 eV`, no crossing exists, and the evolved world is methanogen-only
  near 273.5 K.
- **KE4. Constrained adaptation leaves the set point within 2.5 K of the
  reference.** At `L = 10⁻³` and `E ≥ 0.45 eV`, the crossing falls within
  2.5 K of 281.535 K.
- **KE5. Thermodynamics anchors it.** In S2 at `L = 10⁻³` and `E = 0`,
  freezing `h(T)` removes the crossing or moves it by more than 2 K.
  Freezing maintenance alone does not.
- **KE6. The joint equilibrium is convergence stable.** Every S3 community
  that exists on the branch is convergence stable at all three supply
  ratios. Its frozen-trait thermostat keeps a weakly damped complex pair
  (Q above 10).
- **KE7. The interpolation matters only modestly.** With `smooth_shape`,
  crossings move by less than 2 K from their linear-interpolation values at
  `L = 10⁻³` and `3×10⁻³`.

## Interpretation limits (proposed E13)

- **Trait family.** The result covers one family: translation of measured
  kinetic shapes within the measured range, with an optional
  hotter-is-better cost. It is not general evolutionary theory.
- **Non-evolving parameters.** Thresholds, maintenance and yield do not
  evolve here. "Selection cannot remove the switch" may be said only
  together with "within this family".
- **No rates.** Nothing in this stage calibrates mutation supply or
  evolutionary rates. An evolved set point is an endpoint, not a timeline.
- **Allowed:** "kinetic adaptation shifted the competitive set point by a
  few kelvin, where thermodynamic thresholds anchored the switch".
- **Not allowed:** "evolution cannot break the thermostat", or that the
  Archean set point was evolutionarily stable.

## Outputs and stopping rule

- **Outputs:**
  - `figures/competitive_evolution/best_response.csv` (S1),
    `anchors.csv` (S2), `communities.csv` (S3, with S4 flags) and a
    manifest;
  - a new page, `models/haze_world/competitive-evolution.md`;
  - ledger rows for the confirmed or refuted KE1–KE7;
  - the E13 interpretation limits added to the estimands.
- **Stopping rule.** Stop when KE1–KE7 are each confirmed or refuted with a
  mechanism. If S1 and the preview disagree by more than 0.5 K at any shared
  setting, resolve that before S3.
