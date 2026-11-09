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

**Review history.** Codex's
[independent review](review/darwinian-review-2026-11-09.md) reproduced the
205 endpoint climates and their full local stability, and found two errors in
the first version (`88fbad8`):
- **Supply response.** It used finite ±0.5% supply changes, which straddle
  vertices of the climate curve. The response is now the analytical local
  derivative.
- **Return threshold.** Panel (d) labelled the net-growth edge as a bridge
  threshold. It now shows the critical bridge T₀.

The corrected values reproduce the review's independent audit.

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

*Regulation* is the local response of temperature to a change in supply,
dT/d ln Φ, divided by the same response of a temperature-independent strain
that has the same realized growth at the same equilibrium. With S the methane
source, L the loss and subscripts for derivatives with respect to r:

R = L_r/(L_r − S_r), where S_r = cΦ_K ρ_T T_r/(ρ − 1)².

Using the same equilibrium matters: sensitivities taken at different
equilibria are dominated by the local slope of Arney's curve. A ratio of 1
means no buffering. Below 1, the methanogens' temperature response opposes
the change.

The optimum is singular or held at the floor, so re-evolving it adds nothing
at first order, and the ecological and evolutionary responses coincide. At a
vertex of the piecewise-linear climate curve, the two one-sided values are
both stored; no endpoint falls on a vertex.

*Persistence* is local stability of the full (D, B, M) Jacobian.
*Re-invasion* is whether the evolved strain can grow at the lifeless,
abiotic-only equilibrium r_a. That requires T(r_a) to lie between the strain's
resource-dependent cold and warm net-growth edges. On the bridge,
T(r_a) = (1 − z)T₀ + zT₁ with z = ln(1 + r_a/s)/ln(1 + r₁/s), so each edge
maps to a critical T₀. The critical values and the classifications at
T₀ = 265 K and 283 K are both reported.

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
loss rises with abundance (panels b and e).** The lowest regulation ratios
all occur at E = 0.65 eV.

| Loss | Lowest ratio | Largest offset from control (K) | First E with ratio < 0.5 (eV) |
|---|---:|---:|---:|
| Power, n = 0.2 | 0.296 | 4.32 | 0.45 |
| Power, n = 0.5 | 0.312 | 1.04 | 0.65 |
| Power, n = 1 | 0.917 | 0.32 | none |
| Power, n = 2 | 0.953 | 0.13 | none |
| Logarithmic | 0.295 | 4.61 | 0.40 |

Most of the offset is the thermal response itself, not the changed peak
growth: the matched-peak control accounts for at most 0.35 K. Low elasticity
amplifies the effect because a shallow loss curve converts a small change in
methane capture into a large change in methane.

The jumps in panel (e) occur where the equilibrium moves onto a steeper
segment of the extracted curve. Their size reflects the curve's local slope;
their sharpness reflects the piecewise-linear interpolation.

So the empirical quantity that matters is how steeply photochemical loss
rises with methane. Published haze-free photochemistry gives finite-range
elasticities of about 0.29–0.34 at r < 0.03
([loss evidence](evidence/loss-elasticity.md)). That supports exploring
shallow loss, but does not calibrate the hazy branch near r = 0.2.

**6. A floor restores regulation only when the floor is the set point (panels c
and f).** Floors below about 287 K change the climate by less than 0.1 K. The
ratio first falls below 0.3 at a floor of 291 K (n = 0.2 and log), 292 K
(n = 0.5) or 293 K (n = 1 and 2). Above that, temperature follows the cold
edge, 0.14–2.4 K above it, with a ratio of 0.01–0.16. The lower elasticities
reach the threshold first but buffer less. This is Lenton & Lovelock's point:
regulation returns, but its set point is the constraint. These thresholds
depend on the scenario grid; they are not organismal measurements.

For comparison, the evidence pack reports optima of 288–297 K for modern
cold-adapted isolates ([thermal margins](evidence/thermal-margins.md)). That
range spans the threshold. This is a consistency check, not a calibration:
w = 20 K and the mapping from habitat to global mean are placeholders.

**7. A regulated biosphere can return only if the methane-free climate is
nearly as warm as the regulated one (panel d).** Re-invasion needs the abiotic
climate above the strain's net-growth cold edge, and that edge lies below the
living temperature. The lifeless planet may therefore be somewhat cooler than
the living one; the earlier statement that it must be warmer was wrong.

In the regulated floor states the gap is narrow. The critical bridge T₀ lies
0.55–2.4 K below the living equilibrium for n ≤ 1, and 5.0–8.2 K below it for
n = 2, whose anchoring gives more abiotic methane. For example, at a 300-K
floor with linear loss, the living climate is 281.36 K and the critical T₀ is
280.82 K.
- **With the 265-K bridge:** strains under H at E ≥ 0.4–0.45 eV, or under
  floors of 284–285 K or above, persist but cannot re-establish after a loss.
  With n = 2 the floor threshold rises to 293 K.
- **With the 283-K reference:** every evolved strain re-invades.

Strong buffering and failed return coexist under the cold bridge. This is a
conditional result, controlled by the assumed low-methane climate, not a
general equivalence.

## Variant: strains, mutation and extinction (stage 2)

