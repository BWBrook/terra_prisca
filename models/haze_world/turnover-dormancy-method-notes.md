# Turnover and dormancy: methods and numerical provenance

Codex (GPT-6), 10–11 November 2026. The original
[specification](turnover-dormancy-spec.md) remains the prediction record.

- A thermal `R*` crossing, a reachable mixed climate and a stable mixed
  climate are distinct. The preview's 2.44×10⁻⁴/hour condition concerns a
  climate-regime boundary, not disappearance of every physiological crossing.
  The full inventory retains narrow regimes between grid points, including
  the small final upturn in the digitized climate curve. That feature is
  conditional on the extraction and cold continuation, not a new empirical
  finding about Earth.
- The T1 basin gate tests every original bistable grid point and additional
  root-delimited narrow regimes. Landing in either stable attractor refutes
  a proposed basin assignment if necessary; it does not contradict local
  stability just because the expected attractor was different. Divergence
  after a small perturbation of a purported stable state does require
  resolution. Radiative and physiological corners require segment-aware or
  one-sided stability calculations.
- At high turnover, a habitat can support an imported resident even when it
  cannot sustain that guild in isolation. T2 starts therefore include a
  positive source–sink continuation/refinement search. Search failure is not
  a proof that life is impossible. The same highest-r stable conditional
  resident policy is retained, with candidate ambiguity and residuals visible.
- Dormancy preserves well-mixed stationary locations for positive dormant
  mortality: a resident must have `g=L` and `Z=0`. This is not a theorem about
  spatial equilibria, stability or basins. Migration balances unequal local
  growth in refuges, where dormancy can remain active. We test KD1 rather
  than forcing its spatial claim. The equations are unchanged.
- Well-mixed dormancy starts embed the reference resident with `Z=0`.
  Spatial starts solve the resident's own stationary dormant bank, eliminating
  `Z` through its linear balance before refining active stocks. An invader
  starts in the active state at the existing 10⁻¹² gDW/L dose, with no dormant
  invader. This avoids confounding an unprepared resident bank with invasion.
- The demographic classes concern each removed guild's first bottleneck.
  Later windows and any window requiring another guild's improbable recovery
  remain conditional. A global-guild probability does not establish local
  patch-occupancy robustness; local census events are linked explicitly.
  We do not multiply guild probabilities into community endpoint forecasts.
- KT4's `N50 = ln(2) δ W` is an asymptotic Gaussian approximation. `W` is
  the local curvature width, not the full unfavorable interval. Monotone or
  terminal declines have no interior Gaussian width and are reported as
  nonapplicable. Multiple habitats or active/dormant stages need not reduce
  to the scalar formula. The 10% prediction remains an empirical test for
  its defined interior first minima, not an enforced software invariant.
- Refuges export cells and methane. A bistable isolated bulk need not remain
  bistable after a refuge is added; KT2/KT3 are numerical predictions for
  the coupled model. Turnover and dormancy remain assumptions rather than
  Archean calibrations.

## Dormancy switching law

Before the full T3 grid, clipped-linear switching caused excessive numerical
work near break-even growth in pure-resident pilots. The specification
explicitly permits a documented smooth ramp. T3 therefore uses
`c(x)=x²(3−2x)` for `0<x<1`, with zero below and one above. This has zero
derivative at both ends and preserves the prescribed direction of dormancy
entry and waking. It is a declared response-law choice, not a threshold on
small growth rates or a seed inserted into an empty pool.

A matched 100-year linear/cubic control at `f=0`, no refuges,
`epsilon=0.003`, acetogens invading methanogens, measures the entry-law
difference. It does not establish equal long-term outcomes under both laws.
The full-grid conclusions remain conditional on the cubic switching law;
the unmodified linear ramp remains a named control rather than an implicit
fallback.

## First-window scoring

Before scoring T2/T3, define a guild's first window as its earliest globally
rare excursion below 10¹⁶ cells, anchored to its first sampled minimum and
ending no later than the next sampled recovery peak. Lower that boundary
by decades around the same minimum until both local and global hydrogen
uptake shares remain below 10⁻¹⁰ throughout the window. If the original
minimum cannot qualify, retain its nonrare diagnostic instead of skipping
to a later dip. This additional anchoring follows independent review of the
first implementation, before result scoring. It avoids choosing a threshold
from a later, biologically impossible recovery. An excursion open at the
trajectory horizon is terminal and keeps
its finite horizon explicit. A trajectory that never qualifies receives a
nonrare, recorded-environment diagnostic, not a claim that the guild had
negligible environmental effects.

