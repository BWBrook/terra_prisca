# Step 3a: section abstracts

Claude (Opus 5.5), 12 November 2026. One abstract of 300 words or fewer per
section, in J R Soc Interface order: Introduction, Model, Results,
Discussion. Built from [Step 2](02-one-page-paper.md). Figure and table
numbers follow [Step 1c](01c-display-items.md).

Reviewed by Codex (GPT-6), 12 November 2026. Evidence: C05–C06, C52,
C54–C59; see the [Step 3a review](../../../docs/audits/paper-step3a-codex-review-2026-11-12.md).

---

## 1. Introduction

**Context.** Whether life regulates the climate of its planet has been
argued since the Gaia hypothesis. Daisyworld turned the question into a model
in which competing organisms hold temperature near their optimum (Watson &
Lovelock 1983). Daisyworld studies already show that relative timescales
affect regulation and thermal inertia can produce damped oscillations
(Weaver & Dyke 2012).

**Control theory.** Two results from control theory bear on biological
regulators:

- Stable integral feedback restores a set point after sustained forcing,
  as in cellular adaptation (Yi et al. 2000).
- In molecular models, weakening integral action can improve stability while
  allowing a steady error (Olsman et al. 2019); dilution can itself cause
  such errors (Qian & Del Vecchio 2018).

Slow environmental responses pose a further test of stability.

**The Archean case.** The early Earth faced a fainter Sun. Methane from
methanogens could have warmed it, and above a threshold methane forms an
organic haze that cools the surface (Arney et al. 2016). Acetogens compete
with methanogens for hydrogen. In our reference model, acetogens win below a
switch temperature and methanogens above it. On the haze-cooling branch:

- warming favours methanogens, whose methane thickens the haze and cools the
  surface;
- cooling favours acetogens, which divert hydrogen away from methane and warm
  the surface.

Seto & Akagi (2007) showed that two competitors with matched resource
requirements hold temperature exactly flat against forcing.

**The gap.** For this hydrogen-competition thermostat, we examine how slow
climate adjustment changes stability and what greater durability costs in
precision.

**This study.** We ask three questions, with hypotheses developed in stages
during the work:

1. Does exact regulation survive a slow climate response?
2. How much precision buys how much durability?
3. Does arrival order decide which group persists?

We answer them with stability analysis, tuned loosenings and invasion
simulations.

## 2. Model

**Community.** One acetogen and one hydrogen-consuming methanogen compete for
dissolved hydrogen in a well-mixed habitat (figure 1*a*).

- **Growth:** depends on hydrogen and temperature. Kinetics are transferred
  from cultured strains, with the acetogen benchmarked against
  *Acetobacterium woodii*.
- **Physiology:** extends from the lowest measurement, 277 K, down to 273 K.
- **Hydrogen budget:** open, with a fixed supply Φ and exchange with the
  atmosphere.
- **Acetate:** a fraction f is recycled into methane.

**Climate.** Atmospheric methane balances microbial supply and removal over
an assumed 10,000-year lifetime. Surface
temperature follows the haze response of Arney et al. (2016), case B, with a
response time τ:

τ dT/dt = T_clim(methane) − T

We compare fixed product activities with feedback from methane, acetate or
both. A dial κ turns up acetate feedback while methane activity stays fixed.

**Habitat spread.** Habitats are offset in temperature by up to ±σ and
exchange cells at rate d. They are resolved by adaptive quadrature that
passes a doubling test, and checked by an independent method.

**Analyses:**

- **Steady states,** followed by continuation, and their local sensitivity
  S = dT*/d ln Φ, from the equilibrium equations.
- **Critical response time** τ_c: the first loss of stability as τ grows. It
  comes from the linear stability equations. We search up to 10⁴ years;
  stability through that ceiling gives a lower bound.
- **Kicked trajectories** at chosen τ.
- **Invasions:** a rare invader enters a resident world in one closed
  habitat. Populations are counted every ten years, and a group is extinct
  below one cell.

