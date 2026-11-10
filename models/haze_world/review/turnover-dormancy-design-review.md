# Turnover/dormancy design audit before the new experiments

Codex (GPT-6), 10 November 2026. This audits the equations and inference in
the [specification](../turnover-dormancy-spec.md), independently of the T1–T3
outcomes. It does not calibrate turnover, dormancy or extinction probabilities
for the Archean.

## 1. Equilibrium invariance has a well-mixed scope

For a single habitat without migration, the proposed switching law has a
useful property when `ε > 0`:

- If `g < L`, waking is zero and active biomass obeys
  `X' = (g−L−σ)X < 0`. A positive active resident cannot be stationary.
- If `g > L`, entry is zero. The dormant equation gives
  `Z' = −(ρ+εL)Z`, so stationarity requires `Z=0`; active biomass then grows.
- A positive stationary resident therefore has `g=L`, `σ=ρ=0`, and `Z=0`.

Thus every well-mixed equilibrium embeds the original equilibrium with zero
dormant biomass, and there is no additional positive-resident stationary
state from this mechanism. The resource and methane equations also reduce
to the reference at those states. This supports equality of stationary
locations and the well-mixed `R*` switch. The condition `ε>0` matters: an
immortal dormant pool can supply additional stationary stocks when waking
is zero.

This argument does **not** apply habitat by habitat with migration. At an
ordinary source–sink equilibrium, local active growth balances exchange,
so `g_j−L` need not be zero. Switching can remain active and create a
stationary dormant pool, changing capture, source–sink partition and climate.

A concrete counterexample is the independently checked three-patch reference
anchor in `tests/test_habitat_equilibria.py`, with `f=0.5`, exchange
0.001/year and 278/286 K refuges. Its local active net growth rates are:

| Habitat | Acetogens, /year | Methanogens, /year |
|---|---:|---:|
| Bulk | −3.82416×10⁻⁶ | +2.65155×10⁻⁶ |
| Warm | −3.947809 | +0.000465811 |
| Cold | +0.000541832 | −2.549295 |

Embedding that state with `Z=0` at switching factor 10 produces dormant
source terms of 5.43975×10⁻⁶ gDW/L/year for warm acetogens and
2.37505×10⁻⁶ for cold methanogens under the chosen cubic ramp. The named
linear ramp gives 5.75376×10⁻⁶ and 3.37700×10⁻⁶ respectively. Its new RHS
is not zero under either choice. The assertion
that every spatial equilibrium is unchanged is therefore false before any
new experiment is run.

Spatial invasion experiments should prepare their own conditional resident
equilibria, potentially including dormant biomass. An old active-only state
with `Z=0` may instead be used as an explicitly non-equilibrium initialization,
but it must not be labeled the new model's resident equilibrium.

## 2. Stationary locations do not prove unchanged stability or basins

For the named **linear** control, the ramp has one-sided derivatives at
`g=L`. At a well-mixed resident equilibrium, entry responds at first order
to a resource deficit while waking multiplies an initially zero dormant
stock. The active linear response need not equal the old Jacobian; a
finite-difference Jacobian straddling both sides does not complete the
stability analysis.

The chosen default **cubic smoothstep**, `c(x)=x²(3−2x)` on `[0,1]`, is
different: `c'(0)=0`. At a well-mixed resident equilibrium, all switching
contributions then have zero first derivative. Reordering the variables
gives the old resident Jacobian and additional decaying dormant modes
`−εL`. On each defined side of a climate-curve corner, resident stability
therefore inherits the reference classification. This stronger local result
does not establish identical finite-dose basins or spatial equilibria.

For a rare missing guild in a fixed, well-mixed background, its invasion
sign is preserved. When `g<L`, `ρ=0` and the two-stage linear block is
triangular with negative eigenvalues `g−L−σ` and `−εL`. When `g>L`, `σ=0`
and the eigenvalues include the positive active rate `g−L`. This preserves
the rare-invasion barrier of an acetogen-only background. It does not prove
that dormancy leaves all resident-community stability or finite-dose basins
unchanged.

