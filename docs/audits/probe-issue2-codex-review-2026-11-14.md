# Issue 2 review: imposed warming and sunlight

Codex (GPT-6), 14 November 2026. Reviews `9b5335e`/`2900a49` and pressure-test
post 3416. Three independent bounded reviews covered derivatives/injection,
window/stability, and the primary sources. I integrated them and added a
counterexample using the existing methane-feedback variant. Issue 1 remains
closed. No production model, manuscript, figure or original probe output
changed, and no new experimental stage was run.

**Verdict:** there is a useful response-to-imposed-warming result. Accept it
with the corrected scope below. Do not yet describe it as a calibrated test
against sunlight, a 16–20% solar working window, or a stronger normalized
defence against sunlight than against supply. Keep the adopted main message.

## 1. The local relation passes an independent check

For a regular ecological output closure M(P,T), with linear methane removal
and no direct methane-product dependence in that closure, define E and G
from the **total atmospheric methane source**, including the abiotic term.
Then the stated relations hold locally on the cooling branch:

`S = -k E/(1+k G)`, and `dT/dF = 1/(1+k G) = |S|/(k E)`.

The producer does not independently measure E: `relation` back-solves
`E=-S/(k*dT/dF)` from the proposed identity. Its table alone therefore cannot
validate the identity or independently identify a chemical mechanism.

An independent clamped-actual-temperature Jacobian calculation now supplies
that missing check:

| State | E_total at fixed T | Linear dT/dF | Probe finite difference |
|---|---:|---:|---:|
| D1, f=0, 30-year point | 1.447450655 | 0.001362977646 | 0.001362979587 |
| Spread, sigma=1 K | 1.075509304 | 0.019388275894 | 0.019388267548 |

A separate D1 difference at +/-0.03 K gives 0.001362977820. These support
the quoted 0.14% and 1.9% responses. The sigma=3 reference finite difference
of 5.50% is also consistent with the archived calculation.

The source definition matters. Abiotic methane contributes about 0.279% at
these points. Biological-only E is 1.451496185 and 1.078515616, respectively.
Use total source for the displayed linear-loss identity, or include the
source-share correction. The nearly fixed outlet explains why E exceeds
one approximately; the residual effect of assimilation/composition was not
separated experimentally. The acetate interpretation is plausible and
consistent with the independently measured E, rather than proved merely by
the back-calculated value.

The alias injection and relevant cache clearing check out. The independent
injection checks reproduce the recorded shifts and unchanged slopes. This
qualifies the implemented **rigid vertical temperature shift**, not a solar
photochemistry calculation.

## 2. The two disturbances have the same normalized local gain

At the same reduced operating point, the open-loop supply response is
`-k E`, whereas the direct imposed-temperature response is one. Dividing
each closed-loop response by its corresponding open-loop response gives
the same `H=1/(1+kG)`. The independent calculations agree to numerical
precision for both checked states.

Thus "loose against supply, tight against sunlight" compares unlike units
and forcing magnitudes. Small dT/dF is real buffering; it does not establish
stronger normalized regulation of one disturbance. This normalization also
differs from the paper's frozen-composition `G_loc=S/S0` and must not be
silently substituted for it.

## 3. Supply pinning does not universally imply forcing pinning

Fixed-product exact coexistence is pinned by equality of R-star. Its
fixed-temperature ecological problem is singular: different guild shares
can produce different methane outputs at the same P and T. Accordingly,
M(P,T) is not a single-valued regular closure there. Prove its pinning
separately; do not obtain it by dividing two zero derivatives.

More importantly, the paper's exact states include **methane-only product
feedback**, which the probe's two exact jobs do not test. An accepted example
at f=0.5/P=0.30 has:

- supply sensitivity S=-1.64e-13 K per e-fold;
- imposed-warming sensitivity 0.000191649576 by +/-0.1-K differences;
- independent linear sensitivity 0.000191649553.

It is effectively insensitive, but is not exactly pinned against F.
R-star equality now depends on methane as well as temperature. Restrict
"exact states do not move" to the fixed-product states tested, rather than
all states classified exact against hydrogen supply.

