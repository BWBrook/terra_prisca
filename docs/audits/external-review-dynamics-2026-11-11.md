# Independent dynamic checks of the external-review triage

Codex, 11 November 2026. These checks address X1, X2, X3 and X10 in the
[combined triage](haze-world-external-review-triage-2026-11-11.md), with small
controls relevant to X6. They do not constitute Stage B.

Reproduce from the repository root:

```sh
uv run python docs/audits/external-review-dynamics-2026-11-11.py
```

The [script](external-review-dynamics-2026-11-11.py) writes its own
[receipt](external-review-dynamics-2026-11-11.json). It neither imports the
reviewer implementations nor overwrites their receipts. Source hashes are
recorded in the receipt. All reported stability classifications concern the
stated model, not a calibrated ocean thermal response.

## X1: finite thermal response destabilises the reference mixture

**Confirmed.** I assembled the five physical stock flows directly from guild
uptake, yield, assimilation, gas exchange and methane loss. State derivatives
are analytic on the positive-uptake segment. Only temperature derivatives use
a numerical stencil, at three step sizes. A sixth state obeys
`dT/dt = [T_climate(r) − T]/tau_T`; it leaves the equilibrium unchanged.

The critical thermal relaxation times are **0.149214 yr** at `f = 0` and
**1.102760 yr** at `f = 0.5`. Results agree across the three temperature
derivative steps. The leading-mode reduction gives 0.149221 and 1.106480 yr,
respectively. Thus the simple formula is an approximation, particularly for
the second setting, rather than an exact reduction of the full matrix.

An independently assembled nonlinear six-state integration at `f = 0`,
`tau_T = 3 yr`, starting with a `0.001` increase in log acetogen biomass,
has a sampled minimum of **10^-26.24 acetogen cells worldwide** within
12,000 yr. The 1-yr output grid gives a diagnostic minimum; it is not a
certified dense extremum. Global temperature spans 280.489–282.613 K.
This continuous run retains arbitrarily small biomass. It diagnoses finite
population failure but does not simulate removal or demographic events.

## X2: product feedback supplies a stable, partially buffering example

**Confirmed over the checked settings.** Both `f = 0` and `f = 0.5`
product-feedback mixtures have negative leading eigenvalues at all 16
logarithmically spaced lags from 10^-5 to 10^4 yr, under all three temperature
derivative stencils. This is a finite grid at the reference supply and
turnover, not proof of universal stability.

For `f = 0.5`, I computed the supply derivative by implicit differentiation
of the equilibrium equations, rather than perturbing the supply and finding
new roots. The community has `dT/d ln(supply) = −1.877567 K`, compared with
`−13.263667 K` for the corresponding methanogen-only control. The signed gain
is **0.141557**, or **85.844% attenuation**. This confirms strong partial
buffering and the loss of exact pinning.

## X3: habitat spread helps, but the broad stability/rescue claim fails

**Qualified and partly contested.** I independently assembled a nine-box
model with equal habitat weights, shared methane, local hydrogen and acetate,
and conservative cell exchange of `0.001 yr^-1`. Positive equilibrium stocks
were followed by root continuation from the homogeneous mixture. Temperatures
were never clipped. At `f = 0`, the resulting equilibria are:

| Habitat offsets | Global temperature | Local temperature range |
|---|---:|---:|
| ±3 K | 283.033854 K | 280.034–286.034 K |
| ±6 K | 284.533459 K | 278.533–290.533 K |

Both remain inside the measured physiology interval. The leading eigenvalues
of the explicit lagged system are:

| Spread | 3-yr thermal lag | 30-yr thermal lag | 300-yr thermal lag |
|---|---:|---:|---:|
| ±3 K | −0.00008247 | +0.00270470 | +0.00359278 |
| ±6 K | −0.00015815 | +0.00255772 | +0.00348268 |

Units are inverse years. Two Jacobian step sizes agree. The narrow spreads
stabilise the **3-yr example**, but they do not stabilise the equilibrium for
the longer lags tested here. Fable's ±6 K, 300-yr finite record is bounded
and oscillatory; its boundedness does not establish a stable fixed point.
These calculations do not identify an attracting cycle either.

The triage also merges two different reviewer experiments. In the reviewer's
own invasion records, ±6 K gives minima below one global cell, approximately
10^-573 cells for one direction and 10^-16541 for the other. Protection of
both invasion directions appears only at much wider offsets: ±10 K in one
direction, and ±18 K in the other. The reviewer clips local temperatures to
273–303.15 K, which matters for those wider settings. Therefore **±3–6 K
does not remove the invasion bottleneck in the supplied evidence**. Stage B
must separate fixed-point stability, bounded oscillations and finite
attainability, and must explicitly qualify the temperature-domain treatment.

No independent nonlinear heterogeneous invasion rerun or continuous-spread
qualification was performed in this audit.

## X10: unequal evolutionary constraints can reverse the feedback

**Confirmed.** I called the best-response calculation separately for each
guild, with `E_A = 0.65 eV` and `E_M = 0.10 eV`. At the resulting traits,
I assembled the physical ecological equations and their state derivatives
independently. The cooling-branch communities are feasible but unstable.

| Interpolation | Crossing | d(R*_A − R*_M)/dT | Leading eigenvalue at f = 0 / 0.5 |
|---|---:|---:|---:|
| Linear | 284.715277 K | −0.581583 Pa/K | +0.034225 / +0.025230 yr^-1 |
| Smooth | 285.387460 K | −0.500487 Pa/K | +0.033050 / +0.024038 yr^-1 |

All four equilibria have positive stocks and lie on the extracted cooling
branch. The common-E constraint is consequential; the common-E results
cannot support an unrestricted claim that evolution preserves feedback sign.

## X6: cheap controls with other climates and MSP

For Arney cases A, B and C I fixed the same physiology and selected supply
inside each case's feasible coexistence band, dividing hydrogen uptake
equally between guilds. The common temperature is **281.534823 K** in all
three cases, while the corresponding methane ratios and stability spectra
differ. All three selected instantaneous-climate mixtures are locally stable.
This does not claim they coexist at the same external supply.

The MSP control in case B has a locally stable instantaneous-climate mixture
at **290.285486 K**, with leading eigenvalue `−0.00115117 yr^-1`.

The digits above allow numerical cross-checking. They are not observational
precision or uncertainty estimates for Archean temperature or microbial
physiology.
