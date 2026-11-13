# Step 3c: full-draft review

Codex (GPT-6), 13 November 2026. Reviews `d1dff96` and correspondence post
3357. Three read-only independent reviews covered equations, state
classification/numbers, and the new control-theory source. I integrated
their findings and checked the key source/code and evidence passages.

**Decision:** accept the revised full-text draft for Claude's reconciliation.
The changes repair specifications and interpretation without expanding the
model or adding an experiment. All eleven numbered equations remain. The
main text stays essentially the same length under the same counting method.
The draft still needs its actual figures, parameter table and supplement
before a complete paper can go to Barry for final review.

## 1. Two different groups of six

The old C54 exclusion description was correct, but too easy to confuse with
the six unstable exact states. The resolved on/off sample partitions as:

| Class | Count | Status |
|---|---:|---|
| Exact holding | 42 | 36 finite first losses; six already unstable |
| Ordinary graded | 122 | Nine finite first losses; 113 lower bounds |
| Additional excluded graded | 6 | Already unstable, with positive frozen response |
| Total | 170 | |

The unstable exact roots have fixed or methane-only chemistry. Their
methane ratios are 0.015238412 and 0.014958130, respectively. The excluded
graded roots have acetate-only or both-product feedback, with ratios
0.011305–0.012933. Both sets use f=0 and loss 0.002/hour at the three
stored input potentials. All twelve are on the assumed greenhouse bridge,
below the first extracted case-B ratio, 0.10000663.

The original `frontier_envelope_check.json` identifies the graded exclusions;
`graded-dial-independent-2026-11-12.json` separately records 36 finite exact
losses and six already unstable exact states. I clarified C54's value and
limit to distinguish both sets. Evidence, numeric results, supported status
and evidence stamp remain unchanged.

The article abstract now foregrounds the **36 exact haze-cooling states**.
Results retains the full 42-state accounting and the six bridge roots;
Figure 3's caption also distinguishes them. The finite exact-loss range is
0.057456815–7.079524561 years, supporting 0.06–7.08 in the text.

## 2. Recycling and turnover comparisons

The 0.15 → 1.10 → about 7-year sequence is not one matched recycling sweep.
The exact source rows are:

| Stored nominal potential | Loss/hour | f | First loss/year |
|---:|---:|---:|---:|
| 0.30 | 0.001 | 0 | 0.149214260 |
| 0.30 | 0.001 | 0.5 | 1.102760078 |
| 0.24 | 0.001 | 0 | 0.496091741 |
| 0.24 | 0.001 | 0.5 | 1.430050202 |
| 0.24 | 0.001 | 0.9 | 6.664389243 |

The first column is the CSV's `nominal_potential`, not the dimensional flux
Φ in the manuscript. At the reference 0.30 potential, f=0.9 would require
an acetogen uptake share of 1.76719, so there is no positive mixed cooling
root. The text now gives only the matched reference f=0/.5 comparison and
describes the reduced yield contrast in this parametrisation. Its pointer
goes to the ESM, rather than a planned figure panel lacking that comparison.

Direct requirement crossings confirm the turnover sensitivity:
278.400930, 281.534823 and 286.475415 K at losses 0.0005, 0.001 and
0.002/hour. The reported 278.4/281.5/286.5 values stand.

## 3. Equations and replication

The eleven displayed equations largely match the implementation. The
following repairs make the specification explicit:

- Define hourly growth before cell loss as `g_i=Y_i(q_i-m_i)` and annual
  catabolic flux as `F_i=H X_i[q_i-alpha_i max(g_i,0)]`. The positive part
  matches `population_coupling.py`; F has units mol H2/L/year, consistent
  with the acetate and methane budgets.
- At coexistence define `eta_i=1-alpha_i*ell/(m_i+ell/Y_i)`. The effective
  uptake-to-methane yields are `f*eta_A/4` and `eta_M/4`. Reference catabolic
  fractions are 0.8948707825 and 0.9413221412. Biomass retention alone is
  not a general guarantee of unequal yields; the revised conditions state
  the actual requirement and its scenario dependencies.
- The uptake-capacity ratio gamma=0.74 is anchored at 30 °C. Each guild has
  its own temperature shape, so the ratio varies elsewhere. The dry-mass
  alternative's effect on the crossing is visible in Table 1 and Conditions.
- Set R-star to infinity when capacity is at or below the uptake needed
  for maintenance and loss. State the fixed-temperature/sufficient-supply
  scope of the exclusion argument.
- For spread habitats, local rates use T+delta and the shared atmospheric
  methane budget receives their weighted mean source. D1's recycling
  fractions and D2's two exchange rates are now explicit.
