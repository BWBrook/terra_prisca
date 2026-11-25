# Bistability of atmospheric oxygen (Goldblatt, Lenton & Watson 2006)

Why did oxygen jump at the Great Oxidation instead of creeping up? Goldblatt,
Lenton & Watson (2006) proposed that the atmosphere had two stable states.
Below about 10⁻⁵ PAL, methane destroys oxygen photochemically as fast as
photosynthesis makes it. Above a few 10⁻³ PAL, an ozone layer shields the
methane–oxygen reaction and oxygen stays high. In between, a modest fall in
the supply of reductants, or a small rise in organic-carbon burial, tips the
system from one state to the other in a few hundred thousand years.

This page holds a reconstruction of their three-box model. It is scored
against the vector geometry of the published Figs 2 and 3, and every number the
text states is recomputed.

Status: **built and scored; awaiting Codex review, then Gemini review before
merge** (board thread 194).

## Sources

The citation was checked against Crossref on 25 November 2026.

- Goldblatt, C., Lenton, T. M. & Watson, A. J. (2006). Bistability of
  atmospheric oxygen and the Great Oxidation. *Nature* 443(7112), 683–686.
  [doi:10.1038/nature05169](https://doi.org/10.1038/nature05169).
  - Publisher PDF supplied by Barry: four pages, SHA-256
    `37a2345b997afe01dad259c4f2525f18edbbdc3703ad545211cd859ebfb58112`.
    Its figures are vector drawings, so every curve's vertices can be read
    exactly.
  - Supplementary Information downloaded by Codex from the publisher: 12 pages
    with the full derivation, SHA-256
    `d2236ec0ec767fbcf61031cc4faf3655f1f8f050633e3d18205c1263109d5046`.
- Goldblatt's publications page (colingoldblatt.net/publications, "up-to-date
  as of July 2022") attaches a correction to the paper. It gives the
  methane-oxidation polynomial to seven decimals, adding "correct p is
  especially important to reproduce the results". It also states the
  hydrogen-escape coefficient as s = 3.7 × 10⁻⁵ yr⁻¹. Codex found the note;
  Claude checked its wording.

Both PDFs are copyrighted and stay in `local/sources/goldblatt_lenton_watson/`
(gitignored). The repository holds only the vertex coordinates read from the
figures, never the drawings.

## Code

| File | Role |
|---|---|
| `src/terra_prisca/goldblatt_lenton_watson/glw2006.py` | The model: equations, readings, steady states, stability, transients, redox budget |
| `src/terra_prisca/goldblatt_lenton_watson/vectors.py` | Reads the Fig. 2 and Fig. 3 paths from the article PDF and calibrates them |
| `src/terra_prisca/goldblatt_lenton_watson/fidelity_glw2006.py` | Scores the readings against the figures and recomputes the stated numbers |
| `tests/test_glw2006.py` | Equations, steady states, budget closure, and the Fig. 2 verdicts |

Regenerate the figure vertices, which needs the PDF and PyMuPDF:

```bash
uv run --with pymupdf python -m terra_prisca.goldblatt_lenton_watson.vectors
```

Regenerate every score, table and the overlay, from the committed vertices
only (about 30 s):

```bash
uv run python -m terra_prisca.goldblatt_lenton_watson.fidelity_glw2006
```

## The model as published

Three reservoirs: methane M and oxygen O in the atmosphere and ocean mixed
layer, and organic carbon C in the crust, all in moles (SI eqs 1–3):

    dM/dt = ½ Ω (N + r) − s M − ½ Ψ M^0.7 − ½ Ω (β (N + r) − w C)
    dO/dt = Ω N − (1 − Ω) r − s M − Ψ M^0.7 + (1 − Ω)(β (N + r) − w C)
    dC/dt = β (N + r) − w C

- N is oxygenic net primary productivity and r the net input of reductant
  (ferrous iron), both in mol O₂ equiv. yr⁻¹.
- Ω = (1 − γ)(1 − δ) is the fraction of decomposed organic matter that reaches
  the atmosphere as methane and oxygen.
  - Aerobic respiration takes γ = O/(d_γ + O), with d_γ = 1.36 × 10¹⁹ mol.
  - Methanotrophy takes δ = O/(d_δ + O), with d_δ = 2.73 × 10¹⁷ mol.
- Photochemical oxidation of methane is Ψ M^0.7, with
  Ψ = 10^(a₁ψ⁴ + a₂ψ³ + a₃ψ² + a₄ψ + a₅) and ψ = log₁₀ O. The fit is valid for
  10⁸ < O < 10²⁰ mol.
- Hydrogen escape removes s M of both methane and oxygen.
- A fraction β of organic production is buried, and buried carbon weathers at
  rate w = 6 × 10⁻⁹ yr⁻¹.

In steady state M = r/s and C = β(N + r)/w, and O solves

    Ω N + (Ω − 2) r − Ψ (r/s)^0.7 = 0          (SI eq. 12)

This does not depend on β. Up to three roots exist; where there are three, the
middle one is unstable.

## Readings

Each reading is a fixed set of values taken from a source. None was tuned to a
figure. All three were declared on board thread 194 before any was scored.

| Reading | Polynomial a₁…a₅ | s (yr⁻¹) | Source |
|---|---|---|---|
| `faithful` | 0.0030, −0.1655, 3.2305, −25.8343, 71.5398 | 2.03 × 10⁻⁵ | Article Methods and SI, as printed |
| `author_p` | 0.0030084, −0.1655405, 3.2305351, −25.8343054, 71.5397861 | 2.03 × 10⁻⁵ | Goldblatt's full-precision coefficients |
| `author_corrected` | as `author_p` | 3.7 × 10⁻⁵ | Both of Goldblatt's corrections |

The transients also need β, which the source never prints. Two values are run:

- **SI β = 2.67 × 10⁻³**, from the SI's statement that β(N + r) = 10¹³ mol yr⁻¹
  today, with modern N and r = 7.5 × 10¹⁰;
- **Fig. 3d β = 2.00 × 10⁻³**, read off the published Fig. 3d. At the step,
  burial minus weathering jumps by β ΔN, and the printed jump is
  2.25 × 10¹¹ mol yr⁻¹. Scores of that one trace under this β are flagged as
  fitted.

## Interpretive choices

- **PAL = 0.2095 μ = 3.714 × 10¹⁹ mol.** The source gives μ, the moles in the
  present atmosphere, but never states PAL in moles. The figure confirms the
  choice: the vertical offset that best aligns `author_p` with all four Fig. 2
  curves is −0.001 decades.
- **The Fig. 2b dashed curve is drawn at r = 3 × 10¹¹, not the captioned
  3 × 10¹⁰.** Both values are scored.
- **The Fig. 3 transients start from the lowest stable steady state** of the
  pre-step parameters, with C in balance. This is the low-oxygen state the
  caption describes.
- **The Fig. 3 methane trace is plotted as M in PAL-of-O₂ units on the left
  axis.** The alternative, M/μ in atm on the printed right-hand axis, is scored
  alongside it.
- **The zoom panels of Fig. 3 are registered at the forcing step they draw.**
  In every zoom panel, the step in reductant input sits at 2.39991 Gyr, 90 kyr
  after the labelled 2.4 Gyr. This step is used as time zero for the zoom
  scores; it is a registration, not a fit to O.
- **Transition time is not defined in the source.** Four definitions are
  reported: O crossing 10⁻⁵ PAL, O crossing the upper fold (5 × 10⁻³ PAL), half
  the logarithmic rise, and 90% of it.
- **The reverse switch's forcing is not stated.** The return from high to low
  oxygen is timed for r stepped from 7.5 × 10¹⁰ up to 7.5 × 10¹¹ (the top of
  the BIF band), 10¹², and 3 × 10¹².
- **Below 10⁸ mol the oxidation polynomial is outside its stated range** and
  can create spurious roots, so steady states are sought only above that
  limit. Fig. 2 reaches down to 10⁻¹¹ PAL = 3.7 × 10⁸ mol, inside the range.
- **Stiffness.** The transients are integrated in log M and log O with Radau
  (rtol 10⁻¹⁰). Oxygen's turnover on the low branch is about 0.01 yr, while
  1/w is 170 Myr.

## Fidelity against the published paper

### Reading the figures

Each curve is a stroked polyline in the PDF.

- Paths drawn twice at identical coordinates, in either direction, are counted
  once. Fig. 2 then has 12 distinct paths: in each panel, a solid and a dashed
  curve, each with two stable branches and a dotted unstable connector.
- The calibration fits the decade ticks:
  - Fig. 2 ticks fit to 0.0026 decades, and the frames lie at the axis limits
    to 0.0025 decades;
  - the grey reference lines fall at log₁₀ r = 10.8753 and log₁₀ N = 15.5742,
    against 10.8751 and 15.5740 for the captioned 7.5 × 10¹⁰ and
    3.75 × 10¹⁵;
  - the Fig. 3 ticks fall within 0.006 decades or 0.013 × 10¹¹ mol yr⁻¹ of
    their labels.
- Distances are measured on the printed page, in points (1 pt = 1/72 inch).
  The score is the RMS distance from each printed vertex to the model curve.

[`fidelity/glw2006_vectors.csv`](fidelity/glw2006_vectors.csv) holds the
vertices and [`fidelity/glw2006_calibration.csv`](fidelity/glw2006_calibration.csv)
the checks.

### Fig. 2: steady states

RMS distance from the printed vertices to each reading
([`glw2006_fig2.csv`](fidelity/glw2006_fig2.csv)):

| Curve | `faithful` | `author_p` | `author_corrected` | Null: shifted one decade | Null: flat |
|---|---|---|---|---|---|
| 2a, N = 3.75 × 10¹⁵ | 8.27 pt | **0.059 pt** | 2.42 pt | 8.57 pt | 29.2 pt |
| 2a, N/2 | 7.64 pt | **0.057 pt** | 2.35 pt | 8.64 pt | 29.3 pt |
| 2b, r = 7.5 × 10¹⁰ | 6.25 pt | **0.046 pt** | 1.92 pt | 10.3 pt | 31.9 pt |
| 2b dashed, r = 3 × 10¹⁰ (captioned) | 16.2 pt | 8.36 pt | 10.8 pt | 10.4 pt | 31.7 pt |
| 2b dashed, r = 3 × 10¹¹ | 6.31 pt | **0.046 pt** | 1.94 pt | 10.4 pt | 31.7 pt |

- `author_p` puts every curve within a twentieth of a printed point. Stable
  and unstable sections agree for 99.7% of vertices; the rest lie at the folds.
- With the printed four-decimal coefficients, `faithful` misses by about as
  much as shifting the printed curve by a full decade.
- The fold positions under `author_p` match the printed connector ends to
  0.004 decades in r or N
  ([`glw2006_folds.csv`](fidelity/glw2006_folds.csv)). At modern N the
  bistable range is r = 1.34–5.52 × 10¹¹; the printed range is
  1.35–5.48 × 10¹¹. Under `faithful` it is 3.3 × 10¹¹–3.4 × 10¹².

### Fig. 3: the two triggers

The model starts from the low state and steps at 2.4 Gyr ago, exactly as the
caption states: (a) r falls from 3 × 10¹¹ to 7.5 × 10¹⁰; (c) N rises from
3.6375 × 10¹⁵ to 3.75 × 10¹⁵ at r = 3 × 10¹¹. Scores are in
[`glw2006_fig3.csv`](fidelity/glw2006_fig3.csv).

| Trace (main panels) | `author_p`, Fig. 3d β | `author_p`, SI β | `author_corrected`, Fig. 3d β | `faithful` |
|---|---|---|---|---|
| 3a O₂ | 0.026 pt | 0.026 pt | 0.94 pt | 8.1 pt |
| 3a CH₄ (PAL axis) | 0.022 pt | 0.022 pt | 1.10 pt | 0.91 pt |
| 3b escape, net | 0.028 pt | 0.027–0.028 pt | 0.36–0.44 pt | 2.5 pt |
| 3c O₂ | **0.025 pt** | 0.64 pt | 1.24 pt | 7.6 pt |
| 3c CH₄ (PAL axis) | 0.025 pt | 0.85 pt | 1.37 pt | 0.69 pt |
| 3d escape, net | 0.028–0.031 pt | 0.53–1.05 pt | 0.34–0.38 pt | 2.0–2.2 pt |
| 3d burial | 0.029 pt (fitted) | 1.53 pt | 0.029 pt (fitted) | 0.029 pt (fitted) |

- `author_p` with the Fig. 3d β reproduces every main-panel trace to about
  0.03 pt.
- The β read from one point of the 3d burial trace also brings the
  independent 3c oxygen and methane traces from 0.6–0.9 pt down to 0.025 pt.
- Methane sits where M/PAL puts it (0.022–0.025 pt), not on the printed
  right-hand atm axis (1.7–1.9 pt). Under `author_corrected`, the atm axis is
  the better of the two (0.58–0.67 pt). Taken jointly, the figure was drawn
  with s = 2.03 × 10⁻⁵ and the right-hand axis is mislabelled.
- In the zoom panels, registered at their drawn step, `author_p` is 0.2–0.6 pt
  from the oxygen, methane and 3d budget traces. The 3b zoom budget is
  0.8–1.3 pt out. The zooms draw the pre-step fluxes at different levels from
  the main panels: −3.33 against −2.99 × 10¹¹ for the 3b input, and −2.84
  against −3.00 and 3.11 against 3.00 × 10¹¹ for the 3d input and escape.

![Model curves over the published vertices](fidelity/glw2006_overlay.png)

### Stated numbers, recomputed

From [`glw2006_claims.csv`](fidelity/glw2006_claims.csv), under `author_p`:

| Claim | Stated | Reconstruction |
|---|---|---|
| Steady states at modern N, r = 3 × 10¹¹ | low branch, ~10⁻⁶ PAL | 1.28 × 10⁻⁶ (stable), 4.95 × 10⁻⁴ (unstable), 0.0231 (stable) PAL |
| Steady states at modern N, r = 7.5 × 10¹⁰ | high branch only, ~0.1 PAL | 0.0816 PAL, the only state |
| Edges of the two branches | low < 10⁻⁵, high > 5 × 10⁻³ PAL | low up to 1.99 × 10⁻⁵, high down to 4.48 × 10⁻³ PAL |
| Prebiotic rise to the low state | when N exceeds r | at r = 7.5 × 10¹⁰, O reaches 10⁻¹² PAL at N = 8.7 × 10¹⁰ |
| Total oxidation, case a | 3 × 10¹⁸ mol | 3.05 × 10¹⁸ mol |
| Total oxidation, case c | 9 × 10¹⁷ mol | 9.4 × 10¹⁷ (Fig. 3d β); 9.7 × 10¹⁷ (SI β) mol |
| Transition time, case a | 150 kyr | 146 kyr to half the log rise; 126 kyr to 10⁻⁵ PAL |
| Transition time, case c | 50 kyr | 145 kyr (Fig. 3d β); 86 kyr (SI β) to half the log rise |
| Methane fall | factor 2–6 | 4.0 (a); 2.6 (c) |
| Methane re-adjustment, case a | about 50 Myr | 54 Myr for escape to come within 10% of r |
| Organic carbon, case c | +3% over ~500 Myr | +2.8% after 400 Myr, heading to 3% |
| Reverse switch | 3–7 Myr | 6.6 Myr (r → 7.5 × 10¹¹); 4.1 Myr (r → 10¹²); 1.1 Myr (r → 3 × 10¹²) |
| δ¹³C of carbonate | f = 0.206, +0.23‰ | f = 0.2060, +0.227‰ |
| Simplified eq. (6) equivalent to the full eq. (12) | "when oxygen exceeds 1 × 10⁹ PAL" | above 1.9 × 10⁻⁸ PAL to 1% in r; above 4.3 × 10⁻⁹ PAL to 10% |

## What holds

- **The model reproduces both figures once the polynomial has its full
  precision.** Every Fig. 2 curve lies within 0.06 pt of the printed one, and
  every main-panel trace of Fig. 3 within 0.03 pt. The only value read from a
  figure is β, and the same β also fits a trace it was not taken from.
- **The bistability is real in the model as specified.** At modern
  productivity, reductant inputs between 1.34 × 10¹¹ and 5.52 × 10¹¹ mol yr⁻¹
  have two stable states. The low one sits below 2 × 10⁻⁵ PAL, consistent
  with mass-independent sulphur fractionation; the high one sits above
  4.5 × 10⁻³ PAL. The BIF-era input band of 1.25–7.5 × 10¹¹ overlaps this
  range, and today's 7.5 × 10¹⁰ lies on the high branch alone.
- **Both triggers work as described.** A fall in r or a 3% rise in N switches
  the system to about 0.08 PAL in a few hundred thousand years. Total
  oxidation matches the stated 3 × 10¹⁸ and 9 × 10¹⁷ mol. Methane falls by a
  factor of 2.6–4, and in case a it takes about 50 Myr to re-adjust. For
  reductant inputs within and just above the BIF band, the reverse switch
  takes 3–7 Myr, the stated hysteresis.
- **The steady states follow in closed form.** M = r/s and C = β(N + r)/w, and
  oxygen is a one-dimensional root that does not depend on β. The redox budget
  of the surface system closes exactly as escape plus net burial minus
  reductant input.
- **The carbon-isotope arithmetic is right:** f = 0.206 gives +0.227‰.

## What the source got wrong or left inconsistent

- **The printed polynomial coefficients cannot reproduce the paper's results.**
  At four decimals the rounding errors are multiplied by powers of ψ up to
  ψ⁴ ≈ 8 × 10⁴ near O ~ 10¹⁷ mol, and together they change Ψ about
  threefold. The bistable range then moves to
  3.3 × 10¹¹–3.4 × 10¹² at modern N. At r = 3 × 10¹¹, the BIF-era case,
  there is then no low-oxygen state at all, so the Fig. 3a trigger cannot
  happen. Goldblatt's later note supplies the missing precision; without it
  the paper's central result cannot be rebuilt from the paper.
- **The "corrected" hydrogen-escape coefficient does not match the published
  figures.** With s = 3.7 × 10⁻⁵, the Fig. 2a curves shift by 0.26 decades in
  r, and all four Fig. 2 curves miss by 1.9–2.4 pt. The Fig. 3 oxygen levels also move: 0.12 PAL instead of the
  printed 0.08 PAL, and 4.9 × 10⁻⁶ PAL instead of 1.3 × 10⁻⁶ PAL. The
  published figures were drawn with the printed 2.03 × 10⁻⁵.
- **The Fig. 2b caption misstates the dashed curve's reductant input.** The
  curve drawn is r = 3 × 10¹¹ (0.046 pt), not 3 × 10¹⁰ (8.4 pt).
- **The right-hand axis of Fig. 3a and 3c is mislabelled.** It sits exactly
  one decade below the PAL axis, but 1 PAL of O₂ is 0.21 atm. The methane
  trace is drawn in PAL-of-O₂ units on the left-hand scale. Read on the
  right-hand axis as the caption directs, its pCH₄ is a factor of 2.1 too
  low.
- **The text's biological thresholds do not match the constants.** The
  constants give d_γ = 0.37 PAL (100 µM), against the stated Pasteur point of
  0.01 PAL. They give d_δ = 0.0073 PAL, against the stated 2 × 10⁻⁴ PAL; d_δ
  does equal the stated 2 µM. Both text values follow if 1 PAL were
  1.36 × 10²¹ mol, a factor of 37 from the PAL the figures use. The model,
  and therefore the figures, uses the constants.
- **"Equivalent when oxygen exceeds 1 × 10⁹ PAL"** (Fig. 2 caption, SI p. 10)
  cannot be right as printed. The simplified and full equations agree above
  about 10⁻⁸ PAL, so 10⁻⁹ was probably meant.
- **The case c transition time does not match the text.** The text says
  50 kyr. The model takes about 145 kyr under the β that fits the figure, and
  the published zoom panels show 132 kyr, the same as case a (134 kyr).
- **The Fig. 3 zoom panels are not exact enlargements of the main panels.**
  They draw the forcing step 90 kyr after the labelled 2.4 Gyr. Their pre-step
  fluxes also sit 4–11% away from the same fluxes in the main panels.

## What stays open

- **Why β = 0.0020.** The figure's β does not follow from the SI's statement
  that β(N + r) = 10¹³ mol yr⁻¹ today, which gives 0.0027. Steady states and
  case a are insensitive to β; case c's path is not.
- **Where s = 3.7 × 10⁻⁵ comes from.** It may be a value for later work, or
  a conversion of Catling et al. (2001) under a different definition of M.
  Settling this needs Catling et al. (2001) and possibly the authors.
- **The 4–9 °C cooling.** The SI derives it from Kasting, Pavlov & Siefert
  (2001), Fig. 1 and eq. 1, which this reconstruction does not hold. It needs
  that paper.
- **What "transition time" meant.** Half the logarithmic rise reproduces
  150 kyr for case a. No definition tried gives 50 kyr for case c with either
  β.
- **The reverse switch's forcing.** 3–7 Myr follows for reductant inputs from
  the top of the BIF band to 10¹² mol yr⁻¹, but the source never says what it
  ran.
