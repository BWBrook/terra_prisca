# Physical coupling: unit, inventory and acetate-lag audit

Codex, 9 November 2026. Independent review of
[`population_coupling.py`](../../../src/terra_prisca/haze_world/population_coupling.py).
The annual-rate implementation agrees with the dimensional and inventory
identities below. No core changes were made. This accepts the bookkeeping of
the declared conditional model; it does not establish an Archean calibration,
a full geochemical carbon cycle, or every proposed attractor.

## Units and source conversion

The physical state is `(p, X_A, X_M, A, r)`: pressure in Pa, biomass in gDW/L,
acetate in mol/L and the dimensionless atmospheric CH₄/CO₂ ratio. Let
`H = 8766 h/year`, `S = 31557600 s/year`, `V` be habitat L/cm², `N_A` Avogadro's
constant and `N_C` the fixed CO₂ column in molecules/cm². Then

`Gamma = V N_A / N_C`

converts local methane mol/L into atmospheric ratio. The donor flux Φ is
already expressed as CH₄-equivalent molecules/cm²/s, so annual H₂ input is

`J = 4 Phi S / (N_A V)`.

The factor four belongs here because each methane equivalent supplies four
H₂. No further factor four belongs in the conversion of methane itself.
The independent all-catabolic-H₂-to-methane round trip gives the same
`3.0e-5 ratio/year` as the existing atmospheric column conversion at reference
supply. The code includes the CO₂ mixing fraction in `N_C`.

For hourly specific uptake q_i and maintenance m_i, define annual quantities

`mu_i = H Y_i (q_i − m_i)`, `D = H d`, `U_i = H q_i X_i`,

`P_i = max(mu_i, 0) X_i`, `C_i = U_i − a_i P_i`.

Here P_i is gross biomass synthesis, C_i is catabolic H₂ and a_i is H₂ allocated
per gram synthesized biomass. The population derivative is
`Xdot_i = (mu_i − D) X_i`. Negative mu_i represents additional starvation
loss. The code correctly removes the corresponding unrecycled biomass:

`Bexport_i = a_i [D + max(−mu_i, 0)] X_i`.

Counting only a_i D X_i would fail the inventory check under starvation.
The a_M=0 option deliberately assigns no donor assimilation to methanogen
biomass and is an optimistic source assumption; a_M=0.0824 is the matched
allocation sensitivity borrowed from the acetogen; it is not a measured
methanogen biomass-composition coefficient.

All local flows are annual in the implemented interface. In particular,
`k_rec = f/tau_A` and `k_other = (1−f)/tau_A` are per year when tau_A is years.
They must not receive another factor H. With the signed annual hydrogen
outlet `E = H k_ex (p − p_atm)`, the equations are

`kappa pdot = J − U_A − U_M − E`,

`Adot = C_A/4 − (k_rec + k_other) A`,

`rdot = Gamma (C_M/4 + k_rec A) + c_year Phi_abiotic − L(r)`.

The last two terms already have ratio/year units. Equivalently, biological
methane flux in molecules/cm²/s is
`(V N_A/S) [C_M/4 + k_rec A]`. There is no duplicate hour-to-year conversion
in the current implementation.

## Combined inventory identity

For fixed kappa, V, N_C and assimilation coefficients, define H₂-equivalent
inventory per habitat litre

`B = kappa p + 4 A + sum(a_i X_i) + 4 r/Gamma`.

Substituting the equations gives

`Bdot = J − E − 4 k_other A − sum(Bexport_i)`
`       + (4/Gamma) [c_year Phi_abiotic − L(r)]`.

Acetate production, its recycling, direct methane production and gross biomass
synthesis cancel internally. This is an open-boundary identity: atmospheric
methane destruction, hydrogen exchange, external acetate fate and unrecycled
biomass carry reducing equivalents outside the represented stocks. It is not a
claim that photochemical methane destruction removes reducing power from the
whole planet; the photochemical products and their later recycling are outside
these five states. CO₂ is also an imposed reservoir, rather than a solved
carbon inventory.

The independent check reconstructs the annual equations without calling the
coupling's `fluxes` or `rhs`. Across eight states/configurations—including
starvation, stored acetate release, f=0/1, the cold-limited recycler and
zero methanogen assimilation—the largest inventory residual is
`3.5e-18 mol H2/L/year`. Maximum relative RHS difference is `3.9e-16`.
Stored acetate can temporarily support methane delivery above current donor
input; an instantaneous supply ceiling would be an invalid transient test.
The integrated inventory identity is the appropriate constraint.

