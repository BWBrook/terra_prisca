# Independent audit of the two-habitat refuge design

Codex (GPT-6), 10 November 2026. Reviews the specification in `5e2a262` before
the full invasion grid. The model is a useful, implementable experiment, and
the measured-physiology partition gate is **open**. Several predictions need
more restricted interpretations; they are not numerical acceptance criteria.

[Independent checker](check_refuge_design.py) and
[numeric results and source hashes](refuge_design_check.json):

```sh
uv run python models/haze_world/review/check_refuge_design.py
```

The checker reconstructs the nine-stock RHS from guild kinetics, yields,
maintenance and budget definitions. It does not call the new refuge RHS, run
trajectories or use the new equilibrium solver. Shared source primitives and
the published climate interpolation remain common inputs.

## Conservation and dimensional mapping

Let `a=w_c`, `b=w_w`, with `a+b=1`. The specified exchange terms conserve
area-weighted concentrations:

    a d b (X_w-X_c) + b d a (X_c-X_w) = 0.

This also conserves weighted cell numbers because habitat volume per area and
cell mass are common. The cancellation would require different concentration
coefficients if those assumptions changed. Each exchange term has units
gDW/L/year; local physiological rates must be converted from hours to years.

The total H₂-equivalent inventory is

    sum_j w_j [kappa p_j + sum_i a_i X_ij + 4 A_j] + 4 r/Gamma.

Its external flows are weighted donor input minus hydrogen outlet, acetate
export and biomass export, plus the single atmospheric abiotic source and
methane loss. Atmospheric inventory/source/loss are counted once. Dispersal
adds no export term when the allocation coefficients `a_i` are common across
patches, as in the reference model. Independent perturbed-state checks close
this balance within 7×10⁻¹⁹ mol H₂/L/year.

## What constitutes a partition equilibrium

At `d=0`, a positive A-only cold patch has `p_c=R*_A(T_c)` and a positive
M-only warm patch has `p_w=R*_M(T_w)`. Each also needs `R*` below its lifeless
pressure, positive captured supply, and its own acetate balance. The common
methane equation must then vanish at the resulting global climate.

The inequalities

    R*_A(T_c) < R*_M(T_c),   R*_M(T_w) < R*_A(T_w)

make the missing competitors locally decline. In the chosen fixed-product
reference these are equivalent to `T_c<T_sw<T_w`, where
`T_sw=281.534822805 K`. They are conditions for a protected partition, rather
than sufficient algebraic existence conditions: the scalar methane balance
must also have a root. Boundary equilibria can exist while invadable. Full
climate/community stability additionally needs the nine-dimensional spectrum.

At any `d>0` and nonzero patch weights, an exact A-only/M-only spatial partition
cannot be stationary: export from each occupied patch immediately seeds its
other patch. It becomes a source/sink equilibrium. For a strongly declining
sink, leading-order concentration is

    X_sink ≈ d w_source X_source / |lambda_sink|.

The source-area coefficient matters for small refuges. At finite dispersal a
patch containing both guilds need not satisfy either guild's zero-growth
condition; growth balances net export/import. Consequently, exact local
temperature pinning is a `d=0` fixed-product special case, not an automatic
classification of every locally mixed finite-d state.

## The measured-domain gate is open

The coarse invasion grid does not locate every measured partition. Screening
`w_w=0.01,0.02,...,0.99`, `Delta=0.5,1,...,30 K`, with exact refinement of
detected scalar roots, found 93 protected measured partitions at `f=0` and 222
at `f=0.5`. Only zero and two, respectively, occur on the proposed coarse
invasion grid. These are detected grid roots, not an exhaustive root count;
narrow contacts or branches can evade a finite bracket grid.

Two explicit examples settle the stopping question without relying on absence
claims:

| f | Warm area | Contrast | Global T | Cold T | Warm T | Largest real eigenvalue |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.74 | 1 K | 281.792641 K | 281.052641 K | 282.052641 K | −2.15×10⁻⁴ yr⁻¹ |
| 0.5 | 0.51 | 8 K | 282.002304 K | 277.922304 K | 285.922304 K | −1.45×10⁻⁴ yr⁻¹ |

Both are locally stable under the independently constructed full nine-state
Jacobian. Continuing them to `d=0.001/year` gives positive source/sink stocks,
scaled equilibrium residuals below 1.4×10⁻¹⁴, and stable leading eigenvalues
about −2.59×10⁻⁴ and −1.45×10⁻⁴ yr⁻¹. The measured partition map therefore does
not trigger the specification's early stopping rule. A coarse-grid null at
`f=0` must not be described as nonexistence.

