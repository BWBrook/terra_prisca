# Review: temperature-buffered refuges

Claude (Opus 5.5), 10 November 2026. Review of Codex's buffered-refuge build
(`87103f7` to `85283e7`, [buffered-refuges.md](../buffered-refuges.md)). New
evidence: [bottleneck_branching_pilot.py](bottleneck_branching_pilot.py)
([output](bottleneck_branching_pilot.json)). It reruns six warm-only
invasions through Codex's integrator with no removal floor and 1-year
sampling. It then computes exact survival probabilities for the rare guild
as a birth–death process in each trajectory's environment.

**Verdict.** I accept the build, the reporting and Codex's verdicts on B1 to
B5. Both refuges give two-way rescue to one mixed community, which is the
result the previous geometry could not test. The one-refuge failures are
more interesting than my B3 predicted. The finite-population question they
raise has a quantitative answer in the pilot, and the full test is specified
in [bottleneck-test-spec.md](../bottleneck-test-spec.md).

## 1. Accepted results

- **B1 and B2.** All 12 key runs keep both guilds. Opposing histories match in
  stocks, methane and occupancy at 281.535 K. The previous two-habitat model
  could not reach this paired test.
- **B3 is refuted twice, and both refutations are correct.** At `f=0.9`, the
  acetogen-only start is already hazy at 273.5 K, so no greenhouse peak lies on
  the path and my peak argument does not apply. At `f=0`, the warm-only layout
  loses the invader to its own overshoot, as described below.
- **B4.** Both refuges rescue down to `d=10⁻⁹/yr` and still at 1/yr. The
  100/yr check shows the predicted failure from homogenization. Codex's
  operator eigenvalues (−3.47 and −11.03/yr against local refuge growth of
  +0.81 and +9.54/yr) are the right diagnostic.
- **B5.** Methanogens persist at `f=0.9` on 1.8–2.2% of catabolic H₂, with a
  matched climate contrast of 0.029–0.035 K. Codex correctly reports this as an
  ecological result with no climate consequence.
- **Numbers checked.** My rerun of `main_0010` reaches its minimum of
  10^−1.06 cells at 1,344 years. That matches Codex's counterfactual (0.088
  cells at 1,344.5 years). The `d=10⁻³/yr` minimum is 2.3×10¹² cells,
  consistent with Codex's 2.4×10¹².

## 2. The overshoot: the refuge for the resident protects the invader through climate

In the warm-only `f=0` invasion of acetogens into a methanogen world,
methane falls and the planet warms past the 281.535 K switch. Methanogens
must regrow in the bulk before methane production can pull the climate back.
They regrow from a floor that warm-refuge immigrants maintain, roughly
proportional to `d`. The lower that floor, the later methanogens recover, the
further the climate overshoots, and the longer acetogens decline in a
methanogen-controlled bulk. The uncensored minima show this cleanly:

| `d` (1/yr) | Peak global T (K) | Acetogen minimum (cells) | Year |
|---|---:|---:|---:|
| 10⁻⁹ | 282.50 | 10^−14.25 | 1,401 |
| 10⁻⁶ | 282.32 | 10^−1.06 | 1,344 |
| 10⁻³ | 282.10 | 10^12.37 | 1,273 |

The logarithm of the minimum is linear in `log d`, with slopes of 4.40 and
4.48 per decade. Exchange of the **resident** therefore protects the
**invader**: it damps the climate oscillation the invader itself started.
The reported census minima for lost runs are frozen at the census that
removed the guild. They are not bottleneck depths: `main_0008` records
10^−0.93 at its removal, but its uncensored trajectory goes 13 orders lower.

At `f=0.5` the same layout keeps acetogens at 10^12.5 cells or more at every
tested `d`. Acetate-derived methane slows the methane decline, the overshoot
peaks at 282.11 K, and the bottleneck is shallow.

## 3. A one-cell floor is the wrong extinction criterion, but the error is small here

A deterministic minimum of one cell does not separate survival from loss. Near
the minimum the guild's birth and death rates are each about 8.77/yr, set by
the model's 10⁻³ h⁻¹ loss term, while net growth passes through zero. For a
linear birth–death process with time-varying rates, the probability that a
population survives a bottleneck is `1 − exp(−Λ)`, with

    Λ ≈ 1 / ∫ δ(t)/N̄(t) dt ≈ N_min sqrt(κ/2π) / δ,

where `N̄` is the deterministic trajectory and `κ` the curvature of `ln N̄`
at its minimum. The pilot solves the exact multitype backward equation; the
Gaussian form agrees to three digits. Every bottleneck in the pilot has the
same width, `sqrt(2π/κ) = 37.9` years. This gives:

- **50% survival needs about 230 cells at the minimum,** not one cell. The
  one-cell floor is optimistic by a factor of 230.
- **`main_0010` survives with probability 2.7×10⁻⁴.** Reversing the loss would
  need global cell counts 2,600 times larger than the model assumes. At
  `d=10⁻⁹` it would need 4×10¹⁶ times larger. The `d=10⁻³` survival is
  certain, with 7×10⁹ expected surviving lineages.
- **The criterion matters little for where the transition lies.** Because
  depth scales roughly as `d^4.4`, replacing the one-cell floor with 50%
  survival moves the critical exchange rate from about 1.7×10⁻⁶ to about
  6×10⁻⁶/yr, a factor of about 3.5. A tenfold error in the global cell count
  moves it by a factor of 1.7.

The warm-only `f=0` result is therefore a statement about exchange, not about
census rules. Acetogens are lost if bulk–refuge exchange is below about
10⁻⁵/yr and kept above it. Whether early Earth's exchange rate sat above or
below that value is a question the model cannot answer.

## 4. The largest open dependence is turnover, not census rules

The loss rate `L = 10⁻³ h⁻¹` (turnover about 42 days) sets three things at
once:

- the demographic noise in §3, since birth and death are each about `L` at a
  bottleneck;
- the speed of competitive exclusion, and so every timescale ratio in this
  family of models;
- **the switch itself.** With the reference physiology, `T_sw` is 277.15 K at
  `L = 3×10⁻⁴ h⁻¹`, 281.53 K at 10⁻³ and 291.92 K at 3×10⁻³. Below about
  3×10⁻⁴ h⁻¹ there is no switch: methanogens win at every temperature.

[two-guilds.md](../two-guilds.md) records `L` as an assumed grid, not a measured
sediment turnover, and the stage 3 scoping already found that turnover decides
cold routing. The buffered refuges at 278 and 286 K straddle the switch only
near `L = 10⁻³ h⁻¹`. Every refuge result is conditional on that value. Natural
energy-limited communities can turn over far more slowly, and dormant cells
below their H₂ threshold need not die at the active loss rate. Both effects
would make bottlenecks shallower and slower. I recommend a turnover stage
after the bottleneck test, with refuges set relative to `T_sw(L)`, and a named
dormancy variant. Neither belongs in the bottleneck test itself.

## 5. Small corrections

- The status line on [buffered-refuges.md](../buffered-refuges.md) can now
  read "reviewed". The limitations paragraph should add the turnover dependence
  in §4.
- The page's B3 discussion should state that the overshoot depth depends
  log-linearly on exchange (§2), with a pointer to the pilot.
