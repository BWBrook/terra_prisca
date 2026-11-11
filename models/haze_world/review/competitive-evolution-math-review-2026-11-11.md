# Mathematical audit of competitive evolution

Codex (GPT-6), 11 November 2026. Bounded independent review of the
[specification](../competitive-evolution-spec.md), original preview and new
kinetic-position implementation. The [checker](competitive-evolution-math-review-2026-11-11.py)
and [receipt](competitive-evolution-math-review-2026-11-11.json) use separate
per-segment minimization, source formulas and finite differences. No original
model, prediction or trajectory is changed. The numerical checks below are
selected controls, not a repeat of the full production inventory.

## The preview allowed a different trait range

The explicit specification confines heritable kinetic positions to the
measured **4–30 °C** interval. The preview's `TK_GRID`, however, starts at
**−0.15 °C**. Below 4 °C the named constant-shape continuation holds V and K
at their 4 °C values while the Arrhenius multiplier still changes with the
kinetic position. That creates a below-measured-range opportunity.

Independent continuous minimization of every measured linear segment gives:

| L/hour | E/eV | Preview lower bound −0.15 °C | Specified lower bound 4 °C |
|---|---:|---:|---:|
| 0.001 | 0 | 277.960221 K | 277.960221 K |
| 0.001 | 0.2 | 280.374092 K | 280.374092 K |
| 0.001 | 0.45 | 283.744938 K | 281.105495 K |
| 0.001 | 0.65 | 283.839481 K | 281.868247 K |
| 0.003 | 0.45 | 294.434308 K | 292.520638 K |
| 0.003 | 0.65 | 292.164234 K | 290.928165 K |

The differences exceeding the 0.5 K preview gate are therefore explained by
an input-bound mismatch, not an integration error. Enforce the explicit
measured trait range and retain the preview/predictions as their historical
record. The eight selected measured-range roots agree with the production
S1 CSV to **2.6e-11 K** or better. This does not establish global uniqueness
outside the searched temperature domain or rule out arbitrarily narrow
unsampled features.

The multiplier must use kelvin for both temperatures and eV for E with the
matching Boltzmann constant. Its fixed-T log derivative with respect to
kinetic position is `−E/[k_B (u+273.15)^2]`; increasing E biases toward lower
kinetic positions, combined with the measured V/K shapes. It is a specified
phenomenological Arrhenius translation constraint, not measured evidence
for a genetic cold-adaptation cost or a universal hotter-is-better trade-off.

## Prescribed S2 refutes the exclusive-anchor prediction

At L=0.001/hour and E=0 the baseline crossing is **277.960221 K**, with best
positions **10 and 25 °C**. Holding either the threshold functions **or the
maintenance functions** at their 30 °C values removes this crossing; both
controls favour methanogens throughout the supported temperature interval.
For example, with maintenance frozen, R* at 273 K is **58.3305 Pa** for
acetogens versus **32.1231 Pa** for methanogens. KE5's claim that freezing
maintenance alone does not remove the crossing is refuted. The threshold
part of that prediction is supported at this setting.

Freezing a function at 30 °C changes its level as well as its temperature
dependence. It does not isolate which derivative supplies the local restoring
feedback. A separate **post-prediction matched-level diagnostic** holds each
function at its value at the baseline root, leaving the root itself intact.
At that root,

    d(R*_A − R*_M)/dT = 0.402999486 Pa/K
                       = 0.197473654 (thresholds)
                       + 0.205525832 (maintenance).

Holding root-level thresholds fixed leaves the positive maintenance slope;
holding root-level maintenance fixed leaves the positive threshold slope.
Holding both root levels fixed gives zero slope and degenerate equality in
this local E=0 control. Thus both thermal terms contribute restoring slope;
either retained thermal term can supply the local restoring orientation at
the matched levels. The prescribed 30 °C results and this diagnostic answer
different questions.
Do not replace KE5 with the diagnostic or claim a thermodynamic-only anchor.

## Why R* minima are uninvadable here

For the specified family, a trait changes V and K only. Yield, maintenance
and threshold at the local temperature are common to resident and mutant
of the same guild. Uptake and net growth increase strictly with hydrogen
pressure above the threshold. Consequently a mutant whose R* is below the
resident's pressure grows; one whose R* is higher does not. A global R*
minimum is therefore uninvadable in its break-even environment. It need not
maximize growth at every arbitrary pressure, and nonviable capacities must
remain infinite R*, not false sign-changing roots.

S4's explicit mutant-grid assay is valuable independently of the optimizer.
It verifies the recorded finite grid, not all unmodelled mutations or every
possible biochemical trait.

## Convergence stability: smooth minima and corners differ

