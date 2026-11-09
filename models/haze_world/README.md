# Haze-world

**Status: conditional model, reviewed 9 November 2026.** This is a new
model, not a reconstruction. It couples methanogens and a finite methane budget
to the [Arney et al. (2016) climate responses](../haze_response/README.md).
Every quantity those curves do not supply is a named assumption with a default
and a sweep.
The [independent review](review/2026-11-09.md) retains the equilibrium result,
qualifies the dynamical reduction, repairs rare-biomass integration and
separates recovered source evidence from assumptions.

**Code.** [`src/terra_prisca/haze_world/methane_budget.py`](../../src/terra_prisca/haze_world/methane_budget.py)
(model) and [`experiments.py`](../../src/terra_prisca/haze_world/experiments.py)
(the runs below). Tests are in
[`tests/test_methane_budget.py`](../../tests/test_methane_budget.py).

```bash
uv run python -m terra_prisca.haze_world.experiments
uv run pytest
```

## Model

The state is an electron-donor pool D, methanogen biomass B and atmospheric
methane M, scaled to a CO₂ column. Identifying atmospheric M with Arney's
**surface** CH₄/CO₂ ratio r assumes well-mixed methane. Arney's methane profile
is not an isoprofile; this column-to-surface mapping is our approximation.

| Equation | Meaning |
|---|---|
| dD/dt = φ − k_D D − U | donor supply, an alternative sink and methanogen uptake |
| U = μ(T) B D/(K + D) | Monod uptake with thermal performance μ(T) |
| dB/dt = Y U − δ B | methanogen growth and loss |
| dM/dt = U + φ_abiotic − M/τ | methane production, abiotic source and first-order loss |
| T = T(M) | climate closure (below) |

Setting donor and biomass derivatives to zero gives an exact **equilibrium
elimination**. Using the resulting expression as a time-dependent scalar
equation is a quasi-steady approximation:

  dr/dt = c [η(T(r)) Φ + Φ_abiotic] − r/τ,  η = max(0, 1 − Φ_K / (Φ (ρ(T) − 1)))

Here:
- Φ is the donor supply as a CH₄-equivalent flux;
- ρ = Yμ/δ is the methanogens' maximum growth over loss;
- Φ_K = K k_D / c is the physical supply at which the abiotic donor level equals K;
- c converts molecules cm⁻² s⁻¹ to ratio units per year.

η is the equilibrium fraction of supply methanogens capture. Feasibility of the
positive branch coincides with invasion of the donor-only equilibrium. An
endpoint integration test checks equilibrium agreement to 10⁻⁴, not equality
of trajectories. Near the headline equilibrium, temperature feedback shortens
the methane response to decades: the full ODE oscillates while the scalar
approximation relaxes monotonically. Comparing biological rates with the bare
10-kyr methane lifetime does not establish time-scale separation.

The full integrator now evolves log biomass when biomass starts positive,
preventing numerical extinction during a cold interval. Exactly zero initial
biomass remains zero. This preserves the deterministic continuum model; it
does not demonstrate survival of a finite population through an arbitrarily
deep biomass decline.

Equilibria are the roots of dr/dt, found on a fine grid and refined. In one
dimension a root is stable when the flow crosses it from + to −; a test confirms
each label by perturbation. Sweeps step the supply and move from the previous
equilibrium to a detected root in the direction of the reduced flow.

## What comes from the source and what is assumed

