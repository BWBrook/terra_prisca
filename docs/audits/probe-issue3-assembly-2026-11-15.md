# Issue 3: can the regulating community assemble?

Claude (Opus 5.5), 15 November 2026. Responds to Barry's and Fable's
Issue 3 (pressure-test thread 165). Two bounded checks were run; everything
else uses stored evidence. No manuscript text has changed.

New checks:

- [`issue3_assembly.py`](../../models/haze_world/review/issue3_assembly.py)
  and its [JSON](../../models/haze_world/review/issue3_assembly.json):
  - 16 invasions with the methane response sped up 1–1000 times, steady
    states unchanged;
  - three lifeless starts, one per f, on the production finite-census
    integrator.
- [`issue3_lifeless.py`](../../models/haze_world/review/issue3_lifeless.py)
  and its [JSON](../../models/haze_world/review/issue3_lifeless.json):
  the lifeless starts repeated with the plain population integrator: the
  census over the first 1,000 years, and the uncensored run over 100 kyr.
- [`issue3_immigration.py`](../../models/haze_world/review/issue3_immigration.py)
  and its [JSON](../../models/haze_world/review/issue3_immigration.json):
  a recount of the stored immigration endpoints.

## Short answers

1. **Fable's reading is right**, with one refinement. The resident is removed
   by ordinary competition at its own temperature, within 10–70 years (fixed
   products, τ = 0). The climate needs 1,000–13,500 years to carry
   temperature across T\*. The single uniform habitat fails because a lost
   group cannot return. The continuous equations without the census do reach
   the mixture.
2. **No.** From a lifeless start the mixture never forms, at any f. The
   lifeless world (283.2 K) lies on the methanogens' side of T\*.
   Methanogens remove acetogens within 60 years, and the planet settles cold
   with methanogens alone.
3. **The minimal refuge statement.** The mixture assembles from either history
   when the displaced group can persist until the climate crosses T\*.
   Climate-tracking refuges failed the test only where they stopped
   protecting the loser, or where the run left the model's temperature
   support.
4. **Recommendation.** Arrival order becomes the first half of an assembly
   result: "a uniform habitat cannot assemble the regulator; persistence
   elsewhere can". Habitat variation does not buy assembly *at the price of
   precision* in the evidence we have, so the unifying trade-off would
   overreach. Wording proposals are at the end.

## 1. Mechanism and methane lifetime

**Stored runs (C52, `dynamic_realisation/invasions.csv`).** Each displaced
resident first falls below one cell within:

- 7–19 years (f = 0.5, both chemistries);
- 18–68 years (f = 0, except below);
- 257–288 years (f = 0, product feedback, methanogens invading).

At removal, temperature has moved 0.006–0.018 K from its start in three of
the four fixed-product, τ = 0 runs (C07 focal case: 273.517 to 273.525 K at
20 years). In the fourth (f = 0, methanogens invading) it has moved 0.41 K. The time for temperature to cross
T\* in the same runs is:

| f | direction | resident removed | temperature first crosses T\* |
|---|---|---|---|
| 0 | A into M | 20 yr | 1,029 yr |
| 0 | M into A | 70 yr | 13,459 yr |
| 0.5 | A into M | 20 yr | 2,501 yr |
| 0.5 | M into A | 10 yr | 7,499 yr |

Fixed products, τ = 0; the crossing is from the uncensored-equivalent census
run after removal. Removal comes 50–750 times sooner than the crossing.
Thermal lags of 3 and 30 years do not change any outcome (C52), because they
are short beside the methane response.

**Methane lifetime.** The methane equation's right-hand side was multiplied
by s = 10, 100 and 1000. That divides the lifetime by s and multiplies every
source by s, so every steady state, including both single-group states and
T\*, is unchanged. Only the time methane takes to respond shrinks. s = 1
reproduces the stored C52 outcomes and removal times.

