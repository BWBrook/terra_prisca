# Review of stage 2: collapse timing and mutational rescue

Codex (GPT-6), 9 November 2026. Reviewed stage-1 repair `142a2d9` and the
strain variant `85041a0`. **Accept the stage-1 repair. Revise the stage-2
interpretation before treating its survival labels as lasting rescue.**
Production equations and the original experiment outputs are unchanged here.

All 63 tests pass. Independent checks reproduce all 205 repaired stage-1
sensitivities, return thresholds and invasion classifications to table
rounding; regenerated stage-1 tables and figure are byte-identical. The
strain model's reflecting birth-mutation operator conserves total births
and methane production. Its count rule is an explicit deterministic biomass
removal rule, rather than a calibrated stochastic population model.

## The original survival contrast is a follow-up-time contrast

The reported H stranding case reproduces: with E = 0.65 eV, linear loss,
T₀ = 265 K, 10-year counts and B_min = 10⁻⁶ B*, m = 10⁻⁶ dies 34,440 years
after the supply decline begins. The m = 10⁻⁸ control remains alive at the
original endpoint, but dies at 105,370 years when followed longer.

All **19 extended H cases** tested here eventually die. They include the
count/grid variants below and a finer 0.125-K grid with matched mutation
variance and threshold density. The extended runs hold the final supply for
200,000 years, versus 60,000 originally. This is evidence of delayed collapse
in these cases, not a universal extinction theorem.

At 0.5-K spacing, extinction times after the decline begins are:

| Count interval (yr) | m = 10⁻⁸ | m = 10⁻⁶ |
|---:|---:|---:|
| 1 | 105,366 | 105,363 |
| 3 | 105,367 | 104,881 |
| 10 | 105,370 | 34,440 |
| 30 | 105,370 | 116,500 |
| 100 | 59,700 | 117,300 |

The count rule therefore changes both collapse time and the ranking of
mutation rates. At 30- and 100-year counts the moderate-mutation population
lasts longer. At 1-year counts the two rates give almost identical lifetimes.
The original adverse effect of mutation is not a robust ordering across
these interventions.

## Grid spacing changes the mutation and extinction models

With one-bin mutations per birth, mutational variance is 2m h², where h is
the grid spacing. Holding m fixed while refining the grid changes mutation
size. Holding a per-bin biomass cutoff fixed also changes the aggregation
being removed. Two comparisons are recorded: raw parameter sensitivity,
and a density interpretation holding variance and B_min/h fixed:

    m(h) = m₀ (0.5/h)²
    B_min(h)/B* = 10⁻⁶ h/0.5.

At 10-year counts with base m₀ = 10⁻⁶:

| Grid h (K) | Scaling | Actual m | B_min/B* | Extinction after decline begins (yr) |
|---:|---|---:|---:|---:|
| 1.0 | Raw | 10⁻⁶ | 10⁻⁶ | 47,260 |
| 0.5 | Original parameters | 10⁻⁶ | 10⁻⁶ | 34,440 |
| 0.25 | Raw | 10⁻⁶ | 10⁻⁶ | 107,000 |
| 1.0 | Matched variance/density | 2.5 × 10⁻⁷ | 2 × 10⁻⁶ | 101,500 |
| 0.25 | Matched variance/density | 4 × 10⁻⁶ | 5 × 10⁻⁷ | 115,510 |
| 0.125 | Matched variance/density | 1.6 × 10⁻⁵ | 2.5 × 10⁻⁷ | 111,940 |

Every comparison starts with the same 285.5-K clone, avoiding a change of
initial genotype when rounding to another lattice. The common review grid
runs from 245.5 to 310.5 K; the production default is 245 to 310 K. Recorded
boundary biomass is checked separately in the metadata. This is a sensitivity
study, not a demonstrated continuum convergence or a physically calibrated
demographic prescription.

Tightening rtol from 10⁻⁷ to 10⁻⁹ and all absolute tolerances by a factor of
100 reproduces the original 34,440-year collapse and the fine-grid survival
at the original endpoint. The material differences do not disappear with
that solver-accuracy check.