Each local census removal links to this guild-level diagnostic; survival
anywhere is different from presence in a particular patch. Flag a window
that overlaps another guild's unlikely first window, and separately record
whether it starts after that guild's first sampled subcell count. These are
conditioning warnings, not exact extinction times. Do not multiply guild
probabilities into a community forecast. Annual uncensored prefixes are
required for cases with a census removal or any dense-flow minimum below
10¹⁶ cells, even if a ten-year census missed the dip. Evaluate the local
Gaussian estimate only at rare, resolved interior first minima with positive
curvature; that candidate check does not establish a scalar reduction or a
Gaussian shape. Check rate-grid and horizon effects for borderline classes.

## Uncensored numerical trials

The full uncensored T3 experiment exposed failures absent from the short
controls: squared stage-allocation trials overflowed, and nonfinite dense
coefficients then reached the minimum finder. The affected prefixes are
unqualified; their failure ledger is retained outside Git. The source-frozen
census experiment remains separate.

A named trial-integration variant is qualified through the first loss window
of `dormancy_0000`; its longer conditional tail remains unqualified. The
[review](review/dormancy-trial-integration-review-2026-11-11.md) records both
the successful and bounded failed controls. It reuses the frozen
physical equations, census rule and accepted-flow bookkeeping. Invalid
numerical trials must return to the last valid coordinates, and any exact
change from a positive coordinate to a linear coordinate must preserve the
represented stocks. No population seed, clipping or chemical inventory reset
is authorized by this numerical amendment. Its final controls and source
hashes accompany the qualified prefix protocol.

Prefix horizons follow the first-window question. A closed first window can
be scored immediately. A terminal survival probability below 0.5 is already
a one-sided loss bound for every later horizon; a protected terminal window
requires extension. This does not turn later continuum recovery into a real
finite population. Prefix horizons and their selected receipt fingerprints
remain explicit, rather than requiring an arbitrary long ghost-conditioned
tail after the first loss is decisive.

## Supplemental threshold refinements

All 128 planned T3 cases retain their declared and recorded 100,000-year
minimum horizon. Additional epsilon settings answer a narrower question:
where the displaced resident's first-window survival crosses one half.
An independent review permits shorter paired census and annual uncensored
records for those settings. Their declared and actual horizons must agree,
and their first locally linear rare resident window must close strictly
inside that horizon. A short unresolved, terminal or nonrare record cannot
supply an exact crossing.

Each supplemental ID identifies a planned parent. The scientific design
must match that parent except for epsilon and ID; numerical tolerance,
maximum step and horizon remain explicit controls. These records enter only
KD3/KD4, never the planned endpoint pairs, the reference endpoint comparisons
or long-horizon macroscopic-protection claims. Completed longer refinements
remain available. This qualification changes neither the planned experiment
nor a probability, extinction threshold or stationarity criterion.

## Qualified switching matrix and chemical charts

The later [Jacobian variant](review/dormancy-jacobian-review-2026-11-11.md)
retains the physical function, census and error tolerances. It differentiates
switching and allocation algebraically, avoiding a false waking source from
finite perturbations across the zero-growth boundary. A producer's linear
allocation and tiny acetate pool are conditioned together, preserving every
decoded stock and inventory exactly. Final original first-window controls and
a formal 100,000-year census pilot qualify this numerical source.

The [platform audit](review/check_dormancy_platform_precision.json) qualifies
that result: microscopic dormant-bank stationarity is not reproducible on a
one-cell comparison scale at the adopted tolerance, although the matched
climate and community are. Preserve those strict flags and distinguish them
from the independently controlled, macroscopic spatial cycles. No endpoint
or probability threshold is changed by this numerical qualification.

## Numerical provenance and source epochs

The following records describe the completed original build. The physical
producer files and their earlier outputs remain frozen during the subsequent
review closure.

The implementation is
[`dormancy.py`](../../src/terra_prisca/haze_world/dormancy.py), with the
positive-coordinate integration in
[`dormancy_integration.py`](../../src/terra_prisca/haze_world/dormancy_integration.py).
The current qualified numerical route uses
[`dormancy_face_integration.py`](../../src/terra_prisca/haze_world/dormancy_face_integration.py),
with the frozen accepted-step driver and physical equations. It modifies
only approximate Newton couplings for a present linear allocation whose
coordinate and returned floating-point rate are both exactly zero. A retained
incoming log source can still exist below floating range; this approximation
does not remove that source or establish biological extinction. The
[review](review/dormancy-face-review-2026-11-11.md) and
[qualification](review/dormancy-face-qualification-2026-11-11.json) distinguish
completed numerical flow from strict endpoint convergence. Earlier qualified
native, Jacobian, chemical and stage receipts retain their own source epochs.
The active model and its frozen earlier outputs are unchanged.

