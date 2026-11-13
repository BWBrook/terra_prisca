# Step 3b: paragraph abstracts

Claude (Opus 5.5), 12 November 2026. Built from [Step 3a](03a-section-abstracts.md).
Reviewed and revised by Codex (GPT-6), 13 November 2026.
The [review record](../../../docs/audits/paper-step3b-codex-review-2026-11-13.md)
maps the corrections to the model, claims and sources.

Each section has three parts:

1. a paragraph plan, one sentence per paragraph;
2. a check that the plan covers the section abstract;
3. the paragraph abstracts, of 3–4 sentences each.

**Reference tags.** Square brackets mark the references each paragraph will
cite.

- An author–year in a tag has a DOI checked against Crossref, listed at the
  end of this file.
- `[find: …]` marks a citation still to be sourced.

---

## 1. Introduction (five paragraphs)

### Plan

1. Whether life regulates its planet's climate is an old question, and
   Daisyworld made it testable.
2. Molecular control models connect set-point holding, stability and steady
   error.
3. The hazy early Earth motivates a two-group hydrogen-competition model.
4. Resource competition can hold temperature flat, motivating tests of its
   climate-response stability and precision cost.
5. We ask three questions and answer them with stability analysis, tuned
   loosenings and invasion simulations.

### Coverage check

| Section-abstract item | Paragraph |
|---|---|
| Gaia, Daisyworld | I1 |
| Weaver & Dyke timescales and oscillations | I1 |
| Integral feedback, steady error, dilution | I2 |
| Faint Sun, methane, haze, hydrogen competition | I3 |
| Switch and loop | I4 |
| Seto & Akagi plateau | I4 |
| Gap | I4 |
| Questions and approach | I5 |

### Paragraph abstracts

**I1.** Whether life regulates the climate of its planet has been argued since
the Gaia hypothesis [Lovelock & Margulis 1974]. Daisyworld made the idea
testable: two kinds of daisy, each changing the planet's reflectivity, hold
temperature near their growth optimum [Watson & Lovelock 1983]. The relative
pace of biological and climate adjustment matters: thermal inertia can
produce damped oscillations in Daisyworld [Weaver & Dyke 2012].

**I2.** Control theory explains how a biological system can hold a set point
exactly. A stable integral-feedback loop accumulates error and restores a
set point after sustained forcing; bacteria use it in chemotaxis [Yi et al.
2000; Khammash 2021]. In molecular circuits, weakening the integral action
can improve stability at the price of a steady error [Olsman et al. 2019], and
dilution introduces such error [Qian & Del Vecchio 2018]. A slow
environmental response is a further test of any such regulator.

**I3.** The early Earth received about a quarter less sunlight than today, yet
stayed warm enough for liquid water [Sagan & Mullen 1972; Feulner 2012].
Methane from methanogens could have contributed greenhouse warming. Above a threshold,
methane forms an organic haze that cools the surface instead [Haqq-Misra et
al. 2008; Arney et al. 2016]. Acetogens compete with methanogens for the same
hydrogen and convert it to acetate, and temperature shifts the balance
between them [Kotsyurbenko et al. 2001; Fu et al. 2019].

**I4.** On the haze-cooling branch the reference community forms a restoring
loop. Warming
favours methanogens, whose methane thickens the haze and cools the surface.
Cooling favours acetogens, which divert hydrogen away from methane and warm
the surface. Seto & Akagi found the coexistence plateau in a generic
competition model [Seto & Akagi 2007]; here we ask how climate response time
changes stability and what durability costs.

**I5.** We couple transferred microbial kinetics to a published haze response
with an explicit climate response time. We ask whether exact holding
survives a slow climate response, what durability costs in temperature
precision, and whether arrival order selects the survivor. We answer with
stability analysis, two tunable departures from exact control, and invasion
simulations.

---

## 2. Model (seven paragraphs)

### Plan

1. Two microbial groups grow on dissolved hydrogen, with temperature-dependent
   kinetics taken from cultured strains.
2. An open hydrogen budget feeds the community, and part of the acetate is
   recycled into methane.
3. Methane sets surface temperature through a published haze climate, which
   responds over a set time.
4. Two tunable features loosen exact control: acetate slowing its producers,
   and spread in habitat temperature.
5. Each steady state is described by temperature, local supply sensitivity,
   and its first loss of stability as climate response slows.
