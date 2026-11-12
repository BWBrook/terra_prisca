# Independent review of homogeneous thermal-lag transients

Codex independent mathematical and receipt review, 12 November 2026. This
review covers the homogeneous B2/B3 implementation and its separate
first-episode assessment. It does not repeat the 100 kyr ensembles or review
spatial transients. The producing agent retained ownership of both modules.

**Disposition:** accept the physical equations, actual-temperature branching
rates, amended first-episode interpretation and the finite-window PB5
counterexample. The main ensemble has sampled source checks, not a certificate
of the source over every accepted dense interval. The separately tightened
controls use the interval bound derived below. Keep that distinction in any
result or release description.

## Source identity and completed evidence

The 29 main receipts comprise five B2 and 24 B3 cases, all completed at their
specified 30 kyr and 100 kyr horizons. They share producer SHA-256
`ec9e06f77f647bf7d5be2a9ec7f0747a4430e35945212ca26a650fb336ebc592` and
archived source epoch `f77468b9d23032c908b7`, under ignored
`local/haze/dynamic_transients/source_epochs/`. I independently verified all
21 archived source/input hashes and all 53 uncensored/census NPZ hashes in
those receipts. The starting repository commit was
`39572a4a671dbdc8301ddb5cecb535345a88e29c`.

The assessment source reviewed has SHA-256
`c431cb0cc42493aa0e467ec3eabee5fd06744e91271ce4acd97d9d78623d910a`.
Its published assessment records the correct input-manifest hash, and all
29 referenced receipt hashes match. The final assessment JSON SHA-256 is
`53331f5128ea058c737e42c48ad6acfb2aa5a48f46c330ec70cec9f30c083895`.
Source additions made during this review comprise the producer's source-bound
certificate and the assessor's scalar output recount and clarified amendment
wording; old main receipts were preserved with their original epoch.

The tightened source-bound producer has SHA-256
`ef45d4a944bf888862313340cbab5d4ed3c3d1690459f30611ccdfe46fb85159`,
epoch `47c84ea93d74450d537d`. Compared with the main epoch, only
`dynamic_transients.py` differs. All four controls' archived source hashes
and all six uncensored/census NPZ hashes were independently rechecked.

## Physical equations and branching rates

For uptake per unit biomass `q_i`, yield `Y_i`, maintenance `m_i` and active
loss `L`, define synthesis `s_i = Y_i(q_i-m_i)` in hours. At the actual
thermal state, the physical biomass equation is

    dX_i/dt = H X_i (s_i-L),  H = hours/year.

The coordinate transform is `X = SCALE softplus(z)`, so multiplying the
coordinate derivative by `SCALE sigmoid(z)` recovers this equation. The
rare-population asymptotic branch differs from the exact transform by less
than about 5e-14 relatively at its cutoff. The same transform applies to
acetate. The explicit sixth equation is

    dT/dt = [T_climate(r)-T]/tau.

The hydrogen, biomass-assimilation, acetate and methane terms agree with the
five physical stock equations evaluated at this explicit `T`. A trial
temperature is clipped only while evaluating solver trials; accepted output
is stopped at the physiological temperature-domain boundary. At zero lag,
the temperature is the original piecewise climate response.

I separately reconstructed the physical flows from uptake, synthesis,
assimilation, recycling and atmospheric conversion, rather than calling the
five-stock RHS as the expected value. At
`(p,X_A,X_M,C,r,T)=(50,1e-4,3e-4,1e-5,0.4,285 K)` and `tau=3 yr`, fixed and
product chemistry recovered the physical derivatives with maximum relative
error below 7.5e-16. The corresponding hydrogen-equivalent inventory closure
residual was below 1.8e-18 mol H2/L/yr.

The birth/death decomposition is

    birth_i = H max(s_i,0)
    death_i = H [L+max(-s_i,0)].

Therefore birth minus death equals the retained per-capita growth law even
when maintenance exceeds synthesis. The implementation uses the trajectory's
actual lagged temperature when calculating both rates. The separate check
above agreed to 1.8e-15/year. At the same chemical state, instantaneous climate
temperature would instead be 274.002 K and would change the two per-capita
rates by approximately 6–11/year; this is a consequential check, not a
numerically negligible distinction.

