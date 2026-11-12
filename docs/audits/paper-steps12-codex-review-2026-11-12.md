# Haze-world paper: review of Steps 1–2

Codex (GPT-6), 12 November 2026. Reviews `35d59b1`, following the writing
instructions and direct-edit request in correspondence thread 161, post
3311. Changes cover the working abstract, standalone abstract, display plan,
one-page paper and venue notes. No model, evidence table or ledger value was
changed. The earlier drafts remain in Git.

## Decision

Keep the central result and the four-figure plan. The four tuned branches
support a small local sensitivity cost for a much larger thermal-response
margin. Separate that result from community assembly, and describe the
control analogy at the level actually established. The changes are ready
for Claude's review within Barry's stepwise writing process.

## Numerical and semantic checks

Two independent, read-only subagent reviews covered the numbers and the
prediction/display provenance. I checked their key numerical conclusions
again by reading the committed CSVs and threshold JSON directly.

| Draft statement | Check and disposition |
|---|---|
| All 42 exact states fail at lags ≤7 years | C54's `c0_local_gain.csv` and `c1_resolved.csv` contain 36 finite first losses and six states already unstable at zero lag. Maximum finite loss is 7.079524561 years. Revised to distinguish those cases and round to 7.1. |
| Critical lag is the longest stable lag | E16 defines the first detected loss. Later recovery occurs. Corrected the definition and figure axes/captions. |
| 1.3 K swings just past the threshold | `dynamic_realisation/oscillations.csv`, `B2_f0_tau1`: 1.266352774 K late peak-to-peak span over 30,000 years; minimum log10 cell counts 8.038380 and 22.089265. Its reference threshold is 0.149214 years, so “just past” was inappropriate. State the actual one-year run. |
| Both groups die at 10–100-year lags | The uncensored solutions have subcell bottlenecks. Later continuous regrowth after a first loss does not describe a finite community. Retain the first-bottleneck finding without joint-extinction language. |
| 0.07–0.32 K buys 30 years | C57's `graded_dials/threshold_refinement/thresholds.json`: four local-sensitivity brackets, 0.277613–0.278802, 0.314166–0.315511, 0.070169–0.071412 and 0.161899–0.163533 K per e-fold. Retained with the four-branch and local-derivative scope. |
| 1–2 K buys centuries | All 18 C0/C1 rows with 1≤abs(Sc)≤2 have first losses at 331.426 or 581.482 years, or no loss detected through 10,000. Retained as a sampled result. |
| Those states attenuate an unregulated response by 96–98% | Across those 18 rows, 100(1−abs(G_loc)) ranges 95.527655–98.791771%. More importantly, S0 is the frozen-local-mix counterfactual, retaining other feedbacks. Removed this secondary percentage rather than rename it an unregulated ecosystem. |
| Arrival order selects a regulator in 24 invasions | `dynamic_realisation/invasions.csv`: 12 A-into-M runs end acetogen-only; 12 M-into-A end methanogen-only. These are deterministic one-cell/ten-year census outcomes, including settings with a stable established mixture. Corrected to selection of the surviving guild in the specified closed habitat. |
| Atmospheric H2 up to 100 Pa leaves the set point unchanged | C59 and `readiness-h2-2026-11-12.json` support this reference imposed-reservoir result. Retained. |

CSV paths above are under `models/haze_world/figures/`. C54 is descriptive
across its resolved on/off grid. C55/C57 concern the subsequent dials.
These are complementary scopes, rather than evidence for a universal curve.

## Hypotheses and interpretation

| Hypothesis | Actual provenance |
|---|---|
| H1: lag destabilises exact pinning | `dynamic-realisation-spec.md` opens with the reviewers' already-known destabilisation and the 0.149/1.10-year results. The Stage B specification (`98cca12`) interpreted those observations and specified further mechanism tests. H1 was not a prediction made before the finding. |
| H2: graded mechanisms exchange precision for robustness continuously | Stage B specified mechanism comparisons; several precise predictions failed. PD1 in `graded-dial-spec.md` (`e941a92`) genuinely preceded D1/D2, after the C54 on/off gap was known. Retain that staged prospective test. |
| H3: arrival order controls survival | PB6 specified loss in at least one direction per B3 setting. Both-direction loss was the stronger observed outcome. Earlier bottlenecks had already motivated the experiment. The process is rapid displacement during slow climate adjustment; it does not imply that an established mixture lacks stability. |

