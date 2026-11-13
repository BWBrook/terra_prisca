# Step 3b: reference reading notes

Claude (Opus 5.5), 12–13 November 2026. These notes cover the references
tagged in [03b-paragraph-abstracts.md](03b-paragraph-abstracts.md) that had
been checked only by title. All eleven are now read in full text. Five were
retrieved directly; Barry supplied the other six through UTAS on 13 November. PDFs
are stored in `local/sources/paper_refs/`, which is gitignored and never
pushed. Notes are in my own words.

Codex's targeted review (13 November) checked the M6, D4 and D5 uses without
repeating the full reference search. It corrected the Bebout measurement
description and separated the reasons for population discreteness from the
chosen numerical extinction rule.

| Reference | DOI | Paragraph | What it supports |
|---|---|---|---|
| Lovelock & Margulis 1974 | 10.1111/j.2153-3490.1974.tb01946.x | I1 | The Gaia proposal: the biosphere actively keeps planetary conditions favourable as solar output rises. This is the origin of the question in I1. |
| Khammash 2021 | 10.1016/j.cels.2021.05.020 | I2, D2 | Perfect adaptation returns a variable exactly to its set point after a sustained disturbance; *E. coli* chemotaxis is the lead example. Integral feedback delivers it provided the closed loop stays stable. A "leaky" integrator (degradation or dilution of the controller) introduces steady-state error. Adaptation is a steady-state property and guarantees nothing about transient performance; points to Olsman et al. for the stability–performance trade-offs. |
| Sagan & Mullen 1972 | 10.1126/science.177.4043.52 | I3 | The original faint-young-Sun argument. Adopts a 30% rise in solar luminosity over Earth history (best estimate then 40 ± 10%) and cites geological evidence for liquid water 2.7–4.0 Gyr ago. Supports the paradox; Feulner supplies the modern figure. |
| Feulner 2012 | 10.1029/2011RG000375 | I3 | Stellar models give the early Earth about 25% less solar input than today. Geological evidence nonetheless shows liquid water through the Archean. Supports "about a quarter less sunlight". |
| Haqq-Misra et al. 2008 | 10.1089/ast.2007.0197 | I3 | Organic haze begins to form at CH₄/CO₂ ≈ 0.1 in their model. Surface temperature peaks in the thin-haze range (0.1–0.2) and drops well below freezing as the haze builds; the haze has an anti-greenhouse effect. Supports "above a threshold, methane forms an organic haze that cools the surface". |
| Fu et al. 2019 | 10.3389/fmicb.2019.02418 | I3 | Digester sludge incubated under H₂/CO₂. Acetogenesis took a large share of hydrogen use at 15 °C, and methanogenesis dominated at 30 °C. Direct evidence that temperature shifts the competition. |
| Held et al. 2010 | 10.1175/2009JCLI3466.1 | M3 | A climate model separates a fast surface response, relaxing over about 4 years, from a slow response tied to the deep ocean that lasts centuries. Grounds our τ range: years for the fast mode, centuries for the slow. |
| Mollison 1991 | 10.1016/0025-5564(91)90009-8 | M6 | The "atto-fox" passage: a continuous rabies model never lets infected density reach zero, so a remnant of 10⁻¹⁸ fox per km² starts a spurious second epidemic wave. Mollison traces this to modelling populations as continuous rather than discrete. It motivates discreteness; our total one-cell cutoff and ten-year counting interval remain model choices. |
| Fukami 2015 | 10.1146/annurev-ecolsys-110411-160340 | D5 | Defines priority effects broadly through arrival-order dependence; inhibitory and facilitative effects both count, and prior-residence advantages have received more attention. Our late invaders won all 24 tested invasions under the stated counting rule, contrasting with incumbency advantage. Both arrival orders end with one group; this concerns survivor identity and mixed-community assembly. |
| Hoehler et al. 2001 | 10.1038/35085554 | D4 | Modern hypersaline mats (Guerrero Negro). Hydrogen partial pressure in surface bubbles swings by four orders of magnitude over a day, reaching about 10 kPa at night. Methane production is confined to the high-hydrogen mat layer, where hydrogen relieves sulfate reducers' advantage. Used here for the hydrogen/methane context. |
| Bebout et al. 2004 | 10.1111/j.1472-4677.2004.00024.x | D4 | The same mats held at Archean-like low sulfate. Methane flux rose up to tenfold but stayed a small share of carbon turnover. The methods include organic-acid analysis with acetate, and results report organic-acid fluxes. Less than 0.4% of fixed carbon left as methane, and most carbon not used by sulfate reducers left as organic acids. D4 cites this because it bears on f, the share of acetate returned to methane. These data do not calibrate the acetate-feedback law or habitat-temperature model. |

## Resolution of the `[find]` and pending tags

- **M3 (climate response time):** Held et al. 2010.
- **M6 (finite-population motivation):** Mollison 1991 illustrates spurious
  recovery from fractional individuals. M6 states our chosen cutoff and
  counting interval separately.
- **D4 (mats):** Hoehler et al. 2001 with Bebout et al. 2004 support the
  hydrogen/methane context. Bebout includes organic-acid measurements;
  neither source supplies this model's acetate-feedback or temperature-spread
  calibration. The proposed test adds acetate stocks and turnover, their
  effect on hydrogen requirements, habitat temperatures and cell exchange.
- **D5 (arrival order):** reworded after reading Fukami 2015 to say that the
  late arriver won, reversing the most-studied form of priority effect.

## Reconciliation (Claude, 13 November)

Claude accepted Codex's corrections in `db403cb`, including the Bebout
correction: Claude's earlier note that Bebout held no acetate data was wrong.
D4 now also cites Bebout for the dominance of organic acids over methane in
mat carbon loss. The plain-style pass restored a direct R3 heading and
closing sentence, and D1's explanation that integral control is sensitive to
delay. D1 carries a new `[find]` tag for a control-theory source. No facts
changed.
