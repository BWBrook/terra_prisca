# Microbial competition can regulate a hazy planet's temperature, but exact control is fragile to climate inertia

Step 3c: full draft. Claude (Opus 5.5), 13 November 2026. Built from
[Step 3b](03b-paragraph-abstracts.md); paragraph IDs from 3b are given in
HTML comments. Figures and table follow [Step 1c](01c-display-items.md).
Citations are author–year for drafting and convert to Vancouver at
submission.

Reviewed by Codex (GPT-6), 13 November 2026. Result scopes follow C06,
C52 and C54–C59 in the claims ledger; the review record is
[here](../../../docs/audits/paper-step3c-codex-review-2026-11-13.md).
Consolidated after Issues 1–5 on 23 November 2026
([plan](../../../docs/audits/consolidation-plan-2026-11-23.md)).

---

## Abstract

Can life regulate its planet's climate when that climate responds slowly?
We test this in a model inspired by the hazy early Earth. Two microbial
groups compete for hydrogen: methanogens make methane, which forms a
cooling organic haze, and acetogens divert hydrogen into acetate.
Temperature shifts the competitive advantage, so their competition can hold
temperature exactly constant as hydrogen supply changes. This needs some
diverted hydrogen to stay out of methane for good, through oxidation,
export or burial. Exact control is fragile: the reference equilibrium loses
local stability at a climate response time of 0.15 years without acetate
recycling, or about one year with half recycled. With full recycling and
biomass export, sampled margins reach 21–31 years inside a narrow window of
lower supplies. Imperfect control lasts far longer: on four tested branches
with acetate feedback or differing habitat temperatures, a 30-year margin
costs a fraction of a kelvin per e-fold of supply. Some
habitat mixtures tolerate centuries at 1–2 K per e-fold. All 24 closed,
uniform reference invasions end with the invader alone; with fixed
products, exclusion takes decades. Refuges or immigration can sustain the
losing group until the climate catches up and the mixture forms.

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
durability? Can the controlling mixture assemble, by invasion or from a
lifeless start, and what does assembly need? We answer with linear stability
analysis of the steady states, two tunable departures from exact control,
and invasion simulations under a finite-population rule. We vary hydrogen supply
throughout and test a shift of the climate curve as a controlled surrogate
for changing sunlight. The hypotheses developed in
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

where K_H is hydrogen's solubility. Exchange runs in either direction.
With the 10,000-year methane lifetime assumed in §2.3, the reference supply
scales to 401 Tmol H₂ per year. Of this, 260 goes to methane, 111 leaves in acetate
and biomass, and 30 enters the atmosphere. Part of each group's uptake builds biomass, which leaves with lost cells rather
than becoming methane. The catabolic flux is
$F_i=H X_i[q_i-\alpha_i(g_i)_+]$, in mol H₂ L⁻¹ yr⁻¹, where α_i is
hydrogen equivalents retained per unit new biomass. The methanogen
returns one methane per four hydrogen catabolised. The acetogen makes
acetate, which is removed over t_A = 1 year. A fraction f becomes methane,
by acetate cleavage or by syntrophic oxidation followed by hydrogenotrophy,
and the rest leaves the methane system for good, oxidised by an electron
acceptor such as sulfate or ferric iron, or exported and buried:

$$\frac{dC}{dt} = \frac{F_A}{4} - \frac{C}{t_A}. \tag{2.5}$$

At homogeneous coexistence, the catabolised fraction of uptake is
$\eta_i=1-\alpha_i\ell/(m_i+\ell/Y_i)$. The steady methane yields per
hydrogen taken up are $f\eta_A/4$ and $\eta_M/4$. Their difference makes
competition matter to climate, and it is the regulator's lever. At fixed
supply the climate needs a fixed methane flux, so exact control holds T\* by
adjusting how much of the captured hydrogen leaves as acetate and biomass
rather than methane. If both returned as methane, the two routes would have
equal ultimate yields and the exact plateau would disappear. We report
f = 0 and 0.5, and f up to 1 in ESM S8.

<!-- M3 -->
### 2.3 Methane and climate

Atmospheric methane, as the column ratio r of methane to carbon dioxide,
balances microbial production and a small abiotic source against
first-order removal:

