# Issue 3: Codex review of the checks and applied changes

Codex (GPT-6), 16 November 2026. Reviews `f508dfa`, C65–C66,
`d34a796` and the decision record `0759404`, at working commit `4c2b138`.
Three bounded independent reviews covered dynamics, persistence evidence and
figure provenance; I checked the decisive algebra, counts, applied text and
rendered figure. No new grid or research stage was run.

**Decision:** accept the numerical assembly and persistence results. Make the
scope corrections below before closing Issue 3. Barry's adopted main message
can stay; no new decision or experiment is needed for these corrections.

## What passes

- `Speeded` correctly scales derivative row 4 and the corresponding Jacobian
  row, including its temperature dependence. The parent check's finite
  differences agree within 1.3 × 10⁻⁷ normalized error at τ = 0 and
  7.6 × 10⁻⁹ at τ = 3 years. Its construction preserves steady states.
- The stored response-speed and lifeless-start classifications agree with
  the reported tables. Independent 60-year checks with either balanced or
  exactly zero initial acetate remove acetogens at year 60 in all three
  lifeless cases; removal temperatures differ by less than 4 × 10⁻⁹ K.
  Acetate initialization does not explain the outcome. Short checks of both
  rapidly responding acetogen invasions retain more than 10²⁴ resident
  cells, so their successful assembly is not recovery from subcell fractions
  between censuses.
- C09's twelve key buffered-refuge runs form six matching opposite-history
  pairs. Their temperatures span 281.534822764–281.534901712 K; the largest
  relative stock difference is 3.66 × 10⁻⁶. This supports the selected
  comparison, not every buffered-refuge configuration.
- C66's positive-immigration endpoints give 36/36 materially active mixtures
  at each of f = 0 and 0.5, with no operational immigration-supported sink.
  Independent flux recalculation agrees with stored shares within
  2.11 × 10⁻¹⁰; the minimum catabolic share is 24.57%. These are stationary
  deterministic mean-immigration results, not Poisson rescue probabilities.
- Figure 4c has the correct four identities, native hashes and endpoints:
  281.534823 K from either history with both refuges, versus 294.402630 and
  273.516845 K without them. Payloads and receipts match; the twelve key
  runs' source identities were checked against their frozen source hashes.
  The figure is legible, and a default rebuild needs no ignored raw archive.
- The four targeted paper/ESM/table/figure tests pass. The claims checker
  reports 66 claims, 35 cited, zero errors and 26 uncited-claim warnings.
  Those checks do not resolve the interpretation problems below.

## 1. Describe a response-speed experiment, not a physical lifetime test

The controlled intervention is useful, but it multiplies **every methane
source as well as removal** by s, leaving donor consumption and acetate
production unchanged. This isolates methane response speed while preserving
the reference equilibria. It is not a physical lifetime change at fixed
hydrogen supply.

There is a simple discriminating bound. At the fixed reference supply, even
conversion of all incoming hydrogen to methane gives a maximum sustained
source, including abiotic methane, of 3.00544 × 10⁻⁵ ratio yr⁻¹. A genuine
10-year first-order lifetime therefore allows at most r = 0.000300544 at
steady state; a 1,000-year lifetime allows at most r = 0.0300544. Both are
below the reference mixture's r = 0.195107. A physical 10-year lifetime
cannot sustain the claimed reference mixture at these unchanged supplies.

Use **fixed-equilibrium methane response-speed test**, or equivalent plain
wording, in §3.6, S10's heading/table labels, C65 and the audit. S10 already
discloses the source rescaling correctly; its interpretation must follow it.
Remove the audit's “modern-like 10-year lifetime would therefore assemble”
inference. Also remove its claim of assembly robustness across the sourced
6–19 kyr range: this grid tests response coefficients of 10,000, 1,000, 100
and 10 years. The earlier physical 6/10/19 kyr experiment tests recomputed
equilibria and local stability, not invasion assembly.

No physical-lifetime sweep is requested. The experiment already answers the
intended timescale question after this relabelling.

## 2. Scope the longer assembly claim to the tested reference starts

The abstract (lines 33–38), §4.5 (lines 529–537), and C65's opening claim
are too broad. The new checks themselves contain two closed, uniform-habitat
assemblies after methane response is accelerated. C66 also assembles the
mixture in a uniform habitat supplied with immigrants. “In one uniform
habitat ... never assembled” needs the **closed reference runs** or
**reference methane response and no immigration** qualification.

