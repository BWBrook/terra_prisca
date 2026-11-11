# Stage B design and independent numerical review

Codex independent subagent, 12 November 2026. This reviews the
[Stage B specification](../../models/haze_world/dynamic-realisation-spec.md)
before its decisive B1/B4 calculations. The original PB1–PB7 predictions are
retained. This note separates a meaningful test from the interpretation of
its result; no universal controller theorem is assumed.

## Design findings before numerical results

1. **The integral-control description is local and conditional.** In the
   homogeneous positive community, the exact identity is
   `d ln(X_A/X_M)/dt = n_A − n_M`. The difference in net growth depends on
   hydrogen, temperature, products and the fixed physiology. Only after
   resource elimination and local expansion can this act like an integral
   of temperature error. Atmospheric methane obeys `dr/dt = source − loss(r)`;
   its linear response has a loss term. It is not a second ideal integrator.
   Exact pinning follows from a supply-independent break-even crossing when
   coexistence is feasible. It does not itself prove a universal relation
   between static gain and delay margin. PB1 is a falsifiable model-family
   hypothesis, not an acceptance criterion deduced from control theory.
2. **The matched M-only control is useful, with a restricted interpretation.**
   Hold supply, geometry, chemistry and transport fixed, disable acetogens,
   and evaluate both equilibria on named branches. This measures the effect
   of adding acetogens relative to that biological control. The control can
   occupy a different climate segment, so its slope can differ for geometric
   reasons. Report `dT/d ln Phi` for both states along with their ratio, branch
   and stability. A zero control derivative makes the ratio undefined; do not
   call a zero-over-zero ratio perfect regulation. An absent or unsupported
   control makes the comparison unavailable. Negative ratios are allowed
   algebraically and must not be ranked as stronger attenuation without
   stating that the response changes sign. The static derivative exists for
   an unstable equilibrium, but it is not an attained static climate response.
3. **Delay-margin statuses need censoring.** No crossing found below 10,000
   years is `not detected through 10000`, not mathematical infinity. A state
   already unstable at zero thermal lag has no positive stable delay margin.
   Multiple crossings should be retained; the first loss of the stable branch
   is different from a later restabilisation. Finite bracketing is not proof
   that a narrow stability interval cannot occur between grid points.
4. **B4 has no unique ordinary equilibrium Jacobian under the stated linear
   ramp.** Entry uses `max(-n,0)`, waking uses `max(n,0)`, and the mixed
   equilibrium has `n=0`, dormant biomass zero and active biomass positive.
   To first order with switching factor k and active biomass X,

       delta X' = X delta n - k X max(-delta n,0)
       delta D' = k X max(-delta n,0) - epsilon L delta D.

   The positive- and negative-growth directional derivatives differ. A
   centered numerical Jacobian averages these branches and has no unique
   physical justification. Sector matrices can be useful diagnostics, but
   their individual spectra do not establish the stability of the switched
   system or a smooth Hopf bifurcation. Cubic entry has zero first derivative
   at the switching boundary and therefore a different local structure. A
   bank is not equivalent to a scalar thermal lag simply because both retain
   state. The bank residence time must use L in years, not its input in hours.
5. **Two-layer dynamics are under-specified.** A deep fraction and a ratio
   of time constants do not uniquely define a coupled thermal model. State
   equations, the temperature seen by microbes, coupling normalization and
   equilibrium relation must be fixed before the comparison. A parallel
   weighted two-mode response is distinct from an energy-conserving coupled
   two-box heat balance; do not label one as the other.
6. **PB1's two clauses need separate verdicts.** A failure of the chemistry
   ranking does not necessarily produce a near-pinning long-delay escape.
   Conversely, `|G| < .05` is approximate pinning, not exact pinning. A
   right-censored margin beyond 10,000 is sufficient to assess the 30-year
   threshold, but not to claim stability for arbitrarily long delays. The
   thesis rule must use the actual clause that fails.
7. **Convergence and mixed-state definitions need explicit handling.** An
   implicit derivative at a climate corner is one-sided. A 5% relative error
   at G=0 is undefined; a small absolute tolerance should be fixed. With
   nonzero exchange a guild can occur as a sink in patches where it cannot
   sustain itself, so positive biomass in every patch is not local autonomous
   coexistence. Whole-community presence, local sink stocks and regulation
   are distinct. Grid quantiles may approach physiology-domain boundaries
   as N changes, so support must be checked at each resolution.

