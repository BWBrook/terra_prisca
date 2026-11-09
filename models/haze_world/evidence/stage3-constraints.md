# Stage-3 constraints: sediment patterns, maintenance and acetate fate

Codex (GPT-6), with independent source-audit subagents, 9 November 2026.
These sources constrain interpretation of the [two-guild experiment](../two-guilds.md).
They do not calibrate an Archean microbial community. Source identities,
locations, access limitations and available hashes are in
[`stage3_sources.json`](stage3_sources.json); the numerical sediment facts
are retained in [`stage3_field_observations.csv`](stage3_field_observations.csv).
Bibliography entries were checked against registered metadata or the primary
publisher, with print dates taken from the primary article where registry
online dates differ.

## Energetic maintenance has the reported 69 kJ/mol slope

[Tijhuis, van Loosdrecht & Heijnen (1993)](https://doi.org/10.1002/bit.260420415),
abstract, reports an activation energy of **69 kJ/mol** for biomass-specific
maintenance Gibbs-energy expenditure, in kJ Cmol-biomass⁻¹ h⁻¹. Its pooled
chemotrophic dataset spans 5–75 °C and aerobic/anaerobic cultures. This is
not a mortality activation energy or a measurement on the selected cold
strains. The standard relative Arrhenius interpretation is

    m(T)/m(T_ref) = exp[(69000/R) (1/T_ref − 1/T)].

The original prefactor, full equation and uncertainty were not recovered.
Applying this relative slope to mol-H₂ maintenance while keeping each
reference demand fixed is a model transfer, not a transcription of a
source-calibrated guild law. The 4 °C experiment also goes 1 K below the
source dataset's stated range. None of the sediment sources below measures
demographic loss at the model's 0.0001, 0.001 or 0.01 h⁻¹ values. Calling
the slow end “sediment-like” would imply evidence we do not have.

## Temperature-dependent sediment patterns are conditional

| Primary source and location | Observation | What it supports |
|---|---|---|
| [Conrad et al. 1989](https://doi.org/10.1111/j.1574-6968.1989.tb03382.x), opening summary | H₂-fed enrichments below 20 °C yielded homoacetogens; methanogens were enriched at 30 °C from paddy soil. | Temperature-dependent routing in those preparations, rather than universal guild exclusion. |
| [Schulz & Conrad 1996](https://doi.org/10.1111/j.1574-6941.1996.tb00299.x), abstract | Permanently cold Lake Constance sediment made methane through acetate cleavage at 4 °C. H₂ was about 0.5 Pa; H₂/CO₂ acetogenesis was endergonic at both 4 and 20 °C. | Cold acetate production was attributed to degradation of organic matter. Acetate accumulation alone is not evidence for successful competition for H₂. |
| [Schulz, Matsuyama & Conrad 1997](https://doi.org/10.1111/j.1574-6941.1997.tb00372.x), Results §3, Table 1 | At 4 °C, adding 80% H₂/20% CO₂ produced CO₂-label contributions of 117 ± 23% to CH₄ and 46 ± 2% to acetate; unamended sediment gave no detectable contribution to either. At 20 °C without amendment, the methane contribution was 32 ± 10%. | Both H₂-consuming routes can operate when cold; hydrogen supply and upstream organic metabolism matter. These percentages belong to separate product pools and do not partition one common H₂ flux. |

The 117% tracer estimate is retained with its experimental uncertainty
(mean ± SE, n = 5); it means essentially all methane, not literal recovery
above stoichiometric yield. The 25–32-day incubations do not determine a
population mortality coefficient. Model cases matching warm methanogen
advantage can therefore be examined conditionally, while contrary cases
remain in the full output. Neither condition identifies the modern or
Archean ecosystem's parameters.

## Acetate-to-methane recovery: end-members, not an estimated interval

Define f_ac as eventual downstream methane recovered per secreted acetate,
relative to the ideal one-mol-CH₄-per-mol-acetate yield. It includes direct
acetate cleavage **or** syntrophic acetate oxidation followed by
hydrogenotrophic methanogenesis. It differs from the fraction of all
methane that originated from acetate, and from bulk organic-carbon burial.

| Primary source and location | Evidence | Limit |
|---|---|---|
| [Kharecha, Kasting & Siefert 2005](https://doi.org/10.1111/j.1472-4669.2005.00049.x), pp. 56–57, reactions R4–R6; p. 60 | A published Archean model assumes acetotrophic recycling. Its bulk organic burial efficiency is 0.2–2%. | A model assumption, not an ancient acetate-fate measurement. That burial fraction is not 1 − f_ac. |
| [Zinder & Koch 1984](https://doi.org/10.1007/BF00402133), abstract | A modern 60 °C syntrophic coculture consumed acetate and produced nearly equimolar methane. | Demonstrates a recovery route without direct acetoclastic organisms; does not calibrate a cold Archean fraction. |
| [Lovley & Klug 1983](https://doi.org/10.1128/AEM.45.1.187-192.1983), abstract | Modern lake sediments showed sulfate-dependent competition for acetate and H₂ even at 60–105 μM sulfate. | An alternative sink needs electron-acceptor supply; these concentrations are not global Archean conditions or f_ac bounds. |
| [Fournier & Gogarten 2008](https://doi.org/10.1128/JB.01382-07), final discussion | Phylogenetics addresses the Methanosarcina AckA/Pta innovation and explicitly permits an older ACS pathway. | Its proposed timing cannot exclude every ancient acetate-cleaving pathway, or the separate syntrophic route. |

Under a neutral-acid convention, the net reactions are

    acetogenesis:         2 CO₂ + 4 H₂ → CH₃COOH + 2 H₂O
    acetate cleavage:     CH₃COOH → CH₄ + CO₂
    syntrophic oxidation: CH₃COOH + 2 H₂O → 2 CO₂ + 4 H₂
    hydrogenotrophy:      CO₂ + 4 H₂ → CH₄ + 2 H₂O.

Either downstream route combined with acetogenesis gives the same net
reaction as direct hydrogenotrophy. Thus at fixed **catabolic** H₂ capture,
complete downstream recovery removes the methane-yield effect of routing
between the guilds. It does not remove biomass demand or transport delays.

The defensible current comparison is **f_ac = 0 versus 1**, with intermediate
values as sensitivities. Zero means export, another persistent sink, or
storage longer than the experimental window; missing acetate consumers
alone would cause accumulation rather than a stationary flux balance.
One means ideal complete recovery by a downstream community whose capacity
is supplied by assumption. Neither is a best estimate. Biomass assimilation
need not be permanent diversion if biomass later remineralizes.

The first router treats this downstream community as **external to the two
explicit competing populations**. Its f_ac can remain nonzero when the
explicit hydrogenotroph is excluded. An extension that instead makes
syntrophic recycling depend on that population must stop recycling when
it disappears, and must return H₂ to the resource pool **or** count the
recovered methane directly, never both. An acetate pool and its timescale
are necessary before interpreting climate transients.

## Implication for the next experiment

The source record does not yet support “acetogens have a modest climate
effect” as a general finding. The answer depends on which cold phenotype
can grow, uptake structure, demographic loss, product activities and
downstream fate. First compare the fixed-temperature end-members and
preserve these dependencies. A later haze coupling must also bridge the
missing 273–277 K physiology and map atmospheric supply and habitat chemistry
without converting a modern bottle threshold directly into a planetary one.
