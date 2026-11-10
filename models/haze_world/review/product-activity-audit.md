# Product-activity correction: derivation and scope

Codex, 10 November 2026. Independent audit of the named product-feedback
variant. The implemented relative laws and numerical closure pass the checks below.
This correction is not an absolute thermochemical calibration.

For the reactions written with CO₂ gas, unit water activity and dimensionless
activities/fugacities,

`Q_M = f_CH4 / (f_CO2 f_H2^4)`,

`Q_A = a_acetate a_H+ / (f_CO2^2 f_H2^4)`.

At fixed temperature, critical energy, pH and CO₂, setting
`DeltaG_c = DeltaG_standard + RT ln Q` gives a **positive quarter-power**
dependence of cessation H₂ pressure on the product. More product raises the
H₂ requirement. Relative to reference products the authorized correction is

`pstar_A(T,A) = pstar_A_base(T) (A/A_ref)^(1/4)`,

`pstar_M(T,r) = pstar_M_base(T) [p_CH4(r)/p_CH4_ref]^(1/4)`.

Concentration ratios approximate activity ratios, and pressure ratios
approximate fugacity ratios. Those approximations remain conditional at high
concentration. The reaction definitions and measured final products are in
Kotsyurbenko et al. (2001), section 2.4, p155 and section 3.1, p156:
[primary source](https://doi.org/10.1111/j.1574-6941.2001.tb00893.x).

Use `A_ref = 0.0005 mol/L` (0.5 mM) and `p_CH4_ref = 350 Pa` (0.35 kPa).
For Arney case B, fixed pCO₂ is 0.018 bar = 1800 Pa, so

`p_CH4 = r * 1800 Pa`, `r_ref = 350/1800 = 0.194444444...`.

Using r/r_ref is equivalent only with that explicit reference ratio. Treating
r itself as a methane pressure, mixing Pa with kPa or using the CO₂ mixing
ratio without its total pressure would change the normalization.

The normalized product multipliers are one at their reference products.
Changing products by a factor 16 must multiply the corresponding threshold by
two, after separating the baseline's temperature dependence. Product
inhibition is an increase, not a reciprocal factor.

## Retain the authorized reference convention

The source cultures had measured initial pCO₂ approximately 12 kPa; case B has
1.8 kPa. The current pstar30 inputs are already assumed baseline levels for
the target atmosphere. The product-only variant must **not** silently add a
source-to-case-B CO₂ recalibration. Had one instead transferred thresholds
from the source CO₂ while keeping pH, products and critical energy fixed, the
additional factors would be `(12/1.8)^(1/2)` for acetogenesis and
`(12/1.8)^(1/4)` for methanogenesis. That is a separate scenario, not part of
this correction.

Baseline threshold levels, adopted temperature-shape energies and fixed pH/CO₂
remain declared assumptions. Multiplying by the exact relative product powers
does not make their absolute levels a fitted Nernst reconstruction.

## Zero products and boundary derivatives

As A approaches zero from above, the relative acetogen threshold approaches
zero; methane pressure approaching zero does the same for its threshold.
These are continuous limiting threshold values. The logarithmic free-energy
expression itself is singular at exactly zero product, so do not evaluate
ln(0) and then repair its output. Direct evaluation of the power has the
correct limit. A positive numerical product floor would be a new assumption.

The isolated threshold derivative diverges like product^(-3/4) near zero.
Boundary invasion and Jacobian calculations therefore need care: use the
physical right-hand limit or establish that the full RHS derivative exists.
An undefined derivative of the isolated multiplier does not necessarily make
the full RHS nondifferentiable when its flux is multiplied by zero producer
biomass. Do not infer boundary stability from an undocumented continuation
to negative products.

Product dependence changes uptake and population growth through the threshold;
it does not create or destroy reducing equivalents. The existing combined
inventory identity must still close. Equilibria must solve the product,
population, pressure and methane equations together; fixed-product switch
roots or fixed-temperature winner assignments are insufficient.

## Finite bounds are not physical concentration guarantees

A finite outlet bounds resource pressure: at equilibrium with nonnegative
uptake, `p <= p_atm + J/k_ex`, using consistent hourly or annual units. With
constant positive acetate removal at fixed temperature,

`A* = P_A/k_total <= J_effective/(4 k_total)`.

Here J_effective can be bounded by J+k_ex*p_atm when pressure is nonnegative.
This supply/residence bound can be very large for a long lag. Cold-limited
removal can enlarge it further, or permit accumulation if all removal vanishes.

A positive acetogen equilibrium also requires its resource requirement to fit
below the available resource ceiling. When the product enters only through
cessation pressure, write

`Rstar_A = Rkin_A(T) + pstar_A_base(T) (A/A_ref)^(1/4)`.

For a positive baseline threshold this implies a conditional viability bound

`A < A_ref [(p_lifeless - Rkin_A)/pstar_A_base]^4`,

provided the numerator is positive. This is a fourth-power bound and can remain
enormous when the cold baseline threshold is small. A zero baseline threshold
has no such activity-induced bound. Finite inventory and acceptable aqueous
chemistry are different claims.

Therefore the multiplier alone does not establish that former 37 M or 773 M
pools disappear, nor that all new equilibria are physically plausible. New
self-consistent concentrations must be calculated and reported. Activity,
solubility, pH, nutrient and fixed-CO₂ assumptions still limit interpretation
of large pools even when the mathematical roots are finite.


## Independent implementation checks

The current helper changes only each guild's threshold. All other guild
fields remain identical to the temperature-dependent baseline. Direct checks
of the reference products, zero products, factor 16 products and factor 1/16
products give threshold factors 1, 0, 2 and 1/2 as required. Case-B methane
pressure is computed from its CSV CO₂ pressure. No source-to-target CO₂
recalibration or positive product floor is applied.

An independently reconstructed annual RHS, using the normalized powers and
reading case CO₂ separately from the new helper, agrees with the implementation.
The combined inventory remains closed within about 1.4e-17 mol H₂/L/year in the
product-factor checks. Product inhibition changes rates, not stoichiometric
accounting.

A separate five-variable positive-coordinate equilibrium solve at reference
potential 0.3, f=0.5, tau=1 year gives:

| Quantity | Independent result |
|---|---:|
| Resource pressure |23.15415205 Pa |
| Acetogen biomass |0.0005687760 gDW/L |
| Methanogen biomass |0.0003425058 gDW/L |
| Acetate |0.86796908 mM |
| CH₄/CO₂ |0.1954534860 |
| Temperature |281.28482672 K |

The largest dimensionless root residual is 2.9e-15; agreement with the model's
mixed equilibrium is within 4.5e-14 relative. The result differs from the old
fixed-product switch temperature 281.534823 K, as expected: it solves A and r
self-consistently instead of importing that switch. An independent five-point
Jacobian agrees at 9.3e-10 relative matrix norm and gives maximum real eigenvalue
approximately −0.011336/year. This supports local model stability at this smooth
reference equilibrium, not global attraction or completeness of the root search.

## The large-pool elimination claim fails in the declared model

The two former extreme configurations were re-evaluated with product feedback,
keeping potential 0.6, tau_A=10000 years, the normalized reference habitat and outlet,
and the original recycling variant/fraction:

| Recycling | f | Former fixed-product pool | Product-feedback model state | New pool |
|---|---:|---:|---|---:|
| Constant |0.5|36.70993M|Locally stable acetogen-only|35.25726M|
| Cold-limited |1|773.31154M|Locally stable mixed|405.82210M|

The latter case also retains an unstable acetogen-only root at 706.33897 M.
Every reported candidate was substituted into the independently reconstructed
RHS and inventory balance. Independent Jacobians confirm the two listed local
stability classifications: maximum real parts are approximately −1.0e-4/year
and −4.1095e-6/year, respectively. Their Jacobian matrices agree with the model
within 2e-11 relative norm.

These roots occur at 274.002 K on the **assumed high-methane plateau**, at ratios
about 0.24187 and 0.47918, and use the named physiology continuation below 4 °C.
They are mathematical stress states with implausible ideal-solution acetate
concentrations, not physical aqueous predictions. Their existence is enough to
refute a general claim that adding the quarter power eliminates the huge
pools. It does not validate those states or prove an exhaustive census of
other roots. The correction reduces these concentrations and changes one
community composition, while leaving the larger chemical limitations intact.

## Reproduce

```sh
uv run python models/haze_world/review/product_activity_check.py
```

[Independent check script](product_activity_check.py) and
[numeric results](product_activity_check.json) retain the audited core-file
hash, exact reference tests, equilibrium residuals and long-lag configurations.
