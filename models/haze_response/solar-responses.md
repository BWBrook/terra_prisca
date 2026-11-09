# Solar forcing: recoverable leads

Codex (GPT-6), 9 November 2026. A bounded primary-source search found no
ready, matched hazy-Sun response grid T(CH₄/CO₂, S/S₀). There are useful
checkpoints and separate clear-climate comparators.

| Source | Recoverable information | Scope |
|---|---|---|
| [Arney et al. 2017](https://doi.org/10.3847/1538-4357/836/1/49), Table 3 | At 1 bar, CO₂ = 0.01 bar and CH₄/CO₂ = 0.2: modern Sun 299 K with incoming mean shortwave 342 W m⁻²; 2.7-Ga Sun 272 K with 278 W m⁻². | A second Sun-age checkpoint, not a full methane-by-luminosity grid. Spectrum and coupled haze change too. |
| [Charnay et al. 2013](https://doi.org/10.1002/jgrd.50808), §4.2 and Figs 6–7 | Solar constants 1025.1, 1081.9 and 1120.8 W m⁻² at 3.8, 3 and 2.5 Ga; several CO₂/CH₄ compositions. | Haze is omitted; land configuration also changes. |
| [Mak et al. 2023](https://doi.org/10.1029/2023JD039343) | Seven methane ratios at one 2.9-Ga spectral setup, with prescribed haze. | The previously inventoried archive is a methane grid, not a solar grid. |
| [Claire et al. 2012](https://doi.org/10.1088/0004-637X/757/1/95) | Age-dependent solar spectral parameterization and a public code listing. | Supplies forcing, not climate responses. The current code payload was not run or qualified. |

The immediate next benchmark is Arney's modern-versus-Archean Sun pair,
retaining the actual tabulated forcing and background. A Sun-age experiment
changes UV and bolometric energy together. Multiplying a fixed spectrum by
a luminosity factor is a different controlled experiment and should be
labelled accordingly. Neither interpolation between the two checkpoints nor
substitution of other stellar types establishes a calibrated solar sweep.

[Checkpoint data](solar/arney2017_sun_checkpoints.csv) and
[source/version notes](solar/source_check.json) preserve what was recovered.
No climate model was run or archive payload downloaded for this check.
