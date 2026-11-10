# Audit of the finite-invasion inference

Codex (GPT-6), 10 November 2026; reviews `c9bbac6`.
**The reference invasion crosses a whole-planet one-cell threshold. The
conversion and endpoint reinvasion signs hold, but the experiment does not
establish that mixed persistence universally requires refugia.**

The [checker](check_finite_invasion.py) loads the historical fixed-activity
population and guild code from Git, refines early events over only 30 years,
and tests reinvasion from the acetogen-only equilibria. It does not repeat
the 100,000-year trajectory. [Results and hashes](finite_invasion_review.json):

```sh
uv run python models/haze_world/review/check_finite_invasion.py
```

## Global counts: correct conversion, assumed population scale

For uniform biomass X in the effective habitat,

    N = X V_habitat A_Earth / m_cell.

The reference V=0.00897067755 L/cm², assumed area 5.1×10¹⁸ cm² and assumed
cell mass 3×10⁻¹³ gDW give total volume **4.57505×10¹⁶ L**. One global cell
corresponds to **6.55731×10⁻³⁰ gDW/L**, or **ln X=−67.196972**, matching the
historical check.

This is an effective, uniformly occupied global habitat, not a measured
population inventory. Cell mass is assumed equal across guilds. The
“rare” acetogen seed of 10⁻¹² gDW/L is **1.525×10¹⁷ global cells**, about
**45.75 kg dry biomass**; it is rare relative to resident biomass, not a
one-cell inoculation. Habitat coverage, cell mass, dose and extinction rule
remain separately identifiable assumptions.

## Event times refine the five-year readout

| Methanogen threshold | Refined first downcrossing (yr) | Historical first sampled crossing (yr) |
|---:|---:|---:|
| 10¹² cells | **10.673592** | 15 |
| 10⁶ cells | **14.504137** | 15 |
| 1 cell | **18.334737** | 20 |

Event functions locate zeros in the continuous positive-coordinate solution.
Tightening tolerances and reducing maximum step from 0.1 to 0.025 years
changes these event times by at most 2.3×10⁻⁹ years. The extra digits document
numerical agreement, not biological precision.

The historical “about 20 years” is therefore supported. The identical
15-year readouts for two thresholds were sampling resolution, not identical
population responses. At the crossings, actual methanogen net growth is
about **−3.6066 yr⁻¹**, whereas demographic loss d is **8.766 yr⁻¹**.
Methanogens still synthesize biomass but fail to replace their losses; they
are not simply declining at rate −d.

Changing only the assumed cell mass tenfold gives one-cell crossings at
17.6963–18.9732 years. Assuming 1% of the global area gives 17.0579 years.
These are count-readout sensitivities on the same trajectory, not new
ecological simulations or measured uncertainty intervals.

## Reinvasion must use growth at the actual resource pressure

The appropriate local criterion is

    λ_M = Y_M [q_M(p,T) − m_M(T)] − d.

| Post-removal f_ac | A-only temperature (K) | H₂ pressure (Pa) | Methanogen λ (yr⁻¹) |
|---:|---:|---:|---:|
| 0 | 283.198777 | 21.463301 | **+0.828424** |
| 0.5 | 294.402510 | 47.872537 | **+8.862522** |
| 0.9 | 273.533586 | 27.355009 | **−3.606310** |

Thus the historical yes/yes/no signs happen to be correct. Comparing
temperature with one central switch is not the general reinvasion test,
especially after changing thresholds or activities.

## Protocol limits change the conclusion

The historical code first follows **f_ac=0.5**, removes methanogens at its
20-year sampled crossing, then sets f_ac to 0, 0.5 or 0.9. The f_ac=0 and
0.9 cases are post-extinction parameter interventions; 0.5 retains the
baseline value. These are not three constant-f invasions from their respective controls. Their
equilibrium values are valid counterfactual endpoints, with that protocol
stated.

The result is evidence that **this invasion history** loses a guild under
the chosen cutoff. It is not evidence that mixed persistence requires
immigration under every initial condition. The locally stable reference
mixture contains **8.75×10²⁵ acetogen cells and 5.16×10²⁵ methanogen cells**.
Initialized there, or sufficiently nearby, the deterministic finite-census
model has both guilds far above all three proposed floors without refugia
or immigration. Different invasion directions, doses, turnover, habitat
structure and census intervals remain open tests.

A one-cell cutoff is a discreteness diagnostic, not a calibrated stochastic
extinction probability; the higher floors are chosen removal thresholds.
After the first removal, later minima from the unmodified continuum
trajectory no longer describe the finite trajectory. Reintegrate after each
event. Use event-triggered removal and discrete censuses as distinct
protocols, and separate natural persistence from rescue supplied externally.