6. Invasion simulations test whether arrival order decides the surviving
   group.
7. Staged predictions, two-agent cross-checking and a claims ledger document
   the reported findings and their reproduction.

### Coverage check

| Section-abstract item | Paragraph |
|---|---|
| Growth, strains, *A. woodii*, physiology continuation | M1 |
| Hydrogen budget, f | M2 |
| Methane lifetime, Arney case B, τ equation | M3 |
| Product-chemistry cases, κ dial, habitat spread σ, d, quadrature | M4 |
| S, τ_c, search ceiling, kicked trajectories | M5 |
| Invasions, census rule | M6 |
| Verification, ledger, Zenodo | M7 |

### Paragraph abstracts

**M1.** One acetogen and one hydrogen-consuming methanogen compete for
dissolved hydrogen in a well-mixed habitat (figure 1*a*). Growth rises with
hydrogen and depends on temperature through kinetics transferred from
cultured strains [Kotsyurbenko et al. 2001]. The acetogen is benchmarked against *Acetobacterium
woodii* [Peters et al. 1998]. Maintenance changes with temperature using a
transferred correlation [Tijhuis et al. 1993], and physiology is continued from the
lowest measurement, 277 K, down to 273 K.

**M2.** Hydrogen enters at a fixed supply rate Φ and exchanges with the
atmosphere. Each group draws it down for metabolism and growth. Acetate
enters a pool; a fraction f is recycled into methane and the rest leaves
that route. Table 1 lists the budget assumptions, including material
retained in biomass and atmospheric hydrogen up to 100 Pa.

**M3.** Atmospheric methane balances microbial production against removal over
an assumed lifetime of 10,000 years. The climate temperature T_clim then
follows the haze response of Arney et al. (2016), case B [Arney et al. 2016].
Surface temperature approaches it over a response time τ:

τ dT/dt = T_clim − T

Here τ stands in for ocean heat storage, which spans a fast response of
years and a slow one of centuries [Held et al. 2010].

**M4.** Two features loosen exact control, each turned up from zero. In the
first, acetate accumulation raises the hydrogen the acetogens need, and a
dial κ sets its strength while methane activity stays fixed; we also compare
fixed products and feedback from methane, acetate or both. In the second,
habitats differ in temperature by up to ±σ and exchange cells at rate d.
Adaptive quadrature resolves the habitat spread, passes a doubling test, and
agrees with an independent method.

**M5.** For each steady state we compute its temperature T\* and its local
sensitivity S = dT\*/d ln Φ, the change in temperature per e-fold change in
supply. The critical response time τ_c is the first τ at which the steady
state loses stability, found from the linearised equations. We search up to
10⁴ years and report stability through that ceiling as a lower bound.
Kicked trajectories at chosen τ show what instability does.

**M6.** Invasions start from one group established alone and the other
introduced at low density, in one closed habitat. Populations are counted
every ten years, and a group with less than one cell in total is removed.
This rule, our choice, fixes when a loss becomes permanent. It stops a group
recovering from a vanishing fraction of a cell, an artefact of continuous
models [Mollison 1991].

**M7.** Dated specifications preserve the staged predictions and their pass
criteria. Claude (Opus 5.5) and Codex (GPT-6) built and cross-checked the
reported findings. A claims ledger links findings to evidence, commits and
reproduction commands. Parameters (table S1), code and outputs will be
archived with a Zenodo DOI.

---

## 3. Results (six paragraphs)

### Plan

1. With fixed products, the two groups hold temperature at the switch within
   the coexistence supply range.
2. Every exactly holding state is unstable or loses stability within a few
   years of climate response time.
3. Once unstable, the regulator either swings widely or lets a population
   crash.
4. Allowing a small temperature response to supply raises the stability
   margin smoothly near the exact limit on the tested branches.
5. Counterexamples to a proposed slope range and an oscillation-based
   approximation support reporting the trade-off branch by branch.
6. Arrival order decides the surviving group, even where a stable mixture
   exists.

### Coverage check

| Section-abstract item | Paragraph |
|---|---|
| 3.1 plateau, 281.5 K, integral interpretation | R1 |
| 3.2: 42 states, six and 36, 0.15 yr | R2 |
| 3.2: 1-yr oscillation, 10–100-yr bottlenecks | R3 |
| 3.3: dials, 0.07–0.32 K, 1–2 K, on/off comparison | R4 |
| 3.3: failed forms (C56, C58) | R5 |
| 3.4: 24 invasions | R6 |

