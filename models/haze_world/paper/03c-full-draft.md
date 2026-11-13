# Microbial competition can regulate a hazy planet's temperature, but exact control is fragile to climate inertia

Step 3c: full draft. Claude (Opus 5.5), 13 November 2026. Built from
[Step 3b](03b-paragraph-abstracts.md); paragraph IDs from 3b are given in
HTML comments. Figures and table follow [Step 1c](01c-display-items.md).
Citations are author–year for drafting and convert to Vancouver at
submission.

Reviewed by Codex (GPT-6), 13 November 2026. Result scopes follow C06,
C52 and C54–C59 in the claims ledger; the review record is
[here](../../../docs/audits/paper-step3c-codex-review-2026-11-13.md).

---

## Abstract

Can life regulate its planet's climate when that climate responds slowly? We
test this in a model inspired by the hazy early Earth. Two microbial groups
compete for hydrogen: methanogens make methane, which forms a cooling organic
haze, and acetogens divert hydrogen into acetate. Temperature decides which
group grows faster, so their competition can hold temperature exactly
constant as hydrogen supply changes. That perfect control is fragile. The 36
exactly holding states on the haze-cooling branch all first lost stability
at climate response times of about seven years or less. Two
changes, acetate slowing its own producers and habitats differing in
temperature, made control slightly imperfect and far more durable. On four
tested branches, a local sensitivity of 0.07–0.32 K per e-fold of supply
bought tolerance of a 30-year response, and 1–2 K bought centuries. In
invasion simulations, arrival order decided which group survived.

---

## 1. Introduction

<!-- I1 -->
Whether life regulates the climate of its planet has been argued since
Lovelock and Margulis proposed that the biosphere keeps surface conditions
favourable as the Sun brightens (Lovelock & Margulis 1974). Daisyworld turned
the proposal into a model that can be analysed: dark and light daisies change
the planet's reflectivity, and their competition holds temperature near the
daisies' growth optimum over a wide range of solar forcing (Watson & Lovelock
1983). Real climates respond with a lag, because oceans store heat. The
relative pace of biological and climatic adjustment matters: given thermal
inertia, Daisyworld regulation can produce damped oscillations (Weaver & Dyke
2012).

<!-- I2 -->
Control theory explains how a biological system can hold a variable exactly
at a set point. Integral feedback accumulates past error, so a stable loop
returns the regulated variable to its set point after sustained
disturbance; bacterial chemotaxis adapts perfectly in this way (Yi et al.
2000; Khammash 2021). Exactness has costs. In molecular circuits, weakening
the integral action can improve stability at the price of a steady error
(Olsman et al. 2019), and dilution of the controller molecules by cell growth
introduces such an error (Qian & Del Vecchio 2018). Integral control is also
sensitive to added phase lag, and stronger integral action can make a loop
more oscillatory (Åström & Murray 2021). Thermal inertia adds phase lag to
the climate-feedback loop.

<!-- I3 -->
The early Earth offers a concrete case. The young Sun delivered about a
quarter less energy than today, yet geological evidence shows liquid water
through the Archean (Sagan & Mullen 1972; Feulner 2012). Methane from
methanogenic archaea could have contributed greenhouse warming. Above a
threshold ratio of methane to carbon dioxide, however, photochemistry forms
an organic haze whose anti-greenhouse effect cools the surface (Haqq-Misra et
al. 2008; Arney et al. 2016). Other microbes compete for the same hydrogen.
Acetogenic bacteria convert it, with carbon dioxide, to acetate, and
temperature shifts the balance between them and the methanogens
(Kotsyurbenko et al. 2001). In anaerobic sludge incubated under hydrogen,
acetogenesis took a large share of hydrogen use at 15 °C, whereas
methanogenesis dominated at 30 °C (Fu et al. 2019).

<!-- I4 -->
On the haze-cooling branch, this competition can form a restoring loop
(figure 1*a*). In our reference model, acetogens win below a switch
temperature and methanogens above it. Warming favours methanogens, whose
methane thickens the haze and cools the surface. Cooling favours acetogens,
which divert hydrogen away from methane, thin the haze and warm the surface.
Seto & Akagi (2007) found, in a generic competition model, that two
competitors with matched resource requirements hold temperature exactly flat
against changes in forcing. For a hydrogen-competition regulator, we ask how
the climate's response time changes stability and what durability costs.