If a regular output closure explicitly depends on r, the general differential
has methane-loss elasticity alpha and direct source elasticity h:

`S = -kE/(alpha-h+kG)`,
`dT/dF = (alpha-h)/(alpha-h+kG)`.

Alternatively one can eliminate r into a regular clamped-temperature closure
and redefine its elasticities. Either route requires the definitions and
regularity conditions; zero S by itself is insufficient.

The proposed abstract's "at most 6%" also excludes a tested state. The
sigma=3/P=0.24 result is **8.2615%**. Either specify the reference examples
when quoting 0.14–5.5%, or use the full tested graded range, about 0.14–8.3%.

## 4. The Kelvin window is a feasibility interval, not inclusive stability

For case B, fixed products, reference supply and the two recycling fractions,
the exact geometric limits are:

`F_min = -15.473177194918 K`, `F_max = 8.144822805082 K`.

The probe's existence brackets contain these values. Both guilds remain
positive at the corners. Stable zero-lag interior samples support the
reported cooling-branch behaviour. However, the corners are nonsmooth:
their adjoining warming-side matrices have **real positive eigenvalues**:

| Corner | f=0 | f=0.5 |
|---|---:|---:|
| Cold-forcing end | 0.0153723/year | 0.00982784/year |
| Warm-forcing end | 0.0123120/year | 0.0108612/year |

The associated real eigenvectors have nonzero methane components, so their
sign can be chosen to enter the warming side. One cannot label these states
two-sided stable by using only their cooling-side spectra. Report
coexistence at the boundary and stable sampled interiors, not "stability
holds right to both ends".

Also, literal F=-15.5 K is already outside this interval: the peak misses
T-star by 0.02682 K. It is acceptable as rounded descriptive prose but not
as the coordinate of a computed state in the stability table.

## 5. Response time is state-dependent across the window

The sampled F<=6 K margins differ from reference by at most 5.96% and
6.52%, supporting the stated 7% summary **for those samples**. Near the warm
end they reach 2.093 and 3.598 years, or 14.03 and 3.26 times reference.
The verdict's "unchanged across the window" is false. These remain short
margins, but that is a different claim.

Fixed-state invariance holds for the **full thermal state including actual
temperature**: adding a constant to the thermal equation changes no state
derivative. The probe's stored y omits temperature; holding only that y
fixed while changing F changes the implied temperature and biology. State
which meaning is intended. Stability at a given equilibrium is independent
of which infinitesimal input is used to disturb it; new equilibria and
changed climate slopes can have different margins.

The piecewise curve changes slopes discontinuously, so describe sampled
flattening rather than implying a smooth approach to zero slope.

## 6. Cross-case feasibility is useful; the absence and scaling need narrowing

Cases A and C provide fixed-product coexistence examples at T-star on the
extracted cooling curves. Their differing slopes demonstrate why the actual
climate curve matters. A 4.5-fold change in k alone does **not** establish
a 4.5-fold graded residual: S, E and G can change too, and no cross-case
graded comparison was computed. Case C's stored cooling-branch margins span
1.261–7.196 years, not 1.3–1.4 years over the scan.

Case D cannot reach T-star on its **extracted** curve, but "no mixed state
at any supply" is false for the implemented climate. Its assumed bridge
starts at 283 K. A direct root/budget calculation finds an accepted stable
coexistence state at:

`P=0.02332820953`, `r=0.005272191843`, `T=281.534822805 K`.

Its positive-mixture supply interval is 0.02302879947–0.02362761958, below
the producer's 0.05–2.0 scan. The scaled RHS is 4.15e-15, per-capita residual
1.71e-14/year, and leading eigenvalue real part -9.23e-5/year. This is a
counterexample about the **assumed bridge**, not support for a new physical
Archean state. Restrict absence to the extracted curve or the searched range.

## 7. The solar conversions supply scale, not a tested sunlight window

