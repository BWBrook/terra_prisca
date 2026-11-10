# Refuge coupling: implementation boundaries

Codex (GPT-6), 10 November 2026. These choices precede the invasion matrix.
The original predictions and 432-point design remain in
[Claude's specification](refuge-coupling-spec.md), commit `5e2a262`.

The [independent design audit](review/refuge-design-review.md) finds measured-
temperature partition equilibria, so the equilibrium stopping gate is open.
It also identifies several distinctions needed to test the specified model:

- Strict switch inequalities concern local invasion protection, not algebraic
  existence or the shared atmospheric methane balance. Positive exchange
  produces source/sink communities rather than exact zero stocks in one patch.
- Fast exchange homogenizes biomass concentrations while temperatures and
  resource pressures remain local. Its limit averages local growth, rather
  than evaluating growth at the mean temperature.
- Mutual invasibility of boundary states does not establish a unique global
  attractor in this climate/acetate dynamical system.
- A continuous minimum of a censored trajectory depends on its trajectory
  and censoring. Pre-removal segment minima, post-removal zeros and separately
  uncensored counterfactuals have distinct meanings. Rejected solver trials
  are excluded from trajectory minima.

No extra biological temperature extrapolation is introduced. The reference
biology has measurements at 277.15–303.15 K and a named cold continuation down
to 273 K. Below 273 K and above 303.15 K its rates are undefined. A missing
supported conditional start or a trajectory exiting that domain is reported
as unsupported physiology, not biological extinction or a settled endpoint.
Zero-area habitats are inactive and impose no temperature constraint.

Conditional starts require the resident in every positive-area patch and local
stability with the competing guild disabled. All supported candidates are
retained in the equilibrium output. If multiple such starts exist, the largest
methane ratio is selected consistently and the ambiguity is recorded; it is
the declared hazy-branch initialization, not a uniqueness claim.

The 432 main attempts keep the specified grid unchanged. Supplemental points
test small warm refuges (warm fraction 0.05 at 8.4/8.6/9 K, or 0.01 at 8.8 K), measured
partition examples (0.74/1 K at f=0 and 0.51/8 K at f=0.5), and a small cold
refuge (0.99/15 K at f=0.5). They are chosen from the equilibrium and domain
audit before the full matrix, not claimed as wholly prespecified. A 1,000-year
numerical smoke at warm fraction 0.05 and contrast 8.6 K preceded the batch freeze.
Seed-origin, product-activity and annual-census comparisons use these points.
Unsupported starts remain visible in those subsets as well.

The identical-habitat trajectory limit is tested without removals. A floor of
one cell in each patch differs from one global cell; the finite zero-contrast
slice tests endpoint agreement and reports census-event differences explicitly.

Numerical qualification caught two defects before the full matrix. Linear
acetate inventories developed small negative tails; positive acetate now uses
a positive coordinate, with an exact-zero start changing coordinates only at
its first positive accepted state. No inventory is seeded. Retained log
inventories preserve production and loss below physical floating-point range.
A full-duration smoke then found a dense polynomial reconstructing an accepted
zero allocation as −9.8×10⁻¹⁷. Boundary evaluations now use the saved accepted
state; genuine interior violations still fail. Regression tests and an
[independent Radau comparison](review/check_refuge_trajectory.py) cover these
numerical choices. Neither repair changes the physical right-hand side.