| Quantity | Treatment | Basis |
|---|---|---|
| T(r) within the extracted domain | Arney Fig. 4, case B by default (all four cases are used in panel c) | Extracted; S/S₀ = 0.81, 2.7 Ga, fixed CO₂ and pressure |
| T(r) below the first vertex (**low-methane bridge**) | T₀ + (T₁ − T₀) ln(1 + r/s)/ln(1 + r₁/s), continuous at r₁; T₀ = 265 K, s = 0.01; T₀ swept 250–292 K | **Assumption.** Concave like methane forcing; no published zero-methane temperature for these cases is in hand |
| T(r) above the last vertex | Plateau at the last vertex (274.0 K for B) | Arney's text says case B stabilises at 274 K as haze self-shields; the plateau shape is ours |
| Methane loss | First order, τ = 10 kyr | **Assumption.** Assigning Arney's aggregate onset-flux range to case B at r = 0.15 and assuming well-mixed methane gives 6–19 kyr; this is not a published case-specific lifetime |
| Abiotic methane | 6.8 × 10⁸ molecules cm⁻² s⁻¹ | Earth-mass serpentinization estimate quoted by Arney; gives r ≈ 0.00054 for case B under the assumed loss. The previous 1.3 × 10⁹ value applies to five Earth masses |
| Column and mixing | Well mixed; 2.19 × 10²⁵ molecules cm⁻² at 1 bar (mean molar mass 28 g mol⁻¹) | Assumption |
| Donor supply Φ | Generic electron donor: volcanic H₂ or photosynthetic organic matter, in CH₄ equivalents | Swept as the *potential ratio* τcΦ. This rescales the supply axis for a chosen τ; it does not remove lifetime dependence from donor competition or the abiotic equilibrium |
| Thermal performance ρ(T) | ρ_max (1 − ((T − T_opt)/w)²)₊ with ρ_max = 10, T_opt = 300 K, w = 20 K | **Placeholder**, with the same form as Daisyworld's β. Only the cold edge matters for the main result, and it is swept |
| Φ_K | 10¹⁰ molecules cm⁻² s⁻¹ | Placeholder. The positive-equilibrium derivation assumes finite positive donor removal and half-saturation; the zero-maintenance limit is singular |

The model leaves out:
- methane shielding once haze UV optical depth exceeds about 1; the available
  text does not determine the loss function's slope along increasing r;
- the luminosity dependence of the response;
- ice-albedo feedback;
- H₂'s own greenhouse effect;
- spatial refugia.

## Results

![Climate closure, equilibria under rising and falling supply, set point against thermal tolerance, and regimes](figures/budget_figures.png)

Data: [`budget_sweeps.csv`](figures/budget_sweeps.csv),
[`setpoint.csv`](figures/setpoint.csv), [`regimes.csv`](figures/regimes.csv).

**1. With ample supply, the assumed budget has a stable equilibrium near its
cold net-growth threshold (panels b and c).** The restricted reduced experiment
needs no low/high climate extrapolation. It still assumes the thermal response,
donor diversion, methane loss and atmospheric mixing. On the haze-cooling branch
the feedback runs as follows: more
methane cools the planet, which slows the methanogens, which in turn cut
methane production. The surplus supply goes to the alternative donor sink, and
η falls. In panel c's 78 invariant reduced cases, the equilibrium sits
0.015–0.037 K above the threshold where η becomes zero. These are numerical differences in
the toy model, not the accuracy of the extracted climate physics. The threshold
is a resource-dependent net-growth boundary, not a measured lethal temperature.

For the specified high-supply runs, the **reduced scalar flow** points into
Arney's extracted interval at both ends over these cold-edge ranges:

| Case | Cold edges giving an invariant domain |
|---|---|
| A | 264–282 K |
| B | 274–291 K |
| C | 263–281 K |
| D | 252–273 K |

Every reduced trajectory starting in such an interval stays there. This does
not establish the same property for arbitrary full-system donor/biomass states:
rare biomass at the lower endpoint can initially produce too little methane,
so the full state can leave the interval. Local full-system stability of the
positive equilibrium follows separately from its Jacobian on the cold-growth,
climate-cooling branch; see the review.

The original high-supply temperature-independent control uses the assumed
plateau outside the extracted domain. A separate source-contained comparison
at potential ratio 0.22 gives 281.36 K for thermal methanogens versus 273.44 K
for temperature-independent methanogens, both inside Arney B's interval.
Both reduced intervals are invariant; the 7.93-K contrast still depends on the
assumed biological and loss budget. Daisyworld holds the
temperature where growth balances death. Here the temperature is held at the
limit of the methanogens' tolerance, because capture becomes temperature
sensitive only near that limit.

**2. Away from the thermal edges, biology has almost no effect on the
equilibrium (panel b).** When ρ(T) ≫ 1 + Φ_K/Φ, the capture fraction η ≈ 1.
Methane then tracks the supply, and thermal and temperature-independent
methanogens give the same equilibria. Up to the haze peak, the methane
greenhouse is limited by supply. The methanogens' temperature response does not
matter there.

