# External-review reconciliation and Stage A

Codex (GPT-6), 11 November 2026. Checked against `3f14421`, the two deposited
reviews and the current source. The [original triage](haze-world-external-review-triage-2026-11-11.md)
is preserved as Claude's proposed dispositions. This is the independent reply,
not an endorsement of every sentence in that table.

## Findings and disposition

| Finding | Independent check and disposition |
|---|---|
| X1 | **Accept the local instability.** An equation-assembled Jacobian gives critical lags 0.149214 and 1.102760 years at `f=0/0.5`. The weak-mode approximation agrees. This restricts old stability statements to instantaneous temperature. A modern mixed-layer time constant illustrates physical relevance; it does not calibrate an Archean one. |
| X2 | **Accept the tested lead.** Product feedback is stable on the independently tested lag grid. Implicit differentiation gives a supply-response gain of 0.14156 relative to the methanogen control (85.84% attenuation). Neither a finite grid nor one supply proves universal stability. |
| X3 | **Amend materially.** A narrow temperature spread can reduce instability and smooth supply response, but ±3–6 K does not remove the reported invasion bottlenecks: Fable's own ±6 K invasion minima are log₁₀ counts −573 and −16,541. Its directional rescue examples need ±10/18 K and clip temperatures at the physiological bounds. Independently, the nine-box ±6 K mixed equilibrium is still unstable at a 300-year lag. Bounded finite oscillations, fixed-point stability, and finite survival must be separate Stage B outputs. |
| X4 | **Accept conditional existence; qualify counts and normalization.** The rounded ratio 0.38 gives 297.077 K; the ratio 0.378947 from the printed dry-mass central values gives 297.153 K. Both are above the 297.008 K climate maximum. Independent finer bracketing finds 79 intrinsic restoring crossings among 243 settings, versus the review's 76 detected by the production scanner. The three additional crossings need about 7,149–7,160 Pa, far above the reference 300 Pa lifeless resource ceiling, and are not feasible reference communities. Grid fractions are neither biological probabilities nor a calibrated parameter window. |
| X5 | **Accept with existing qualification preserved.** The R* equality contains thresholds, maintenance, capacity, affinity, yield and guild losses. Turnover moves it when the rest are fixed. The synthesis already says this more carefully than the brief; E1 now does too. |
| X6 | **Accept the examples, qualify the uncertainty.** The MSP crossing is 290.285 K. Fixed-product R* equality is climate-independent; the climate and supply decide feasibility and stability. The reported roughly 1.4 K is a standard deviation under an assumed independent assay-error model, not a 95% error bound or total physiological uncertainty. |
| X7 | **Accept a narrowing supply band, reject an inferred Archean f near one.** The ideal catabolic band is 1/f. Assimilation and the hydrogen outlet change it: the reference full-budget ratios are 1.996 at f=.5, 1.152 at .9, and 1.047 even at 1. The last residual comes from differential permanent biomass export. The existing source audit explicitly distinguishes bulk burial from acetate fate and supplies no quantitative Archean f estimate. Strong routing regulation requires an effective non-methane sink; its historical magnitude is unknown. |
| X8 | **Accept the open budget.** Directly checked zero atmospheric H₂, no photochemical return, and reference input 1.50×10¹² H₂ molecules cm⁻² s⁻¹. That flux alone does not identify a unique source. Atmospheric pressure sensitivity is Stage C; no claim of a closed planetary redox budget is justified. |
| X9 | **Accept the missing precedents.** Source-level checks establish Seto & Akagi's two-species/one-resource temperature regulator, the timescale literature, and Sauterey's coupled ecosystem–atmosphere model. Equation-level novelty comparison remains Claude's Stage D. Sauterey's acetogens use CO; do not describe it as the identical hydrogen-competition experiment. |
| X10 | **Accept.** Independent best responses with E_A=.65 and E_M=.10 give reversed slopes and positive ecological eigenvalues on the extracted cooling branch under both interpolations. C30/C34 remain valid only within their common-E family and instantaneous closure. |
| X11 | **Accept the scope criticism.** The precursor and kinetic-family experiments allow different traits to evolve. Non-evolving terms preserve a dependence by construction; this is not proof of immunity to selection on maintenance or a calibrated genetic trade-off. A like-for-like trade-off experiment remains optional, not an implicit extension of Stage A. |
| X12 | **Accept and repair.** The dense polynomial helper accepted a root without validating its residual. This is independent of whether one platform happens to pass the old exposure tests. The shared repaired helper, finite precursor guard, tests and targeted requalification are recorded in the numerical audit. Archived evidence is retained at its original source epoch. |
| X13 | **Accept.** A separate ordinary-probability backward ODE gives 230.45 cells for the original split and 2,534.92 after adding 87.66/year equally to birth and death. Identical net growth does not identify demographic variance or the survival threshold. |
| X14 | **Accept.** The half-life fraction is ln(2)/ln(N₀/N₅₀); 1.275% follows from the chosen entering/surviving population ratio, not a universal seed-bank property. |
| X15 | **Split finding from hypothesis.** Harmful dormancy depends on the growth-triggered cue, as the equations and existing controls show. The proposed common mechanism for bank cycles and thermal-lag instability is plausible but untested. Keep it a Stage B question. |
| X16 | **Accept the slope sensitivity, correct the count.** The committed B curve has six vertices (five segments) from its maximum to minimum, not four vertices for the whole cooling branch. The reference lies on one segment of slope −721.26 K per ratio. Period, damping and the critical lag inherit that local slope and the assumed methane lifetime. |
| X17 | **Accept as a diagnostic.** Reaction quotients give (12000/1800)^(1/2) and ^(1/4), or 2.582 and 1.607, for the two threshold multipliers; the independent crossing is 279.921 K. Because the baseline anchors were assumed, this is a reference-chemistry sensitivity, not a recovered calibration or transcription correction. |
| X18 | **Accept the limitation; defer extension.** First-window branching solves each guild in a recorded exogenous environment. The finite-census refuge recovery is deterministic. Neither establishes joint stochastic recovery after a guild's loss changes that environment. |
| X19 | **Accept and address boundedly.** Existing auditors overwrite their own committed JSON and several need ignored raw files. A non-mutating replay entry point and a checksum-pinned curated raw companion now distinguish table/algebra replay, raw replay and fresh integration. A prepared payload is not a public deposit; long-producer regeneration is a separate level. |
| X20 | **Accept mechanical repairs.** E11 is current; common-E and instantaneous-temperature restrictions are explicit; missing spaces are fixed; the review brief is visibly historical with corrections; the MSP table's window censoring is named. Main-page restructuring and publication rounding wait for the post-B synthesis rather than rewriting the thesis prematurely. |

