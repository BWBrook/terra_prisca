# Audit of Kotsyurbenko et al. (2001) cessation energies

Codex, 9 November 2026. Independent source check of the energy claim in
Claude's review of `124ef94`.

The paper reports approximately **−5 to −7 kJ per mol H₂ for homoacetogens**
and **−6 to −8 kJ per mol H₂ for methanogens**, within their adapted ranges.
The apparent “35–37” and “36–38” values are a PDF text-extraction error:
the extraction substitutes the digit `3` for a minus sign. The interpretation
in the review should be corrected; it does not indicate a different definition
of critical Gibbs energy. The clean primary publisher HTML gives the negative
single-digit ranges explicitly. [Primary article](https://doi.org/10.1111/j.1574-6941.2001.tb00893.x)

## Source positions and encoding check

The primary HTML [article, section 4](https://academic.oup.com/femsec/article/38/2-3/153/607304?searchresult=1)
contains the ranges in the paragraph discussing average ΔG_c. The same ranges
occur in section 3.1, printed page 156; the discussion continues on printed
page 158. Section 2.4, printed page 155, defines the calculation. The abstract
also gives the combined approximate range −5 to −8 kJ mol⁻¹.

The registered [version-of-record PDF](https://academic.oup.com/femsec/article-pdf/38/2-3/153/18089579/38-2-3-153.pdf)
has several internally checkable extraction failures:

| Extracted token | Correct value in primary HTML | Quantity |
|---|---:|---|
| `3130.7` | −130.7 | Methanogenesis ΔG° |
| `3253.0` | −253.0 | Methanogenesis ΔH° |
| `355.0` | −55.0 | Acetogenesis ΔG° |
| `3270.7` | −270.7 | Acetogenesis ΔH° |
| `35` to `37` | −5 to −7 | Acetogen ΔG_c per mol H₂ |
| `36` to `38` | −6 to −8 | Methanogen ΔG_c per mol H₂ |

The first four energies are kJ per mol of the full reaction. The PDF extraction
also corrupts superscript minus signs in units. No new figure digitization or
visual PDF inspection was needed or is claimed for this audit; the primary
HTML resolves the encoding unambiguously.

## Definition and unit conversion

Section 2.4 calculates Gibbs energy from standard reaction energy and measured
reactant/product quantities using the Nernst equation. It calculates ΔG_c in
the same way with the measured cessation H₂ pressure. Thus ΔG_c is the actual
reaction Gibbs energy at cessation, normalized per mol H₂ when the paper
reports its ranges. It is negative for the exergonic consumption direction.

Both full reactions consume four H₂. Consequently the reported adapted ranges
become:

| Guild | kJ per mol H₂ | kJ per mol full reaction |
|---|---:|---:|
| Homoacetogens | −7 to −5 | −28 to −20 |
| Methanogens | −8 to −6 | −32 to −24 |

The paper's interpretation in terms of a separation between experimental and
theoretical threshold curves is consistent with that definition. At fixed
activities and temperature, write Q=A/p_H₂⁴ using dimensionless pressure or
fugacity. If p_eq is the theoretical threshold where ΔG=0, then

`ΔG_c = −4 R T ln(p_cessation / p_eq)`.

Division by four gives energy per mol H₂. A larger observed threshold than the
thermodynamic equilibrium threshold therefore corresponds to negative ΔG_c;
this is not a separate positive energy offset or a redefinition relative to
ΔG°.

## Why the standard-energy argument fails

Actual energy is `ΔG = ΔG°(T) + R T ln Q`. Standard energy is a reference-state
value, not an upper bound on available energy. For Q<1 the logarithmic term is
negative and ΔG can be more negative than ΔG°. For example, at 298.15 K,
Q=0.01 adds about −11.42 kJ per mol reaction. A hypothetical cessation
requirement with magnitude greater than |ΔG°| is therefore not thermodynamically
impossible merely for that reason. It must instead be checked against the
actual activities, temperature and organism. This correction does not validate
the extraction's spurious large energies.

## Recommended assumption bracket

Use the following adopted anchors, all in **kJ per mol of the full four-H₂
reaction**:

- Acetogen ΔG_c: −20, −24, −28.
- Methanogen ΔG_c: −24, −28, −32.

Their Cartesian product gives nine transparent source-window sensitivity
cases. The existing pair (−24, −28) corresponds to −6 and −7 kJ per mol H₂
and lies within the reported adapted ranges. These are representative
assumptions, not fitted strain-specific values or recovered Fig. 1 points.
Constant ΔG_c outside the adapted physiological range also remains an
assumption.

For a shape anchored at a chosen reference threshold, constant activities,
constant ΔG_c and temperature-independent ΔH° give

`p*(T) / p*(T_ref) = exp[(ΔH° − ΔG_c)/(4 R) × (1/T − 1/T_ref)]`.

Use joules consistently with R and the full-reaction values in this expression.
Values near −144 kJ per reaction may be used only as separately labelled,
arbitrary structural stress tests; they are neither required by this audit
nor supported as the adapted-range values of this paper.
