# Issue 1 review: habitat spread and the real-planet interpretation

Codex (GPT-6), 14 November 2026. Reviews `af6eb3d` and pressure-test thread
165, post 3377. Three independent bounded checks covered the geometry,
predictor and primary sources. No manuscript, figure, model or original
probe output was changed, and no experimental stage was added.

**Verdict: accept the concern and the narrow numerical findings; dispute the
claimed real-planet placements and the proposed universal replacement
message.** The 0.07–0.32 K price is a local result on four selected branches,
not an estimate of a planet's expected sensitivity. Habitat structure can
make the residual response much larger. The new evidence does not establish
that real surface communities have little regulation, or that deep-water
communities occupy the reported durable regime.

## (a) Geometry, exactness and gain

The mechanism is useful. In an ideal sharp-switch, weak-mixing community,
the methanogen share is `phi = 1 - F_delta(T_star - T)`. Its temperature
derivative is the offset density at the switch. If emissions are
proportional to `P*g(phi)`, removal is linear in methane, and other source
terms are neglected, then on the cooling branch

`1/|S| = 1/k + rho(T_star - T)*Delta`,

where `k = |dT_clim/d ln r|` and `Delta = d ln g/d phi`. This gives the
stated general-density relation. For the uniform reduced closure, its
geometric term contains an additional `r/r_star` factor:

`|S_geo| = 2*sigma*(r/r_star)*(P_lo/P)*Q/(Q-1)`.

Setting that factor to one and holding k at its reference value are
approximations. Moreover, the production model has a hydrogen outlet,
assimilation and temperature-dependent catabolised fractions throughout
the distribution. At the reference crossing 7.4954% of supplied hydrogen
leaves through the outlet. The raw yield ratio
`eta_M/(0.5*eta_A) = 2.10382` therefore differs from the nominal-input
endpoint ratio `Q = 1.99551`. Substituting endpoint Q into a proportional-
supply closure does not make the production model exact.

Independent source-table recount confirms the practical fit: computed over
predicted sensitivity is 0.9444–1.0398 across the 20 weak-mixing states. At
d=0.01/year it is 0.9248–1.0432; at d=0.1 it is 0.7051–1.0698. The worst
case is 29.49% below the prediction, or a 41.82% overprediction relative to
the computed value. Thus call this a **reduced-model identity and useful
weak-mixing approximation**, not an exact production-model law.

At stronger mixing, sharp exclusion no longer describes the profile: at
sigma=1 K, f=0.5 and reference supply, the mixed zone occupies 1.51 of the
2 K support at d=0.01, and all 2 K at d=0.1. Precision is not bounded by
spread independently of connectivity, chemistry and habitat weighting.

The extrapolated surface values, |S|=34.63 and 44.14 at sigma=15 and 21 K,
are correctly obtained from the approximation. Their attenuation factors
of 4.06 and 3.19 compare against **bare haze**, not the paper's frozen-mix
counterfactual. The distinction matters: at sigma=3, d=0.0001 and P=0.30,
the actual `S=-8.30391`, `S0=-88.38329`, `G_loc=0.0939534`; `|S|/k=0.0590`
is a different ratio. No corresponding surface S0 was computed. The large
spreads also leave the full model's support, so these are extrapolations,
not numerical real-planet predictions. A three- to fourfold attenuation
alone does not establish that the remaining regulation is negligible.

## (b) Predictor, acceptance and finite responses

The fresh mesh and `local_profile_correction` are seeds, not substitutes
for equilibrium. Full positive balances, actual per-capita residuals,
whole-support physiology, logit resolution, mesh-doubling agreement in T,
S and S0, and the frozen finite-difference check follow. Three points were
reconstructed from saved methane ratio/mean biomasses on fresh uniform
meshes and requalified: sigma=1/P=0.30, sigma=3/P=0.473984375, and
sigma=8/P=0.31078125. Temperatures agree within 1e-8 K and slopes within
2e-6 K per e-fold; scaled RHS and per-capita residuals satisfy 1e-8.
No invalid qualified root was found. Lag margins have their additional
doubling check; this review did not rerun a lag sweep.
For sigma=3 they were evaluated at four supply values, so those samples
do not establish stability at every point of the finite-response curve.

There is a small, concrete reporting defect in `branch_job`: after a
recursive step fails, `branch_ends` reports the older whole-step state,
although accepted bisection steps remain in `rows`. For sigma=8 upward it
says P=0.31, while accepted rows reach 0.31078125. Return the last accepted
recursive state, or derive stop metadata from the accepted rows. The
original artifact remains unchanged pending reconciliation.

All eight stopping reasons are numerical unresolved statuses. They do not
locate extinction, a pure-guild endpoint, or an exact domain boundary.
The accepted sigma=1 and 3 extrema do approach T_star +/- sigma within
0.01 K, but over the **fixed homogeneous interval** P=0.229178–0.457327
the spans are 1.91115 and 5.40874 K. Those interval definitions should not
be interchanged. Sigma=6 and 8 cover only part of that interval; the
reduced-model comparisons concern sampled admissible portions, not complete
12- or 16-K continuum sweeps.

## (c) Source numbers versus habitat and climate mappings

The quotations mostly check; their pairing into physical archetypes does not.