## Independent evidence

- [Static checks](external-review-static-2026-11-11.py) and
  [receipt](external-review-static-2026-11-11.json): independent pressure
  bracketing, full-budget supply endpoints, demographic ODE, assay-error
  diagnostic, CO₂ factors and climate geometry.
- [Dynamic checks](external-review-dynamics-2026-11-11.md): independently
  assembled ecological derivatives, thermal-lag block matrix, unequal-E
  optimization, and a bounded distributed-habitat check.
- [Numerical repair and requalification](external-review-numerics-2026-11-11.md).
- [Reproduction levels and payload](../reproducibility/haze-world-core.md).

A separate agent reviewed the static algebra and interpretation scopes. That
review caught an overstatement that acetate diversion was necessary for *all*
pinning: the retained biomass-export sink permits a narrow band at f=1. The
estimands now distinguish those mechanisms.

The static script uses the production guild definitions as factual inputs but
does not call the production crossing finder for its primary root result.
It reports the latter separately, exposing the finite-grid detection difference.
Its demographic ODE does not call the repository's branching solver. Assay
noise assumes independent Gaussian errors; covariance and transfers between
strains remain unidentified. No new empirical parameter distribution is inferred.

### Supply-band derivation

At a fixed-product crossing, write q_i=m_i+L/Y_i and
η_i=1−a_iL/q_i. With J in mol H₂/L/hour, outlet k(p*−p_atm), atmospheric
loss ℓ in ratio/year, and inventory conversion C in ratio/(mol/L),

    J_M = k(p*−p_atm) + 4ℓ/(C H η_M)
    J_A = k(p*−p_atm) + 4ℓ/(C H f η_A),

where H is hours/year and there is no abiotic source in the reference.
The mixed interval lies between these two pure-guild endpoints, with positivity
and stability checked separately. Exact 1/f requires equal efficiencies and
negligible outlet. The full-budget endpoints at reference T* are potential
0.229755 to 0.458542 for f=.5, and 0.229755 to 0.240514 for f=1.
The residual at f=1 is a consequence of assumed exported biomass, not acetate
diversion. Recycling biomass would require an additional budget.

### Source checks and physical interpretation

[Seto & Akagi (2007)](https://pubmed.ncbi.nlm.nih.gov/17588612/) directly
describe one-resource competition and temperature regulation with coexistence.
[Weaver & Dyke (2012)](https://pubmed.ncbi.nlm.nih.gov/22902427/) examine the
timescale separation behind Daisyworld regulation.
[Sauterey et al. (2020)](https://www.nature.com/articles/s41467-020-16374-7)
couple methanogens, CO acetogens and acetotrophs to atmosphere and climate.
These are precedents, not an equation-level identity claim.

As a physical illustration, [Held's GFDL two-layer discussion](https://www.gfdl.noaa.gov/blog_held/3-transient-vs-equilibrium-climate-responses/)
uses a roughly four-year fast surface response and distinguishes surface and
deep heat capacities. It supports treating subannual critical lags as a serious
model-realisation issue. It does not establish a unique relaxation time for
Arney's Archean atmosphere, its ocean, or the particular microbial habitat.
Stage B must report a response-time envelope rather than calling one borrowed
time constant the physical truth.

## Decision and stopping point

Stage A verification: the full suite passed **852 tests** in 167.5 seconds;
the final safe-replay wrapper passed **five targeted tests** after its last
change. The claims checker reports **37 claims, zero errors and warnings**.
The parent also ran compact replay independently: both audits and the fresh
C07 prefix passed. The curated roughly 45 MB payload passed isolated
extraction, all four raw/algebra auditors and the evolution table assessment,
without modifying any of its 579 hashed objects. It is prepared for Zenodo,
not deposited; public raw-data availability remains an explicit unfinished
release task. See its preparation receipt for exact hashes and source epochs.

Writing readiness remains withdrawn. Stage A repairs and packages the record;
it does not validate the old physical thesis. Stage B should separately report
equilibrium stability, bounded finite oscillation, supply gain and finite
invasion survival. A temperature spread is a testable mechanism, not an assumed
cure. Claude should reconcile these amendments and specify that experiment
before its full build. No manuscript products, new deposit or release are
created by this audit.