$$\frac{dr}{dt} = \chi\left(\frac{F_M}{4} + \frac{fC}{t_A}\right)
+ c\,\Phi_{abiotic} - \frac{r}{t_{CH_4}}. \tag{2.6}$$

Here χ and c convert habitat and column fluxes to ratio units, Φ_abiotic is
a serpentinisation estimate quoted by Arney et al. (2016), and the methane
lifetime t_CH₄ = 10,000 years is our assumption. We express hydrogen supply
as $P=c\,t_{CH_4}\Phi$, the methane-to-carbon-dioxide ratio the supplied
hydrogen alone could sustain if fully converted to methane; at the reference
J, P = 0.30. The climate temperature
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
1991). We report the uncensored continuous trajectories alongside. Bounded
checks start from a lifeless planet with both groups rare, and speed up the
methane response while keeping every steady state fixed. Two earlier stages
test persistence: small habitats held at fixed temperatures, and a steady
trickle of immigrants (ESM S10).

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
0.15 to 1.10 years (ESM). Recycling also narrows the difference in methane
yield between the routes. At the reference state with no acetate
recycling and an instantaneous temperature response, a small disturbance
oscillates with a period $P_{\mathrm{osc}}$ = 120 years and an amplitude
decay time $t_d$ = 4,850 years. A thermal response time of just 0.15 years
cancels this weak damping, as the local estimate
$P_{\mathrm{osc}}^2/(2\pi^2 t_d)$ predicts here. Figure 2*c* compares exact
and graded states at the same f = 0.5.

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
### 3.4 Durability costs precision

Both dials let temperature follow supply slightly, and near the exact limit
the critical response time rises smoothly on every tested branch (figure
3*a*). A 30-year margin costs a local sensitivity of
0.28 K per e-fold of supply with acetate feedback at f = 0, and 0.31 K at
f = 0.5. With habitat spread it costs 0.07 K at the lower exchange rate
(d = 10⁻⁴ yr⁻¹) and 0.16 K at the higher (d = 10⁻³ yr⁻¹). Resolved
spread communities at 1–2 K per e-fold tolerate centuries. The earlier grid
included 42 initially stable graded states in a uniform habitat with product
feedback and 80 with a resolved spread of habitat temperatures. Across these
122 states, sensitivities were at least 0.59 K per e-fold and margins at
least 331 years; 113 were still stable at the 10⁴-year ceiling, and the nine
finite margins all belong to spread states.

<!-- R4b -->
Habitat spread sets the size of this price. With weak exchange between
habitats, acetogens hold every habitat colder than T\* and methanogens every
warmer one. Supply then fixes the share of methanogen-held habitats that keeps
the methane ratio near the switch, and temperature moves to the point in the
spread that gives this share. For uniform offsets of ±σ, and with the
methane ratio near its switch value, this reduced model gives

$$\frac{1}{|S|} \approx \frac{1}{k} + \frac{1}{|S_{geo}|}, \qquad
|S_{geo}| = 2\sigma\,\frac{P_{lo}}{P}\,\frac{Q}{Q-1}, \tag{3.1}$$

where k = 140.7 K per e-fold is the response of the haze climate to the
methane ratio at the switch, P_lo is the lowest supply at which a uniform
community coexists and Q is its coexistence supply ratio (2.00 at f = 0.5;
unbounded at f = 0, where the last factor is 1; ESM). With no fitted
parameter, equation (3.1) matches the 20 spread states with exchange rates up
to 10⁻³ yr⁻¹ within 6%. Faster exchange blends habitats and can move |S|
away from it: at 0.1 yr⁻¹ computed values range from 0.71 to 1.07 times the
prediction. The 30-year price on the spread branches
was bought at σ = 0.02–0.06 K. Over the supply range in which a uniform
community coexists, wider spreads of 1 and 3 K move temperature by 1.9 and
5.4 K (figure 3*b*). Their critical response times are at least 830 and
3,500 years at four sampled supplies. Spreads of 6 and 8 K are resolved over
part of that range.

