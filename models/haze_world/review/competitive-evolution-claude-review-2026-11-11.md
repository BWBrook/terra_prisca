# Review: competitive kinetic evolution

Claude (Opus 5.5), 11 November 2026. This reviews Codex's build of the
[competitive-evolution stage](../competitive-evolution.md), commits
`6ebb9eb`–`f497d56`, against the [specification](../competitive-evolution-spec.md).

**Verdict: accepted.** KE1, KE2, KE4, KE6 and KE7 are supported, KE3 has
qualified support, and KE5 is refuted. I accept each of these assessments,
the ledger rows C29–C37, and E13.

## Independent recomputation

I recomputed the key numbers with the preview's own best-response code
([competitive_evolution_preview.py](competitive_evolution_preview.py)),
with the trait confined to 4–30 °C. That code path is separate from Codex's
`competitive_best_response` and `evolved_kinetics` modules.

| Quantity | Codex | Claude |
|---|---:|---:|
| Reference-turnover crossing, `E = 0`, linear shape | 277.960221 K | 277.960 K, at kinetic positions 10 and 25 °C |
| Same, `E = 0.65 eV` | 281.868 K | 281.868 K, at 5.7 and 8.3 °C |
| Matched-level slope `d(R*_A − R*_M)/dT` | 0.402999 Pa/K | 0.402999 Pa/K |
| Threshold contribution | 0.197474 Pa/K | 0.197474 Pa/K |
| Maintenance contribution | 0.205526 Pa/K | 0.205526 Pa/K |

C29, C32 at `E = 0.65`, and C36 therefore have a second implementation
behind them.

## My errors

- **The trait bound.** My spec said the kinetic position stays "within the
  measured range", but my preview allowed it down to −0.15 °C, which is the
  continuation below 4 °C. Codex used the specified 4–30 °C bounds. That
  explains why the preview's `E ≥ 0.45` values (283.75 and 283.84 K) differ
  from production (281.11 and 281.87 K). The predictions were not rewritten
  to fit, which is right.
- **The thermodynamic anchor.** KE5 is refuted fairly. Freezing either
  thresholds or maintenance removes the crossing, and the two contribute
  almost equally to the restoring slope. The narrative I drafted,
  "selection tunes enzymes, not thermodynamics", is wrong for this model.
  The supported statement is narrower: the temperature dependences that
  the evolving trait cannot reach (thresholds and maintenance together)
  keep the crossing.

## Framing constraint for the paper

The contrast with the single-guild precursor (C02) is not like-for-like.

- **In C02**, the whole thermal performance curve evolved, so every
  temperature dependence was within selection's reach. The signature
  vanished.
- **Here**, only the uptake kinetics evolve. Thresholds and maintenance stay
  fixed, and they carry the switch.
- **The comparison therefore shows** that a thermostat survives selection
  insofar as its temperature dependence lies outside the traits under
  selection.
- **What that means for maintenance.** Cessation thresholds are
  thermodynamic and largely beyond selection's reach. The maintenance
  temperature response is physiological and could plausibly evolve. Whether
  the switch survives selection on maintenance is therefore the natural next
  question, and the paper should say so.

E13 already forbids "evolution-proof" and generalisation beyond this trait
family. I have added one bullet to synthesis step 8 so that the contrast
cannot be read as like-for-like.

## Other points

- **Turnover dependence of evolution.** Kinetic adaptation keeps the
  thermostat at reference turnover. It loses the crossing at low turnover,
  and at high turnover some crossings leave the climate range. 30 of the 72
  joint settings have no community. That turnover dependence belongs
  alongside C12 in the paper, not in a footnote.
- **S3 and S4.** Separating them is the right call. The 14 greenhouse roots
  are uninvadable by mutants yet ecologically unstable, which is a good
  teaching example of why a trait optimum is not a climate equilibrium.
- **KE3.** The 274.002 K plateau value is better than my informal "near
  273.5 K". The qualifier stands: the stopped canonical paths do not show
  arrival there.

## Readiness

All four conditions in [synthesis.md § Paper](../synthesis/synthesis.md#paper)
now hold:

1. The ledger's 37 rows are all supported, refuted or superseded, with no
   checker errors.
2. Both agents accept E1–E13.
3. The scope is complete.
4. Every agreed figure question has committed data, including the C07
   transient.

I am reporting readiness to Barry.
