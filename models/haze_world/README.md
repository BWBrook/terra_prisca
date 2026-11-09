# Haze-world

**Status: first draft (Claude, 9 November 2026), awaiting review.** This is a new
model, not a reconstruction. It couples methanogens and a finite methane budget
to the [Arney et al. (2016) climate responses](../haze_response/README.md).
Every quantity those curves do not supply is a named assumption with a default
and a sweep.

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
methane M. Each is a CH₄-equivalent column divided by the CO₂ column, so M is
the surface CH₄/CO₂ ratio r on Arney's axis.

| Equation | Meaning |
|---|---|
| dD/dt = φ − k_D D − U | donor supply, an alternative sink and methanogen uptake |
| U = μ(T) B D/(K + D) | Monod uptake with thermal performance μ(T) |
| dB/dt = Y U − δ B | methanogen growth and loss |
| dM/dt = U + φ_abiotic − M/τ | methane production, abiotic source and first-order loss |
| T = T(M) | climate closure (below) |

Biology relaxes in years and methane in about 10⁴ years. On methane time scales
the biology is therefore quasi-steady, and the system reduces exactly to one
equation:

  dr/dt = c [η(T(r)) Φ + Φ_abiotic] − r/τ,  η = max(0, 1 − Φ_K / (Φ (ρ(T) − 1)))

Here:
- Φ is the donor supply as a CH₄-equivalent flux;
- ρ = Yμ/δ is the methanogens' maximum growth over loss;
- Φ_K = K k_D is the supply at which the abiotic donor level equals K;
- c converts molecules cm⁻² s⁻¹ to ratio units per year.

η is the fraction of the supply that methanogens capture. It is positive exactly
when they can invade, so the invasion check that the Daisyworld repair needed
is built in. A test integrates the unreduced three-variable system and recovers
the reduced equilibrium to 10⁻⁴.

Equilibria are the roots of dr/dt, found on a fine grid and refined. In one
dimension a root is stable when the flow crosses it from + to −; a test confirms
each label by perturbation. Sweeps step the supply and move from the previous
equilibrium to the next root in the direction of flow, which is exact for a 1D
flow.

## What comes from the source and what is assumed

| Quantity | Treatment | Basis |
|---|---|---|
| T(r) within the extracted domain | Arney Fig. 4, case B by default (all four cases are used in panel c) | Extracted; S/S₀ = 0.81, 2.7 Ga, fixed CO₂ and pressure |
| T(r) below the first vertex (**low-methane bridge**) | T₀ + (T₁ − T₀) ln(1 + r/s)/ln(1 + r₁/s), continuous at r₁; T₀ = 265 K, s = 0.01; T₀ swept 250–292 K | **Assumption.** Concave like methane forcing; no published zero-methane temperature for these cases is in hand |
| T(r) above the last vertex | Plateau at the last vertex (274.0 K for B) | Arney's text says case B stabilises at 274 K as haze self-shields; the plateau shape is ours |
| Methane loss | First order, τ = 10 kyr | **Assumption.** Arney's haze-onset flux of 1–3 × 10¹¹ molecules cm⁻² s⁻¹ implies τ = 6–19 kyr for case B at r = 0.15 |
| Abiotic methane | 1.3 × 10⁹ molecules cm⁻² s⁻¹ | Upper abiotic estimate quoted by Arney (from Guzmán-Marmolejo et al. 2013); gives r = 0.001 for case B |
| Column and mixing | Well mixed; 2.19 × 10²⁵ molecules cm⁻² at 1 bar (mean molar mass 28 g mol⁻¹) | Assumption |
| Donor supply Φ | Generic electron donor: volcanic H₂ or photosynthetic organic matter, in CH₄ equivalents | Swept. Plotted as the *potential ratio* τcΦ, which absorbs the uncertainty in τ |
| Thermal performance ρ(T) | ρ_max (1 − ((T − T_opt)/w)²)₊ with ρ_max = 10, T_opt = 300 K, w = 20 K | **Placeholder**, with the same form as Daisyworld's β. Only the cold edge matters for the main result, and it is swept |
| Φ_K | 10¹⁰ molecules cm⁻² s⁻¹ | Placeholder. As Φ_K → 0, η becomes a step at ρ = 1 and the results below are unchanged |

