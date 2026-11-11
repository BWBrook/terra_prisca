# Claude's review of Stage B1 and B4

Claude (Opus 5.5), 12 November 2026. Reviews Codex's build (`db09eea`,
`1c1df89`, `c96c801`) against my [specification](../dynamic-realisation-spec.md)
and Codex's [frozen methods](../dynamic-realisation-methods.md). The next step
is specified in [continuum-habitats-spec.md](../continuum-habitats-spec.md).

## Verdict

I accept the build and every verdict Codex recorded. Three of my predictions
were wrong on their stated terms:

- **PB2 (C39).** I guessed the wrong mechanism. Acetate self-limitation
  supplies the damping, not the direct methane loop.
- **PB4, two-layer clause (C41).** I left the equations under-specified.
  With `τ_s = 100 τ_f` the low-frequency delay is `101 τ_f`, so `τ_f` alone was
  never the right lag to compare.
- **PB7 (C42).** The prediction was ill-posed. The bank is empty at the mixed
  state, so linear analysis cannot see it, and the clipped ramp has no ordinary
  Jacobian there.

Codex's pre-run corrections also stand. Methane is a leaky stock, not an
integrator. The guild log-ratio integrates a fitness difference, not
temperature error directly. The frontier is therefore a hypothesis about this
model family, not a control-theory theorem.

## The chemistry result supports the frontier

The PB2 refutation strengthens PB1's mechanism. At the homogeneous reference
(`σ = 0`, `f = .5`, C43):

| Chemistry | Supply slope, K per e-fold | τ_c |
|---|---:|---:|
| fixed | ≈ 0 | 1.10 yr |
| methane_only | ≈ 0 | 1.10 yr |
| acetate_only | −1.88 | > 10⁴ yr |
| products | −1.88 | > 10⁴ yr |

The comparison control's slope is −13.26 K per e-fold.

- **Methane feedback keeps exact pinning and does not stabilise.** It acts on
  both thresholds through a variable shared by the whole community. The
  break-even pair (T, r) still does not depend on supply, as Codex predicted
  before the runs. Nothing about it is graded in the guild share, so it adds
  no proportional action.
- **Acetate feedback stabilises and gives up pinning.** It ties the acetogen
  threshold to the acetogens' own product. That makes the acetogens'
  competitive position depend on their own abundance, which is the graded,
  proportional term.

So within the chemistry dimension, the stabiliser that costs pinning is the
one that works. The one that keeps pinning does nothing for stability. The
ranking clause of PB1 holds at the reference. The no-escape clause still
needs the full map.

## Why the habitat calculation does not converge

**Diagnosis.** Each habitat switches from acetogen to methanogen dominance
across a zone whose width is set by cell exchange `d`. The equal-weight grids
of B1 do not resolve that zone. Increasing N then changes which habitats sit
inside the zone, rather than refining a smooth integral.

**Evidence.** I re-ran the B1 equilibrium and lag scan with Codex's
production core, for fixed chemistry, `f = .5`, reference L and supply, and
`σ = 1 K`. Each N started from the homogeneous homotopy. The reproducer is
[check_habitat_resolution.py](check_habitat_resolution.py) and its output is
[habitat_resolution_check.json](habitat_resolution_check.json). "Mixed" means
the local acetogen share lies between 1% and 99%.

| d, yr⁻¹ | N | τ_c, yr | dT/d ln J, K | Mixed habitats | Mixed-zone width, K |
|---|---:|---:|---:|---:|---:|
| 10⁻³ | 9 | 7.23 | −0.074 | 1 | (0.22) |
| 10⁻³ | 17 | 16.3 | −0.18 | 1 | (0.12) |
| 10⁻³ | 33 | 102 | −1.04 | 2 | 0.12 |
| 10⁻³ | 65 | > 10⁴ | −4.05 | 5 | 0.15 |
| 10⁻³ | 129 | 236 | −1.69 | 10 | 0.16 |
| 10⁻³ | 257 | > 10⁴ | −4.17 | 20 | 0.16 |
| 10⁻³ | 385 | 1547 | −3.37 | 29 | 0.15 |
| 10⁻³ | 513 | 782 | −2.79 | 39 | 0.15 |
| 10⁻² | 9 | 87.0 | −0.67 | 7 | 1.56 |
| 10⁻² | 33 | > 10⁴ | −2.22 | 25 | 1.52 |
| 10⁻² | 65 | > 10⁴ | −2.776 | 49 | 1.51 |
| 10⁻² | 129 | > 10⁴ | −2.779 | 97 | 1.50 |
| 10⁻² | 257 | > 10⁴ | −2.772 | 194 | 1.51 |
| 10⁻¹ | 9–129 | > 10⁴ | −2.11 | all | 2.0 |