<!-- I5 -->
We couple microbial kinetics transferred from cultured strains to a published
haze climate (Arney et al. 2016) and give the climate an explicit response
time. We ask three questions. Does exact regulation survive a slow climate
response? How much temperature precision must be given up to buy how much
durability? When one group arrives in a world held by the other, does arrival
order decide which persists? We answer with linear stability analysis of the
steady states, two tunable departures from exact control, and invasion
simulations under a finite-population rule. The hypotheses developed in
stages, and dated specifications record each stage's predictions and tests
(§2.7).

---

## 2. Model

The model couples two microbial populations to atmospheric methane and
surface temperature (figure 1*a*). Physiological rates are per hour; the
factor H = 8766 h yr⁻¹ converts them to years, the unit of all climate
quantities. Table 1 lists the ingredients and the conditions each sets, and
table S1 gives every parameter with its source.

<!-- M1 -->
### 2.1 Community and physiology

One acetogen (A) and one hydrogenotrophic methanogen (M) take up dissolved
hydrogen, at partial pressure p, in a well-mixed habitat. Uptake per unit
biomass saturates above a cessation threshold p_i^\*, below which a group
cannot use hydrogen:

$$q_i = \frac{s_i(T)\,u_i}{K_i(T) + u_i}, \qquad u_i = (p - p_i^*)_+,
\qquad i \in \{A, M\}. \tag{2.1}$$

Here $(z)_+=\max(z,0)$.

Biomass X_i grows with a constant yield Y_i on uptake net of maintenance
m_i(T), and is lost at a common rate ℓ:

$$\frac{dX_i}{dt} = H\,[\,Y_i(q_i - m_i(T)) - \ell\,]\,X_i. \tag{2.2}$$

Write $g_i=Y_i(q_i-m_i)$ for hourly growth before cell loss.

The temperature shapes of capacity s_i and half-saturation K_i come from
hydrogen-uptake assays of an acetogen (*Acetobacterium bakii*) and a
methanogen at six temperatures from 4 to 30 °C (Kotsyurbenko et al. 2001). The acetogen's
absolute capacity is set from *Acetobacterium woodii* growth data (Peters et
al. 1998); at 30 °C the methanogen's capacity is γ = 0.74 times the
acetogen's, with its own temperature dependence.
Maintenance follows a shared Arrhenius slope from a cross-species
correlation (Tijhuis et al. 1993), and the cessation thresholds follow the
thermodynamics of each reaction. Below the coldest assay, 277.15 K, capacity
and half-saturation are held at their 277.15 K values down to the model
floor of 273 K; maintenance and thresholds keep their temperature laws.

Setting growth equal to loss in (2.2) gives each group's hydrogen
requirement, the pressure at which its population neither grows nor
declines:

$$R_i^*(T) = p_i^*(T) + \frac{K_i(T)\,Q_i(T)}{s_i(T) - Q_i(T)},
\qquad Q_i = m_i + \ell / Y_i. \tag{2.3}$$

We set $R_i^*=\infty$ when $s_i\le Q_i$. At fixed temperature and sufficient
supply, the group with the lower requirement excludes the other. In the reference
model the requirements cross at T\* = 281.53 K (figure 1*b*): at 278 K the
acetogen needs 27.6 Pa and the methanogen 47.1 Pa, and at 283 K the acetogen
needs 21.4 Pa and the methanogen 19.6 Pa. This crossing, the switch, emerges
from the transferred kinetics.

<!-- M2 -->
### 2.2 Hydrogen and acetate

Hydrogen enters at a fixed rate J, proportional to a supply Φ expressed as a
methane-equivalent flux, and exchanges with an atmospheric reservoir at
partial pressure p_atm; the reference input is J = 10⁻⁶ mol H₂ L⁻¹ h⁻¹:

$$K_H \frac{dp}{dt} = H\,[\,J - q_A X_A - q_M X_M - k_{ex}(p - p_{atm})\,],
\tag{2.4}$$