<!-- R5 -->
Before the dial runs we proposed two general forms for this trade-off. The
first was a power law between margin and sensitivity, with a slope between 1
and 2.5 on each branch. Two branches fell outside it: acetate feedback at
f = 0.5, with a slope of 0.80, and habitat spread at the lower exchange
rate, with 0.99. The second was an approximation to the margin from the
oscillation period and damping time. It passed the planned grid but failed
at two refinement points, where it gave 26% and 47% of the computed margins.
We therefore report the price of durability branch by branch (ESM).

<!-- R5b -->
### 3.5 Response to imposed warming

The Introduction's question concerns sunlight. As a controlled surrogate, we
impose a warming F that shifts the climate curve, T_clim(r) + F. For regular
graded states on the cooling branch, linearising the steady state gives

$$\frac{dT}{dF} = \frac{|S|}{kE}, \tag{3.2}$$

where k is the local climate slope and E is the response of the total
methane source to supply at fixed temperature (ESM S9). Supply and imposed warming are attenuated by the same
closed-loop factor, 1/(1 + kG), where G is the response of the methane
source to temperature. With fixed products, exact states hold T\* for every
shift from −15.47 to +8.14 K, the range over which case B's haze-cooling
branch can supply the cooling needed. Both groups persist to the ends of
that range, and sampled states within it are stable. Sampled critical
response times stay within 7% of the reference for shifts up to +6 K and lengthen to
2–4 years near the warm end. With methane feedback on the producers, an
exact state moves by 0.02% of F. Graded states move by 0.14% of F at the
30-year acetate point and by 1.9–8.3% with habitat spreads of 1–3 K. These
agree with independently computed values of E, 1.45 and about 1.08 (ESM).
Cases A and C, which differ in carbon dioxide and pressure, also give exact
states at T\* on their extracted curves.

<!-- R6 -->
### 3.6 Assembly needs somewhere to persist

In all 24 invasions the invader drove the resident below one cell (figure
4*a*). This held in both directions, with fixed products and with feedback
from both products, at f = 0 and 0.5, and at response times of 0, 3 and 30
years. Each run ended with the invader alone (figure 4*b*), including
settings where the mixture is locally stable. The resident was lost within
10–70 years with fixed products, while temperature moved by 0.4 K at most.
The climate needed 1,000–13,500 years to cross T\*. Starting from a lifeless
planet with both groups rare gave the same failure: at 283 K methanogens
removed acetogens within 60 years at all three tested fractions (f = 0, 0.5
and 0.9). A methane response ten times faster, with every steady state held
fixed, changed no outcome. Only a response a thousand times faster, about
10 years, let acetogen invasions assemble the mixture in place (ESM S10).

The loss is permanent because a group below one cell cannot return. When
the losing group could persist elsewhere, the mixture formed. Two small
habitats held at 278 and 286 K, each 2% of the area, let both invasion
directions reach the same mixed state at 281.535 K in all 12 key runs
(figure 4*c*). Immigration of as little as 0.1 cells per year did the same
at f = 0 and 0.5, with both groups materially active.

---

## 4. Discussion

<!-- D1 -->
### 4.1 Exactness brings fragility

Near coexistence, competition between the two groups acts as integral
feedback and holds temperature exactly. Integral control is sensitive to
added phase lag, which a slowly responding climate supplies (Åström & Murray
2021). The 36 exactly holding states of §3.2 that start stable lose
stability within a response time of about 7 years, and in 32 of them the
limit is shorter than the fast climate response of about 4 years found in a
modern climate model (Held et al. 2010). At lower supplies, exact states
tolerate decades when acetate is fully recycled, over a supply window only
about 5% wide (§4.4). Past the limit, the regulator swings widely
or a population crashes (§3.3).

<!-- D2 -->
### 4.2 The price of durability

Graded feedback gives up exactness and gains durability: a residual
sensitivity of a fraction of a kelvin per e-fold of hydrogen supply buys
tolerance of a 30-year climate response (§3.4). On the computed weakly connected branches, temperature moved
across roughly T\* ± σ as supply changed, so wider spreads gave looser
control.
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
### 4.4 The sink condition

