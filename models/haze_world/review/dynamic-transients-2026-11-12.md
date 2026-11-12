# Homogeneous B2/B3: thermal-lag trajectories

Codex, 12 November 2026. This is the homogeneous nonlinear tranche authorised
by the [continuum specification](../continuum-habitats-spec.md), after the
[method freeze](../continuum-habitats-methods.md). Habitat-spread trajectories
are not run here. The original PB5/PB6 predictions remain unchanged.

## Protocol

B2 covers the five reference fixed-product mixtures unstable at the selected
lags: f=0 at 1/10/100 years and f=.5 at 10/100 years. Each starts from the
mixed equilibrium with acetogen biomass multiplied by exp(.001), uses no
census, and runs for 30,000 years. Products has no B2 case because its
reference equilibrium has no detected instability on that lag grid.

B3 has 24 cases: both invasion directions, f=0/.5, thermal lag 0/3/30 years,
and fixed/products chemistry. The resident begins at its conditional pure
equilibrium. The missing guild receives the established 1e-12 gDW/L dose.
Each uncensored run retains positive guild logarithms and runs for 100,000
years. A separate rerun applies a global one-cell census every ten years,
without immigration. The census endpoint is a deterministic finite-rule
outcome, not a joint demographic survival probability or a stability proof.

The model keeps the historical hydrogen, two biomass, acetate and methane
budgets. Every biological rate uses the explicit lagged temperature when
the lag is nonzero. At zero lag it recovers the original climate closure.
No physical temperatures are clipped: only rejected numerical trial states
receive the established boundary extension, and accepted intervals must
remain in the declared physiological support.

## Numerical qualification

Biomass and positive acetate use the existing softplus positive-coordinate
chart, logarithmic at rare abundance. Initially zero acetate is promoted
to that chart after its first positive accepted step. Underflowed biomass
retains a finite logarithm and its per-capita dynamics, so a continuous run
may recover from biologically meaningless subcell expectations; these are
diagnostic trajectories, not finite populations.

An analytic coordinate Jacobian includes uptake, product-threshold,
assimilation, softplus and explicit thermal derivatives. Only the thermal
physiology column uses a numerical stencil. Four fixed/products, zero/finite
lag regression cases compare it with the physical RHS. Checked dense-output
polynomial roots locate guild minima and one-cell crossings. Temperature
extrema are evaluated on the explicit thermal polynomial, or on the original
piecewise climate response at zero lag.

The first numerical batch exposed rejected solver trials in which the
log-acetate source exceeded exponential representation. That batch and its
source epoch are retained under ignored `local/haze/dynamic_transients/`;
missing receipts are not biological outcomes. The final route uses the
analytic Jacobian and a finite tangent continuation only for trial sources
whose log exceeds 100. Every accepted dense interval is checked at its
start, midpoint and end; a detected accepted continuation raises an error.
These three samples are not an interval certificate. Their largest source
log is 9.739 across the 29 main trajectories, far below the threshold of 100.

The four tighter controls add a conservative interval certificate. Exact
checked dense-polynomial extrema bound the acetogen coordinate above and the
acetate coordinate below. A global physiological uptake ceiling then bounds
the log source throughout each accepted interval; assimilation can only lower
this source. Any upper bound above 100 rejects the trajectory. This adds no
physical floor or equation change. Its producer epoch is distinct from the
main batch and is recorded per receipt. Regressions check interior polynomial
extrema and inject an unsafe accepted source. Exact producer sources and input
hashes accompany every raw receipt.

## Legacy window and amended first-episode interpretation

The producer retains the existing bottleneck diagnostic:

    N_lin = min(1e16, 1e8 N_min).

That legacy threshold is reduced by decades until the guild's local/global uptake
fraction is at most 1e-10 throughout its scored interval. Only the first
contiguous rare window is scored. Birth and death are computed at the actual
thermal state; their difference equals the retained per-capita growth law.
The existing backward branching solver operates in that recorded exogenous
environment. Its log probabilities are retained through ordinary numeric
underflow.

A terminal window is horizon-censored, not automatically assigned zero
survival. A missing rare window is reported as unassessed, not certain
persistence. Flags retain prior below-one-cell loss of the other guild;
later continuous "ghost" recovery must not be read as a physically available
rescue. A robust first window does not establish survival through subsequent
cycles or a common finite endpoint.

**Post-diagnostic procedural correction.** In growing recurrent paths,
anchoring the threshold to the full-run global minimum can select a later
excursion after an earlier one has already crossed below one cell. For example,
the fixed f=0, 10-year-lag pilot first crosses below one acetogen cell near
1,830 years, while its legacy threshold first selects a window near 14,422
years. Calling that the first physical bottleneck would be wrong.

The separate `dynamic_transient_assessment.py` therefore starts with a fixed
cap of 1e16 cells, selects the **first contiguous rare episode, scored only
if it is declining**,
and lowers the threshold by decades only within that same episode until
uptake is at most 1e-10. It never skips to a later deeper episode. If the
first episode cannot satisfy rarity, it is unassessed rather than replaced.
This is an explicit correction after diagnosis, not a wholly prespecified
first-survival estimator. It changes neither trajectories nor PB5/PB6.
An initially rare growing invader remains unassessed; the code does not skip
its initial episode to find a later declining one.

In the completed batch, 53 of 58 legacy windows start after that guild's
first below-one crossing, including 21 of 24 displaced residents. The amended
resident windows all enter before their own or the other guild's crossing.

