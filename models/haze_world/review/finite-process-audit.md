# Finite-process audit

Codex, 10 November 2026. The short independent checks support the shifted
population coordinate, deterministic census rule and immigrant/cull ledgers.
The process must be described as a **deterministic census with continuous mean
immigration**, not an individual-based population process or an estimate of
extinction probability. This audit does not qualify the long-tail batch.

## Boundary and process definitions

For a guild receiving immigrant biomass density I per year, let o be one
year's input, let s be the biomass scale, and choose anchor a so that
`s softplus(a) = o`. The coordinate is

`X = s [softplus(z) − softplus(a)]`.

Thus z=a represents exactly X=0. The transformed equation is

`zdot = (g X + I) / [s sigmoid(z)]`.

It points into positive biomass at the zero boundary when I>0. The offset is
a coordinate choice, not extra biomass, a numerical survival floor or an
immigrant pulse. The stable decoder using log1p/expm1 is algebraically the
same difference of softplus values. Its very-negative-tail expression has
`zdot ≈ g + (I/o − g) exp(a−z)`, the appropriate exponential limit. At the
boundary that limit gives I/o, a positive rate. The tail evaluation is a
numerical approximation to softplus, not an ecological timescale reduction.

With I=0, an initially positive guild uses the ordinary positive coordinate;
an exactly absent guild remains exactly absent. Following a census removal,
I=0 makes absence absorbing. With I>0 the coordinate retains the zero boundary
and continuous input resumes immediately after removal. Repeated census
removals therefore do not imply irreversible extinction.

`minimum_cells=0` disables removals while preserving the same continuous
physical ODE. Cell counts are derived from biomass using the assumed cell
mass and total active volume `habitat_l_cm2 * surface_cm2`. Counts may be
fractional because this remains a mean-density model. The area and cell mass
are assumptions, not measurements of Archean population size.

## Reducing-equivalent bookkeeping

Core continuous dynamics already have the combined inventory identity audited
in [full-coupling-budget-audit.md](full-coupling-budget-audit.md). If a_i is
biomass H₂-equivalent allocation per gram, immigration adds `sum(a_i I_i)`
to its per-litre inventory derivative. A census removing density X_i exports
`a_i X_i` from that inventory. No pressure, acetate or methane pulse should be
added for that discarded biomass.

The implemented ledgers use global quantities: imported or culled cells times
cell mass give gDW, and multiplying by a_i gives mol H₂-equivalent. Immigration
is external imported biomass, not biomass synthesized from the local donor
pool. The shift offset must not enter those ledgers, and does not.

A frozen-growth control isolates this ledger. At two immigrants/year, a
five-cell census floor, one-year censuses and a 2.5-year run, approximately four
cells are culled at years 1 and 2 and one remains after the final half-year.
The exact input is five cells. Its global mass discrepancy is 5.3e-7 relative
to imported mass, consistent with numerical integration in the transformed
coordinate. It is not machine-precision trajectory conservation. The ledger's
H₂-equivalent entries agree with the mass entries times a_i.

## Timing and interpretation of returned fields

A census occurs at t=0, before the first reported state, so initial positive
stocks below the floor are removed immediately. An exact initial absence
produces no removal event. Later scheduled censuses also report their states
**after removal**. A final partial interval is integrated and reported without
an extra census.

`first_extinction_yr` and its guild-specific counterparts mean first census
removal under this rule. They are not interpolated floor-crossing times,
waiting times for demographic extinction or extinction probabilities.
`arrival_events` mark first retained-at-census stock following census absence;
they are not immigrant arrival times. Continuous mean immigration has neither
Poisson waiting times nor stochastic colonization events.

`census_activity` has one entry for each census, including t=0. It is not indexed
by the possibly thinned output time array. For example, the short control
sampled at `[0,2,2.5]` years but its census flags described `[0,1,2]` years.
Never zip these arrays by position. The metadata's `n_censuses` includes the
initial census; `last_census_yr` can precede the final reported time.

`min_cells` and `min_log_cells` describe **pre-census samples**, including the
initial state. They exclude the continuous minima between censuses and the
post-removal jump at that same census. An immediate removal of 0.5 initial
cells in a zero-duration run correctly leaves min_cells=0.5, despite a reported
final population of zero. These scopes are documented in the returned metadata
and must survive into tables and interpretation.

Decisions extremely close to the census floor can depend on integration error.
The tiny exact-threshold conversion guard is not a general event-time error
bound. Material conclusions resting on such a near-threshold census need a
numerical convergence check; no such ambiguous comparison was needed for the
controls below.

## Short checks

- Exact zero initial stocks with I=0 remained zero even under positive
  synthetic growth, with no extinction or arrival events.
- Zero initial stock with I>0 and no floor recovered the analytic five-cell
  endpoint after 2.5 years within 1.7e-6 relative error, exercising the rare
  shifted coordinate. Its first retained census was year 1, despite input
  beginning continuously at year 0.
- The repeated-removal control retained approximately one cell in the final
  partial interval while every census flag was absent. This distinguishes
  final stock from census retention and absorbing extinction.
- A 0.5-cell initial stock was removed at t=0, with the corresponding mass and
  H₂-equivalent exports.
- A dense immigrant control exercised the non-rare coordinate and agreed with
  its analytic endpoint within 1.4e-8 relative error.
- In the actual product-feedback model, the Nmin=0,I=0 control agreed with the
  existing continuum integrator within 2.2e-10 maximum relative state error
  over two years. Unchanged censuses caused no solver resets.

```sh
uv run python models/haze_world/review/finite_process_check.py
```

[Check script](finite_process_check.py) and [results](finite_process_check.json)
retain the audited source hash and explicit controls. Synthetic controls freeze
nonpopulation states to test the process mechanics; they are not biological
forecasts. The bounded review found no core defect requiring a change.
