# Feedback sign at the two-guild switches

Codex, 9 November 2026. Bounded independent check of the switch interpretation
in the two-guild review. This checks the committed Arney case-B response and
conditions for a coupled equilibrium; it does not build or establish stability
of the climate coupling.

At both supplied central finite-outlet, fixed-energy MSB switch temperatures,
**less methane warms the planet**. The committed case-B curve has negative
local slope there. The proposed cooling → acetogen dominance → less methane
→ further cooling sequence therefore has the wrong final sign for these
switches.

| Acetogen kinetics | Switch T (K) | CH₄/CO₂ ratio at T | Local dT/dr (K per unit ratio) |
|---|---:|---:|---:|
| Saturating | 281.534823 | 0.195106875 | −721.258 |
| First order | 282.780106 | 0.193163005 | −599.934 |

These calculations use the same piecewise-linear interpolation as
`Response.temperature_k`, with no extrapolation. The first switch lies between
case-B vertices 4–5 (282.005 to 274.002 K); the second between vertices 3–4
(292.002 to 282.005 K). A local ratio decrease of 0.0001 raises temperature by
0.0721 and 0.0600 K, respectively. The switch temperatures were supplied from
the parent analysis; this note independently checks their positions and slopes,
not the ecological root-finding. The working
[figure4.csv](../../haze_response/arney2016/figure4.csv) was verified identical
to its committed Git blob. Numeric provenance is in
[switch_feedback_check.json](switch_feedback_check.json).

If lower temperature favors acetogens and their methane delivery is smaller,
this local sequence instead opposes the initial cooling: cooling favors
acetogens, reduced methane weakens haze cooling, and warming moves selection
back toward methanogens. This is a negative feedback sign, not a stability
proof. The methane-delivery ordering itself must include capture and biomass
allocation, not just a routing factor.

On a branch with dT/dr > 0, the same ecological and source ordering can give
positive feedback: less methane cools, reinforcing acetogens. Case B has a
positive-slope greenhouse branch before its temperature maximum and a small
upturn near its high-methane floor. The present switches are on neither.
Additional crossings, a global transition across the methane maximum, or an
assumed low-methane bridge could still permit bistability or hysteresis. Local
negative feedback at these two points does not disprove those possibilities.

## The fixed-temperature tie need not remain a continuum

At a candidate coexistence temperature T_s, let both guilds have the same
resource requirement p_s = R*_A = R*_M and zero net growth. With common biomass loss d and
specific uptake at coexistence Q_i,

`Q_i = m_i + d/Y_i`.

The resource balance fixes total captured H₂:

`C = J − k_ex (p_s − p_atm)`, with `C > 0`.

At fixed T_s and p_s, any nonnegative allocation of this uptake between guilds
can satisfy the resource balance. Write θ for the fraction captured by the
acetogen. Its steady-state biomass is θ C/Q_A and the methanogen biomass is
(1−θ) C/Q_M. A genuinely mixed state requires 0 < θ < 1; a pure state has an
endpoint value.

Include the model's persistent biomass allocation before methane routing.
If a_i is H₂ allocated per gram synthesized biomass, define

`b_i = 1 − a_i d/Q_i`.

The instantaneous methane source is then

`S(θ) = C/4 [(1−θ)b_M + θ f_ac b_A] + S_abiotic`,

before, or consistently after, the positive unit/geometric conversion from
volumetric delivery to atmospheric flux. All fluxes in the following condition
must use the same units. The default a_M = 0 gives b_M = 1 and an optimistic
methanogen delivery endpoint; it is an assumption.

Let the selected Arney branch give ratio r_s with F(r_s) = T_s, and let L(r_s)
be atmospheric methane removal. A candidate coupled mixture exists only if
L(r_s) lies between S(0) and S(1), resource capture is positive, and both guilds
remain within their kinetic domains. For distinct endpoints, the source
condition selects

`θ = [L(r_s) − S(0)] / [S(1) − S(0)]`.

A strict interior value removes the fixed-temperature composition freedom at
the level of equilibrium constraints and could pin temperature to T_s. Equal
source endpoints provide no such composition constraint. At f_ac = 1,
identical methane yield is restored per catabolic H₂, but source per incoming
H₂ can still differ because b_A and b_M differ. Full acetate recycling alone
does not remove the existing biomass-allocation assumption.

This is an existence condition only. It neither proves that this state can be
reached nor that perturbations decay. Treating composition as an obligatory
0/1 winner at every temperature can omit a mixed coupled branch. Conversely,
the current fixed-T tie's zero-biomass placeholder must not be interpreted as
a physical lifeless community when calculating coupled methane delivery.

## What coupling must test

The first coupled analysis should solve pure branches and the mixed-state
source condition, retain each supported climate branch, and identify which
candidates satisfy resource, energy and kinetic domains. Atmospheric loss and
any low-methane bridge must stay explicit. Stability then needs the Jacobian
or invasion/transient analysis of the actual resource, biomass, methane and
any acetate-delay equations. A negative feedback sign alone cannot rule out
oscillation, delay-driven instability or global hysteresis.

A bifurcation diagram can test for regulation, coexistence, bistability and
loss of consumers. It should not assume a cold trap as its required outcome.
