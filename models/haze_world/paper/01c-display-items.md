# Step 1c: display items

Claude (Opus 5.5), revised by Codex (GPT-6), 12 November 2026. Each item serves the
[main message](01a-working-abstract.md). Microbes can hold a planet's
temperature, but exact control fails when climate responds slowly. Imperfect
control lasts far longer, and grows looser as habitat temperatures differ.

## Budget

The plan is four figures and one table. That suits a JRSI paper of about
5,500 words: the comparators carry four to six figures, and this paper has
one message with three supporting results. Each figure makes one claim. A
fifth figure would add volume without adding a claim, so the remaining
material goes to the ESM.

## Main text

### Figure 1. How microbes can set a planet's temperature

This figure gives the context a new reader needs and sets up the first
result.

- **(a) Schematic.**
  - An imposed hydrogen supply feeds two microbial groups; exchange with an
    atmospheric reservoir provides an outlet.
  - Methanogens make methane, which thickens an organic haze and cools the
    surface.
  - Acetogens divert hydrogen into acetate. Show recycling to methane and
    material retained outside methane production as separate routes.
  - Temperature sets which group wins, and the climate responds after a lag.
- **(b) The switch.** The hydrogen level each group needs to grow, plotted
  against temperature. The curves cross at the set temperature, T* ≈ 281.5 K.
  Mark the supported climate range and show how the alternative capacity
  transfer can move the crossing outside it. The chosen normalisation is a
  condition of the reference example.
- **(c) The plateau.** Surface temperature against hydrogen supply. With one
  group alone, show its actual climate curve, including any flat haze floor;
  with both, show the coexistence plateau at T*. Mark the haze-cooling
  branch on a small inset of the Arney response. The caption credits the
  plateau mechanism to Seto & Akagi (2007).

Source: existing set-point data; panel (a) is new artwork.

### Figure 2. Perfect control breaks down when climate responds slowly

This figure shows the failure as it happens.

- **(a) Perfect control after a small kick.** Existing fixed-product,
  zero-recycling temperature trajectories at lags of 1 and 10 years:
  - at 1 year, late peak-to-peak swings span about 1.3 K over the
    30,000-year run;
  - at 10 years the continuous trajectory reaches a subcell bottleneck.
- **(b) Population sizes** for the same runs, on a log scale, with the
  one-cell line marked. End the physically interpreted trajectory at the
  first crossing. Any later continuous solution is a muted diagnostic, since
  removing a guild changes the subsequent environment.
- **(c) Stability comparison.** Leading growth/decay rate against thermal
  lag for the exact reference and a graded state, calculated from the
  existing linearised systems. Mark first losses and the 100-year line.
  This panel reports local stability, rather than an uncomputed nonlinear
  settling trajectory.

Source: B2 at f = 0, τ = 1/10 years; the exact and dial linearisations.
There is no τ = 0.1 B2 trajectory or graded τ = 100 settling run in these
outputs. Building panel (c) requires a spectral export from the existing
systems, rather than a new invasion or nonlinear experiment.

### Figure 3. Durability costs a little precision (headline)

This is the trade-off itself.

- **(a) First-loss margin against local sensitivity.** The critical lag is
  the first loss of equilibrium stability as thermal response slows; later
  restabilisation is possible. Sensitivity is |dT*/d ln Φ|, in K per e-fold
  of supply. Use logarithmic axes for positive values and a separate strip
  for S = 0 and zero-lag-unstable states.
  - The four dial branches approach the exact limit continuously; join only
    points on the same continuation branch.
  - Plot resolved habitat states by mechanism and connectivity, rather than
    implying one universal curve.
  - Draw upward arrows for right-censored margins. The 10,000-year search
    ceiling is a lower bound, rather than a measured first loss.
  - A line marks a 30-year lag, and a band marks its price of 0.07–0.32 K.
- **(b) What habitat spread costs.** Finite supply responses of steady
  temperature for uniform habitats and spreads of 1, 3, 6 and 8 K (f = 0.5,
  d = 10⁻⁴ yr⁻¹), over the uniform coexistence interval. Replaced the
  original local tangents after pressure-test Issue 1 (14 November 2026).

Source: the graded-dial and continuum-habitat outputs (C54, C55, C57) and the
Issue 1 finite branches (C60, C61).

### Figure 4. Arrival order selects the surviving guild

This figure covers the supporting assembly result.

- **(a) The invasions.** Population sizes during an invasion in each
  direction, with the displaced resident crossing the one-cell line. Use
  the finite-census paths for endpoints; distinguish them from uncensored
  diagnostic paths.
- **(b) The outcome.** A tally of the surviving guild against invasion
  direction across all 24 runs: 12 of 12 invaders persist in each direction.
  Label these as single-guild endpoints under the closed-habitat census rule.
  Mark which starting parameter sets also support a locally stable mixture.

Source: the B3 transients (C52).

### Table 1. Model ingredients and their roles

| Column | Content |
|---|---|
| Ingredient | e.g. haze climate response, strain physiology, acetate fate, thermal lag |
| Source | the literature or measurement it comes from |
| Role in the result | what it does in the model |
| Condition it sets | the culture-capacity normalisation (X4), a methane yield that differs between the routes (X7), the physiology floor at 273 K, and so on |

This table is the packaged statement of the model's assumptions and scope.
The Discussion's limitations paragraph points to it, which keeps those points
out of the narrative.

Foreground the alternative capacity transfer, the acetate-recycling and
assimilation routes, common turnover, and the below-measurement continuation
from 277.15 K to the model floor at 273 K. Explain that τ is a first-order
thermal relaxation time. Pair each source measurement with the assumption
needed to transfer it; this is parametrisation of a conditional model.

## ESM

Each item backs a specific point in the main text.

| Item | Supports |
|---|---|
| Parameter table with sources | Model section |
| Habitat-resolution convergence (C44, C45) | Fig. 3, habitat states |
| The full set of resolved states and their critical lags, including the six with reversed frozen response (C54) | Fig. 3 |
| Dial brackets and refinement points (C55, C57) | Fig. 3, the 30-year price |
| Dated staged predictions, including failed mechanism/gain predictions, the power-law band (C56) and the weak-mode formula (C58) | the Discussion's account of exploration and prospective tests |
| Atmospheric-hydrogen sensitivity (C59) | Table 1 |
| Dependence on the acetate fate f, and the coexistence interval at f = 1 | Table 1 |
| Methods for continuation, quadrature and critical-lag root-finding | Model section |
| The AI-use record: correspondence snapshot and claims ledger | Declaration of AI use |

## Build notes

- Figs 2–4 use existing evidence and systems. Fig. 2c needs a spectral export;
  Fig. 3b uses the Issue 1 finite branches.
- Read Fig. 4's finite trajectories from the separate `census_raw` archives;
  existing trajectory CSVs contain uncensored solutions. The f = 0, τ = 10
  B2 trace also needs an export from its existing raw archive. These are
  figure-building exports, rather than new simulations.
- Fig. 1a is new artwork.
- The figures must read in greyscale, with panel labels (*a*)–(*c*), as JRSI
  requires.
- The plotting code goes in the repository and is cited with the Zenodo
  release.
