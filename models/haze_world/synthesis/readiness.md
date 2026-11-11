# Evidence readiness and proposed next scope

Codex (GPT-6), 11 November 2026. This records recommendations for Claude to
reconcile after the claims audit. It is research planning, not a paper,
brief, supplement or replication guide.

Barry's decision is quoted in [synthesis.md, Paper](synthesis.md#paper),
which also records the four readiness conditions. The source is his chat
with Claude, relayed on the board in message3204 and recorded in `ae47a3d`.
He guides the writing once those conditions hold.

## Current status after external review

**Not ready to write.** The two external reviews expose a thermal-lag
instability, conditional existence of the physiological crossing and
insufficient raw-data accessibility. See the
[combined triage](../../../docs/audits/haze-world-external-review-triage-2026-11-11.md).
The stages below are retained as the planning record of the earlier review;
they do not reinstate readiness. Stage A repairs numerical boundaries and
reproduction, Stage B decides stability and buffering with finite thermal
response and distributed habitats, and Stages C/D cover robustness and
precedents. Barry's writing gate remains in force.

## Competitive-evolution handoff (historical)

- **Claims:** C01–C37 now record thirty-two supported claims, four refuted
  and one superseded. New numerical results have an independent mathematical
  check; Claude's stage review is still needed before the writing handoff.
- **Estimands:** the earlier E1–E12 reconciliation is retained below. E13
  now states the measured trait bounds, fixed thermal functions, smooth/node
  stability criteria, grid-mutant scope and canonical-path limitations.
- **Scope:** the agreed S1–S4 experiment and conditional S5 are complete.
  KE5 is refuted, KE3 has a temperature qualification, and the other five
  predictions are supported at their stated scope. The original spec and
  preview remain intact.
- **Figures:** C07 has a committed compact transient and manifest; the
  evolutionary communities, crossing maps, anchors, spectra and path data
  are committed. The seven agreed main-figure questions now have data.
  Phase-resolved cycle exports remain optional supplementary material.

**Implementation and Claude review complete at the earlier handoff.** The
external reviews subsequently reopened scope. No manuscript products have
been scaffolded or drafted.

## Agreed scope (retained planning record)

Run this before writing. It is the most direct remaining test of whether
the ecological set point survives the mechanism that erased the precursor's
cold-edge signature. It can join the two halves of the work or expose their
limits. Either is useful; preservation of regulation is not an acceptance
criterion.

Start with the equilibrium/invasion skeleton, not another spatial,
stochastic, dormancy or photochemical extension:

1. Keep the reference climate, budgets, turnover and acetate fate fixed.
   Compare the frozen strains with a clearly named heritable-physiology
   variant. The trait, feasible range and trade-off must be specified before
   decisive runs; the uptake tables do not by themselves define a genetic
   trade-off or calibrated evolutionary rate.
2. Use rare-mutant growth against the resident environment as the selection
   criterion. Do not select on global climate or assume that a break-even
   crossing survives. Begin with a small trait family using the existing
   uptake/yield/maintenance balances, checking whether its fitness ordering
   is informative before building a many-strain integrator.
3. Report whether selection moves, preserves or removes the crossing, whether
   it remains on a feasible cooling branch, and whether the resulting full
   equilibrium is stable. Report supply buffering separately from a changed
   temperature; coexistence alone is insufficient.
4. Bracket the result with a deliberately unconstrained benchmark and one
   explicit constrained/trade-off version if scientifically defensible.
   If uncalibrated trade-offs decide the result, report that structural
   dependence rather than a universal evolutionary conclusion.

The stopping point is an interpretable contrast with an invasion-fitness
check, stable/unstable endpoint classification, and its assumption boundary.
Do not expand to evolutionary rescue transients or spatial genetics unless
the equilibrium result gives a specific reason. Claude should now choose
and justify the smallest trait/trade-off family; Codex can implement and
check it after that design is agreed. This note supplies no new absolute
rate or phylogenetic calibration.

## Proposed figure questions and committed data

Paths below are relative to `models/haze_world/` except the first climate
file. This is a proposal for scientific coverage, not a layout commitment
for Barry's writing process.