**Verification.**

- Dated specifications preserve each stage's predictions and criteria.
- Claude and Codex cross-checked the reported findings.
- A claims ledger links findings to evidence, commits and reproduction
  commands.
- Table S1 will list parameters; code and outputs will receive a Zenodo DOI.

## 3. Results

**3.1 Perfect control** (figure 1*b*,*c*). The two groups coexist where their
hydrogen requirements match, at 281.5 K in the reference case. Changes in
supply shift the balance between the groups and leave temperature unchanged:
S = 0, the plateau mechanism of Seto & Akagi (2007). Growth-rate differences
keep shifting the balance between the groups. Near coexistence this acts
like integral feedback.

**3.2 Perfect control is fragile** (figure 2). We found 42 exactly holding
states:

- six are unstable even with an instant climate response;
- the other 36 first lose stability at response times of about 7 years or
  less.

The reference state loses stability at 0.15 years.

- **At a 1-year response time,** both groups persist for 30,000 years while
  temperature swings span about 1.3 K.
- **At 10–100 years,** the calculations reach populations below one cell.

**3.3 Durability costs a little precision** (figure 3). Acetate slowing its
own producers, and spread in habitat temperature, each let temperature
follow supply slightly. Near the perfect-control limit, the tested branches
show a smooth rise in the critical response time.

- **On four tuned branches,** local sensitivities of 0.07–0.32 K per e-fold buy
  tolerance of a 30-year response.
- **Resolved spread communities,** at 1–2 K per e-fold, tolerate centuries.
- **The 122 initially stable graded states in the earlier on/off comparison**
  have sensitivities of at least 0.59 K per e-fold and margins of at least
  331 years; 113 have only lower bounds at the 10⁴-year search ceiling.

A proposed range of power-law slopes and an oscillation-based approximation
each had counterexamples (ESM).

**3.4 Arrival order decides the survivor** (figure 4). In all 24 invasions,
the invader drove the resident below one cell, including where a stable
mixture exists. Arrival order chose the surviving group.

## 4. Discussion

**The trade-off.** This microbial thermostat can hold temperature exactly, and
in doing so it inherits the weakness of integral control: sensitivity to
delay. Graded feedback relaxes the exactness. A residual sensitivity of a
fraction of a kelvin per e-fold of supply then buys tolerance of decades,
and 1–2 K buys centuries. This parallels precision–stability trade-offs in
molecular circuits (Qian & Del Vecchio 2018; Olsman et al. 2019).

**Relation to earlier work.** Seto & Akagi (2007) found the plateau. We add:

- thermal-response stability margins in a haze-climate model;
- the local sensitivity cost of graded feedback;
- finite-population resident–invader assembly tests.

Archean ecosystem–climate models (Kharecha et al. 2005; Ozaki et al. 2018;
Sauterey et al. 2020) provide context for hydrogen cycling.

**The Archean.** Acetate feedback and habitat variation provide candidate
routes to graded regulation on early Earth. Their strength sets the balance
between precision and durability in the model.

**Assembly.** Arrival order chose the survivor even where a stable mixture
exists. Stability and assembly are therefore separate problems.

**Limitations.** These results come from a conditional model. Its conditions
are listed in table 1:

- the switch depends on culture transfers and the assumed cell-loss rate;
- regulation needs the two hydrogen pathways to yield different amounts of
  methane;
- physiology below 277 K is a continuation;
- the costs are local slopes on four branches;
- stability is local to each steady state;
- invasions use one closed habitat with a one-cell rule.

**Tests and generality.** Measuring sensitivity and response time together
would test the trade-off in other microbial feedbacks and mesocosms. The
analysis offers a method for comparing those systems' stability and precision.

**Conclusion.** Microbes can hold a planet's temperature steady, but perfect
control breaks down when the climate responds slowly. Slightly imperfect
control is far more durable.