These clarifications preserve the stated experimental scope and predictions.
They avoid interpreting a numerical absence, undefined comparison or
nondifferentiable operator as a physical result. B2/B3 remain outside this
initial static audit.

## Independent numerical checks

After the implementation-method freeze (`db09eea`), the
[independent script](dynamic-realisation-review-2026-11-12.py) derives the
homogeneous resource/biomass balances directly, assembles physical flows
without calling the new core's flow function, and computes five-point
finite-difference state matrices at three step sizes. It also perturbs supply
and solves the independent steady-state equations again. The
[receipt](dynamic-realisation-review-2026-11-12.json) retains every selected
state, derivative, delay scan and source hash.

Reproduce without replacing historical evidence:

```sh
uv run python docs/audits/dynamic-realisation-review-2026-11-12.py \
  --compare-production --output /tmp/dynamic-realisation-independent.json
```

### The proposed dominant methane loop fails its reference test

All four homogeneous chemical variants have positive cooling-branch mixtures
at reference turnover/supply for both tested fractions. At `f=.5`:

| Chemistry | Temperature, K | Raw slope dT/d ln J, K | Gain G | First lag crossing, yr |
|---|---:|---:|---:|---:|
| fixed | 281.534823 | approximately 0 | approximately 0 | 1.102760 |
| products | 281.284827 | −1.877567 | 0.14155717 | none detected through 10,000 |
| acetate only | 281.284709 | −1.877743 | 0.14155741 | none detected through 10,000 |
| methane only | 281.534914 | approximately 0 | approximately 0 | 1.102958 |

At `f=0`, fixed and methane-only lag crossings are respectively 0.149214
and 0.149235 years; acetate-only and full-product variants again have no
crossing detected through 10,000 years. The independent control's supply
derivative is −13.264890 K without methane feedback and −13.263667 K with it.
Finite-supply perturbations reproduce the product-feedback derivatives to
about 7e-8 K per log supply. The approximately zero slopes are numerical
round-off near 1e-13, not inferred observational precision.

Thus the methane-only variant preserves the supply-independent coexistence
constraint, but does not obtain long-lag stability here. The algebraic escape
candidate identified before the runs fails dynamically. In contrast,
acetate-only almost reproduces both the full variant's buffering and its
checked stability. PB2's attribution of most stabilisation to the direct
atmospheric methane loop is refuted by these reference controls. These tests
do not establish its performance over the entire B1 grid or every delay.

The important distinction is between **having** a temperature-bypassing loop
and that loop being quantitatively influential. At the reference state the
methanogen chemical cut-off is small relative to its total break-even resource
requirement. The acetate pool provides a separate local feedback. Deleting
one loop at a time is informative; bypassing temperature alone does not prove
dominance.

### Production comparison and one habitat-spread control

All eight independently derived homogeneous mixtures (four chemistries,
`f=0/.5`) match the new core's roots to at worst 1.6e-13 in scaled state.
The independently differenced fixed-temperature matrices differ by at most
6.9e-7 in scaled entries, and implicit derivative numerators by at most
2.2e-9 K per log supply. This is a separate equation/derivative route, not
agreement between two calls to the production Jacobian.

A selected nine-midpoint-habitat, `sigma=3 K`, fixed-product, `f=.5`
mixture has T=281.535322 K and local temperatures 278.869–284.202 K.
Its production root satisfies the independently assembled physical flows
with scaled residual 2.94e-11. Two independent Jacobian steps give raw
community slope −0.07353136 K per log supply. Leading eigenvalues are
−0.00035712/year at a three-year lag, +0.00164637 at 30 years and
+0.00286783 at 300 years, agreeing with the core within 2e-11/year.
The associated methanogen-only geometry is outside the physiological domain;
therefore these numbers do not provide a defined control gain or a PB1
counterexample. No independent complete search for heterogeneous branches
or nonlinear invasion calculation was made.

### A consequential failure of habitat-resolution convergence

