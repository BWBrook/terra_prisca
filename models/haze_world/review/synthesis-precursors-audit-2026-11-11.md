# Independent audit of single-guild synthesis claims C01–C04

Codex, 11 November 2026. The [checker](synthesis-precursors-audit-2026-11-11.py)
uses independent scalar balance equations and table recounts, without calling
the production equilibrium, regulation or viability solvers. Its
[output](synthesis-precursors-audit-2026-11-11.json) retains exact values,
selectors, input hashes and its own source hash. No long trajectory was
rerun and no earlier physical source or output was edited.

## C01: support after correcting the atmosphere scope

The 78 domain-invariant rows in `figures/setpoint.csv` pool four atmospheres:
A has 19, B has 18, C has 19 and D has 22. The ledger's “Arney case B only”
limit is wrong for that pooled number.

Starting from the climate vertices and atmosphere table, the checker solves
`r = r_a + P eta(T(r))`, with
`eta = max(0, 1 - P_K/[P(rho-1)])`. Each independently recovered root agrees
with the rounded CSV temperature within 0.000501 K, remains in the extracted
climate interval, lies on a cooling segment, and has a stable scalar slope.
The unrounded offsets are **0.0149483–0.0369396 K**, which round to the cited
**0.015–0.037 K**. The source bounds point inward independently.

Suggested claim: “In the high-supply scalar experiment across Arney A–D,
locally stable equilibria lie 0.015–0.037 K above the resource-dependent
cold net-growth edge.” Use `figures/setpoint.csv` and this audit JSON as the
specific evidence. This does not prove exact reduced dynamics for the full
system, nor temperature accuracy at the millikelvin scale in the real climate.

## C02: support within the fixed-peak U family

At an interior unconstrained singularity with fixed peak growth, the selection
gradient gives `theta = T`; then `rho = 10` and `rho_T = 0`. Capture and methane
source therefore equal the temperature-independent `rho=10` control, and
the local regulation ratio is one for any regular loss law with nonzero
local slope. The five sensitivity laws are anchored to that same control.
The independent constant-capture balance gives
`r = 0.219655255922115`, `T = 273.4375738262 K`, matching every U endpoint to
CSV precision. The stored control contrasts are zero.

Suggested claim: “In the fixed-peak U adaptive-dynamics model, a feasible
interior singular optimum removes the cold-edge temperature response and
recovers the temperature-independent control.” Keep the one-guild,
monomorphic, common-resource and fixed-peak qualifications. “Nothing
constrains it” should not obscure these structural assumptions.

## C03: support the floor result, reject the unrestricted “only”

Recounting F endpoints gives first sampled floors with a local regulation
ratio below 0.3 of **291 K** for power exponent 0.2 and logarithmic loss,
**292 K** for exponent 0.5, and **293 K** for exponents one and two.
Independently solving those roots and differentiating the source–loss balance
reproduces each recorded ratio within 1e-6. Across the selected strong-buffering
F rows the cold-edge offsets are **0.1440–2.3944 K**, supporting the displayed
**0.14–2.4 K**.

The result is specific to the **hard-floor F family**. It is not evidence that
a floor is the only route to regulation. The same frozen endpoint table has
12 hotter-is-better H rows with ratios below 0.5 and no optimum floor; its
lowest ratio is 0.295431. The synthesis currently drops this known contrast.

Suggested claim: “Within the fixed-peak hard-floor family, strong buffering
returns at sampled optimum floors of 291–293 K, with the equilibrium following
the resource-dependent cold edge.” Cite `figures/darwinian_endpoints.csv`
and this audit JSON. State separately that an H trade-off retains buffering
under sufficiently shallow loss. These are sensitivity results, not measured
thermal limits or photochemistry.

## C04: support death during warming for the frozen U controls

`figures/strains_rescue.csv`, rather than the sparse example series, supplies
the full survival evidence. Its 18 U/no-mutation rows all die **2,910–4,200
years after the decline begins**, across two methane-free climate assumptions,
three final supplies and three census intervals. These are fixed-optimum
populations; other mutation settings and the H family do not have that fate.

Independently minimizing
`P_required = r-r_a + P_K/(rho(T(r),theta)-1)` at `theta=273.5 K` gives
0.00107507 and 0.00120280 for the two bridge anchors, both below even the
lowest tested final supply of 0.02. The final environment can sustain the
frozen strain, so the observed loss is a transient problem.

The extracted case-B warming maximum is **297.008 K** (displayed 297 K).
The example fixed-U series has its last living saved state at **288.188 K**
and its first dead saved state at **292.801 K**, before reaching that maximum.
The data therefore support death **during the warming excursion toward the
peak**, not literal death at 297 K. The 500-year example cadence does not
locate the exact death temperature; the census table supplies exact removal
timing within that model.

Suggested claim: “Under the specified decline, fixed-optimum U populations
without mutation die during warming as haze clears, despite viable final
supplies.” Retain uncalibrated mutation, biomass cutoff, census and bridge
assumptions; do not generalize to every methanogen population.

## Reproduction

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run python models/haze_world/review/synthesis-precursors-audit-2026-11-11.py
```

The original experiment commands remain available to regenerate their source
tables; this bounded audit adds independent algebra and recounts from their
committed evidence. Status may become supported only for the corrected,
qualified claims above.
