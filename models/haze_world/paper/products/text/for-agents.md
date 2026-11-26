---
document: agent-facing paper
authors: Claude Opus 5.5 (Anthropic) and Codex GPT-6 (OpenAI), joint first; Gemini 4 Carbon (Google); Claude Fable 5.2 (Anthropic); Barry W. Brook (University of Tasmania)
study: haze-world regulator — microbial competition for hydrogen as a climate thermostat on a hazy early Earth
status: internal draft, consolidated after five pressure tests; not yet submitted or released
human_paper: models/haze_world/paper/products/text/main.md and figures.md (+ ../esm/esm.md, brief.md); built by `make -C models/haze_world/paper/products`
claims_ledger: models/haze_world/synthesis/claims.csv (single source for all products; checked by tools/claims.py)
interpretation: models/haze_world/synthesis/estimands.md (what each analysis bounds; allowed and forbidden phrasings)
governing_docs: [AGENTS.md, docs/vision.md, models/haze_world/synthesis/jrsi-format-notes.md, docs/audits/consolidation-plan-2026-11-23.md]
authority: Barry W. Brook decides public release, submission and any correspondence outside the collaboration
updated: 26 November 2026
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
2. `models/haze_world/paper/products/text/main.md` (with `figures.md`) for the argument; `models/haze_world/paper/esm/esm.md`
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
  (C67), so the 7.08-yr maximum belongs to the original grid only (E22). Past the limit a 1-yr lag
  keeps both groups for 30,000 yr while oscillating (C51); in the 10- and 100-yr disturbance runs at
  least one continuous population fell below one cell (§3.3;
  `models/haze_world/figures/dynamic_realisation/oscillations.csv`, separate from the C52 invasion
  censuses).
- **What does durability cost?** On four dial branches a 30-yr margin costs a local sensitivity of
  0.07–0.31 K per e-fold of supply at the bracket midpoints; the bracket edges span
  [0.070]{.C57}–[0.316]{.C57} (C57). S is a local derivative, not the drift after multiplying supply
  by e (E22). The original 122 graded states have
  margins of at least [331]{.C54} yr (C54). Weakly connected spread communities follow the no-fit
  relation of equation (3.1) (C60); spreads of 1 and 3 K move temperature by [1.91]{.C61} and
  [5.41]{.C61} K over the uniform coexistence range with margins of centuries (C61).
- **Does it hold against imposed warming?** Supply and imposed warming share one closed-loop factor;
  graded states follow by |S|/(kE) (C62). Fixed-product exact states hold T\* for F from
  [−15.47]{.C63} to [8.14]{.C63} K (C63). Cases A and C also give exact states; case D does not on its extracted curve, although its assumed
  low-methane extension admits a state near P = 0.0233 (C64, E18).
- **Does the mixture assemble?** Not in a closed, uniform habitat: all [24]{.C52} reference invasions
  end with the invader alone (C52). In the four fixed-product, zero-lag runs the resident goes within
  decades while temperature takes millennia to cross T\* (C65). Two buffered refuges restore matching
  mixtures in the 12 key runs (C09); any tested positive immigration gives two materially active groups
  near T\* at f = 0 and 0.5, but no material mixture at f = 0.9 (C66). In two product-feedback
  invasions the resident briefly grew faster before it was removed (E19).
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
| S, S_c | Local sensitivity dT_eq/d ln Φ of the *equilibrium* temperature, K per e-fold of supply; S = 0 is exact control. The physiological switch T\* in the numerator would make S vanish by definition |
| Q | Coexistence supply ratio (upper/lower edge of the window) |
| exact / graded | S = 0 (integral-like pinning) / S ≠ 0 (residual drift with supply) |
| D1, D2 | Dial branches: D1 acetate feedback strength κ at f = 0 or 0.5; D2 habitat spread at exchange d = 10⁻⁴ or 10⁻³ yr⁻¹ |
| σ, d | Habitat temperature half-width; cell exchange rate between habitats |
| fixed / product feedback | Fixed *effects* of the products on the physiological hydrogen thresholds (methane and acetate stocks still evolve) / acetate and methane feed back on their producers' thresholds |
| census | Finite-population rule: populations are continuous; every ten years a guild whose biomass represents less than one cell is removed |
| F | Imposed warming: rigid vertical shift of the climate curve, a surrogate for sunlight |
| s | Methane response-speed multiplier at fixed equilibria (C65); not a physical lifetime |
| case A–D | The four Arney et al. (2016) haze-climate responses; results use case B unless stated |
| PB*, PC*, PD* | Pre-registered predictions of stages B, C and D (ESM S6) |

## 4. Provenance map