The working abstract now calls H1–H3 organising hypotheses developed during
the investigation. The ESM plan preserves original predictions, failed gain
thresholds, the failed common slope band and weak-mode counterexamples.

For integral action, the exact identity is
`d ln(X_A/X_M)/dt = g_A − g_M`. It integrates fitness difference. Effective
integral action near coexistence is supported; a global temperature-error
integrator or a literal leaky-controller identity needs a further reduction.
The one-page paper now states the identity and the local interpretation.

Residual sensitivity is a model result and a candidate quantity for future
comparisons. It is neither established as necessary for every durable
biological regulator nor a diagnostic biosignature. The new Earth-history /
exoplanet signature sentence was replaced by a proposal to test sensitivity
and response time together in other microbial systems.

## Display plan

Keep four figures and one table, with these corrections:

- Fig. 1 shows recycling and retained material explicitly, the climate's
  cooling branch, and the capacity-transfer condition. Single-guild curves
  retain their actual flat portions.
- Fig. 2 uses existing B2 trajectories. The proposed 0.1-year kick and graded
  100-year settling trajectories do not exist in that tranche. Replace them
  with a planned spectral export showing local stability. End physical
  interpretation at the first subcell crossing.
- Fig. 3 separates exact-zero states from positive log-axis values, marks
  censored margins as lower bounds, and joins only the same branch. Its
  illustrative supply slopes are labelled tangents, rather than uncomputed
  finite forcing responses.
- Fig. 4 reports single-guild census endpoints, rather than different
  durable regulators. Table 1 foregrounds transfer assumptions, turnover,
  recycling/assimilation and the continuation below measured temperatures.
  Figure construction must read the separate census archives, rather than
  the existing uncensored trajectory CSVs; the f=0, τ=10 B2 trace also needs
  an export from its existing archive. No new simulation is required.

The revised abstract has 141 whitespace-delimited words; the one-page body
is about 620. Scope conditions remain together rather than interrupting each
result. The prose pass followed the audit-ai-writing guidance on replacing
unsupported generality with the concrete result.

## Venue and verification

Retain JRSI Research Article, preprint first. Its
[physical/life-science scope](https://royalsociety.org/journals/) fits the
paper. The [general author instructions](https://www.royalsociety.org/journals/authors/author-guidelines/)
confirm a standalone abstract of at most 200 words without references.
The journal-specific page remained inaccessible, so its word limit remains
unverified in the format notes.

The [current AI policy](https://royalsociety.org/journals/ethics-policies/artificial-intelligence/)
also restricts replacing scientific insight, analysis and interpretation;
the earlier notes incorrectly treated analysis as unrestricted. Corrected
the notes and recorded Barry's existing instruction to draft with full
disclosure. This review makes no editorial enquiry or submission.

Verification command:

```sh
uv run python tools/claims.py check models/haze_world/synthesis/claims.csv models/haze_world/paper/01a-working-abstract.md models/haze_world/paper/01b-abstract.md models/haze_world/paper/01c-display-items.md models/haze_world/paper/02-one-page-paper.md
```

The checker verifies ledger evidence/stamps and cited claim identities; the
drafts' plain numerals were checked directly as above. It does not replace
the semantic review. It reported zero errors and 37 warnings for ledger
claims absent from these four short drafts. Both independent reviewers
also checked the revisions and found no remaining material issue. No
simulation or production code changed, so a new full model-test run was
unnecessary.

## Follow-up: plain-style pass at `785b4f2`

Accepted Claude's simpler prose in Steps 1b and 2. Small edits preserve its
style while restoring the meaning: the first loss of stability, losses by
about seven years rather than all at seven years, the four-branch/local
scope in the standalone abstract, and temperature swings spanning about
1.3 K. The growth explanation now describes differences shifting relative
abundance without incorrectly saying the raw ratio integrates them. The
continuous crash calculations report populations below one cell, rather
than actual loss of both groups. Smoothness is stated near the exact limit
on the tested branches. A steady hydrogen supply replaces the unsupported
implication that the model's whole supply comes from volcanoes.

“Count a group as extinct when its population falls below one cell” is clear
wording for the model rule, with the ten-year count interval in Scope. Kept
that wording and the single Scope paragraph. No numerical evidence or
scientific conclusion changed. This is a focused review of wording against
the already-checked evidence, rather than a new modelling audit.
