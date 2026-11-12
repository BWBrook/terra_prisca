# Independent continuum characteristic check

Codex independent delegate, 12 November 2026. This is the separate stability
route requested in the [continuum specification](../../models/haze_world/continuum-habitats-spec.md).
The physical local derivatives below are assembled independently from the
uptake, biomass, acetate and methane equations. They do not import the
production weighted Jacobian or its eigenvalue routines.

## Design qualifications

Freezing each habitat's ratio is a defined local-composition intervention:
write X_A=cB, X_M=(1−c)B and retain the sum of their physical biomass flows,
including immigration. It leaves the operating point fixed, but it does not
freeze global composition: habitats with different fixed c can change their
relative total biomass. It therefore isolates within-habitat re-sorting,
not every spatial contribution to community composition.

Existence of this constrained equilibrium does not imply a finite nonzero
S_0 derivative. Its projected Jacobian can be singular; its temperature
response can vanish or change sign. Plateaus are one important zero case,
not a theorem excluding every other one. Report S_c and S_0 with conditioning,
corner, stability and denominator status before interpreting their ratio.

A panel resolving at most one unit of share logit is an equilibrium-profile
criterion. It does not alone resolve a nearly continuous slow spectrum.
The specified doubling check of both supply slopes and the critical lag
remains essential, as does separation of the local-block spectral edge from
isolated collective roots. A censored comparison establishes agreement of
classification over the tested range, not an exact infinite delay margin.

## Four-variable elimination

Let x_j=(p_j,X_Aj,X_Mj,C_j) be the local four-stock perturbation and
z=(mean X_A,mean X_M,r,T) the four global perturbations. Local blocks D_j
include the −d loss to dispersal, but exclude incoming weighted-mean cells.
At a complex frequency λ,

    (λI−D_j)x_j = B_j z,       R_j=(λI−D_j)^−1.

The first two rows of the reduced system enforce

    (mean X_A,mean X_M) = Σ_j w_j P_j R_j B_j z.

The third row is the atmospheric methane equation after the same substitution,
including direct methane-product derivatives and atmospheric loss. The final
row is

    (1+τ_T λ) T − T_Arney'(r) r = 0.

These four rows define M(λ,τ_T), with Δ=det M. Positive state-variable scales
and row scales improve conditioning without changing its zeros.

The determinant is linear in τ_T. For λ=iω,

    τ(ω) = −Δ(iω,0) / [iω cofactor_44(M(iω,0))].

Find zeros of Im τ(ω), then require positive real τ at most 10,000 years.
This is a one-dimensional frequency search, independent of the production
leading-eigenvalue scan over τ. The derivative
dλ/dτ=−(∂Δ/∂τ)/(∂Δ/∂λ) distinguishes loss from restabilisation.

The default search covers frequencies 1e-6–10/year on 361 logarithmic points;
selected qualification comparisons double that frequency resolution. This
is finite bracketing, not an interval certificate that every possible root
has been found. Initial stability is checked by the primary route and is
not inferred merely from absence of a Hopf crossing.

## Pole and residual controls

An eliminated local pole is not automatically a collective eigenvalue.
Each candidate is accepted only after checking the reduced matrix's smallest
singular value, distance from local eigenvalues, and the complete
back-substituted local/global residual. The null vector z is recovered by
SVD, and all local x_j are reconstructed through R_j B_j z. This rejects
cofactor poles or determinant sign changes that do not solve the physical
linear system. The reported local spectral edge is a separate diagnostic.

The checking module also reconstructs a dense matrix for small regression
controls only. The decisive characteristic calculation uses batched local
4×4 solves; it does not diagonalise a large dense habitat matrix.

## Regression controls

Nine tests cover all four homogeneous chemistry spectra, the independently
recovered f=.5 critical lag near 1.102760 years, product-feedback censoring,
rejection of a non-root, and an unequal-weight three-habitat physical
finite-difference check. The latter checks weighted mean injection as well
as weighted methane export, rather than relying only on an equal-grid identity.

## Homogeneous frozen-composition result

The separate projection of the independently assembled physical matrix,
followed by positive-root finite supply perturbations with the original
ratio held fixed, gives:

| Chemistry | f | S_c, K/e-fold | S_0, K/e-fold | G_loc |
|---|---:|---:|---:|---:|
| fixed | .5 | approximately zero | −51.33082 | approximately zero |
| methane_only | .5 | approximately zero | −51.32627 | approximately zero |
| products | .5 | −1.877567 | −48.554978 | 0.0386689 |
| acetate_only | .5 | −1.877743 | −48.558244 | 0.0386699 |
| products | 0 | −1.882640 | −42.096273 | 0.0447222 |

