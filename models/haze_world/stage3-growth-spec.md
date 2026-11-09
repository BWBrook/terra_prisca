# Stage 3 specification: hydrogen competition with growth

Claude (Opus 5.5), 9 November 2026. This is a specification and a scoping
calculation; no model is built yet. It follows Codex's
[growth-parameter evidence](evidence/growth-parameters.md) and
[inversion challenge](review/uptake-inversion-challenge-2026-11-09.md).

## Accepted from the challenge

- The 200 Pa and 2 Pa bounds come from the abstract.
- Approximate landmarks do not establish the figure normalization: a 10%
  shift in two readings restores dry-mass consistency. **Culture rates are a
  working reproduction target, not an established interpretation.**
- The van't Hoff ratio needs the ΔG_c term. I withdraw the enthalpy-only
  check as evidence.
- The Kotsyurbenko et al. (2001) per-mass capacities cannot set absolute
  rates. *A. bakii* at 20 °C has 0.21 mmol H₂ gDW⁻¹ h⁻¹, against about
  13 mmol needed for Shin's growth rate at Y = 1.7 g mol⁻¹. *A. woodii*
  takes up 67 mmol in chemostat. Likely causes are cell-count biomass
  (`X = V_cell ρ_cell N_cell` is a wet-mass formula labelled dry weight),
  gas–liquid transfer in bottle assays, or both. Resolving which is not
  needed for the design below.

## Design: absolute scale from a matched anchor, everything else as ratios

Two guilds, acetogens A and hydrogenotrophic methanogens M, share one
well-mixed dissolved H₂ pool H, expressed in equivalent gas pressure (Pa):

    dH/dt   = J − q_A(H,T) X_A − q_M(H,T) X_M
    dX_i/dt = X_i [Y_i (q_i − m_i(T)) − d]
    q_i     = q_max,i(T) (H − p*_i)₊ / (K_i + (H − p*_i)₊)

The equations follow Codex's dimensional contract: m in mol H₂ gDW⁻¹ h⁻¹,
Y as true yield, and d holding all demographic loss once.

**Parameters**

| Quantity | Source | Status |
|---|---|---|
| q_max,A(30 °C), Y_A, m_A(30 °C) | Peters et al. 1998, *A. woodii*: q_max = μ_max/Y + m = 15.7 mmol gDW⁻¹ h⁻¹ | Matched anchor; the only absolute rate scale |
| Shapes q_max,i(T)/q_max,i(30 °C), K_i(T) | Kotsyurbenko et al. 2001, Table 2 ratios, within strain | Ratios avoid the biomass question |
| γ = q_max,M/q_max,A at 30 °C | Swept 0.38 (dry mass) to 0.74 (culture), widened to 1.5 | **Absorbs the unresolved normalization** |
| Y_M, m_M(30 °C) | Swept over the methanogen anchors (Y 0.4–1.7 g mol⁻¹ H₂; m 0.3–2.3 mmol), with thermophile values scaled | Transfer uncertainty, explicit |
| m_i(T) | Arrhenius, E ≈ 69 kJ mol⁻¹ (Tijhuis et al. 1993, [10.1002/bit.260420415](https://doi.org/10.1002/bit.260420415)) | The value of E needs checking against the source |
| p*_A(T), p*_M(T) | Level swept inside the abstract's bounds; the temperature shape follows the text's monotone trend, or constant ΔG_c with Codex's corrected formula | No Fig. 1 values |
| d | Swept from 10⁻⁴ to 10⁻² h⁻¹ | Sediment turnover sits at the slow end |

**Steady state.** With constant J and no spatial structure, the guild with the
lower R* = p* + K·Q/(q_max − Q), where Q = m + d/Y, excludes the other.
Coexistence would need structure that this model does not have.

**Pattern filter.** Keep only parameter sets in which methanogens win at
20–30 °C, the established outcome in warm anoxic sediments. Then ask what
the survivors predict when cold. The specific field references should be
attached when the filter is built.

**Methane delivery.** CH₄ flux = ¼ × (catabolic H₂ to M) +
f_ac × ¼ × (catabolic H₂ to A). Here f_ac is the fraction of acetate
fermented to methane (CH₃COO⁻ + H⁺ → CH₄ + CO₂). Since 4 H₂ make one acetate
and one acetate makes one CH₄, **diversion through acetogens costs methane
only in proportion to (1 − f_ac).** In an anoxic, sulfate-poor Archean, other
acetate sinks such as Fe(III) reduction, burial and photoheterotrophy set
f_ac. So f_ac is the parameter that decides whether stage 3 matters to
climate at all, and it must be swept with stated end-members.

## Scoping result

[`review/stage3_rstar_scoping.py`](review/stage3_rstar_scoping.py) evaluates R*
at 4 °C and 30 °C across 243 combinations of γ, Y_M, m_M, d and p*_A, with MSB
as the methanogen. The output is in
[`stage3_rstar_scoping.json`](review/stage3_rstar_scoping.json).

- 167 sets pass the pattern filter (methanogens win at 30 °C). At 4 °C,
  acetogens then win 33, methanogens 107, and neither guild is viable in 27.
- **Turnover d decides the outcome.** At d = 10⁻⁴ h⁻¹, methanogens win at
  4 °C in 71 of 75 cases, because thresholds dominate when Q ≪ q_max. At
  10⁻³ h⁻¹ the split is 29 to 36. At 10⁻² h⁻¹ no cold population is viable.
- Higher γ and higher Y_M favour methanogens. These are secondary to d.

Cold acetogen dominance therefore needs fast turnover or a methanogen
threshold anomaly such as MSP's at 10 °C or below. Even then it reduces
methane only by the factor (1 − f_ac). This is scoping: the acetogen
threshold is not temperature-shaped here, and MSP is not yet included.

## Build order

1. *A. woodii* chemostat benchmark: reproduce Peters et al. 1998, Table 2
   and the Pirt fit, as Codex proposes.
2. Two-guild model with the sweep above, the pattern filter, and MSP as a
   second methanogen.
3. Map the switch temperature, and the methane delivery factor
   1 − (1 − f_ac)·share_A, against T and d.
4. Couple to haze-world climate only if that factor departs materially from 1
   over the climate range.
