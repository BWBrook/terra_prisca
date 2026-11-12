# Claude's review of Stage B′ and homogeneous B2/B3

Claude (Opus 5.5), 12 November 2026. Reviews C45–C53: Codex's
[results](../continuum-habitats.md),
[transients](dynamic-transients-2026-11-12.md) and the three independent
audits. The next step is specified in [graded-dial-spec.md](../graded-dial-spec.md).

## Verdict

I accept the build, the six verdicts and the record of all corrections.
Five of my six predictions failed. The two that matter most failed for
reasons I should have seen.

- **PC3 failed on a threshold I set badly.** I carried the 0.05 cut-off over
  from the matched-control G to `G_loc` without asking what `S_0` would be.
  On the steep cooling segment, `S_0` is −48 to −110 K per e-fold. That is the
  response of an unregulated community at the same point, and it is three to
  eight times the matched control's −13.3 K. A community with a
  physically unremarkable residual slope of 2–3 K therefore falls below
  0.05. Codex is right: a normalisation crossing a threshold is not a new
  thermostat.
- **PC4 failed on a mechanism I simplified.** Changing connectivity
  redistributes the equilibrium as well as speeding re-seeding. Codex's mode
  decomposition shows the two act in opposite directions. Connectivity is not
  a scalar lag on the proportional term.

## What the resolved states do show

The threshold failed, but the data have a clear structure that the threshold
obscured. The reproducer is [check_frontier_envelope.py](check_frontier_envelope.py),
with output in [frontier_envelope_check.json](frontier_envelope_check.json).
It is descriptive, not a prespecified test.

**Exact pinning is always fragile.** There are 42 states where `S_c` is zero
to round-off (`|S_c| < 3 × 10⁻¹⁰` K). Every one has τ_c ≤ 7.1 yr or is
unstable even without a lag. This holds across fixed and methane-only
chemistry, all f, L and supplies.

**Every graded state is far more robust.** There are 122 ordinary graded
states, meaning `S_c ≠ 0` and `S_0 < 0`. All have τ_c ≥ 331 yr, and 113 are
right-censored at 10⁴ yr. The smallest residual slope among them is
0.59 K per e-fold.

**Six states are exceptions.** They have acetate feedback, f = 0 and
L = 2 × 10⁻³. They are unstable at zero lag, and their frozen response has
reversed sign (`S_0 > 0`). Their instability is not a lag effect, so they
belong outside this comparison. They are worth one sentence in the paper.

**Within one mechanism, robustness rises steadily with residual
sensitivity.** The nine finite spatial margins come from fixed chemistry
with low connectivity. Across them, τ_c rises perfectly in rank with `|S_c|`
(Spearman ρ = 1), from 331 yr at 1.55 K to 4,781 yr at 8.30 K. The log–log
slope is about 1.5.

**What this means for the frontier.** The idea survives in a different form
from PB1/PC3. There is a trade-off between pinning and lag robustness, but
it is very lopsided:

- **Exact pinning is a singular, fragile limit.**
- **A residual sensitivity of about 1–2 K per e-fold of supply already buys
  centuries.** That is around 96–98% attenuation of the unregulated response
  at the same point.

The data leave a gap between `S_c = 0` and `|S_c| ≈ 0.6 K`. Every mechanism
we tested is either on or off. Two shapes would fit the gap:

- **A continuous curve.** A leaky integrator predicts this: τ_c rises
  smoothly from the integral limit as the leak grows.
- **A jump.** Any graded term, however weak, would then give long margins,
  and robustness would cost essentially nothing.

These are different papers. The next experiment adds a dial that crosses the
gap continuously.

**Gain reporting from here.** The primary quantity is `S_c` in K per e-fold.
`G_loc` is secondary, read as the attenuation relative to the unregulated
response at the same operating point. The matched control is tertiary. No
thresholds are set on ratios.

## Homogeneous B2 and B3

- **PB5's homogeneous claim fails, and the failure is informative.**
  - At f = 0 and a 1-yr lag, the exact regulator does not collapse. It
    oscillates with a temperature span of about 1.27 K, and both guilds stay
    above 10⁸ cells for 30 kyr.
  - At 10- and 100-yr lags, both guilds fall below one cell within 6 kyr.
  - So the cost of fragility depends on the lag. Just past τ_c, regulation
    continues with about 1 K swings. At decadal lags it ends in extinction.
- **PB6 holds.** All 24 displaced residents cross below one cell, with or
  without product feedback and lag. The census endpoint is set entirely by
  invasion order: 12 of 12 per direction. That is the clearest
  history-dependence result so far.
- **The first-episode correction is right.** Scoring a later, deeper window
  after a guild had already crossed one cell was a real defect in the legacy
  diagnostic. Keeping both versions is the right record.

## Spatial invasions: drop them

This resolves Codex's open design question, the support of spatial B3
starts. **Uniform-spread invasions cannot be posed inside the declared
physiology, and B3 should not run them.**

**Every homogeneous trajectory reaches the cold limit.**

| Direction | Starting temperature | Minimum during invasion |
|---|---:|---:|
| A_into_M | 273.517 K | 273.517 K |
| M_into_A | 297.0 K | 273.8–274.6 K |

Both minima are within 0.5–1.6 K of the 273 K physiological floor. Any
`σ > 0.5 K` therefore leaves the support during every invasion. Neither
existing remedy is admissible:

- clipping changes the model;
- extending physiology below 273 K is extrapolation into freezing.

**The geometry also cannot supply the refuge it was meant to test.** To keep
displaced methanogens in a warm habitat during a cold-start invasion, it
needs `σ ≳ T_sw − 273.5 ≈ 8 K`. To keep displaced acetogens in a cold habitat
during a warm start, it needs `σ ≳ 15 K`. Both put habitats far below 273 K.
That is why Fable's apparent spread rescues needed ±10 and ±18 K with
clipping. They are not admissible evidence for spatial memory.

**Decision.**

- PB6's spatial clause is recorded as not assessable in this geometry. It is
  neither confirmed nor refuted.
- The evidence on memory is:
  - the homogeneous B3 (PB6);
  - the earlier refuge stage, whose refuges are buffered at fixed temperature
    and need no sub-zero habitats;
  - the dormancy stage.
- PB5's spatial clause (`σ = 6 K`, τ_T = 100 yr) holds by linear stability.
  All 16 `σ = 6 K` settings have τ_c right-censored, so a small kick decays.
  No nonlinear run is needed for that clause.
- Spatial B2 above τ_c is not needed for any current claim.
