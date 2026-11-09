# Hydrogen competition: a benchmark before climate coupling

Codex (GPT-6), 9 November 2026. Fixed reaction energetics constrains
competition, but does not make its biological thresholds evolution-proof.
The primary studies support a strain-resolved uptake benchmark; they do not
yet supply an Archean methane partition or a climatic set point.
Verified entries: [`haze-evolution.bib`](../../../docs/references/haze-evolution.bib).

| Primary source | Recovered evidence | Use and limitation |
|---|---|---|
| [Conrad & Wetter 1990](https://doi.org/10.1007/BF00291281) | Temperature-dependent H₂ metabolism over 4–80 °C. Abstract reports critical energies of −5 to −6 for acetogens and −9 to −12 for methanogens, **kJ per mol H₂**. | Qualitative thermodynamic anchor. Full strain curves and assay conditions not recovered; no digitized calibration from this source. |
| [Kotsyurbenko et al. 2001](https://doi.org/10.1111/j.1574-6941.2001.tb00893.x) | Cold-adapted MSB retains low-H₂ advantage over *Acetobacterium bakii* across 4–30 °C. Less cold-adapted MSP loses it below 10 °C. | Cold reversal is strain-specific. [Table 2 uptake data](kotsyurbenko2001_table2.csv) provide Vmax and Km, not net-growth thresholds. Figure 1 threshold coordinates are not recovered. |
| [Munoz & Philips 2023](https://doi.org/10.1111/1462-2920.16429) | Eight acetogen strains at 30 °C have H₂ depletion thresholds spanning 6 ± 2 to 1,990 ± 67 Pa, despite sharing the reaction. | [Table 1 values](munoz_philips2023_table1.csv) demonstrate biological diversity. Energetic and ATP differences are inferred, not direct ATP measurements. |
| [Westermann, Ahring & Mah 1989](https://doi.org/10.1128/AEM.55.5.1262-1266.1989) | *Methanosarcina barkeri* 227 changes H₂ Km 4.8-fold and Vmax 5.4-fold between 20 and 37 °C. | Primary abstract establishes physiological temperature dependence, not its evolutionary rate. |

## Data provenance and units

The two CSVs are factual transcriptions of primary publisher tables, read
through indexed full text on 9 November 2026. They contain no source prose
or figure images. Retain them as uptake observations, rather than fitting
population growth to them without biomass yields and maintenance losses.

Kotsyurbenko used 20 mL liquid in 60 mL bottles, pH 7.0 ± 0.2 and measured
CO₂ partial pressure 12 ± 1 kPa. Endpoint products were acetate
0.5 ± 0.2 mM or methane 0.35 ± 0.2 kPa. Table 2 Vmax is **nmol per hour for
the entire 20 mL culture**. Estimated dry biomass concentrations for
*A. bakii*/MSB/MSP were 0.18/0.35/0.33 mg mL⁻¹: divide by 3.6/7.0/6.6 mg
before comparing specific uptake. Uncertainty columns are 95% confidence
half-widths. MSP's 10 °C Km uncertainty is blank because the indexed
transcription is ambiguous; its central estimate of 300 Pa is retained.
The reported adapted-range critical energies (about −5 to −7 for acetogens,
−6 to −8 for methanogens) are per mol H₂, not per four-H₂ reaction.

Munoz used 60 mL cultures, pH 7 and 30 °C, with initial 2.1% H₂ in CO₂ at
1.4 bar and no significant growth. CSV uncertainties are SDs, not confidence
limits. ATP per acetate is inferred using an assumed 75 kJ mol⁻¹ ATP.
A separate, more sensitive detector gave *S. ovata* about 3.0 ± 0.2 Pa;
do not pool it into Table 1. The source's strain-specific acetate activities
must accompany its energetic estimates. Crossref reverses author given and
family names; the bibliography corrects Laura Munoz and Jo Philips from the
primary contribution statement.

## Thermodynamic scaffold

For dimensionless gas fugacities f = p/p_standard, solute activities a, and
water activity near one:

    CO₂ + 4H₂ → CH₄ + 2H₂O
    Q_m = f_CH4 / (f_CO2 f_H2⁴)

    2CO₂ + 4H₂ → acetate⁻ + H⁺ + 2H₂O
    Q_a = a_acetate a_H+ / (f_CO2² f_H2⁴).

Kotsyurbenko §2.4 gives standard 298.15 K values in **kJ per mol reaction**:
methanogenesis ΔG° = −130.7, ΔH° = −253.0; acetogenesis ΔG° = −55.0,
ΔH° = −270.7. These are untransformed constants with the explicit proton
term, rather than pH-7 transformed ΔG°′. Mixing those conventions counts pH
twice. Changing to bicarbonate requires matching speciation and constants.
The gas pressure standard must also match the selected constant set; Pa in
the data table is not itself a dimensionless fugacity.

Neglecting heat-capacity changes gives the temperature approximation

    ΔG°(T) = ΔG°(T_ref) T/T_ref + ΔH°(T_ref) (1 − T/T_ref).
    ΔG = ΔG°(T) + RT ln Q.

This independent derivation uses constant ΔH°, not a fitted thermal trait.
Keep R and ΔG units consistent. If Q = A/f_H2⁴, cessation at an organism's
critical energy ΔG_c < 0 gives

    f_H2,* = [A exp((ΔG° − ΔG_c)/(RT))]^(1/4).

The reversible chemical boundary is ΔG = 0; usable energy ends earlier.
Critical energy, ATP coupling, maintenance, yield and uptake kinetics differ
among organisms. Thermodynamics alone does not specify them or prevent
selection from changing them.

## Next build

First reproduce the measured-temperature uptake comparisons, with biomass
normalization and distinct Km and cessation threshold. Then add explicit H₂
resource balance, biomass yields/losses and product activities, allowing
sensitivity or adaptation in biological constraints. A depletion threshold
is neither Km nor the minimum donor concentration for positive net growth.
Account for acetate fate: acetoclastic methanogenesis may recycle it into
methane, whereas permanent diversion needs another sink.

Transfer to Arney needs care: the competition assays' CO₂ pressure exceeds
the 0.36–1.8 kPa climate cases, and their cold end (277 K) is above the
evolution preview's endpoint (273–274 K). Published competition does not
close that gap. Keep chemistry, organism physiology and climate coupling
separate so their contributions can be tested.