## Source continuation: qualification and interval bound

The main producer checks log acetate-coordinate source at the start,
midpoint and end of every accepted LSODA interval. All 29 uncensored runs
have reported maxima between 0.7743 and 9.7386, whereas the trial continuation
begins at 100. This is a large observed margin. Three samples nevertheless
do not prove that an interior source maximum is below 100. The main NPZs
retain step temperature ranges, but not the dense acetate and acetogen
polynomials; the missing interval certificate cannot be reconstructed
afterwards from those samples alone.

A cheap conservative bound is available before discarding each dense
polynomial. If `zA_max` and `zC_min` are the exact polynomial extrema on that
accepted interval, and `qA_max` bounds saturating acetogen uptake throughout
the declared temperature domain, then

    log source <= log(H qA_max/4) + log(SCALE)
                  + log softplus(zA_max) - log(ACETATE_SCALE)
                  + logaddexp(0,-zC_min).

This follows because acetate production per unit biomass is at most
`H qA_max/4`; assimilation subtracts from it. Both coordinate functions in
the bound are monotone. The extrema occur at polynomial endpoints or
validated real roots of the derivative. For the reference saturating
kinetics and constant cold continuation, uptake capacities are piecewise
linear in temperature, so the maximum over the temperature knots is a
global bound. Here `qA_max = 0.01633808049535604 mol H2/gDW/hour`.
Product-dependent cessation thresholds cannot invalidate this uptake ceiling.

The producing agent implemented this bound for the four already-planned
tighter controls. I inspected that implementation and checked it against
12 independent cubic coordinate paths, each evaluated at 1,001 points;
every calculated bound exceeded the sampled source maximum. These examples
supplement the mathematical argument and the new interior-extremum test;
they are not a substitute for the bound. The four controls' maximum
whole-interval upper bounds are all below 100. The controls use `rtol=2e-9`,
maximum step 2 yr and 0.5 yr samples. No full main-grid rerun was requested.

| Control | Uncensored source bound | Census source bound | Largest absolute minimum-count change, decades |
|---|---:|---:|---:|
| B2 fixed, f=0, lag 1 yr | 4.4740 | — | 0.0000382 |
| B2 fixed, f=0, lag 100 yr | 25.1274 | — | 0.0000351 |
| B3 fixed, f=0.5, lag 3 yr, A into M | 29.3909 | 11.9957 | 0.001158 |
| B3 products, f=0.5, lag 3 yr, M into A | 30.1629 | 3.3366 | 0.001140 |

All four preserve their above/below-one classifications. The two B3 census
endpoints and first removals are unchanged: methanogens removed at 20 yr in
the fixed A-into-M case, acetogens removed at 10 yr in the products
M-into-A case. Maximum absolute peak-temperature change is below 1.5e-6 K.
The products control uses the continuation in one rejected trial; its
whole-interval bound still excludes the continuation everywhere on the
accepted dense path.

The eight first-window refinement comparisons also retain their assembly
classes. They do not justify high-precision survival estimates: the B2
100-year-lag acetogen probability changes from 0.00056144 to 0.00056777,
and some rarity thresholds move one or two decades. The two qualified B3
resident log probabilities change by less than 0.019, preserving the same
negligible conditional-survival conclusion.

Thus it is supported that the certified controls never enter the source
continuation anywhere on their retained dense interpolants. For the main
grid, state only that all sampled accepted checks remained far below the
continuation, with the stronger control evidence reported separately.

## First episode, censoring and assembly interpretation

The amendment is explicitly post-diagnostic. It fixes a real interpretive
failure in the retained legacy diagnostic: 53 of its 58 guild scores begin
after that guild's own first below-one-cell crossing. A later global minimum
can select continuous recovery from an earlier fractional-cell stock.

The new algorithm starts at the first contiguous excursion below 1e16 cells,
requires a declining portion, and refines the rarity threshold only inside
that original episode. If no subepisode meets the uptake-fraction condition,
it returns unassessed. It never substitutes a later deeper episode. An
initially rare, purely growing invader is also unassessed; it does not cause
the code to scan forward for a later declining episode. Describe the rule
as the **first rare episode, scored only if declining**, rather than implying
that such invaders are skipped in search of a later eligible episode.

