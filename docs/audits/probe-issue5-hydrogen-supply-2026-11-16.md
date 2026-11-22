# Pressure test, Issue 5: how big is the hydrogen supply, and what provides it?

Claude (Opus 5.5), 16 November 2026, for Barry and Fable. This record follows the same rules as the earlier issues: address each question, fix what is wrong, or dispute it with evidence.

- **Arithmetic.** Q1 and Q3 use stored numbers only. The script is `models/haze_world/review/issue5_supply_scale.py`, which reads `issue4_acetate_fate.json` and writes `issue5_supply_scale.json`. No model is run.
- **Sources.** A Claude Sonnet 5.5 subagent searched and verified the sources. I spot-checked Canfield et al. 2006, Table 12, against the PMC text.
- **Scope.** No new experimental stage.

## Q1. The reference supply in planetary units

The per-litre supply J = 10⁻⁶ mol H₂ L⁻¹ h⁻¹ has no planetary volume of its own. The model gets its planetary scale from one quantity: the methane flux that holds the mixed state's methane ratio, r* = 0.195, against the assumed 10,000-year lifetime. That conversion is 4.011 × 10⁸ Tmol yr⁻¹ per mol L⁻¹ h⁻¹.

| Quantity at the reference state (P = 0.30, f = 0.5) | Value |
|---|---|
| Hydrogen supply | **401.1 Tmol H₂ yr⁻¹** (100.3 Tmol CH₄-equivalent) |
| … becoming methane | 260.1 Tmol H₂ (65.03 Tmol CH₄) |
| … exported as acetate and biomass | 110.9 Tmol H₂ (27.73 Tmol CH₄-eq.) |
| … escaping to the atmosphere at R* | 30.1 Tmol H₂ |
| Total methane flux, biotic plus abiotic | 65.21 Tmol CH₄ yr⁻¹ = 2.44 × 10¹¹ molecules cm⁻² s⁻¹ |

Fable's estimate of about 370 Tmol is correct for the hydrogen that the guilds take up. The 401 Tmol total adds the 30 Tmol that leaves through the atmospheric outlet. The supply potential P = 0.30 is self-consistent: it is the methane ratio that the whole supply would sustain if all of it became methane.

**The range over which the reference results hold.** All results are stated in P, at P = 0.30 or as local derivatives there. In planetary units:

| Range | P | Tmol H₂ yr⁻¹ |
|---|---|---|
| Exact window, f = 0.5 | 0.229–0.457 | 306–611 |
| Exact window, f = 0 | ≥ 0.229 (no upper end) | ≥ 306 |
| Exact window, f = 0.9 / 1 | 0.229–0.264 / 0.229–0.240 | 306–353 / 306–321 |
| Reference supply, lifetime 6–19 kyr | 0.30 | 668–211 |

The 6–19 kyr lifetime range comes from assigning Arney's haze-onset flux to case B (see the model page). At fixed P the planetary flux scales as 1/τ. A different lifetime would also change the abiotic share and the methane response time, so this row rescales only the size of the supply, not the model's results.

**Implied habitat volume.** The per-litre rate implies an effective habitat volume of 4.6 × 10¹⁶ L. That equals a 9-cm active layer over the whole planet, which is a sediment- or mat-like setting rather than a water column.

## Q2. Comparison with sourced fluxes

All values are converted to Tmol yr⁻¹. Each source's identity was checked against its Crossref record. "Verified" means the number was read in the source itself.

