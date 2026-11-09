# Audit of the conditional A. woodii affinity check

Codex (GPT-6), 9 November 2026; reviews `124ef94`.
**The calculations reproduce. They support an affinity sensitivity, not a
calibration or identification of an assay artefact.** Keep the faithful
benchmark unchanged.

The [original check](woodii_affinity_check.py) correctly converts the Pirt
demand into mmol H₂ gDW⁻¹ h⁻¹ and minimizes squared log-pressure residuals.
The [independent checker](check_woodii_affinity.py) reproduces its three
results, tests another objective, perturbs printed pressures and omits each
observation in turn. [Numerical evidence](woodii-affinity-audit.json) includes
inputs and code hashes. Reproduce with:

```sh
uv run python models/haze_world/review/check_woodii_affinity.py
```

## The source supplies an independent maximum-growth constraint

[Peters et al. (1998)](https://doi.org/10.1111/j.1574-6941.1998.tb00516.x)
determined μ_max through washout experiments, following biomass decline
after setting dilution above μ_max (methods, pp. 320–321). Table 2 reports
0.024 h⁻¹ for H₂/CO₂ growth. Their four residual pressures and the 94 Pa
pressure at half maximum growth are reported measurements; the paper does
not fit the particular uptake-plus-maintenance law used here. Gas and liquid
measurements were checked for Henry-law agreement within approximately
12% (p. 320), which is neither a supplied confidence interval for these four
pressures nor evidence about the later bottle assay.

Freeing capacity therefore relaxes an independent source constraint. The
log fits imply μ_max = 0.02056–0.02067 h⁻¹, **14% below** the reported
0.024. This cannot be presented as an equally source-constrained estimate
of K with every other parameter unchanged. No uncertainty for the source
μ_max was recovered.

Growth half-saturation and uptake half-saturation also differ when
maintenance is positive. Under this closure, with s = m + μ_max/Y,

    p_half-growth = p* + K (s + m)/(s − m).

The source's 94 Pa half-growth pressure would imply uptake K = **76.63 Pa**
at p* = 0, or **60.33 Pa** at p* = 20. Those are conditional conversions,
not additional independent observations or a directly measured uptake K.

## The 63–160 Pa range depends on the objective and closure

| Pressure objective | Capacity | p* (Pa) | K (Pa) | Implied μ_max (h⁻¹) |
|---|---|---:|---:|---:|
| Squared log residuals | Free | 0 | 76.083 | 0.020669 |
| Squared log residuals | Free | 20 | 63.467 | 0.020561 |
| Squared log residuals | Fixed | 0 | 160.132 | 0.024000 |
| Squared log residuals | Fixed | 20 | 152.326 | 0.024000 |
| Squared Pa residuals | Free | 0 | 121.157 | 0.021120 |
| Squared Pa residuals | Free | 20 | 114.154 | 0.021064 |
| Squared Pa residuals | Fixed | 0 | 377.233 | 0.024000 |
| Squared Pa residuals | Fixed | 20 | 372.334 | 0.024000 |

Neither objective has a verified measurement-error model. Log weighting
emphasizes relative errors; Pa weighting gives the high-pressure points
greater influence. At p* = 0, the free log fit has log RMSE 0.269 and
pressure RMSE 127.5 Pa. The fixed-capacity log fit has corresponding RMSEs
0.704 and 779.7 Pa. Changing K alone does not closely reconstruct all four
means under the source-constrained closure.

Inverting each observation separately while retaining measured μ_max gives
K = **89.20, 76.63, 222.57 and 432.22 Pa** at p* = 0. The scatter tests the
joint assumptions: constant Pirt coefficients, the saturating uptake form,
cessation level, capacity closure and measurement comparability. It does
not isolate an affinity error.

## What rounding and point leverage change

At the 16 corners formed by perturbing each printed pressure by ±0.5 Pa,
the free log p* = 0 estimate spans only **75.62–76.55 Pa**; the fixed log estimate spans
**159.49–160.78 Pa**. This explicit last-digit sensitivity cannot explain the
spread above and is not a confidence interval. Varying the printed μ_max by
±0.0005 h⁻¹ gives fixed-capacity log K = **149.30–170.74 Pa**, also merely a
rounding scenario.

Leaving out one observation gives free log K = **51.66–91.56 Pa** and
fixed log K = **115.01–204.73 Pa**. Omitting the highest-dilution point makes
the free fit predict washout at 0.01866 h⁻¹, before that omitted 0.020 h⁻¹
living observation. The near-washout point materially controls capacity.

## Consequence for stage 3

The transferred *A. bakii* K = 520 Pa, joined to the *A. woodii* Pirt and
capacity anchor, does not reproduce these *A. woodii* residuals. That is a
useful **conditional mismatch in a cross-strain transfer**, not evidence
that the original *A. bakii* parameter is wrong. The comparison cannot
distinguish strain physiology, growth versus uptake assays, gas transfer,
or inadequacy of the chosen uptake law.

The proposed λ = 1, 1/3 and 1/7 scenarios are useful exploratory choices:
they span several conditional fits while retaining the original transfer.
They are not calibrated corrections or confidence bounds. Applying λ to
both guilds additionally assumes a common assay effect; acetogen data do
not establish that. Describe this as a sensitivity and retain the joint
transfer and measurement limitations when interpreting its outcomes.