Independent synthetic checks confirmed that:

- a later deeper minimum cannot replace the first eligible episode;
- failure to attain rarity inside that first episode remains unassessed;
- a terminal declining episode is horizon conditional, with a finite
  conditional survival probability, rather than being assigned zero;
- another guild's below-one crossing inside the window invalidates an
  assembly inference without deleting the conditional branching calculation.

The additional other-guild likely-loss check is also conservative: a low
conditional first-window probability in the other guild can mark this
window unassessed. It does not establish a joint stochastic endpoint.
The recorded terminal flag remains available even when an assembly status
becomes unassessed.

The 58 amended guild rows contain 31 qualified conditional first windows,
26 unassessed because of other-guild loss, and one with no rare episode
(methanogens in B2 at f=0, lag 1 yr). No actual row has a nondeclining first
episode; that branch was checked synthetically. All 24 displaced-resident
B3 rows have a qualified first window; their maximum recorded uptake
fraction is below 1e-10. Their
log survival probabilities range from about -124579 to -2871. Ordinary
probabilities therefore underflow to zero; this is not a mathematical claim
of exact zero. Their logs are retained. All 24 uncensored displaced-resident
global minima cross below one cell, supporting homogeneous PB6 in its
specified deterministic diagnostic sense.

These probabilities condition on the recorded environment, the birth/death
split, linearly interpolated sampled rates and the Poisson-entry convention.
They establish neither simultaneous finite-world survival nor recovery after
a guild has been removed. The separate ten-year census endpoints answer a
different, explicitly rule-dependent question. A qualified first episode
also makes no claim about subsequent oscillations.

## PB5 counterexample and tighter control

The main fixed-chemistry, `f=0`, `tau=1 yr` trajectory never crosses below
one global cell over 30 kyr. Its dense global minima are
`log10 N_A = 8.03838034466` and `log10 N_M = 22.0892645960`; both first-crossing
times are absent. Because the whole-run dense minimum is above one, this
also covers PB5's specified 20 kyr test window. The trajectory's final
6 kyr temperature span is 1.26635 K. A finite observed envelope is not a
proof of an attracting or permanently bounded cycle.

The independent receipt audit used:

- main `B2_f0_tau1-efc80c67ce99eb1e2f60.json`, receipt SHA-256
  `563d21b07c0f6c8bcac5e50ffaa604a8c32fbc1d3f1cca2b21de4d0d3f424773`;
- tightened `B2_f0_tau1-29c5d3cd28fc0c503ddd.json`, receipt SHA-256
  `d3312fa9e9adfcac5a78fc93abd2efbdf08a7b86c111f52df6097761ea7453da`;
- tightened raw NPZ SHA-256
  `ad21a22e8c6d4ab50089ea12617170a4f644e8e361dde46f2f07019c69e63eca`.

The tighter run uses `rtol=2e-9`, maximum step 2 yr and 0.5 yr samples,
compared with the main `2e-8`, 50 yr and 1 yr settings. Its dense minima are
`8.03834222064` and `22.0892567079`, differing from the main run by only
`-3.81e-5` and `-7.89e-6` decades. Neither guild crosses below one cell.
Its interval source certificate excludes continuation throughout the
accepted dense path. This refutes PB5's homogeneous universal statement
that every selected `f=0`, lag-at-least-one-year B2 path loses a guild
within 20 kyr. It does not establish indefinite finite-population persistence,
nor address PB5's still-unrun spatial clause.

## Verification and remaining actions

I ran the two relevant regression files independently: 15 tests passed in
2.77 seconds. After the final recount/output addition I reran the three
assessment tests; all passed. The physical-flow reconstruction, redox identity, source-bound
examples, synthetic episode cases, hash inventory and output recount above
were separate small diagnostics. I did not launch a new long trajectory or
edit producer, assessor, tests or result tables.

Before closing the stage:

1. Preserve the old main epoch and the new certified-control epoch separately;
   publish the main-grid sampled-check qualification and all four controls.
2. Retain the precise first-episode wording and the conditional, finite-horizon
   limits. Do not equate census endpoints, first-window probabilities and
   later uncensored global minima.

No additional physical-equation defect or first-episode selection defect was
found in this bounded review.
