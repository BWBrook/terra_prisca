# Independent synthesis audit: community claims C05–C11

Codex, 11 November 2026. This audit re-derives the switch and reference mixed
state from the uptake, resource and methane balances; uses a separate
five-point numerical derivative for stability; verifies one checksum-pinned
finite-invasion record; and recounts the selected trajectory tables. It adds
no trajectories, changes no frozen producer, and supplies no new empirical
calibration. The [checker](synthesis-communities-audit-2026-11-11.py) and
[JSON evidence](synthesis-communities-audit-2026-11-11.json) retain the
calculations and source identities.

## Claim dispositions

| Claim | Disposition after correction | Specific evidence and limit |
|---|---|---|
| C05 | Support the local restoring sign | Solving equality of the two independently evaluated break-even pressures gives 281.534822805 and 282.780105860 K for saturating and first-order acetogen uptake. The corresponding case-B climate slopes are −721.258 and −599.934 K per ratio. Cold favors acetogens and warming favors methanogens locally. The feedback is restoring **if acetogen routing delivers less methane**. Negative sign is not a general stability proof. |
| C06 | Supported conditional equilibrium contrast | An independent two-by-two hydrogen/methane allocation balance gives the mixed state at 281.534822805 K. Both five-point derivative scales give leading real eigenvalue −0.000926010368/year. The methanogen-only controls are 273.516744039 K and 276.807475951 K, giving contrasts 8.018078766 and 4.727346854 K. These are conditional controls with acetogens disabled, not two simultaneously stable full-community states. |
| C07 | Support the specified f=0/0.5 invasion-history result | All 144 selected endpoints are census-stationary. Of 36 zero-immigration runs, the 24 at f=0/0.5 finish with the invader alone; the twelve at f=0.9 finish acetogen-only from either direction. The focal f=0.5, fixed-activity, one-cell/ten-year-census record removes methanogens at 20 years while temperature moves 273.516744039→273.525251377 K. Therefore do not extend history dependence to every recycling fraction or every initial state. |
| C08 | Replace universal failure by a domain-limited result | The path-protection recount gives 38 protected completed runs with the losing guild present, plus eight protected but domain-censored prefixes. No nonzero-contrast f≤0.5 opposing pair has two supported stationary endpoints in this design. However nine f=0.9 opposing pairs do reach matching coexisting endpoints at nonzero contrast. Thus “tracking refuges cannot support paired rescue” is false without the f≤0.5/design restriction. |
| C09 | Support twelve key runs, not all 192 | The key default-temperature, both-refuge subset at f=0/0.5 and positive exchange ≤0.001/year has twelve runs and six matching mixed pairs, 281.534822764–281.534901712 K. Direct comparison of methane, pressures, cell stocks and acetate gives maximum relative stock difference 3.65e−6. The full 192-case design is 123 coexisting, 44 acetogen-only and 25 methanogen-only endpoints, with thirteen 200 kyr extensions. Across 96 history pairs, 63 match and 49 match as mixtures. |
| C10 | Supported for the defined first bottleneck and exchange cut | An independent centered least-squares calculation on the 41 f=0, 2%-warm-refuge points at exchange 10⁻⁹–10⁻⁴/year gives slope 4.423187496 and maximum residual 0.05279045 decades. The 50% first-window crossing is 5.87616e−6/year; annual and ten-year posthoc global one-cell crossings are 1.72959e−6 and 1.72893e−6/year, ratios 3.3974 and 3.3987. These count diagnostics are not counterfactual reruns of local censuses. The Gaussian approximation gives 230.285 cells; exact table thresholds span 230.327–230.455 cells on that cut. |
| C11 | Supported numerical refutation | All 98 f=0.5 exchange cases are robust first-window survivors under the specified count scales. Their smallest **global acetogen count** is 115,536,991,713.862 cells, for warm-refuge area 0.005 and exchange 10⁻⁹/year (`exchange_0098`). This refutes the 10¹² minimum, while supporting the conditional persistence component of K5. “In the 0.5% refuge” must not imply a local refuge population count. |

## Consequential overclaims

C09's synthesis sentence says all 192 planned cases recover the same mixed
state. That confuses the total inventory with the twelve key runs. The
selected tables already contain both single-guild outcomes and mismatched
histories; no new simulation is required to correct it.

