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

## Variant: an evolving thermal optimum (stage 1)

**Code.** [`darwinian.py`](../../src/terra_prisca/haze_world/darwinian.py)
is a named variant; the budget above is unchanged. Tests are in
[`tests/test_darwinian.py`](../../tests/test_darwinian.py).
Scope and assumptions: [evolution-scope.md](evolution-scope.md).

**Independent review, 9 November 2026:** the 205 endpoint climates and full
local stability checks reproduce. The reported sensitivity ratios below use
finite ±0.5% supply changes rather than converged local derivatives, and panel
(d) labels a net cold edge as a bridge-temperature threshold. Their numerical
thresholds and associated prose need correction; see the
[review and analytical audit](review/darwinian-review-2026-11-09.md).
The production variant and its original figure are retained pending that repair.

```bash
uv run python -m terra_prisca.haze_world.darwinian
```

**Method.** The methanogens' thermal optimum θ evolves by monomorphic adaptive
dynamics. A rare mutant invades a resident at its equilibrium when it grows
faster at the resident's temperature T\*. The selection gradient is
E/(kθ²) − 2x/(w² − x²), with x = θ − T\*. It depends on the resident only
through T\*, so each evolved endpoint solves a single methane balance. Three
constraint scenarios are compared:

- **U**, unconstrained: peak growth fixed at 10;
- **F**, a hard floor on θ, swept from 274 to 300 K;
- **H**, hotter-is-better: peak growth 10·exp[(E/k)(1/300 K − 1/θ)], with E
  swept from 0 to 0.65 eV. These values of E are sensitivities, not measured
  for methanogens.

Five loss shapes are compared: power laws with elasticity d ln L/d ln r of 0.2,
0.5, 1 and 2, and Codex's logarithmic law. Each is anchored at the
temperature-independent ρ = 10 control, so every shape leaves the control
climate unchanged. All runs use case B at potential ratio 0.22.

**Measures.** Each endpoint is compared with two controls: the ρ = 10 control,
and a matched-peak temperature-independent strain with the same peak growth.

*Regulation* is the response of temperature to a change in supply,
dT/d ln Φ, divided by the same response of a temperature-independent strain
that has the same realized growth at the same equilibrium. Using the same
equilibrium matters: sensitivities taken at different equilibria are
dominated by the local slope of Arney's curve. A ratio of 1 means no
buffering. Below 1, the methanogens' temperature response opposes the
change.

*Persistence* is local stability of the full (D, B, M) Jacobian.
*Re-invasion* is whether the evolved strain can grow at the lifeless,
abiotic-only equilibrium. That depends on the bridge, and is reported for
T₀ = 265 K and 283 K.

![Evolving thermal optimum: trait paths, constraint sweeps, regulation and re-invasion](figures/darwinian_figures.png)

Data: [`darwinian_endpoints.csv`](figures/darwinian_endpoints.csv) and
[`darwinian_paths.csv`](figures/darwinian_paths.csv). All 205 endpoints
persist and lie inside Arney's extracted interval.

**4. Without a constraint, evolution erases every thermal signature (panels a
and b).** Under U, θ evolves to T\*. Growth is then at its peak, so its
temperature derivative is zero. Under every loss shape, the climate equals the
ρ = 10 control exactly and the regulation ratio is 1. This null result holds
for any loss law at a feasible interior singularity. The original cold-edge
equilibrium does not survive selection.

**5. With hotter-is-better, any surviving signal depends on how steeply methane
loss rises with abundance (panels b and e).**
- **Elasticity 1 or 2:** the evolved climate stays within 0.33 K of the
  control and the regulation ratio stays at 0.92 or above.
- **Elasticity 0.5 or less, or the log law, with E ≥ 0.3–0.4 eV:** the offset
  reaches 4.3–4.6 K and the ratio falls to 0.3.

Most of that offset is the thermal response itself, not the changed peak
growth: the matched-peak control accounts for at most 0.35 K. Low elasticity
amplifies the effect because a shallow loss curve converts a small change in
methane capture into a large change in methane.

So the empirical quantity that matters is how steeply photochemical loss
rises with methane. Arney's statement about self-shielding points toward
lower elasticity, but no curve has yet been recovered. The steps in panel (e)
occur where the equilibrium crosses a vertex of the piecewise-linear
extracted curve. Their levels reflect the curve's slope; their sharpness is
an artefact of interpolation.

**6. A floor restores regulation only when the floor is the set point (panels c
and f).** Floors below about 287 K change the climate by less than 0.1 K.
Between 290 and 293 K, depending on loss shape, the evolved cold edge
approaches the control climate. Temperature then follows the edge, 0.14–2.8 K
above it, and the regulation ratio falls to 0.01–0.3. The lower elasticities
reach the threshold first but buffer less. This is Lenton & Lovelock's point:
regulation returns, but its set point is the constraint.

For comparison, the evidence pack reports optima of 288–297 K for modern
cold-adapted isolates ([thermal margins](evidence/thermal-margins.md)). That
range spans the threshold. This is a consistency check, not a calibration:
w = 20 K and the mapping from habitat to global mean are placeholders.

**7. A regulated biosphere persists but may not return (panel d).** When the
climate is held near the cold edge, T\* is close to the edge. A rare strain
can then re-invade the lifeless state only if the methane-free planet is
warmer than that edge. In practice that means warmer than the regulated
climate, which is possible only because haze cools the planet below its
methane-free temperature.
- **With the 265-K bridge:** strains under H at E ≥ 0.4–0.45 eV, or under
  floors of 284–285 K or above, persist but cannot re-establish after a loss.
  The exception is elasticity 2: its higher abiotic methane warms the bridge,
  and the floor threshold rises to 293 K.
- **With the 283-K reference:** every evolved strain re-invades.

Constraints that restore regulation therefore also open a cold trap, unless
the methane-free climate is warm. Because the loss law is anchored at the
control, the abiotic methane level also varies with loss shape.

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
  A [new source review](evidence/loss-elasticity.md) recovers published
  haze-free finite-secant elasticities around 0.29–0.34 and separate Arney
  2018 haze-threshold anchors. Neither identifies the local loss slope near
  r = 0.2 for this climate case.
  A shielding-induced reduction at fixed r does not establish a negative
  slope of total loss along increasing r. Recovering sustaining fluxes would
  constrain equilibrium balance; transients also require methane column
  storage N(r), since dr/dt = (source − required flux)/N′(r) in consistent time units. See the
  [source-recovery record](review/source-recovery.md).
- **Evolution.** Stage 1 (results 4–7) is monomorphic and deterministic.
  Stage 2 adds strain-resolved mutation and an explicit demographic floor
  B_min, to test evolutionary rescue under declining supply and escape from
  the cold trap. Stage 3, hydrogen competition with homoacetogens, waits on
  the [strain-resolved benchmark](evidence/hydrogen-competition.md). The
  decisive empirical input for H is the elasticity of photochemical methane
  loss with abundance. See the [scope](evolution-scope.md) and
  [thermal evidence](evidence/thermal-margins.md). This links the haze-world to
  the "evolving daisies" re-imagining in [`docs/vision.md`](../../docs/vision.md).
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
Claude designed and wrote the evolving-optimum variant (`darwinian.py`), its
loss family, matched controls, regulation and re-invasion measures, tests and
the variant section above, building on Codex's loss-shape counterexample.
