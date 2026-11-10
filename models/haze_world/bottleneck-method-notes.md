# Bottleneck test: implementation qualifications

Codex (GPT-6), 10 November 2026. These qualifications precede the E1/E2
results and retain the original [specification](bottleneck-test-spec.md).

- The backward equation gives survival to a stated end time in a recorded,
  deterministic environment. It is not the exact stochastic, climate-coupled
  ecosystem. Birth minus death must recover the physical growth rate.
- `1-exp(-Λ)` is exact for independent Poisson starting counts. Known integer
  counts instead give `1-product((1-u_j)**N_j)`. Both conventions are checked;
  the distinction is small when individual-lineage survival is small.
- No return above a threshold by a finite horizon does not imply zero
  survival probability. Such a trajectory is reported as unresolved unless
  sustained late decline and the endpoint's invasion operator support
  exclusion. An extremely small expected count supplies a finite-horizon
  upper bound, rather than an invented exact zero probability.
- Global rarity and local habitat loss are different. The planned selection
  retains every case with any local removal, but probabilities describe a
  whole guild. The rare-guild uptake fraction is checked locally and globally
  in each probability window; failure is visible, not silently accepted.
- Multiple rare excursions receive separate windows. Their probabilities
  describe survival conditional on rejoining the prescribed large-population
  path between windows; they do not reproduce correlated, climate-coupled
  demographic histories.
- Each guild's probability is conditional on the uncensored community path.
  If another guild would already have disappeared, its missing resource and
  methane feedback can invalidate the later environment. Per-guild values
  must not be multiplied into a joint stochastic community or climate forecast.
- The specified split into cell birth and death is an event-model assumption
  beyond net biomass growth. In particular, representing maintenance deficits
  as cell death differs from shrinkage or dormancy. Probability classes remain
  conditional on this split and the fixed turnover rate.
- The E2 one-cell floor diagnostics apply after the fact to the uncensored
  **global** count, as specified. They are not reruns of the earlier local
  removal model and do not establish its counterfactual final climate.
- Turnover and dormancy remain outside this test. The accepted 278/286 K
  refuges straddle the switch only around the reference loss rate; numerical
  robustness to counting cannot establish robustness to turnover physiology.