[Arney et al. (2017), table 3](https://arxiv.org/pdf/1702.02994) supports the
272/299 K and 278/342 W/m2 values. Its secant is 1.1728 K per 1% of the
**young-Sun** flux, or 1.4428 K per 1% of modern flux. Keep the denominator
explicit. It joins two case-A states at one methane ratio, with spectrum
and haze changing together (section 3.3.1, pp.8–10). It is not case B's
fixed-r solar derivative, nor a calibration of a translated entire curve.

The AR6 arithmetic produces 1.4431 K/% under the chosen assumptions, but
two source transfers prevent calling it an AR6 solar sensitivity:

- The 0.32 in [Arney (2016)](https://arxiv.org/abs/1610.04515v1), accepted
  manuscript p.24, is prescribed **surface albedo**, including a cloud proxy.
  TOA absorbed forcing requires planetary/Bond albedo. The 2017 table lists
  planetary values of 0.238 and 0.216.
- [AR6 chapter 7](https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-7/)
  gives ECS=3 K and likely 2.5–4 K; 3.93 W/m2 is doubled-CO2 **effective**
  forcing. Multiplying its reciprocal feedback by instantaneous absorbed
  sunlight assumes away forcing adjustments/efficacy. The actual historical
  solar formula has a factor 0.72 and planetary albedo 0.29
  ([supplement pp.3,6](https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_Chapter07_SM.pdf)).
  Applied literally it would give 1.0848 K/%, but modern UV/ozone adjustments
  are themselves not an Archean calibration.

Dividing 23.618 K by the two chosen central conversions yields about 16–20%
of young-Sun flux. These are scenario-scale analogies, not bounds on a
physical solar window; the stated ECS range alone would broaden the
simplified arithmetic to roughly 12–20%. Solar change also alters haze,
climate shape and potentially methane loss. The primary result must remain
in **kelvin of imposed vertical shift**. Omit the percent window from the
abstract; if retained in discussion, label it a rough illustrative scale
after correcting albedo/forcing definitions.

[Gough (1981), p.28 equation 1](https://articles.adsabs.harvard.edu/pdf/1981SoPh...74...21G)
supports the luminosity-age arithmetic. It does not establish billion-year
regulation: unchanged physiology, supply and a rigid climate map over that
time are untested. Do not turn the schematic conversion into a persistence
duration.

## 8. Recommended paper treatment and disposition

- Add a section about **response to imposed climate warming**, rather than
  "Sunlight acts through the same loop". Explain that it is a controlled
  surrogate relevant to the sunlight motivation, not its complete test.
- Retain the independently checked local identity, with total-source and
  regularity definitions. Prove fixed-product pinning separately. Qualify
  direct methane-feedback cases.
- Keep the Kelvin feasibility window and sampled stability results, with
  the endpoint and margin corrections above. State that the probe did not
  sweep graded-state margins in F.
- Remove the normalized "loose versus tight" comparison and the abstract's
  solar percentage claim. Fix the 6% subset error.
- Proposed C62–C64 should respectively cover the qualified local relation,
  the fixed-product Kelvin feasibility window with sampled margins, and
  extracted-curve cross-case feasibility. Do not give C64 an all-supply D
  absence claim.
- Leave the adopted main message unchanged. No new experiment or matched
  solar-grid project is required to report these narrower findings. A real
  solar calibration would be a separate proposed stage under Barry's gate.

The scripts and JSON receipts beside this review are bounded checks of local
derivatives, selected roots, corner spectra and the archived summaries:

```sh
uv run python docs/audits/probe-issue2-local-check-2026-11-14.py --output /tmp/terra-issue2-local.json
uv run python docs/audits/probe-issue2-window-check-2026-11-14.py --output /tmp/terra-issue2-window.json
uv run python docs/audits/probe-issue2-scope-check-2026-11-14.py --output /tmp/terra-issue2-scope.json
```

All pass. The producer's 95-second grid was not rerun, and no new transient,
lag or solar grid was computed. Its reproduction wording should also say
agreement within tolerance: the off-reference P=0.42 comparison differs by
3.30e-5 K in T and 1.33% in S0, rather than bit for bit. The original probe
and its outputs remain intact for reconciliation.
