# Two nonspatial dormancy cycle candidates survive cross-solver checks

Codex, 11 November 2026. Independent Radau continuations reproduce the
recurrent climates in two no-refuge runs. These trajectories have one active
habitat, zero dispersal and no immigration. Neither continuation invokes a
census removal, chart restart or positive-dense extension. This establishes
that the observed recurrence does not require spatial refuges or the new
interpolation regularization.

Each control starts from its exact recorded year-80,000 physical input and
continues for 2,000 years with the original one-cell/ten-year census. Native
clock time is preserved. Radau uses `rtol=2e-9` and maximum step one year,
against the original solver's `2e-8` and ten years. Annual observations come
only from accepted flow; official census states replace any corresponding
interior observation. No seed, clipping or physical stock reset is introduced.

| Case | Active loss per hour | Dormant-loss fraction | Annual temperature range | Period | Maximum common-time temperature difference |
|---|---:|---:|---:|---:|---:|
| 0024 | 0.001 | 0.003 | 0.330701 K | 140.431 yr | `1.30e-7 K` |
| 0126 | 0.002 | 0.001 | 0.202474 K | 130.614 yr | `2.10e-7 K` |

The controls complete in 42.29 and 42.50 seconds respectively. Their sampled
minimum global guild counts exceed `10^24.5` cells, and the original late
windows have no removals. They preserve both communities, rather than
recovering a guild from a fractional-cell tail. There is no finite-stage-log
mask loss during physical initialization; coordinate round-trip differences
are at most `1.95e-16` relative. Both controls have zero native failures,
positivity refinements, stage promotions/conditionings or chemical maps.

The annual extrema and period estimates improve on the original ten-year
sampling. Resampling the controls at the original observation times reproduces
the original envelopes and fitted periods. The common-time temperature
comparisons in the table therefore measure numerical agreement directly,
without confusing sampling cadence with a changed oscillation.

## Local equilibria and interpretation

Direct mixed-root solves have scaled residuals below `3e-15`. Their refined
physical spectra are locally stable:

| Case | Mixed-root temperature | Leading real part |
|---|---:|---:|
| 0024 | 281.534823 K | `-2.0602e-4 /yr` |
| 0126 | 286.475415 K | `-1.0727e-4 /yr` |

Four finite-difference scales agree. A separate block check gives the same
leading pair: at the exact mixed root, active growth is zero and stationary
dormant stocks are zero; cubic switching has zero first derivative. The
linear spectrum therefore consists of the existing active five-state block
and two negative dormant-loss modes. Inactive forced-zero habitat axes are
excluded. The root lies away from the known climate and kinetic corners.

The temperature averaged over complete sampled cycles differs from the mixed
root by only 0.00028 K in case 0024 and 0.00074 K in case 0126. Regulation near
the mixed-community temperature can therefore coexist with a recurrent
climate rather than a constant one in these runs.

The original late windows have stable envelopes; the independent precision
continuations preserve them. That supports a **continuous, nonspatial cycle
candidate** at both reference and higher turnover. It does not prove an
asymptotic periodic orbit, its Floquet stability, a Hopf bifurcation, basin
sizes or global uniqueness. The stable local roots and finite recurrence are
separate findings. Every original `unsettled` label remains unchanged.

## Evidence and reproduction

[Comparison JSON](dormancy126_cycle_comparison.json) records the source and
receipt hashes, envelopes, counts, restart diagnostics and root spectra.
Per-case JSON files retain initialization masks and detailed provenance:
[0024](dormancy126_cycle_0024.json), [0126](dormancy126_cycle_0126.json).
Accepted annual arrays and full metadata remain under the ignored raw paths
named there. The original 0126 checker bytes are archived with its control;
a subsequent read-only dependency-guard correction permits comparison with
the older 0024 numerical protocol and changes no model or solver operation.

```sh
uv run python models/haze_world/review/dormancy126_cycle_check.py --case 0126
uv run python models/haze_world/review/dormancy126_cycle_check.py --case 0024
uv run python models/haze_world/review/dormancy126_cycle_summary.py
```

These are bounded 180-second controls using the frozen `09be346c` Radau helper.
The separate ordinary native failure of Radau case 0010 remains documented in
[the numerical review](dormancy-radau-review-2026-11-11.md); these successful
continuations do not imply that the backend resolves every original start.