Likewise, T1 bistability in an isolated bulk is not a theorem of T2 history
dependence. Refuges export cells and methane and alter the shared atmosphere.
On the low-methane greenhouse branch, methane from a warm refuge can warm the
bulk toward an invasion threshold. The refuged system has its own equilibria
and basins. KT2/KT3 remain predictions to test, rather than consequences of
the T1 map.

## 3. Thermal crossings and climate-regime boundaries are different

The preview's statement that there is no switch below 2.44×10⁻⁴/hour is
too broad. Direct evaluation of the reference `switch_temperatures` gives
273.188120 K at `L=2.3×10⁻⁴/hour` and 273.786025 K at
`L=2.4×10⁻⁴/hour`, both inside the named physiological continuation. At
`L=0.0043/hour` there is still a crossing at 297.567517 K, above the
published climate response's maximum.

A physiological `R*` crossing, a feasible mixed equilibrium on a particular
radiative branch, and a stable climate regime are separate objects. T1 must
locate the actual feasibility/stability boundaries, not equate disappearance
of a climate thermostat with disappearance of every thermal crossing. The
microbes determine the coexistence temperature in this model; the climate
response still determines whether that temperature is reachable and whether
the feedback is stabilizing.

An additional numerical distinction occurs when `T_sw` equals an exactly
flat continuation of the climate response. If feasible positive mixtures span
that ratio interval, the stationary solutions form a family rather than a
finite list of isolated roots. A root finder that samples an identically
zero residual must report the interval, not reinterpret its samples as
distinct isolated equilibria. Such plateau-contact structure depends on the
named climate interpolation and continuation.

## 4. The demographic rule is a Gaussian approximation

For a scalar birth–death process in a prescribed environment, let `N(t)` be
the corresponding mean count and `u(t)` the single-lineage terminal survival.
The backward equation gives the exact identity

    Λ⁻¹ = 1/N(t_out) + ∫ b(t)/N(t) dt
         = 1/N(t_in)  + ∫ δ(t)/N(t) dt,
    Λ = N(t_in) u(t_in).

If one deep, interior minimum dominates, `log N` is approximately quadratic
there with curvature `κ>0`, death varies little over it, and endpoint terms
are negligible, then

    Λ ≈ N_min / (δ_min W),   W = sqrt(2π/κ),
    N_50 ≈ ln(2) δ_min W.

`W` is an effective local Gaussian width, not the entire unfavorable period
`τ` used in the seed-bank estimate. A single minimum alone is insufficient:
skewness, broad tails, varying rates and endpoint terms can matter. A
multitype process need not have a scalar reduction at all. KT4's 10% accuracy
is an empirical prediction for applicable first bottlenecks; terminal or
monotone minima and nonpositive curvature have no such Gaussian width.

The KD3 estimate similarly assumes the reference unfavorable duration and a
large dormant stock at entry. Dormancy changes uptake and the climate path,
so that reference duration is not a rigorous bound on the new duration.
The proposed one-to-three-times range remains a testable prediction, not a
guarantee derived solely from the decay inequality.

## 5. Two-stage branching implementation and controls

The new [branching module](../../../src/terra_prisca/haze_world/dormancy_branching.py)
orders types as `[X_j,Z_j]` within each positive-area habitat. Active birth
and death are evaluated by the frozen reference helper; dormant birth is
zero and death is `εL`. Entry and waking are conservative type transitions;
each stage migrates with origin-row rate `d w_destination`. Applying the
forward mean-count operator reproduces both physical pool derivatives after
the area-to-count conversion.

