# Conversion-opening probability arithmetic

The opening bootstrap had two independently demonstrated numerical defects.
This repair changes its probability formulas and minimum Poisson-series
order, preserving the recorded rates, adaptive coarse/fine error criterion,
probability-domain checks and first-window interpretation.

The old source is `3e423ee451d46b1f5ec269047513751d109cb365b97d34b174898fce405f6405`
at commit `0455d15`. The repaired source is
`c754e3feac7baf81feb8bf2ffb353f488e06632586b06bb82f96c7969f6293df`.
The [checker](dormancy-opening-kernel-review-2026-11-11.py) retrieves and verifies
that historical source, then writes the [source-bound controls](dormancy-opening-kernel-review-2026-11-11.json).

## Leading paths

Absolute Poisson-tail truncation could stop before constructing a reachable
five-hop path in six types. Two half steps could then contain paths missing
from one coarse step. At still smaller durations both approximations could
omit the path and falsely agree.

In an affine six-type chain over `10^-10 yr`, the analytic log survival is
`-121.355156754806`. The old coarse and fine answers were both `-1000`.
The repaired coarse answer differs from the analytic value by `3.75e-11`;
the fine answer differs by `1.05e-12`.

Both constant and time-varying uniformization kernels now construct at least
`n-1` jump terms before applying the original absolute-tail stop. Every
reachable simple path needs at most that many jumps. This preserves its
leading term when representable; it does not turn the absolute-tail stop
into an entrywise relative-error bound. The adaptive coarse/fine check remains
necessary. Analytic tests cover constant and affine chains at durations
`10^-6`, `10^-8` and `10^-10 yr`.

## The survival-one boundary

The original scalar formula subtracted nearly equal logarithms. The conversion
mixture also evaluated a nearly unit stochastic row sum with `logsumexp`.
Both could return positive log survival through roundoff. A common-death
control whose exact log survival is `-8.223e-22` returned up to `+1.110e-16`.

The scalar map now evolves extinction odds `v = 1/u - 1`, which satisfy
`v' = death - (birth-death)*v`. Its positive affine solution is evaluated in
log coordinates and converted with `log u = -logaddexp(0, log v)`.
The conversion mixture uses normalized weighted extinction deficits near
survival one, and normalized log-sums for lower probabilities. These are
equivalent probability formulas chosen to retain small deficits and deep
tails. No clipping or acceptance epsilon is used. The tiny-death control
now agrees across types, and survival one is exact when death is zero.

## Actual-profile scope and verification

The old-source expanded rollup failed for cases `0006`, `0007`, `0062` and
`0063`. Its single 60-second diagnostic did not reach the eventual failure.
It captured a **resolved** six-attempt opening at `52230.007499 yr` in case
`0006`. Replaying those captured affine rate arrays after repair changes the
fine log probabilities by at most `1.78e-15` and retains the same normalized
error, `0.149052955`. The input report and physical-profile hashes are recorded
in the control JSON. This is no claim that the later failure has been
reproduced or that the expanded grid has already been rescored.

All 26 focused tests and all 42 related branching and turnover-survival tests
pass. Existing closed forms, forward no-birth controls, stiff conversion,
underflow-tail recovery and physical mean-rate checks remain covered.
An independent read-only review cleared the same source and test hashes,
checked the formulas and reachability floor, and reran all 26 focused tests.
Full expanded-grid rescoring under the new source is a separate completion
gate. No physical trajectories were regenerated for this repair.

```sh
uv run pytest -q tests/test_dormancy_branching.py tests/test_branching.py tests/test_turnover_survival.py
uv run python models/haze_world/review/dormancy-opening-kernel-review-2026-11-11.py
```