C08's unqualified tracking-refuge failure is contradicted by existing f=0.9
results. A representative pair is `subsets_0030_t100000`/
`subsets_0031_t100000`: warm area 0.05, contrast 8.6 K, exchange 0.001/year,
fixed activities. Both finish in matching spatial coexistence. The two
zero-exchange pure-partition pairs require their separate local-census
conditioning caveat; seven positive-exchange pairs provide the same direct
counterexample without that zero-exchange issue. Coexistence at high recycling
still must be distinguished from material climate regulation.

The failure to construct supported paired f=0/0.5 paths in the original
geometry is not a theorem about all climate-tracking refuges. Its imposed
area-weighted offsets and finite physiological domain are part of the result.

## Why memory is not necessary for every initial state

The independently reconstructed C06 mixed state has about **8.75449e25
acetogens and 5.15948e25 methanogens globally**, with a stable smooth
five-stock Jacobian. It has no refuge, dormant bank or outside immigration.
A one-cell census does nothing at that state, or in a sufficiently small
positive invariant neighbourhood attracted to it. This supplies a direct
counterexample to an unqualified assertion that a finite competitive
thermostat always requires an additional spatial or dormant store.

The results do support a more useful transient statement: under the studied
destructive resident–invader starts, exclusion can remove the losing guild
long before methane changes the environment in its favour. Refuges or dormant
banks can preserve that guild across this transient. A theorem of necessity
for every disturbance, population size, loss law or initial composition has
not been established. Per-guild conditional first-window probabilities do not
establish joint community persistence.

## Evidence paths and reproduction

Prefer the specific outputs below to model-page summaries:

- C05: this audit's `C05`, the committed Arney `figure4.csv`, and the selected
  switch configurations; the audit re-solves the roots rather than taking
  parent-supplied switch temperatures.
- C06: this audit's `C06`, `figures/population_coupling/continuation_check.csv`
  and `methanogen_only.csv`.
- C07: `figures/finite_populations/attained_endpoints.csv` plus the pinned
  `main_0024_t100000-ce9c0899cdf042d0.json.gz` record; its SHA256 is
  `48f936931d3c5118d7a8e9effb1cce30a47e76e66d3ab566e739922b7498aea1`.
- C08: `figures/refuge_coupling/selected_main.csv`, `selected_subsets.csv`
  and `direction_comparisons.csv`.
- C09: `figures/buffered_refuges/selected_main.csv`, `selected_controls.csv`,
  `selected_sensitivity.csv` and `direction_comparisons.csv`.
- C10–C11: `figures/bottleneck/exchange_continuation.csv`; the independent
  fit and threshold interpolation are in this audit's JSON.

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache MPLCONFIGDIR=/tmp/terra-prisca-mpl \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
uv run python models/haze_world/review/synthesis-communities-audit-2026-11-11.py
```

The checker completes in well under a second. Its algebra shares the model's
empirical uptake inputs and physical RHS; this is independent calculation,
not independent empirical validation. Full-state and probability conclusions
retain their original domain, activity, count and initialization assumptions.

## One-pass semantic check of the revised synthesis

The revised thesis is supported at its stated scope: rescue through the studied
destructive invasions, rather than universal necessity of a refuge or seed bank.
It now retains the stable abundant unrefuged mixed-state counterexample and
separates per-guild first-window survival from joint endpoint persistence.
C08 correctly retains the higher-recycling coexistence counterexamples; C09
correctly separates the twelve key runs from the full 192-case inventory.
The corrected C05–C11 values and interpretation limits agree with this audit.
No further experiment is needed for that scoped synthesis.

Three small wording clarifications would remove residual ambiguity:

- In argument 5, say the cold refuge must **remain favorable while global
  climate crosses** the 297 K greenhouse peak. Its local temperature is the
  global temperature minus its offset; the refuge itself does not reach 297 K.
- Give C09's key exchanges explicitly as `10⁻⁹`, `10⁻⁶` and `10⁻³/year`, rather
  than “through 0.001/year”. The result is the three tested positive settings,
  not every intervening rate or the zero-exchange control.
- In E3, the reason not to infer continuum climate bistability from C07 is
  that distinct absorbing census outcomes do not establish two stable
  continuous equilibria. Existence of a stable mixed state alone would not
  rule out additional stable states. The synthesis itself already uses the
  sounder “not a new proof” wording.

These are precision edits, not unresolved scientific objections to the revised
argument. This was one bounded read-only pass; the shared prose, estimands and
ledger were not edited by this reviewer.