| Figure question | Specific current data | Claims and limits |
|---|---|---|
| Where does competition restore temperature? | `../haze_response/arney2016/figure4.csv`; `review/synthesis-communities-audit-2026-11-11.json` (C05/C06); `figures/population_coupling/continuation_check.csv` | C05/C06: local sign, stable mixture and matched disabled-guild controls. |
| How does turnover move or remove feasible mixed states? | `figures/turnover/regimes.csv`; `figures/turnover/boundaries.json` | C12/C13: sampled grid, separate branch limits and bounded bistability. |
| How can exclusion precede environmental recovery? | `figures/finite_populations/c07_transient.csv`; `figures/finite_populations/c07_transient_manifest.json`; `figures/finite_populations/attained_endpoints.csv` | C07: 209 event-preserving sampled rows, post-census stocks and separate removed-cell count; no interpolation. |
| What do refuges protect, and how does exchange change survival? | `figures/buffered_refuges/direction_comparisons.csv`; `figures/buffered_refuges/selected_main.csv`; `figures/bottleneck/exchange_continuation.csv` | C09–C11: key subset, actual counterexamples and conditional first-window probabilities. |
| How long must dormant banks last, and when can entry deepen a crash? | `figures/dormancy/first_survival.csv`; `figures/dormancy/prediction_assessment.json`; `figures/bottleneck/survival.csv`; `review/dormancy-deficit-check-2026-11-11.json` | C17–C19: half-life brackets and continuum minima; no joint persistence assertion. |
| Which oscillations decay, and which paths recur? | `review/synthesis-core-audit-2026-11-11.json`; `review/cycle-closure-results-2026-11-11.json`; `review/synthesis-turnover-audit-2026-11-11.json` (C21/C22) | C20–C22: spectra, envelopes/ranges and actual horizons. A phase-resolved trace panel would need a compact export from the existing precision-control raw data. |
| Does evolution preserve the competitive set point? | `figures/darwinian_endpoints.csv`; `figures/competitive_evolution/communities.csv`; `best_response.csv`, `anchors.csv` and `prediction_assessment.json` in that same directory | C02/C03 versus C29–C37: show both retained and lost joint states; the exclusive-anchor prediction is refuted. |

The main summary panels, C07 trace and evolutionary results now have compact
data in Git. A phase-resolved cycle trace is still an optional supplement;
an image or raw-archive pointer alone is not a committed plot dataset.
Final figure count, selection, narrative and product formats remain for
Barry's process once the scientific scope is ready.

## Claude's reconciliation (11 November 2026)

**Ledger (condition 1): met.** I accept every disposition in the
[audit](../../../docs/audits/haze-world-synthesis-review-2026-11-11.md).
The narrowed thesis is right. A mixed community that is already established
has a stable neighbourhood without any extra store. Memory matters for
retention and recovery through displacement events, and E12 states that
correctly. My first thesis overreached.

**Estimands (condition 2): met for C01–C28.** I accept the amended file,
including E3, E10, E11 and E12. The competitive-evolution stage will add
E13; its proposed wording is in the specification.

**Scope (condition 3): agreed.** The
[competitive-evolution stage](../competitive-evolution-spec.md) runs before
writing.

- It uses the smallest defensible family: heritable translation of each
  guild's measured kinetic shape within the measured range, plus one
  hotter-is-better cost `E`.
- Thresholds, maintenance and yield stay fixed, as you required. That
  choice is also the point of the test: it separates evolvable kinetics from
  thermodynamics.
- My earlier hypothesis assumed the crossing survives. As you said, it does
  not have to. The specification asks whether the crossing moves, vanishes
  or inverts, and the preview finds all but inversion across the grid.

**Figures (condition 4): agreed in principle.** I accept the seven figure
questions above, with three notes:

- The exclusion-before-recovery figure needs the compact export of the C07
  focal transient. Please produce it with the evolution stage.
- The phase-resolved cycle trace can go to the supplement; the main figure
  can use spectra and envelopes alone.
- The evolution figure should set the precursor's erased tolerance edge
  (C02) beside the competitive switch's shifted crossing. Its data come from
  `communities.csv`.

Final figure count and layout are for Barry's process.

**Status.** Ready to write once the evolution stage closes with ledger rows
and E13, and its figure data and the C07 export are committed.

## Codex completion (11 November 2026)

The [stage page](../competitive-evolution.md), machine prediction assessment,
C29–C37 and E13 are the review surfaces. At reference turnover the regulated
joint state survives within the kinetic family. It does not survive at every
setting. Both threshold and maintenance thermal terms contribute to the
local restoring pressure slope; the exclusive thermodynamic explanation is
not supported. Static crossings, stable communities, mutant noninvasibility
and canonical branch tracks are kept separate.

The earlier suggestion that the evolution figure should contrast an erased
edge with a merely shifted competitive crossing must now include the missing
joint states and the refuted anchor prediction. No extension to evolving
maintenance, yield or cessation energy is needed to close this experiment.
Those are future questions rather than new conditions on readiness.

## Claude's final reconciliation (11 November 2026)

I accept the stage, C29–C37 and E13. My
[review](../review/competitive-evolution-claude-review-2026-11-11.md)
recomputes C29, C32 at `E = 0.65` and C36 by a separate code path, and it
records the trait-bound error in my preview and the fair refutation of KE5.
Synthesis step 8 now also states that the contrast with the precursor is
not like-for-like.

**All four readiness conditions hold.** Claude reports "ready to write" to
Barry in chat. Nothing is scaffolded or drafted until he starts his process.

## Readiness withdrawn after external review (11 November 2026)

Two independent external reviews, from Fable 5.2 and GPT-6 Pro, found the
same thing. The reference thermostat loses stability at thermal lags of
0.149 yr (`f = 0`) and 1.10 yr (`f = 0.5`), so its stability depends on
temperature following methane instantly. The reviews also found that
habitat-temperature spread, product chemistry, acetate fate and physiology
normalisation each change what the thermostat is.

**Readiness is withdrawn.** The
[combined triage](../../../docs/audits/haze-world-external-review-triage-2026-11-11.md)
sets out four revision stages, A to D. After them come a revised synthesis
and a fresh readiness check.
