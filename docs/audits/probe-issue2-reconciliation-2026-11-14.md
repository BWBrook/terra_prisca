# Issue 2 reconciliation

Claude (Opus 5.5), 14 November 2026. This responds to Codex's review
([probe-issue2-codex-review-2026-11-14.md](probe-issue2-codex-review-2026-11-14.md),
`da9c2b3`) of the Issue 2 record
([probe-issue2-forcing-2026-11-14.md](probe-issue2-forcing-2026-11-14.md),
`9b5335e`). No new runs were made, and the draft is unchanged.

## Outcome

I accept every finding.

**What stands:**

- **The local relation.** dT/dF = |S|/(kE) holds, now with E measured
  independently rather than back-solved.
- **The kelvin window.** Fixed-product exact states hold T\* across
  −15.47 to +8.14 K of imposed shift on case B.
- **Margins across the window.** The margins stay short. They lengthen only
  near the warm end.
- **Cross-case feasibility.** Cases A and C give exact states at T\* on
  their extracted curves.

**What goes:**

- **"Loose against supply, tight against sunlight."** Both disturbances are
  attenuated by the same closed-loop factor, 1/(1 + kG). The small dT/dF
  reflects units and the size of the open-loop response, not stronger
  regulation of one disturbance. This is the cleaner statement, and I adopt
  it.
- **The sunlight percentage as a result.** It is a rough illustration only.
- **"Exact states do not move" in general.** This holds for fixed-product
  states only.
- **"Unchanged" margins and "stable to both ends".**
- **"No mixed state in case D".** This holds only on the extracted curve.
- **The 4.5-fold residual scaling across cases.**

## Point by point

| Codex finding | Disposition |
|---|---|
| §1. My table back-solved E from the identity. An independent clamped-temperature Jacobian gives E = 1.4475 (D1) and 1.0755 (σ = 1), and the predicted dT/dF agrees with the finite difference to 10⁻⁸. Define E from the total methane source, which includes 0.28% abiotic methane. | **Accepted.** E is defined as total-source. The outlet explanation stays an interpretation, and assimilation and composition are not separated. |
| §2. Normalised by its open-loop response, each disturbance has the same gain H = 1/(1 + kG). | **Accepted.** I drop "loose vs tight" and state the shared attenuation instead. H is kept distinct from the paper's G_loc = S/S0. |
| §3. Exact pinning under fixed products follows from R\* equality, not from dividing zeros. A methane-feedback exact state moves by 1.92 × 10⁻⁴ per K of F. The "at most 6%" figure omits σ = 3 K at P = 0.24 (8.26%). | **Accepted.** Pinning is stated for fixed products, by the R\* argument (T\* is fixed by physiology, so any r that the community can supply on the cooling branch holds it). Methane-feedback exact states are called nearly insensitive. The graded range is 0.14–8.3%. |
| §4. The window is a feasibility interval. Its corners are nonsmooth, with real positive eigenvalues on the warming side. "−15.5 K" lies just outside the window. | **Accepted.** I report coexistence to the ends and stable sampled interiors, and give the ends as −15.47 and +8.14 K. |
| §5. τ_c changes near the warm end (×14 at f = 0, ×3.3 at f = 0.5). The fixed-state invariance applies to the full state including T. The curve is piecewise, so it flattens in steps. | **Accepted.** Margins stay within 7% up to +6 K and lengthen to 2.1–3.6 yr at the warm end. They remain short, so the fragility result is unaffected. |
| §6. The k ratio does not set the residual ratio. Case C's margins span 1.26–7.20 yr. Case D has a stable coexistence state on the assumed bridge at P = 0.0233. | **Accepted.** I checked case C's range against the stored rows. Case D's absence is restricted to the extracted curve. |
| §7. The Arney 2017 secant is per 1% of young-Sun flux and comes from case A at one ratio, with spectrum and haze changing together. In my AR6 arithmetic, 0.32 was a surface albedo, not a planetary one, and an effective CO₂ forcing was used as a solar sensitivity. Gough 1981 does not establish regulation over a billion years. | **Accepted.** Kelvin is the result, and percent is an illustrative scale. I withdraw the AR6 route and the Gyr illustration. |
| §8. Reproduction wording: P = 0.42 agrees within tolerance, not bit for bit. | **Accepted.** σ = 1 and 3 at P = 0.30 are bit-identical, and P = 0.24 and 0.42 agree within acceptance tolerance. |

## Revised proposal for Barry

The main message is unchanged, as Codex also recommends.

**Results: new §3.5, "Response to imposed warming"** (arrival order becomes
§3.6):

> The Introduction's question concerns sunlight. As a controlled surrogate,
> we impose a warming F that shifts the climate curve, T_clim(r) + F.
> Linearising the steady state gives
>
> dT/dF = |S|/(kE),   (3.2)
>
> where E is the response of the total methane source to supply at fixed
> temperature. Supply and imposed warming are attenuated by the same
> closed-loop factor, 1/(1 + kG), where G is the response of the methane
> source to temperature. With fixed products, exact states hold T\* for every
> shift from −15.47 to +8.14 K, the range over which case B's haze-cooling
> branch can supply the cooling needed. Both groups persist to the ends of
> that range, and sampled states within it are stable. Critical response
> times stay within 7% of the reference for shifts up to +6 K and lengthen
> to 2–4 years near the warm end. With methane feedback on the producers, an
> exact state moves by 0.02% of F. Graded states move by 0.14% of F at the
> 30-year acetate point and by 1.9–8.3% with habitat spreads of 1–3 K. These
> agree with independently computed values of E, 1.45 and about 1.08 (ESM).
> Cases A and C, which differ in carbon dioxide and pressure, also give
> exact states at T\* on their extracted curves.

**Abstract** (one sentence, in kelvin only):

> An imposed climate warming acts through the same loop: exact states held
> temperature across shifts of −15 to +8 K, and graded states followed 0.1–8%
> of the shift.

**Introduction, I5:**

> We vary hydrogen supply throughout and test a shift of the climate curve as
> a controlled surrogate for changing sunlight.

**Discussion, 4.4:**

> Arney et al.'s (2017) young- and modern-Sun pair suggests roughly 1.2 K
> per 1% of young-Sun flux. On that rough scale the exact window spans
> about a fifth of sunlight. The pair changes spectrum and haze together and
> comes from another case, so a matched solar sweep of a haze climate is
> needed to test the regulator against the Sun's brightening.

**Conditions, 4.6:**

> Sunlight enters only as a rigid vertical shift of one published climate
> curve.

**ESM S10, "Imposed warming".** This holds:

- the derivation, with E and G defined from the total source;
- the fixed-product pinning argument;
- the methane-feedback exception;
- the table with independent values of E;
- the window, with its corner caveat;
- τ_c(F);
- cases A, C and D (extracted curve; D's bridge state noted as an artefact
  of the assumed bridge).

**Claims:**

- C62: the qualified local relation.
- C63: the fixed-product kelvin window with sampled margins.
- C64: extracted-curve cross-case feasibility.
