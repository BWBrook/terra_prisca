# Consolidation pass: proposed abstract and moves

Claude (Opus 5.5), 23 November 2026, for Barry's decision before the rest is applied. No new analysis or claims.

## Limits

- **Abstract: 200 words at most**, with no references or unexplained abbreviations. Source: the Royal Society's [author guidelines](https://royalsociety.org/journals/authors/author-guidelines/), which cover every Royal Society journal and were read live on 23 November.
- **Article length: unresolved.**
  - The general guidelines defer length to each journal's author-information page. Interface's [for-authors page](https://royalsocietypublishing.org/rsif/pages/for-authors) is behind a bot check.
  - The only Interface page that loaded, [Information for reviewers](https://royalsocietypublishing.org/rsif/pages/for-reviewers), says "The strict length requirements are 2500 words (5000 words for review articles only)". That count includes the cover page, references, end sections and figure legends.
  - Published Interface research articles are far longer, for example Blanco 2026 at about 4,400 main-text words (see `models/haze_world/synthesis/jrsi-format-notes.md`), so the 2,500 figure needs checking on the author page.
- **Current draft:**
  - main text (Introduction to §4.7): about 5,150 words;
  - abstract: 307;
  - table 1: about 510;
  - figure captions: about 780;
  - end statements: about 180.

## Proposed abstract (195 words)

Can life regulate its planet's climate when that climate responds slowly? We test this in a model inspired by the hazy early Earth. Two microbial groups compete for hydrogen: methanogens make methane, which forms a cooling organic haze, and acetogens divert hydrogen into acetate. Temperature decides which group wins, so their competition can hold temperature exactly constant as hydrogen supply changes. This needs some diverted hydrogen to stay out of methane for good, through oxidation, export or burial. Exact control is fragile: the reference state fails once the climate takes over 0.15 years to respond, or about one year if half the acetate becomes methane. Near-complete recycling stretches this to decades over a much narrower supply range. Imperfect control lasts far longer: when acetate slows its own producers or habitats differ in temperature, a sensitivity of a fraction of a kelvin per e-fold of supply tolerates a 30-year climate response, and 1–2 K tolerates centuries. In one uniform habitat, the group favoured at the starting temperature removes the other within decades, long before the climate can reverse its advantage. The mixture forms only where the losing group can persist, in a refuge or through immigration.

Leaves the abstract, kept in the body:

| Item | Kept in |
|---|---|
| "in the original sampled inventory" and the seven-year bound | §3.2 |
| Recycling trade, numerically (factor 2 to 5%; 21–31 years at f = 1) | §4.4 |
| Branch-by-branch prices 0.07–0.32 K | §3.4 |
| Habitat half-widths 0.02–0.06 K | §3.4 |
| Imposed-warming result (−15 to +8 K; 0.1–8%) | §3.5 |

## Moves in the body

**§4.4 is split.** It currently has seven topics:
1. sink;
2. oxidant budget;
3. interception;
4. recycling trade;
5. fermentation;
6. habitat contrasts and mat tests;
7. sunlight.

The proposed structure gives one point per paragraph:

- **§4.4 The sink condition**, in three paragraphs:
  - The regulator needs a lasting non-methane fate, and the known routes return acetate to methane. The oxidant budget (20 Tmol acetate needs 20 sulfate or 160 Fe(III) a year) is compared with published estimates. An oxidant sink must intercept acetate before it becomes methane.
  - More recycling trades range for tolerance: the window narrows from 2.0 to 1.05 while the exact margin grows from about 1 to 21–31 years. This moves here from §4.6, where it now stands as a condition.
  - Hydrogen supply: the geological comparison moves here from §2.2, followed by fermentation (600 Tmol C; the 149–189 window; 64%; 50 Tmol acetate) and the anoxygenic-flux comparison.
- **§4.5 Graded control on the early Earth:** habitat temperature contrasts against the 0.02–0.06 K that bought 30 years, and the rough solar scale.
- **The tests section** (now §4.8) gains the mat measurements, so all proposed tests sit together.
- The old §4.5–4.7 become §4.6–4.8.

**Cuts for repetition:**

- §2.2 keeps the 401 Tmol scale and its split. The geological comparison moves to §4.4.
- §4.4's "If biomass returns as methane too, the exact plateau disappears" goes. §2.2 and table 1 already say it.
- §3.2 drops "The 10,000-year methane lifetime sets the removal rate of the atmospheric stock" (§2.3 says it). The stranded "Recycling also narrows the difference in methane yield" moves next to the f = 0 to 0.5 margin it explains.
- §4.1 and §4.2 drop the restated numbers; they keep the interpretation and point to §3.2–3.4.

**Scope conditions that move to §4.6 (Conditions), stated once:**

| Now in | Condition |
|---|---|
| §2.2 | Gross delivery could include recycled hydrogen; merged with "Supply is prescribed" |
| §3.5 | Stability is sampled inside the warming window, not claimed at its ends |
| §3.6 | The faster-methane test is not a shorter physical lifetime |
| §3.6 | Climate-tracking habitats gave no paired test at f = 0 and 0.5; f = 0.9 is not regulation |
| §4.4 | The oxidant budgets do not cap gross cycling, and oxidant regeneration must enter the methane budget |
| §4.4 | The two-guild calculation assumes reducers take little hydrogen |
| §4.4 | Habitat contrasts set only an illustrative scale; the residual also depends on how supply is shared, exchange and acetate chemistry |
| §4.4 | The solar pair changes spectrum and haze together; a matched solar sweep is the test, which also goes in §4.8 |
| §4.5 | The refuge-assembled mixture's margin against slow climate was not computed |

§4.6 is rewritten as grouped paragraphs: physiology and switch, chemistry and sink, supply, climate, and assembly rules. It is no longer one run-on list.

**Contradictions to fix:**

- §4.1 says every exact state that starts stable fails at a response time of 7 years or less. That predates Issue 4, whose f = 1 exact states hold for 21–31 years (C67). Restate it for the sampled grid (f up to 0.9) and name the f = 1 exception. §3.2's count of 42 states names its grid and stays as it is.
- The old abstract's "original sampled inventory" and the new "we found" both depend on that same grid. The new abstract anchors on the reference state instead.

**Optional, older than the issues:** the §3.1 figure of 4.7 K under the alternative cold continuation could also move to §4.6. It is left in place unless you want it moved.

**Expected size:** main text about 4,800 words; §4.4 and the new §4.5 together about 600 instead of 712.

## Applied (23 November)

Barry: "Apply all." He also pasted the Interface length rule: research articles run over 2,500 words and no more than 8,000, "this includes cover page, references and acknowledgements". The rule is recorded in `models/haze_world/synthesis/jrsi-format-notes.md`.

**Applied as proposed:**
- the abstract (196 words);
- §2.2;
- §3.2, §3.6, §4.1 and §4.2;
- §4.4 split into §4.4 (sink condition) and §4.5 (graded control on the early Earth);
- the old §4.5–4.7 renumbered to §4.6–4.8;
- §4.7 Conditions regrouped under physiology and habitats, sink and supply, climate, and assembly;
- the mat tests and the matched solar sweep moved to §4.8.

**Departures from the plan:**
- §4.2 keeps the 30-year figure and drops only "1–2 K buys centuries".
- §4.7 no longer repeats conditions that table 1 already gives: the loss-rate shifts of T\*, dry-mass normalisation, continuation to 273 K, the one-cell reading, the sink requirement and the methane lifetime. It points to table 1 instead.
- "The headline results use f = 0 and 0.5" was dropped, since §2.2 says it.
- §4.1 no longer claims a bound "with up to 90% of acetate recycled": exact margins at f = 0.9 reach 6.6–9.7 years (S8c). It now refers to the 36 states of §3.2 and says that higher recycling lengthens the limit.
- The Introduction's sentence on staged hypotheses and §4.6's "Persistence does not by itself give durable control" were cut in the first pass and then restored, because they were not on the approved list.

**Length:**

| Part | Words |
|---|---|
| Main text | 5,231 (5,151 before) |
| Table 1 | about 520 |
| Captions | about 780 |
| End statements | about 185 |
| References | 39 |

The plan's estimate of 4,800 for the main text was wrong. The moved conditions were relocated, not deleted. Counted as Interface counts (cover, abstract, text, end statements and references at an estimated 25 words each), the paper is about 6,627 words. With table 1 and the captions included as well, it is about 7,927. The reference word count is an estimate.

**Checks:** claims check gives 70 claims, 40 cited, 0 errors. The four paper tests pass.

**Mechanical diff against `1a2f9ae`.** Every number that left a section still appears elsewhere in the draft, except the abstract-only rounded forms −15 and 0.1–8 (§3.5 keeps −15.47 and 0.14% to 8.3%). All 39 references are still cited.

## Combined review applied (23 November)

Claude (Opus 5.5) applied Codex's combined review ([consolidation-codex-review-2026-11-23.md](consolidation-codex-review-2026-11-23.md), which integrates Gemini's message 3711):

- **Abstract (200 words):** uses Codex's wording with "Exact control is fragile" and "Imperfect control lasts far longer" restored as the framing. It names the reference *equilibrium* and its loss of local stability, places the 21–31-year margins at lower supplies with full recycling and biomass export, scopes the 30-year price to four tested branches, and limits "decades" to fixed-product invasions. The last sentence allows the accelerated-methane in-place assemblies.
- **Body:**
  - P is defined after equation (2.6);
  - §3.2 names P_osc and t_d;
  - §3.4 and the Figure 3 caption separate the 42 uniform states from the 80 spread states;
  - (3.1) and (3.2) are display equations;
  - §4.1 and §4.4 use the recycling wording;
  - §4.7 has the habitat-provenance and C63 endpoint wording;
  - the Figure 1 caption says "shifts the competitive advantage".
- **ESM:** S10 capitalisation fixed. S11 names threads 150, 151, 161, 165 and 192, links both Figure 4 raw-data manifests, and credits Gemini's review. The AI-use declaration draft also credits it, with the version left for Barry to confirm.
- **Unchanged:** C38 stays provisional.

**Length:** main text 5,344 words (+113). On Codex's rendered count (7,743 with Table 1 and captions at `066c580`), the stricter total is now about 7,870, about 130 words under 8,000 before the final cover details and declarations. The submission export must keep the `\tag` numbers that Pandoc's DOCX writer drops.

**Follow-up after Codex's acceptance (23 November).**
- The abstract drops "a sensitivity of" and now has 197 words by whitespace count, 199 in Writer.
- C65's claim text now has the narrower scope Codex recommended: four fixed-product, zero-lag reference invasions; tenfold speed keeps all four outcomes; thousandfold speed assembles the mixture from acetogen invasions; lifeless starts. Its basis, ESM S10 and the S11 index now name "the four matching fixed-product, zero-lag C52 runs". Its status stays supported and its evidence is unchanged.
- The reviewer is credited as Gemini 4 Carbon, the name Barry reported to Codex. Board message 3711 records the model only as "Gemini".