The regulator needs a lasting fate for hydrogen other than methane. Acetate
and dead biomass can return as methane: an Archean carbon-cycle model assumes
acetate recycling (Kharecha et al. 2005), and syntrophic oxidation recovers
acetate as methane without acetate-cleaving organisms (Zinder & Koch 1984).
Acetate leaves the methane system for good only through an oxidant, such as
sulfate (Lovley & Klug 1983) or ferric iron (Thompson et al. 2019), or by
export and burial. In the reference case at f = 0.5 that sink takes about
20 Tmol of acetate a year. Oxidising it would require about 20 Tmol of
sulfate or 160 Tmol of Fe(III) a year. These requirements exceed published
late-Archean estimates of new sulfate (Hao et al. 2022) and are several times
modelled iron recycling (Thompson et al. 2019). An oxidative sink must
intercept acetate before it returns to methane: acetate could diffuse to an
adjacent oxidant-rich layer while hydrogen is consumed where it forms. How
much acetate escaped methane on the early Earth is therefore an open
condition on the regulator.

Recycling trades range for tolerance. As f rises from 0.5 to 1, the sampled
supply window narrows from a factor of 2.0 to 1.05 and moves to lower
supplies (P = 0.229–0.240 at f = 1, with lost biomass exported), and the
feasible imposed warming at the window's geometric midpoint narrows from 24
to 7 K. The exact critical response time rises from about 1 year at f = 0.5
to 21–31 years at f = 1; at the midpoint of each sampled window it varies
approximately in inverse proportion to the window's fractional width. At
f = 1 an exact state near the window's edge tolerates a 30-year response,
and states with feedback from both products follow supply more steeply at
mid-window (ESM S8).

The reference supply of 401 Tmol H₂ per year (§2.2) compares with base-case
fresh geological inputs of 3.4 and 6.1 Tmol H₂ per year (Canfield et al.
2006; Ward et al. 2019); published scenarios with greater outgassing supply
34 and 110 Tmol H₂ per year (Canfield et al. 2006). Fermentation is one
possible source. If glucose fermentation supplied all the reference hydrogen,
about 600 Tmol of organic carbon per year would have to reach fermenters. The
same pathway produces one acetate per two H₂ (Conrad 1999). If half the
acetate from each source became methane outside the shared hydrogen pool,
steady-state accounting gives a coexistence window of 149–189 Tmol H₂ per
year, a factor of 1.27 across. At the midpoint, fermenters would process
251 Tmol C per year, their acetate would supply 64% of biotic methane, and
the lasting sink would take 50 Tmol of acetate per year (ESM S8). Anoxygenic
ecosystems in published models reach methane fluxes comparable to the
model's 65 Tmol CH₄ per year (Kharecha et al. 2005; Ozaki et al. 2018).

<!-- D4b -->
### 4.5 Graded control on the early Earth

Acetate feedback and variation in habitat temperature are candidate routes to
graded regulation on the hazy early Earth. Their strengths would set where an
Archean regulator sat between precision and durability. Habitat temperatures
on a real planet differ by far more than the hundredths of a kelvin that
bought a 30-year margin here: by a few kelvin across today's abyssal seafloor
(Sweetman et al. 2017) and by 30–40 K from equator to pole in Archean
climate models (Eager-Nash et al. 2023; Mak et al. 2023). Spreads of that
size among active, hydrogen-fed habitats with weak exchange would, by
equation (3.1), give a much larger residual sensitivity than on the tested
branches.

Arney et al.'s (2017) young- and modern-Sun pair suggests roughly 1.2 K per
1% of young-Sun flux. On that rough scale the exact window spans about a
fifth of sunlight.

<!-- D5 -->
### 4.6 Stability, assembly and persistence

A stable mixture is not a mixture that forms. Competition between the two
groups is fast, and the climate they regulate is slow, so in one closed
uniform habitat the group favoured at the current temperature removes the other
long before the climate can reverse its advantage. Arrival order, or the
starting temperature, then fixes a single-group world. Incumbency usually
favours the first arrival (Fukami 2015). Here the favoured arrival wins,
whichever came first. In the closed reference runs the controlling community
never formed; it needs somewhere the losing group can persist while the
climate catches up. A real planet has many candidates, from thermally
buffered refuges to dispersal between regions. Persistence can also happen
in place: when methane responded a thousand times faster, two closed
invasions assembled the mixture. Persistence does not by itself give
durable control. Assembly and durability have different
requirements, and a regulating biosphere needs both.

