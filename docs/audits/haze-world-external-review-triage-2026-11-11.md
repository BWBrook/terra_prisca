# Haze-world external reviews: combined triage

Claude (Opus 5.5), 11 November 2026. This file triages the two independent
reviews of tag `haze-world-review-1`:

- [Fable 5.2](../reviews/haze-world-2026-11/fable_5-2/review-claude-fable-5-2.md),
  with its [checks](../reviews/haze-world-2026-11/fable_5-2/checks/);
- [GPT-6 Pro](../reviews/haze-world-2026-11/gpt6_pro/package/haze_world_independent_review_2026-11-11.md).

The table merges findings both reviewers raised. A source written `F-R1`
means Fable's finding R1; `G-R4` means GPT-6 Pro's R4. Every disposition
here is **proposed**. Codex checks each finding's factual basis by its own
route before any becomes final. Neither of us accepts a finding unchecked or
dismisses one without a test.

## The short version

The two reviewers worked independently and agree on the main point. The
reference thermostat is stable only because temperature follows methane
instantly.

- **Agreement on the lag.** Both added a first-order thermal lag, and both
  found the mixed state goes unstable at the same critical lags: 0.149 yr
  at `f = 0` and 1.10 yr at `f = 0.5`.
- **Agreement with a closed form.** Both values match
  `τ_crit ≈ P²/(2π² t_damp)` applied to C20. I recomputed this:
  119.57²/(2π² × 4854) = 0.1492 yr.
- **The physical comparison.** A surface mixed layer responds over years,
  so the stable regime is not the physical one.

Each reviewer also found a way out, and the two point in different
directions:

- **Product-dependent chemistry (GPT-6 Pro).** It stays stable at every lag
  tested, from 10⁻⁵ to 10⁴ yr. It keeps about 86% supply buffering but loses
  exact temperature pinning.
- **Habitat temperature spread (Fable).** A spread of ±3–6 K removes both the
  lag instability and the invasion bottleneck. It also turns the set point
  into graded, proportional control: temperature slides 5–10 K across the
  supply band. That removes much of the case for "memory".

Together these change what the paper can claim. Readiness to write is
**withdrawn** until the revision stages below are complete.

Both reviewers recommend a single paper, organised around which conditions
a competitive regulator needs and what a real planet does to it. That
replaces our current memory thesis.

## Findings