| Flux | Value | Tmol yr⁻¹ | Source | Verified |
|---|---|---|---|---|
| CH₄ flux that initiates haze, Archean | ~1–3 × 10¹¹ molecules cm⁻² s⁻¹ | **27–80 CH₄** | Arney et al. 2016 (10.1089/ast.2015.1422), Discussion | yes (arXiv text) |
| Arney's view of that flux | "broadly consistent with" biological fluxes after oxygenic photosynthesis (Kharecha et al. 2005) | — | same | yes |
| Volcanic H₂ boundary flux in Arney's model | 3.5 × 10⁹ molecules cm⁻² s⁻¹ | 0.93 H₂ | same, supplement | yes |
| Present geological H₂ (volcanic, serpentinisation, MOR) | 1.8–5.0 × 10¹¹ mol yr⁻¹ | 0.18–0.50 H₂ | Canfield, Rosing & Bjerrum 2006 (10.1098/rstb.2006.1906), Table 7 | yes |
| Early-Earth H₂ assumed by Canfield et al. | 10 × present (base case); Tables 8 and 13 also run 3.4 × 10¹³ and, with escape reduced tenfold, 1.1 × 10¹⁴ mol yr⁻¹ | 3.4 base; scenarios to 34 and 110 H₂ | same, §7, Tables 8 and 13 | yes (*corrected 21 Nov*) |
| Archean H₂ supply, volcanic plus water–rock | 4.7 + 1.36 × 10¹² mol yr⁻¹ (Fe²⁺ 0.19 + 1.4) | 6.06 H₂ (Fe²⁺ 1.59) | Ward, Rasmussen & Fischer 2019 (10.1029/2018JG004679), Table 1 | yes (*corrected 21 Nov*: the earlier "1.5–6 each" was the §2.1 order-of-magnitude sentence; 1.5 is iron) |
| Maximum serpentinisation H₂, one Earth mass | 3.0 × 10¹² mol yr⁻¹ | 3.0 H₂ | Guzmán-Marmolejo et al. 2013 (10.1089/ast.2012.0817) | yes |
| Mid-ocean-ridge serpentinisation, modern | ~10¹² mol yr⁻¹ | ~1 H₂ | Worman et al. 2016 (10.1002/2016GL069066), abstract | yes |
| Maximum abiotic CH₄, one Earth mass | 6.8 × 10⁸ molecules cm⁻² s⁻¹ | 0.18 CH₄ | Guzmán-Marmolejo et al. 2013, quoted by Arney | yes |
| Modern total CH₄ emissions, 2008–2017 | 576 (top-down) / 737 (bottom-up) Tg | **35.9 / 45.9 CH₄** | Saunois et al. 2020 (10.5194/essd-12-1561-2020), Table 3 | yes |
| Modern natural CH₄ emissions | 218 / 371 Tg | 13.6 / 23.1 CH₄ | same | yes |
| Early-Earth primary production (Fe-based dominates) | 2.8 × 10¹⁴ mol C yr⁻¹ (Fe-based 1.7–5.0 × 10¹⁴; H₂-based 2.9 × 10¹³) | 280 C | Canfield et al. 2006, Table 12 | yes (checked by me) |
| Archean anoxygenic NPP, limited by electron donors | ≤ ~2.75 × 10¹² mol C yr⁻¹, counting only new donors and excluding recycling by design | ≤ 2.75 C | Ward et al. 2019, §§2–3 | yes |
| Modern primary production | 4 × 10¹⁵ mol C yr⁻¹ / 104.9 Pg C yr⁻¹ | 4,000 / 8,740 C | Canfield et al. 2006, Table 12 / Field et al. 1998 (10.1126/science.281.5374.237) | yes |

**What follows from these numbers:**

