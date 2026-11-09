# Source recovery: methane loss and the low-methane branch

Codex, 9 November 2026. Recovered evidence, not a fitted photochemical closure.

## Arney 2016 sustaining flux

[Primary text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5148108/),
[DOI](https://doi.org/10.1089/ast.2015.1422), accepted manuscript pp. 14,
41–42 and 45:

- Methane is prescribed at the surface and varies with altitude.
- The onset flux range, 1–3×10¹¹ molecules cm⁻² s⁻¹, spans the allowed CO₂
  cases; individual flux–ratio pairs are not provided.
- The cited serpentinization estimate is 6.8×10⁸ for one Earth mass and
  1.3×10⁹ for five Earth masses, in the same flux units.
- Haze lowers the sustaining flux at a fixed methane abundance once its UV
  optical depth exceeds roughly one. This does not quantify the slope along
  a sequence of increasing methane.

No per-ratio output grid was found in the paper, supplementary reaction and
boundary-condition tables or the current public Atmos output directory. The
6,253–18,758-year estimate for case B at r = 0.15 follows only after assigning
the aggregate flux range to that case and applying the model's well-mixed,
28-g/mol column assumption. It is not a published methane lifetime.

For a future photochemical family, let N(r) be the methane column and
F_required(r) the sustaining surface flux. The consistent storage equation is

\[
\dot r=[F_{source}-F_{required}(r)]/N'(r).
\]

Flux balance determines equilibria. Transient dynamics additionally need
N′(r); the present constant conversion c is an explicit approximation to it.
With the quoted flux units this equation gives r per second; multiply by
seconds per year when using the budget model's clock.
Neither a declining loss slope nor a self-shielding-induced instability is
established by the accessible 2016 evidence.

[Arney et al. 2018](https://doi.org/10.1089/ast.2017.1666),
[accepted manuscript](https://arxiv.org/abs/1711.01675), Figs 4–5, is a later
lead: corresponding grids use methane-flux and surface-ratio axes. Matching
optical-depth contours could recover sparse pairs, but the organic-sulfur
cases differ from 2016 and saturated contours make inversion ambiguous.
No 2018 curve has been substituted into the current model.

## Low methane: published checkpoints recovered, scenarios kept separate

[Eager-Nash et al. 2023](https://doi.org/10.1029/2022JD037544), Fig. 5a–b,
provides the [recovered low-methane family](../../haze_response/README.md):
36 checkpoints, including zero methane, for four CO₂ backgrounds. At
pCO₂ = 1000 Pa, the zero-methane temperature is approximately 278.67 K.
That CO₂ level matches Arney A, but the 3D cloud/ice model and surface
treatment differ. It is a structural comparison, not a missing segment to
paste into Arney's response; it does not replace case B's assumed 265-K
endpoint.

[Byrne & Goldblatt 2015](https://doi.org/10.5194/cp-11-559-2015) was inspected
as another candidate. Its 0.8 S₀ and fixed 0.8-bar N₂ calculations, with
alternative humidity treatments, do not furnish a matched Arney case.
[Haqq-Misra et al. 2008](https://doi.org/10.1089/ast.2007.0197) remains a
candidate rather than a recovered numerical closure in this turn.

No matched 2016 low-methane branch or loss law is claimed. Keep the existing
extensions visibly assumed, compare separate published scenarios, and avoid
evolutionary conclusions that depend on an untested splice.
