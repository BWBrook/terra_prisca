# Competitive-evolution stage: checks and dispositions

Codex (GPT-6), 11 November 2026. Implementation of the unchanged
[specification](../../models/haze_world/competitive-evolution-spec.md),
with the [method qualifications](../../models/haze_world/competitive-evolution-methods.md)
and [independent mathematical review](../../models/haze_world/review/competitive-evolution-math-review-2026-11-11.md).
Original reference producers and predictions are preserved.

| Finding or prediction | Check | Disposition | Owner |
|---|---|---|---|
| Preview uses traits below the specified measured interval | Independent per-segment minimization and production comparison at shared settings | Enforce explicit 4–30 °C bound. Preview differences above 0.5 K are explained before S3; original preview retained. | Codex |
| KE1 reference zero-E joint equilibrium | Root, resource balance, spectra and mutant checks | Supported:277.960221 K and stable mixtures at both f values. | Codex |
| KE2 orientation | S1 and joint frozen-trait thermal slopes | Supported for all 166 detected crossings, not an interval theorem beyond the search. | Codex |
| KE3 low-turnover state | Static crossing map and separately optimized pure-resident assays | Qualified support: no crossing; pure M at 274.002 K on the imposed plateau. No fixed tolerance for “near273.5 K” was specified; canonical paths do not establish arrival there. | Codex |
| KE4 constrained shift | Shared-setting both-interpolation comparison | Supported: maximum 0.491 K, within stated2.5 K band. | Codex |
| KE5 unique thermodynamic anchor | Prescribed30 °C h/m controls | Refuted: freezing maintenance alone also removes reference crossing. | Codex |
| Meaning of unmatched freezes | Separate matched-value local derivative decomposition | Post-prediction diagnostic: threshold 0.197474 and maintenance 0.205526 Pa/K both contribute positive slope. Do not substitute it for KE5 or claim whole-control ecological stability. | Codex |
| KE6 local convergence and damped mode | Ecological matrices, smooth canonical reduction, one-sided node tests and independent selected finite differences | Supported on 42stable cooling states at all 3supplies; Q 16.30–516.53.14greenhouse roots are unstable and excluded from adiabatic convergence. | Codex |
| KE7 interpolation | Shared roots and feasibility flags | Supported below 2 K, maximum 1.231 K; at high loss/E=.2 interpolation changes whether a joint state exists. | Codex |
| S4 optimizer versus invasion fitness | All 112 guild assays independently re-evaluated on 2601traits | All pass tolerance1e-8/hour; max 7.07e-17/hour. Not a theorem for unmodelled mutations. | Codex |
| S5 ecology originally inspected only at saved intervals | Parent code review | Fixed before final run: check every accepted step; last supported state and attempted next traits separated. | Codex |
| S5 paths versus physical extinction | Paired.05/.025 °C trait steps, branch checks, separate pure states |60tracks lose supported mixed branch. Finite-step/max 0.207 K endpoint difference remains; no extinction, arrival or calibrated-year claim. | Codex |
| Fixed-trait inventory |501/1001 root-grid comparison | All 200rows agree; retain numerical rather than exhaustive/global-attractor scope. | Codex |
| C07 figure export | SHA-verified raw record, original metadata conversion and matching original climate sources |209 event-preserving post-census samples, no interpolation. Removed-cell counts are separate. | Codex |
| Full test discovery included archived historical test copies | Actual collection error | Limit pytest discovery to repository tests/; package dependencies unchanged. | Codex |

## Verification and artefacts

The final full suite passes **843 tests**, including the new physiology,
budget, equilibrium, invasion, convergence and path failure-mode controls.
The independent checker verifies all 112 mutant assays, selected ecological
and canonical matrices, source/output hashes and the two distinct anchor
controls. The derived assessment recomputes all seven prediction outcomes.
The compact C07 CSV is checked against its original exact removal event and
temperatures. Test logs remain in ignored local working storage.

The results are reproducible through:

```sh
uv run python -m terra_prisca.haze_world.competitive_best_response --run
uv run python -m terra_prisca.haze_world.competitive_evolution --run
uv run python -m terra_prisca.haze_world.competitive_assessment
uv run python -m terra_prisca.haze_world.export_c07
uv run python models/haze_world/review/competitive-evolution-math-review-2026-11-11.py
uv run pytest
```

All new scientific outputs are compact CSV/JSON/PNG files below the repository
size boundary. No new remote job, large raw archive, manuscript scaffold or
paper product was created. The required C07 raw input already belongs to the
finite-invasion archive.

C29–C37 and E13 record the results and their limits. C33 retains the refuted
KE5 prediction, with the corrected C36 diagnostic alongside it. The original
preview/specification, old physical results and existing strict endpoint and
survival labels remain unchanged. The next action is Claude's scientific
reconciliation, followed by the agreed readiness report to Barry if accepted.
