# Finite-process audit

Codex, 10 November 2026. The short independent checks support the repaired, scaled-linear immigrant
coordinate, deterministic census rule and immigrant/cull ledgers.
The process must be described as a **deterministic census with continuous mean
immigration**, not an individual-based population process or an estimate of
extinction probability. This audit does not qualify the long-tail batch.

## Boundary and process definitions

For a guild receiving immigrant biomass density I per year, let o be one
year's input and use the scaled linear coordinate

`X = o Z`, `Zdot = g Z + I/o = g Z + 1/year`.

Here time is measured in years. This is exactly `Xdot = g X + I`; there is no
model approximation and no offset biomass. At Z=0 the derivative points into
the physical domain. A census removal resets Z to zero while retaining the
same positive immigration rate.

The earlier shifted-softplus immigrant coordinate was mathematically equivalent
but caused an observed LSODA failure during unphysical Newton trials. The new
coordinate removes that nonlinear transformation from immigrant guilds only.
It does not clip stocks, alter growth/loss rates or change immigration into
random arrivals. Negative accepted physical stocks raise an error. Solver
trial states are not interpreted as accepted populations.

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
pool. The coordinate scale must not enter those ledgers as extra biomass, and does not.

A frozen-growth control isolates this ledger. At two immigrants/year, a
five-cell census floor, one-year censuses and a 2.5-year run, approximately four
cells are culled at years 1 and 2 and one remains after the final half-year.
The exact input is five cells. Its global mass discrepancy is 2.1e-16 relative
to imported mass in this frozen-growth linear control. This does not establish
long-tail trajectory conservation for the biological model. The ledger's
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
  endpoint after 2.5 years to reported floating-point precision, exercising
  a very small physical immigrant density. Its first retained census was year 1, despite input
  beginning continuously at year 0.
- The repeated-removal control retained approximately one cell in the final
  partial interval while every census flag was absent. This distinguishes
  final stock from census retention and absorbing extinction.
- A 0.5-cell initial stock was removed at t=0, with the corresponding mass and
  H₂-equivalent exports.
- A dense immigrant control agreed with its analytic endpoint to reported
  floating-point precision.
- In the actual product-feedback model, the Nmin=0,I=0 control agreed with the
  existing continuum integrator within 2.2e-10 maximum relative state error
  over two years. Unchanged censuses caused no solver resets.


## Formerly failing protocol: first-census comparison

The products, f=0.9, Nmin=1, relative immigration=0.1/year, methanogen-into-
acetogen protocol was integrated through its first scheduled census at year 10.
A separate Radau solve of the physical equations plus the same mean immigration,
using the scaled linear immigrant variable, supplies an independent numerical
comparison to LSODA. This checks the previously failing interval, not the full
100000-year tail.

Both solves complete. Radau gives about 65.405964 methanogen cells before the
census; LSODA gives 65.406350, a relative difference of 5.9e-6. Both are safely
above the one-cell floor, and neither removes the guild. The resident biomass
agrees within 1.8e-15 relative error. The maximum remaining state difference is
2.6e-8 under the stated relative/scaled metric. This explicitly separates
rare-population relative error from errors in the larger physical stocks.

The Nmin=0,I=0 continuum control is unchanged by the immigrant-only coordinate
repair. So are the deterministic census schedule, per-cell mass, physical
immigration density, gross synthesis/loss equations and imported/culled
reducing-equivalent ledgers. The log-of-cell-conversion rewrite is algebraically
equivalent and avoids overflow in an intermediate volume/mass ratio.

```sh
uv run python models/haze_world/review/finite_process_check.py
```

[Check script](finite_process_check.py) and [results](finite_process_check.json)
retain the audited source hash and explicit controls. Synthetic controls freeze
nonpopulation states to test the process mechanics; they are not biological
forecasts. The scaled-linear repair passes these bounded checks; the long-tail batch was not duplicated.