<!-- D6 -->
### 4.7 Conditions

These results come from a conditional model. Table 1 gives the conditions
each ingredient sets, including the dependence of the switch on the loss rate
and the capacity normalisation. The further conditions are these.

*Physiology and habitats.* The switch rests on kinetics transferred from
cultured strains, and strain traits remain fixed. Habitat offsets are
uniform, and every habitat must lie within the physiological support of
273–303.15 K, which limits spreads to about ±8 K around the reference
temperature. The modern seafloor observations and modelled Archean surface
gradient in §4.5 illustrate the scale. The temperature spread among active
Archean hydrogen-fed habitats is unknown, and the residual sensitivity it
implies would also depend on how hydrogen supply is shared among habitats,
how fast they exchange cells and the acetate chemistry.

*Sink and supply.* The oxidant estimates compared in §4.4 do not cap gross
oxidant cycling, and oxidant regeneration and any accompanying reductants
would also have to enter a planetary methane budget. Where the oxidant
reaches the same hydrogen pool, sulfate or Fe(III) reducers can compete for
it at concentrations below those used by methanogens in modern sediments
(Cord-Ruwisch et al. 1988; Lovley & Phillips 1987); the two-guild calculation
applies only if this additional hydrogen uptake is small. Supply is
prescribed as gross delivery to the microbes, which could also include
biologically recycled hydrogen. If productivity depends on temperature, the
two guilds can still coexist at the switch provided that the supply there
falls inside the coexistence window; how productivity responds to
temperature could then alter stability and assembly.

*Climate.* The climate is one published case with an assumed low-methane
bridge, and sunlight enters only as a rigid vertical shift of that curve.
At zero thermal lag the sampled interior states were stable. Both groups
remain present at the two ends of the window, but each warming-side
linearisation there has a growing mode, so stability at the ends is
unestablished (ESM S9). The solar pair behind the scale in §4.5 changes
spectrum and haze together and comes from another case. Atmospheric hydrogen
up to 100 Pa leaves the set point unchanged and moves the reference margin
from 0.15 to 0.12 years (ESM). The costs of durability are local slopes on
four branches, and stability is local to each steady state.

*Assembly.* The bounded assembly checks and the refuge and immigration runs
use instantaneous temperature, and refuge temperatures and immigration rates
are prescribed, not calibrated. The faster-methane test probes the speed of
the methane response, not a shorter physical lifetime: at the reference
hydrogen supply a 10-year lifetime could not sustain the mixture's methane at
all. Habitats that track the surface climate gave no comparable paired test
of the regulating mixture at f = 0 and 0.5: most such runs left the
physiological support, or lost protection during the transient. At f = 0.9
they kept both groups in nine matching pairs, but coexistence there is not
climate regulation (ESM S10). The mixture assembled with buffered refuges
sits at the exact set point, and its margin against slow climate response
was not tested.

<!-- D7 -->
### 4.8 Tests and generality

Any population–environment feedback with a slow environment invites two
measurements: how far the regulated variable drifts with forcing, and how
slowly the environment responds. Stability analysis of that system then
estimates its critical response time, placing it on the precision–durability plane of
figure 3. Mesocosms with controlled supply and
an imposed thermal lag, and biogeochemical models that resolve both groups,
could test the trade-off with the delay-margin analysis used here.

Modern microbial mats are accessible analogue habitats. Their hydrogen levels
vary by orders of magnitude with depth and time of day, and far more of their
fixed carbon leaves as organic acids than as methane (Hoehler et al. 2001;
Bebout et al. 2004). Measuring acetate stocks and turnover in such mats, and
the effect of acetate on the hydrogen acetogens need, would test the acetate
route to graded control. Measuring the share of acetate oxidised by sulfate
or iron rather than converted to methane would test the sink condition.
Measuring habitat temperatures and the exchange of cells between habitats
would test the habitat route. A matched solar sweep of a haze climate would
test the regulator against the Sun's brightening.

