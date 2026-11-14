# Budyko–Sellers energy-balance models: faithful reconstruction (branch model/budyko-sellers)

Board discussion 164, status open.

## Message 3374 · Claude (claude-opus-5-5) · proposal

Time: 2026-11-14T01:39:46.232826+00:00

A new track, separate from the haze-world paper. Barry (chat, 14 November 2026), relaying the plan agreed with Fable: "faithful reconstructions of the other base models in docs/vision.md, one at a time … First model: the Budyko–Sellers ice-albedo energy-balance models." The work is on branch `model/budyko-sellers` in its own worktree. It touches only `src/terra_prisca/budyko_sellers/`, `models/budyko_sellers/` and `tests/`, and is not coupled to the haze-world. A Claude session will review the build in this thread before merge.

**Sources (verified against Crossref).**
- Budyko, M. I. (1969). The effect of solar radiation variations on the climate of the Earth. *Tellus* 21(5), 611–619. doi:10.3402/tellusa.v21i5.10109 (also registered as 10.1111/j.2153-3490.1969.tb00466.x). Obtained from tellusjournal.org; the journal page shows CC BY 4.0.
- Sellers, W. D. (1969). A global climatic model based on the energy balance of the Earth-atmosphere system. *J. Appl. Meteorol.* 8(3), 392–400. doi:10.1175/1520-0450(1969)008<0392:AGCMBO>2.0.CO;2. **Not yet obtained:** the AMS site refuses automated access, so I have asked Barry for the PDF. Sellers' fidelity targets will be posted here once I have the paper. I will not set them from memory.

**Budyko (1969): the results that define fidelity.** These are the paper's own computed results. Figs 1–2 are observational inputs.
1. **Fig. 3**: the computed present-day zonal profile T₀(φ). The printed observed curve T is data. It serves as a benchmark for what Budyko called "good agreement", not as a model target.
2. **Fig. 4**: the profiles T₀, T₁.₀ and T₁.₅ for radiation reduced by 0, 1.0 and 1.5%.
3. **Fig. 5**: the planetary temperature Tₚ and the ice-edge latitude φ₀ against ΔQₚ/Qₚ, up to the critical point.
4. **Fig. 6**: the ice-free profile T_q against T₀.
5. **Numbers in the text**:
   - 1.5 °C per 1% with fixed albedo 0.33;
   - ΔTₚ of −5 and −9 °C at −1 and −1.5%;
   - an ice-edge shift of 10–18°;
   - runaway past −1.6%, with the ice edge near 50°;
   - an ice-free polar mean "several degrees below zero".
6. **Fig. 2**, as an input check: refitting the printed points should return β = 0.235.

**Scoring.** The Daisyworld review asked for a two-way score that identifies each printed curve. I will trace each printed curve separately from the scan, calibrated from its tick marks, and report RMSE in data units, both directions, plus the key points listed above.

**Null controls.** The score must reject each of these:
- (a) no ice-albedo feedback, with the ice edge held at 72°;
- (b) no change, with T₀ offered as T₁.₀ and T₁.₅;
- (c) two alternative readings of eqs (6)–(7) that the text leaves open:
  - the albedo profile translated with the edge rather than stepped;
  - S counted against the whole globe while ice grows in one hemisphere.

**Prototype finding.** The step reading reproduces the text closely; the other readings in (c) do not:
- α = 0.62 poleward of φ₀ and 0.32 equatorward, with 0.50 used for the edge temperature where T = T(72°) at present;
- the critical point is at −1.64% and 51.5° (published: −1.6%, about 50°);
- ΔTₚ is −4.7 and −8.0 °C at −1 and −1.5% (published: −5 and −9);
- the ice edge is at 61.3° and 55.9° (published shift: 10–18° from 72°);
- the translated profile gives runaway at −0.7%;
- the whole-globe S gives −4.0% at 39°.

**Interpretive choices recorded so far.**
- Annual-mean insolation by latitude is computed from obliquity 23.45° on a circular orbit, because the paper gives no Q(φ) table.
- A month is 365.25/12 days, which converts 1.92 cal cm⁻² min⁻¹ into Qₚ = 21.04 kcal cm⁻² month⁻¹. That value reproduces αₚ = 0.33 and 1.56 °C per 1%.
- The latitude field is continuous rather than 10° nodes.
- Tₚ′ comes from eq. (5) rather than an observed value.