For example, the longer discussion can say: “In the closed reference runs,
the controlling community never formed; the losing group disappeared before
the climate caught up.” Then give the demonstrated refuge and immigration
routes. Keep Barry's adopted short main message unchanged. Persistence can
also mean surviving the transient in the same habitat; it need not always
mean being stored elsewhere.

The lifeless result concerns the tested 283.2-K bridge and f = 0, 0.5 and
0.9. Replace “at every f” in §3.6 with the tested values or an explicit
“all three tested fractions”. Remove S10's and the audit's inference that a
colder bridge merely reverses the winner with the same outcome. No such
starts were run. Near T*, exclusion becomes arbitrarily slow: at T* both
guilds have the same R* (22.4863 Pa); 0.001 K below it, the losing guild's
decay rate is only about 5.35 × 10⁻⁴ yr⁻¹. Rapid exclusion before methane
responds therefore cannot be presumed on either side of the switch.

This narrows the tested basin of assembly failure; it does not undermine the
24 reference invasions or request a new basin survey.

## 3. Preserve the already-supported climate-tracking results

S10's final climate-tracking sentence (line 422) says these designs do not
test assembly. That erases part of supported C08. The existing comparison
table has **nine matching coexisting f = 0.9 pairs**, seven with positive
exchange. There are also one-direction coexisting endpoints at f = 0/0.5.
Coexistence remains distinct from climate regulation.

Say instead that **paired assembly of the regulating mixture at f = 0/0.5
is domain-limited in the tested mean-preserving tracking geometry**. Keep the
higher-recycling coexistence counterexamples. The main text can retain its
shorter “no comparable test” statement if it explicitly refers to that
lower-recycling, paired regulating-mixture comparison.

The 38 protected completions establish retention of the direction-labelled
resident, not 38 assembled mixtures: six have single-acetogen endpoints.
The current sentence “kept it” is correct. Do not turn that recount into a
general sufficiency claim that any protection guarantees assembly.

## Other corrections and figure fidelity

- §4.6 line 561 and S10 line 424 say all assembly runs use instantaneous
  temperature. The 24 reference invasions include τ = 3 and 30 years.
  Scope this condition to the new bounded checks and the refuge/immigration
  checks. S6 line 289 also needs updating: refuge outcomes are now reported
  in S10 and Figure 4c.
- S10's f = 0.9 trace-immigration statement applies only to the highest
  tested relative rate, 100 yr⁻¹: 12/12 retain trace methanogens. The other
  24 positive-immigration endpoints have zero methanogens after census.
  For f = 0/0.5, use 281.285–281.569 K; 281.29 results from double rounding.
  Preserve C66's existing deterministic-mean and unrepresented-reservoir
  qualifications, and its distinction between cells yr⁻¹ and rate relative
  to the removal floor.
- The 19 new trajectories are completed 100-kyr runs, not a blanket set of
  certified stationary endpoints. The reference f = 0 acetogen-invasion run
  has a 0.0222-K final-window span. Its absorbing absence already proves
  assembly failure, so no longer run is needed for that claim.
- Figure 4c's 100 retained points per case are exact native values, but
  logarithmic thinning misses extrema; the maximum deviation between the
  plotted interpolation and native trace is about 0.63 K. Retain turning
  points or use a bounded-error simplification when refreshing panel c.
  The endpoint result is unaffected. Its caption should explicitly say
  fixed products. Source descriptions should include gzipped JSON, not
  only NPZ census archives.
- The audit's stated default-step certificate failure during the lifeless
  initial bloom was not reproduced with the current balanced-acetate f = 0.5
  census initialization through year 60. Keep the conservative one-year
  step limit, but identify any retained failure claim by its actual
  configuration or mark it as a historical observation.

## Reproduction and hand-off

The committed bounded check records current input hashes and recomputes the
source bound, scaled Jacobians and decisive persistence counts:

```sh
uv run python docs/audits/probe-issue3-codex-check-2026-11-16.py --output /tmp/terra-issue3-codex.json
uv run pytest -q tests/test_paper_esm.py tests/test_paper_table_s1.py tests/test_paper_transient_figures.py
uv run python tools/claims.py check models/haze_world/synthesis/claims.csv models/haze_world/paper/03c-full-draft.md models/haze_world/paper/esm/esm.md
```

No manuscript, production model, figure or original evidence receipt was
changed in this review. Claude can reconcile the labels and scope, preserve
the adopted message, and refresh the figure export if addressing its
transient fidelity. The existing data suffice; Issue 3 needs no new stage.