## The final supply cannot support a stationary living H state

Under this assumed cold bridge, the final supply potential 0.02 is below the
best attainable stationary threshold, about **0.02087893**. The threshold
occurs at r = 0.01185708, T = 273.80498 K and optimal θ = 285.72262 K.
It lies entirely below Arney's interval, in the assumed low-methane bridge.

For a positive steady state under linear loss, write r_a for abiotic methane
and P_K = τ c Φ_K. The required donor supply potential is

    P_required(r, θ) = r − r_a + P_K/[ρ(T(r), θ) − 1],    ρ > 1.

Numerically minimizing this expression over the best-growth trait gives the
threshold above. The frozen 285.5-K control also has no positive equilibrium:
its minimum is 0.02088523. Independent sign scans agree with the production
root finder. For a stationary community, mean growth cannot exceed the
best-growth envelope; mutation therefore cannot provide a stationary mixture
with better resource capture than this bound.

The equilibrium argument does not exclude all nonstationary full-system
attractors. The population integrations independently establish extinction
for the tested settings. Together these results explain why a long-lived
low-mutation control is not evidence of a viable final living state. Near
the supply threshold, slow passage through a bottleneck can outlast the
original observation window.

To test lasting evolutionary stranding, first choose a final supply where
the fixed reference and a best-adapted population both have viable living
equilibria. Then compare whether their trajectories reach them. The current
experiment instead tests how traits and count rules alter collapse timing
after forcing supply below a living-equilibrium threshold.

## Mutation rescues some initially declining clones

The seed experiment itself contains a counterexample to its broad result-10
heading. Negative net growth is not zero reproduction. At T₀ = 265 K, with
one initially occupied bin and no initially viable strain:

| Initial optimum (K) | Initial net growth (yr⁻¹) | No mutation | m = 0.01 |
|---:|---:|---|---|
| 285.0 | −0.43325 | Extinct at 32 yr | Survives 20,000 yr |
| 285.5 | −0.90736 | Extinct at 16 yr | Survives 20,000 yr |

Both mutating populations recover to about 0.999987 B* with 25–26 living
bins. At 20,000 years their climates are 284.69 and 285.09 K, respectively.
This is de novo mutational rescue from declining clones, without immigration
or initial standing variation. The result is conditional on the mutation,
seed and bridge assumptions; 20,000-year survival is not an asymptotic proof.

The correct barriers are that **total extinction is absorbing** and **zero
division prevents birth-mediated mutation**. The model's finite mutational
reach under a chosen threshold does not make every cold-trap introduction
evolutionarily absorbing. Standing variation already present in a population
is also distinct from immigration.

The original seed jobs use **1-year** counts through the Run default; the
rescue jobs explicitly use **10-year** counts. The model-page description
must distinguish them. The seed field `established` currently means only
that total extinction has not occurred by 500 years.

## Reproduce and act next

From the repository root, with three local workers for the sweep:

```sh
uv run python models/haze_world/review/strain_robustness.py models/haze_world/review
uv run python models/haze_world/review/check_strain_supply.py models/haze_world/review
uv run python models/haze_world/review/check_strain_seed_rescue.py models/haze_world/review
```

Outputs: [39 count/grid/horizon runs](strain_robustness.csv),
[settings and boundary check](strain_robustness_metadata.json),
[stationary supply feasibility](final_supply_equilibria.json),
[seed controls](seed_mutational_rescue.json), and
[20,000-year seed trajectories](seed_mutational_rescue_long.json).

Revise results 9–10 and their framing, distinguish finite-horizon survival
from a viable final attractor, and report census settings per experiment.
The U heat-exposure mechanism was not disproved by these H-focused runs.
Hydrogen competition should still begin with the published uptake benchmark.

One nonblocking stage-1 metadata issue remains: `local_regulation()` detects
a climate vertex by comparing response ratios. When ρ_T = 0, both ratios
are 1 even if the absolute one-sided temperature sensitivities differ, so
`at_vertex` can be false at a real vertex. No current stage-1 endpoint is at
one; its reported numerical results are unaffected.
