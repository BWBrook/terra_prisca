# Issue 4: Codex review and oxidant-source check

Codex (GPT-6), 16 November 2026. Reviews `3628035`, C67–C68 and the
proposal in board post 3496, at base `ce0d22b`. Independent bounded checks
covered the budget, selected stability margins and forcing windows; a
separate source pass checked sulfate, and I checked the iron source and
re-ran the numerical checks. No new model, integration grid or research
stage was run. The manuscript and adopted main message remain unchanged.

**Decision:** foreground the condition, but specify a **competition-dependent
methane-yield difference**. The source data and selected numerical results
pass; the interpretation needs the corrections below. The evidence does not
calibrate f near 1, and 20 Tmol acetate yr⁻¹ is a reference-scenario example,
not a universal sink requirement. Barry's choice about the main message is
still open.

## What reproduces

- All 24 analytical supply-window rows, with and without biomass recycling,
  match an independent calculation. The catabolic fractions are
  η_A = 0.894871 and η_M = 0.941322.
- Independent hydrostatic-column conversion gives 65.2143 Tmol total and
  65.0326 Tmol biotic methane yr⁻¹ at the reference state, matching the
  production conversion.
- Finite differences of the physical ODE and a separate eigenvalue
  calculation reproduce selected exact margins: 1.10736 yr at f = 0.5
  mid-window, and 21.2725/30.6566 yr at f = 1 mid-window/upper sampled
  position. The full-product upper-position margin at f = 0.5 is
  48.2902 yr. Finite supply perturbations reproduce the mid-window graded
  sensitivities of −1.33215 and −15.3695 K per e-fold.
- Intersecting the independently calculated methane-feasibility interval
  with the native cooling segments gives warming-window widths of
  23.618, 23.618, 16.5856 and 6.59254 K at f = 0.5, 0.7, 0.9 and 1.
  Their differences from the stored values are below 0.02 K, consistent
  with two inward-bisected endpoints each accurate to 0.01 K. This check
  establishes feasibility, not continuous stability throughout each window.

## 1. The fixed sink is acetate plus biomass

Let U = J − e be captured hydrogen, u_A + u_M = U its allocation, and n the
hydrogen-equivalent flux needed to produce the target biotic methane. Then

    n = f η_A u_A + η_M u_M
    u_A = (η_M U − n)/(η_M − f η_A)
    D_acetate = (1 − f) η_A u_A
    D_biomass = (1 − η_A)u_A + (1 − η_M)u_M
    D_acetate + D_biomass = U − n.

The D terms are mol H₂-equivalent per unit time. Divide by four to express
them as methane-equivalent fluxes. At the reference supply P = 0.3:

| f | Acetate export (Tmol acetate yr⁻¹) | Biomass export (Tmol CH₄-equivalent yr⁻¹) | Combined export (Tmol CH₄-equivalent yr⁻¹) |
|---|---:|---:|---:|
| 0 | 21.184 | 6.542 | 27.726 |
| 0.5 | 20.187 | 7.539 | 27.726 |
| 0.7 | 18.996 | 8.730 | 27.726 |

Thus **total** non-methane export is f-independent at this fixed feasible
state; acetate alone is not. At P = 0.3 coexistence requires f < 0.783458:
the reference mixture does not exist at f = 0.9 or 1. At f = 0.9 and
P = 0.24, the original evidence instead gives 2.242 Tmol acetate yr⁻¹.
Replace “20 Tmol acetate whatever f” throughout the proposal and C68's
interpretation with a stated reference example and the combined budget.

The counterfactual baseline also matters. Additional export relative to
all methanogens at the same supply and T* is 22.2833 Tmol CH₄-equivalent
yr⁻¹; extra hydrogen supplied above the lower-supply methanogen endpoint is
23.6723 in those units. Neither is the 20.1875 acetate flux or the 27.7262
total export. Avoid interchanging these meanings of “above methanogens”.

With all lost biomass returned as methane, the reference required acetate
export would instead be 27.726 Tmol yr⁻¹ wherever coexistence is feasible.
The proposed 20-Tmol sulfate and 160-Tmol Fe(III) comparisons should identify
the f = 0.5, biomass-exported scenario. They are approximately 20.19 Tmol
sulfate or 161.5 Tmol Fe(III) yr⁻¹, not universal Archean requirements.

## 2. Equal final yields remove the exact plateau, not every climate effect

The analytical b formula is correct. At f = b = 1 the two routes have equal
ultimate methane yields, closing the composition-controlled coexistence
window. This is the essential condition to foreground.

