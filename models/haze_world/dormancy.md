# Dormancy in haze-world

**Status: methods and assessment code are built; the full T3 experiment has
not yet been assessed.** The assessment refuses to interpret T3 until the
independent turnover basin gate has closed. The original
[specification](turnover-dormancy-spec.md) records KD1–KD5 before the runs;
the [method notes](turnover-dormancy-method-notes.md) record qualifications
made before full-grid scoring.

That gate is scoped to the checked starts and reconciled local stability,
not a proof that equilibrium roots exhaust every global attractor. T3 uses
only `f=0` and `0.5`. The assessment retains the gate's qualifications
alongside its hash.

This variant asks whether a dormant seed bank can retain the microbial group
that temporarily loses the competition for hydrogen. The atmosphere adjusts
over millennia while active populations can decline within years. Dormancy
can bridge that interval without a spatial refuge, but its success depends
on the duration and shape of the climate excursion, not just the final
environment. The dormant loss rates and switching law are hypotheses for
this model, not measurements of an Archean biosphere.

## Model and units

Each habitat has hydrogen, active acetogens `X_A`, active methanogens `X_M`,
acetate, dormant acetogens `Z_A` and dormant methanogens `Z_M`. Habitats share
atmospheric methane and the existing case-B climate response. Biomass is in
g dry weight/L, and the integration time is years. The reference hourly
growth, loss and switching rates are converted to years consistently.

For each guild, with synthesis `g = Y(q − m)` and active loss `L`,

    dX/dt = (g − L)X − σX + ρZ + cell exchange
    dZ/dt = σX − ρZ − εLZ + cell exchange

    σ = kL c((L − g)/L)
    ρ = kL c((g − L)/L)

T3 uses the documented cubic ramp `c(x)=x²(3−2x)` between zero and one,
clipped to those values outside that interval. Thus entry occurs only under
negative active growth, and waking only under positive active growth. The
main switching factor is `k=10`, with `k=1` as the slow control. The permitted
linear ramp remains a separate named control. A short matched linear/cubic
comparison does not establish equal long-term outcomes; T3 conclusions are
conditional on the cubic law.

Dormant cells neither consume hydrogen nor incur maintenance or generate
products. They retain their biomass, die at `εL`, and disperse at the same
per-cell rate as active cells. Conversion preserves biomass; dormant death
enters the same turnover accounting as active death. The census counts
`X+Z` in each habitat and removes a guild there below one cell. No group can
regrow after global removal without a surviving population elsewhere.

The implementation is
[`dormancy.py`](../../src/terra_prisca/haze_world/dormancy.py), with the
positive-coordinate integration in
[`dormancy_integration.py`](../../src/terra_prisca/haze_world/dormancy_integration.py).
The qualified production numerical variant is
[`dormancy_jacobian_integration.py`](../../src/terra_prisca/haze_world/dormancy_jacobian_integration.py).
It retains the physical equations and accepted-flow rules while correcting
the Newton matrix and coordinating chemical charts. The active model and
its frozen earlier outputs are unchanged.

## Stationary locations and resident preparation

The specification's KD1 statement requires a distinction. In one well-mixed
habitat with `ε>0`, a stationary living resident has `g=L`, no switching and
`Z=0`. Its stationary location is therefore the reference location. For the
cubic ramp the switching derivative also vanishes at break-even growth;
this supports the local resident stability comparison stated in the
[independent design review](review/turnover-dormancy-design-review.md).
It does not establish unchanged finite-dose basins.

Spatial source–sink residents differ. Dispersal balances unequal local
growth, so `g−L` need not vanish in every habitat. A habitat can maintain a
dormant bank even at a stationary global state. Thus the claim that *every*
spatial equilibrium remains unchanged is false. Each spatial resident is
prepared at its own stationary bank, solving

    [diag(ρ + εL + d) − d 1 wᵀ] Z = σX

and refining its hydrogen, active biomass, acetate and atmospheric methane
together. A root qualifies only with supported physiology, a small residual
and agreeing conditional resident spectra at two step sizes on each climate
side. The bounded stencil refinement retains every coarse spectrum.

Each experiment uses the highest-methane qualifying resident, then adds
`10⁻¹² gDW/L` active invader in every positive-area habitat and zero dormant
invader. This is the earlier finite invasion dose. The root search and
selection do not prove global uniqueness or resistance to invasion by the
other guild.

## Experiments and endpoint comparisons

The 128 planned runs comprise:

- 112 main cases: acetate recycling `f=0` or `0.5`, seven `ε` values from
  `10⁻⁴` to `0.1`, both invasion directions, and no refuge, a 2% warm refuge
  at exchange `10⁻⁹` or `10⁻⁶/year`, or both 2% refuges at `10⁻⁶/year`;
- 12 slow-switching cases without refuges, at `ε=0.01`, `0.001` or `0.0001`;
- four no-refuge cases at active loss `0.002/hour`, testing the bistable
  reference regime at `f=0` and `ε=0.01` or `0.001`.

The initial horizon is 100,000 years with a ten-year census. Unsettled cases
require extensions. A stationary endpoint needs less than 0.1% change in
every stock, less than 0.01 K temperature change, small scaled derivatives
and no occupancy changes over its final 20,000 years. Opposite invasion
directions agree only when both endpoints qualify, every habitat has the
same guild occupancy, their temperatures differ by less than 0.01 K, and
every active, dormant, chemical and atmospheric stock agrees within 0.1%
using declared near-zero floors. Equal temperature alone is insufficient.

KD1's no-removal reference clause additionally compares matching frozen
buffered-refuge endpoints. It projects active plus dormant biomass into the
reference guild stocks and records dormant fractions separately. Selected
stationary horizons are explicit; an extended endpoint comparison is not
reported as a literal 100,000-year identity.

## First bottlenecks and KD1–KD5

The two-stage backward branching calculation treats active birth/death,
dormant death, stage conversion and habitat migration explicitly. With zero
switching and zero initial dormant cells, it reproduces the frozen active
probabilities bit for bit. Closed-form and independent forward controls,
including reopening pathways after severe underflow, are recorded in the
design review.

Each guild is assessed at its first resolved globally rare bottleneck. The
boundary is lowered only around that first minimum until local and global
hydrogen uptake shares are negligible. A later continuum recovery cannot
replace an earlier failed bottleneck. Terminal declines retain their finite
horizon. Their survival probability is an upper bound for survival through
any later horizon, so a terminal value below 0.5 supplies a one-sided loss
constraint without waiting for an implausible continuum recovery. A
terminal value above 0.5 needs a longer hold.

The probabilities assume the recorded environment and a Poisson population
at window entry. They concern survival somewhere across all habitats and
both stages. They do not certify local occupancy or a joint community
endpoint. Rows flag dependence on the other guild's improbable continued
survival. Demographic classes use the accepted thousandfold range in the
global cell-count scale.

The result assessment keeps the predictions separate:

| Prediction | Assessment rule |
|---|---|
| KD1: unchanged stationary states | Preserve the well-mixed theorem; test spatial endpoints and qualify its failed spatial premise. |
| KD2: warm-refuge acetogens never fall below `10¹³` cells | Use the global `X+Z` first minimum, plus the first-window persistence class; never substitute a patch minimum or a later ghost minimum. |
| KD3: a seed bank replaces refuges | Retain every measured `P=0.5` bracket. Compare it with the predicted 1–3× bands, without imposing monotonicity or a unique threshold. |
| KD4: switching speed changes the critical `ε` by less than threefold | Compare all fast/slow bracket ratios. A broad ratio interval requests refinements rather than a fabricated point estimate. |
| KD5: dormancy cannot alter the bistable outcome | Test the specified finite doses and both invasion directions. Preserving stationary locations is not a proof about these basins. |

The KD3 prediction bands are `0.006–0.018` and `0.0025–0.0075` for displaced
methanogens at `f=0` and `0.5`, and `0.00046–0.00138` and
`0.00082–0.00246` for displaced acetogens. The reference-duration argument
that produced them is a prediction, not a rigorous lower bound once
dormancy changes the climate path. Where the coarse grid cannot test these
bands, the assessment lists targeted `ε` refinements. It keeps all observed
crossings, including a reversed crossing if one occurs.

Macroscopic protection is retained separately: a guild whose complete
census trajectory remains above `10¹⁶` cells is protected on that recorded
horizon, even if it has no linear rare-population window. Such a point can
guide a targeted refinement between protection and a measured loss. It is
not assigned an exact rare-lineage probability of one and does not by
itself close a stochastic threshold bracket.

## A checked nonstationary outcome

Four completed census trajectories have persistent finite-amplitude cycles:
both invasion directions at `f=0`, with both fixed refuges, exchange
`10^-6/year`, active loss `0.001/hour`, and `epsilon=0.003` or `0.001`.
Their 40,000–100,000-year envelopes remain constant within the sampling
resolution. The respective periods are about 145.5 and 128.7 years, with
temperature ranges of 0.321 and 0.189 K. Both guilds remain above `10^24`
cells during the late cycles. No late census removal or stage-chart change
occurs.