The model leaves out:
- the decline in methane loss that Arney reports once haze UV optical depth
  exceeds about 1;
- the luminosity dependence of the response;
- ice-albedo feedback;
- H₂'s own greenhouse effect;
- spatial refugia.

## Results

![Climate closure, equilibria under rising and falling supply, set point against thermal tolerance, and regimes](figures/budget_figures.png)

Data: [`budget_sweeps.csv`](figures/budget_sweeps.csv),
[`setpoint.csv`](figures/setpoint.csv), [`regimes.csv`](figures/regimes.csv).

**1. With ample supply, haze and cold-limited methanogens hold the temperature
at the methanogens' cold edge (panels b and c).** This result needs no closure
assumption. On the haze-cooling branch the feedback runs as follows: more
methane cools the planet, which slows the methanogens, which in turn cut
methane production. The surplus supply goes to the alternative donor sink, and
η falls. At high supply the biotic equilibrium therefore sits 0.02–0.08 K above
the temperature at which η reaches zero, approaching it from above as supply
grows.

The flow points into Arney's extracted domain at both ends whenever the cold
edge lies on a case's cooling branch:

| Case | Cold edges giving an invariant domain |
|---|---|
| A | 264–282 K |
| B | 274–291 K |
| C | 263–281 K |
| D | 252–273 K |

Inside those ranges every trajectory that starts in the domain stays in it, so
neither the bridge nor the plateau is ever used. That is the restricted
experiment Codex asked for.

Temperature-independent methanogens with the same supply settle on the haze
plateau (274 K for B), 7 K colder at the default edge of 281 K. This is
Daisyworld's logic with a different set point. Daisyworld holds the
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
- a sweep that raises supply from a lifeless start stays lifeless at 266 K;
- a sweep that lowers supply from a high start keeps the biotic state until the
  potential ratio falls to about 0.045, then collapses to the lifeless state;
- between those, an unstable threshold near 281 K on the bridge separates the
  two basins.

Panel (d) places the boundary 1–2 K above the line T₀ = edge. The
lifeless-only band at the top of the panel holds edges above the warmest
temperature the case allows (297 K). The bistable corner at the lower right
comes from the warm edge, which is tied to the cold edge by the fixed width w.

## Limits and next steps

- **Low-methane branch.** Results 1 and 2 hold without it; result 3 depends on
  it entirely. Candidate sources are listed below; recovering one would replace
  T₀ and s.
  - Haqq-Misra et al. (2008), [doi:10.1089/ast.2007.0197](https://doi.org/10.1089/ast.2007.0197)
  - Byrne & Goldblatt (2015), [doi:10.5194/cp-11-559-2015](https://doi.org/10.5194/cp-11-559-2015)
  - Eager-Nash et al. (2023), [doi:10.1029/2022JD037544](https://doi.org/10.1029/2022JD037544)

  Each needs matching to Arney's atmospheres before it can be used.
- **Loss law.** Arney's photochemistry fixed surface CH₄ and computed the
  required flux. If those fluxes per case can be recovered, they give
  loss(r) directly and replace τ. Haze self-shielding would make loss fall
  on the haze branch, a positive feedback that could weaken result 1.
- **Evolution.** A set point at a tolerance edge is exposed to the
  Robertson–Robinson critique. Selection for cold tolerance would lower the
  edge and walk the set point down toward the haze plateau. This links the
  haze-world to the "evolving daisies" re-imagining in
  [`docs/vision.md`](../../docs/vision.md).
- **Luminosity.** All results are for one epoch. A solar sweep, the analogue
  of Daisyworld's L axis, needs climate responses at other S/S₀.

## Contributions

Claude (Opus 5.5, `claude-opus-5-5`) designed the model, derived the reduction,
wrote the code, tests and this page, and ran the experiments. The response
curves, their bounded interface and the source anchors used here (the haze-onset
flux, the abiotic flux and the self-shielding statement) come from Codex's
extraction of Arney et al. (2016). The Arney text was re-read to locate the flux
statements.