| X | Finding | Source | Basis | My first check | Proposed disposition | Owner |
|---|---|---|---|---|---|---|
| X1 | Thermal lag above 0.149 yr (`f = 0`) or 1.10 yr (`f = 0.5`) destabilises the fixed-product reference. At a 3-yr lag, a 0.1% kick drives acetogens below 10⁻²⁵ cells. | F-R1, G-R1 | verified by both; independent implementations | Closed form reproduces 0.1492 yr | **Accept, critical.** C06, C20 and C34 hold only with instantaneous temperature. Stage B. | Claude spec; Codex build |
| X2 | Product-dependent chemistry is stable at all 16 lags tested, with about 86% supply attenuation and loss of exact pinning | G-R1 | verified | — | **Accept as a lead.** Stage B tests it across supply and turnover. | Stage B |
| X3 | A ±3–6 K habitat spread removes the lag instability and the invasion bottleneck, and converts integral control to proportional control | F-R2 | verified (nine boxes, one solver) | — | **Accept as a lead, likely thesis-changing.** Stage B runs it with qualified solvers. | Stage B |
| X4 | The restoring crossing lies on the cooling branch in only 31% of the MSB grid. The dimensionally matched capacity ratio (0.38, per dry mass) puts it off the branch, at 297.08 K. Unequal guild losses move it 278–294 K. | F-R3, G-R3 | verified by both | The 0.379 vs 0.737 choice is documented in `two-guilds.md` but never foregrounded. Equal dry mass conflicted with the source's crossovers (`hydrogen-uptake.md`). | **Accept, major.** Existence of the crossing becomes a stated condition, with a robustness map. The capacity normalisation is the single most consequential transfer. Stage C. | Codex |
| X5 | "Turnover sets the set point" is wrong as stated. The set point is an R* crossing fixed by joint physiology, the classic chemostat crossing between an affinity specialist and a rate specialist. Turnover is one axis. | F-R6, G-R3 | verified decomposition; reasoned framing | Agree | **Accept.** Reword E1, C12 and the synthesis, and cite chemostat theory. | Claude |
| X6 | Understated strengths. The set point is identical on Arney cases A and C (R* equality does not depend on the climate curve, which only decides whether it lies on a cooling branch). MSP gives a stable mixture at 290.285 K. Assay uncertainty is ±1.4 K. | F-R12, F-R10 | verified | Agree with the reason given | **Accept.** Report in Stage C. | Codex |
| X7 | The thermostat regulates against supply only over a factor of about 1/f, and the repository's own evidence points to f near 1 | F-R4 | verified (`fband.py`) | Closed form: at fixed T*, methane must lie between fΦ and Φ, so the supply band is exactly 1/f (ignoring assimilation) | **Accept, major.** Regulation needs a non-methane acetate fate. This becomes a condition in the thesis, with candidate sinks named and the band reported against f. | Claude framing; Codex band |
| X8 | The hydrogen budget is open: the atmosphere is held at zero H₂, photolysis returns nothing, and the reference supply implies a fermentative source | F-R5 | reasoned; flux verified | `Competition.atmosphere_pa` already exists | **Accept.** A cheap sensitivity on atmospheric H₂ pressure (Stage C), plus a discussion engaging Kharecha 2005, Ozaki 2018 and Sauterey 2020. | Codex; Claude |
| X9 | Close precedents go uncited: Seto & Akagi 2007 (one-resource competition that regulates its environment); integral rein control; Daisyworld oscillation driven by thermal inertia; chemostat theory; Sauterey 2020 as the main ecosystem comparator | G-R5, F-R7, F-R6 | reasoned; DOIs verified by both | — | **Accept.** An equation-level comparison with Seto & Akagi, and a reframe around integral control. Stage D. | Claude |
| X10 | Different evolutionary constraint strengths (`E_A = 0.65`, `E_M = 0.10` eV) reverse the feedback and give unstable communities on the extracted branch | G-R2 | verified, independent optimiser | — | **Accept, major for the evolution claim.** An `E_A × E_M` map; restrict C30 and C34 explicitly to common E. Stage C. | Codex |
| X11 | Our wording "survives insofar as its temperature dependence lies outside the evolving trait" is close to a tautology. A like-for-like test would trade cold capacity against warm capacity. | F-R8 | reasoned | Agree | **Accept.** Shorten evolution to a section. The trade-off test is optional, depending on X10. | Claude |
| X12 | False domain exits: an unvalidated polynomial root is accepted. Three tests fail in the reviewer's environment. | G-R4, G-R7 | verified | **The same three tests pass here** (macOS arm64, NumPy 2.5.4, SciPy 1.18.1): the failure depends on platform round-off. The defect, an unchecked residual, is real. | **Accept, major.** Fix the root validation and the finiteness guard. Requalify domain-censored cases and dense minima, starting with any archive produced on Linux. Stage A. | Codex |
| X13 | The 230-cell threshold is not identified by net growth: balanced extra birth and death raises it to 2,535 | G-R8 | verified | — | **Accept.** Present 230 as a worked example and add a sensitivity panel. | Codex |
| X14 | The "1% half-life" rule is arithmetic on exponential decay: ln 2 / ln(N₀/N₅₀) | F-R9, G | reasoned | Agree | **Accept.** Plot the dimensionless relation instead. | Claude |
| X15 | Harmful dormancy follows from the growth-triggered cue. Persistent cycles may be the same delay instability as X1, with the dormant bank acting as the lag. | G-R9, F-R13 | reasoned; R13 suspected | R13 is plausible: the bank is a lag | **Accept.** Dormancy moves to the supplement. Stage B tests R13 cheaply. | Codex |
| X16 | Case B's cooling branch is four digitised vertices, so period, damping and τ_crit inherit one segment slope | F-R11 | reasoned | Agree | **Accept.** Stage B sweeps the slope (×0.5, ×2) and the methane lifetime (6–19 kyr). | Codex |
| X17 | The assay's CO₂ (about 12 kPa) differs from case B's (1.8 kPa); threshold multipliers give 279.9 K | G §1.3 | verified | — | **Accept** as a named diagnostic in Stage C. | Codex |
| X18 | Joint stochastic recovery is untested. C09 shows deterministic finite-census recovery. | G-R11 | reasoned | — | **Defer.** Decide after Stage B whether recovery stays a main claim. | — |
| X19 | Reproducibility: ledger auditors stop at absent raw files; reproduce commands rerun tables, not the model; auditors overwrite committed JSON | G-R6, F-R14 | verified | Agree | **Accept.** Deposit the decisive raw subset on Zenodo; give reproduction levels in the ledger; add a `reproduce-core` command. Stage A. | Codex |
| X20 | Documentation problems: stale E11; the brief over-generalises C02; the README reads as a changelog; precision far exceeds the ±1.4 K uncertainty; "reference" means `f = 0.5` in code but `f = 0` for the 120-yr mode; missing spaces in `competitive-evolution.md`; the `competition-switches` MSP window misses 290.285 K | F-R10, F-R14, G-R10 | verified | Agree | **Accept.** Stage A for mechanical fixes; Claude rewrites the README and tags ledger assumptions after Stage B. | Codex; Claude |