1. **The methane scale is right for a haze.** The model's 65 Tmol CH₄ yr⁻¹ lies inside Arney's haze-onset range of 27–80. It is 1.4–1.8 times modern total emissions and 3–5 times modern natural emissions.
2. **Named fresh geological inputs fall short by about two orders of magnitude.** The reference supply is 118 times Canfield's 3.4 Tmol H₂ yr⁻¹ base case and 66 times Ward's 6.06. *Corrected 21 Nov after Codex's review:* this is a comparison with selected fresh-input scenarios, not a bound. Canfield et al. also ran 34 and 110 Tmol H₂ yr⁻¹. Kharecha et al.'s anaerobic Case 3 spans 1.7–68.4 Tmol yr⁻¹ of fresh volcanic H₂ and 35–172 Tmol yr⁻¹ deposited into the ocean, because atmospheric recycling raises gross delivery above fresh input. The model prescribes gross delivery to the microbes. Abiotic methane is 2–3 orders of magnitude short of haze onset, as Arney argues.
3. **A fully fermentation-fed reference supply would need about 600 Tmol C yr⁻¹ reaching fermenters** (602; 1.5 mol C per mol H₂, Q3). For scale, that is about 7% of global NPP or 15% of marine NPP, and twice Canfield's burial-based 280 Tmol C yr⁻¹ for 3.8 Ga; Canfield's 34-Tmol H₂ reduced-escape scenario reaches 1,100 Tmol C yr⁻¹ of anoxygenic production. *Withdrawn 21 Nov after Codex's review:* the comparison with Ward's 2.75 Tmol C yr⁻¹ (which excludes recycled electrons by design) and the inference that this flux requires oxygenic photosynthesis. Kharecha et al.'s anaerobic Cases 2–3 give about 10–80 Tmol CH₄ yr⁻¹, which brackets the model's 65, and Ozaki et al. show iron and hydrogen phototrophs amplifying methane release. The source of J stays open.
4. **The Arney match is partly by construction.** The assumed 10-kyr lifetime was itself bracketed by assigning Arney's onset flux to case B, so agreement with the 27–80 Tmol range is a consistency check, not independent support.
5. **Fable's recollection is broadly right.** Base-case geological hydrogen is a few Tmol H₂ yr⁻¹, which in methane equivalents is a few percent of the haze requirement. The modern scale is confirmed at ~576 Tg top-down. *Corrected 21 Nov:* published higher-outgassing scenarios do reach tens of Tmol and more: 34 Tmol at standard escape and 110 Tmol with escape reduced tenfold (Canfield et al., Tables 8 and 13), and up to 68 Tmol of fresh volcanic H₂ in Kharecha et al.'s Case 3 (Codex's reading).

**Not verified:**

- A global rate in Sleep et al. 2004.
- The 2025 Global Methane Budget update.

*Recovered by Codex, 21 Nov* (`probe-issue5-codex-review-2026-11-21.md`, §3): Holland 2002, table A3, gives 4.8 ± 3.6 Tmol H₂ yr⁻¹ for present-day input; Kharecha et al. 2005, table 2 and fig. 12, as above; Ozaki et al. 2018, fig. 2 and supplement; Conrad 1999, table 1, gives the one-third H₂-derived share for ideal glucose degradation with complete methane recovery, with departures in both directions.

## Q3. A fermentation-fed supply

When fermenters degrade carbohydrate at the low hydrogen that competition maintains, they make C₆H₁₂O₆ + 2 H₂O → 2 CH₃COOH + 2 CO₂ + 4 H₂. That is two acetate, 16 electrons, for every four hydrogen, 8 electrons. Two thirds of the reducing power therefore reaches the methane system as acetate, which bypasses the hydrogen competition. That ratio is the most hydrogen fermenters can make from carbohydrate. Lipid-rich substrates give a similar split.

**Framing.** *Revised 21 Nov:* fermentation is one possible source of J, not an established one. If J is fermentation hydrogen, then:

- "changes in hydrogen supply" means changes in the organic flux that reaches anoxic decomposition: productivity, minus remineralisation by oxidants and burial before fermentation;
- the regulator holds temperature against changes in the biosphere's own productivity, not against geological forcing;
- supply is no longer strictly exogenous, because productivity can itself depend on temperature. At an exact state T is fixed, so the guilds still coexist at the switch provided the supply there stays inside the coexistence window (*corrected 21 Nov*, following Codex). In graded and transient states it adds a loop that the model omits.

**Co-delivered acetate.** Suppose fermentation acetate shares the acetogens' fate f, as it should: both feed the same pool. Then a fraction f of it becomes methane that the competition does not control. The exact window then follows from η_M(J − e) + 2fJ = n for methanogens alone and fη_A(J − e) + 2fJ = n for acetogens alone. Here e is the outlet at R* and n is the methane needed, both from the stored parts.

| f | window ratio, model as written | window ratio, fermentation-fed | H₂ supply at mid-window (Tmol yr⁻¹) | biotic CH₄ outside competition | acetate leaving for good (Tmol yr⁻¹): fermenters + acetogens |
|---|---|---|---|---|---|
| 0 | no upper end | no upper end | 401 (reference) | 0 | 200.5 + 21.2 = **221.7** |
| 0.5 | 2.00 | **1.27** | 168 | **64%** | 41.9 + 8.4 = **50.2** |
| 0.7 | 1.45 | 1.12 | 130 | 70% | 19.5 + 3.5 = 23.0 |
| 0.9 | 1.15 | 1.04 | 107 | 74% | 5.4 + 0.9 = 6.2 |
| 1 | 1.05 | 1.01 | 99 | 76% | 0 |

**Conclusion.** A fermentation-fed supply keeps the exact plateau, because competition still sets T*. It does narrow the window, and at f = 0.5 fermenter acetate supplies about two-thirds of the biotic methane flux. *Corrected 21 Nov:* that is a flux share, not a measure of control; a climate sensitivity would need a separate calculation. It also tightens Issue 4's condition. The lasting acetate sink becomes about 50 Tmol yr⁻¹ at f = 0.5 (50 Tmol sulfate or 400 Tmol Fe(III)) and about 220 Tmol at f = 0. That is more than published new-sulfate and modelled iron-recycling fluxes (Issue 4).

*Withdrawn 21 Nov:* the inference that a biosphere this productive is probably oxygenic (see Q2, point 3). Each row holds only at its stated evaluation supply: the f = 0 row at the original 401 Tmol H₂ yr⁻¹, the others at their geometric mid-window. At the original supply and f = 0.5, fermenter acetate alone would yield 100.3 Tmol CH₄ yr⁻¹, above the 65.03 needed. The bypass assumes acetate reaches methane by cleavage or by hydrogen transfer outside the contested pool; syntrophic oxidation that releases H₂ back into that pool would change the allocation (Conrad 1999).

**Arithmetic only.** These rows apply the stored parts to an added supply-proportional methane source. They are not model runs. The model has no fermenters, and figures and stability margins were not recomputed for this case.

## Q4. Proposed wording, for Barry's decision (superseded 21 Nov; see Revised Q4 wording)

**§2.2**, after "the reference input is J = 10⁻⁶ mol H₂ L⁻¹ h⁻¹":

> Scaled to the planet by the methane flux that holds the reference state against the assumed lifetime, this is about 400 Tmol H₂ yr⁻¹: 260 Tmol becomes methane, 110 Tmol leaves as acetate and biomass, and 30 Tmol escapes to the atmosphere. The resulting 65 Tmol CH₄ yr⁻¹ lies within the range that Arney et al. (2016) found necessary to form haze. Archean volcanoes and serpentinisation supplied perhaps 1–10 Tmol H₂ yr⁻¹ (Canfield et al. 2006; Guzmán-Marmolejo et al. 2013; Ward et al. 2019). J therefore stands for hydrogen released by fermenters degrading the organic matter of a productive biosphere, and a change in J for a change in the productivity that feeds them.

**Table 1, hydrogen supply row:**

| Ingredient | Basis | Role | Condition |
|---|---|---|---|
| Hydrogen supply and exchange | Assumption; planetary scale set by the methane lifetime: about 400 Tmol H₂ yr⁻¹ at reference (306–611 across the f = 0.5 window) | Feeds the community; atmospheric outlet | 40–400 times Archean geological hydrogen, so implies fermentation of about 600 Tmol C yr⁻¹, which also delivers acetate. Reservoir at 0 Pa; 0–100 Pa leaves T* unchanged (ESM) |

**§4.4**, a new paragraph after the acetate-fate paragraph:

> A fermentation-fed supply sharpens this condition. Fermenters deliver about two acetate for every four hydrogen. Whatever share of that acetate returns as methane is methane the competition does not control. If it shares the acetogens' fate, at f = 0.5 it is about two-thirds of the biotic methane. The exact window then narrows from a factor of 2.0 to 1.3, and the lasting sink must take about 50 Tmol of acetate a year; at f = 0 it takes about 220 Tmol. The regulator then acts on the hydrogen share of a fermentation-driven methane cycle.

**§4.6 or the limitations**, one sentence:

> The model treats supply as exogenous and omits fermenters. If productivity, and so supply, depends on temperature, graded and transient states gain a feedback loop the model does not include, although the exact plateau is unaffected.

**My recommendation.** Adopt all four as written. The abstract and main message need no change: "as hydrogen supply changes" stays true once §2.2 says what the supply is. On adoption I would:

- add claims C69 (supply scale and source comparison) and C70 (fermentation co-supply arithmetic);
- add a short ESM subsection (S8e) with the fermentation table;
- add the new references: Canfield et al. 2006, Guzmán-Marmolejo et al. 2013, Ward et al. 2019 and, if cited, Saunois et al. 2020.

A model variant with explicit fermenters would be a new experimental stage, and I am not proposing one.

## Reconciliation after Codex review (21 November)

Codex reviewed this record (`probe-issue5-codex-review-2026-11-21.md`, `9189bae`). It recomputed all five fermentation rows from the saved endpoints and found they balance. It also recovered the four sources I could not read. I accept its corrections, and they are applied in place above, each with a note:

- **Fresh-input comparison.** "Geology falls short by two orders of magnitude" is now a comparison with named base cases: 118 times Canfield's 3.4 and 66 times Ward's 6.06 Tmol H₂ yr⁻¹. Canfield's 34- and 110-Tmol scenarios and Kharecha's Case 3 inputs are listed alongside. I checked Ward's Table 1 (4.7 volcanic + 1.36 water–rock) and Canfield's Tables 8 and 13 in the source texts myself.
- **Withdrawn.** The ">200 × Ward" productivity comparison. The inference that the flux requires oxygenic photosynthesis. The framing "J stands for fermentation hydrogen". The source of J stays open, and fermentation is an example.
- **Evaluation supply.** Each fermentation row is labelled with its evaluation supply. The script now stores the planetary window ends (148.6–189.0 Tmol H₂ yr⁻¹ at f = 0.5) and the fermenter-acetate methane at the original supply (100.3 Tmol CH₄ yr⁻¹ at f = 0.5).
- **Arney match.** The agreement with Arney's onset range is partly by construction.

**Gemini's two additions.** Codex recommends both. I have seen them only in Codex's rendering.

- **§3.2, weak mode.** I confirmed the §3.2 numbers against stored results:
  - the period is 119.56826 yr and the damping time 4,853.910 yr (C20);
  - the weak-mode estimate is 0.14921427 yr (`docs/audits/graded-dial-independent-2026-11-12.json`);
  - the independent stability crossing is 0.14921426 yr (`docs/audits/continuum-characteristic-main-map-2026-11-12.json`).

  C58 already records that the formula passes the original grid, which includes this reference, and fails at two refinement states. C20 and C58 therefore cover the sentence, and no new claim is needed.
- **§4.4, oxidant access.** The sentence replaces the literal co-location requirement with access to the acetate flux before it becomes methane. It cites culture and sediment competition experiments (Cord-Ruwisch et al. 1988, 10.1007/BF00411655; Lovley & Phillips 1987, 10.1128/aem.53.11.2636-2641.1987; both identities checked in Crossref).

## Revised Q4 wording (21 November), for Barry's decision

Codex's wording, with two changes Codex has not yet seen. In A1 I add Canfield's high-input scenarios (34 Tmol at standard escape, 110 with reduced escape; read in his Tables 8 and 13), so the base cases do not read as the full range. In A3 I add the final sentence citing Kharecha and Ozaki, as Codex suggested.

**A1. §2.2**, after "the reference input is J = 10⁻⁶ mol H₂ L⁻¹ h⁻¹":

> At the assumed methane lifetime of 10,000 years, the reference supply scales to 401 Tmol H₂ per year. Of this, 260 goes to methane, 111 leaves in acetate and biomass, and 30 enters the atmosphere. Base-case fresh geological inputs are 3.4 and 6.1 Tmol H₂ per year (Canfield et al. 2006; Ward et al. 2019), and published scenarios with greater outgassing reach 34–110 Tmol (Canfield et al. 2006). The model prescribes gross delivery to the microbes, which could also include biologically recycled hydrogen.

**A2. Table 1, hydrogen supply row, "Basis" column:**

> Gross H₂ input prescribed. At a 10,000-year methane lifetime, 401 Tmol H₂ yr⁻¹ at reference and 306–611 across the half-recycling window. Geological and recycled contributions are unresolved.

The existing condition stays unchanged: "Reservoir at 0 Pa; 0–100 Pa leaves T\* unchanged (ESM)".

**A3. §4.4**, a new paragraph after the acetate-fate paragraph:

> Fermentation is one possible source. If glucose fermentation supplied all the reference hydrogen, about 600 Tmol of organic carbon per year would have to reach fermenters. The same pathway produces one acetate per two H₂ (Conrad 1999). If half the acetate from each source became methane outside the shared hydrogen pool, steady-state accounting gives a coexistence window of 149–189 Tmol H₂ per year, a factor of 1.27 across. At the midpoint, fermenters would process 251 Tmol C per year, their acetate would supply 64% of biotic methane, and the lasting sink would take 50 Tmol of acetate per year. Anoxygenic ecosystems in published models reach methane fluxes comparable to the model's 65 Tmol CH₄ per year (Kharecha et al. 2005; Ozaki et al. 2018).

**A4. §4.6**, after the sentence on acetate fate:

> Supply is prescribed. If productivity depends on temperature, the two guilds can still coexist at the switch provided that the supply there falls inside the coexistence window. How productivity responds to temperature could then alter stability and assembly.

**B1 (Gemini). §3.2**, after "raises the margin from 0.15 to 1.10 years (ESM)":

> The 10,000-year methane lifetime sets the removal rate of the atmospheric stock. At the reference state with no acetate recycling and an instantaneous temperature response, a small disturbance oscillates with a period of 120 years and an amplitude decay time of 4,850 years. A thermal response time of just 0.15 years cancels this weak damping, as the local estimate $P_{\rm osc}^2/(2\pi^2 t_d)$ predicts here.

**B2 (Gemini). §4.4**, after the oxidant budget:

> An oxidative sink must intercept acetate before it returns to methane. Acetate could diffuse to an adjacent oxidant-rich layer while hydrogen is consumed where it forms. Where the oxidant reaches the same hydrogen pool, sulfate or Fe(III) reducers can compete for it at concentrations below those used by methanogens in modern sediments (Cord-Ruwisch et al. 1988; Lovley & Phillips 1987). The two-guild calculation then applies only if this additional hydrogen uptake is small.

**On adoption:**

- **Claims.**
  - Add C69, the conditional planetary scale and the named source comparisons, with the supply labelled.
  - Add C70, the static fermentation budget, with each row's evaluation supply.
  - Stamp both to the evidence commit.
- **ESM.** Add S8e with the fermentation table. Its f = 0 row is labelled at the original supply.
- **References.** Add Canfield et al. 2006, Ward et al. 2019, Conrad 1999, Cord-Ruwisch et al. 1988 and Lovley & Phillips 1987.
- **Unchanged.** The abstract and the main message stay as they are.

**My recommendation.** Adopt A1–A4 and B1–B2. B1 explains the 0.15-year margin that §3.2 already reports.

## Decision and application (22 November)

Barry, in chat on 22 November 2026: "Adopt all", answering "Adopt the revised Issue 5 wording?" (A1–A4 and B1–B2).

Applied as worded above:
- §2.2: A1, after the paragraph on equation (2.4).
- §3.2: B1.
- §4.4: B2 after the oxidant budget, and A3 as a new paragraph, ending with a pointer to ESM S8.
- §4.6: A4.
- Table 1: A2.
- ESM S8: a new paragraph on planetary scale and fermentation (C69, C70), and table S8e, generated by `esm_tables.s8_acetate` from `issue5_supply_scale.json`.
- Claims C69 and C70, stamped to `56a4609`; CLAIM_USE maps both to S8.
- References: Canfield et al. 2006, Conrad 1999, Cord-Ruwisch et al. 1988, Lovley & Phillips 1987 and Ward et al. 2019, all checked in Crossref. The reference table is now sorted alphabetically.

Checks: the claims checker reports 70 claims, 39 cited, 0 errors. The four targeted paper tests pass.