- [Eager-Nash et al. (2023)](https://doi.org/10.1029/2022JD037544),
  [primary manuscript](https://arxiv.org/abs/2302.12518), figure 7, p.16:
  equatorial–polar contrasts of 27.9–32.8 K, with methane adding up to
  about 8.2 K. These are regional means in a 50-m slab aquaplanet without
  horizontal ocean heat transport (p.6), not a uniform biological habitat
  distribution. The contrast also changes with methane; fixed translated
  offsets are a further model assumption.
- [Mak et al. (2023)](https://doi.org/10.1029/2023JD039343),
  [primary manuscript](https://arxiv.org/abs/2310.06818), figure 5, p.10:
  approximately 289 to 247 K at r=0.125 is a fair surface-temperature
  reading. Much of that contrast is frozen surface (p.9). Its full range
  does not identify equally supplied methane-producing habitats.
- [Sweetman et al. (2017)](https://doi.org/10.1525/elementa.203),
  [primary PDF](https://nora.nerc.ac.uk/id/eprint/526869/1/203-2504-2-PB.pdf),
  table 1, p.4: the cited extrema give half-range 2.72 K. They describe
  modern annual-climatological abyssal **seafloor** temperatures, not
  deep-water-volume or sediment-habitat weights. The text also notes warm
  Mediterranean abyssal exceptions. This is an illustrative modern range,
  not an Archean distribution or its mean temperature.
- [Geoffroy et al. (2013)](https://doi.org/10.1175/JCLI-D-12-00195.1),
  [author-hosted PDF](https://www.umr-cnrm.fr/old/IMG/pdf/2box_i.pdf), table 4,
  p.1847: 4.1 and 249 years, and intermodel ranges 1.6–5.5 and 126–698,
  are correctly quoted. They are two modes of the same modern two-layer
  climate system, **not separately measured surface- and deep-habitat
  lags**. Both modes enter both temperature responses (equations 1–2 and
  11–12, pp.1842–1844). The slow mode is not an overturning transit time
  that can simply replace this model's one global-temperature tau.

Consequently, the computed sigma=3 margins of roughly 3.5–4.8 kyr support
a mathematical example, not a sourced placement of Archean deep habitats
at tau=250 yr. A habitat that follows surface climate through an additional
thermal filter has a different feedback system. A fixed mean offset also
moves the required surface set point; a spread alone does not specify it.
[Horne & Goldblatt (2024)](https://doi.org/10.1029/2023GC011252), end of
section 2.8, **assume** deep-ocean and sediment offsets of -15 and -17 C;
those choices do not calibrate either a spread or a lag here.

## (d) Methanogens alone and the haze floor

The overlay is a **homogeneous methanogen-only baseline**, whereas the new
two-guild curves have spread habitats. `homogeneous_curves` does not keep
sigma and habitat physiology matched. It therefore cannot isolate the
effect of removing acetogens from each spread community. The existing
frozen-mix S0 remains the defined local regulation comparator; a different
climate baseline needs its own clearly stated purpose and support.

The closure warning should be precise. At P=0.30, the homogeneous M-only
state is 273.5167 K at r=0.216150, **inside** the extracted Arney curve;
the existing C06 reference contrast is not invalidated. But 28 of 46 stored
M-only samples in the homogeneous coexistence interval are beyond the last
extracted ratio, 0.2333365, and use the assumed 274.002-K plateau. They
begin at sampled P=0.32. Shade or label that part, and do not treat its
zero supply sensitivity as an empirical unregulated reference.

## (e) Disposition of the proposed changes

| Proposal | Review disposition |
|---|---|
| Add geometry and finite responses | Agree in principle after narrowing exactness, interval coverage and endpoint language; repair stop metadata |
| Put surface/deep archetypes on Figure 3 | Hold: the source contrasts do not supply biological weights or paired habitat lags |
| Replace panel 3(b) | Decide after scientific reconciliation; a finite-response panel is useful, but its baseline and extrapolated regions must be explicit |
| Adopt the proposed main message | Dispute its universal habitat-uniformity condition; Barry's message decision remains open |
| Add claims | Add qualified candidate claims only after reconciliation; do not turn the source analogies into calibrated planetary results |
| Extend inactive/winner-only tails | A new named sensitivity stage requiring the agreed approval; neither extension is established by assay coverage |

In particular, 273 K is this model's support floor, not proof that water or
microbes disappear below it: the cited modern abyssal range itself includes
liquid water below 0 C. Likewise, the absence of transferred kinetics above
303.15 K does not establish biological inactivity. Production methane flux
depends on uptake, outlet and assimilation across all active habitats, not
only the density at the switch. Truncating tails changes that budget and
cannot be assumed innocuous.

The paper can retain the conditional finding that a small loss of precision
buys large lag margins on the tested branches. It should not call that price
typical of a planet. The proposed replacement also overreaches: precision
depends on supply-weighted habitat structure, connectivity and chemistry,
not habitat uniformity alone. We have an explanatory mechanism and useful
finite examples, but no calibrated location of Earth on Figure 3.

Reproduction: `uv run python docs/audits/probe-issue1-codex-check-2026-11-14.py
--predictor-checks --output /tmp/terra-issue1-check.json` (one line). The
committed JSON records the recount, three fresh-mesh checks and input hashes.
No full sweep or general test suite was rerun for this read-only review.
