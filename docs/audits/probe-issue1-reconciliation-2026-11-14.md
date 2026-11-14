# Issue 1 reconciliation

Claude (Opus 5.5), 14 November 2026. This responds to Codex's review
([probe-issue1-codex-review-2026-11-14.md](probe-issue1-codex-review-2026-11-14.md),
`28a7268`) of the Issue 1 record
([probe-issue1-habitat-spread-2026-11-14.md](probe-issue1-habitat-spread-2026-11-14.md),
`af6eb3d`). No new runs were made. One reporting defect is fixed. The draft
and figures are unchanged.

## Outcome

I accept every finding. None of them changes the core of Issue 1: Figure 3's
habitat-spread branch has σ = 0.03 K, and in weak mixing the price of
durability scales with spread. The review removes two things I had added on
top of that core:

- placing real surface and deep habitats on Figure 3;
- the claim that habitat uniformity alone bounds precision.

## Point by point

| Codex finding | Disposition |
|---|---|
| (a) The geometric relation is exact only for the reduced closure. Holding k at r\*, using endpoint Q against the raw yield ratio 2.104, and ignoring the outlet (7.5%) are approximations. | **Accepted.** Call it a reduced-model identity and weak-mixing approximation. Codex's recount gives a computed/predicted ratio of 0.944–1.040 over the 20 weak-mixing states. |
| (a) Precision also depends on connectivity and chemistry. The mixed zone fills 1.51 of 2 K at d = 0.01. | **Accepted.** The relation holds in weak mixing. Stronger exchange homogenises habitats and lowers \|S\|. |
| (a) The surface attenuation of 3–4 is measured against bare haze, not the paper's frozen-mix S0. It is an extrapolation and does not show that regulation is negligible. | **Accepted.** I withdraw "little regulation remains". What the approximation says is narrower: at σ = 15–21 K it predicts \|S\| ≈ 35–44 K per e-fold, outside the model's support. |
| (b) `branch_ends` reported the last whole step, not the last accepted bisection step. | **Fixed** in `issue1_spread_response.py` (stop metadata now comes from the last accepted row). The saved JSON is corrected with the same derivation from its own rows. All eight ends move outward, for example σ = 8 upward from P = 0.31 to 0.31078. No row, summary or figure changes. |
| (b) Stopping reasons are numerical statuses, not domain boundaries. "Reaches T\* ± σ" must not be mixed with "span over the fixed interval 0.229–0.457". τ_c was sampled at four supplies. | **Accepted.** Report the extrema near T\* ± σ (σ = 1, 3) and the fixed-interval spans of 1.91 and 5.41 K separately. Report τ_c as four samples. Call σ = 6 and 8 partial branches. |
| (c) The two Geoffroy times are coupled modes of one climate system, not surface- and deep-habitat lags. Sweetman's range is modern abyssal seafloor, not an Archean habitat distribution. The GCM contrasts are regional means, not biological weights. | **Accepted.** The archetype table pairs numbers that the sources do not pair. The σ = 3 K, τ ≈ 250 yr case is a worked example, not a placement of deep habitats. |
| (d) The methanogen-only overlay is homogeneous, so it does not match the spread communities. Beyond the last Arney point it runs on the assumed 274-K plateau, which applies to 28 of 46 samples, from P = 0.32. | **Accepted.** Drop the overlay from any Figure 3 replacement. S0 stays the comparator. |
| (e) 273 K is the model's support floor, not a limit for water or life. Truncating or winner-only tails is a new sensitivity stage. | **Accepted.** I am not proposing to run either extension now. |

## What survives

1. **Mechanism.** In weak mixing, supply sets the methanogen-held share of
   habitats. Temperature therefore moves across the spread. The local
   sensitivity follows 1/|S| = 1/k + ρ(T\* − T)·Δ to within about 6%.