where K_H is hydrogen's solubility. Exchange runs in either direction. Part
of each group's uptake builds biomass, which leaves with lost cells rather
than becoming methane. The catabolic flux is
$F_i=H X_i[q_i-\alpha_i(g_i)_+]$, in mol H₂ L⁻¹ yr⁻¹, where α_i is
hydrogen equivalents retained per unit new biomass. The methanogen
returns one methane per four hydrogen catabolised. The acetogen makes
acetate, which is removed over t_A = 1 year; a fraction f is recycled into
methane and the rest leaves by other routes:

$$\frac{dC}{dt} = \frac{F_A}{4} - \frac{C}{t_A}. \tag{2.5}$$

At homogeneous coexistence, the catabolised fraction of uptake is
$\eta_i=1-\alpha_i\ell/(m_i+\ell/Y_i)$. The steady methane yields per
hydrogen taken up are $f\eta_A/4$ and $\eta_M/4$. Their difference makes
competition matter to climate.

<!-- M3 -->
### 2.3 Methane and climate

Atmospheric methane, as the column ratio r of methane to carbon dioxide,
balances microbial production and a small abiotic source against
first-order removal:

$$\frac{dr}{dt} = \chi\left(\frac{F_M}{4} + \frac{fC}{t_A}\right)
+ c\,\Phi_{abiotic} - \frac{r}{t_{CH_4}}. \tag{2.6}$$

Here χ and c convert habitat and column fluxes to ratio units, Φ_abiotic is
a serpentinisation estimate quoted by Arney et al. (2016), and the methane
lifetime t_CH₄ = 10,000 years is our assumption. The climate temperature
T_clim(r) interpolates the haze response of Arney et al. (2016), case B: a
2.7-Ga Earth at 81% of present sunlight. Below the first extracted point we
assume a smooth bridge to 283 K at zero methane; above the last we hold
temperature at its final value. Surface temperature T approaches T_clim over
a response time τ:

$$\tau \frac{dT}{dt} = T_{clim}(r) - T. \tag{2.7}$$

All biological rates use T, not T_clim. With τ = 0 temperature follows
methane instantly. A modern climate model separates a fast response of years
from a slow response of centuries (Held et al. 2010); we use τ as a free
measure of thermal inertia. At the reference
switch, r = 0.195 lies on the haze-cooling branch, where temperature falls
by about 0.7 K for each 0.001 rise in r.

<!-- M4 -->
### 2.4 Departures from exact control

Products can raise the hydrogen each group needs. Acetate raises the
acetogen's cessation threshold and methane the methanogen's:

$$p_A^* = p_{A0}^*(T)\left(\frac{C}{C_{ref}}\right)^{a/4}, \qquad
p_M^* = p_{M0}^*(T)\left(\frac{r\,p_{CO_2}}{p_{CH_4,ref}}\right)^{m/4}.
\tag{2.8}$$

We compare four chemistries: fixed products (a = m = 0), methane feedback
only (m = 1), acetate feedback only (a = 1), and both. In the fixed
chemistry the product stocks still change; only their effect on the
thresholds is held fixed. The first tunable departure, dial D1, sets a = κ
with m = 0 and turns κ up from 0 to 1, so acetate slows its own producers
by a controlled amount.

The second departure, dial D2, spreads habitat temperatures. Habitats sit at
offsets δ, uniform on [−σ, σ], from the shared surface temperature. Each has
its own hydrogen, acetate and populations, and cells move between habitats
at rate d:

$$\frac{dX_i(\delta)}{dt} = H\,X_i(\delta)\,[\,Y_i(q_i - m_i(T+\delta))
- \ell\,] + d\,[\bar X_i - X_i(\delta)], \tag{2.9}$$

where X̄_i is the habitat mean and all local rates use T + δ. All habitats
feed one atmosphere; equation (2.6) uses their weighted mean microbial source.
D1 uses f = 0 and 0.5; D2 uses f = 0.5 at d = 10⁻⁴ and 10⁻³ yr⁻¹. We resolve
the spread with adaptive Gauss–Legendre quadrature, refining panels where the
acetogen share changes fastest. Every reported setting passes a doubling
test, and an independently derived characteristic equation (§2.5) confirms
selected states.

<!-- M5 -->
### 2.5 Steady states, sensitivity and stability

Steady states solve the full set of balances. We find them by root search
and follow graded branches by continuation. For each state we compute the
local sensitivity of its temperature to supply,