![Persistent spatial dormancy cycles](figures/dormancy/spatial_cycles.png)

The mixed equilibrium near 281.535 K is still locally stable: its leading
real eigenvalue converges to approximately `-1.986e-4/year` at four numerical
difference scales. Thus these paths are candidates for an additional
finite-amplitude attractor, not evidence that the equilibrium loses linear
stability. Their phases differ, so equal endpoint stocks are not claimed.

Two 2,000-year continuations from the exact recorded 80,000-year states use
tenfold tighter relative tolerance, a one-year maximum step and annual
observation while retaining the ten-year census. They agree with the
original temperatures within `7e-7 K` at common times. Period estimates
change by less than 0.006% and temperature ranges by less than 0.001%.
Neither control needs numerical recovery or removes a guild. The
[root and envelope audit](review/dormancy_spatial_cycle_check.json) and
[precision evidence](review/dormancy_spatial_cycle_precision.json) retain
source, input and raw-output hashes. These are controls within the same
stiff-solver family; they do not prove a periodic orbit or exhaust its basin.
All four original paths retain their nonstationary classification.

## Reproduction and current evidence boundary

Run the physical experiment, generic endpoint comparison, first-window
scoring and final T3 assessment in that order:

```sh
uv run python -m terra_prisca.haze_world.dormancy_jacobian_experiments --mode census --workers 4
uv run python -m terra_prisca.haze_world.turnover_assessment --variant dormancy
# Run the required first-window prefixes at their recorded horizons;
# this is one selected example.
uv run python -m terra_prisca.haze_world.dormancy_jacobian_experiments \
  --mode uncensored --years 3000 --case-id dormancy_0010 --workers 4
uv run python -m terra_prisca.haze_world.turnover_survival --variant dormancy
uv run python -m terra_prisca.haze_world.dormancy_assessment
```

The probability stage requires annual uncensored profiles for culled cases
or cases whose dense minima enter the rare-population range. Its missing
profile error identifies where those runs are needed. Large raw arrays stay
under gitignored `local/haze/dormancy/`; receipts pin the source graph,
protocol, environment and payload checksum. Derived summaries, assessment
JSON and figures belong under `figures/dormancy/`.

The earlier guarded runner has a **bounded first-window qualification**. Its
[numerical review](review/dormancy-trial-integration-review-2026-11-11.md)
records the successful 3,000-year control and the unqualified longer tail.
It rejects
nonfinite numerical trial stages through the existing rollback/refinement
path while reusing the frozen physical function. A guarded prefix is
accepted for assessment only when every census physical source and parameter
matches, the source graph adds exactly `dormancy_prefixes.py` and
`dormancy_trial_integration.py`, both added hashes match current files, and
the protocol records `solver="nonfinite_stage_trial_rejection"`, architecture
and operating system.

The production Jacobian variant has a separate
[qualification](review/dormancy-jacobian-review-2026-11-11.md), covering both
original 3,000-year first-window controls and a formal 100,000-year census
pilot. Its source graph adds exactly `dormancy_jacobian_experiments.py`,
`dormancy_jacobian_integration.py` and the frozen trial helper, with solver
flag `analytic_dormancy_switching_jacobian`. Current file hashes and platform
provenance must match. Neither allowlist accepts partial or mixed variants.
Census and prefix recording rules retain their original
one-cell/ten-year and zero-floor/annual definitions, respectively. This
declared numerical change does not alter the ongoing frozen census batch.
Any numerical repeat is selected by an explicit receipt fingerprint shared
by the endpoint and probability consumers. Reused census evidence requires
the canonical physical graph, an approved numerical graph and no removals.
A numerical trial-control pass is not by itself
a scientific endpoint or survival result.

The [platform check](review/check_dormancy_platform_precision.json) records a
real precision limit. Matched Mac and Linux runs agree in climate and final
stocks, yet a transient Linux dormant bank of about 996 cells changes the
strict stationarity flag. It represents about `10^-23` of total biomass and
does not resemble the macroscopic cycles above. Both original flags remain;
criteria are not relaxed. Tiny-stage stationarity is therefore assessed
separately from material ecological or climate oscillations.

No decisive T3 result is stated here until the T1 basin gate passes and the
full receipts, stationarity checks and required first-window evidence have
been reconciled. The source assumptions, local/global distinction and
finite-population interpretation apply to every later result on this page.