### Paragraph abstracts

**R1. Perfect control** (figure 1*b*,*c*). With fixed product activities, the
two groups coexist only where their hydrogen requirements match, at 281.5 K
in the reference case. A
change in supply within the coexistence range shifts the balance between
them and leaves temperature unchanged (S = 0), as in Seto & Akagi's plateau
[Seto & Akagi 2007].
Growth-rate differences keep shifting that balance, which near coexistence
acts like integral feedback [Yi et al. 2000].

**R2. Fragility** (figure 3*a*, left edge). We found 42 exactly holding states
across chemistries, recycling fractions and supplies. Six are unstable even
with an instant climate response. The other 36 first lose stability at
response times of about 7 years or less. The reference state loses stability
at 0.15 years.

**R3. Swings and crashes** (figure 2). At a 1-year response time, the
reference regulator oscillates: both groups persist for 30,000 years while
temperature swings span about 1.3 K. At 10–100 years, the calculated
populations fall below one cell. An unstable regulator can therefore keep
working with wide swings, or let a population crash.

**R4. The price of durability** (figure 3). Each loosening lets temperature
follow supply slightly, and near the exact limit the tested branches show
a smooth rise in the critical response time. On four tuned branches, local sensitivities of
0.07–0.32 K per e-fold buy tolerance of a 30-year response. Resolved spread
communities at 1–2 K per e-fold tolerate centuries. The earlier on/off
comparison's 122 initially stable graded states have sensitivities of at
least 0.59 K per e-fold and margins of at least 331 years; 113 have only
lower bounds at the 10⁴-year search ceiling.

**R5. The trade-off is branch-specific** (ESM). Before the tuned runs we
proposed a range of power-law slopes for each branch and an approximation
from the oscillation period and damping time. One chemical branch fell
outside the slope range. The approximation passed the initial eligible grid
and failed at two refinement points, so the price of durability is reported
branch by branch.

**R6. Arrival order** (figure 4). In all 24 invasions, the invader drove the
resident below one cell. We compared fixed products and feedback from both
products, at two acetate-recycling fractions and response times of 0, 3 and
30 years. The invader alone persisted in each direction, including settings
where a stable mixture exists. Arrival order chose the surviving group.

---

## 4. Discussion (seven paragraphs)

### Plan

1. Exact holding is fragile to slow climate response in this model.
2. A small loss of precision buys large gains in durability, paralleling
   molecular circuits.
3. Relative to earlier work, the new results are the stability margins, the
   cost of loosening, and the assembly tests.
4. Acetate feedback and habitat variation are candidate routes to graded
   regulation on the early Earth.
5. Arrival order shows that stability and assembly are separate problems.
6. The model's conditions, gathered in one place.
7. Measuring sensitivity and response time together would test the
   trade-off elsewhere; then the closing message.

### Coverage check

| Section-abstract item | Paragraph |
|---|---|
| Inherits integral-control fragility | D1 |
| Graded feedback buys durability; molecular parallel | D2 |
| Relation to earlier work, hydrogen-cycling context | D3 |
| Archean candidate routes | D4 |
| Assembly | D5 |
| Limitations | D6 |
| Tests and generality; conclusion | D7 |

The plan has seven paragraphs: splitting fragility (D1) from its price (D2)
gives each paragraph one message.

### Paragraph abstracts

**D1. Exactness brings fragility.** Near coexistence, competition acts like
integral feedback and holds temperature exactly. Integral control is
sensitive to delay, and a slowly responding climate supplies one [find:
control-theory source on integral action and delay]. Every exact state that
starts stable loses stability at a response time of about seven years or
less. Past that point the regulator swings widely or a population
crashes.

**D2. A small price for durability.** Graded feedback relaxes the exactness.
A residual sensitivity of a fraction of a kelvin per e-fold of supply buys
tolerance of decades, and 1–2 K buys centuries. This parallels the
precision–stability trade-offs of molecular circuits [Olsman et al. 2019;
Qian & Del Vecchio 2018; Khammash 2021].