Conditional probabilities are retained even where they cannot support an
assembly claim. A threshold below one cell, prior own loss or loss of the
other guild before/inside the window makes assembly unassessed. Other-guild
loss is checked at both window start and end, with its own first-window
likely-loss diagnostic retained as well. Terminal windows remain censored
at the observed horizon. The legacy global-minimum calculation is published
alongside the amended primary diagnostic so that the procedural effect is
visible.

The global minimum can occur in a later window than the first one. Endpoint
fate under the one-cell census is reported separately. PB6 refers to the
displaced resident: methanogens for A_into_M and acetogens for M_into_A.

## Reproduction

```sh
uv run python -m terra_prisca.haze_world.dynamic_transients --workers 2
uv run python -m terra_prisca.haze_world.dynamic_transient_assessment --refine
uv run pytest -q tests/test_dynamic_transients.py tests/test_dynamic_transient_assessment.py
```

The main-batch producer is preserved in its source epoch. Running the current
producer makes a new, interval-certified epoch rather than overwriting that
evidence. `transient_archive_manifest.json` names the canonical main receipts
and four tighter controls, hashes every raw/source file and lists public-file
hashes. The initial failed numerical epochs remain separate.

Large raw arrays and receipts remain under ignored
`local/haze/dynamic_transients/`. The public tables are `oscillations.csv` and
`invasions.csv`, with a `transient_manifest.json`. Selected compact traces
retain original one-year samples plus exact checked dense-minimum states;
they do not interpolate invented trajectories. Finite late-window spans
are observational diagnostics, not a claim of an attracting limit cycle.

## Results

All 29 main trajectories completed their full horizons without a habitat exit
or numerical failure. The five B2 dense minima are shown as log10 global cell
counts; large negative values are continuous diagnostic expectations.

| Acetate fraction | Lag (yr) | Acetogen minimum | Methanogen minimum |
|---:|---:|---:|---:|
| 0 | 1 | 8.03838 | 22.08926 |
| 0 | 10 | −171.87022 | −13.47429 |
| 0 | 100 | −1823.32354 | −281.85436 |
| .5 | 10 | −49.42129 | −16.47495 |
| .5 | 100 | −839.77219 | −419.14564 |

**PB5 fails in its homogeneous claim** []{.C51}. At f=0 and a one-year lag, neither
guild falls below one global cell during the full 30 kyr. The last four
temperature spans are 1.247, 1.258, 1.264 and 1.266 K. Those finite windows
suggest a leveling envelope; they do not establish an attracting limit cycle,
indefinite demographic persistence or a theorem of boundedness. At ten- and
100-year lags, acetogens first cross below one cell at 1,830 and 1,013 years,
and methanogens at 5,688 and 3,259 years. The habitat-spread half of PB5 lies
outside this homogeneous tranche.

**PB6 holds for all homogeneous settings** []{.C52}. Every displaced resident in all
24 B3 runs crosses below one global cell, including product chemistry and
both invasion directions at every lag. Resident-methanogen minima range from
10^−1244 to 10^−3163 cells; resident-acetogen minima range from 10^−20399 to
10^−54101 cells. These extrapolated continuous minima are not recoverable
finite populations.

The separate one-cell/ten-year census removes the resident in every run.
All 12 A_into_M runs end acetogen-only and all 12 M_into_A runs end
methanogen-only, demonstrating invasion-history dependence under that stated
finite rule. Acetogens displace methanogens at the 20-year census; acetogens
displaced by methanogens are removed between ten and 290 years. This does
not give a coupled stochastic endpoint probability.

The amended first-episode analysis gives all 24 displaced residents
conditional log survival probabilities between −2,871 and −124,579.
Their ordinary probabilities underflow, while the logarithms remain finite.
The other guild has not yet crossed its physical floor in these resident
windows. Of all 58 guild diagnostics, 26 later windows are unassessed for
assembly because the other guild was already lost before or during the
window, and one has no rare episode. The 31 remaining conditional diagnostics
include the 24 displaced residents; a safe first B2 episode does not imply
survival through later cycles.

The legacy-window diagnosis and explicit procedural correction are retained
as a separate evidence claim []{.C53}; neither replaces the original fixed
prediction or the independently evaluated census outcome.

Four controls tighten relative tolerance tenfold, reduce maximum steps from
50 to two years and halve the retained sampling interval. They cover B2 f=0
at one- and 100-year lags, fixed B3 f=.5/tau=3/A_into_M, and products B3
f=.5/tau=3/M_into_A. The largest minimum change is 0.00116 in log10 cells,
and the largest peak-temperature change is 1.46e-6 K. All below-one classes,
primary assembly-assessment classes, census endpoints and census-removal
clocks agree. The interval source bound stays below 30.163 in all four
uncensored controls and below 11.996 in their census reruns.

First-window probabilities are finite-grid diagnostics. In the B2 100-year
control the conditional probability changes from 0.0005614 to 0.0005678;
other supported survival classes remain unchanged. Rarity thresholds can
move by one or two decades with the sampling grid. The two displaced B3
resident log probabilities change by less than 0.019, retaining the same
negligible conditional survival interpretation. Detailed comparisons are in
`transient_refinement_first_survival.csv`; they should not be promoted to
high-precision survival estimates.

`transient_archive_manifest.json` lists 33 canonical receipts, 59 raw NPZs
and 42 archived source/input files: 261,442,585 bytes in 134 distinct files.
Fourteen public evidence files have their own hashes. Every listed raw hash
and source epoch is checked when the index is built. The package is prepared
locally and has not been deposited. Fifteen focused tests pass; the parent
also arranged an independent audit of the RHS, rates, root diagnostics,
receipts, control bounds and window semantics. No conclusion here relies on
a failed or missing numerical receipt.