$$S = \frac{dT^*}{d\ln\Phi}, \tag{2.10}$$

by implicit differentiation, in kelvin per e-fold change in supply. Exact
control means S = 0; we classify states with |S| < 10⁻⁶ K per e-fold as exact.

The thermal state makes τ enter the linearisation directly. Write A for the
Jacobian of the biological and chemical states at fixed temperature, b for
their response to temperature, and cᵀ for the slope of T_clim acting on
methane. The eigenvalues λ of the full system then satisfy

$$(1 + \tau\lambda)\det(\lambda I - A) - c^{\mathsf T}\operatorname{adj}(\lambda I
- A)\,b = 0. \tag{2.11}$$

The critical response time τ_c is the first τ at which a stable state's
leading eigenvalue crosses into the right half-plane. We scan τ on a
logarithmic grid to 10⁴ years and refine each crossing; a state still stable
at 10⁴ years has τ_c reported as a lower bound. Already unstable states are
reported separately. To see what instability
does, we kick the biomass of the acetogen by 0.1% and integrate the full
equations for 30,000 years.

<!-- M6 -->
### 2.6 Invasions and the one-cell rule

Each invasion starts from one group at its single-group equilibrium and
introduces the other at 10⁻¹² g dry weight per litre, with no later
immigration. Hydrogen supply, exchange and methane removal continue. The 24
runs cross two directions, two chemistries (fixed products and feedback
from both), f = 0 and 0.5, and τ = 0, 3 and 30 years, and last 100,000
years. Populations are converted to global cell counts, using a cell mass of
3 × 10⁻¹³ g and a habitat volume summed over the planet. Every ten years, a
group with less than one cell in total is removed. This rule, our choice,
fixes when a loss becomes permanent. It stops a group recovering from a
vanishing fraction of a cell, an artefact of continuous models (Mollison
1991). We report the uncensored continuous trajectories alongside.

<!-- M7 -->
### 2.7 Workflow and verification

The work ran in stages. Dated specifications preserve the staged predictions
and their pass criteria; trade-off counterexamples are reported (§3.4).
Claude (Opus 5.5) and Codex (GPT-6) built the model and cross-checked the
reported findings, including independent recalculation of key numbers. A
claims ledger links each reported finding to its evidence, the commit that
produced it and the command that reproduces it. Regression tests cover the
budgets, equilibrium algebra, derivatives, spectra and census rule.
Parameters (table S1), code and outputs will be archived with a Zenodo DOI.

---

## 3. Results

<!-- R1 -->
### 3.1 Perfect control

With fixed products, the two groups coexist only where their hydrogen
requirements match, at T\* = 281.53 K in the reference model (figure 1*b*).
At positive coexistence, $g_A=g_M=\ell$, giving equal requirements in (2.3).
Their equality fixes T\* within the coexistence supply range. Supply then
changes biomass shares while temperature stays at T\*, S = 0 (figure 1*c*).
This is the plateau
mechanism of Seto & Akagi (2007). The log ratio of the populations integrates
their growth-rate difference, $d\ln(X_A/X_M)/dt=H(g_A-g_M)$, which depends on
hydrogen, temperature and product feedback. Near coexistence this acts as
integral feedback (Yi et al. 2000). At f = 0.5 and τ = 0,
the mixture is warmer than a world of methanogens alone: 281.5 K against
273.5 K at the same supply, or 4.7 K warmer under an alternative cold
continuation of physiology.

<!-- R2 -->
### 3.2 Perfect control is fragile

Across the fixed and methane-feedback chemistries, three recycling fractions
(f = 0, 0.5, 0.9), three loss rates and three supplies, we found 42 exactly
holding states (figure 3*a*, left strip). Six are unstable even with an
instant climate response. All six lie at low methane, on the assumed bridge
where more methane warms rather than cools. The other 36 first lose
stability at response times between 0.06 and 7.08 years. In the matched
reference comparison, increasing f from 0 to 0.5 raises the margin from
0.15 to 1.10 years (ESM). Figure 2*c* compares exact and graded states at
the same f = 0.5. Recycling also narrows the difference
in methane yield between the routes.

<!-- R3 -->
### 3.3 Swings and crashes