**Code.** [`strains.py`](../../src/terra_prisca/haze_world/strains.py), with
tests in [`tests/test_strains.py`](../../tests/test_strains.py).

```bash
uv run python -m terra_prisca.haze_world.strains
```

**Model.** The methanogens occupy 131 bins of thermal optimum, from 245 to
310 K at 0.5-K spacing. Each bin follows the stage-1 physiology, and all
bins share the donor pool and the climate. Linear loss is used throughout,
with τ = 10 kyr.

Mutation sends a fraction m of each bin's births to each neighbouring bin.
Methane comes from uptake, so mutation leaves methane production unchanged.
Two consequences follow:
- **A strain that cannot divide produces no mutants.**
- **Extinction is explicit.** Every 10 years (the census interval), any bin
  below B_min is set to zero. Mutation from a living neighbour can repopulate
  an emptied bin, but extinction of every bin is permanent. The effective
  establishment condition is therefore mutant inflow per census, about
  m·U·Δt, compared with B_min.

The mutation fraction m, the threshold B_min (relative to the initial
biomass B\*) and the census interval are uncalibrated, so they are swept or
stated. Time is in years under the stage-1 biology.

**Experiments.**
- **Rescue.** Start at the evolved state for potential ratio 0.22, then lower
  the supply linearly to 0.02 over 100, 1,000 or 10,000 years and hold it
  for 60 kyr. Constraints U and H (E = 0.65 eV), with m = 10⁻⁴, 10⁻⁶ and
  10⁻⁸, B_min = 10⁻⁹ and 10⁻⁶ B\*, and bridge T₀ = 265 and 283 K.
- **Seed escape.** On the lifeless planet with T₀ = 265 K (265.6 K at the
  abiotic methane level) and constant supply, seed one strain at 10⁻³ B\*.

![Strain-resolved rescue under declining supply, and seed escape from the cold trap](figures/strains_figures.png)

Data: [`strains_rescue.csv`](figures/strains_rescue.csv),
[`strains_seed.csv`](figures/strains_seed.csv) and the example
[`strains_series.csv`](figures/strains_series.csv).

**8. Losing the supply means losing the haze, and the danger is heat (panel
a).** At potential ratio 0.22 the climate sits at the haze minimum near
273 K. As supply falls, methane decays over about 10⁴ years. The planet passes
back through Arney's warm peak (297 K) before cooling onto the low-methane
bridge. Methanogens adapted to the hazy minimum must first survive that
warming.
- **Under U with too little mutation**, they die in the warm phase,
  2.5–7.3 kyr after the decline begins, at either T₀. Too little means
  m = 10⁻⁸ with B_min = 10⁻⁶ B\*, where mutants cannot reach B_min within one
  census. Methane then collapses to the abiotic level and the climate settles
  at the lifeless 266 K or 283 K.
- **Every other U run survives.** The largest lag behind the singular optimum
  is 5–17 K, inside the 19-K thermal window (panel c).
- **The duration of the decline matters little.** Methane relaxation, not the
  supply schedule, sets the pace.

**9. Evolution can strand a population (panel b).** Under H at E = 0.65 eV,
T₀ = 265 K and B_min = 10⁻⁶ B\*:
- with m = 10⁻⁶, the population went extinct 34–39 kyr after the decline
  began, and the planet fell to 267 K;
- with m = 10⁻⁸, it survived.

The mechanism is mutation supply, which scales with population size. While
supply and biomass were still high, the m = 10⁻⁶ population tracked the
warming to an optimum near 299 K. After the supply fell, biomass dropped about
14-fold. Mutant inflow per census fell below B_min, the population was left
with one or two bins, and it could not follow the climate back down. The
nearly non-mutating population kept its 285.5-K optimum. Hotter-is-better
gives that optimum a thermal window wide enough for both the warm peak and
the cooled endpoint.

Adapting to a transient is costly when evolvability then collapses. This is
conditional on the census threshold, which is the least constrained
assumption here. With T₀ = 283 K every H run survives.

**10. Mutation cannot carry a lifeless planet out of the cold trap (panel
d).** A seed strain establishes only if its optimum is within about 1 K of
the viable range: optimum ≤ 285–285.5 K, against viability below 284.5 K.
Beyond about 285.6 K it cannot divide at 265.6 K, so it makes no mutants and
dies within 7–16 years at any m. Escape by mutation would need standing
variation that already reaches the viable range, which is immigration under
another name. The cold trap is evolutionarily absorbing, so whether a lifeless
haze-world can be colonised depends on its methane-free climate, which is
still the bridge assumption.

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
- **Evolution.** Stages 1 and 2 (results 4–10) use one deterministic
  physiology with uncalibrated mutation, census and extinction settings, and
  a single forcing (declining supply) in case B. Stage 3, hydrogen
  competition with homoacetogens, waits on the
  [strain-resolved benchmark](evidence/hydrogen-competition.md). The decisive
  empirical inputs are:
  - the elasticity of photochemical methane loss near r ≈ 0.2
    ([evidence](evidence/loss-elasticity.md));
  - the methane-free climate of a matched atmosphere;
  - the scale of mutation supply relative to demographic extinction.

  See the [scope](evolution-scope.md) and
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
Claude also built the strain-resolved stage-2 variant (`strains.py`), its
rescue and seed-escape experiments, tests and the stage-2 section.
