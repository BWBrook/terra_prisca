# Step 3a: section-abstract review

Codex (GPT-6), 12 November 2026. Reviews `4ef675e` and correspondence
post 3326. Direct edits are confined to `03a-section-abstracts.md`; this note
records the checks. The scope and plain-language decisions from Steps 1–2
remain in force. No model, input or claims-ledger value changed.

## The three new claims

**Cold competition.** The direction is correct for the reference crossing,
rather than a general statement that acetogens grow faster at lower
temperatures. Direct evaluation of the reference guilds gives:

| Temperature (K) | Acetogen break-even H2 (Pa) | Methanogen break-even H2 (Pa) |
|---|---:|---:|
| 278 | 27.614932 | 47.105768 |
| 280 | 24.153670 | 27.921596 |
| 283 | 21.449531 | 19.566694 |
| 286 | 26.986748 | 19.976919 |

The crossing is 281.534822805 K. The lower requirement determines the
winner under the reference one-resource competition. Thus cooling favours
acetogens near the crossing, and warming favours methanogens. On the
haze-cooling branch, methane diversion reduces haze and warms the planet.
The revised Introduction states both halves of that restoring loop.

Reproduce the diagnostic with the existing model:

```python
from terra_prisca.haze_world.population_coupling import reference, switch_temperatures
from terra_prisca.haze_world.two_guilds import guilds
p = reference()
print(switch_temperatures(p.biology))
for t in (278., 280., 283., 286.):
    a, m = guilds(t - 273.15, p.biology)
    print(t, a.rstar(p.biology.loss_h), m.rstar(p.biology.loss_h))
```

**The likely Archean state.** The model supplies candidate mechanisms, not
a probability ranking of real Archean thermostats. Acetate feedback and
habitat variation are now described as routes to graded regulation whose
strength determines model behaviour. The phrase “would most plausibly” has
been removed. The existing capacity-transfer, methane-yield and physiology
conditions remain together in Limitations; the assumed cell-loss rate is
now explicit there too.

**Weaver & Dyke.** The timescale characterisation is supported, and the
precedent deserves specific credit. A read-only independent source review
checked the relevant primary passages. In *The importance of timescales
for the emergence of environmental self-regulation*, DOI
[10.1016/j.jtbi.2012.07.034](https://doi.org/10.1016/j.jtbi.2012.07.034),
section 2.3.1 treats forcing relative to biological adjustment; section
2.3.2, equations 14–17, treats thermal-inertia-induced damped oscillations.
The Introduction now names those oscillations. The contribution is this
haze-competition model's stability margins, graded-response cost and finite
resident–invader tests. Thermal inertia or dynamics in general are precedents.

## Control-theory source check

- [Qian & Del Vecchio (2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5832733/),
  DOI 10.1098/rsif.2017.0902, section 2.2: molecular dilution makes the
  controller memory leaky and introduces adaptation error. Their result
  does not establish a universal ecological precision–lag law.
- [Olsman et al. (2019)](https://nolsman.com/Papers/HardLimitsAIF2019.pdf),
  DOI 10.1016/j.cels.2019.06.001, main-text pages 50 and 56, equations
  10–13: degradation can improve stability while introducing error in their
  specified antithetic network. This is an appropriate molecular precedent.
  The revised Discussion says the ecological result parallels it.

Access limits: Olsman's primary manuscript was accessible. Relevant Weaver
and Qian main-text sections were recovered through indexed primary full
text; direct retrieval was blocked. Weaver's
[repository manuscript](https://eprints.soton.ac.uk/342026/1/YJTBI_7011.PDF)
and Qian's primary page identify the source. This is a targeted check of
the cited passages, not a claim to have read every proof or supplement or
visually verified their figures. No source PDF or extracted text was added
to the repository. This updates the title/abstract-only reading status for
these specific passages in the earlier literature-framing note.

## Model and numerical checks

- `dynamic_core.CHEMISTRIES` contains four cases: fixed, methane-only,
  acetate-only and both products. The abstract now includes all four.
- D1 turns up the acetate correction with methane activity fixed, as in
  `graded-dial-methods.md`. Habitat offsets and cell exchange are correctly
  represented by σ and d. The climate response is a first-order ODE;
  stability comes from its linearised equations, rather than an assumed
  pure time-delay equation.
- Atmospheric methane balances production and removal; the reference
  lifetime is an assumed 10,000 years. Local supply slopes come from the
  equilibrium equations; continuation follows equilibrium branches.
- The existing C0/C1 CSVs recount to 42 exact states: six already unstable
  and 36 finite first losses. The initially stable, ordinary graded subset
  contains 122 states, including 113 censored at 10,000 years and nine finite
  losses. Minimum sensitivity is 0.589645 K per e-fold and minimum finite
  margin 331.426 years. The 122-state summary is now expressly the earlier
  on/off comparison, not all later graded-dial states.
- C57's four threshold brackets still support 0.07–0.32 K per e-fold for
  a 30-year first-loss margin. Directly reread the threshold JSON and the
  24 invasion rows: 12 acetogen invasions end acetogen-only and 12 methanogen
  invasions end methanogen-only.
- The one-year B2 example remains a finite 30,000-year record with late
  swings spanning about 1.3 K. Higher-response-time calculations reach
  fractional-cell populations; they do not establish actual loss of both
  groups. The wording now follows the accepted Step 2 version.
- C56 refutes the prespecified power-law slope band, rather than every
  possible power-law description. C58 has counterexamples at authorised
  refinement points, despite passing the original eligible grid. The
  Results sentence now identifies the proposed slope range and the
  oscillation-based approximation as having counterexamples.

The verification paragraph preserves staged predictions without claiming
that every hypothesis arose before observation. It reports the checked
findings and makes DOI archiving future tense: the package is prepared,
but no Zenodo deposit has yet been made.

## Structure and acceptance

Retain four main Results subsections. C59's atmospheric-H2 check belongs
with Table 1 and the ESM; it remains supported, but needs no separate main
Results subsection. Conditions remain in one Limitations paragraph. The
revised section word counts are 299 / 299 / 291 / 299.

The existing claims checker, including this draft, reports zero errors and
37 warnings for ledger claims outside the selected drafts. The diff check
passes. The wording was compared with E15/E16 and the accepted Steps 1–2
audits. The independent source reviewer also reread the revised Introduction
and Discussion and found their source comparisons and historical scope
supported. No new simulation or full model-test run was required.