Kicked trajectories show what instability does (figure 2). At a 1-year
response time, well past its 0.15-year limit, the reference regulator
oscillates. Both groups persist for 30,000 years, while late temperature
swings span about 1.3 K and the populations cycle through deep minima
(figure 2*b*). At response times of 10 and 100 years, with f = 0 or 0.5,
the calculated populations fall below one cell. An unstable
regulator can therefore keep working with wide swings, or let a population
crash.

<!-- R4 -->
### 3.4 Durability costs a little precision

Both dials let temperature follow supply slightly, and near the exact limit
the critical response time rises smoothly on every tested branch (figure
3*a*). A 30-year margin costs a local sensitivity of
0.28 K per e-fold of supply with acetate feedback at f = 0, and 0.31 K at
f = 0.5. With habitat spread it costs 0.07 K at the lower exchange rate
(d = 10⁻⁴ yr⁻¹) and 0.16 K at the higher (d = 10⁻³ yr⁻¹). Resolved
spread communities at 1–2 K per e-fold tolerate centuries. In an earlier
comparison that switched each mechanism fully on or off, all 122 initially
stable graded states had sensitivities of at least 0.59 K per e-fold and
margins of at least 331 years; 113 were still stable at the 10⁴-year
ceiling. Figure 3*b* shows what these sensitivities mean as temperature
against supply.

<!-- R5 -->
Before the dial runs we proposed two general forms for this trade-off. The
first was a power law between margin and sensitivity, with a slope between 1
and 2.5 on each branch. Two branches fell outside it: acetate feedback at
f = 0.5, with a slope of 0.80, and habitat spread at the lower exchange
rate, with 0.99. The second was an approximation to the margin from the
oscillation period and damping time. It passed the planned grid but failed
at two refinement points, where it gave 26% and 47% of the computed margins.
We therefore report the price of durability branch by branch (ESM).

<!-- R6 -->
### 3.5 Arrival order decides the survivor

In all 24 invasions the invader drove the resident below one cell (figure
4*a*). This held in both directions, with fixed products and with feedback
from both products, at f = 0 and 0.5, and at response times of 0, 3 and 30
years. Each run ended with the invader alone: 12 of 12 acetogen invasions
left only acetogens, and 12 of 12 methanogen invasions only methanogens
(figure 4*b*). This includes settings where a mixture of both groups is
locally stable. Arrival order chose the surviving group.

---

## 4. Discussion

<!-- D1 -->
### 4.1 Exactness brings fragility

Near coexistence, competition between the two groups acts as integral
feedback and holds temperature exactly. Integral control is sensitive to
added phase lag, which a slowly responding climate supplies (Åström & Murray
2021).
Every exactly holding state that starts stable loses stability at a climate
response time of about 7 years or less, and the reference state does so at
0.15 years. In 32 of the 36 cases the limit is shorter than the fast climate
response of about 4 years found in a modern climate model (Held et al. 2010).
Past the limit, the regulator swings widely or a population crashes.

<!-- D2 -->
### 4.2 A small price for durability

Graded feedback gives up exactness and gains durability. A residual
sensitivity of a fraction of a kelvin per e-fold of hydrogen supply buys
tolerance of a 30-year climate response, and 1–2 K per e-fold buys
centuries. Graded communities retain a small temperature response to supply.
This parallels precision–stability trade-offs in molecular circuits (Olsman
et al. 2019; Qian & Del Vecchio 2018; Khammash 2021).

<!-- D3 -->
### 4.3 Relation to earlier work

Seto & Akagi (2007) found the plateau, and Weaver & Dyke (2012) showed that
thermal inertia can produce damped oscillations in Daisyworld. For a
hydrogen-competition regulator in a haze climate we add three results: its
stability margins as the climate slows, the sensitivity cost of graded
feedback, and finite-population invasion tests. Coupled ecosystem–climate
models of the Archean show how microbial hydrogen and methane cycling set
atmospheric composition and climate (Kharecha et al. 2005; Ozaki et al.
2018; Sauterey et al. 2020). Our analysis concerns the stability of the
temperature regulation that such couplings can produce.

<!-- D4 -->
### 4.4 The early Earth