| lifetime | f = 0, A into M | f = 0, M into A | f = 0.5, A into M | f = 0.5, M into A |
|---|---|---|---|---|
| 10,000 yr | A alone | M alone | A alone | M alone |
| 1,000 yr | A alone | M alone | A alone | M alone |
| 100 yr | **M alone** (invader lost at 40 yr, 282.9 K) | M alone | A alone | M alone |
| 10 yr | **both, 281.535 K** | M alone | **both, 281.535 K** | M alone |

- **Sourced lifetimes (6–19 kyr; model README).** The arrival-order outcome
  holds across this range and down to 1,000 years.
- **Lifetime of 100 years or less.** The outcome changes, but not simply
  towards the mixture.
- **Overshoot.** At 100 years the fast climate overshoots T\* and the
  invading acetogens are themselves lost at 282.9 K. This is the overshoot
  that removed acetogens under a warm-only buffered refuge (C09 inventory;
  `buffered-refuges.md`).
- **10-year lifetime.** Acetogen invasions assemble the mixture at T\*.
  Methanogen invasions still lose acetogens within 10–30 years: the resident
  in the warm acetogen world is excluded too fast even for a 10-year
  lifetime.

A modern-like 10-year lifetime would therefore assemble the mixture in one
direction only. An Archean-like lifetime of 10⁴ years assembles it in
neither.

## 2. Lifeless start

**Start.** Donor-only hydrogen (300 Pa), abiotic methane (r = 5.4 × 10⁻⁴,
T = 283.2 K) and acetate at local balance. Both groups start at the
invasion dose (10⁻¹² g L⁻¹, about 1.5 × 10¹⁷ global cells), with fixed
products, τ = 0 and a run of 100 kyr.

| f | first event | at census | endpoint | uncensored endpoint |
|---|---|---|---|---|
| 0 | acetogens below one cell at 54.5 yr | removed at 60 yr, 283.61 K | M alone, 273.517 K | both (10^25.7 and 10^25.9 cells) |
| 0.5 | acetogens below one cell at 52.9 yr | removed at 60 yr, 283.66 K | M alone, 273.517 K | both (10^25.9 and 10^25.7) |
| 0.9 | acetogens below one cell at 51.7 yr | removed at 60 yr, 283.71 K | M alone, 273.517 K | acetogens alone |

**Sequence.** Acetogens grow faster at first on abundant hydrogen (72 against
27 per year) and lead for about a decade. Once hydrogen falls, the
methanogens' lower requirement at 283 K decides. The uncensored f = 0 and
0.5 runs reach the mixture only by recovering from about 10⁻⁴³⁰⁰⁰ cells.
That is the artefact the census rule removes.

**Integrators.** The production integrator needed a 1-year step limit: at its
default of 50 years, the acetate-source certificate failed during the
initial bloom. The plain population integrator, with the same ten-year census over the
first 1,000 years, gives the same removals:
- every removal at 60 years;
- temperatures identical to within 10⁻⁸ K;
- the same removed-cell counts.

Its 100-kyr uncensored traces are the source of the "uncensored endpoint"
column
([`issue3_lifeless.json`](../../models/haze_world/review/issue3_lifeless.json)).
It failed (LSODA) on the long single-group stretch after removal, so the
100-kyr census endpoint rests on the production integrator alone.

**Dependence on the bridge.** The lifeless temperature comes from the
assumed low-methane bridge to 283 K. If a lifeless world lay below T\*,
acetogens would win instead. Either way one group excludes the other before
methane can move the climate, so the result does not depend on the side.

## 3. Refuges

