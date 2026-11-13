# Paper display items and supplement: Codex review

Codex (GPT-6), 13 November 2026. Reviews `d15a65a` and `a84fe12`, following
correspondence post 3366. Three bounded independent reviews covered the
transients, parameter table, and supplement. I checked the key numerical
comparisons, integrated the repairs, and inspected the exported figures.

**Decision:** accept the corrected display items for Claude's reconciliation.
The headline trade-off stands. These repairs change a displayed comparison,
trajectory provenance and supplementary budget logic; no production model
parameters or historical experiment outputs were changed. This is not a
release approval or a new calibration of Archean biology.

## Figures 1 and 2

Figure 1 now separates the extracted climate curve from its assumed
low-methane bridge and high-methane plateau. Both extrapolations are dashed
and correctly labelled in the exported data. Panel (b) also shows the
alternative dry-mass capacity normalisation requested in the display plan.
The source-table ratio `(560/7)/(760/3.6) = 0.3789474` puts its crossing at
297.1528 K, just above case B's 297.008 K peak. The reference crossing
remains 281.5348 K. The bar marks the published haze-cooling temperatures;
the caption states that capacity ratios are anchored at 30 °C and that
biomass export is omitted from the schematic.

The original Figure 2(c) compared the exact state at f=0 with a graded state
at f=0.5. Its opening caption incorrectly implied f=0 throughout. It now
compares **matched f=0.5 states**, with first-loss margins 1.1027601 and
38.48635 years. The f=0 margin, 0.1492143 years, remains the correct
reference for the kicked trajectories in panels (a,b) and the separate
recycling comparison in the ESM. The main-text pointer and caption agree.

Both 30,000-year f=0 trajectories were regenerated. Their first crossings,
population minima and temperature summaries reproduce the archived values;
the builder now checks agreement rather than merely recording two columns.
At tau=10 years, the physically interpreted curves stop at the first
one-cell crossing, 1829.9917 years.

The approximately 380-year late oscillation period is supported: consecutive
peaks in the archived 24,000–30,000-year window are 375–377 years apart.
The amplitude is still changing: successive 3,000-year temperature spans
from 18,000 years onward are 1.24698, 1.25849, 1.26380 and 1.26635 K.
Neither settling nor an attracting cycle follows from this finite record.
The caption now says so.

## Figure 3 and the second failed slope prediction

An independent recount, using source CSVs and a separate scalar regression,
confirms the partition of 170 states: 42 exact (36 finite losses, six already
unstable), 122 ordinary graded (nine finite losses, 113 lower bounds), and
six additional excluded graded bridge states. The four exported 30-year
brackets equal their archived continuation brackets. The headline price
remains 0.07–0.32 K per e-fold of supply. Censored margins are shown as
lower bounds, and panel (b) correctly labels local tangents.

The revised C56 is correct. On the prescribed grid and the original
2 < tau_c < 1000-year selection:

| Branch | Points | Log–log slope | R squared | Within predicted 1–2.5 band |
|---|---:|---:|---:|---|
| D1, f=0 | 2 | 1.200473 | 1.000000 | yes |
| D1, f=0.5 | 3 | 0.796568 | 0.984131 | no |
| D2, d=0.0001/year | 6 | 0.985198 | 0.997730 | no |
| D2, d=0.001/year | 5 | 1.108485 | 0.997557 | yes |

Thus two branches refute the slope clause. The two-point D1 fit cannot test
curvature. No prediction record or acceptance band was rewritten. The
recount and input hashes are in
`paper-display-items-check-2026-11-13.py` and its JSON receipt.

## Figure 4: physical invasion paths and matched stability

The original panel used uncensored trajectories and labelled the invader's
entire path physical even after the resident crossed below one cell. Losing
the resident changes the environment, so that later path was also a
counterfactual continuation.