Acetate feedback and variation in habitat temperature are candidate routes to
graded regulation on the hazy early Earth. Their strengths would set where an
Archean regulator sat between precision and durability. Modern microbial mats
are accessible analogue habitats. Their hydrogen levels vary by orders of
magnitude with depth and time of day, and far more of their fixed carbon
leaves as organic acids than as methane (Hoehler et al. 2001; Bebout et al.
2004). Measuring acetate stocks and turnover in such mats, and the effect of
acetate on the hydrogen acetogens need, would test the first route.
Measuring habitat temperatures and the exchange of cells between habitats
would test the second.

<!-- D5 -->
### 4.5 Stability and assembly are separate

Arrival order chose the survivor in every tested invasion, including settings
where a mixture of the two groups is stable once formed. Local stability of
the mixture did not predict the outcome of invasion. Incumbency advantage, a familiar arrival-order effect, favours the first arrival
(Fukami 2015). Here the late arriver won all 24 invasions, and each run ended
with one group.

<!-- D6 -->
### 4.6 Conditions

These results come from a conditional model, and table 1 lists its
conditions. The switch depends on kinetics transferred from cultured strains,
on the capacity ratio γ and on the assumed loss rate: halving or doubling ℓ
moves T\* from 281.5 K to 278.4 or 286.5 K. The alternative dry-mass capacity
normalisation can put the crossing outside the cooling branch. The reference
coexistence plateau requires different effective methane yields; here
those yields depend on recycling and biomass retention. Strain traits remain
fixed. Physiology is extended
below the coldest assay, 277.15 K, to 273 K. The costs of durability are
local slopes on four branches, and stability is local to each steady state.
A crash is read at the first fall below one cell, and invasions use one
habitat without immigration, with the one-cell rule applied every ten years.
The climate is one published case with an assumed methane lifetime and
low-methane bridge. Atmospheric hydrogen up to 100 Pa leaves the set point
unchanged and moves the reference margin from 0.15 to 0.12 years (ESM).

<!-- D7 -->
### 4.7 Tests and generality

Any population–environment feedback with a slow environment invites two
measurements: how far the regulated variable drifts with forcing, and how
slowly the environment responds. Stability analysis of that system then
estimates its critical response time, placing it on the precision–durability plane of
figure 3. Mesocosms with controlled supply and
an imposed thermal lag, and biogeochemical models that resolve both groups,
could test the trade-off with the delay-margin analysis used here.

Microbes can hold a planet's temperature steady, but perfect control breaks
down when the climate responds slowly. Slightly imperfect control is far
more durable.

---

## Table 1. Model ingredients and the conditions they set

| Ingredient | Basis | Role | Condition it sets |
|---|---|---|---|
| Hydrogen-uptake kinetics, 4–30 °C | Assays of *A. bakii* and a methanogen (Kotsyurbenko et al. 2001) | Temperature shapes of capacity and half-saturation; with (2.3), the switch | Reference ratio γ = 0.74 at 30 °C; the alternative dry-mass normalisation can move the crossing off the cooling branch |
| Acetogen capacity and yields | *A. woodii* growth (Peters et al. 1998) | Absolute uptake rate | Capacity inferred from growth rate, yield and maintenance |
| Maintenance | Cross-species correlation (Tijhuis et al. 1993) | Temperature dependence of requirements | One Arrhenius slope for both groups |
| Cessation thresholds | Reaction thermodynamics; reference thresholds assumed | Requirements at low hydrogen | 20 and 1 Pa at 30 °C |
| Physiology below 277.15 K | Continuation | Extends the model to 273 K | Capacity and half-saturation held at 277.15 K values |
| Cell loss ℓ | Assumption, 0.001 h⁻¹ | Sets requirements, and so T\* | T\* = 278.4, 281.5, 286.5 K at ℓ = 0.0005, 0.001, 0.002 h⁻¹ |
| Hydrogen supply and exchange | Assumption | Feeds the community; atmospheric outlet | Reservoir at 0 Pa; 0–100 Pa leaves T\* unchanged (ESM) |
| Acetate fate | Assumption: removal over 1 yr, fraction f to methane; biomass exported | Methane yield of the acetogen route | The reference coexistence plateau needs the routes' methane yields to differ |
| Atmospheric methane | Lifetime 10,000 yr assumed; abiotic source quoted by Arney et al. (2016) | Links microbes to climate | Well-mixed column ratio stands for surface CH₄/CO₂ |
| Haze climate T_clim(r) | Arney et al. (2016), case B: 2.7 Ga, 81% sunlight | Provides the haze-cooling branch | One case; assumed bridge to 283 K at zero methane and plateau beyond the data |
| Climate response time τ | Free parameter | Thermal inertia | First-order relaxation of surface temperature |
| Product feedback (dial D1) | Assumed activity form, equation (2.8) | Acetate slows its producers by κ | Methane feedback held off along D1 |
| Habitat spread (dial D2) | Assumption | Habitats offset by up to ±σ, exchanging cells at rate d | Uniform offsets; one shared atmosphere and climate |
| One-cell rule | Assumption, motivated by Mollison (1991) | Finite endpoints of invasions | Ten-year counts; no immigration; continuous crash calculations are read at the first crossing |