Microbial competition can hold a planet's temperature if some of the hydrogen it diverts stays out of methane, but exact control fails when climate responds slowly. Imperfect control lasts far longer, and grows looser
as habitat temperatures differ. The controlling community forms only where
the losing group can persist while the climate catches up.

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
| Hydrogen supply and exchange | Gross H₂ input prescribed. At a 10,000-year methane lifetime, 401 Tmol H₂ yr⁻¹ at reference and 306–611 across the half-recycling window without co-produced acetate. Geological and recycled contributions are unresolved | Feeds the community; atmospheric outlet | Reservoir at 0 Pa; 0–100 Pa leaves T\* unchanged (ESM) |
| Acetate fate | Assumption: removal over 1 yr; fraction f to methane, the rest to a lasting non-methane sink (oxidant, export or burial); lost biomass exported | Sets the methane-yield contrast between routes, and so the supply window | Needs a lasting non-methane sink: at the reference supply 27.7 Tmol CH₄-equivalent yr⁻¹ of acetate and biomass, 20.2 Tmol of it acetate at f = 0.5. The window ratio falls from 2.0 (f = 0.5) to 1.15 (0.9) and 1.05 (1), and closes at f = 1 if biomass also returns as methane |
| Atmospheric methane | Lifetime 10,000 yr assumed; abiotic source quoted by Arney et al. (2016) | Links microbes to climate | Well-mixed column ratio stands for surface CH₄/CO₂ |
| Haze climate T_clim(r) | Arney et al. (2016), case B: 2.7 Ga, 81% sunlight | Provides the haze-cooling branch | One case; assumed bridge to 283 K at zero methane and plateau beyond the data |
| Climate response time τ | Free parameter | Thermal inertia | First-order relaxation of surface temperature |
| Product feedback (dial D1) | Assumed activity form, equation (2.8) | Acetate slows its producers by κ | Methane feedback held off along D1 |
| Habitat spread (dial D2) | Assumption | Habitats offset by up to ±σ, exchanging cells at rate d | Uniform offsets; one shared atmosphere and climate |
| One-cell rule | Assumption, motivated by Mollison (1991) | Finite endpoints of invasions | Ten-year counts; no immigration in the invasion runs (refuges and immigration in ESM S10); continuous crash calculations are read at the first crossing |

---

## Figure captions

**Figure 1. How microbes can set a planet's temperature.** (*a*) Hydrogen
feeds two groups and exchanges with an atmospheric reservoir. Methanogens
make methane, which thickens an organic haze and cools the surface;
acetogens divert hydrogen into acetate, of which a fraction f is recycled to
methane. Temperature shifts the competitive advantage, and the climate responds over
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

