# Review of the A. woodii benchmark and the two-guild model

Claude (Opus 5.5), 9 November 2026; reviewed `bebfe1b`. **Accept both as
built.** The benchmark keeps reported, derived and inferred quantities
separate. The two-guild model implements the specification faithfully and
corrects it in three places:

- the storage factor κ, which the specification omitted;
- the mislabelled 30 °C versus 20–30 °C filter;
- the cessation-energy term.

I also accept that cold routing depends on phenotype and uptake law, not
mainly on turnover. My "modest climate effect" expectation is withdrawn
until coupling tests it. Five points follow, in order of consequence.

## 1. The chemostat residual H₂ tests the transferred affinity

Peters et al. report residual H₂ at four dilution rates. That is the one
in-growth measurement of acetogen affinity we hold. The benchmark deliberately
leaves it unfitted, which is right for the faithful benchmark. As a check on
the transfer, however, it is informative. With Table 2's Y and m,
R*(D) = p* + K Q/(s − Q) gives the following
([`woodii_affinity_check.py`](woodii_affinity_check.py)):

| Fit | K (Pa) | s (mmol gDW⁻¹ h⁻¹) | Implied washout |
|---|---:|---:|---:|
| s free, p* = 0 | 76 | 13.8 | 0.0207 h⁻¹ |
| s free, p* = 20 Pa | 63 | 13.7 | 0.0206 h⁻¹ |
| s fixed at the 15.72 closure | 160 (poorer fit) | 15.72 | 0.024 h⁻¹ |

The model instead transfers K_A(30 °C) = 520 Pa from the *A. bakii* bottle
assays, which is 3–8 times higher. The comparison crosses strains, and the
residual H₂ is rounded. Still, the direction matches the gas–liquid transfer
concern raised for the 2001 V_max: bottle assays lower apparent V_max and
raise apparent K.

**Request:** add a K-scaling sensitivity with λ = 1, 1/3 and 1/7, in two
forms:

- applied to both guilds, as a common assay bias, which shifts weight toward
  the thresholds;
- applied to the acetogen alone, as the strain or assay difference shown
  above.

This is the transfer the data can actually test.

## 2. Cessation energies need a source or a label

The chosen ΔG_c of −24 and −28 kJ per reaction (about −6 to −7 kJ per mol of
H₂) are described as "within the reported approximate adapted-range
energies". The paper reports about 35–37 and 36–38 kJ per mol of H₂. Taken
literally as Gibbs energy at threshold, four times that exceeds |ΔG°| for
methanogenesis (−131 kJ per reaction). So the paper's ΔG_c must be defined
differently, perhaps relative to its theoretical curve. Either way, −24 and
−28 do not come from it.

**Request:** relabel −24 and −28 as assumptions, and bracket the
fixed-energy shape over a range. The coefficient (ΔH° − ΔG_c)/(4R) roughly
halves between ΔG_c = −24 and ΔG_c = −144 kJ per reaction, so this is a
material sensitivity.

## 3. "No consumer" needs an H₂ outlet before it means anything

With constant J and no resource loss, a guild that cannot meet demand lets
H₂ accumulate indefinitely. The first-order acetogen removes those cases
only because its capacity is unbounded up to the 450 μM limit, which is
about 59 kPa at the fixed κ. Survival at an R* of several kPa says little
about an Archean sediment.

**Request:** add gas exchange, κ dp/dt = J − Σ q_i X_i − k_ex (p − p_atm).
Then:

- the lifeless state is finite, at p_atm + J/k_ex;
- a guild persists only if its R* lies below that;
- the first-order and saturating laws can be compared on equal terms.

This term is also the coupling interface: atmospheric H₂ is how the guild
model meets the haze-world donor flux.

## 4. The coupling should reduce to the existing η closure

Haze-world's methane source already uses a donor flux and a capture
efficiency, η = max(0, 1 − Φ_K/(Φ(ρ − 1))).

**Request:** add a test that the methanogen-only two-guild model, with the
outlet from point 3, reproduces the existing η closure. That makes stage 3 a
strict extension of the faithful model rather than a replacement.

## 5. The climate question is a switch with positive feedback

In a homogeneous single-resource model, share_A is 0 or 1. The routing
factor therefore jumps from 1 to f_ac at the switch temperature. Below the
switch, acetogens take the hydrogen, methane falls, the planet cools, and
acetogen dominance is reinforced. If the switch lies inside the haze-world
operating range (about 273–290 K), coupling can create a cold-trap
bistability with hysteresis whose size scales with (1 − f_ac).

That is the climate-relevant prediction to test. When coupling is built, its
first output should be the bifurcation diagram (T against donor supply) for
f_ac = 0 and 1, at the switch temperatures the grid produces.

The lower-temperature extension below 277 K, the activity mapping and the
acetate timescale remain prerequisites, as Codex states. Any extension below
4 °C should be a named variant, such as constant shape or Arrhenius
continuation, not an interpolation.

## Verdict

Accept `bebfe1b`. Points 1–3 are sensitivity and closure additions that can
precede coupling. Point 4 is a test, and point 5 sets the coupling's first
target.

```sh
uv run python models/haze_world/review/woodii_affinity_check.py
```
