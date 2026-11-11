# X12: dense roots and nonfinite precursor output

Codex, 11 November 2026. External-review Stage A, against the reviewed
`haze-world-review-1` source epoch. The
[check script](external-review-numerics-2026-11-11.py) and
[receipt](external-review-numerics-2026-11-11.json) retain source and input
hashes. This is a numerical repair, without a change to the physical equations.

## Defects and repairs

Both `habitat_integration` and `refuge_integration` accepted a companion-matrix
polynomial root solely from its imaginary part and interval. The review's
near-linear example has a quadratic coefficient about 5e-18: an alleged root
at zero can have a residual about 0.089. Depending on the numerical platform,
this can falsely report a physiological-domain exit at the beginning of an
accepted step.

Both integrations now use `dense_roots.real_roots`: it maps the requested
interval to [-1, 1], normalizes coefficients, removes trailing terms below
round-off on that interval, checks root residuals in both coordinate systems,
and independently brackets a sign change if the companion solve yields no
valid candidate. The domain helper separately checks that an interior exit
meets a physiological boundary; an exit inferred from an unpartitioned
interval starting strictly inside the domain raises an error. Dense-minimum
callers, including dormancy, inherit the same maintained root helper.
The experiment identity functions include its source hash.

`methane_budget.integrate_full` could overflow when exponentiating an unsafe
log-biomass trial, then accept nonfinite output despite a successful solver
status. It now uses an exact softplus coordinate for positive biomass:
`B = s log(1 + exp(z))`, evaluated with `logaddexp`, with numerical scale
`s = 1e-6`. It is logarithmic near zero and linear for large positive trials;
the transformed derivative preserves the physical equations. Exactly absent
biomass remains absent. Every accepted internal output and the final physical
state must be finite. This introduces no extinction floor, clipping of positive
biomass or automatic reseeding.

The original three exposure tests pass on this machine. New regressions inject
the false companion root, test a bounded tangency and interval scaling, reject
an exit without a valid boundary, and reject accepted NaNs independently of
solver status. These are platform-independent checks, rather than reliance on
the reviewer's failure recurring under this machine's round-off.

## Targeted requalification

The accepted raw manifest is verified by SHA-256 before examining its exits.
Neither accepted archives nor their historical producer sources were changed.

| Check | Result | Scope |
|---|---|---|
| All 103 stored domain exits: 69 main, 34 subsets | Every returned methane ratio meets its stated boundary; largest residual 1.39e-17 | Rules out the demonstrated false-interior-exit signature in these records; does not prove the first crossing was found |
| Two representative exit tails, restarted at the preceding stored state and integrated with `max_step = 0.1 yr`, `rtol = 1e-10` | Both still exit; time changes -0.00144 yr and +0.00000167 yr; boundary residual zero | A bounded tail check, not a rerun of the complete preceding path |
| Headline warm-refuge, no-recycling, exchange 1e-6/yr bottleneck | A 2,000-year uncensored replay covers both recorded minima. Across 4,387 accepted intervals, old versus repaired minima evaluated on the **same** polynomials differ by at most 1.78e-15 in local log stock and exactly zero globally | Separates root evaluation from trajectory round-off |
| Same headline versus its archived trajectory | Acetogen minimum log stock changes by 7.4e-7; methanogen minimum is unchanged | No material change to the reported approximately 0.09-cell minimum; probabilities were not rescored in this check |
| Explicitly Linux-produced dormancy pilot, first 1,500 years | Across 9,064 accepted intervals, old/repaired local and global minima are identical; recorded methanogen minimum is reproduced, and acetogen removal still occurs at year 1,410 | Includes the recorded minimum and first loss, not the full 100,000-year trajectory |

The 103 domain-exit records and the headline bottleneck do **not** record their
producer operating system. Their host provenance is left unknown. The
dormancy pilot explicitly records Linux/x86_64; its replay here uses
macOS/arm64. Replays compare physical parameters before integration where the
complete original parameter record is available.

The original archives retain sampled states and extrema, but not all accepted
dense polynomials. Consequently this check cannot certify every historical
interior minimum or every first-crossing time. It establishes that the
demonstrated defect is repaired and that these boundary, bottleneck and Linux
controls retain their scientific classifications. An archive-wide claim would
require new trajectories; none is made here.

## Reproduce

From the repository root, with the named local raw inputs restored:

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache MPLCONFIGDIR=/tmp/terra-prisca-mpl \
  uv run python docs/audits/external-review-numerics-2026-11-11.py \
  --output /tmp/terra-prisca-numerics-check.json
uv run pytest -q tests/test_dense_roots.py tests/test_methane_budget.py \
  tests/test_habitat_integration.py tests/test_refuge_integration.py
```

The script writes only its explicitly supplied destination. It never replaces
committed historical results or the archived raw inputs.