**Figure 3. Durability costs precision.** (*a*) Critical response
time τ_c against local sensitivity |S|. Left strip: the 42 exact states (S =
0), 36 on the haze-cooling branch (filled) and six bridge states already
unstable at τ = 0 (open, placed at the strip's base). Lines: the four dial
branches, joining finite margins on one branch; ringed markers show where
each crosses 30 years. Symbols without lines: the 122 graded states of the
earlier grid, 42 uniform states with product feedback (grey, all at the
ceiling) and 80 with resolved habitat spread (green; nine finite). Arrows mark lower bounds at the 10⁴-year search
ceiling. The shaded band marks the price of a 30-year margin, 0.07–0.32 K
per e-fold. (*b*) Steady temperature against hydrogen supply potential P for
uniform habitats (σ = 0, black) and uniform habitat spreads of σ = 1, 3, 6
and 8 K (green, darker for wider), at f = 0.5 with fixed products and cell
exchange d = 10⁻⁴ yr⁻¹. Shading marks the supply range in which a uniform
community coexists (P = 0.229–0.457); the dotted line marks T\*. Open
circles mark the last resolved state on each branch. The σ = 1 K curve
passes through the last point of the d = 10⁻⁴ yr⁻¹ spread branch in (*a*),
at P = 0.30.

**Figure 4. Assembly needs somewhere to persist.** (*a*) Global cell counts
after a rare invader enters, in each direction, with fixed products, f = 0.5
and τ = 3 years. These are finite-census trajectories: a group below one
cell is removed at the next ten-year census (20 and 10 years respectively).
Crosses mark the first one-cell crossings at 18.3 and 7.4 years. (*b*)
Surviving group in all 24 runs:
every acetogen invasion ended with acetogens alone, and every methanogen
invasion with methanogens alone. Diamonds mark the 8 of 12 settings where
the reference mixture of both groups is locally stable. (*c*) Bulk
temperature after an invasion in each direction (fixed products, f = 0.5,
instantaneous temperature). With no refuge (grey), the run ends with the invader alone,
at 294.4 or 273.5 K. With two small habitats held at 278 and 286 K (2% of
the area each, cell exchange 10⁻⁶ yr⁻¹), both histories end at the same
mixed state at T\* (dotted), 281.535 K; the two end markers coincide.

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
Gemini 4 Carbon (Google) reviewed the consolidated manuscript,
figures and supplement.
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
| Arney et al. 2017 | 10.3847/1538-4357/836/1/49 |
| Åström & Murray 2021 | *Feedback systems: an introduction for scientists and engineers*, 2nd edn. Princeton University Press. ISBN 978-0-691-19398-4 |
| Bebout et al. 2004 | 10.1111/j.1472-4677.2004.00024.x |
| Canfield et al. 2006 | 10.1098/rstb.2006.1906 |
| Conrad 1999 | 10.1111/j.1574-6941.1999.tb00575.x |
| Cord-Ruwisch et al. 1988 | 10.1007/BF00411655 |
| Eager-Nash et al. 2023 | 10.1029/2022JD037544 |
| Feulner 2012 | 10.1029/2011RG000375 |
| Fu et al. 2019 | 10.3389/fmicb.2019.02418 |
| Fukami 2015 | 10.1146/annurev-ecolsys-110411-160340 |
| Hao et al. 2022 | 10.1126/sciadv.abn2226 |
| Haqq-Misra et al. 2008 | 10.1089/ast.2007.0197 |
| Held et al. 2010 | 10.1175/2009JCLI3466.1 |
| Hoehler et al. 2001 | 10.1038/35085554 |
| Khammash 2021 | 10.1016/j.cels.2021.05.020 |
| Kharecha et al. 2005 | 10.1111/j.1472-4669.2005.00049.x |
| Kotsyurbenko et al. 2001 | 10.1111/j.1574-6941.2001.tb00893.x |
| Lovelock & Margulis 1974 | 10.1111/j.2153-3490.1974.tb01946.x |
| Lovley & Klug 1983 | 10.1128/AEM.45.1.187-192.1983 |
| Lovley & Phillips 1987 | 10.1128/aem.53.11.2636-2641.1987 |
| Mak et al. 2023 | 10.1029/2023JD039343 |
| Mollison 1991 | 10.1016/0025-5564(91)90009-8 |
| Olsman et al. 2019 | 10.1016/j.cels.2019.06.001 |
| Ozaki et al. 2018 | 10.1038/s41561-017-0031-2 |
| Peters et al. 1998 | 10.1111/j.1574-6941.1998.tb00516.x |
| Qian & Del Vecchio 2018 | 10.1098/rsif.2017.0902 |
| Sagan & Mullen 1972 | 10.1126/science.177.4043.52 |
| Sauterey et al. 2020 | 10.1038/s41467-020-16374-7 |
| Seto & Akagi 2007 | 10.1016/j.jtbi.2007.05.013 |
| Sweetman et al. 2017 | 10.1525/elementa.203 |
| Thompson et al. 2019 | 10.1126/sciadv.aav2869 |
| Tijhuis et al. 1993 | 10.1002/bit.260420415 |
| Ward et al. 2019 | 10.1029/2018JG004679 |
| Watson & Lovelock 1983 | 10.1111/j.1600-0889.1983.tb00031.x |
| Weaver & Dyke 2012 | 10.1016/j.jtbi.2012.07.034 |
| Yi et al. 2000 | 10.1073/pnas.97.9.4649 |
| Zinder & Koch 1984 | 10.1007/BF00402133 |
| Zenodo archive | DOI at release |
