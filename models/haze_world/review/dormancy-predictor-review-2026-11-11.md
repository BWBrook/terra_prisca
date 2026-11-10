# Strict Radau with a zero-stage predictor

The new predictor variant removes repeated negative dormant-acetogen endpoint
trials at the recorded 13,362-year state of case 0125. It extends the strict
conditioned producer, with the original machine-epsilon-squared interpolation
budget everywhere. It imports no terminal-budget helper. Targeted tests, a
bounded accepted-state replay and independent read-only source review pass.
The parent experiment's original-start and first-window controls remain separate
qualification gates.

The helper is `src/terra_prisca/haze_world/dormancy_predictor_integration.py`,
SHA-256
`c2cf311336cfc24e8683c4b8e10d4c89cd1af60929b81935363de1948e2d5af8`.
Its flag is `radau_dormancy_zero_stage_predictor`. The exact source extension is
the conditioned producer's 13 files plus this helper and its separately owned
runner: 15 numerical source files, with no terminal-budget files. Earlier
producers and their receipts retain their original numerical epochs.

Maintained SciPy Radau normally extrapolates the previous dense polynomial to
initialize its next collocation stages. When native `sol` is absent, the same
method uses zero stage increments. The new rule selects that standard guess
when the native accepted state contains any **present linear allocation**
between zero and 10⁻²⁴ inclusive. It temporarily sets only native `sol=None`.
On success, it retains the newly computed dense output. On a native failure or
exception, it restores the prior dense object. It does not reset native stocks,
time, error history, Jacobian/LU objects or their ordinary update rules.

A verified method-resolution order keeps the conditioned helper's accepted
root-conditioning check ahead of the injected native step. A local constructor
closure supplies its coordinates through a copied predecessor step namespace;
no module global changes. The physical RHS, units, error tolerances, six-iteration
Newton budget, census, stock ledgers, native endpoint and domain-prefix checks,
failed-state rollback/counters and strict dense certificates remain inherited.

All 17 targeted tests pass in 3.86 seconds. They check the preserved native
state, error-history and Jacobian/LU identities at the call into the maintained
method; failure and exception restoration; new dense output on success;
predicate exclusions and exact boundaries; accepted root conditioning before
native construction; module-global identity and wrapper failure accounting;
strict dense/domain composition; census inventories; retained rare logarithms;
and ordinary physical RHS and short-flow agreement.

Independent review reran all 17 tests and checked the installed SciPy method's
uses of `sol`. Six synthetic linear-ODE steps match a manually zero-initialized
maintained Radau method bitwise in states, RHS values, Jacobian, collocation
increments, history and dense output. No scientific trajectory was added by
that review.

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache \
MPLCONFIGDIR=/tmp/terra-prisca-mpl \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
uv run pytest -q tests/test_dormancy_predictor_integration.py
```

The final helper replayed the exact pinned state at 13,362.348592 years for
100 years in 0.1195 seconds: 21 accepted pieces, 226 RHS evaluations, four
Jacobians and one backend. There were no resets, positivity refinements,
negative native endpoints, declined defects, native failures or chord
extensions. Twenty prior dense predictors were suppressed; the initial step
already had no previous dense output. Final physical stocks and accepted work
match the preceding strict-parent scratch control bitwise. That control also
matched the terminal-parent zero-predictor endpoint bitwise, using no broader
interpolation repair in either run.

By comparison, the original predictor advanced only 2.93123 years from the same
pinned state before a 60-second wall bound. It made 13,180 accepted pieces,
115,992 RHS evaluations and 2,636 positivity rejections. Every recorded negative
endpoint was dormant acetogen allocation index 4; early examples were about
−9.18 × 10⁻⁴¹ on attempted 0.01-year pieces. All were rejected by the existing
guards. There were no native solver failures or chord-defect refusals. This
comparison was incomplete and has no final endpoint or inferred full-run
runtime. It isolates a repeated predictor-dependent numerical rejection at
this state.

The final control preserves temperature, hydrogen pressure and active acetogen
biomass at their initial values to stored precision. Its tiny dormant pool
decays; that microscopic result has no independent rare-lineage accuracy
certificate. The control uses exact retained allocation/chemical charts and an
absolute-clock wrapper without initial recensus. It is a bounded diagnostic,
not a canonical full-horizon producer receipt. No exact-flow, global-trajectory,
extinction-probability or rare-lineage error guarantee follows.

The [review receipt](dormancy-predictor-review-2026-11-11.json) records source,
controller, input and raw hashes, exact protocol, verified method order,
predictor/work counters and the bounded original comparison. Raw controls are
in `local/haze/dormancy_predictor_review/`; the comparison inputs are pinned
under `local/haze/dormancy_strict_zero_predictor_review/`. The ignored controller
`local/haze/dormancy_trial_review/production_predictor0125_probe.py` accepts a
fresh `--output-dir` and refuses to overwrite a prior receipt.
