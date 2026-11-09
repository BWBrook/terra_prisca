# Challenge to the crossover inversion

Codex (GPT-6), 9 November 2026; reviewed `f80db0d`. The inversion algebra is
correct. Whole-culture rates are a reasonable working reconstruction target,
but approximate textual landmarks do not uniquely identify the authors'
normalization. The vertex repair uses the correct segment geometry; all
71 existing tests pass.

## The 200 Pa statement is in the abstract

The original abstract, printed p. 153, reports thresholds below 2 Pa for
methanogens and below 200 Pa for homoacetogens, except cold MSP. The saved
middle-page excerpt omitted the abstract. This is the source of the existing
coarse parameter boxes, not a number inferred from the competition plots.
These descriptive ranges are not strain-specific measurements or confidence
limits. Registered source:
[Kotsyurbenko et al. (2001)](https://doi.org/10.1111/j.1574-6941.2001.tb00893.x).

## What the inversion establishes

For positive methanogen rate v_M below acetogen capacity V_A,

    p_A* = p − K_A v_M/(V_A − v_M).

A physical solution also needs 0 ≤ p_A* < p. Negative results are failures of
that parameter/crossover combination, not negative biological thresholds.
Independent forward substitution verifies the inversion.

At exactly 80 Pa (4 °C) and 10 Pa (15 °C), the reported marginal parameter
boxes give the following extrema. The boxes are not a joint 95% confidence
region; covariance is unknown.

| Basis | 4 °C inferred threshold (Pa) | 15 °C inferred threshold (Pa) |
|---|---:|---:|
| Culture | −30.000 to 42.857 | −3.077 to 6.675 |
| Equal dry mass | 10.000 to 68.155 | 1.250 to 8.585 |

Negative endpoints are inadmissible. Thus the nominal fixed-pressure
dry-mass contradiction survives correction of the review's smaller maxima.
The original inversion script only generates central values; the new
checker enumerates the marginal-box corners as well.

The 15 °C sentence gives acetogen dominance **above** about 10 Pa. It does
not expressly establish equality there. The appropriate use is an inequality
on uptake, rather than an exact additional threshold measurement.

## Sensitivity to the approximate landmarks

The source supplies no numerical error bounds for its approximate pressures.
The following is a deliberately explicit what-if test: lower 80 and 1,000 Pa
by 10%, while retaining the 15 °C winning condition at 10 Pa. Use one common
acetogen mass of 4.2 mg at every temperature, MSB mass 5.8 mg at both
temperatures, and MSP mass 7.0 mg. Every chosen kinetic value and mass is
inside its reported marginal range.

| Temperature (°C) | Pressure used (Pa) | Acetogen threshold (Pa) | Specific acetogen / methanogen uptake |
|---:|---:|---:|---|
| 4 | 72 | 5.301608 | 13.293889 / 13.293889 |
| 15 | 10 | 7.000000 | 1.738186 / 1.292175 |
| 30 | 900 | 189.225779 | 92.492782 / 92.492782 |

Rates are nmol H₂ h⁻¹ mg⁻¹. Methanogen thresholds are 0.1, 1 and 1 Pa,
respectively. All evaluated pressures are above both thresholds. The
acetogen thresholds increase monotonically with temperature and remain
below 200 Pa. An independent rational-arithmetic check confirms the rates.

This is **not a calibration, a probability statement, or a claim that 10%
is the source's actual uncertainty**. It demonstrates that the exclusion
depends on treating unquantified approximate landmarks as exact. The
central-value normalization discrepancy remains, and the culture hypothesis
may require fewer adjustments; no likelihood or covariance model permits a
formal ranking here. Qualitative product-stoichiometry language is also not
a precise independent constraint on residual hydrogen.

The source's monotone cooling trend is informative, but neither it nor three
approximate pressures recovers a full threshold curve. Close this tranche
as: kinetics reproduced; selected textual landmarks compatible with a
culture-rate interpretation; figure normalization and figure fidelity remain
unresolved. Further pixel recovery need not block work on a separately named
growth model with explicit source uncertainty.

## Thermodynamic subcheck

For constant activity combination and fixed cessation energy ΔG_c per whole
four-H₂ reaction,

    ln[p*(T₂)/p*(T₁)] = (ΔH° − ΔG_c)/(4R) (1/T₂ − 1/T₁).

The enthalpy-only ratio is the special equilibrium case ΔG_c = 0. A measured
nonzero critical energy, temperature-dependent activities or pH/speciation
requires the corresponding terms. This cannot be treated as a separately
measured threshold curve.

Reproduce the corner ranges and shared-mass witness:

```sh
uv run python models/haze_world/review/check_uptake_inversion.py models/haze_world/review
```

[Machine-readable inputs, checks and results](inversion_challenge.json).
Growth-model parameter evidence is in
[growth-parameters.md](../evidence/growth-parameters.md).
