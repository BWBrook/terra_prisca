# Step 3b: paragraph-framework and accuracy review

Codex (GPT-6), 13 November 2026. Reviews `a2fda04` through `3eeb6e7` and
correspondence posts 3333, 3336 and 3346. Edits cover the paragraph abstracts
and reference notes. No model, input or claims-ledger value changed.

## Framework decision

Keep the 25-paragraph plan: five Introduction, seven Model, six Results and
seven Discussion paragraphs. Each revised abstract has three or four
sentences. The plans and coverage tables now agree with the abstracts,
including the switch/loop pointer to I4.

Keep R3 separate: stability of a steady state, oscillating regulation over a
finite record and a population bottleneck are different outcomes. Keep R5
as a compact paragraph within the trade-off Results subsection. It carries
the distinct message that failed proposed summaries make branch-specific
reporting necessary; detailed fits and refinement diagnostics stay in the
ESM. No additional main figure or Results subsection is proposed.

## M6: discreteness and the extinction assumption

Mollison (1991), section 4.6, discusses an epidemic model that recovers from
a fractional infected individual. This supports the reason for addressing
discreteness. It does not calibrate the model's total one-cell threshold or
ten-year count interval. M6 now calls the rule chosen, specifies the total
population, and attributes the epidemic-model example as one discussed by
Mollison. D6 retains the chosen removal rule and limits interpretation of
continuous crash calculations to the first fall below one cell.

The source was checked in the local text at lines 1790–1800. The paper
stays in ignored `local/sources/paper_refs/`. No source text is reproduced
here. DOI: 10.1016/0025-5564(91)90009-8.

## D4: analogue mats and the proposed test

Hoehler (2001) and Bebout (2004) support the mat hydrogen/methane context.
Hydrogen *levels* are measured in depth profiles; calling those levels
hydrogen supply confuses concentrations with fluxes.

One reference-note correction was necessary: Bebout's Analytical methods
include organic-acid analysis accounting for acetate, and its carbon-balance
Results report organic-acid fluxes. The earlier blanket statement that it
has no acetate data was too strong. The relevant local text is at lines
221–225 and 305–318. Those measurements do not supply the model's
acetate-feedback law or habitat-temperature calibration.

D4's proposed measurements remain our own proposal. Acetate turnover and
temperature variation alone constrain only part of the mechanisms. The
revision adds acetate stocks, effects on hydrogen requirements and cell
exchange. These correspond to product feedback and habitat connectivity,
without claiming that modern mats identify an Archean regulator.

## D5: late-invader dominance

Fukami (2015), section 2.1, treats arrival-order effects broadly and notes
the attention given to inhibitory/prior-residence effects. Contrasting our
late-invader wins with incumbency advantage is appropriate. It is not a
reversal of every type of priority effect.

Direct recount of `figures/dynamic_realisation/invasions.csv` gives:

- 12 acetogen-into-methanogen runs ending acetogen-only;
- 12 methanogen-into-acetogen runs ending methanogen-only.

These are C52's chosen-census outcomes. Both directions end with one group,
so the results concern survivor identity and the assembly of a stable mixed
community. They do not show that arrival order decides whether a planet
ever acquires any regulator. The revised D5 removes that inference. Fukami
is cited for the ecological interpretation in D5; R6 reports our own data.

## Model and result wording

| Location | Correction and evidence |
|---|---|
| I1/I2/I4/I5 | Keep the checked thermal-inertia precedent, stable-loop condition and generic Seto–Akagi model attribution. Describe culture kinetics as transferred. Remove the unsupported broad equilibrium-only framing. |
| M1 | Attach the kinetics source to the transferred strain data; specify that the maintenance temperature correlation is transferred too. |
| M2 | Atmospheric exchange can import or export hydrogen. Recycling fraction f controls acetate return to methane; assimilation and biomass retention also affect methane yield. See `population_coupling.fluxes`. |
| M4 | Accepted: the acetate correction is `(C/C_ref)^(κ/4)`, with methane activity fixed along D1. |
| M5/M7 | First loss of stability, rather than the slowest response ever tolerated. Dated specifications preserve staged predictions; they do not mean every organising hypothesis preceded observation. |
| R1 | Exact holding operates within the positive-coexistence supply interval under fixed product activities. |
| R2/R3 | The 42-state split and finite oscillation example stand. Longer-response calculations diagnose bottlenecks; they establish neither a universal monotone oscillation-to-collapse path nor joint finite extinction. |
| R4 | The 122 states are the initially stable graded subset of the earlier on/off comparison, with 113 right-censored margins. Smoothness is local near the exact limit on the tested branches. |
| R5 | PD2 proposed a slope range of 1–2.5 on each branch, rather than a single shared exponent. C58 passes the original eligible grid and has counterexamples at two authorised refinement points. |
| R6 | C52 compares fixed and both-product feedback, f=0/.5, τ=0/3/30 years, in both invasion directions. The revised text identifies the actual comparison. |
| D1/D3/D6 | Keep near-coexistence integral interpretation, give Weaver–Dyke credit for damped oscillations, and gather conditions in one paragraph. Our nonlinear crash results are not attributed to the Daisyworld paper. |

Existing scope is governed by E15/E16 and claims C05/C06, C52 and C54–C59.
The earlier Step 1–3a audit evidence remains applicable;
no new numerical experiment was required.

## Independent checks and source record

One read-only delegate audited model/Results wording against code and
evidence. Another checked only the M6/D4/D5 source boundaries and C52.
Claude's completed eleven-reference search was not duplicated. I checked
the key source passages and the invasion-table design/endpoints, then both
delegates reread the revisions and found no remaining material issue.

The four local PDFs used in the targeted check have these SHA-256 values:

| File in `local/sources/paper_refs/` | SHA-256 |
|---|---|
| mollison1991.pdf | 57937a28d3105c7860039e4a808d93ce3fd2525aa915b225bf9cde81cd0d2a04 |
| fukami2015.pdf | 895a9e2d58ee227bb85d016468b65d9e22f60ec53aa23f497bf0bea1c728122f |
| hoehler2001.pdf | 38981b947477bed5c7bd87ac6696b8a05fbd8a3bfe619991d059fef6199cb353 |
| bebout2004.pdf | b42df241d563f228e61d6c7420c1e3476f941aa447e62d2ab517b81784b1c3e0 |

Reference tags resolve to the draft's DOI-key table. Structural checks
confirm 25 abstracts and three or four sentences per abstract. The claims
checker reports zero errors and the same 37 warnings for ledger claims
outside these short drafts. The diff check passes. No production-code test
suite was needed for these prose-only changes.
