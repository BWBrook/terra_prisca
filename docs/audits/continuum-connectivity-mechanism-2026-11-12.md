# Why connectivity does not monotonically buy delay margin

Codex, 12 November 2026. Bounded follow-up to PC4 using four accepted
fixed-chemistry, σ=1 K, reference-supply equilibrium records. No production
equations or ensembles were changed. The
[script](continuum-connectivity-mechanism-2026-11-12.py) and
[receipt](continuum-connectivity-mechanism-2026-11-12.json) retain input/source
hashes, mode frequencies and the local sensitivity decomposition.

**The direct mixing effect is stabilising in these examples, but the
equilibrium-profile change can outweigh it.** Connectivity enters both the
outgoing/incoming exchange operator and the equilibrium distributions of
hydrogen, microbes and acetate. Replacing that combination by a single
re-seeding delay misses the second effect. This is why the PC4 monotonicity
prediction fails; it does not establish connectivity-independent robustness.

## A local calculation that separates the two effects

Let F(y,d)=0 define the instantaneous-climate equilibrium, and K(y,d,τ) its
full ecology–methane–temperature Jacobian under thermal lag τ. At a simple
Hopf crossing, let λ=iω and let l/r be the left/right eigenvectors. Then

    dy*/d ln d = −[∂F/∂y]⁻¹ ∂F/∂ ln d
    ∂λ/∂a = lᴴ (∂K/∂a) r / (lᴴr)
    d ln τ_c/d ln d = −Re(dλ/d ln d) / Re(∂λ/∂ ln τ).

The numerator splits into:

- **Explicit dispersal:** ∂K/∂ln d at the fixed equilibrium stocks. This is
  exactly d times the weighted mixing operator in the two biomass blocks.
- **Equilibrium-profile shift:** the derivative of K along dy*/dln d,
  holding d fixed when evaluating that derivative. It includes local resource,
  biomass and acetate changes, plus the small atmospheric/climate shift.

The second term is a tangent derivative, not an experiment in which an
off-equilibrium community is assigned an ecological stability interpretation.
Only the sum is the derivative along the equilibrated branch. Central tangent
steps 10⁻³, 5×10⁻⁴ and 2.5×10⁻⁴ agree to much better than the quoted precision.
The equilibrium derivative uses the full weighted static Jacobian and the
actual migration forcing, without a population denominator floor.

| f | d, yr⁻¹ | τ_c, yr | Explicit contribution to d ln τ_c/d ln d | Profile-shift contribution | Total |
|---:|---:|---:|---:|---:|---:|
| 0 | 10⁻⁴ | 581.48 | +0.145 | −0.474 | −0.329 |
| 0 | 10⁻³ | 331.43 | +0.610 | −0.552 | +0.059 |
| 0.5 | 10⁻⁴ | 947.43 | +0.200 | −0.542 | −0.343 |
| 0.5 | 10⁻³ | 842.24 | +1.453 | −0.894 | +0.558 |

Positive values mean that locally increasing connectivity raises the critical
lag. At the lower connectivity, redistribution of the equilibrium profile
lowers the margin more strongly than explicit mixing raises it. At the higher
connectivity, the explicit mixing effect wins. Thus the local derivative itself
changes sign: these endpoints are consistent with a nonmonotonic margin, not
with a uniform improvement or uniform deterioration.

For f=.5, one additional doubling of the mixed-zone panels confirms this
diagnosis. At d=10⁻⁴, nodes increase from 176 to 296 and τ_c changes from
947.430 to 947.400 yr; the total derivative is −0.34272 versus −0.34273.
At d=10⁻³, nodes increase from 144 to 256 and τ_c changes from 842.2408 to
842.2397 yr; the derivative is +0.558491 versus +0.558492. These are selected
resolution checks of the diagnostic, not a new parameter map.

## What changes in the coupled mode

The f=.5 crossing mode has period about 6,468 yr at d=10⁻⁴ and 3,414 yr at
d=10⁻³. The mode therefore changes along with its delay margin. The increase
in connectivity is not simply shortening one otherwise fixed delay in an
unchanged loop.

Global equilibrium quantities barely move: the local dT*/dln d is about
−0.00024 K at the lower d and −0.00153 K at the higher d. Relative mean-biomass
derivatives are only of order 10⁻⁵–10⁻⁴ per e-fold. Nevertheless, the narrow
local transition between guilds broadens with connectivity, changing which
habitats contribute to the collective response and how their local growth,
resource and product responses enter that mode. The profile contribution in
the table demonstrates the resulting retuning. It does not uniquely attribute
that contribution to one biochemical derivative or one geographic location.

For f=0 there is an additional complication: the two endpoints lie on opposite
sides of an Arney vertex. Their global temperatures are 282.00944 and
282.00447 K, bracketing the digitised vertex at 282.005 K. The local climate
slope changes from −599.934 to −721.258 K per methane ratio. This can further
change the finite connectivity comparison. It cannot explain the whole PC4
failure: the f=.5 counterexample stays on the same climate segment and has
the same explicit-versus-profile competition. The local derivatives above
remain on their own side of the vertex; they do not integrate through its
nondifferentiable point.

## Scope and interpretation

The weighted mixing operator alone dissipates biomass heterogeneity. That
fact says nothing by itself about monotonic movement of a coupled biological
climate system's delay margin as its equilibrium also changes. In the selected
examples its direct modal effect really is stabilising; the missing mechanism
in PC4 is the competing equilibrium-profile response.

The calculation is local at four fixed-chemistry states, with an extra mesh
check for the two f=.5 points. It is not a global bifurcation continuation,
an identification of every intervening mode switch, or an Archean estimate of
connectivity. In particular, the sign at the high-d endpoint does not undo the
observed decrease between endpoints, and the two local derivatives do not
locate a unique intermediate minimum.

**PC4's failure should not trigger the specification's inference that spatial
regulation is robust whatever the connectivity.** The observed margins remain
finite at the lower rates and change with d. Monotonicity is refuted;
connectivity dependence is retained. Whether the same parameter also protects
through invasions is a separate question for the nonlinear runs and memory
mechanisms, rather than a consequence of this local delay-margin calculation.
