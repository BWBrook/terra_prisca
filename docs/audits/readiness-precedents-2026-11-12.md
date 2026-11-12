# Readiness check: the Seto–Akagi precedent

Codex (GPT-6), independent source review, 12 November 2026.

**Disposition:** the proposed paper can proceed to writing as a conditional
model study. The central attribution to Seto & Akagi is correct. Three
comparative phrases need narrowing during writing; they do not require
another experiment.

## Source and method

- Seto, M. & Akagi, T. (2007), *Coexistence introducing regulation of
  environmental conditions*, *Journal of Theoretical Biology* 248, 267–274.
- DOI: [10.1016/j.jtbi.2007.05.013](https://doi.org/10.1016/j.jtbi.2007.05.013).
- Source: ignored `local/sources/seto_akagi_2007.pdf`, eight pages. Its DOI,
  title, author identity and pagination agree with the cited work.
- SHA-256: `c68eaaed094e38e591cf5a1d0bc5a4cadbf61f176453cb8c41ade64184f6a33c`.
- Read the paper and inspected rendered equations on printed pages 268, 271
  and 273; also inspected its response plots on page 270. Temporary text and
  page images remain outside the tracked repository. This note contains own
  paraphrases and mathematical comparisons, not a copy of the paper.

This review checks the source comparison in
[`literature-framing.md`](../../models/haze_world/synthesis/literature-framing.md).
It is not a comprehensive novelty search or full reading of the other
control-theory papers listed there.

## What the source supports

The model definition on page 268, equations (4)–(8), contains:

1. Two populations with dynamics `N_i' = N_i[beta(T) mu_i(R) - d_i]`.
2. Species-specific Monod resource functions `mu_i(R)=r_i R/(K_i+R)`.
3. A shared parabolic thermal factor, with the same optimum and width.
4. The resource constraint `R=R_init-N_1-N_2`, with immediate recycling and
   no external resource input or output.
5. Algebraic temperature `T=T_b+E_1 N_1+E_2 N_2`.

The main calculations take equal death rates. Positive coexistence therefore
requires equality of both resource requirements. On page 271, equations
(9)–(12), this gives

```
R_coex = (r_1 K_2 - r_2 K_1)/(r_2-r_1)
beta(T_reg) = d/mu_i(R_coex)
T_reg = T_opt +/- sqrt[(1-d/mu_i(R_coex))/c].
```

Subject to positivity and stability, neither coexistence temperature depends
on the background-temperature forcing. Composition changes accommodate that
forcing. The source's resource crossing and regulated plateaus thus directly
precede the general coexistence-pinning mechanism used in haze-world. It is
right to give that mechanism explicit credit rather than present a static
set point as new.

The source has no separate atmospheric methane or acetate stock, no explicit
thermal relaxation equation, no open hydrogen supply and no corresponding
delay-margin or acetate-feedback-strength experiment. Those are defensible
specific contrasts with this paper. The source is a generic environmental
regulation model; using modern strain physiology with an Arney climate curve
does not by itself turn haze-world into a calibrated reconstruction of an
actual Archean community.

## Wording that needs narrowing

| Current comparison | Source-level qualification | Suitable treatment |
|---|---|---|
| The new contribution is “the dynamics” | The source already has population ODEs, nonlinear time courses in section 3.2/Fig. 3, phase-plane trajectories in Fig. 6 and local stability analyses. | Identify the new contribution as this haze-climate dynamical extension, explicit climate lag, measured delay margins, graded-response cost and finite assembly experiments. Do not claim dynamics generally as new. |
| Assembly was not studied | Fig. 3 follows replacement or coexistence from two initially present populations. It is not the controlled resident–invader protocol with finite censuses, refuges or dormant banks used here. | Say the source does not test resident–invader assembly with finite-population loss or the present refuge/dormancy mechanisms. |
| The stable coexistence root depends on the sign of E_1 | Section 4.2.2 simplifies the analytical model to E_2=0. Section 4.3's root/sign discussion carries that assumption, with positivity and resource/background-temperature conditions. | State that assumption when reproducing the sign-based result; do not imply that sign alone settles arbitrary two-species climate effects. |

The comparison table's label “Calibration” would be clearer as
“Parametrisation/application”. The haze climate response is source-based,
whereas the ecological transfers remain conditional. Similarly, uniqueness
against Seto & Akagi does not establish priority against all climate-control
or Daisyworld literature. The paper should describe its own contribution
without an unchecked first-ever claim.

## Consequence for readiness

The close precedent strengthens the need for a precise introduction and
novelty statement; it does not remove the tested contribution. I find no
source-level discrepancy requiring a new simulation before drafting.

The readiness concurrence is for a paper about conditions and dynamics in an
Archean-inspired model, with the capacity-normalisation and acetate-fate
conditions visible. The abstract-only status of other control-theory sources
must remain explicit until they are read in full; their detailed theorems
cannot yet be used to justify the model's mechanism or novelty. Parent review
separately addresses whether the proposed “leak” language is an exact
derivation or a local control analogy.
