# Independent synthesis audit: turnover, refuge function and dormancy

Codex, 11 November 2026. Audit of provisional C12–C15 and C21–C23 in the
haze-world synthesis at `6042391`. The
[checker](synthesis-turnover-audit-2026-11-11.py) and
[machine output](synthesis-turnover-audit-2026-11-11.json) retain independent
recounts, algebraic roots, raw hashes and source identities. No model,
physical trajectory, old classification or threshold was changed.

All seven claims can be supported at the amended scopes below. The current
synthesis/estimands need three substantive qualifications before support.

## C12: turnover-controlled branch, conditional on physiology

Recounted `figures/turnover/regimes.csv`: **859 equilibria at 245 settings**.
The actual sampled stable-mixed temperatures are **273.616–295.672 K**.
The quoted **273.4–296.1 K** instead describes the rounded limits of the
root-delimited branch: **273.390–296.0911368 K**. State that distinction.
The lower limit depends on the digitized climate minimum and the named cold
physiology continuation. It is not a resolved physical early-Earth window.

Solving the explicit saturating-uptake break-even formula

    q_i = m_i + L/Y_i
    P_i* = P0_i + K_i q_i/(V_i-q_i)

for equality at 273.390 K independently gives
**L = 0.00023335239009623/hour**, reproducing the onset in
`figures/turnover/boundaries.json`. Uptake must have `q_i<V_i`; otherwise this
formula cannot supply a living consumer.

“Turnover sets the set point” means varying shared loss under fixed
physiology moves the competitive crossing. Yield, maintenance, affinity,
capacity and cessation thresholds all enter that crossing. The synthesis's
“turnover, not tolerance” should not imply physiological independence.

## C13: bistability occupies bounded intervals

At `f=0`, equality of the break-even pressures at the acetogen-world
283.1987768 K independently gives the acetogen invasion/stability boundary
**0.00123814494915118/hour**. The ledger's boundary value is correct.
“Bistable above” is too broad:

- **0.001238145–0.003936106/hour:** stable acetogen and mixed equilibria.
- **0.003936106–0.004088515/hour:** stable acetogen and methanogen equilibria.
- Above the second interval the acetogen-only state can be the sole stable
  equilibrium; at still larger loss only lifeless remains. Representative
  full inventories at **0.0042/hour** and **0.0095/hour** demonstrate these
  counterexamples to unbounded bistability.

The transition values come from `figures/turnover/boundaries.json`;
classification is local equilibrium stability, not enumeration of every
possible attractor. Exact boundaries may be marginal and should not be
silently included as ordinary strictly stable interior points. E2's allowed
wording must specify an interval or “a bistable window begins at”.

## C14: 0.28 K is a forcing diagnostic

For `refuges_0115` (`f=0`, shared loss 0.0015/hour, two absolute refuges,
exchange 10^-6/year), recomputing the methane from the warm/cold endpoint
stocks, omitting bulk methane, and applying the explicit first-order loss
balance gives ratio **0.0056017991378453** and temperature
**284.669797385709 K**. Independently solving the thermal crossing gives
**284.390390960552 K**: a forcing margin of **0.279406425157 K**.

This is a fixed-flux establishment diagnostic, not a separate spatial
equilibrium. The actual mixed endpoint is **284.390390979974 K**, effectively
at the switch, rather than 0.28 K above it. It helps explain why refuge
methane enables bulk invasion beyond the isolated bulk's bistability
boundary. It does not measure a 0.28 K extension of a temperature interval.
Its low ratio is below Arney's extracted branch and uses the assumed bridge.
Evidence: `figures/turnover/endpoint_assessment.json` (endpoint state and
forcing diagnostic) plus `figures/turnover/refuges.csv` (case identity and
opposite-history endpoints).

## C15: source–sink occupancy and temperature pinning differ