| Result | Inputs | Code | Output | Claims |
|---|---|---|---|---|
| Figure 1 (mechanism, requirement curves, plateau) | `models/haze_response/arney2016/`, model parameters | `src/terra_prisca/haze_world/paper_figures/fig1.py` | `models/haze_world/paper/figures/fig1.*`, `figures/data/fig1*.csv` | C05, C06 |
| Figure 2 (swings, crashes, eigenvalues) | committed trajectory exports | `paper_figures/fig2.py` (`--refresh` reruns) | `figures/fig2.*`, `figures/data/fig2*.csv` | C20, C51, C52 |
| Figure 3 (precision–durability plane) | `models/haze_world/figures/continuum_habitats/c0_local_gain.csv` (original states), `c1_resolved.csv` (resolved habitats), `models/haze_world/figures/graded_dials/`, `review/issue1_spread_response.*` | `paper_figures/fig3.py` | `figures/fig3.*`, `figures/data/fig3*.csv` | C54, C57, C60, C61 |
| Figure 4 (assembly) | census archives and refuge records (manifests in `figures/dynamic_realisation/transient_archive_manifest.json`, `figures/buffered_refuges/raw_manifest.json`) | `paper_figures/fig4.py` (`--refresh` needs raw payloads) | `figures/fig4.*`, `figures/data/fig4*.csv` | C09, C52, C65 |
| Imposed warming (§3.5) | model | `models/haze_world/review/issue2_forcing.py` | `review/issue2_forcing.json`, `issue2_forcing_window.csv` | C62–C64 |
| Acetate fate (§3.7) | model | `review/issue4_acetate_fate.py` | `review/issue4_acetate_fate.json`; ESM S8 tables | C67, C68 |
| Supply scale (§3.7) | `review/issue4_acetate_fate.json` | `review/issue5_supply_scale.py` | `review/issue5_supply_scale.json` | C69, C70 |
| ESM tables, Table S1 | ledger, committed outputs | `paper_figures/esm_tables.py`, `table_s1.py` | marked blocks in `esm/esm.md`, `esm/*.csv` | all S-table rows |
| Graphical abstract | `figures/data/` | `paper_figures/graphical_abstract.py` | `products/figures/graphical_abstract.*` (also reads `models/haze_response/arney2016/figure4.csv`, `review/issue4_acetate_fate.json`) | C06, C09, C54, C57, C66, C67 |

Selection rules that most misquotations drop: the headline margins are the **reference** states
(P = 0.30, fixed products, case B, ℓ = 0.001 h⁻¹) at f = 0 and 0.5; the f sweep exports lost biomass;
the 36-state inventory is the original grid (f = 0, 0.5, 0.9; three loss rates; three supplies); the
30-yr price is interpolated inside refined brackets (`threshold_refinement/thresholds.json`), and the
paper quotes bracket midpoints (0.07–0.31); 0.070–0.316 are the outer bracket edges. The original graded
rows plotted require a negative frozen-composition response, which excludes six already-unstable cases;
the 113 markers at the 10,000-yr search ceiling are lower bounds on tolerated lag.

## 5. Traps: superseded results and known misreadings

1. **"The regulator fails at 0.15 yr."** It loses *local stability*. At a 1-yr lag the f = 0 reference
   keeps both groups for 30,000 yr with 1.3 K late swings (C51). Governs: C63, C51, E22.
2. **"Near-complete recycling gives the reference state decades of margin."** The 21–31-yr margins
   belong to lower supplies (P = 0.229–0.240) with biomass exported; the reference mixture vanishes
   above f ≈ 0.78 (C67, C68, E20).
3. **"More recycling leaves less sink."** The combined acetate-plus-biomass export at fixed supply is
   independent of f; the window narrows because the two routes' methane yields converge (C68).
4. **"Exclusion always takes decades."** Only with fixed products. Three product-feedback invasions took
   260–290 yr (C52). C65's removal-versus-crossing comparison covers only four fixed-product, zero-lag
   runs; C65 also covers the methane-speed variants and the lifeless starts (E19).
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
17. **"Every exact state loses stability within about 7 years."** The 7.08-yr maximum is for the 36
    initially stable exact states of the original grid (C54). At f = 1 with biomass exported an exact
    state at lower supply tolerates 30 yr inside a window about 5% wide (C67, E22).
18. **"The favoured group always grows faster until it wins."** The invader ended alone in all 24 runs
    (C52), but in two product-feedback methanogen invasions the resident acetogens briefly grew faster
    (within years 22–30) before removal. Distinguish the eventual winner from the growth advantage along the
    path (E19; `docs/audits/haze-world-invasion-wording-2026-11-25.py`).
19. **"Fermentation enlarges the sink."** C70 is a conditional glucose budget: all hydrogen from
    fermentation, half of every source's acetate becoming methane outside the shared pool. Its window
    ends are pure-guild limits; it says nothing about stability or assembly (E21).
20. **Old abstracts and step documents** (`01a`, `01b`, `02`, `03a`, `03b`, and `03c-full-draft.md` in
    history) are dated stages of the writing process. The article moved to `products/text/main.md` on
    25 November 2026 and is built by makedoc with numbered citations.

## 6. Checks before and after any change

```sh
uv run pytest -q                                   # whole suite (~4 min; 1,035 tests on 25 Nov 2026)
uv run pytest -q tests/test_paper_esm.py tests/test_paper_table_s1.py tests/test_paper_transient_figures.py
make -C models/haze_world/paper/products check     # claims ledger against all four products, makedoc lint
make -C models/haze_world/paper/products           # article, supplement and brief PDFs; brief two-page check
                                                   # the supplement's links pin to HEAD: commit sources first
uv run python -m terra_prisca.haze_world.paper_figures            # Figures 1–4 and the ESM tables
uv run python -m terra_prisca.haze_world.paper_figures.graphical_abstract   # the brief's figure
uv run python -c "from terra_prisca.haze_world.paper_figures import table_s1; table_s1.main()"
uv run tools/refs.py build models/haze_world/paper/products/references
```

A Git-only clone passes the four paper tests and regenerates Figures 3 and 4 and the graphical abstract.
Figure 2's `--refresh` reintegrates; Figure 4's `--refresh` needs the 24 native census files and four
native refuge records named in the manifests (archive status: `docs/reproducibility/haze-world-core.md`;
ESM S11). When updating a claim, commit its evidence before stamping it: a stale evidence stamp is only a
warning. The figure builders verify exports and selected assertions against the ledger; whether the
words match the ledger needs a semantic review against `estimands.md`.

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
- **Submission build.** makedoc builds `build/article.pdf` and `build/supplement.pdf`; the PDFs carry all
  13 equation numbers, but the Word export drops them. Length is governed by Interface's own count
  (Barry, 25 November 2026); recount when the cover and declarations are final.

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