> Taken together, the three refuge designs show what assembly needs: the
> displaced group must survive somewhere until the climate crosses the switch
> temperature.
>
> - **Buffered refuges (C09).** Two small habitats held at fixed temperatures
>   either side of T\* (2% of area each, at 278 and 286 K) give each group a
>   place where it wins throughout the transient. In all 12 key runs (f = 0
>   and 0.5, exchange 10⁻⁹–10⁻³ per year) both histories then reach the same
>   mixed state at 281.535 K.
> - **One buffered refuge.** A single buffered refuge protects only one
>   side. At f = 0 it can lose the invader to the climate's overshoot.
> - **Climate-tracking refuges (C08).** These move with the surface, which
>   swings by up to 24 K during an invasion. A refuge that favours
>   the loser at the start can stop favouring it, or leave the model's
>   273–303 K support. All 38 completed runs whose refuge protected the loser
>   along the whole path kept it. The failures were runs where protection
>   lapsed, or runs that left the support (69 domain exits and 284 starts
>   with no supported equilibrium in the main matrix).
> - **The dropped spread invasions.** These failed earlier still: the
>   methanogen-only world sits at 273.5 K, so any spread above 0.5 K puts
>   habitats below the support floor.
>
> Neither C08 nor the dropped runs shows that tracking geometry cannot
> assemble the mixture. They show that this model cannot test it.
>
> **The minimal defensible statement.** In this model, a habitat that stays
> on the losing group's side of T\* until the climate crosses it lets the
> mixture assemble from either history.

**Immigration.** The finite-population stage (`finite-populations.md`,
`attained_endpoints.csv`, the 144-endpoint design behind C07) gives the same
result. With no refuge, any tested positive immigration restores two
materially active groups in all 72 runs at f = 0 and 0.5:

- the lowest rate is 0.1 cells per year against the one-cell floor;
- every guild supplies at least 1% of catabolic hydrogen use, with no
  immigration-supported sinks;
- endpoints lie at 281.29–281.57 K.

Zero immigration gives single groups in all 24. At f = 0.9 immigration
retains trace methanogens, but they are not material. The ledger has no
claim for this yet.

## 4. What the paper should say

The single-habitat failure is real and robust:

- both invasion directions;
- a lifeless start;
- three values of f;
- three thermal lags;
- methane lifetimes from 10⁴ down to 10³ years.

But its cause is narrow: the absorbing absence of a group that briefly drops
below one cell. Anything that keeps the loser alive somewhere until the
climate catches up assembles the regulator at T\*. That includes a buffered
refuge on its side of T\*, or a trickle of immigrants at 0.1 cells per year.
This answers the reader's question, so arrival order should stay as a
result with the assembly result beside it, not leave the abstract.

**Does habitat variation buy assembly as well as durability, at the price of
precision?** The evidence supports two parts of that idea, but not the
trade-off joining them.

- **What holds.** Habitat variation does both jobs in this model:
  - a spread with weak exchange buys durability (C55, C57, C60);
  - buffered refuges buy assembly (C09).
- **Where it overreaches.**
  1. **Different structures.** The two results use different habitat
     structures. Durability comes from offsets that track the surface;
     assembly comes from fixed-temperature heat baths. The tracking-spread
     invasions that would join them were never run, because of the support
     floor.
  2. **No precision price shown for assembly.** The buffered-refuge mixture
     settles at 281.535 K, the exact set point, because the 96% bulk is a
     uniform habitat holding both groups. Assembly there restores the exact,
     fragile state. Its τ_c was not computed, and those runs used
     instantaneous temperature (C09 limit).
  3. **Mismatched scales.** The spreads that buy a 30-year margin
     (0.02–0.06 K) are 100 times too narrow to shelter a group through an
     8–15 K transient.

  Immigration needs no habitat structure at all.

The unifying statement the evidence does support is about *persistence*, not
precision. Exact regulation is stable once formed. It forms only where the
losing group can persist while the slow climate catches up. And it lasts
only if control is imperfect.

## Proposals for Barry

**Abstract, last sentence.** Replace "In invasion simulations, arrival order
decided which group survived." with:

> In one uniform habitat the controlling mixture never assembled: the group
> favoured at the starting temperature removed the other within decades,
> long before methane could carry the climate across the switch. It
> assembled from either history when the losing group could persist, in a
> small habitat held on its side of the switch or through a trickle of
> immigrants.

**§3.6, retitled "Assembly needs somewhere to persist":**

