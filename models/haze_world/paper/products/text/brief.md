# Can microbes hold a planet's temperature steady when its climate is slow to respond?

Barry W. Brook (University of Tasmania), with Claude (Anthropic), Codex (OpenAI) and Gemini (Google). Draft of 25 November 2026; a plain-language summary of a living research repository, <https://github.com/BWBrook/terra_prisca>.

<div id="figures"></div>

![*Graphical abstract.* (1) Hydrogen feeds two competing groups; near the switch, temperature decides which wins and so how much cooling haze forms. (2) Together they hold temperature at the set point over a doubling of supply[]{.C06}[]{.C67}. (3) The 36 original exact states lose stability within about seven years of climate delay; a small drift buys decades or more[]{.C54}[]{.C57}. (4) Two refuges let both groups persist and reach the set point[]{.C09}.](../figures/graphical_abstract.pdf){#fig-brief width=100%}

## The puzzle

Four billion years ago the Sun shone markedly fainter than today, yet the
young Earth kept liquid water [@sagan1972EarthMarsEvolution; @feulner2012FaintYoungSun]. One idea is
that life helped. Microbes that made methane may have thickened an organic
haze, which cools the surface, while warmer temperatures favoured those same
microbes. Could such a living loop act as a thermostat and hold the planet
near a *set point*, the temperature a regulator returns to?

## Why it is hard

Microbial populations change within years. Climate does not: oceans store
heat, so the surface takes years to centuries to catch up. A regulator that acts fast on a slow system can overshoot, the way a
shower swings between too hot and too cold when the water takes a while to
reach you. Earlier models showed that a living thermostat is possible in
principle [@watson1983BiologicalHomeostasisGlobal; @seto2007CoexistenceIntroducingRegulation]. We asked whether
this hydrogen-competition thermostat survives a slow climate response.

## What we did

- Built a model of two groups of microbes competing for hydrogen, coupled to a
  published estimate of how a methane haze sets temperature on a
  2.7-billion-year-old Earth [@arney2016PaleOrangeDot].
- Measured how slowly the climate can respond before each regulated state
  loses stability, across [42]{.C54} exactly regulating states, [122]{.C54}
  loosely regulating ones and four tuned families of states between them.
- Ran [24]{.C52} invasions in which a group below one cell, checked every ten
  years, dies out; then ran separate tests with small sheltered habitats and
  with a trickle of immigrants.

## What we found

1. **Competition can hold temperature exactly, but only if some hydrogen
   leaves for good.** One group (methanogens) turns hydrogen into methane and
   cools the planet through haze; the other (acetogens) turns it into acetate
   instead. Near the switch, on the haze-cooling branch, the acetogens win
   below [281.5]{.C06} K and the planet warms;
   above it the methanogens win and it cools. With half the acetate
   eventually becoming methane, temperature stays at the set point while the
   hydrogen supply changes by a factor of [2.0]{.C67}. If both the acetate and
   the lost biomass returned as methane, the two groups would deliver the same
   yield and the lever would vanish.
2. **Exact control is fragile.** With no acetate recycled, the reference
   state loses stability once the climate takes more than [0.15]{.C63} years
   to respond, and with half recycled, about a year[]{.C63}. Every stable exact state
   in our original survey lost stability within about [7]{.C54} years; recycling
   all the acetate, with biomass exported, let one tolerate 30 years, but only
   near the edge of a supply range about 5% wide[]{.C67}. In disturbance runs
   past the limit, the regulator swung widely or a population crashed.
3. **Slightly imperfect control lasts far longer.** Where acetate slows its
   own producers, or habitats differ slightly in temperature, temperature
   drifts as the supply changes. In four tested cases, a local slope of
   [0.07]{.C57} to [0.31]{.C57} K per *e-fold* (2.7-fold step) of supply,
   measured over small changes, let the regulator tolerate a 30-year climate response, and some
   habitat-spread communities tolerated centuries[]{.C61}.
4. **In our reference runs the community did not form in one uniform habitat.**
   In all [24]{.C52} closed invasions the newcomer ended alone. In four
   simplified controls it removed the resident within decades[]{.C65}, while
   atmospheric methane needed over a thousand years to bring temperature across
   the set point. Two small
   sheltered habitats let the mixture form at the set point[]{.C09}; as little
   as [0.1]{.C66} immigrant cells a year kept both groups active near it, with
   none or half of the acetate recycled.
5. **The hydrogen bill is large.** At the assumed ten-thousand-year methane
   lifetime, the model's gross supply is about [401]{.C69} trillion moles of hydrogen a
   year, far above published base cases for fresh hydrogen from volcanoes and
   rocks. Fermentation is one possible source; if it supplied all of it and
   half of all acetate became methane, the workable supply range would
   narrow[]{.C70}.

## What it means

In this model a living thermostat that holds temperature exactly over a wide
range of supply is fragile; control that tolerates a slow climate lets
temperature drift slightly or works over only a narrow range of supply. In our reference runs the regulating mixture formed
only where the losing group had somewhere to wait. Two things remain
unknown: how much acetate escaped methane on the early Earth, and how well a
mixture formed this way tolerates a slow climate. The model's main conditions can be tested today: acetate turnover, the share of
acetate that escapes methane, and the spread of habitat temperatures in
modern microbial mats.

## How this work was done

Barry W. Brook led the project. Claude (Opus 5.5) wrote the stage
specifications, reviewed each stage and drafted the paper; Codex (GPT-6) built
the model code, ran the independent audits and reviewed each step. Claude Fable 5.2,
as project adviser, posed five pressure-test questions, and Gemini 4 Carbon
reviewed the draft. Every number here is checked against the project's
public claims ledger.

## Sources
