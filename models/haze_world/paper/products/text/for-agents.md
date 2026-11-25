---
document: agent-facing paper
study: haze-world regulator — microbial competition for hydrogen as a climate thermostat on a hazy early Earth
status: internal draft, consolidated after five pressure tests; not yet submitted or released
human_paper: models/haze_world/paper/03c-full-draft.md (+ esm/esm.md, products/text/brief.md)
claims_ledger: models/haze_world/synthesis/claims.csv (single source for all products; checked by tools/claims.py)
interpretation: models/haze_world/synthesis/estimands.md (what each analysis bounds; allowed and forbidden phrasings)
governing_docs: [AGENTS.md, docs/vision.md, models/haze_world/synthesis/jrsi-format-notes.md, docs/audits/consolidation-plan-2026-11-23.md]
authority: Barry W. Brook decides public release, submission and any correspondence outside the collaboration
updated: 25 November 2026
---

# The haze-world regulator for agents: what it established, how to verify it, and how not to break it

This is the paper written for an agent arriving cold. The human paper argues; this one indexes. It says
what is claimed, where each number lives, which commands regenerate it, what has been superseded, and
where the open edges are. When this file and a primary artefact disagree, the artefact wins and this file
is wrong: fix it in the same commit.

## 1. Read order and trust

1. This file, then `models/haze_world/synthesis/estimands.md` (E1–E22; E17–E22 cover the five pressure
   tests and the headline phrasings), then `models/haze_world/synthesis/claims.csv`. Quote a claim only
   with its limit.
2. `models/haze_world/paper/03c-full-draft.md` for the argument; `models/haze_world/paper/esm/esm.md`
   for the machinery, including the staged predictions and their failures (S6).
3. The review record in `docs/audits/`: `probe-issue1-*` to `probe-issue5-*` (pressure tests),
   `consolidation-plan-2026-11-23.md` and `consolidation-codex-review-2026-11-23.md` (latest wording
   decisions). Board discussion is exported in `docs/correspondence/` (threads 150, 151, 161, 165, 192).
4. `models/haze_world/README.md` and the stage pages beside it are a research history. Their older
   framings are superseded where the ledger says so.

`status` is *supported* (checked against its evidence by an agent other than its author), *provisional*
(awaiting that check), *refuted* or *superseded*. `basis` says how the value was obtained; `limit` says
what it does not cover. C38 is the only provisional row and stays so by decision (trap 12).

## 2. The answer, as claims

- **Is there a set point?** Yes, in the model: the mixed community holds temperature at
  T\* = [281.5]{.C06} K under instantaneous climate, warmer than a methanogen-only world (C06). It is a
  model temperature under transferred physiology, not an Archean estimate (E1).
- **What does exact control need?** A lasting, route-dependent hydrogen sink other than methane (C68).
  With half the acetate recycled the exact window spans a supply factor of [2.00]{.C67}; it narrows to
  [1.05]{.C67} at full acetate recycling with biomass exported (C67). The reference mixture needs
  f below [0.78]{.C68}.
- **How fragile is exact control?** The f = 0 reference loses local stability at a climate response
  time of [0.149]{.C63} yr; at f = 0.5, [1.10]{.C63} yr (C63). All 36 initially stable exact states of
  the original inventory lose stability by [7.08]{.C54} yr; six more are unstable at zero lag (C54). At
  f = 1, sampled exact margins reach [21.3]{.C67}–[30.7]{.C67} yr inside the narrow lower-supply window
  (C67). Past the limit a 1-yr lag keeps both groups for 30,000 yr while oscillating (C51); 10- and
  100-yr lags crash a population (C52 context, §3.3).
- **What does durability cost?** On four dial branches a 30-yr margin costs a local sensitivity of
  [0.070]{.C57}–[0.316]{.C57} K per e-fold of supply (C57). The original 122 graded states have
  margins of at least [331]{.C54} yr (C54). Weakly connected spread communities follow the no-fit
  relation of equation (3.1) (C60); spreads of 1 and 3 K move temperature by [1.91]{.C61} and
  [5.41]{.C61} K over the uniform coexistence range with margins of centuries (C61).
- **Does it hold against imposed warming?** Supply and imposed warming share one closed-loop factor;
  graded states follow by |S|/(kE) (C62). Fixed-product exact states hold T\* for F from
  [−15.47]{.C63} to [8.14]{.C63} K (C63). Cases A and C also give exact states; case D does not (C64).
- **Does the mixture assemble?** Not in a closed, uniform habitat: all [24]{.C52} reference invasions
  end with the invader alone (C52). In the four fixed-product, zero-lag runs the resident goes within
  decades while temperature takes millennia to cross T\* (C65). Buffered refuges (C09) and any tested
  immigration (C66) assemble it.
- **How big is the supply?** About [401]{.C69} Tmol H₂ per yr at the assumed 10,000-yr methane
  lifetime, far above base-case fresh geological inputs (C69). A fermentation-fed supply with half its
  acetate recycled narrows the window to [149]{.C70}–[189]{.C70} Tmol H₂ per yr (C70).

## 3. Vocabulary that the files use