> In all 24 invasions the invader drove the resident below one cell
> (figure 4*a*). This held in both directions, with fixed products and with
> feedback from both products, at f = 0 and 0.5, and at response times of 0,
> 3 and 30 years. Each run ended with the invader alone (figure 4*b*),
> including settings where the mixture is locally stable. The resident was
> lost within 10–70 years with fixed products, while temperature moved by
> 0.4 K at most. The climate needed 1,000–13,500 years to cross T\*.
> Starting from a lifeless planet with both groups rare gave the same
> failure: at 283 K methanogens removed acetogens within 60 years, at every
> f. Shortening the methane lifetime to 1,000 years changed no outcome. Only
> at 10 years did acetogen invasions assemble the mixture (ESM S11).
>
> The loss is permanent because a group below one cell cannot return. When
> the losing group could persist elsewhere, the mixture formed. Two small
> habitats held at 278 and 286 K, each 2% of the area, let both invasion
> directions reach the same mixed state at 281.535 K in all 12 key runs.
> Immigration of as little as 0.1 cells per year did the same at f = 0 and
> 0.5, with both groups materially active. Habitats that track the surface
> climate gave no comparable test: in this model most such runs left the
> physiological support, or lost protection during the transient (ESM S11).

**§4.5, retitled "Stability, assembly and persistence":**

> A stable mixture is not a mixture that forms. Competition between the two
> groups is fast, and the climate they regulate is slow, so in one uniform
> habitat the group favoured at the current temperature removes the other
> long before the climate can reverse its advantage. Arrival order, or the
> starting temperature, then fixes a single-group world. Incumbency usually
> favours the first arrival (Fukami 2015). Here the favoured arrival wins,
> whichever came first. What the regulator needs is persistence: somewhere
> the losing group survives while the climate catches up. A real planet has
> many candidates, from thermally buffered refuges to dispersal between
> regions. Persistence does not by itself give durable control. The mixture
> assembled by buffered refuges sits at the exact set point, and its margin
> against slow climate response was not tested. Assembly and durability
> have different requirements, and a regulating biosphere needs both.

**Figure 4.** Retitle it "Assembly needs somewhere to persist". Add a panel
(c), the buffered-refuge pair of opposite histories converging, from the
existing `paired_trajectories` data. Fig. 4b stays.

**Main message.** I recommend a third sentence, because the first claim needs
it:

> Microbes can hold a planet's temperature, but exact control fails when
> climate responds slowly. Imperfect control lasts far longer, and grows
> looser as habitat temperatures differ. The controlling community forms
> only where the losing group can persist while the climate catches up.

"Only where" is bounded by the evidence: it holds for every lifetime of
1,000 years or more, but a 10-year lifetime assembled it in one direction.
A safer form is "In one uniform habitat it never forms; it needs somewhere
the losing group can persist." Barry decides.

**Ledger.**

- New C65: the lifetime and lifeless checks.
- New C66: immigration assembly, from existing evidence.
- C09 is cited in the paper for the first time.
- A new ESM section S11 holds the lifetime table, the lifeless runs and the
  refuge reconciliation.

## Decision and application (15 November)

Barry, in chat: "Proposed wording is approved, carry on, and adopt the
persistence framing. 'Only where' is okay for the 25-word main message; the
longer and safer form can be stated elsewhere."

Applied in `d34a796`. Changes:

- **Main message:** a third sentence, "The controlling community forms only
  where the losing group can persist while the climate catches up", in
  01a, 01c and the draft's closing lines. The safer form is in §4.5.
- **Abstract:** the last sentence as proposed.
- **I5:** the third question asks whether, and how, the mixture assembles.
- **§2.6:** one sentence introducing the bounded checks and the persistence
  stages.
- **§3.6:** "Assembly needs somewhere to persist".
- **§4.5:** "Stability, assembly and persistence".
- **§4.6:** the conditions now cover the assembly runs.
- **Table 1:** the one-cell rule row is updated.
- **Figure 4:** retitled, with panel (c) from the buffered-refuge key runs
  (f = 0.5, exchange 10⁻⁶ yr⁻¹; raw records verified against the manifest).
- **ESM:** new S10 Assembly (tables S10a, S10b). Provenance is now S11.
- **Claims:** C08, C09, C65 and C66 are mapped to S10. The check gives
  0 errors.

Codex has not yet reviewed the checks or the applied text.
