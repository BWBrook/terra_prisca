# A finite hydrogen outlet and the methanogen-only limit

Codex (GPT-6), 9 November 2026. This extends the
[fixed-temperature competition model](two-guilds.md) following
[Claude's review](review/two-guilds-review-2026-11-09.md).
The [switch experiment](competition-switches.md) locates transitions;
it does not yet couple this subsystem to climate.

## Exchange makes the lifeless resource state finite

The resource equation is now

    κ dp/dt = J − Σ q_i(p,T) X_i − k_ex (p − p_atm).

The units are κ in mol L⁻¹ Pa⁻¹, p in Pa, J in mol L⁻¹ h⁻¹, and
**k_ex in mol L⁻¹ h⁻¹ Pa⁻¹**. It is a conductance, not a rate constant
in h⁻¹. The bath-relaxation rate is k_ex/κ. Biomass equations and source
uptake parameters retain their previous units and interpretation.

For k_ex > 0 the lifeless state is

    p₀ = p_atm + J/k_ex,    X_A = X_M = 0.

A guild with finite intrinsic R* can establish only if R* < p₀. At equality
it is marginal, with zero equilibrium biomass. If neither can establish,
the returned state is `lifeless`, at finite p₀. With an established winner:

    p = min(R*_A, R*_M)
    captured H₂ = J − k_ex (p − p_atm)
    X_winner = captured H₂ / q_winner(p).

The outlet does not alter intrinsic R* or the ordering of two feasible
competitors. It determines whether the winner can persist at the supplied
resource level and how much input it captures. Negative exchange denotes
H₂ supplied **from the bath**. In that case uptake/J can exceed one, and
the implementation accounts for the extra source rather than clipping it.

An exact R* tie remains a coexistence family with no selected biomass
partition; product routing is not inferred from its placeholder biomasses.
First-order cases outside the declared concentration domain remain
unresolved. Neither status is treated as demonstrated extinction.

The core retains k_ex = 0 as the explicitly named **no-outlet reference**,
so the earlier sensitivity tables can be regenerated. There the absence
of viable consumers means resource accumulation, not a finite lifeless
equilibrium. All active switch experiments use a positive outlet. The
reference and outlet experiments are distinct physical assumptions, not
alternative numerical treatments of the same system.

The exploratory outlet levels set p₀ = 30, 300 or 3000 Pa at reference
J = 10⁻⁶ mol L⁻¹ h⁻¹ with p_atm = 0. Thus k_ex = J_ref/p₀ is fixed
within each scenario; changing J subsequently changes p₀. These levels,
and the zero-H₂ bath, are assumptions rather than Archean estimates.
Exchange into a prescribed reservoir is not a model of atmospheric storage,
transport or escape to space. Those require a consistent column and habitat
mapping before climate coupling.

## Exact recovery of the existing donor-capture rule

In the **methanogen-only** limit, turn off acetogens and set Pirt maintenance
m_M = 0, cessation pressure p*_M = 0 and bath pressure p_atm = 0. With
saturating uptake q = s p/(K + p), true yield Y and demographic loss d,

    ρ = Y s/d
    R* = K/(ρ − 1),                         if ρ > 1
    η = max[0, 1 − k_ex K/(J (ρ − 1))],     if ρ > 1
    η = 0,                                 if ρ ≤ 1.

For a common conversion c from molar H₂ to CH₄-equivalent surface flux,
set Φ = c J/4 and Φ_K = c k_ex K/4. The conversion cancels, giving exactly

    η = max[0, 1 − Φ_K/(Φ (ρ − 1))].

This is the [existing haze-world rule](README.md), not a fitted
approximation. A regression test calls the existing `capture_efficiency`
function over temperature, supply and capacity cases spanning persistence
and failure to establish. With zero methanogen assimilation, methane
delivery/J has the matching factor η/4. The core exposes `enabled=(False,
True)` for this steady-state comparison.

This equality has explicit limits. The earlier parameter named
`maintenance_flux` is Φ_K, which represents donor leakage; it is not
Pirt maintenance expenditure. Restoring m_M, p*_M or p_atm gives

    Q = m_M + d/Y
    ρ_eff = s/Q
    R* = p*_M + K/(ρ_eff − 1)
    η = max[0, 1 − k_ex (R* − p_atm)/J],

when s > Q. If s ≤ Q there is no finite positive-growth threshold. The
new general model need not numerically equal the old zero-maintenance
closure under the same untransformed parameters. Assimilation also
separates resource capture from methane yield. Tests retain these
differences instead of forcing the models to agree outside the limit.

## Affinity and cessation-energy sensitivities

The [affinity audit](review/woodii-affinity-audit.md) reproduces Claude's
log-pressure fits, but finds important dependence on weighting and capacity.
K is 63–76 Pa when capacity is free and 152–160 Pa when it is fixed under
log weighting; absolute-pressure weighting gives roughly 114–377 Pa.
Free capacity predicts maximum growth about 14% below the independently
measured 0.024 h⁻¹. Individual source-constrained observations imply
different K values. Last-digit pressure rounding has much less effect.
These checks support **sensitivity scenarios**, rather than a unique
correction to the 520-Pa cross-strain transfer or proof of gas-transfer bias.

The active λ scenarios are (K_A scale, K_M scale):

    (1, 1), (1/3, 1/3), (1/7, 1/7), (1/3, 1), (1/7, 1).

Scaling both guilds is an additional common-assay assumption. Under the
first-order acetogen variant, scaling K changes its low-pressure slope;
there is no measured saturation K for that alternative.

The [cessation-energy audit](evidence/cessation-energy-audit.md) corrects
the review's PDF extraction. The publisher's primary HTML gives −5 to −7
kJ/mol H₂ for acetogens and −6 to −8 for methanogens; “35–37/36–38” is a
corrupted minus sign. The existing −24/−28-kJ full-reaction pair is inside
those ranges. The adopted Cartesian bracket is

    ΔG_c,A = {−20, −24, −28} kJ per four-H₂ reaction
    ΔG_c,M = {−24, −28, −32} kJ per four-H₂ reaction.

These are nine representative source-window assumptions, not recovered
strain-specific calibrations. At fixed reference cessation pressure they
alter the temperature shape through (ΔH° − ΔG_c)/(4R). The spurious
−144-kJ interpretation is not used to enlarge the source-supported bracket.

## Verification

`tests/test_two_guilds_outlet.py` checks finite lifeless states, the
first-order survival constraint, signed atmospheric exchange, source
reference anchors, named cold continuations, the exact η limit and its
generalization, and symmetric methanogen assimilation. Direct population
integrations reach predicted pressure and biomass for both winners under
positive exchange, or approach the finite lifeless state. The temperature
extensions are explicitly assumed; agreement of their numerical limits
with the 4 °C endpoint does not validate their physiology.

```sh
uv run pytest tests/test_two_guilds.py tests/test_two_guilds_outlet.py
uv run python models/haze_world/review/check_woodii_affinity.py
uv run python -m terra_prisca.haze_world.competition_switches
```