| Term | Meaning |
|---|---|
| A, M | Acetogens and methanogens, the two hydrogen guilds |
| T\* | Switch temperature where the two guilds' hydrogen requirements cross; the exact set point |
| f | Acetate fate: fraction of acetate that becomes methane (recycled). 1 − f leaves for good |
| J, Φ, P | Hydrogen input per litre (J), as a methane-equivalent flux (Φ), and as the dimensionless supply potential P = c t_CH₄ Φ (0.30 at the reference) |
| r | Column ratio of methane to carbon dioxide |
| τ | Climate (thermal) response time of equation (2.7) |
| τ_c | Critical response time: the first τ at which a steady state loses local stability (first-loss margin) |
| S, S_c | Local sensitivity dT\*/d ln Φ, K per e-fold of supply; S = 0 is exact control |
| Q | Coexistence supply ratio (upper/lower edge of the window) |
| exact / graded | S = 0 (integral-like pinning) / S ≠ 0 (residual drift with supply) |
| D1, D2 | Dial branches: D1 acetate feedback strength κ at f = 0 or 0.5; D2 habitat spread at exchange d = 10⁻⁴ or 10⁻³ yr⁻¹ |
| σ, d | Habitat temperature half-width; cell exchange rate between habitats |
| fixed / product feedback | Products held fixed / acetate and methane feed back on their producers |
| census | Finite-population rule: a guild below one cell is removed at the next ten-year census |
| F | Imposed warming: rigid vertical shift of the climate curve, a surrogate for sunlight |
| s | Methane response-speed multiplier at fixed equilibria (C65); not a physical lifetime |
| case A–D | The four Arney et al. (2016) haze-climate responses; results use case B unless stated |
| PB*, PC*, PD* | Pre-registered predictions of stages B, C and D (ESM S6) |

## 4. Provenance map

| Result | Inputs | Code | Output | Claims |
|---|---|---|---|---|
| Figure 1 (mechanism, requirement curves, plateau) | `models/haze_response/arney2016/`, model parameters | `src/terra_prisca/haze_world/paper_figures/fig1.py` | `models/haze_world/paper/figures/fig1.*`, `figures/data/fig1*.csv` | C05, C06 |
| Figure 2 (swings, crashes, eigenvalues) | committed trajectory exports | `paper_figures/fig2.py` (`--refresh` reruns) | `figures/fig2.*`, `figures/data/fig2*.csv` | C20, C51, C52 |
| Figure 3 (precision–durability plane) | `models/haze_world/figures/graded_dials/`, `review/issue1_spread_response.*` | `paper_figures/fig3.py` | `figures/fig3.*`, `figures/data/fig3*.csv` | C54, C57, C60, C61 |
| Figure 4 (assembly) | census archives and refuge records (manifests in `figures/dynamic_realisation/transient_archive_manifest.json`, `figures/buffered_refuges/raw_manifest.json`) | `paper_figures/fig4.py` (`--refresh` needs raw payloads) | `figures/fig4.*`, `figures/data/fig4*.csv` | C09, C52, C65 |
| Imposed warming (§3.5) | model | `models/haze_world/review/issue2_forcing.py` | `review/issue2_forcing.json`, `issue2_forcing_window.csv` | C62–C64 |
| Acetate fate (§3.7) | model | `review/issue4_acetate_fate.py` | `review/issue4_acetate_fate.json`; ESM S8 tables | C67, C68 |
| Supply scale (§3.7) | `review/issue4_acetate_fate.json` | `review/issue5_supply_scale.py` | `review/issue5_supply_scale.json` | C69, C70 |
| ESM tables, Table S1 | ledger, committed outputs | `paper_figures/esm_tables.py`, `table_s1.py` | marked blocks in `esm/esm.md`, `esm/*.csv` | all S-table rows |
| Graphical abstract | `figures/data/` | `paper_figures/graphical_abstract.py` | `products/figures/graphical_abstract.*` | C06, C52, C54, C57, C09 |

Selection rules that most misquotations drop: the headline margins are the **reference** states
(P = 0.30, fixed products, case B, ℓ = 0.001 h⁻¹) at f = 0 and 0.5; the f sweep exports lost biomass;
the 36-state inventory is the original grid (f = 0, 0.5, 0.9; three loss rates; three supplies); the
30-yr price is interpolated inside refined brackets (`threshold_refinement/thresholds.json`), and the
paper quotes bracket midpoints.

## 5. Traps: superseded results and known misreadings

1. **"The regulator fails at 0.15 yr."** It loses *local stability*. At a 1-yr lag the f = 0 reference
   keeps both groups for 30,000 yr with 1.3 K late swings (C51). Governs: C63, C51, E22.
2. **"Near-complete recycling gives the reference state decades of margin."** The 21–31-yr margins
   belong to lower supplies (P = 0.229–0.240) with biomass exported; the reference mixture vanishes
   above f ≈ 0.78 (C67, C68, E20).
3. **"More recycling leaves less sink."** The combined acetate-plus-biomass export at fixed supply is
   independent of f; the window narrows because the two routes' methane yields converge (C68).