An open discrepancy to chase: my computed T₀ is warmer than the printed Fig. 3 at low latitudes (by about 2 °C at the equator before digitising). This suggests that Budyko's Q(φ) table differs from exact orbital insolation.

## Message 3375 · Claude (claude-opus-5-5) · evidence

Time: 2026-11-14T01:53:49.813154+00:00
Reply to: 3374

**Budyko (1969) is built and ready for review.** Branch `model/budyko-sellers`, commit 1557b36. The model page is `models/budyko_sellers/README.md`. Run `uv run pytest tests/test_budyko1969.py` (12 tests; the fidelity test needs the CC BY scan in `local/`, SHA-256 on the page).

**Method.**
- **Exact branch.** Eq. (7) is linear in ΔQₚ/Qₚ for a fixed ice edge, so the ice-edge branch of Fig. 5 is solved exactly, stable and unstable parts alike.
- **Digitising.** Every printed curve in Figs 3–6 is traced separately: seeded strokes for solid curves, boxed dashes for dashed ones. Each figure is calibrated from its own ticks; the largest tick residual is 1.7 px, about 0.16 °C. Scores are column RMSE in data units, plus a two-way pixel distance.

**Readings fixed by the figures.** These replace the prototype readings in my opening post:
- **Present albedo profile.** The stated 60/70/80° values are kept as a profile. Stepping 0.32 to 0.62 at 72° fits worse.
- **Planetary albedo.** αₚ is the area mean, 0.341. It gives Tₚ = 15.1 °C, against 14.9 °C printed. The insolation-weighted mean gives 17.3 °C.
- **Ice albedo.** The step reading for ice holds: 0.62 poleward of the edge, 0.50 for the edge temperature.
- **Area basis of S.** S is counted over one hemisphere.

**Fidelity, faithful reading (RMSE).**
- Fig. 4: T₀ 0.65, T₁.₀ 0.34 and T₁.₅ 0.91 °C.
- Fig. 6: T₀ 0.75 and T_q 0.64 °C.
- Fig. 5: Tₚ 0.66 °C and φ₀ 1.53°.
- Runaway: −1.67%, against −1.63% printed and "1.6%" in the text, with the edge at 51.5°.
- ΔTₚ at −1 and −1.5%: −4.6 and −7.7 °C. The printed values are −4.3 and −9.0 °C; the text says −5 and −9 °C.

**Controls (RMSE on T₁.₅ and φ₀).**
- No feedback: 7.3 °C and 9.1°.
- No change: 9.3 °C and 9.1°.
- Insolation-weighted αₚ: 2.4 °C.
- Stepped present albedo: 1.9 °C.
- Translated profile: runaway at −0.7%.
- Whole-globe S: runaway at −5.1%.

**Two findings for the reviewer to test.**
1. **The paper's own T₀ curves disagree.** The T₀ drawn in Figs 4 and 6 matches the solid curve of Fig. 3, labelled *observed* (RMSE 0.49 °C). It does not match the dashed curve labelled *computed* (1.95 °C). Our T₀ follows Figs 4 and 6 (0.65–0.75 °C) and the solid curve (0.96 °C), and misses the dashed curve (2.46 °C). Either Fig. 3's labels are swapped, or Figs 4 and 6 draw observations as the baseline. The perturbed results are unaffected.
2. **The printed Fig. 5 branch is straighter than ours.** To hold the edge at 65° Budyko needs −0.71% (we need −0.56%); at 55° he needs −1.45% (we need −1.57%). The likely cause is his insolation table, which the paper does not give. Obliquity alone moves the runaway between −1.3% and −2.2% over 22–24.5°. We have not tuned it.

**Points worth attacking:**
- the Fig. 3 dash and label clipping in `scan_budyko1969.py`;
- whether eq. (6)'s 0.30S should also count the 72–80° band, which our local albedo brightens;
- whether the area-mean αₚ is the right reading of "planetary values of radiation and albedo".

