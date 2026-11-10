# Independent audit of buffered-refuge design

Codex (GPT-6), 10 November 2026. Reviews the specification in `4720c65`.
This audit checks the model's mathematical interpretation and a bounded
three-patch equilibrium. It does not select or fit the main-grid outcomes.

## What the new geometry changes

A fixed-temperature refuge no longer forces another habitat to compensate
its heat anomaly. That removes the earlier geometric conflict. The bulk
retains the source model's global temperature and its named cold continuation;
refuges at 278 and 286 K are inside the measured temperature window.

This is a prescribed thermal environment, not an energy-balance model of a
hydrothermal zone or water column. An external heat bath maintains each refuge.
A small departure of area-mean habitat temperature from global temperature
is not an energetic closure or an empirical calibration of refuge area.
For both default 2% refuges,

    mean(T_habitat) − T_global = 0.02 (286 + 278 − 2 T_global).

Across the default closure's 273.39–297.008 K span this ranges from +0.3444
to −0.60032 K. The exact trajectory range should still be reported. Remaining
within this physiological temperature interval does not mean remaining within
the published radiative domain: the low-methane bridge and high-methane
plateau remain assumptions.

## Conservation and equilibria

Let `w_j` be habitat weights, `B_i=sum_j w_j X_ij`, and `g_ij` annual biological
net growth. The specified exchange is

    E_ij = d (B_i − X_ij),
    sum_j w_j E_ij = 0.

For a guild present globally at a positive-dispersal equilibrium,

    X_ij = d B_i / (d − g_ij),
    sum_j w_j d / (d − g_ij) = 1,
    g_ij < d.

These are exact equilibrium identities, not a quasi-steady dynamical closure.
They provide an independent way to construct or check conditional starts.
For a single resident with fixed product activities, at fixed methane `r`,
let `q_j(p)` be annual uptake per dry mass and
`H_j(p)=J−k_ex(p−p_atm)` annual donor supply remaining after the outlet. Where
uptake is positive,

    X_j = H_j(p_j) / q_j(p_j),
    (d−g_j(p_j)) H_j(p_j) / q_j(p_j) = d B.

For a trial `B`, this last equation is monotone in local pressure on the
physical branch: donor capture falls while uptake and growth rise with
pressure. The upper limit is the smaller of the lifeless pressure and the
pressure at which `g=d`. Local pressures can therefore be solved separately,
followed by the scalar consistency equation `B=sum_j w_j X_j`; the shared
methane balance supplies an outer scalar equation in `r`. A zero-uptake sink
needs the separate branch `p=p_lifeless`, `X=dB/(d−g)`, rather than dividing
zero donor capture by zero uptake. Product-dependent acetate thresholds add a
local acetate consistency condition.

For full coexistence the two `B_i` consistency equations couple through each
habitat's donor balance, plus the common methane equation. Denominators
`d−g` make an unscaled elimination poorly conditioned at very small `d`;
per-capita balance with positive biomass coordinates is an alternative.

A rare guild's instantaneous invasion operator is

    diag(g_j−d) + d 1 wᵀ.

Its dominant eigenvalue, evaluated in the resident environment, is the
appropriate metapopulation invasion rate. A refuge's local temperature or
break-even pressure alone does not include emigration loss and subsidies of
its competitor from other habitats.

## Independent three-patch anchor

The [checker](check_buffered_design.py) constructs local uptake, assimilation,
catabolism, biomass growth, exchange, acetate and methane balances directly
from source guild primitives. It does not call the new model RHS or its
parent's equilibrium finder to construct the equilibrium. Its independent
nonlinear solve eliminates acetate algebraically at fixed activities.

For `f=0.5`, weights `(0.96,0.02,0.02)`, temperatures `(T(r),286,278)` K and
`d=0.001/year`, it finds

- methane ratio `r=0.19510686213952005`;
- global/bulk temperature `281.53483197 K`;
- local hydrogen pressures `(22.48628493,19.97802291,27.61638376)` Pa;
- scaled equilibrium residual about `1.4e−15`;
- largest real eigenvalue about `−9.11e−4/year` in the full 13-state system.

The [numeric evidence](buffered_design_check.json) compares perturbed RHSs,
weighted exchange, redox budgets and the full Jacobian spectrum with the
implemented model. It also compares product-feedback RHSs without silently
holding chemical methane activity fixed. Buffered temperature has zero
`dT/dr`; local chemical rates can still depend on `r` through methane activity.
Source hashes and the scope of common inputs are retained. This is numerical
independence of implementation, not independent empirical validation.

```sh
uv run python models/haze_world/review/check_buffered_design.py
```

## Reading B1 to B5 without turning them into acceptance tests

- **B1.** The earlier path-protection check has 46 survivors, including eight
  trajectories stopped at a physiological boundary. It supports protection
  over those observed prefixes, not a general theorem about indefinite
  persistence. Fixed buffered temperatures and low exchange make the present
  prediction plausible, but actual global minima, fluxes and immigration-load
  effects remain the tests.
- **B2.** Different finite-census endpoints alone do not establish genuine
  continuous-system multistability. First rule out slow settling and numerical
  or extinction-census barriers; then refine candidate equilibria, test their
  full local stability and examine uncensored basin trajectories when needed.
  The planned sensitivity gate should be applied after that distinction.
- **B3.** The path must be checked, rather than assuming every M invasion
  crosses 297 K. That peak matters for transitions from a low-methane start to
  a hazy endpoint. At `f=0.9` the acetogen-only start is already hazy; the old
  isolated hot partitions also stop short of the peak. One-sided rescue is a
  model hypothesis, not evidence that a particular Archean refuge existed.
- **B4.** Export from source habitat `k` into recipient `j` is
  `I_j←k=d w_j N_k`, not the full `d N_k` into every recipient. Mature source
  abundance is not its minimum during the transient. With the declared
  inoculum, however, even a newly seeded 2% refuge begins with about `3e15`
  cells, so the tested `d=1e−9/year` can already deliver many cells annually.
  There is no need to infer a universal `1e−25/year` threshold from this grid.
  Nor is `d=1/year` automatically a homogenized or failing limit: fixed-source
  invasion advantages at the default temperatures are about +2.79/year for M
  at 286 K and +6.67/year for A at 278 K. Actual conditional pressures matter.
- **B5.** A climate contrast below 0.1 K is a prediction to measure against a
  declared same-configuration control. Coexistence, material hydrogen use and
  global climate response should be reported separately. A trace imported sink
  is not an established climate-regulating population.