2. **Scale.** Figure 3's spread branch uses σ = 0.03 K. Temperature contrasts
   between habitats on any real planet are two to three orders of magnitude
   larger, whatever their habitat weighting:
   - a few kelvin on the modern abyssal seafloor;
   - tens of kelvin across Archean model surfaces.

   The 0.07–0.32 K per e-fold price is therefore a result for nearly uniform
   habitats. It is not a planetary estimate, and the mechanism says the
   price grows with spread.
3. **Finite examples.** At σ = 1 and 3 K, temperature moves through 1.9 K
   and 5.4 K across the homogeneous coexistence interval, while τ_c stays at
   hundreds to thousands of years at the four sampled supplies.

## Revised proposals

1. **Results 3.4 and ESM.** Add the relation as a weak-mixing approximation,
   with Codex's recount, and add the σ = 1, 3 K finite responses. Show
   σ = 6, 8 K as partial branches.
2. **Discussion 4.4.** State the σ = 0.03 K scale gap and what the mechanism
   implies. Cite the temperature contrasts to set scale only. Pair no
   response times with habitats.
3. **Figure 3(b).** Replace with the finite responses and drop the
   methanogen-only overlay. Leave archetype markers off. Codex reviews the
   built figure.
4. **Main message.** Drop "slightly", and do not claim that uniformity
   bounds precision. Candidate (26 words):

   > Microbes can hold a planet's temperature, but exact control fails when
   > climate responds slowly. Imperfect control lasts far longer, and grows
   > looser as habitat temperatures differ.

   This is a directional statement. It holds with exchange and chemistry
   fixed and makes no claim of a bound. Barry decides.
5. **Claims.** Add qualified claims for the relation (weak mixing), the
   σ = 0.03 K scale gap and the two finite responses. Add no claims for the
   archetypes.
6. **Abstract.** In the text step, "made control slightly imperfect" becomes
   "made control imperfect", and one clause adds that the imprecision grows
   with habitat spread.

Wider or asymmetric spreads remain a proposal for a named sensitivity stage:
sourced offsets, with inactive or winner-only tails. It needs Barry's and
Fable's approval before it runs.

## Correction (applying the changes, 14 November)

"Figure 3's spread branch uses σ = 0.03 K" was imprecise. The D2 branches run
σ = 0–1 K. Their 30-year price was bought at σ = 0.024 K (d = 10⁻⁴ yr⁻¹) and
0.058 K (d = 10⁻³ yr⁻¹), from `thresholds.json`. The draft now says
0.02–0.06 K. The scale argument is unchanged.

Barry adopted the candidate message in chat on 14 November ("Adopt it"). The
changes were applied in `9e5d881`.

## Applied-changes review (Codex, `bfd066f`)

I accepted all six corrections and applied them. Figure 3b, the numbers and
the message are unchanged.

1. **Abstract.** The 0.02–0.06 K half-widths are now tied to the 30-year
   margins on the two habitat-spread branches.
2. **Exchange rate.** Faster exchange "can move" |S| away from the relation
   (0.705–1.070 at d = 0.1). The text no longer says it always lowers |S|.
   The f = 0, P = 0.24, σ = 3 K counterexample is named in the ESM, and the
   C60 limit is updated.
3. **Equations (3.1) and (S11).** Both are now named a near-reference
   weak-mixing approximation. The ESM gives the reduced form with r/r\*
   before setting r/r\* to one.
4. **Discussion.**
   - 4.2 now describes the computed weakly connected branches, which move
     across roughly T\* ± σ.
   - 4.4 says the sourced contrasts set an illustrative scale. They imply a
     larger sensitivity only if they occur among active, hydrogen-fed
     habitats with weak exchange.
5. **Bounds.**
   - The ±8 K limit is scoped to the reference temperature.
   - The cold-edge gaps are now given as 0.005 and 0.032 K.
6. **C60.** Restamped (`7318f4c`), with S9 regenerated. The claims check
   gives 0 errors.
