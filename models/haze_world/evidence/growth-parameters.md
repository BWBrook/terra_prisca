# Growth yields and maintenance for stage 3

Codex (GPT-6), 9 November 2026. Quantitative anchors are recovered, but no
same-strain, 4–30 °C yield–maintenance dataset matching the historical uptake
assays was found. These sources support a parameterized growth model, not a
calibrated cold-community default. Climate coupling remains a later step.

Data: [acetogen observations](acetogen-growth-parameters.csv),
[four matched chemostat points](peters1998_chemostat.csv),
[methanogen observations](methanogen-growth-parameters.csv), and
[source identity, access and hashes](growth_parameter_sources.json).

## Acetogen anchors

| Primary source | Measurement | Transfer boundary |
|---|---|---|
| [Peters, Janssen & Conrad 1998](https://doi.org/10.1111/j.1574-6941.1998.tb00516.x), *A. woodii* DSM1030, H₂/CO₂ chemostat, 30 °C | Maintenance-corrected yield 1.7 gDW mol⁻¹ H₂; acetate-basis true yield 7.7 gDW mol⁻¹; Pirt intercept 0.40 mmol acetate gDW⁻¹ h⁻¹. | A matched growth/maintenance anchor, not a cold *A. bakii* coefficient. |
| [Neuendorf et al. 2021](https://doi.org/10.1016/j.ymben.2021.09.004), *A. woodii*, 30 °C | Observed H₂-feed yield 0.82 ± 0.08 gDW mol⁻¹ H₂, growth 0.054 ± 0.002 h⁻¹ and uptake 66.9 ± 7.5 mmol H₂ gDW⁻¹ h⁻¹. | SDs from biological triplicates; medium includes yeast extract. Observed yield is not a maintenance-corrected true yield. |
| [Shin et al. 2018](https://doi.org/10.1261/rna.068239.118), *A. bakii* DSM8239, H₂/CO₂ batch | Growth 0.16 ± 0.04 d⁻¹ at 10 °C and 0.53 ± 0.02 d⁻¹ at 20 °C. | Different assay and gas supply from the 2001 uptake experiment; no yield or maintenance recovered. |
| [Muñoz-Duarte et al. 2025](https://doi.org/10.1002/bit.28904), washed acetogen cells | Reports first-order H₂ uptake to approximately dissolved saturation and discusses mass-transfer effects on earlier kinetic fits. | A structural alternative to universal Monod saturation; not a yield/maintenance measurement or permission to edit the faithful 2001 reconstruction. |

Using the 1998 source's biomass-assimilation assumption, 0.0206 mol
acetate-equivalent per gDW, independently reconciles its two yield bases:

    Y_H2 = 1/[4(1/Y_acetate + 0.0206)] = 1.661 gDW/mol H₂,

consistent with the rounded 1.7. Dividing 7.7 by four alone gives 1.925 and
omits biomass assimilation. At zero growth the catabolic maintenance
conversion gives 4 × 0.40 = **1.60 mmol H₂ gDW⁻¹ h⁻¹**.

An independent Pirt fit to the four rounded chemostat means gives true
acetate yield 7.622 and intercept 0.355 mmol acetate gDW⁻¹ h⁻¹, close to the
tabulated values rather than an exact reconstruction of the original fit.
The modern observed-yield check gives 0.054/0.0669 = 0.807 gDW/mol H₂,
consistent with its separately reported 0.82 ± 0.08.

## Methanogen anchors

| Primary source | Measurement | Transfer boundary |
|---|---|---|
| [de Poorter, Geerts & Keltjens 2007](https://doi.org/10.1128/AEM.01885-06), *M. thermautotrophicus* ΔH, 65 °C, pH 7 | True/Pirt yields about 3.1 ± 0.1–0.3 gDW mol⁻¹ CH₄ at low dissolved-H₂-equivalent pressures, rising to 6.9 ± 0.5 at 15–25 kPa. | Thermophile. Apparent H₂-controlled yield is lower; inferred maintenance includes pressure-dependent uncoupling/leakage, not a universal death rate. |
| [Goyal et al. 2015](https://doi.org/10.1186/s12934-015-0336-z), *M. maripaludis* S2, 37 °C, pH 5.6 | Observed exponential yield 3.549 ± 0.149 gDCW mol⁻¹ CH₄; fitted NGAM 7.836 mmol ATP gDCW⁻¹ h⁻¹ and GAM 27.14 mmol ATP gDCW⁻¹. | ATP costs are model fits, not direct cold-strain substrate-maintenance or mortality measurements. |
| [Morii et al. 1987](https://doi.org/10.1002/bit.260290304), *M. arboriphilus* A2 | Observed yield range 1.06–1.42 g cell mol⁻¹ CH₄ in H₂-limited chemostats. | Primary abstract only; temperature, dry-mass convention and maintenance not verified. |
| [Bonk et al. 2019](https://doi.org/10.3389/fmicb.2019.00166), mixed communities at 37 °C | Data/model comparison bounds maintenance below 0.2 kJ Cmol-biomass⁻¹ h⁻¹ under its assumptions. | Includes non-hydrogenotrophic pathways; not an isolated-guild parameter. |

The [cold-isolate evidence](thermal-margins.md) supplies a 15 °C growth-rate
anchor for *M. frigidum*, but no matched yield/maintenance pair. The fuller
CSV preserves other measurements, uncertainty types and unrecovered fields.

## Assay compatibility changes the model design

The historical *A. bakii* 30 °C table gives

    qmax = 760/(20 × 0.18) = 211.11 nmol H₂ h⁻¹ mgDW⁻¹
         = 0.21111 mmol H₂ gDW⁻¹ h⁻¹.

Borrowing the 1998 *A. woodii* maintenance unchanged would demand **7.58
times this entire uptake capacity**, before any growth or mortality. Such a
combination predicts nonviability by construction. It is an assay/strain
transfer failure, not evidence that acetogens lose Archean competition.

Likewise, combining the 2001 uptake capacities with Shin's growth rates
would imply yields of 54.5 and 107.4 gDW/mol H₂. Those are compatibility
diagnostics, not biological yield estimates. Resting-cell uptake, balanced
growth, estimated cell biomass, gas transfer and substrate conditions cannot
be merged as interchangeable organism constants.

## Proposed dimensional contract

For a separately named growth model, keep:

- qmax and substrate maintenance m_H in mol H₂ gDW⁻¹ h⁻¹;
- true biomass yield Y in gDW mol⁻¹ H₂;
- physical dilution and additional mortality d in h⁻¹;
- resource pressure, Km and cessation p* in Pa, or a consistently converted
  dissolved concentration with specified gas/aqueous partitioning.

Under a chosen constant-yield, constant-maintenance closure,

    μ_net(p) = Y [q(p) − m_H] − d.
    Q = m_H + d/Y.
    R* = p* + Km Q/(qmax − Q),       provided 0 < Q < qmax.

If Q ≥ qmax there is no viable stationary consumer. With substrate-dependent
maintenance, solve the net-growth root instead. This is a model contract,
not a uniquely inferred physiological law. Specify starvation behavior and
which losses were already absorbed into a fitted Pirt intercept. Do not add
separate maintenance to an observed yield as though it were a true yield,
or count mortality both in an intercept and as an independent loss.

The unit conversion from the current benchmark is

    μ (h⁻¹) = 10⁻⁶ Y (gDW/mol H₂) q (nmol H₂ h⁻¹ mgDW⁻¹).

Batch Kcomp is not the population selection criterion: R* also depends on
yield, maintenance and demographic loss. Atmospheric H₂ abundance is not
automatically the microbes' dissolved substrate. No verified numerical
Archean H₂ pressure was recovered from Kharecha et al. (2005) in this tranche.
Acetate fate and biomass assimilation must enter a methane/electron balance
before either guild is coupled to the atmosphere.

The most useful next benchmark is the matched *A. woodii* chemostat/Pirt
dataset. Then test the uptake-form and source-transfer alternatives before
choosing cold-guild parameter sweeps. No stage-3 climate model is implemented
or calibrated here.

Reproduce unit and compatibility calculations:

```sh
uv run python models/haze_world/review/check_growth_parameters.py models/haze_world/review
```

[Numerical checks](../review/growth_parameter_checks.json).