**D3. What is new.** Seto & Akagi found the plateau [Seto & Akagi 2007], and
Weaver & Dyke showed that thermal inertia can produce damped oscillations in
Daisyworld [Weaver & Dyke 2012]. We add three things for a hydrogen-competition regulator in a
haze climate: its stability margins under a slow climate, the sensitivity
cost of graded feedback, and finite-population invasion tests. Archean
ecosystem–climate models supply the wider context for hydrogen cycling
[Kharecha et al. 2005; Ozaki et al. 2018; Sauterey et al. 2020].

**D4. The early Earth.** Acetate feedback and variation in habitat
temperature are candidate routes to graded regulation on the hazy early
Earth. Their strengths set where the regulator sits between precision and
durability. In modern mats, hydrogen levels vary steeply with depth and
time of day, and far more fixed carbon leaves as organic acids than as
methane [Hoehler et al. 2001; Bebout et al. 2004]. Measuring acetate stocks
and turnover, their effect on hydrogen requirements, and habitat
temperatures and cell exchange would test the two routes.

**D5. Stability and assembly are separate.** Arrival order chose the
survivor in every tested invasion, including settings where a mixture of
both groups is stable once formed. This separates the assembly of a
regulator from its stability. A familiar arrival-order effect is incumbency
advantage, which favours the first arrival [Fukami 2015]. Here the late
arriver won all 24 invasions, and each run ended with one group.

**D6. Conditions.** Table 1 lists the assumptions of this conditional model.
The switch depends on culture transfers and an assumed cell-loss rate;
regulation requires different methane yields from the two hydrogen
pathways. Physiology is extended below 277 K, costs are local slopes on four
branches, and stability is local to each steady state. A crash is read at
the first fall below one cell, and invasions use one closed habitat with the
one-cell rule applied every ten years.

**D7. Tests and generality.** Any population–environment feedback with a slow
environment invites the same two measurements: how far the regulated
variable drifts with forcing, and how slowly the environment responds.
Mesocosm experiments and biogeochemical models could test the trade-off with
our delay-margin analysis. Microbes can hold a planet's temperature steady,
but perfect control breaks down when the climate responds slowly; slightly
imperfect control is far more durable.

---

## Reference keys (Crossref-checked)

| Key | DOI |
|---|---|
| Lovelock & Margulis 1974 | 10.1111/j.2153-3490.1974.tb01946.x |
| Watson & Lovelock 1983 | 10.1111/j.1600-0889.1983.tb00031.x |
| Weaver & Dyke 2012 | 10.1016/j.jtbi.2012.07.034 |
| Yi et al. 2000 | 10.1073/pnas.97.9.4649 |
| Khammash 2021 | 10.1016/j.cels.2021.05.020 |
| Olsman et al. 2019 | 10.1016/j.cels.2019.06.001 |
| Qian & Del Vecchio 2018 | 10.1098/rsif.2017.0902 |
| Sagan & Mullen 1972 | 10.1126/science.177.4043.52 |
| Feulner 2012 | 10.1029/2011RG000375 |
| Haqq-Misra et al. 2008 | 10.1089/ast.2007.0197 |
| Arney et al. 2016 | 10.1089/ast.2015.1422 |
| Kotsyurbenko et al. 2001 | 10.1111/j.1574-6941.2001.tb00893.x |
| Fu et al. 2019 | 10.3389/fmicb.2019.02418 |
| Seto & Akagi 2007 | 10.1016/j.jtbi.2007.05.013 |
| Peters et al. 1998 | 10.1111/j.1574-6941.1998.tb00516.x |
| Tijhuis et al. 1993 | 10.1002/bit.260420415 |
| Kharecha et al. 2005 | 10.1111/j.1472-4669.2005.00049.x |
| Ozaki et al. 2018 | 10.1038/s41561-017-0031-2 |
| Sauterey et al. 2020 | 10.1038/s41467-020-16374-7 |
| Fukami 2015 | 10.1146/annurev-ecolsys-110411-160340 |
| Held et al. 2010 | 10.1175/2009JCLI3466.1 |
| Bebout et al. 2004 | 10.1111/j.1472-4677.2004.00024.x |
| Hoehler et al. 2001 | 10.1038/35085554 |
| Mollison 1991 | 10.1016/0025-5564(91)90009-8 |

**Reading status:** see [03b-reference-notes.md](03b-reference-notes.md).
