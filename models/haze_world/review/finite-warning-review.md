# Immigrant-coordinate failure and repair

Codex (GPT-6), 10 November 2026. **The warning was a genuine integration
failure, not a qualified harmless trial.** The immigrant coordinate has been
replaced; the physical equations, census rules and zero-immigration
coordinate are unchanged.

The [checker](check_finite_warning.py) loads the old integrator from
`2b8b070`, reproduces its failure, tests the repair and compares selected
previously successful cases. [Results, source hashes and tolerances](finite_warning_check.json):

```sh
uv run python models/haze_world/review/check_finite_warning.py
```

## The affected case

Case **0123** has product-activity feedback, f_ac=0.9, a one-cell removal
floor, mean immigration 0.1 cells/year into each guild, ten-year censuses,
and methanogens introduced into the acetogen-only control. The historical
100-year prefix scan covered all **108** positive-immigration cases:
107 completed and only 0123 warned and failed. Completed diagnostic files
must not be confused with successful trajectories.

The shifted-softplus scheme evaluated `exp(anchor − z)` at
**anchor=−62.591802**, **z=−952.465571**, argument **889.873769**. The timed
callback recorded 21.587497 years. Its trial state included pressure
26,479.9 Pa, acetogen biomass 0.9046 gDW/L, acetate 1.101 mol/L, and
**negative** methanogen biomass −6.5573×10⁻³¹ gDW/L. This was outside the
physical population domain, not an observed biological excursion. An
internal solver trial may extend beyond the requested census time; the
integrator ultimately failed before returning the first census.

On the physical side of the old anchor, the exponential factor is at most
one. The overflow therefore came from an unphysical numerical trial.
Nevertheless the endpoint guards subsequently detected failure, so it was
not safely ignorable. Tighter and step-limited scratch replays of the old
scheme also failed through excessive solver work; not every failed replay
produced the same overflow warning.

## Repair without changing the population model

For a guild receiving mean biomass input i>0, use

    Z = X / (i × 1 year),
    dZ/dt = g Z + 1/year.

This scaled linear coordinate is regular at X=0 and has no shifted-softplus
boundary singularity. It is algebraically the same equation dX/dt=gX+i.
No rates, census stocks or rare populations are clipped. Accepted negative
stocks remain errors. Guilds with i=0 retain the previous positive softplus
coordinate, including exactly absorbing absence.

The regression suite checks analytic growth/immigration, decay across
18 orders of abundance, import/cull budgets, initial and scheduled censuses,
the no-removal limit, the reference invasion and case 0123. **All nine tests
pass.**

## Bounded numerical checks

The repaired 0123 prefixes complete without warnings: approximately
0.3 seconds for 100 years and 2.3 seconds for 1,000 years locally. Methanogen
removals start at 20 years. The 100-year default solution also agrees with
rtol tightened tenfold, absolute tolerances tightened tenfold and maximum
step 0.1 year: census activity and cull topology match exactly; maximum
retained log-stock difference is 4.93×10⁻⁶. Absolute differences are below
1.6×10⁻¹² Pa, 4.4×10⁻¹⁹ mol/L acetate and 2.3×10⁻¹⁶ in methane ratio.

Eight previously successful cases were replayed for 100 years with both
coordinates. All retain exactly the same census activity and cull times,
guilds and reasons. Retained log-stock differences are at most 1.99×10⁻⁵;
macroscopic stock differences remain below 3.2 times the declared reference
local-tolerance scale.

This is **not bitwise ledger identity**. Case 107 fails the separately
declared 10⁻⁴ culled-log-stock comparison: its difference is 1.30×10⁻⁴
(about 0.013%), equivalent to at most 1.89 mean cells, 5.67×10⁻¹³ gDW and
4.67×10⁻¹⁴ mol H₂-equivalent per event. Across all eight comparisons, the
largest absolute cull difference occurs in case 141: 3.39×10⁻⁹ gDW and
2.80×10⁻¹⁰ mol H₂-equivalent. Those numerical differences are retained in
the report; the cull-amount tolerance was not relaxed to erase the failure.

These checks qualify the numerical repair over the stated prefixes. They
do not validate a tighter-control 100,000-year trajectory or a complete
phase map. The original long-run dataset remains historical; the entire
main, census and extension sets require new source fingerprints and fresh
completion receipts before results from the repaired integrator are used.