Panel (a) now uses the actual finite-census histories. The first crossings
are 18.3 and 7.4 years; the residents are removed at the subsequent 20- and
10-year censuses. No ghost continuation is plotted. Empty counts in the CSV
mean an absent guild, rather than an extremely small positive population.

All 24 native census archives were hash-verified and their endpoints
recounted: the invader alone remains in both directions, 12 cases each.
The stability labels are also matched. For each chemistry/recycling pair,
the B3 parameter objects equal the homogeneous stability setup, after
normalising its separately represented chemistry flag; perturbed physical
right-hand sides agree within 1e-10 relative. Independently recomputed
spectra confirm **eight of twelve** settings have a locally stable mixture.
This does not imply those invasions reach it.

The raw check verifies every one of the 164 plotted census rows and records
source hashes, endpoint checks, eigenvalues and finite-window periods in
`models/haze_world/review/paper_transient_figure_check.{py,json}`. The default
plot build uses the committed compact exports; explicit `fig4 --refresh`
regenerates them from native archives. Regression checks reject a mismatched
source identity and ensure the default build does not read ignored archives.

## Table S1 and ESM

Table S1 now has **117 rows**, adding the B4 lifetime/slope sweeps,
two-layer constants and selected-state settings. Numerical choices are
distinguished from scientific assumptions. Literal design settings have
parsed-source guards, while unmarked locations are explicitly navigation
aid only. A regression catches a changed tolerance even when its old
numeric literal remains elsewhere. These checks do not prove that an
archived run used today's defaults; native receipts retain that role.

The exact methanogen yield 0.78 and maintenance 0.001 mol H2/gDW/hour remain
uncalibrated assumptions. The yield's source range does not establish the
derivation of this exact anchor. No replacement source or parameter was
invented. The kinetic units and the culture-to-biomass capacity distinction
are explicit, including gamma's 30 °C anchor.

The material ESM repair is in S7. Its former effective-supply calculation
subtracted the hydrogen outlet a second time, despite comparing against
bounds that already included the baseline outlet. The equivalent
zero-reservoir supply is
`P_equiv = P + 0.30*k_ex*p_atm/J_ref`, without subtracting R-star again.
At f=0.5 the reference branch ends at **157.326965 Pa**, not the erroneous
179.813265 Pa implicit in the old formula. Every original coarse pressure
sample happened to keep the same classification, so the new regression
tests the boundary and 160 Pa, which the old check misclassified. The main
C59 results therefore stand.

S8 now calls eta the **catabolised fraction**, and explains that continued
yield contrast at f=1 requires eta_A < eta_M, not merely both below one.
The positive coexistence interval 0.229178–0.239907 is unchanged; it is not
a new all-lag stability result. S3's connectivity-width statement is
restricted to the fixed-product case, and its frozen-slope numerical steps
match the implementation. S6 distinguishes commit chronology from an
independently timestamped computational freeze and identifies prior-informed
predictions. These repairs preserve the original specifications.

The AI-use record includes Sonnet 5.5's display/supplement work and this
subsequent Codex review. Barry's final review remains pending. The older
unpublished core companion predates Stage B; Stage B's large native payloads
still need inclusion in the eventual public evidence deposit. The supplement
states that boundary instead of promising an existing public raw archive.

## Verification and hand-off

- The documented no-argument display command rebuilds all four figures,
  Table S1 and the generated ESM tables. Figure and table exports were
  checked, and the four PDF figures were rendered and visually inspected.
- Twenty-three relevant tests pass, including four new regressions for
  budget boundaries, table guards and figure-data provenance. The two long
  Figure 2 replays and the separate native-data audit also pass.
- The independent Figure 3/C56 recount passes. The claims checker reports
  zero errors; its 29 warnings are claims outside these two selected paper
  documents. No ledger value or evidence stamp changed in this review.

Claude should reconcile these display/caption/ESM repairs, then return to
the agreed text step. No new experiment or scientific decision is needed
for this hand-off. The unsourced biological anchors and release-time raw
data packaging remain explicit limits.
