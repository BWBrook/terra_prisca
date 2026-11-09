# Review of the hydrogen-uptake benchmark

Claude (Opus 5.5), 9 November 2026; reviewed `287294f`. **Accept the kinetic
reconstruction.** Units, the threshold-shifted Michaelis–Menten form, the NaN
for joint inactivity and the monotone envelope argument are correct. I
recomputed the 30 °C, 500 Pa intervals by hand and they agree.

## The normalization can be decided from the text's own crossovers

The 30 °C, 500 Pa verdict depends on the 200 Pa ceiling on the *A. bakii*
threshold. That ceiling does not appear in the recovered text. A stronger test
uses only statements the text does make:

1. MSB beats *A. bakii* except above about 80 Pa at 4 °C, and above about
   1000 Pa at 30 °C.
2. *A. bakii* beats MSP at 15 °C only above about 10 Pa.
3. *A. bakii* thresholds "steadily decreased with decreasing temperature
   down to 4 °C".

Each crossover fixes the acetogen threshold that makes the two uptake rates
equal there, given the methanogen threshold (0–2 Pa).
[`uptake_threshold_inversion.py`](uptake_threshold_inversion.py) gives:

| Basis | θ(4 °C) | θ(15 °C) | θ(30 °C) |
|---|---:|---:|---:|
| Culture, central | 16–17 Pa | 2.6–4.1 Pa | 94–95 Pa |
| Equal dry mass, central | 52 Pa | 6.0–6.8 Pa | 748 Pa |
| Culture, all 95% corners | −30 to 42 Pa | −3 to 6 Pa | — |
| Dry mass, 95% corners incl. biomass | 10–68 Pa | 1.2–8.2 Pa | 267–890 Pa |

Statement 3 requires θ(4 °C) < θ(15 °C).

- **Equal dry mass violates it** at central values (52 vs 6 Pa), and still
  violates it at the most favourable joint corner of every kinetic and
  biomass limit (≥ 10.0 vs ≤ 8.2 Pa). It also needs a 30 °C threshold of
  about 270–890 Pa. That is hard to square with the text's statement that
  products were "fairly stoichiometric" to the initial 1.5 kPa H₂.
- **Culture rates satisfy it** within the published limits, for example
  θ(4 °C) of a few Pa rising to about 5 Pa at 15 °C and about 95 Pa at 30 °C.
  The central values alone do not satisfy it (16.5 vs 3.4 Pa), so the
  figures were probably drawn from parameters within, not at, the
  tabulated means.

**Conclusion.** Figs. 3 and 4 were most likely computed from the tabulated
whole-culture rates. "Equal biomass" in the captions is then either loose
wording or a normalization that the published inputs do not reproduce.
Treat the culture basis as the reproduction target. This is an inference
from three approximate landmarks plus a qualitative monotonicity statement,
not a figure match.

A van't Hoff check is less decisive. Taking ΔH° ≈ −271 kJ per mol of
4 H₂ + 2 CO₂ → acetate⁻ + H⁺ + 2 H₂O from standard formation enthalpies, the
threshold ratio from 30 °C to 4 °C should be about 12. Dry mass gives 14 and
culture gives 5.6. Neither gives a 15 °C value below 10 Pa, so the "parallel
to theory" statement and the MSP landmark cannot both hold at central values.
I would not pursue this further without Fig. 1.

## Why reproduction and coupling need different bases

Matching the paper's figures and choosing the model's rate basis are
separate questions.

- A population model needs specific rates: μ_max = Y · V_max / X, with
  R* = K·D/(μ_max − D) + p*. That uses the per-dry-mass column whatever the
  authors plotted.
- The two bases put the 30 °C crossover at about 850 Pa or about 60 Pa.
  That shift matters if Archean surface H₂ lies in the tens to hundreds of
  Pa, which needs checking against Kharecha et al. (2005) before it is
  relied on.
- At steady state, competition is decided by R*, so thresholds and yields
  dominate. Batch Kcomp at a fixed pressure is not the model's selection
  criterion.

## Recommendation

- Close the benchmark as "kinetic table reproduced; competition figures
  consistent with whole-culture rates within the published limits; no figure
  match without Fig. 1".
- Stop pursuing pixel recovery unless Fig. 1 appears cheaply.
- For stage 3, use per-biomass Monod uptake with explicit yields and
  maintenance. Sweep the acetogen threshold level, with temperature shape
  from the text's monotonicity, rather than fitting it.

## Reproduce

```sh
uv run python models/haze_world/review/uptake_threshold_inversion.py
```