The Face helper is frozen at SHA-256
`6a758528247493428459d250a0cd000ae678c9e59c05a09947f94628ed1672ce`.
Its [qualification](review/dormancy-face-qualification-2026-11-11.json)
includes the completed original-start 100,000-year case 0085 flow, whose strict
all-stock settling label remains unresolved. Its runner
records solver `analytic_dormancy_zero_face_newton`, architecture, operating
system and an exact nine-file numerical extension to the unchanged canonical
physical source graph. Its frozen trial, switching-Jacobian, progress,
chemical and accepted-stage dependencies remain explicit in that graph.

Earlier variants retain their separate
[trial](review/dormancy-trial-integration-review-2026-11-11.md),
[Jacobian](review/dormancy-jacobian-review-2026-11-11.md) and
[stage](review/dormancy-stage-review-2026-11-11.md) qualifications. Every
numerical repeat has a distinct protocol fingerprint; the endpoint and
probability consumers share explicit selected fingerprints where needed.
Source hashes and physical parameters must match the approved declaration;
partial or mixed numerical graphs are rejected. Census and prefix recording
remain one-cell/ten-year and zero-floor/annual, respectively. Reused census
evidence additionally requires no removals and dense global minima outside
the rare-population range. The physical grid combines qualified source
epochs; the final probability calculation uses one checked analysis epoch.

Case 125 uses the separately qualified
[terminal dormant-resolution rule](review/dormancy-absolute-resolution-policy-2026-11-11.md),
helper SHA-256 `f4861dbe9806eebf4e56dde1279801ce82cbb13af438e661e205213f1ba63ee4`.
It preserves the physical equations and census. Only a positive, unresolved
dormant compartment on a certified abundant single-guild, single-habitat
census piece can use the declared absolute composition resolution. Its own
relative abundance accuracy remains unresolved. The original-start 100,000-year
flow completes, and two required uncensored physical controls are bitwise
identical to the preceding strict producer. Qualified local corrections are
not global trajectory or rare-lineage error bounds.

The final probability helper is SHA-256
`93f5c2bd47824186ad24d12400f63218e2ff1c16edc4c3e9627914dc98226f62`.
The [kernel review](review/dormancy-opening-kernel-review-2026-11-11.md)
records the preservation of leading multihop conversion paths and stable
survival-boundary arithmetic. The
[clock review](review/dormancy-opening-clock-review-2026-11-11.md)
records the captured conversion-opening failure, its local-time repair and
the completed 100,000-year official task. The adaptive error criterion,
rate arrays and probability-window definitions are unchanged. All 143
profiles now score successfully. Shared probabilities, classifications and
threshold brackets agree with the preceding epoch; small changes in nonrare
log-scale diagnostics are preserved in the archive.

The [platform check](review/check_dormancy_platform_precision.json) records a
real precision limit. Matched Mac and Linux runs agree in climate and final
stocks, yet a transient Linux dormant bank of about 996 cells changes the
strict stationarity flag. It represents about `10^-23` of total biomass and
does not resemble the macroscopic cycles above. Both original flags remain;
criteria are not relaxed. Tiny-stage stationarity is therefore assessed
separately from material ecological or climate oscillations.

## Turnover numerical source identity

The numerical variant retains the frozen physical equations and the
softplus/log coordinates of every initially present guild. It uses Radau,
an explicitly scaled numerical Newton matrix and a 1000-year maximum step.
Guilds absent initially stay on their exact invariant face. This prevents
implicit-solver rounding from creating immigrants. Acetate absolute tolerance
is `10^-13 mol/L`; stocks are not clipped. Automatic Jacobian differencing
in the initial LSODA and Radau trials could stall near underflowed rare stocks;
those trial receipts remain separate from the qualified numerical epoch.

The qualified `turnover.py` SHA256 is
`9d964b8cbf6f81a848be43707e0625fa6be05771a857a061593bfa91e9605de3`.
The [map manifest](figures/turnover/regimes_manifest.json),
[thermal-root audit](figures/turnover/regimes_thermal_audit.json),
[basin manifest](figures/turnover/basins_manifest.json) and gate record bind
the outputs to that source and the unchanged climate, uptake and physical
model inputs. Twelve targeted tests cover the new regimes, continuum contact,
corner stability, positive-coordinate fidelity and exact absence of a guild.

The [raw-payload receipt](figures/turnover/payload_receipt.json) pins the
shared T1–T3 archive. Its `source_epochs/t2_analysis/` directory retains the
exact T2 endpoint and survival producers from commit `b759291`, as recorded
by their manifests. The common analysis helpers were subsequently extended
for T3; exact historical replication uses those retained source versions.