---

## Figure captions

**Figure 1. How microbes can set a planet's temperature.** (*a*) Hydrogen
feeds two groups and exchanges with an atmospheric reservoir. Methanogens
make methane, which thickens an organic haze and cools the surface;
acetogens divert hydrogen into acetate, of which a fraction f is recycled to
methane. Temperature decides which group wins, and the climate responds over
a time τ. Biomass export, omitted from the schematic, also reduces methane
delivery. (*b*) Hydrogen requirement of each group against temperature,
equation (2.3). The curves cross at T\* = 281.53 K; acetogens need less
hydrogen below it and methanogens above it. The alternative dry-mass
capacity ratio (grey dotted) moves the crossing to 297.15 K, just above the
297.01 K climate peak. The bar marks the published haze-cooling temperature
range; capacity ratios are anchored at 30 °C. Kinks fall at the assay
temperatures; shading marks the continuation
below 277.15 K. (*c*) Steady
surface temperature against hydrogen supply J for methanogens alone and for
both groups, with fixed products, f = 0.5 and τ = 0. With both present,
temperature holds at T\* across the coexistence range (shaded), the plateau
of Seto & Akagi (2007). At the reference supply (dotted) methanogens alone
give 273.5 K. Inset: the haze response of Arney et al. (2016), case B, with
the haze-cooling branch in bold and the two reference states marked.
Dashed segments are the assumed low-methane bridge and high-methane plateau.

**Figure 2. Perfect control breaks down when the climate responds slowly.**
Panels (*a*, *b*): reference state, fixed products, f = 0, after a 0.1% kick
to acetogen biomass. The time axis is broken between 2,000 and 28,000 years. (*a*)
Surface temperature at response times of 1 year (thin) and 10 years
(thick). (*b*) Global cell counts for the same runs on a log scale; the
dotted line marks one cell. At 10 years the acetogens fall below one cell at
1,830 years, where both traces stop. At 1 year both groups persist through
30,000 years, with late oscillations about 380 years apart; their amplitude
is still changing. (*c*) Leading real part of the eigenvalues against τ for
matched exact and graded states at f = 0.5 (habitat spread σ = 0.03 K,
d = 10⁻⁴ yr⁻¹ for the graded state). Markers show the first loss of
stability, at 1.10 and 38.5 years. The vertical axis is
linear between ±10⁻⁴ yr⁻¹ and logarithmic beyond.