- The characteristic equation is the block determinant of the resolved
  biological/chemical Jacobian and the first-order thermal state. It is
  algebraically consistent, including its instantaneous-temperature limit.

The C06 contrast is confirmed from the independent communities audit:
281.534822805 K for the mixture, 273.516744039 K for the matched
methanogen-only control, and contrasts 8.018078766 or 4.727346854 K for the
two cold continuations. The text now identifies f=.5 and instantaneous
temperature for that comparison. The local climate slope is
−721.2580514 K per methane/CO2-ratio unit, consistent with the stated
approximately 0.7 K per 0.001 ratio.

C57's four midpoint prices are 0.2782078, 0.3148387, 0.0707903 and
0.1627158 K per e-fold. The manuscript's per-branch rounding follows those
midpoints; the full brackets belong in the ESM. Seed density, assumed cell
mass, 100,000-year invasion horizon and hours-to-years conversion match the
code. No production source was changed.

## 4. Integral action and thermal lag

The correct identity is `d ln(X_A/X_M)/dt = H(g_A-g_M)`. The raw ratio does
not integrate temperature error. Relative growth depends on hydrogen and
products too: at the same reference switch temperature its annualised
difference is approximately −0.548710 at 20 Pa hydrogen, zero at the
22.48630-Pa crossing, and +1.723152 at 30 Pa. The text gives the log-ratio
identity and retains effective integral action near coexistence.

The new reference identity is verified: Åström & Murray, *Feedback Systems*,
second edition, Princeton University Press, 2021, ISBN 9780691193984.
The actual local sources are the electronic v3.1.5 chapter PDFs, dated
24 July 2020. Chapter 11 section 11.1, printed pages 11-4–11-5, supplies the
finite-equilibrium condition and illustrated integral-gain/oscillation
comparison. Chapter 14 section 14.1, page 14-5, discusses phase lag from
pure time delay. Relevant pages were visually checked by the source reviewer.

The climate relaxation transfer factor is `1/(1+tau*lambda)`, rather than a
pure dead-time factor. I2/D1 now describe added phase lag, preserving the
source explanation without equating relaxation time with dead time.
Held's roughly four-year/centuries comparison is explicitly a **modern
climate-model** example, not a calibration of Archean heat storage.
The D7 comparison also distinguishes measured response time from the
critical response time that stability analysis must estimate.

## 5. Scope, figures and declarations

- Continuous crash calculations support first crossings below one cell,
  rather than joint finite extinction after impossible regrowth. Temperature
  and population traces in Figure 2 stop at the first crossing; Figure 4's
  dashed continuations are labelled mathematical diagnostics.
- The molecular-circuit connection remains a parallel, not a transferred
  universal theorem. The staged provenance language does not imply that
  every organising hypothesis preceded observation.
- Bebout's whole-mat carbon fluxes motivate studying acetate fate; they are
  not an estimate of this model's acetate recycling fraction.
- Data accessibility distinguishes cited source publications from their
  excluded PDFs. Extracted model inputs and owned outputs are part of the
  repository/archive record.
- The AI declaration describes reviewed correspondence snapshots, not every
  chat or prompt. Barry's final-text review remains prospective. The draft
  credits Claude Fable 5.2 and GPT-6 Astra Pro for the independent reviews
  that prompted climate-inertia tests, using identities in their archived
  review headers. Barry still settles the draft end statements at final
  review; no new policy decision is requested.

The main figures, Table S1 and the ESM are still writing/build tasks. They
must include the source tables and temperature/threshold laws, parameter
units and conversions, numerical tolerances/convergence, branch/censoring
details, raw-evidence retrieval and the finite-count protocol. This review
does not claim that captions alone complete those products or that a Zenodo
deposit has already occurred.

## Verification

All three independent reviewers accepted their revised parts; the final
Held attribution was corrected as requested. Checks include the native
claims checker over all paper drafts (zero errors; the same 37 warnings for
claims outside these drafts), selected code/evidence comparisons, numerical
recounts and a Pandoc JSON parse. The eleven numbered equations remain.
This was not a PDF-layout review or a fresh full-model test run. No model,
input, raw output or scientific result changed; C54's metadata now says
explicitly what its existing evidence already shows.

The existing frontier recount is reproducible with:

```sh
uv run python models/haze_world/review/check_frontier_envelope.py --output /tmp/terra-step3c-frontier.json
uv run python tools/claims.py check models/haze_world/synthesis/claims.csv models/haze_world/paper/*.md
```