The N = 385 and 513 rows are in
[habitat_resolution_check_large_n.json](habitat_resolution_check_large_n.json),
from the same script.

**What the table shows:**

- **The mixed zone scales linearly with d.** It is 0.15 K at 10⁻³ and 1.5 K
  at 10⁻². This is the balance between immigration and local selection. Its
  width implies a selection gradient near the switch of roughly
  `d / 0.016 K ≈ 0.06 yr⁻¹ K⁻¹` per e-fold of share.
- **At `d = 10⁻²` the equal-weight grid converges by N = 65.** The supply
  slope agrees to 0.3%, and no lag crossing appears through 10⁴ yr. The rule
  of thumb is about five nodes per e-fold of the share profile.
- **At `d = 10⁻³` it does not converge even at N = 513.** Both τ_c and the
  slope jump between N values, and τ_c is right-censored at some of them.
  The classification is steadier than the values: every N ≥ 33 gives
  τ_c > 100 yr or no crossing, and a slope of −1 to −4 K. The
  leading eigenvalue at zero lag sits at −1 to −2 × 10⁻³ yr⁻¹, which is
  −d to −2d. That is the edge of the quasi-continuous spectrum of
  immigration-limited sink populations. Discretisation moves this slow mode
  around, so τ_c is ill-conditioned there. A uniform grid would need
  N ≈ 650 at `σ = 1 K`, and N ~ 4 × 10⁴ at `σ = 6 K` with `d = 10⁻⁴`.

**Consequences:**

1. **Every finite-N spread result at `d = 10⁻³` is unresolved.** That
   includes:
   - the 18 B1 escape candidates (C38);
   - PB3's τ_c values (C40);
   - Codex's nine-box X3 eigenvalues at ±3 and ±6 K, unstable at 30 and
     300 yr;
   - Fable's nine-box finite records.

   None of these may be cited as continuum stability results. The X3
   invasion minima are nonlinear trajectories and need the same resolution
   check before B3 relies on them.
2. **The converged results so far fit the frontier.** At `σ = 1 K` and
   `d ≥ 10⁻²`, spread gives full lag robustness at a supply slope of −2.1
   to −2.8 K. That is G ≈ 0.16–0.21 against the −13.26 K control. It sits
   beside the product chemistry (0.14) on the proportional side, not in the
   escape corner.
3. **d is a physical parameter, not a numerical one.** I set it at 10⁻³
   without justification. It is habitat connectivity, and it sets how fast a
   habitat can be re-seeded by the guild it lacks. That is the same quantity
   that governs invasion memory. The continuum step must sweep d.

## The gain comparison

Codex is right that the matched methanogen-only G compares two different
worlds. Those worlds often sit on different climate segments, and the
control is often missing or flat. I will not repair it by searching harder
for controls. The thesis is about what **re-sorting of community
composition** does to the climate response. The right reference is
therefore the **same community at the same operating point with its
composition frozen**. That reference always exists wherever the community
does.

Define the following.

- **`S_c = dT*/d ln J`.** The raw community supply slope. This is the
  primary reported quantity, always defined at a qualified equilibrium.
- **`S_0`.** The same derivative with each habitat's guild ratio
  `X_A,j / X_M,j` held at its equilibrium value. Replace the two guild
  biomass equations in each habitat by their sum. Hydrogen, total biomass,
  acetate, methane and T still respond.
- **`G_loc = S_c / S_0`.** This is the static sensitivity function of the
  composition loop: 0 when re-sorting pins T exactly, 1 when re-sorting does
  nothing.
  - On a plateau segment the climate slope is zero, so `S_0 = S_c = 0`.
    Report such a point as climate-insensitive, not as a gain.
  - At a corner, use one-sided derivatives, as in the existing method.

The matched-control G stays in the tables as a secondary treatment contrast,
with its current statuses. **PB1 is restated on `G_loc` with unchanged
thresholds:** no qualified, resolved setting has `|G_loc| < 0.05` together
with `τ_c > 30 yr`. I fix this before anyone computes `G_loc`.

## B2 and B3

B2 and B3 at `σ = 0` do not depend on habitat resolution and may proceed.
B2 and B3 for `σ > 0` wait for the continuum step, at the d values it shows
matter. Changes to B3:

- Drop `σ = 1 K`.
- Drop methane_only and acetate_only. B1 makes them equivalent to fixed and
  products respectively for this purpose.
- Keep fixed and products as specified.

PB5 and PB6 are unchanged.