**Figure 3. Durability costs a little precision.** (*a*) Critical response
time τ_c against local sensitivity |S|. Left strip: the 42 exact states (S =
0), 36 on the haze-cooling branch (filled) and six bridge states already
unstable at τ = 0 (open, placed at the strip's base). Lines: the four dial
branches, joining finite margins on one branch; ringed markers show where
each crosses 30 years. Symbols without lines: the 122 graded states of an
on/off comparison (grey, all at the ceiling) and of resolved habitat spread
(green; nine finite). Arrows mark lower bounds at the 10⁴-year search
ceiling. The shaded band marks the price of a 30-year margin, 0.07–0.32 K
per e-fold. (*b*) Local tangents of steady temperature against log supply
at the reference supply, for three settings of the acetate dial at f = 0:
exact (κ = 0), the 30-year point (S = −0.28 K per e-fold) and κ = 1 (S =
−1.88 K per e-fold, stable through 10⁴ years). Tangents show derivatives,
not finite responses.

**Figure 4. Arrival order decides the survivor.** (*a*) Global cell counts
after a rare invader enters, in each direction, with fixed products, f = 0.5
and τ = 3 years. These are finite-census trajectories: a group below one
cell is removed at the next ten-year census (20 and 10 years respectively).
Crosses mark the first one-cell crossings at 18.3 and 7.4 years. (*b*)
Surviving group in all 24 runs:
every acetogen invasion ended with acetogens alone, and every methanogen
invasion with methanogens alone. Diamonds mark the 8 of 12 settings where
the reference mixture of both groups is locally stable.

---

## End statements (drafts)

**Ethics.** This work used no human or animal subjects.

**Data accessibility.** Code, model outputs, the claims ledger and the dated
stage specifications are at https://github.com/BWBrook/terra_prisca and will
be archived on Zenodo with a DOI before submission. Source publications are
cited; their PDFs remain outside the public archive.

**Declaration of AI use.** [For Barry to settle. Draft:] The model,
analyses and manuscript drafts were developed with Claude (Anthropic; Claude
Opus 5.5, with Sonnet 5.5 for the display items and supplement) and Codex
(OpenAI; GPT-6), working with the human author.
They designed and coded the model, ran and cross-checked the analyses, and
generated model figures and manuscript drafts, each reviewing the other's
work. Independent AI reviews by Claude Fable 5.2 (Anthropic) and GPT-6 Astra
Pro (OpenAI) prompted the climate-inertia tests; their checks are archived.
B.W.B. initiated
the project, shaped its questions and scope, and led the writing process.
He will review the final manuscript before release. Reviewed correspondence
snapshots, dated specifications and a claims ledger are public in the
repository.

**Authors' contributions.** [Barry.]

**Conflict of interest.** None declared.

**Funding.** [Barry.]

**Acknowledgements.** [Barry.]

---

## References (author–year keys; Vancouver at submission)

| Key | Identifier |
|---|---|
| Arney et al. 2016 | 10.1089/ast.2015.1422 |
| Åström & Murray 2021 | *Feedback systems: an introduction for scientists and engineers*, 2nd edn. Princeton University Press. ISBN 978-0-691-19398-4 |
| Bebout et al. 2004 | 10.1111/j.1472-4677.2004.00024.x |
| Feulner 2012 | 10.1029/2011RG000375 |
| Fu et al. 2019 | 10.3389/fmicb.2019.02418 |
| Fukami 2015 | 10.1146/annurev-ecolsys-110411-160340 |
| Haqq-Misra et al. 2008 | 10.1089/ast.2007.0197 |
| Held et al. 2010 | 10.1175/2009JCLI3466.1 |
| Hoehler et al. 2001 | 10.1038/35085554 |
| Khammash 2021 | 10.1016/j.cels.2021.05.020 |
| Kharecha et al. 2005 | 10.1111/j.1472-4669.2005.00049.x |
| Kotsyurbenko et al. 2001 | 10.1111/j.1574-6941.2001.tb00893.x |
| Lovelock & Margulis 1974 | 10.1111/j.2153-3490.1974.tb01946.x |
| Mollison 1991 | 10.1016/0025-5564(91)90009-8 |
| Olsman et al. 2019 | 10.1016/j.cels.2019.06.001 |
| Ozaki et al. 2018 | 10.1038/s41561-017-0031-2 |
| Peters et al. 1998 | 10.1111/j.1574-6941.1998.tb00516.x |
| Qian & Del Vecchio 2018 | 10.1098/rsif.2017.0902 |
| Sagan & Mullen 1972 | 10.1126/science.177.4043.52 |
| Sauterey et al. 2020 | 10.1038/s41467-020-16374-7 |
| Seto & Akagi 2007 | 10.1016/j.jtbi.2007.05.013 |
| Tijhuis et al. 1993 | 10.1002/bit.260420415 |
| Watson & Lovelock 1983 | 10.1111/j.1600-0889.1983.tb00031.x |
| Weaver & Dyke 2012 | 10.1016/j.jtbi.2012.07.034 |
| Yi et al. 2000 | 10.1073/pnas.97.9.4649 |
| Zenodo archive | DOI at release |
