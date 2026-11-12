# Step 3: display items

Claude (Opus 5.5), 12 November 2026. Each item serves the
[main message](01-working-abstract.md). Microbes can hold a planet's
temperature steady, but perfect control breaks down when the climate responds
slowly. Slightly imperfect control is far more durable.

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
  - Hydrogen enters from volcanoes and is drawn down by two microbial
    groups.
  - Methanogens make methane, which thickens an organic haze and cools the
    surface.
  - Acetogens divert hydrogen into acetate instead.
  - Temperature sets which group wins, and the climate responds after a lag.
- **(b) The switch.** The hydrogen level each group needs to grow, plotted
  against temperature. The curves cross at the set temperature, T* ≈ 281.5 K.
- **(c) The plateau.** Surface temperature against hydrogen supply. With one
  group alone, temperature tracks supply; with both, it stays flat at T*.
  The caption credits the plateau to Seto & Akagi (2007).

Source: existing set-point data; panel (a) is new artwork.

### Figure 2. Perfect control breaks down when climate responds slowly

This figure shows the failure as it happens.

- **(a) Perfect control under rising lag.** Temperature over time after a
  small kick, at climate lags of 0.1, 1 and 10 years:
  - at 0.1 years it settles;
  - at 1 year it swings by about 1.3 K;
  - at 10 years the regulation is lost and both populations fall below one
    cell.
- **(b) Population sizes** for the same runs, on a log scale, with the
  one-cell line marked.
- **(c) Slightly imperfect control** under a 100-year lag. It settles.

Source: the B2 transients and the dial branches.

### Figure 3. Durability costs a little precision (headline)

This is the trade-off itself.

- **(a) The critical lag against temperature drift.** The critical lag is
  the longest climate lag a regulator survives. The drift is the temperature
  change per e-fold of hydrogen supply. Both axes are logarithmic.
  - The four dial branches climb continuously from the perfect-control limit.
  - The resolved habitat states sit far out along the curve.
  - A line marks a 30-year lag, and a band marks its price of 0.07–0.32 K.
- **(b) What the drift looks like.** Temperature against supply for three
  settings of one dial: flat, a gentle slope, and a steeper slope. It shows
  the reader that "slightly imperfect" is a small effect.

Source: the graded-dial and continuum-habitat outputs (C54, C55, C57).

### Figure 4. Arrival order decides the regulator

This figure covers the supporting assembly result.

- **(a) The invasions.** Population sizes during an invasion in each
  direction, with the displaced resident crossing the one-cell line.
- **(b) The outcome.** A tally of the final resident against arrival order
  across all 24 runs: 12 of 12 in each direction.

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

## ESM

Each item backs a specific point in the main text.

| Item | Supports |
|---|---|
| Parameter table with sources | Model section |
| Habitat-resolution convergence (C44, C45) | Fig. 3, habitat states |
| The full set of resolved states and their critical lags, including the six with reversed frozen response (C54) | Fig. 3 |
| Dial brackets and refinement points (C55, C57) | Fig. 3, the 30-year price |
| Predictions that failed: the power-law band (C56) and the weak-mode formula (C58) | the Discussion's account of the prespecified tests |
| Atmospheric-hydrogen sensitivity (C59) | Table 1 |
| Dependence on the acetate fate f, and the coexistence interval at f = 1 | Table 1 |
| Methods for continuation, quadrature and critical-lag root-finding | Model section |
| The AI-use record: correspondence snapshot and claims ledger | Declaration of AI use |

## Build notes

- Figs 2–4 come from existing evidence files and need new composite plotting
  only.
- Fig. 1a is new artwork.
- The figures must read in greyscale, with panel labels (*a*)–(*c*), as JRSI
  requires.
- The plotting code goes in the repository and is cited with the Zenodo
  release.
