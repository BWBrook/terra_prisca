# Review of the full population coupling

Claude (Opus 5.5), 10 November 2026; reviewed `86b28ae`. **Accept the
deterministic coupling and its local stability results.** I also accept
Codex's review of my reduced model:

- inherited capture was an assumed closure even at mixed states;
- stability for every g also needs f_r < 0;
- the root finder drops exact and tangent roots;
- the no-capture label conflated climate and composition stability.

Two results matter most for interpretation. The second decides which
limitation comes first.

## 1. Acetogens warm this world

The source-consistent methanogen-only control sits at **273.5 K** on the
cold haze plateau. With acetogens present, the stable state is the mixed
community at **281.5 K**. Competition for H₂ diverts methane, thins the
haze and warms the planet by 8.0 K, or 4.7 K under the Arrhenius
continuation. This is the clearest ecological consequence the coupling has
produced so far, and it belongs in the page's lead. It is conditional on the
physiology below 4 °C, as the page already says.

## 2. A finite biosphere does not reach the mixed state from invasion

The 10⁻¹² gDW/L invasion falls to ln biomass of −7244 for methanogens and
−7669 for acetogens. At the reference habitat volume (0.00897 L cm⁻² ×
5.1 × 10¹⁸ cm²) and 3 × 10⁻¹³ gDW per cell, one cell on the whole planet is
ln X ≈ −67.2 ([`finite_invasion_check.py`](finite_invasion_check.py),
[output](finite_invasion_check.json)).

- **Methanogens fall below one cell globally within about 20 years** of the
  acetogen seed. The figure is 15 years for 10⁶ or 10¹² cells: acetogens draw
  H₂ below the methanogen break-even, and methanogens decay at the loss
  rate d.
- If methanogens are removed at that point, the acetogen-only world settles
  well away from the mixed state:

| f_ac | Acetogen-only endpoint | Could methanogens re-invade if any remained? |
|---:|---:|---|
| 0 | 283.2 K (the methane-free bridge) | yes, since T > T_sw |
| 0.5 | 294.4 K (greenhouse side) | yes |
| 0.9 | 273.5 K (haze plateau) | no, since T < T_sw |

So the endpoint of an invasion depends on whether methanogens survive the
transient anywhere. In this well-mixed single-habitat model they cannot. A
real biosphere would keep them through refugia: cold or warm patches,
sediments with different turnover, hydrothermal sources. Spatial structure
is therefore not a refinement; it decides the answer. The deterministic
mixed state is the right attractor only if some immigration or refugial
source exists.

## Priorities

1. **Finite persistence, first.** Reuse the stage-2 census approach: zero a
   guild when it falls below N_min cells globally (N_min = 1, 10⁶, 10¹²).
   Add an explicit immigration or refugial seed flux, I·X_seed, swept from
   zero upward. Report the endpoint (mixed, acetogen-only, methanogen-only,
   lifeless) as a map over N_min, I and f_ac, from both invasion directions.
   The minimal spatial version is two coupled habitats at different
   temperatures sharing one atmosphere. That is the natural next model if
   immigration alone proves decisive.
2. **Chemical-activity feedback, second.** Under the fixed-ΔG_c threshold
   law with other activities held, a Nernst correction is exact:
   p*_A ∝ [acetate]^{1/4} and p*_M ∝ p_CH₄^{1/4}. At the reference mixed state
   ([Ac] = 0.88 mM against the source's 0.5 mM), it raises p*_A by about 15%,
   a small shift. In the long-lag cases (37 M, 773 M), the same quarter-power
   law makes acetogenesis self-limiting before such pools form. That removes
   the implausible inventories by physics rather than by a validity flag.
   Cheap to add: one factor in the threshold call and a re-run.
3. Then a check of how much the 281.535 K pinning moves under items 1 and 2,
   and of the 283 K versus 265 K bridge only where physiology is defined.

## Verdict

The coupling is sound as a deterministic, well-mixed model. Its stable mixed
state is real in that model. It is reachable from invasion only if
methanogens persist somewhere. Report the warming result, and present
finite persistence and spatial refugia as the decisive open question.

```sh
uv run python models/haze_world/review/finite_invasion_check.py
```
