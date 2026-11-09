# Review of the revised survival experiments

Codex (GPT-6), 9 November 2026; reviewed `28295c0`. **Accept the revised
results within the tested settings and follow-up horizon.** No lasting
stranding was found in the 144-run grid. Mutation causes no extra extinction
relative to a matched frozen control that survives that grid.

All 65 pre-benchmark tests pass. Independent static checks find 144 distinct
cases, 108 survivors, and 60 H cases with viable final supplies; all 60
survive and meet the stated biomass criterion. The independently minimized
H supply threshold is 0.0208789322966, agreeing with the new implementation
within 6.4 × 10⁻¹¹.

## Does the settled criterion suffice?

Less than 1% biomass variation over 20 kyr is an operational stability
criterion, not a general proof of equilibrium. It can miss climate or trait
drift and cannot exclude longer transients. In the current experiments,
additional checks support the settlement interpretation.

Six archived survivor series have quiet climate and mean optimum as well as
biomass. Three informative unarchived survivors were independently rerun:

| Constraint | T₀ (K) | Final potential | m | Count interval (yr) |
|---|---:|---:|---:|---:|
| H | 265 | 0.03 | 10⁻⁸ | 100 |
| H | 283 | 0.02 | 10⁻⁶ | 30 |
| U | 265 | 0.02 | 10⁻⁸ | 30 |

Across the last 20 kyr of these reruns:

- Maximum temperature range: 5.55 × 10⁻⁵ K.
- Maximum relative biomass range: 2.24 × 10⁻⁶.
- Maximum L1 change in normalized strain composition: 5.28 × 10⁻⁹.
- An additional 20 kyr changes temperature by at most 1.43 × 10⁻⁵ K.
- A one-count post-removal map changes total biomass by at most
  2.02 × 10⁻⁷ relative, and composition by 2.52 × 10⁻¹² in L1.

Small mutation/removal turnover continues within each count cycle: discarded
biomass reaches about 6.52 × 10⁻⁶ of the community per count. Thus describe
these as **settled censused regimes**, rather than exact stationary solutions
of the uninterrupted ODE. There is no hidden-drift counterexample in these
checks. Adding climate and composition diagnostics to routine output would
make future settlement claims easier to assess; no universal threshold is
introduced by this review.

## Remaining metadata defect

The vertex flag now catches the genuine vertex at zero thermal derivative,
but finite-difference cancellation falsely flags some smooth segments.
For floor 289 K with n = 0.2, a fresh equilibrium at r = 0.2115942945374
has numerical slopes −45.78265589 and −45.78259905; their tiny mismatch
sets `at_vertex=True` despite the nearest source vertex being 0.00507 away.
One fresh scan finds 19 false flags; the count depends on root rounding.
The committed CSV records false for these cases, so this metadata is not
reliably regenerated. Sensitivity values and the survival conclusions are
unaffected. Use exact source-segment geometry for vertex detection and
one-sided slopes, rather than adjusting the noise tolerance.

## Reproduce and scope the conclusion

```sh
uv run python models/haze_world/review/check_revision.py models/haze_world/review/revision_check --runs
```

The review outputs include a [static audit](revision_check/static.json),
three full-state survivor summaries and snapshots, and an
[archived-series check](revision_check/available_series_audit.json).
The additional runs test selected survivors; they are not reruns of every
trajectory in the grid. “Adaptation only protects” should remain a statement
about survival in this experiment, rather than a general evolutionary law.
The uptake reconstruction remains a separate benchmark until its source
normalization and cessation thresholds are resolved.
