# Independent population-coupling review

Codex (GPT-6), 9 November 2026. **The reference equilibrium and local
stability claims hold. A rare-invasion path exposed an integrator failure;
the revised positive coordinate passes the bounded independent check below.
A separately identified parent follow-up closes one longer trajectory test.**

The [checker](check_population_coupling.py) derives the five physical
balance derivatives independently. Pressure derivatives are analytic;
temperature coefficients are differenced separately before applying the
climate slope. This avoids merely repeating the source's coordinate-wise
finite differences. It checks disabled coordinates, invasion eigenmodes,
stock residuals, grid resolution and a rare-invasion trajectory.
[Results and code/input hashes](population_coupling_review.json):

```sh
uv run python models/haze_world/review/check_population_coupling.py
```

## Equilibrium and invasion checks

Twenty-one candidates were checked across the reference factory, the
methanogen-only control, f_ac=0 and 1, cold-limited recycling, and an acetate
lifetime of 10⁴ years. The independent Jacobians agree with the implemented
ones; the maximum normalized entry difference is 3.72×10⁻⁷. Every tested
candidate closes its stock equations within 10⁻⁶ Pa/year for pressure and
10⁻¹⁰ in the remaining stock units per year.

For the reference potential 0.3, f_ac=0.5 and one-year acetate lifetime:

| State | Temperature (K) | Largest real eigenvalue (yr⁻¹) | Interpretation |
|---|---:|---:|---|
| Lifeless | 283.198777 | +72.214308 | Consumers establish |
| Pure acetogen | 294.402510 | +8.862522 | Methanogen invades |
| Mixed | **281.534823** | **−0.000926010** | Locally stable |
| Pure methanogen | 273.516744 | +12.123212 | Acetogen invades |
| Methanogen-only control | **273.516744** | **−0.0000971446** | Stable when acetogens are disabled |

The absent-guild growth rate appears as an eigenmode of each pure state.
Thus the stability classification checks more than the fixed-temperature
resource winner. Disabling a guild removes its coordinate and invasion mode
without introducing a spurious zero eigenvalue.

The mixed-state construction uses actual captured supply and the two
distinct assimilation factors. Its acetate stock balances production against
both sinks, and its methane equation closes independently. A constant lag
changes the acetate stock and eigenvalues, while leaving its equilibrium
temperature and source allocation unchanged. This is an equilibrium result,
not a claim that acetate can be eliminated during transients.

Full recycling does not recover the physiological methanogen-only control:
the tested f_ac=1 configuration has a stable pure-acetogen state at
**274.002 K** on the assumed high-methane plateau, versus 273.516744 K in
that control. Capture and assimilation
remain guild dependent. The reduced model's exact f_ac=1 identity was a
property of its imposed common closure.

## Root and stability scope

The reference list of four states is unchanged using 101, 501 and 2,001
ratio-grid samples. Exact climate vertices are explicitly included; the
independent check covers the full-recycling vertex state using both climate
slopes. The repaired sampled-zero handling addresses the reduced finder's
specific omission.

Finite grids still cannot exclude an unsampled tangent root or two roots
inside one cell. Near-coincident roots and equal-endpoint mixture continua
also need explicit treatment before a complete bifurcation classification.
The present finder intentionally skips the degenerate mixture case when
both methane-delivery endpoints coincide. Biological interpolation knots
are additional possible derivative corners: a candidate exactly at one
needs one-sided physiological derivatives as well as climate derivatives.
None of the smooth reference mixed states tested here sits at such a knot.

These local checks do not establish global attraction, persistence under a
finite-population extinction rule, or absence of additional cold branches.
The assumed methane-free bridge and the named low-temperature continuation
remain part of the result's definition.

## Rare-invasion dynamics: failure and bounded repair check

Starting from the stable methanogen-only control, re-enabling acetogens with
X_A=10⁻¹² gDW/L exposed overflow in the original pure-log integrator during
a 20,000-year run. Seeds of 10⁻³⁰, 10⁻¹⁰⁰ and 10⁻²⁵⁰ failed similarly.
The same trajectories could run for 2,000 years, demonstrating that a
near-equilibrium convergence test had not covered the invasion excursion.

The revised integrator uses LSODA and a positive softplus coordinate that is
log-like when rare and linear for large solver trials. In the independent check,
X_A=10⁻¹⁰⁰ from the same control runs for **2,000 years without warnings**.
Its internal/log output stays finite even though methanogen biomass reaches
log B=**−6816.31** and underflows in the exported physical array. Its final
climate is **278.794516 K**, so this run is explicitly **still transient**;
it does not establish convergence to 281.534823 K or close the longer-run
verification gate.

**Parent integration follow-up:** a single uninterrupted 100,000-year run
from the methanogen-only control with X_A=10⁻¹² gDW/L reaches the predicted
mixed stocks and 281.534822805 K; its final methane tendency is about
−3.5×10⁻¹² yr⁻¹. The [experiment record](../population-coupling.md) retains
that protocol and trajectory. This is additional parent-run evidence, not
an independent repetition of the long run. The 20,000-year endpoint had
remained far from the mixture; the longer run distinguishes that excursion
from a demonstrated persistent cycle. It does not establish convergence
from every initial condition or realistic survival through biomass minima
near log B=−7,670.

Retaining internal coordinates matters: restarting from an underflowed
physical endpoint would replace a rare population with exact absence.
Likewise, a continuum trajectory through such biomass minima is not evidence
that any finite biological population survives them. Logs solve a numerical
representation problem; an extinction rule is a different model.

## Scientific boundaries

The full model now obtains resource capture, source allocation and the
switch from the same parameter configuration. That removes the reduced
coupling's unsupported mixed-state η identity. The equilibrium pinning is
therefore a conditional result of this population model, rather than an
algebraic routing assumption alone.

Long-lag states can be mathematically stable but environmentally implausible:
the tested 10⁴-year lag stores about **8.82 mol/L acetate**. The fixed-product-
activity thresholds omit that chemical feedback. Interpret long-lag stability
as a structural experiment, not a physically validated habitat. The effective
habitat volume, methane-free climate, transfer parameters and cold continuation
also remain assumptions; this review supplies no Archean calibration.
