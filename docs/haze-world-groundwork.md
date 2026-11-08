# Haze-world: evidence and a first experiment

Codex research note, 8 November 2026. This is a proposal for discussion, not a
new fixed plan for Terra Prisca. No haze-world model has been implemented.
Literature reconnaissance and design criticism used a GPT-5.6 Sol subagent
(medium reasoning); the parent Codex session (GPT-6) checked the principal
sources and integrated the proposal.

The useful question is whether temperature-sensitive methane production
reduces or amplifies climate sensitivity, and under which environmental
conditions. Methane greenhouse warming and organic-haze cooling arise from
the same methane supply. Haze is a photochemical product, not a second
organism that can be substituted directly for white daisies.

## What the primary literature changes

| Source | Evidence available to reconstruct | Consequence for our design |
|---|---|---|
| Arney et al. (2016), [10.1089/ast.2015.1422](https://doi.org/10.1089/ast.2015.1422), [open text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5148108/) | Fig. 4: surface temperature against methane for four atmospheric cases; Tables 1–2: atmospheric baselines and temperature/haze checkpoints | The reported haze-onset ratios span CH₄:CO₂ = 0.15–0.28 across these cases. A universal hard switch at 0.1 would discard material dependencies. |
| Mak et al. (2023), [10.1029/2023JD039343](https://doi.org/10.1029/2023JD039343) | Fig. 4: global temperature; Fig. 5: latitude-dependent temperature; Fig. 1: prescribed haze profiles. [Archived outputs](https://doi.org/10.5281/zenodo.8178651) | Their fixed 2.9-Ga, 1-bar, pCO₂ = 3000 Pa atmosphere warms with thin haze at ratio 0.1 and cools strongly with thicker haze. Haze cannot be assumed to cool under every condition. |
| Eager-Nash et al. (2023), [10.1029/2022JD037544](https://doi.org/10.1029/2022JD037544) | Table 1: CO₂–CH₄ grid; Fig. 2: radiative forcing; Fig. 5: temperatures. [Archived data](https://doi.org/10.24378/exe.4347) | A haze-free comparison is needed: methane's own shortwave absorption can offset its greenhouse warming. |
| Sauterey et al. (2020), [10.1038/s41467-020-16374-7](https://doi.org/10.1038/s41467-020-16374-7), [open text](https://pmc.ncbi.nlm.nih.gov/articles/PMC7264298/) | Figs 2–3: coupled microbial ecosystems, methane, climate and reductant supply; supplementary parameters | Coupled microbial–methane–climate models are established prior art. Their results also show why electron-donor budgets matter. The paper offers code/data on request rather than an open archive. |

Earlier foundations include the ecosystem–climate coupling of Kasting et al.
(2001), [10.1023/A:1010600401718](https://doi.org/10.1023/A:1010600401718),
the production budgets of Kharecha et al. (2005),
[10.1111/j.1472-4669.2005.00049.x](https://doi.org/10.1111/j.1472-4669.2005.00049.x),
and the haze-feedback studies of Domagal-Goldman et al. (2008),
[10.1016/j.epsl.2008.01.040](https://doi.org/10.1016/j.epsl.2008.01.040), and
Zerkle et al. (2012), [10.1038/ngeo1425](https://doi.org/10.1038/ngeo1425).
The general methane-feedback idea is therefore not a novelty claim.

## Recommended first step

Reconstruct a published radiative response before attaching population
dynamics. Mak et al.'s Fig. 4 is a useful target because its thin-haze warming
challenges the simplest proposed feedback. Its archive contains 38.3 GB in
one zip and requires Iris to analyse. Inspect the archive inventory first,
then extract the surface-temperature diagnostics and averaging provenance;
keep raw outputs outside Git. This would reproduce a result from archived
outputs, not independently rerun the Met Office Unified Model. No archive
download or remote workload has been launched in this review.

Compare the recovered checkpoints with Arney et al.'s published curves as
different atmospheric/model cases. These differences cannot be attributed to
dimensionality alone: haze properties and background atmospheres differ too.
Do not combine the cases into a single smooth curve without accounting for
those differences. A one-epoch response curve also supplies no validated
luminosity dependence; that would need additional climate calculations or an
explicitly labelled approximation.

The next small biological model could track limiting reductant, methanogen
biomass and atmospheric methane, with haze diagnosed from the chosen
photochemical response. Methane needs a finite source–loss budget. Initially
hold CO₂ and the background atmosphere fixed. Compare temperature-sensitive
production against temperature-independent production, prescribed methane
flux, haze-suppressed and lifeless controls. Report equilibrium stability and
changes in temperature sensitivity; regulation is a possible result, not a
condition for success. Ice, a changing carbon cycle and evolution can be added
when a specific result requires them.

This gives a clear stopping point for the next reconstruction: recover the
published climate checkpoints with reproducible units and averaging, record
what the fixed atmosphere permits us to infer, and then discuss which
biological feedback to attach. A transparent small synthesis and a test of its
limits would already be a useful Terra Prisca product.