But “competition would not affect climate” is too broad. Away from T*, the
guilds have different hydrogen requirements, and consequently different
hydrogen leakage and capture. At 277.15 K, for example, their R* values are
29.732 and 73.492 Pa. Under the same supply, complete-recovery methane
production at those fixed-temperature resource equilibria would be
90.337 versus 75.710 Tmol yr⁻¹. These are budget counterexamples, not new
self-consistent climate equilibria. They suffice to show why equal ultimate
yields do not erase every capture effect.

Say **the exact composition-controlled plateau disappears**. A common
hydrogen outlet already exists even at complete recycling; the central
condition is that changing the competitive allocation changes net methane
delivery. Persistent export, burial or oxidant-supported processing can
provide that difference. Merely storing material for one methane response
time does not establish the infinite-time steady-state contrast after
eventual complete recovery.

## 3. Keep the f-sweep's labels and limits

- The graded calculations use `chemistry='products'`: **both acetate and
  methane feedback at their full reference strength**, not the acetate-only
  D1 tuning dial. Correct “D1 reference”, “reference κ” and C67's labels;
  the computed numbers themselves need no retuning.
- The observed τ_c(Q − 1) ≈ 1.00–1.10 yr relation is a mid-window sampled
  result for f = 0.5–1 with biomass exported. Retain the approximate sign
  and this scope; do not extrapolate it as a law of the unimplemented
  biomass-recycling dynamics.
- At f = 1 and window position 0.95, an exactly pinned state **is stable at
  a 30-year lag**, with leading real part −5.77 × 10⁻⁶ yr⁻¹. Mid-window it is
  unstable. Exact control therefore need not require grading to pass this
  particular benchmark when the supply window is narrow. C54's original
  gap remains a description of its C0/C1 inventory; the new states fill it.
- Midpoint |S| ln Q is a local-tangent estimate, not a measured finite
  temperature excursion. Across the stored 5–95% supplies, full-product
  temperatures change by 1.251, 1.214, 1.162, 1.086, 0.963, 0.863 and
  0.690 K as f rises from 0.5 to 1. Label the proxy or report those actual
  excursions, specifying the sampled span of the exact-reference window.
- The estimate 2.10382 is 5.43% above the exact 1.99551 at f = 0.5:
  replace “within 5%” with “about 5%” or “within 6%”.
- Conditional b = 0.98–0.998 gives Q − 1 = 0.0835–0.00833%, and the local
  warming proxy k ln Q = 0.117–0.0117 K. Report a range rather than a single
  0.1%/0.1-K value. Bulk burial is not a measured guild-specific recovery
  fraction; the conversion to b assumes all other material becomes methane.

## 4. What the oxidant sources support

The detailed primary-source pass and verified DOIs are in
[`probe-issue4-oxidant-sources-2026-11-16.md`](probe-issue4-oxidant-sources-2026-11-16.md).
It supplies a ferric-reduction citation and places the reference demand
against published new-sulfate and iron-recycling scenarios. The comparison
makes a global oxidant-supported sink demanding; it does not provide an
upper bound on all gross oxidant cycling, demonstrate local impossibility,
or measure acetate recovery.

Withdraw “the evidence supports f near 1 as the default” as a source-derived
conclusion. The existing evidence file expressly says neither end-member
is a best estimate. Complete recycling is a useful conditional scenario;
its realized fraction is unresolved. Regeneration of oxidants can create
reductant elsewhere, so a planetary methane budget cannot treat gross
sulfate/Fe(III) throughput as freely available net removal. Oxidant reducers
may also consume hydrogen directly, as the proposal already acknowledges.

## Recommendation and hand-off

I favour bringing the sink condition into the main message, but connect it
to **competition changing methane delivery**, rather than merely the
presence of any non-methane loss. A possible first sentence for Barry is:

> Microbes can hold a planet's temperature when competition diverts hydrogen
> from methane, but exact control fails when climate responds too slowly.

This is a proposal, not a replacement of the adopted wording. The other two
sentences need no change for Issue 4. The body should state the persistent
route-dependent sink and identify the 20-Tmol reference example. The source
record does not establish that an Archean biosphere supplied that sink.

Reproduce the two bounded checks without rerunning the producer sweep:

```sh
uv run python docs/audits/probe-issue4-budget-check-2026-11-16.py --output /tmp/terra-issue4-budget.json
uv run python docs/audits/probe-issue4-dynamics-check-2026-11-16.py --output /tmp/terra-issue4-dynamics.json
uv run python tools/claims.py check models/haze_world/synthesis/claims.csv models/haze_world/paper/03c-full-draft.md models/haze_world/paper/esm/esm.md
```

Both independent checks pass. The existing claims checker reports 68 claims,
35 cited, zero errors and 28 uncited-claim warnings; C67–C68 remain uncited
because the manuscript proposal is unapplied. No manuscript, original
receipt, production model or ledger was edited. Claude can reconcile the
technical scope now; Barry's main-message choice remains his decision.