Sampled rates and conversion matrices are interpolated linearly. The usual
calculation solves the per-type backward equation in log survival. A wake
edge can open after a dormant probability has become smaller than floating
point range, making a log-ratio trial overflow. An error-controlled positive
operator step handles that case: exact constant birth–death maps and a
positive time-ordered CTMC propagator are composed symmetrically, compared with two half steps,
and the logarithmic solver restarts. Tiny type tails are retained; neither
cell populations nor probabilities receive invented seeds. The CTMC
propagator uses positive uniformization terms, integrating the affine rate
matrix's ordered products in a Bernstein basis. This preserves the leading
probability of a newly opened multi-hop wake/migration path; a single
midpoint matrix exponential need not have the correct leading coefficient.
The known row-sum invariant is restored after roundoff. Constant generators
use scaled positive uniformization and squaring, avoiding tiny negative
entries from a generic exponential on very stiff conversion rates.

Disconnected constant-transition blocks dispatch to the frozen solver. With
zero switching and zero initial dormant counts, active probabilities recover
the reference **bit for bit**. Dormant initial cells, if supplied, remain an
additional population and cannot be claimed to disappear from the comparison.

Eleven controls pass, covering zero-switch identity, one-way conversion and
pure-death closed forms, time-varying four-type conversions against an
independent forward no-birth fundamental matrix, no-death certainty,
physical count-flow agreement under both ramps, stiff conversion kernels and invalid inputs. A forced wake-opening
example first decays a dormant lineage by `exp(−999)`, then restores finite
survival through an earlier wake interval. It matches independent quadrature
to better than 3×10⁻⁷ relative, and tighter integration agrees within
2×10⁻⁸. This validates finite-time lineage survival in the recorded
environment, not establishment or a coupled stochastic climate endpoint.
Four additional prescribed-environment stress controls cover 100,000 years,
three habitats, exchange 0 or 10⁻⁹/year and `ε=0.1/0.0001`; each completes
in less than two seconds on the local test machine. These exercise the
probability solver and physical rate helper, not coupled ecosystem trajectories.

The first-window convention, Poisson versus fixed-count distinction, and
conditioning on the other guild's survival carry forward from the accepted
bottleneck review. Local census removal and global guild survival remain
different quantities, especially for isolated habitats.

## 6. Conditional resident starts

`dormancy_starts.py` correctly eliminates the stationary dormant pool in
density coordinates. For each guild it solves

    [diag(ρ + εL + d) − d 1 wᵀ] Z = σX.

With `ε>0` this is a nonsingular M-matrix, so a nonnegative source gives a
nonnegative bank. The active, hydrogen, acetate and methane equations must
then be refined together; imposing the bank alone does not make an old
spatial state stationary.

The first start implementation selected positive stationary roots without a
stability certificate. The new `resident_stability` gate now records full
conditional spectra at two finite-difference step sizes and, at a climate
corner, separately on both radiative sides. Perturbations stay inside the
neighboring source segments. Only supported cubic-ramp roots with agreeing,
strictly negative leading eigenvalues qualify. The classifier excludes the
competing guild; it certifies a stable resident preparation, not resistance
to invasion. A linear-ramp switching corner is labeled unqualified instead
of being silently averaged into a smooth Jacobian.

The highest-r qualifying root is still a selection rule, not a global root
count. Its seeded search inherits qualifying roots found by the old-model
start search; failure to find a candidate is not a proof of nonexistence.
One positive-area habitat has identically zero exchange regardless of the
nominal `d`, so the well-mixed embedding shortcut now applies in that case
too. Regression controls cover both climate-side spectra, rejection of an
uncertified root and the one-habitat identity.

One cubic start was independently checked: three default habitats, exchange
0.001/year, `ε=0.01`, methanogen resident. The stationary residual is
1.98×10⁻¹⁶ and dormant-balance residual 2.22×10⁻³⁰. Conditional Jacobians
at finite-difference relative steps 10⁻⁵, 10⁻⁶ and 10⁻⁷ consistently have a
leading eigenvalue near −9.88942×10⁻⁵/year. This particular start is stable;
the check is not a blanket result for every spatial root.