For `refuges_0149` (`f=0`, shared loss 0.002/hour, two relative refuges,
exchange 0.001/year), recomputing catabolic fluxes from the stored endpoint
state gives methanogens **2.082381568% globally** and
**0.00107985554% in the bulk**, matching the quoted 2.082% and 0.001080%.
Bulk methanogen net growth is **−1.66191223/year**, so immigration maintains
that population. The bulk temperature **284.60593796 K** is well below its
competitive switch **286.47541462 K**; this is not pinning at the switch.

E10's assertion that an immigrant-supported sink “does not regulate the
climate” is too absolute. The refuge source still emits methane and can
shift climate; occupancy alone establishes neither autonomous bulk
competition nor temperature buffering. Report the ecological and climate
quantities separately. Evidence: `figures/turnover/refuges.csv` and the
explicit endpoint state in `endpoint_assessment.json`.

## C21: recurrence with a locally stable root, not a proved periodic attractor

Read SHA-verified 80,000–82,000-year precision-control raw stocks for 0024,
0126 and 0012, and recomputed their temperatures. Ranges are respectively
**0.3307015, 0.2024742 and 1.4820034 K**, supporting the rounded 0.2–1.5 K
range. Independently constructing scaled physical Jacobians at two difference
steps gives strictly negative leading real eigenvalues at all three stored
mixed roots. This confirms the local-stability/observed-recurrence contrast.

Case 0012 includes **28 local census removals**, so it is a hybrid census
recurrence, whereas the two nonspatial controls have no removals. Do not
combine them into a theorem about a continuous periodic orbit. The stored
long native windows, tight controls and finite durations are evidence for
recurrence; no Floquet stability, global basin or asymptotic orbit is proved.
Specific evidence: `review/dormancy126_cycle_0024.json`,
`review/dormancy126_cycle_0126.json`, `review/dormancy0012_cycle_check.json`
and their raw-control receipts. The new audit provides an independent
spectrum/range route without new trajectories.

## C22: three decaying controls, two unresolved

Independently re-read raw linear controls and measured the two final windows.
Cases 0024, 0032 and 0126 span 0–20,000 years. Their final 5,000-year temperature
spans are **2.43291549e-5, 1.71932394e-5 and 4.09020943e-5 K**: **0.19975,
0.20078 and 0.36512** of the preceding window's span. Thus all three show
continued damping. This is finite-duration evidence, not a general stability
theorem for the nonsmooth linear equilibrium.

The summary correctly leaves 0012 and 0068 unresolved. A returned 2,000-year
startup for 0068 is not a completed long comparison; the 80,000-year
switch-only inputs have zero returned continuation duration. No timeout
supplies an ecological outcome. Evidence:
`review/cycle-closure-results-2026-11-11.json` and its pinned raw controls.
The ledger's current default module command only produces a small default
pilot. Use the stored controller arguments or the analysis command, not
that default as the reproduction of all five controls.

## C23: independently reproduced partition and failed bank forecasts

Recounting row classes gives **56 strict stationary, 41 macrostate stationary
with unresolved bank, 31 other unsettled, 0 verified bank relaxation**.
Additionally, every candidate bank was independently forecast from the
stored initial late bank and root coefficients using a weighted-symmetric
eigendecomposition of the linear bank matrix. This differs from the
original assessor's augmented-matrix exponential over successive saved
intervals. All 41 cases still fail the fixed 0.001 range-error criterion;
the smallest per-case worst-bank error is **0.284584978** of its observed
range. Thus this is not a marginal classification near the bound.

No conclusion follows about eventual convergence, biological relevance or
whether the residual source variation is physical or numerical. Preserve
the strict flags. Evidence:
`review/dormancy-tail-assessment-2026-11-11.json` plus its SHA-pinned raw
records. The new audit verifies the key bank-fit result rather than merely
repeating its row labels.

## Reproduction

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache MPLCONFIGDIR=/tmp/terra-prisca-mpl OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run python models/haze_world/review/synthesis-turnover-audit-2026-11-11.py
```

The raw inputs are the existing accepted turnover/dormancy archive and its
incremental closure payload, identified by the public payload receipts.
This audit adds no raw arrays, new long trajectories or numerical producer.