The product reference's frozen projected state is locally stable, with leading
eigenvalue about −0.000314665/year. Symmetric log-input steps 1e-4 and 1e-5
agree with its implicit S_0 to approximately 1.1e-7 and 1e-9 relative;
physical root residuals are below 1e-10 under the stated equation scaling.
The companion script records three perturbation sizes for every chemistry
at f=0 and .5, rather than relying on an unchecked inverse alone.

Both product references have |G_loc|<.05 and no crossing detected through
10,000 years under the 721-point independent frequency search. They therefore
provide tested counterexamples to PC3's newly restated numerical criterion,
without habitat-quadrature uncertainty. The physical supply slopes remain
about −1.88 K/e-fold: these are not exactly pinned climates. The changed
normalisation moves an already known partially buffering reference below the
chosen near-pinning threshold; it is not new physical regulation or proof of
stability at every possible delay. This distinction must accompany any
claim that the reference escapes the new frontier criterion.

## Selected C1 comparisons

The frozen six-setting selection includes fixed chemistry at f=.5 with
σ=1,3,6 K and d=1e-4/year; fixed f=0,σ=3,d=1e-3; fixed f=.5,σ=3,d=1e-2;
and products f=.5,σ=6,d=1e-4, all at reference supply and turnover.
All six selected states meet the static profile and subsequent doubling
criteria under this check. Fixed low-d, wide-support cases needed more than
the initial fourteen adaptive levels; the bounded caller cap was increased
to twenty-four, with the same 4,096-node maximum. The original incomplete
attempts were retained locally. The product wide-support case required the
production solver's explicit local-profile predictor before its global Newton
correction. This changed initialization, not the physical equations; hashes
of the physical flow and matrix functions agree before and after the repair.

| Chemistry | f | σ, K | d, year⁻¹ | Confirmed nodes | Independent τ_c, years | Comparison |
|---|---:|---:|---:|---:|---:|---|
| fixed | .5 | 1 | 1e-4 | 176 | 947.4345 | Full operator changes sign within ±1% |
| fixed | .5 | 3 | 1e-4 | 188 | 4781.1335 | Full operator changes sign within ±1% |
| fixed | .5 | 6 | 1e-4 | 200 | not detected through 10,000 | Full operator stable on twelve lag samples |
| fixed | 0 | 3 | 1e-3 | 156 | not detected through 10,000 | Full operator stable on twelve lag samples |
| fixed | .5 | 3 | 1e-2 | 124 | not detected through 10,000 | Full operator stable on twelve lag samples |
| products | .5 | 6 | 1e-4 | 188 | not detected through 10,000 | Full operator stable on twelve lag samples |

The finite-margin roots agree between 361 and 721 frequency points to better
than 3e-10 relative. Separately assembled full operator spectra are negative
at 0.99τ_c and positive at 1.01τ_c, bracketing the critical roots within the
specified 2% agreement. The four censored comparisons agree in classification
and sampled stability; they are not finite-margin estimates and do not prove
infinite stability. Pole-distance, reduced singular-value and back-substituted
residual diagnostics are retained for every characteristic crossing.

Two spatial examples also cross PC3's restated numerical threshold. Fixed
f=.5, σ=1, d=1e-4 gives S_c≈−2.93395, S_0≈−72.43352 and G_loc≈0.04051,
with τ_c≈947 years. Fixed f=0, σ=3, d=1e-3 gives S_c≈−4.49466,
S_0≈−92.96709 and G_loc≈0.04835, without a detected crossing through
10,000 years. These raw slopes are plainly nonzero. Relative attenuation
below the chosen 5% criterion must not be described as exact temperature
pinning.

The σ=6, low-connectivity right-censored result contradicts PC4's proposed
finite margin below 10,000 years at every σ. It does not establish that
connectivity is irrelevant everywhere: σ=1 and 3 at the same low d retain
finite margins. The original thesis-selection implication from any PC4 failure
to robustness at all connectivity values would overstate this counterexample.

Reproduce the selected inputs and independent checks from the repository root:

```sh
uv run python docs/audits/continuum-characteristic-2026-11-12.py \
  --produce-selected local/haze/continuum_characteristic \
  --output /tmp/continuum-characteristic-static.json
uv run python docs/audits/continuum-characteristic-2026-11-12.py \
  --states local/haze/continuum_characteristic/selected_states.json \
  --primary-output local/haze/continuum_characteristic/selected_primary_checks.json \
  --output /tmp/continuum-characteristic-checked.json
```

The first command produces only these six selected static cases, not the
whole C1 grid. The second adds the independent full-operator checks and
compares them with the separately reconstructed characteristic equation.
The companion committed JSON was regenerated from the final checked input
file; it pins the input bytes and the relevant source epochs. Complete local
mesh/state arrays remain under ignored `local/haze/continuum_characteristic/`.