Sellers (1969) is still blocked on the source (the AMS site refuses automated download). Its targets will be posted here when I have it.

## Message 3378 · Claude (claude-opus-5-5) · proposal

Time: 2026-11-14T03:24:54.010777+00:00
Reply to: 3374

**Sellers (1969): what defines fidelity**

Source: Sellers, W. D. (1969), J. Appl. Meteorol. 8, 392–400, doi:10.1175/1520-0450(1969)008<0392:AGCMBO>2.0.CO;2. Barry supplied the PDF from AMS (local/ only). It is a 300-ppi 1-bit scan with no text layer; Tables 1–3 are transcribed by hand at native resolution.

The inputs are Tables 1–2 (b, Z, α_d, Δp, Δz, Q_s, K_h, K_w, K_0, a), eqs (1)–(13) and S = 2.00 ly/min. The targets are what the model *computed*:

1. **Present state.** The circled points in Fig. 4 (T, v and α_s for 18 belts and 17 circles), Fig. 3 (C, Lc, F and P at the circles) and Fig. 2 (ΔC, LΔc, ΔF and R_s per belt). The text gives T̄ ≈ 14.0 °C. The Fig. 5 inset gives the computed albedos of the untreated polar belts (0.61/0.58 N, 0.79/0.84 S).
2. **Solar-constant response.** Fig. 6 plots T̄(S) for fixed albedo, α = b − 0.009T_g and α = b − 0.005T_g, plus the K×2 and K×0.5 symbols. Text numbers:
   - 0.009 law: about −2% gives an ice age with the ice edge at 50° and the jump to ice cover at −100 °C;
   - 0.005 law: severe ice age only at −5 to −6%;
   - fixed albedo: −10% cools 14.3 °C at 0–20° and 50–60°, and 13.0 °C at 80–90°; +10% warms about 12 °C;
   - K×2: about +5 °C, with the NH equator–pole difference falling from 48 to 28 °C;
   - K×0.5: below −70 °C at the poles and below −10 °C at 45°.
3. **Profiles.** Fig. 7, curves a–i, with S at +0, +1, +5, +10, −1 and −2%, K×2 and K×0.5, and −3% with K×2.
4. **Polar albedo manipulation.** Fig. 5: ΔT for the six inset cases. Text: about 7 °C poleward of 70N for case 3, and 12–15 °C in the Antarctic with 4 °C in the Arctic.
5. **Secondary, because it needs a land fraction the paper does not give:** Table 3 ΔT₁ and ΔT₂ for added heating H.

Scoring follows Budyko. Each printed curve or point set is traced separately from the scan, and the circled points are located by ring-template matching at the known belt or circle latitudes. Results are RMSE in data units, with these controls:
- nulls: radiative equilibrium with no transport, observed T offered as the solution, and fixed albedo where Sellers did not use it;
- rejected readings for each open choice.

**Choices the paper leaves open, to be decided by fit and recorded:**
- l′, the ocean length of each circle, is not tabulated. I'll compute it from the R `maps` world coastline; the alternative is a ±5° band average.
- The saturation vapour pressure formula is not given. I'll use Clausius–Clapeyron with Sellers' own L, ε and R_d, with Tetens as an alternative.
- T in vT₀ (eq. 12): Kelvin. The K_h values near the equator (133 and 68 ×10¹⁰) only make sense if the vT term is large.
- |ΔT̄| (eq. 8): the l-weighted mean over all 17 circles, or over each hemisphere.
- The 0.005 law, "b adjusted accordingly": either continuous at 283.16 K (α_d + 0.005(283.16 − T_g)) or anchored to keep the present albedo. Fig. 6 decides.
- Solver: Sellers shot from the north pole on T(80–90N) and took the physical root of the quadratic in ΔT. I'll solve the same 18 belt balances simultaneously, check the result against a pole-to-pole march, and use continuation in S to follow branches.

Same branch, model/budyko-sellers. Code goes in src/terra_prisca/budyko_sellers/sellers1969.py.

## Message 3384 · Claude (claude-opus-5-5) · evidence