Nothing is contested at this stage. The one finding I would challenge
before accepting it is the strength of X3. Nine discrete boxes with one
solver step the temperature by a whole box offset. A continuum spread with
qualified integration could behave differently near the edges. Stage B
settles this.

## Proposed revision stages

**Stage A: repairs and record (Codex; can start now, no design needed).**

- Fix the dense-polynomial root validation and the finiteness guard (X12).
- Requalify affected classifications.
- Make the mechanical documentation fixes (X20).
- Package a reproducible raw subset for Zenodo (X19).

**Stage B: dynamic realisation.** I specify it; Codex builds it.

- **Grid.** The thermal lag `τ_T`, crossed with:
  - chemistry: fixed products or product feedback;
  - habitats: one temperature, or a continuous spread `σ`;
  - `f`: 0, 0.5 and 0.9;
  - the climate segment slope and methane lifetime.
- **Report for each setting:**
  - stability;
  - supply-response gain, separating pinning from buffering;
  - invasion minima in both directions.
- **R13.** Whether the dormancy cycles are a lag instability.
- **Why this stage leads.** It decides what the thermostat is.

**Stage C: robustness maps.** Codex; mostly static and cheap.

- capacity normalisation, unequal losses and yields (X4);
- the MSP reference and cases A–C (X6);
- the regulation band against `f` (X7);
- atmospheric H₂ pressure (X8);
- the `E_A × E_M` map (X10);
- the CO₂ activity diagnostic (X17);
- demographic splitting (X13).

**Stage D: literature and framing** (Claude). Equation-level comparison with
Seto & Akagi 2007, and the integral-control reframe (X9).

Then a revised synthesis, ledger and estimands, followed by a fresh
readiness check. The thesis is rewritten only after Stage B, because B
decides it.

## Decisions for Barry

- **Readiness is withdrawn.** He is told in chat.
- **One paper.** Both reviewers recommend it, and we agree.
- **Scope of Stage B.** It is the main new cost, a few days of work.
  Leaving it out would mean declaring instantaneous, single-temperature
  climate as a limiting assumption. Both reviewers say a referee would
  reject that. We recommend doing it.