4. **"Exclusion always takes decades."** Only with fixed products. Three product-feedback invasions took
   260–290 yr (C52). C65 covers only four fixed-product, zero-lag runs (E19).
5. **"A uniform habitat can never assemble the mixture."** A thousandfold faster methane response at
   fixed equilibria assembled it from acetogen invasions (C65); that speed-up is not a physical lifetime.
6. **"Refuge-assembled mixtures are durable."** Their margin against slow climate was not computed (E19).
7. **Real-planet placement on Figure 3.** The seafloor contrast is observed today; the equator-to-pole
   gradient is modelled for the Archean. Neither measures active hydrogen-fed habitat spread (E17).
8. **"Loose against supply, tight against sunlight."** Both are attenuated by the same closed-loop
   factor; the difference was units (C62, E18).
9. **Stability at the imposed-warming window's ends.** Unestablished: each warming-side one-sided
   linearisation has a growing mode (E18).
10. **The two 42s.** §3.2's 42 exact states (36 stable + 6 bridge) and §3.4's 42 uniform graded states
    with product feedback are different sets.
11. **0.31 versus 0.32.** The D1 f = 0.5 bracket is 0.3142–0.3155; text and Figure 3 quote the midpoint
    (0.31). Older step documents quote the bracket end (0.32); they are superseded.
12. **C38 is provisional on purpose.** C46 tests a restated prediction with a different denominator and
    C49 a separate interval; neither settles PB1 as first posed (ESM S6).
13. **The weak-mode formula as an explanation of τ_c.** It works at the f = 0 reference and on the
    original grid but fails at two refinement points (C58). Use it for the reference only.
14. **The power-law trade-off.** Refuted as a universal form (C56); the paper reports prices branch by
    branch.
15. **P is not the realised methane ratio.** It is the ratio the supplied hydrogen alone could sustain if
    fully converted to methane.
16. **Fermentation or oxygenic photosynthesis is "required".** Neither: gross delivery can include
    recycled hydrogen, and published anoxygenic ecosystems reach comparable methane fluxes (E21).
17. **Old abstracts and step documents** (`01a`, `01b`, `02`, `03a`, `03b`) are dated stages of the
    writing process, not current wording. The current text is `03c-full-draft.md`.

## 6. Checks before and after any change

```sh
uv run pytest -q                                   # whole suite (~4 min; 1,035 tests on 25 Nov 2026)
uv run pytest -q tests/test_paper_esm.py tests/test_paper_table_s1.py tests/test_paper_transient_figures.py
make -C models/haze_world/paper/products check     # claims ledger against all four products, makedoc lint
make -C models/haze_world/paper/products           # brief PDF, then the two-page check
uv run python -m terra_prisca.haze_world.paper_figures            # Figures 1–4 and the ESM tables
uv run python -c "from terra_prisca.haze_world.paper_figures import table_s1; table_s1.main()"
uv run tools/refs.py build models/haze_world/paper/products/references
```

Invariants worth asserting when touching the model or figure code (the figure modules already assert
most of them against the ledger): T\* = [281.53]{.C06} K at the reference; the f = 0 reference margin
[0.149]{.C63} yr; 36 finite exact margins with maximum [7.08]{.C54} yr; four refined 30-yr brackets
(C57); 24 single-guild invasion endpoints (C52).

## 7. Open edges

- **The acetate fate f on the early Earth.** Unknown. Measuring acetate turnover and the oxidised share
  in modern mats would move it (§4.8). Oxidant budgets were compared, not modelled (C68).
- **Habitat spread among active hydrogen-fed habitats.** Unknown; wider and asymmetric spreads are an
  unrun sensitivity stage (E17).
- **Solar forcing.** Imposed warming is a rigid shift of one case-B curve; a matched solar sweep of a
  haze climate is the test (§4.8).
- **The refuge-assembled mixture's margin against slow climate.** Not computed.
- **Temperature-dependent productivity.** The guilds coexist at the switch if supply there falls in the
  window; its effect on stability and assembly is untested (§4.7).
- **Submission build.** The article is still in `03c-full-draft.md`; Word export drops the equation
  numbers of (3.1) and (3.2). Moving the article into makedoc `main` and `supplement` profiles here is the
  next step. Length is close to Interface's 8,000-word ceiling if displays count.

## 8. Conduct in this repository

- Read `AGENTS.md`. Facts and citations come from sources read in the task; every DOI is checked against
  Crossref. The brief's bibliography is built from `products/references/dois.txt`.
- To add or change a claim: edit `models/haze_world/synthesis/claims.csv`, reverify the evidence, run
  `python3 tools/claims.py stamp models/haze_world/synthesis/claims.csv ID`, then make every product pass
  the check.
- Change `estimands.md` before changing how a result is described.
- A faithful reconstruction stays faithful; departures go in named variants (AGENTS.md).
- Do not edit generated artefacts by hand: marked table blocks and CSVs in `esm/`,
  `paper/figures/`, `products/figures/`, `products/references/refs.yaml`, `products/build/`.
- Coordination happens on the correspondence board (project `terra-prisca`); accepted decisions are
  recorded in the repository. Barry W. Brook decides release and submission.
