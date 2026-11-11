# Mathematical scope of the dormancy interpretations

Codex, 11 November 2026. Bounded audit of the new interpretations in
[Claude's review](turnover-dormancy-claude-review-2026-11-11.md), using the
existing equations and recorded diagnostics. No physical trajectory or
earlier assessment is changed. The [checker](dormancy-interpretation-math-check-2026-11-11.py)
and [receipt](dormancy-interpretation-math-check-2026-11-11.json) retain the
algebraic controls, source hashes and numerical values.

## The seed-bank formula is conditional

For an isolated nonreproducing bank, constant dormant mortality gives

```text
N_end = N0 exp(-epsilon L tau)
epsilon* = ln(N0 / N50) / (L tau)
t_half / tau = ln(2) / ln(N0 / N50).
```

Here `N0` must be the viable bank entering the interval, and `N50` must
include the subsequent chance that a surviving dormant cell wakes and leaves
living descendants. The formula assumes negligible continued entry and
waking during the interval, a specified environment and recovery law, and
an approximately fixed suppression duration. It is generally implicit if
`N0`, `N50` or `tau` depends on epsilon.

The four measured brackets are consistent with the review's approximate
formula: measured epsilon divided by the quoted prediction lies within
0.992–1.167. They do not determine exact equality. The review's coefficient
`6.2 years`, with `L=8.766/year`, implies `ln(N0/N50)=54.3492`, giving a
half-life of 1.275% of the suppression time. The 1.3% coefficient is therefore
specific to that population ratio. The original prescribed f=0.5 methanogen
lower bound was 0.0025; the review's refined 0.00247 approximation does not
erase the recorded refutation of the literal earlier bound.

Dormant cells have no direct uptake or methane source in this model, but
this does not make the coupled climate path invariant. Entry removes active
consumers; waking returns them. Summing the actual bank equations gives

```text
dZ_global/dt = sum(w sigma X) - sum(w rho Z) - epsilon L Z_global.
```

Exchange cancels in this global balance, but entry and waking do not. The
checker demonstrates the indirect dependency in a synthetic positive state
within the measured temperature range: doubling dormant methanogens leaves
the instantaneous methane source unchanged, while waking changes the active
methanogen derivative by 0.008766 gDW/L/year and changes the subsequent
methane-source derivative. This establishes a dependency, not a measured
effect on the four threshold paths. Treat their close agreement as a useful
approximation to be checked against each regime, rather than a theorem that
the reference suppression duration is always unchanged.

## The integrated scalar rule has a boundary term

For a single-type linear birth–death process in a fixed recorded environment,
let the expected population satisfy `Nbar'=(b-delta)Nbar`. The exact
single-cell survival probability to a finite terminal time obeys

```text
1/u(t0,T) = 1 + integral[t0,T] delta(t) Nbar(t0)/Nbar(t) dt.
```

Under the repository's Poisson initial-count convention, the minimum
population corresponding to half survival is therefore

```text
N50 = ln(2) [Nmin/Nbar(t0) + integral delta(t) Nmin/Nbar(t) dt].
```

For constant mortality and a negligible entry-boundary term this becomes
`N50 ~= ln(2) delta W_int`. A Gaussian population shape is a further
approximation to `W_int`; Gaussian shape is unnecessary for the integrated
scalar identity. Fixed integer initial counts require the corresponding
independent-lineage formula, which agrees with the Poisson approximation
when individual survival is small.

The existing [Gaussian counterexample](check_turnover_gaussian.json) correctly
retains the boundary term and time-dependent weighted death. Its integrated
scalar diagnostic is 105.6363 cells, against the multitype value 105.6468
cells, a relative difference of 0.00993%. Its integrated width is 57.9515
years rather than the Gaussian width of 36.5208 years. This close empirical
agreement does not make the scalar formula a general identity for migrating
or active/dormant types: type composition and future reproductive values can
matter separately from total population and mean mortality.

## One-cycle risk does not establish million-cycle persistence

The case-0012 calculation is a plausible small *conditional one-cycle*
hazard estimate, using an approximate scalar width and death rate. It has
not established a uniformly small extinction probability after every
possible previous stochastic history.

The checker gives a scalar counterexample to that inference. Start with a
Poisson mean of 14,500 cells, let birth and death both be 6.6/year for 15
years of each 443-year cycle, and let neither event occur between those
intervals. Do not restore population size. Its deterministic mean stays
14,500 throughout. After `n` cycles,

```text
u_n = 1 / (1 + 99 n)
P_extinct(n) = exp(-14500 u_n).
```

The first-cycle extinction probability is about `1.06e-63`, yet extinction
probability is 0.231 after 100 cycles and 0.999854 after a million. Half
survival occurs at about 211 cycles. Fixed integer initial counts give the
same qualitative result. This counterexample is not a prediction for the
coupled case-0012 ecosystem.

If ecological feedback genuinely restores the same viable population and
composition after each surviving cycle, and the one-cycle hazard is
uniformly bounded by the first-cycle value, a million-cycle union bound is
indeed below `1.1e-57` in the example. Such restoration may occur in the
full ecological model, but the current exogenous-environment branching
calculation does not verify it. Report the one-cycle estimate with this
condition. A claim about millions of cycles would need a justified
regeneration argument or a coupled demographic calculation; it is not needed
to close the present deterministic cycle tests.

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache \
MPLCONFIGDIR=/tmp/terra-prisca-mpl \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
uv run python models/haze_world/review/dormancy-interpretation-math-check-2026-11-11.py
```
