# Can microbes hold a planet's temperature steady when its climate is slow to respond?

Barry W. Brook (University of Tasmania), with Claude (Anthropic), Codex (OpenAI) and Gemini (Google). Draft of 25 November 2026; a plain-language summary of a living research repository, <https://github.com/BWBrook/terra_prisca>.

<div id="figures"></div>

![*Graphical abstract.* (1) Hydrogen feeds two competing groups; temperature decides which wins, and so how much cooling haze forms. (2) Together they hold temperature at the set point over a doubling of supply[]{.C06}. (3) Exact control loses stability within years of climate delay; a small drift buys decades or more[]{.C54}[]{.C57}. (4) Refuges let both groups reach the set point[]{.C52}[]{.C09}.](../figures/graphical_abstract.pdf){#fig-brief width=100%}

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
principle [@watson1983BiologicalHomeostasisGlobal; @seto2007CoexistenceIntroducingRegulation]. Whether it survives a
slowly responding climate was untested.

## What we did

- Built a model of two groups of microbes competing for hydrogen, coupled to a
  published estimate of how a methane haze sets temperature on a
  2.7-billion-year-old Earth [@arney2016PaleOrangeDot].
- Measured how slowly the climate can respond before each regulated state
  loses stability, across [42]{.C54} exactly regulating states, [122]{.C54}
  loosely regulating ones and four tuned families of states between them.
- Ran [24]{.C52} invasions with populations counted in whole cells, so that a
  group can die out, and repeated them with small sheltered habitats and with
  a trickle of immigrants.
- Pressure-tested the result five ways, from habitat temperatures to the
  size of the hydrogen supply.

## What we found

1. **Competition can hold temperature exactly, but only if some hydrogen
   leaves for good.** One group (methanogens) turns hydrogen into methane and
   cools the planet through haze; the other (acetogens) turns it into acetate
   instead. Below [281.5]{.C06} K the acetogens win and the planet warms;
   above it the methanogens win and it cools. With half the acetate
   eventually becoming methane, temperature stays at the set point while the
   hydrogen supply changes by a factor of [2.0]{.C67}. If all of it returned
   as methane, the lever would vanish. How much escaped on the early Earth is
   unknown.
2. **Exact control is fragile.** With no acetate recycled, the reference
   state loses stability once the climate takes more than [0.15]{.C63} years
   to respond, and with half recycled, about a year[]{.C63}. Every stable exact state
   we found lost stability within [7]{.C54} years. Past that limit the regulator swings widely
   or a population crashes.
3. **Slightly imperfect control lasts far longer.** Where acetate slows its
   own producers, or habitats differ slightly in temperature, temperature
   drifts as the supply changes. A drift of [0.07]{.C57} to [0.31]{.C57} K
   for each *e-fold* (a 2.7-fold change) of supply let the regulator tolerate
   a 30-year climate response, and looser control tolerated centuries[]{.C61}.
4. **The regulating community does not form in a single uniform habitat.**
   In all [24]{.C52} closed invasions the newcomer ended alone. The group
   favoured at the starting temperature removed the other within decades[]{.C65},
   while the climate needed more than a thousand years to cross the set
   point. Two small sheltered habitats, or as little as [0.1]{.C66} immigrant
   cells per year, let both groups persist and the mixture form at the set
   point. How well that mixture tolerates a slow climate was not tested.
5. **The hydrogen bill is large.** At the assumed ten-thousand-year methane
   lifetime, the model needs about [401]{.C69} trillion moles of hydrogen a
   year, far more than volcanoes and rocks are thought to have supplied. Fermentation of organic
   matter is one possible source, but it also makes acetate, which would
   narrow the range of supply the regulator can handle[]{.C70}.

## What it means

In this model a living thermostat can be exact or durable, not both. If
microbes did help hold the early Earth's temperature, the version that
survives a slow climate holds temperature within a band rather than at a
point, and in our reference runs it formed only where the losing group had
somewhere to wait. The
model's main conditions can be tested today: acetate turnover, the share of
acetate that escapes methane, and the spread of habitat temperatures in
modern microbial mats.

## How this work was done

Barry W. Brook led the project and decided its questions. Claude (Opus 5.5)
specified and reviewed the analyses and drafted the paper; Codex (GPT-6)
wrote the model code and independently audited each stage. Claude Fable 5.2,
as project adviser, posed the five pressure tests, and Gemini 4 Carbon
reviewed the draft. Every number here is checked against the project's
public claims ledger.

## Sources