One additional bounded check used fixed products, `f=.5`, reference turnover
and supply, with `sigma=1 K`. Starting from each production candidate, I
refined the root using the independently assembled physical equations in
log coordinates, then independently finite-differenced its matrix at two
step sizes. At N=17 and N=33 the refinement changes stocks by less than
9.5e-14 relative, with maximum normalized equation residual 2.9e-14.

| Habitats | Equilibrium temperature, K | Raw dT/d ln J, K | Critical lag, yr |
|---:|---:|---:|---:|
| 9 | 281.535332 | −0.073571 | 7.231507 |
| 17 | 281.535865 | −0.179020 | 16.275554 |
| 33 | 281.537767 | −1.040954 | 102.08536 |

The two derivative stencils agree on the N=33 critical lag within 6.6e-6
years, and the independently assembled spectra agree with production within
1e-10/year. Thus the discrepancy between resolutions is not a finite-difference
artifact. Steady temperatures can agree to a few millikelvin while response
derivatives and delay margins remain far from converged.

This is a counterexample to PB3's expectation of N=33 convergence and a
sub-30-year critical lag for the tested finite approximation. It does **not**
establish a converged continuous-uniform delay margin. No qualified matched
methanogen-only control was found in the producer's search for this setting;
the raw slopes above therefore cannot be used as defined G values or as a
PB1 near-pinning/robustness escape. Empty homotopy is not a proof that a
physically admissible control cannot exist.

### The named two-layer coefficient comparison fails PB4

For homogeneous fixed products, `f=.5`, reference turnover and supply, I
assembled the two-layer block independently from the finite-difference
ecological matrix:

    tau_f Ts' = Teq(r) - 2 Ts + Td
    100 tau_f Td' = Ts - Td,

with biology at Ts. The first crossing occurs at
`tau_f = 0.010963377106 yr`, compared with one-layer
`tau_T = 1.102760078 yr`: a ratio of 0.009941761. All three derivative
stencils agree within 2.3e-12 years. This refutes PB4's factor-of-two clause
under the explicitly frozen two-layer interpretation.

The apparent hundredfold change has a direct mathematical explanation.
For this block the transfer from Teq to Ts is

    H(s) = (1 + tau_s s) /
           [1 + (tau_f + 2 tau_s)s + tau_f tau_s s^2]
         = 1 - (tau_f + tau_s)s + O(s^2).

Its low-frequency effective lag is therefore `101 tau_f`, not `tau_f`.
Neither coefficient is by itself the observed relaxation time of this
coupled system. The result diagnoses the chosen coefficient comparison;
it is not a calibration of an Archean ocean or a claim that a physical
two-layer ocean is universally a hundred times less stable.

### Abiotic-source correction to the earlier supply-band diagnostic

The reference includes a constant abiotic methane source of
5.43771586767e-8 in ratio/year. A resource-to-methane balance must therefore
replace atmospheric loss by **loss minus this source** before attributing
the required methane to either guild. The earlier Stage A static diagnostic
had omitted that small term, while the physical model retained it.

The independently corrected homogeneous fixed-product supply interval starts
at nominal potential 0.229177607. Its upper endpoint is 0.457326965 for
`f=.5`, 0.264064447 for `.9`, and 0.239906633 for `1`. Corresponding width
ratios are 1.995513, 1.152226 and 1.046815. The interpretation remains:
the ideal catabolic 1/f relationship is modified by outlet and differential
permanent biomass export; a narrow residual exists even with complete acetate
recycling. This small arithmetic repair does not identify an Archean acetate
fraction or change the earlier structural conclusion.

### Review of branch-band reporting

The runner's exact homogeneous endpoint formula includes the abiotic
subtraction and agrees with the independently derived balance above. For
other mechanisms its continuation uses 25% multiplicative supply steps.
The last successful points define a **resolved branch segment**, not located
coexistence boundaries or a globally complete supply band. Domain loss,
continuation failure and an outer search limit must remain censoring labels.

Two reporting issues were returned to the parent before accepting the full
map: climate-slope sign alone cannot identify a branch when deduplicating
band starts; and a generic `no_admissible_control` label must not be read as
proof of one particular cause (absence, domain exit, instability or solver
failure). The independent checks above qualify selected states, not every
branch in the eventual map.