An equilibrium inside the measured window does not establish that its
conditional pure starts or invasion trajectories stay there. Existing
physiology has a named continuation down to 273 K, but no definition below
273 K or above 303.15 K. For example, retaining a 273.5 K global mean while
placing a 10% warm patch 9 K above it necessarily puts the bulk patch near
272.5 K. Flagging a temperature does not define the missing physiology. Such
configurations need an unsupported-domain status unless a separately named
and justified continuation is introduced; temperature clipping changes the
stated model.

## P3 and the high-recycling measured range

The dense scan detected no protected measured pure partition at `f=0.9`.
There is a stronger `d=0` bound for the reference physiology. At local
single-guild break-even states, express methane delivery as the equilibrium
ratio it would sustain over the whole area, before multiplication by `f` for
acetogens. Conservative endpoint enclosures over temperature subintervals
give

    A in [277.15 K,T_sw]: ratio-equivalent source >= 0.238923816,
    M in [T_sw,303.15 K]: ratio-equivalent source >= 0.250553024.

Within source interpolation segments the capacities and half-saturation
pressures are linear, while maintenance and reference thresholds are
monotone. The checker encloses required uptake, break-even pressure, capture
and catabolic allocation on 0.025 K subintervals including every source knot;
it does not simply assume that sampled source minima are exact.

Any protected pure partition at `f=0.9` would therefore have

    r >= min(0.9*0.238923816,0.250553024) + r_abiotic
      = 0.215575206.

The adopted climate curve has `T(r) <= 274.002 K` throughout that ratio range.
Both measured patches would instead imply their weighted mean is at least
277.15 K: a contradiction. Thus a **zero-dispersal pure protected partition**
at `f=0.9` cannot lie wholly inside measured physiology. This is not a theorem
excluding all finite-d coexistence, because migration modifies the local
break-even conditions. Finite-d states must be checked directly. In particular,
a successful warm-refuge calculation should retain its cold-domain flag.

## Thresholds, invasion and the large-d limit

The preregistered offsets are useful first-order hypotheses. They use the
single-habitat starting climates, while actual two-habitat pure equilibria
have different capture, local maintenance and atmospheric balance. They cannot
serve as exact bounds on transient survival. Persistence depends on the
time-integrated growth and exchange history as well as cell counts.

For a rare guild in a temporarily fixed environment, the relevant matrix is

    [[lambda_c-d w_w, d w_w],
     [d w_c, lambda_w-d w_c]].

Its dominant eigenvalue, rather than the sign of one patch growth rate alone,
determines invasion. Its determinant is
`lambda_c lambda_w - d(w_c lambda_c+w_w lambda_w)`. A favorable patch can fail
to support the total lineage if emigration losses are too large.

As `d` tends to infinity, exchange equalizes concentrations, but leaves the
patch temperatures, local hydrogen and local acetate distinct. The slow
population equations use `sum_j w_j mu_i(p_j,T_j,products_j)`, which generally
differs from growth evaluated at mean conditions. Even with identical 30 Pa
hydrogen in two equally weighted patches at 285 and 295 K, average annual
growth is (−3.41964, 3.11796) for (A,M), versus (−2.73642, 3.45270) evaluated
at 290 K. This explicit counterexample refutes the general claim that rapid
cell mixing recovers a single habitat at the area-mean temperature. The
`Delta=0` symmetric limit remains a valid code requirement.

Similarly, mutual invasibility of the two pure equilibria does not prove a
unique global mixed attractor for a system containing resource, acetate and
climate dynamics. It establishes boundary instability in the relevant invasion
directions. Cycles, multiple interior equilibria and other basins require
separate analysis. The scoping Pi also uses the initial invader growth as a
proxy for the eventual resident decline; it is a heuristic, not a rigorous
survival bound.

## Continuous minimum reporting

The minimum of an actual trajectory depends on its equations, immigration or
dispersal, and census interventions. Once a population is removed, its
post-removal minimum is zero (log minus infinity). An uncensored continuum
counterfactual is a separate run, whose bottleneck can be useful but must be
named. It does not make censored minima independent of census timing.

Numerical RHS callback trials must not be used as trajectory minima. Implicit
solvers evaluate unphysical trial states during rejected steps/Newton
iterations. Use accepted-step or dense-interpolant extrema and state their
sampling/refinement scope; census-only minima remain sampled diagnostics.
