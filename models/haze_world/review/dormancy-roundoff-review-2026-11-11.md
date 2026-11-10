# Roundoff-stagnation fallback with existing physical guards

The roundoff variant combines the zero-stage predictor and certified
terminal-face dense adapter, adding one tightly qualified native Newton
correction. Targeted tests, a bounded accepted-state control and independent
read-only source review pass. The parent experiment's original-start and
required rare-window qualification remain separate gates.

The helper is `src/terra_prisca/haze_world/dormancy_roundoff_integration.py`,
SHA-256
`037761c4293b103eb44dee0a798a02d2c91b48faf53a03fdde47fb5b0f8f2369`.
The flag is `radau_dormancy_roundoff_stagnation`. Its numerical source extension
is the union of the predictor and terminal producers plus the new helper and
runner: 19 files. Every predecessor remains unchanged and retains its own
valid numerical epoch.

A private, verified one-return AST transformation passes the native
collocation solver's actual current W, Z, LU factors, state and scale to a
callback. It changes no earlier iteration. Converged solves and solves with
fewer than two iterations return their original values without additional work.
For a nonconverged solve after at least two iterations, the callback recomputes
one correction using those actual inputs and the original residual transform.
It does not reconstruct W from Z.

The proposed update qualifies only when all these checks pass:

- States, step, rate, RHS values, correction and stage bounds are finite.
- The normalized correction meets the existing native Newton tolerance.
- Every represented ODE collocation-stage coordinate, **after adding y**, moves
  by at most 64 machine spacings of the larger old/new magnitude. Zero uses
  the minimum positive subnormal spacing. Retained logarithmic information
  therefore cannot hide behind decoded biomass underflow.
- Every decoded physical collocation-stage stock passes the same 64-spacing
  check independently.

On qualification, the callback returns the proposed `T.dot(W+dW)` increments,
the iteration count plus one and the original convergence-rate estimate.
Otherwise it returns the original tuple's values and original Z object.
Physical exceptions propagate. The maintained native method still performs
its local-error test and its ordinary Jacobian/LU and error-history updates.
Native endpoint checks, domain prefixes, census, stock ledgers, root
conditioning, zero-predictor restoration, failed-trial counters and rollback
remain inherited. No stock is clipped, seeded or reset.

The terminal dense adapter retains its reviewed gate: an actual one-cell,
ten-year census, exactly one active habitat and present guild, finite native
arrays and a whole-piece certificate of at least 10¹⁶ cells. All other pieces,
including every uncensored, rare, two-guild or multi-habitat piece, retain the
original machine-epsilon-squared dense budget. Actual machine roundoff bounds
and physical error tolerances remain unchanged.

All 26 targeted tests pass in 2.00 seconds. They cover each independent gate,
the 64/65-spacing boundary, retained-log and physical-decoder distinctions,
zero spacing, nonfinite exclusions, original tuple identity, exact W/LU
plumbing, physical exception propagation, predictor success/failure/exception
restoration, root guards and module globals, terminal/domain composition,
strict-budget exclusions and ordinary physical RHS/redox agreement.

Independent review reran all 26 tests and exercised a nonconverged native
kernel after two iterations, with convergence rate 6.617. It verified the
actual W/Z/LU/state/scale supplied to the callback, bitwise native return on
exclusion, and unchanged global solver functions. No scientific trajectory was
added by that review.

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache \
MPLCONFIGDIR=/tmp/terra-prisca-mpl \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
uv run pytest -q tests/test_dormancy_roundoff_integration.py
```

The final helper advances the exact pinned 239.074051-year state by 100 years
in 0.1056 seconds: 17 accepted pieces, 123 RHS evaluations, two Jacobians and
one backend. There are no resets, positivity refinements, native failures or
negative native endpoints. Final physical stocks and accepted work counts
match the preceding combined scratch control bitwise.

One collocation fallback qualifies. One dense piece uses the terminal budget,
with an outward defect bound of 4.2549 × 10⁻²⁸ and local normalized-curve
redistribution bound of 0.129776 cells. Its conservative population lower
bound is 4.5449 × 10¹⁸ cells. The remaining pieces need no dense extension.
The event ledger retains every qualified correction's actual normalized norm,
worst coordinate and physical spacing changes, native time, step and iteration
count. Such events can belong to trials later rejected or truncated; they are
not counts of accepted physical steps.

This is a private absolute-clock accepted-state replay with retained charts
and no initial recensus, not a canonical full-horizon receipt. There is no
matched original 100-year runtime benchmark at this input state. The
qualification checks give neither a root or exact-flow error bound nor a
global-trajectory, rare-lineage or extinction-probability guarantee.

The [review receipt](dormancy-roundoff-review-2026-11-11.json) records source,
input, controller and raw hashes, the exact protocol, method-order and AST
proof, all qualified correction details and the dense certificate. Ignored raw
controls are in `local/haze/dormancy_roundoff_review/`. The ignored controller
`local/haze/dormancy_trial_review/production_roundoff0125_probe.py` accepts a
fresh `--output-dir` and refuses to overwrite a prior receipt.