## What acetate lifetime and fraction mean

For constant positive production at fixed temperature, the base model has
`A* = (C_A/4) tau_A`, residence time tau_A and eventual methane recovery
fraction f. Increasing tau_A changes inventory and dynamics, not the stationary
fraction or source. At fixed stationary ecological flows, A* scales linearly
with tau_A.

In the named cold-limited variant let sigma be its logistic temperature
factor. At fixed temperature,

`f_effective = f sigma / (1−f + f sigma)`,

`tau_effective = tau_A / (1−f + f sigma)`.

For 0<f<1, cooling both lengthens residence and reduces eventual methane
recovery, because the competing sink remains active. For f=1 and sigma>0,
ultimate recovery remains one while residence becomes tau_A/sigma. If
recycling is exactly zero and production remains positive, acetate accumulates
without a finite steady pool; this is not permanent removal. With varying
temperature, a parcel's ultimate fate depends on the future hazard history,
not solely the instantaneous fixed-temperature expression.

At f=1 and a stationary acetate pool, biological methane is

`Gamma/4 [J − E − sum(a_i D X_i)]`.

Thus complete acetate recycling equates methane yield per catabolic H₂, but
neither eliminates persistent biomass export nor forces the old model's
capture law. Different physiology, R*, exchange and assimilation can still
change delivery per incoming donor. The old and new ecological models do not
become equivalent simply by setting f=1.

## Jacobian and lag stability

The model's scaled Jacobian is the similarity transform `S_scale^-1 J S_scale`,
so its eigenvalues retain units/year. Independent five-point differences of
the independently reconstructed annual RHS agree with it to `9.6e-10` in
relative matrix norm, for constant and cold-limited recycling at the reference
physical state. Analytic entries also agree, including `J_AA=−k_total`,
`J_rA=Gamma k_rec > 0` and the negative pressure response to added biomass.
Slow-mode eigenvalue differences are below `1.6e-10/year`; the larger absolute
difference, about `3.4e-7/year`, concerns the fast approximately −45937/year
resource mode.

At the reference constant-recycling mixed equilibrium, the slow pair is
approximately `−0.00092601 ± 0.04094346 i` per year; the other eigenvalues are
negative. That is local linear damping for this smooth equilibrium. The
cold-limited Jacobian comparison uses the same physical state as an algebra
check, not its independently solved equilibrium, and is not a stability claim
for that variant.

An acetate pool introduces a relaxation pole, not an automatic Hopf
bifurcation. In a smooth two-state reduction

`rdot = F(r,A)`, `Adot = P(r) − k(r) A`,

the Jacobian is

`[[F_r, F_A], [P_r − k_r A, −k]]`.

A Hopf candidate requires `F_r − k = 0`, positive determinant and a transverse
complex-pair crossing. If F_r remains nonpositive, this reduction cannot
undergo a smooth Hopf merely by increasing lag; its trace stays negative.
It can still lose stability through a real eigenvalue. The full resource and
population states add further feedback paths and timescales, so this reduced
restriction does not exclude Hopf in the five-state system. The full test must
follow equilibrium branches, check that a complex pair crosses while the other
modes remain stable, and then assess the nonlinear orbit. A stable periodic
orbit is not established by a positive real part alone. Temperature dependence
of k_rec contributes to both the methane-source and acetate-removal derivatives.

These checks are at a smooth interior point. Climate vertices, uptake
cessation boundaries and other kinks require separate one-sided or nonsmooth
analysis; ordinary smooth Hopf criteria do not apply there.

## Limits of long-lag scenarios

The reference A* is about 0.882 mM at tau_A=1 year. Holding its stationary
flows fixed gives about 0.0882 M at 100 years, 0.882 M at 1000 years and 8.82 M
at 10000 years. These are consequences of the pool equation, not recovered
Archean concentrations. High-lag equilibria cannot be treated as physically
validated aqueous states while thresholds retain fixed product activities,
CO₂ is imposed, and osmotic/nonideal effects are absent. The original uptake
assays' acetate product concentration was about 0.5±0.2 mM. Long-lag scans
therefore test model structure; they do not by themselves establish plausible
Archean oscillations. This is a limitation to report, rather than a reason to
alter the declared conditional equations silently.

## Reproduce

```sh
uv run python models/haze_world/review/full_coupling_budget_check.py
```

[Check script](full_coupling_budget_check.py) and
[numeric results](full_coupling_budget_check.json) retain the audited core-file
hash. The audit does not fit parameters or validate the full attractor census.
