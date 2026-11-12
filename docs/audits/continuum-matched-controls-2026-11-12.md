# Secondary matched methanogen-only controls

The retained B1 treatment comparison is now exported separately from the primary
local frozen-composition gain. No primary equilibrium, spectrum, gain or PC0–PC6
verdict changes. The output contains 90 unchanged C0 comparisons and 80 newly
attempted C1 comparisons.

## Method and qualification

The sidecar keeps the community's supply, habitat offsets and quadrature
weights, dispersal rate, and chemistry. It removes acetogens and solves the
pure-methanogen resource and immigration balances analytically at each trial
atmospheric methane ratio. A scalar log-biomass solve closes the weighted
immigration mean. The atmospheric balance is searched on a finite 121-point
grid augmented with all climate vertices and the intersections with the
full-support temperature boundaries. Exact grid and vertex zeros are included,
residual-validated, and deduplicated; an invalid bracket-solver return is
rejected.

Admissibility requires the entire temperature support to remain within
273–303.15 K, a true per-capita balance residual below 1e-7 per year, and a
stable full resident Jacobian. The resident matrix contains pressure and
methanogen biomass in every habitat plus atmospheric methane; it does not
retain artificial absent-acetogen modes. The control supply slope follows from
the same implicit Jacobian. A unique qualified control with nonzero slope
defines the secondary ratio Sc / S_M. Plateau, corner, singular, ambiguous,
unstable, and unresolved controls do not acquire a defined ratio. A finite
search finding no admissible root is not a proof of branch nonexistence.

The quadratic local solution rejects materially negative discriminants and
clamps only roundoff-sized negatives. The final balance guard still governs
acceptance of the returned roots.

## Results

| C1 outcome | Settings |
|---|---:|
| Defined secondary gain | 8 |
| Candidate root, unresolved true balance | 8 |
| No admissible root detected in the finite search | 64 |

The eight defined gains occur at potential 0.24, spread 3 K, and dispersal
0.01 or 0.1 per year, across both chemistries and acetate fractions. Their
control temperatures are about 280.232 K and their slopes are approximately
−24.1 to −24.3 K per log supply. The eight unresolved controls remain
explicitly unresolved; negative resident eigenvalues do not substitute for
equilibrium balance qualification. Detailed root inventories and residuals are
in `matched_controls_manifest.json`.

All 48 reference-potential (0.3) C1 settings have
`no_admissible_control_detected`, with no supported root inventoried. The old
homogeneous pure-methanogen endpoints, 273.516744 K under fixed chemistry and
273.516850 K under product chemistry, cannot simply be reused as spread
initial states: each prescribed positive spread extends below 273 K. The
reference spread A-into-M invasion design therefore needs a supported starting
state or an explicit design revision before execution. These finite searches
do not establish that every possible replacement branch is absent.

## Reproduction and provenance

Run:

```sh
OPENBLAS_NUM_THREADS=1 uv run pytest -q tests/test_continuum_controls.py
OPENBLAS_NUM_THREADS=1 uv run python -m terra_prisca.haze_world.continuum_controls
```

All six focused tests pass, covering the homogeneous B1 root and slope,
weighted resource and immigration balance, support rejection, plateau
undefinedness, exact-vertex/false-root handling, and cache-tamper rejection.
The C0 cache and all 80 C1 input caches are read only after their hashes match
the primary manifest. Current model sources are checked against that manifest;
the separately documented flat-export module is excluded from that source
comparison. The sidecar manifest pins its own source, weighted core, dynamic
core, primary manifest, every input cache, and the output CSV.

Final SHA256 values:

| Artifact | SHA256 |
|---|---|
| `continuum_controls.py` | `6cc6a1a2bb5e17dfce995c8efc5292dc2a14f6130c613ac03bbcf2a5b158dae3` |
| `test_continuum_controls.py` | `846aa6d6877eee496ca465a8777ec11f3423dea96684cf3acf6d9ef1f315ab45` |
| `matched_controls.csv` | `7d333efd46f400b3a96a619fe5136ed9933bfb6be693e7fa04cec3d0c3e986be` |
| `matched_controls_manifest.json` | `7f5c6f7914fe3d48b0ea5fca10e0a6838624941524c96495952f9756c7b20ad2` |