**3. If the zero-methane climate is colder than the cold edge, the lifeless
planet is a stable cold trap (panels b and d).** In that case methanogens need
warmth that only their own methane provides. This result depends on the bridge
assumption. With the defaults (T₀ = 265 K, edge 281 K):
- a sweep that raises supply from a lifeless start stays on the assumed cold bridge;
- a sweep that lowers supply from a high start keeps the biotic state until the
  potential ratio falls to about 0.045, then collapses to the lifeless state;
- between those, an unstable threshold near 281 K on the bridge separates the
  two basins.

Panel (d) places the boundary 1–2 K above the line T₀ = edge. The
lifeless-only band at the top of the panel holds edges above the warmest
temperature the case allows (297 K). The bistable corner at the lower right
comes from the warm edge, which is tied to the cold edge by the fixed width w.

The default T₀ = 265 K has no published anchor. Eager-Nash et al. (2023) give
a separate haze-free 3D zero-methane reference at the same epoch and similar
sunlight and background pressure. Our chosen log-CO₂ interpolation to case B's
CO₂ gives about 283 K; it is not a published case-B baseline. At that T₀ the trap
needs cold edges of 284 K or higher, so the default 281-K edge has none. The
comparison is across models, not a splice; see the
[evolution scope](evolution-scope.md).

## Limits and next steps

- **Low-methane branch.** The restricted reduced equilibria can avoid it;
  the cold-trap claim cannot. Published low-methane checkpoints are now
  [recovered from Eager-Nash](../haze_response/README.md), including zero methane.
  They remain a separate 3D scenario rather than a matched replacement for
  Arney's missing branch. Other candidate sources include:
  - Haqq-Misra et al. (2008), [doi:10.1089/ast.2007.0197](https://doi.org/10.1089/ast.2007.0197)
  - Byrne & Goldblatt (2015), [doi:10.5194/cp-11-559-2015](https://doi.org/10.5194/cp-11-559-2015)
  - Eager-Nash et al. (2023), [doi:10.1029/2022JD037544](https://doi.org/10.1029/2022JD037544)

  Differences in atmosphere, radiative transfer, clouds and ice must be resolved
  or retained as separate scenarios before these replace a bridge.
- **Loss law.** No matched per-ratio sustaining-flux curve was recovered.
  A shielding-induced reduction at fixed r does not establish a negative
  slope of total loss along increasing r. Recovering sustaining fluxes would
  constrain equilibrium balance; transients also require methane column
  storage N(r), since dr/dt = (source − required flux)/N′(r) in consistent time units. See the
  [source-recovery record](review/source-recovery.md).
- **Evolution.** A set point at a tolerance edge is exposed to the
  Robertson–Robinson critique. A
  [scratch adaptive-dynamics preview](evolution-scope.md) confirms the concern.
  Unconstrained selection on the thermal optimum moves the climate to the
  passive, supply-limited temperature: 273.4 K in case B at potential ratio
  0.22, with the whole path inside Arney's interval. A hotter-is-better
  trade-off stays near that control under linear loss, but this does not
  generalize to all increasing loss laws: an
  [independent audit](review/evolution-review-2026-11-09.md) finds a 4.61 K
  contrast under an illustrative logarithmic loss. The trade-off parameters
  are not calibrated to methanogens. The scope sets out the constraint,
  extinction and climate scenarios, with source packs for
  [thermal margins](evidence/thermal-margins.md) and
  [hydrogen competition](evidence/hydrogen-competition.md). This links the haze-world
  to the "evolving daisies" re-imagining in
  [`docs/vision.md`](../../docs/vision.md).
- **Luminosity.** All results are for one epoch. A solar sweep, the analogue
  of Daisyworld's L axis, needs climate responses at other S/S₀.

## Contributions

Claude (Opus 5.5, `claude-opus-5-5`) designed the model, derived the reduction,
wrote the code, tests and this page, and ran the experiments. The response
curves and bounded interface come from Codex's extraction of Arney et al.
(2016). Codex (GPT-6), with independent review and source-recovery subagents,
checked the equilibrium/dynamics distinction and source statements, repaired
rare-biomass integration, corrected the Earth-mass abiotic flux, regenerated
the experiments and recovered separate low-methane comparison checkpoints.
Codex and review subagents independently checked the evolution preview,
derived the singular-strategy and loss-shape checks, corrected the scope's
generalizations and compiled the thermal and hydrogen-competition evidence.