Time: 2026-11-14T03:51:47.851104+00:00
Reply to: 3378

**Sellers (1969) is built, scored and ready for review.** Commit dffd375 on model/budyko-sellers; the full write-up is in models/budyko_sellers/README.md, section "Sellers (1969)".

**Present state.** Computed from Tables 1–2 with nothing fitted.
- T̄ is 14.06 °C; Sellers says "about 14.0".
- RMSE against the circled points:
  - Fig. 4: T 0.58 °C, v 0.26 cm/s, α 0.002;
  - Fig. 3: C, Lc, F, P 2–5 kcal/cm/s, on a ±600 scale;
  - Fig. 2: belt fluxes 0.7–0.9 kly/yr.
- The no-transport null scores 81 °C on Fig. 4 T.

**Experiments.**
- Fig. 5 curves 6 and 5 (circled): 0.17 and 0.25 °C. Traced curves 1–4: 0.3–0.8 °C. The untreated polar albedos in the inset are reproduced to 0.02.
- Fig. 6:
  - 0.009 law: circles at 0.75 °C; jump to ice at S = 1.9573 (printed vertical 1.9544); ice-covered state about −100 °C.
  - 0.005 law: circles at 0.91 °C, steepest fall at 1.87 as printed.
  - fixed albedo: 0.30 °C.
  - nulls: no change 57 °C, fixed albedo 54 °C.
- Fig. 7: curves a–e, g and i at 0.5–0.9 °C; f (−2%) 2.4 °C; h (K×0.5) 3.9 °C.
- Table 3: ΔT₁ 0.24 °C, ΔT₂ 0.45 °C.
- Text numbers (K×2 +5.2 °C; fixed ±10%; the Antarctic and Arctic cases; K×0.5) all match. The exceptions are listed below.

**Readings decided by fit.**
- vT in eq. (12) uses Kelvin. With °C, Fig. 4 T scores 14 °C.
- |ΔT̄| is a global mean, not per hemisphere (per hemisphere: Fig. 4 T 1.2 °C, Table 3 2.3 °C).
- The 0.005 law keeps today's albedo. Continuity at α_d would make today 18 °C.
- Eq. (5) uses max(b − 0.009T_g, α_d). Table 1's 2.548 against 0.009 × 283.16 = 2.54844 otherwise leaves a 0.0004 step with no equilibrium on it.
- Ocean fraction (R `maps`, circle or band) and the vapour-pressure formula (Clausius–Clapeyron or Tetens) make no material difference.

**Findings for the reviewer to pressure-test.**
1. Curve i (−3%, K×2) has two equilibria, at T̄ 13.0 and 3.1 °C. Sellers' text (equator 16 °C colder, NH equator–pole 26 °C), his Fig. 6 square and his Fig. 7 curve all sit on the cold one, which we reproduce: 16.0 and 26.3 °C, curve RMSE 0.61. The paper does not mention the multiplicity.
2. Close to the jump, Sellers' planet is colder although his jump comes at a lower S (Fig. 6 at S = 1.96: 1.6 against 3.5 °C). This explains the curve f misfit. Not tuned.
3. Two text–figure inconsistencies in the paper:
   - K×2 NH equator–pole difference: text 28 °C, his own Fig. 7 curve g 21.8 °C, reconstruction 19.7 °C.
   - Present-day NH equator–pole difference: text 48 °C, his own Fig. 4 circles 45.5 °C.

**Digitising.**
- Affine frames are fitted to the ruled frame and ticks; the largest calibration residual is 1% of an axis range.
- An annulus detector reads the circles. Eight detections were rejected by inspection; they are listed in NOT_POINTS.
- A seed-based column/row tracker reads the unmarked curves. Fig. 6 marks are read by eye and refined on the scan.
- Model output never enters the reading.
- The AMS scan is not in the repository. The overlay plots digitised values only.

**Tests.** 9 new in tests/test_sellers1969.py; 21 pass across the two models. They include Sellers' march reproducing the simultaneous solution to 1e-6 K, and scan fidelity with null margins.

Requested: a Claude review of both builds (Budyko 3375, Sellers here) before merge.
