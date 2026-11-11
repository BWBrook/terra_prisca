# Haze-world synthesis

Claude (Opus 5.5), 11 November 2026. This page frames what the haze-world
stages add up to. Every result statement cites the [claims ledger](claims.csv),
and [estimands.md](estimands.md) states what each result may claim. Codex
checks the provisional rows next. This synthesis will become a paper (see
[Paper](#paper)).

## Thesis

**A thermostat built from competitive exclusion needs a memory.** Under an
Archean organic haze, two microbial guilds competing for hydrogen can
regulate climate. The regulation works because the competitive winner
switches with temperature, on the branch where more methane cools. But
exclusion is fast and the climate response is slow, so the guild that is
losing now is gone before the climate turns in its favour. The thermostat
persists only if something stores the loser across that gap. Biology offers
two stores: space, as refuges, and time, as dormancy. Each works through its
own mechanism, and each has a simple quantitative threshold.

## The argument

1. **A single guild regulates only at its tolerance edge, and evolution
   erases that.**
   - On Arney's haze-cooling branch, one methanogen guild holds the climate
     [0.015–0.037]{.C01} K above its cold net-growth threshold.
   - Once the thermal optimum can evolve, the signature disappears: the
     regulation ratio is [1]{.C02} under every loss shape.
   - Regulation returns only when an imposed floor becomes the set point
     []{.C03}.
   - The danger in losing supply is heat, not cold: methanogens die in the
     [297]{.C04} K warm peak as the haze collapses.

2. **Hydrogen competition supplies a second thermostat, with an ecological
   set point.**
   - Acetogens win in the cold and methanogens in the warm.
   - Both central switches, [281.5]{.C05} and [282.8]{.C05} K, lie on the
     haze-cooling branch, so the feedback restores the climate rather than
     trapping it.
   - With explicit populations, the mixed community holds the climate at
     [281.535]{.C06} K, against [273.517]{.C06} K for methanogens alone.
     Acetogens warm the world by diverting hydrogen from methane.
   - The warming falls from [8.02]{.C06} K to [4.73]{.C06} K under the
     alternative cold physiology.

3. **Turnover, not tolerance, sets the set point.**
   - The switch sits where the guilds' break-even hydrogen pressures cross,
     and the required uptake `m + L/Y` moves that crossing.
   - Across the turnover range, stable set points span
     [273.4]{.C12}–[296.1]{.C12} K.
   - At `f = 0` an acetogen-only world becomes stable above
     [0.001238145]{.C13} h⁻¹, and the planet is then bistable.

4. **In finite worlds, exclusion outruns the climate.**
   - With a census and no immigration, methanogens are removed after
     [20]{.C07} years, while the climate has moved only from
     [273.517]{.C07} to [273.525]{.C07} K.
   - Invasion history therefore picks a single guild, even though the
     continuum equations have one stable mixed state.

5. **Space can store the loser, if the refuges are buffered.**
   - Refuges that track global temperature fail. The cold refuge must also
     survive the [297]{.C08} K greenhouse peak.
   - Temperature-buffered warm and cold refuges restore the same mixed state
     from both invasion directions, in all [192]{.C09} planned cases.
   - One refuge leaves an overshoot bottleneck whose depth scales as
     exchange to the power [4.423]{.C10}.
   - A demographic criterion of [230]{.C10} cells moves the critical
     exchange only about [3.4]{.C10}-fold.
   - Refuge methane can extend the mixed window, by [0.28]{.C14} K at one
     setting.
   - Coexistence is not regulation. Source–sink methanogens can carry
     [2.082]{.C15}% of global catabolism but only [0.001080]{.C15}% of bulk
     catabolism.

6. **Time can store the loser, if dormant cells outlast about 1.3% of the
   unfavourable interval.**
   - Without refuges, 50% first-window survival needs these dormant
     half-lives:

     | Displaced guild | f = 0 | f = 0.5 |
     |---|---|---|
     | Methanogens | [11.3]{.C17}–[13.2]{.C17} yr | [31.6]{.C17}–[32.3]{.C17} yr |
     | Acetogens | [158]{.C17}–[172]{.C17} yr | [88]{.C17}–[96]{.C17} yr |

   - Acetogens need longer because their suppression spans the greenhouse
     peak.
   - The approximation `ε* ≈ ln(N₀/N₅₀)/(Lτ)` predicts these within a factor
     of [0.992]{.C18}–[1.167]{.C18}. Its coefficient of [1.275]{.C18}%
     belongs to this population ratio.
   - **Dormancy can also hurt.** Under a growth-triggered switch, cells
     enter dormancy during a mild disadvantage and then die faster than they
     would have while active. At `ε = 0.1` the acetogen minimum reaches
     10^[−59.5]{.C19}, against 10^[−14.25]{.C19} without dormancy.

7. **The thermostat rings.**
   - The reference mixed state is a weakly damped oscillator: period
     [119.6]{.C20} yr, damping time [4,854]{.C20} yr, quality factor
     [127]{.C20}. The competitive switch supplies a stiff restoring force,
     while slow methane removal supplies weak damping.
   - Kicks of ±10% decay as that linear mode predicts []{.C20}. They do not
     reach the dormancy cycles []{.C27 .superseded}.
   - Some invasion paths under cubic switching keep cycling, with ranges of
     [0.2]{.C21}–[1.5]{.C21} K, beside a stable equilibrium.
   - Linear switching damps three of these controls. The two warm-refuge
     controls remain unresolved []{.C22}.

## What is robust and what is conditional

| Result | Robust to | Conditional on |
|---|---|---|
| Restoring switch (2) | uptake law and phenotype choices tested in the switch maps | Arney case B's haze-cooling branch |
| Turnover sets the set point (3) | `f` and refuge geometry | uniform `L` for both guilds |
| Exclusion outruns climate (4) | census floor and activity scheme | methane lifetime; quasi-static climate |
| Buffered refuges rescue (5) | invasion direction | refuge temperatures fixed outside the model |
| Seed-bank rule (6) | switching speed (slow switching moves `ε*` by less than 3×) | entering population; climate path |
| Harmful dormancy (6) | refuge exchange | growth-triggered switching law |
| Ringing (7) | `f` and `L` (`Q` from 22 to 263) | reference physiology |

Every row is also conditional on the four shared assumptions in
[estimands.md](estimands.md).

## Corrections recorded along the way

The record of failed predictions is part of the result. Products should
show it, not hide it.

- Claude proposed a cold trap from the switch. Codex's sign check showed
  the switch restores instead.
- KD2 predicted that dormancy removes the overshoot loss. It fails, and C19
  gives the mechanism (C28).
- Claude's "exact" seed-bank formula is superseded by approximate agreement
  (C25 → C18).
- The predicted 10¹² minimum for robust persistence was refuted at
  1.16×10¹¹ cells (C11).
- Bank-only endpoints decaying at `εL` (C26) and 10% kicks reaching the
  cycle (C27) are refuted.

## Open questions, in order of value

1. **Does selection erase the competitive set point?** C02 showed that
   evolution removes a tolerance-edge thermostat. The two-guild switch
   differs: it is the crossing of two break-even pressures. Selection on
   affinity or maintenance moves each guild's curve, not the fact that they
   cross.
   - *Hypothesis:* selection can shift a competition-set point but cannot
     remove it, wherever the crossing rests on hydrogen thresholds that
     differ in temperature dependence.
   - This is the natural bridge between the two halves of the haze world,
     and the most interesting next experiment.
2. **Coupled stochastic demography.** A coupled calculation would replace
   per-guild first-window probabilities with joint endpoint probabilities.
   It would also decide the many-cycle question (C24).
3. **The two unresolved warm-refuge linear controls (C22).** Pursue them
   only if a claim depends on them. None in this synthesis does.
4. **External inputs that bind the conditionality.** In order:
   - the photochemical loss elasticity near `r ≈ 0.2`;
   - a matched methane-free climate, to replace the bridge;
   - cold-strain physiology;
   - Archean turnover rates.
5. **Luminosity.** A solar sweep needs climate responses at other S/S₀.

## Paper

**Decision.** Barry, 11 November 2026, in chat with Claude: "Yes, we should
aim for a paper. But I'd like to follow a particular structured approach to
doing this. So, when you and Codex are 'ready to write', that's when I'll
step in and guide that part of the process more carefully."

Barry will lead the writing process. Until he does, Claude and Codex do not
scaffold or draft the manuscript products. They bring the evidence to a
ready-to-write state.

**Ready to write** means all four of these hold:

1. Every current ledger row is `supported`, or it has been contested and
   resolved into a supported, superseded or refuted row.
2. Claude and Codex both accept [estimands.md](estimands.md).
3. Both agree the scope, including whether the evolution test (open
   question 1) runs before writing.
4. Both agree a figure plan, with each figure's data file in the
   repository.

Claude then tells Barry in chat.

The working title is *A microbial thermostat needs a memory: hydrogen
competition, refuges and dormancy under an Archean haze*. The outline below
is a proposal for Barry's process, not a commitment.

- **Article.** The argument above, with six figures:
  - the climate response with the switch (2);
  - the turnover regime map (3);
  - an exclusion-versus-climate timeline (4);
  - refuge rescue and the bottleneck scaling (5);
  - seed-bank thresholds and the harmful-dormancy traces (6);
  - the damped mode with the cycling paths (7).

  The stage-1 and stage-2 single-guild results enter as the motivating
  contrast.
- **Brief.** Two pages on "why a living thermostat needs a memory".
- **Agent guide.** Module map, frozen archives and manifests, the estimands
  and their traps, and the reproduce commands from the ledger.

The roles section would name Claude (Opus 5.5) for design, specifications,
reviews and this synthesis. It would name Codex (GPT-6) for the
implementations, experiments, archives, qualification checks and
mathematical audits. Barry is the scientific facilitator. The board record
can be published with it.

## Next steps

- **Codex:**
  - Check each provisional row by a separate route, and tighten evidence to
    the most specific output file. Several rows cite model pages; a frozen
    CSV or JSON is better.
  - Amend [estimands.md](estimands.md) where it disagrees.
  - Restamp, then mark rows supported or contest them.
- **Claude:** reconcile Codex's changes and agree the scope and figure
  plan, then report readiness to Barry.

Check the ledger and its citations with:

```bash
python3 tools/claims.py check models/haze_world/synthesis/claims.csv models/haze_world/synthesis/synthesis.md
```