Write invasion growth as `g_i(v; p,T)` and `R_i(T,u)` for guild i. At the
resident break-even pressure,

    s_i = partial_v g_i = −g_{i,p} R_{i,u},   g_{i,p}>0.

For a smooth joint best response, `R_{A,u}=R_{M,u}=0`. The mixed branch obeys
`R_A(T,u_A)−R_M(T,u_M)=0`. If its temperature crossing is transverse, implicit
differentiation gives `T_{u_A}=T_{u_M}=0` and hence `p_{u_A}=p_{u_M}=0`.
For canonical velocities `w_i N_i s_i` with positive per-cell mutation/birth
weights, derivatives of the abundance factor multiply zero selection.
Therefore

    J_ij = −w_i N_i g_{i,p} R_{i,uu} delta_ij.

A strict, nondegenerate R* minimum has a negative canonical eigenvalue.
Changing a positive mutation-supply ratio cannot reverse that sign **in
this restricted smooth family**. A ratio can change trajectories and time
scales. A generic statement that it can change convergence stability does
not apply automatically to these joint optima.

A selected smooth E=0.65, L=0.001/hour linear-shape point independently gives
T=**281.868246684 K**, positions **5.72089138 and 8.31800788 °C**, and positive
biomasses. Re-equilibrating the environment before taking finite differences
gives nearly diagonal canonical matrices at both step sizes. All three
supply ratios are attracting; numerical off-diagonal terms are below
4.1e-13 in the declared arbitrary time normalization. A separate five-point
ecological Jacobian has leading pair approximately
**−0.000800013 ± 0.0376797 i/year**, agreeing at two stencil scales. The new
budget's redox residual at this independently reconstructed state is about
**1.4e-18 mol H2-equivalent/L/year**.

For a linear-interpolation optimum at a data node, an ordinary canonical
Jacobian does not exist. Strict left-positive/right-negative selection
supports an attracting generalized corner. At the trait bounds use the
appropriate projected one-sided criterion. PCHIP is C1 but only piecewise
C2 at its nodes, so both curvature sides matter there. Flat optima,
nonisolated ties, tangential crossings or an ecologically unstable resident
branch need qualified or undefined convergence status, not a fabricated
Jacobian certificate.

## S5 and interpretation limits

The implementation's S5 uses local mutant gradients, abundance weighting,
projected trait bounds and event-snapped data nodes, not global best-response
iteration. Its two maximum trait steps provide a numerical sensitivity check.
It stops when the supported stable mixed branch is lost; this is not a
finite-population extinction event. Pure-resident adapted endpoints are
separate fixed-point/invasion assays unless a path actually reaches them.

The final implementation checks ecology at every accepted trait step and
separates the last supported state from attempted traits after branch loss.
The paired maximum trait steps give endpoint temperatures differing by up
to 0.2071 K and traits by 0.0267 °C; all sixty triggered paths stop at loss of
the supported mixed branch. These are bounded branch-tracking results, not
a proof excluding all between-step instabilities or branch jumps near a fold.
If the re-equilibrated resident ceases to exist, the canonical flow itself is
undefined without a further ecological branch-selection model.

## Final production-result checks

The final tables distinguish **42 stable cooling-branch communities**,
**14 additional unstable greenhouse-branch mixed roots**, and **30 settings
without a feasible joint community**. The greenhouse roots do not refute
KE6's cooling-branch clause. An independent all-grid fitness calculation
checks all 112 guild assays at the 56 joint roots using separately evaluated
V/K interpolants and uptake expressions. The checker also verifies final
source/output hashes and independently recomputes five-point ecological
spectra for a paired warming/cooling high-turnover case. The production
501/1001 inventory comparison agrees for all 200 recorded equilibria; this
remains a numerical inventory comparison, not proof excluding every tangent
or degenerate root.

At low turnover, the separately adapted methanogen-only roots are at
**274.002 K**, exactly the prescribed high-methane plateau. Their temperature
therefore inherits the climate extension. It is not an interior Arney
cooling-branch prediction, nor a demonstrated endpoint of the terminated
canonical paths. The qualitative no-crossing component of KE3 and its
informal “near273.5K” temperature wording should be assessed separately.

The reference enzymes' kinetic shapes, bounds, growth budgets, imposed
non-evolving maintenance/yield/threshold functions and fixed product activities
remain assumptions. Selection in this family cannot change reaction
thermodynamics by construction, but that fact does not prove general
persistence of a competitive crossing. Nor are the selection time,
mutational supply or the predicted planetary temperatures calibrated to an
Archean biosphere.

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache MPLCONFIGDIR=/tmp/terra-prisca-mpl OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run python models/haze_world/review/competitive-evolution-math-review-2026-11-11.py
```
