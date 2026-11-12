# Step 3a: section abstracts

Claude (Opus 5.5), 12 November 2026. One abstract of 300 words or fewer per
section, in J R Soc Interface order: Introduction, Model, Results,
Discussion. Built from [Step 2](02-one-page-paper.md). Figure and table
numbers follow [Step 1c](01c-display-items.md).

---

## 1. Introduction

**Context.** Whether life regulates the climate of its planet has been
argued since the Gaia hypothesis. Daisyworld turned the question into a model
in which competing organisms hold temperature near their optimum (Watson &
Lovelock 1983). Most analyses study regulation at equilibrium. Yet climates respond slowly,
and relative timescales govern whether self-regulation emerges (Weaver & Dyke
2012).

**Control theory.** Two results from control theory bear on biological
regulators:

- Integral feedback holds a set point exactly against a sustained
  disturbance, and cells use it for exact adaptation (Yi et al. 2000).
- Integral feedback trades precision against robustness, and leaky
  integration relaxes exactness (Qian & Del Vecchio 2018; Olsman et al.
  2019).

Delay is the classic way to destabilise such a controller.

**The Archean case.** The early Earth faced a fainter Sun. Methane from
methanogens could have warmed it, and above a threshold methane forms an
organic haze that cools the surface (Arney et al. 2016). Acetogens compete
with methanogens for the same hydrogen and grow better in the cold. On the
haze branch, their competition forms a closed loop:

- warming favours methanogens, whose methane thickens the haze and cools the
  surface;
- cooling favours acetogens, which divert hydrogen away from methane.

Seto & Akagi (2007) showed that two competitors with matched resource
requirements hold temperature exactly flat against forcing.

**The gap.** Two things remain open: how such a thermostat behaves when the
climate responds slowly, and what a durable version costs in precision.

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

**Climate.** Methane production sets the atmospheric methane level. Surface
temperature follows the haze response of Arney et al. (2016), case B, with a
response time τ:

τ dT/dt = T_clim(methane) − T

Product chemistry has three named variants: fixed product activities, methane
feedback, and acetate feedback. A dial κ moves continuously from fixed
chemistry to full acetate feedback.

**Habitat spread.** Habitats are offset in temperature by up to ±σ and
exchange cells at rate d. They are resolved by adaptive quadrature that
passes a doubling test, and checked by an independent method.

**Analyses:**

- **Steady states and their sensitivity** S = dT*/d ln Φ, by continuation in
  supply.
- **Critical response time** τ_c: the first loss of stability as τ grows. It
  comes from the delay characteristic equation, solved by root-finding up to
  10⁴ years. Larger values are reported as censored.
- **Kicked trajectories** at chosen τ.
- **Invasions:** a rare invader enters a resident world in one closed
  habitat. Populations are counted every ten years, and a group is extinct
  below one cell.

**Verification.**

- Hypotheses and pass criteria were fixed in dated specifications before each
  stage.
- Two independent AI agents built, audited and cross-checked every result.
- A claims ledger links each number to code, commit and a reproducing
  command.
- Parameters are given in table S1, and all code is archived (Zenodo DOI).

## 3. Results

**3.1 Perfect control** (figure 1*b*,*c*). The two groups coexist where their
hydrogen requirements match, at 281.5 K in the reference case. Changes in
supply shift the balance between the groups and leave temperature unchanged:
S = 0, the plateau of Seto & Akagi (2007). The log ratio of the populations
integrates their difference in growth rate. Near coexistence this acts as
integral feedback.

**3.2 Perfect control is fragile** (figure 2). We found 42 exactly holding
states:

- six are unstable even with an instant climate response;
- the other 36 first lose stability at response times of about 7 years or
  less.

The reference state loses stability at 0.15 years.

- **At a 1-year response time,** both groups persist for 30,000 years while
  temperature swings over about 1.3 K.
- **At 10–100 years,** both populations fall below one cell.

**3.3 Durability costs a little precision** (figure 3). Acetate slowing its
own producers, and spread in habitat temperature, each let temperature
follow supply slightly. The critical response time then rises smoothly from
the perfect-control limit.

- **On four tuned branches,** 0.07–0.32 K per e-fold of supply buys
  tolerance of a 30-year response.
- **Resolved spread communities,** at 1–2 K per e-fold, tolerate centuries.
- **All 122 graded states** have sensitivities of at least 0.59 K and
  critical response times of at least 331 years; 113 exceed the 10⁴-year
  search limit.

Two simple forms we predicted for this curve, a power law and a weak-mode
formula, each failed on at least one branch (ESM).

**3.4 Arrival order decides the survivor** (figure 4). In all 24 invasions,
the invader drove the resident below one cell, including where a stable
mixture exists. Arrival order chose the surviving group.

**3.5 Atmospheric hydrogen** up to 100 Pa leaves the set point unchanged
(ESM).

## 4. Discussion

**The trade-off.** A microbial thermostat can hold temperature exactly, and
in doing so it inherits the weakness of integral control: sensitivity to
delay. Graded feedback relaxes the exactness. A residual sensitivity of a
fraction of a kelvin per e-fold of supply then buys tolerance of decades,
and 1–2 K buys centuries. This is the precision–robustness trade-off of molecular circuits (Qian & Del
Vecchio 2018; Olsman et al. 2019), operating between species at planetary
scale.

**Relation to earlier work.** Seto & Akagi (2007) found the plateau. We add:

- its dynamics under climate delay;
- the measured cost of loosening it;
- its assembly.

Archean ecosystem–climate models (Kharecha et al. 2005; Ozaki et al. 2018;
Sauterey et al. 2020) frame the hydrogen budget.

**The Archean.** Any hydrogen-competition thermostat on the hazy early Earth
would most plausibly run in its graded form. Acetate accumulation and
spatial heterogeneity are ordinary features of sediments and mats.

**Assembly.** Arrival order chose the survivor even where a stable mixture
exists. Stability and assembly are therefore separate problems.

**Limitations.** These results come from a conditional model. Its conditions
are listed in table 1:

- the temperature switch depends on how growth capacities transfer from
  culture;
- regulation needs the two hydrogen pathways to yield different amounts of
  methane;
- physiology below 277 K is a continuation;
- the costs are local slopes on four branches;
- stability is local to each steady state;
- invasions use one closed habitat with a one-cell rule.

**Tests and generality.** Measuring sensitivity and response time together
would test the trade-off in other microbial feedbacks and mesocosms; the
delay-margin analysis transfers directly.

**Conclusion.** Microbes can hold a planet's temperature steady, but perfect
control breaks down when the climate responds slowly. Slightly imperfect
control is far more durable.
