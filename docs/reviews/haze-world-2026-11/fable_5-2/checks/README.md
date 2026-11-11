# Reviewer checks for the haze-world review (Claude Fable 5.2)

Scratch code behind the findings marked **verified** in
`review-claude-fable-5-2.md`. Everything imports the repository's own model
functions unchanged, at tag `haze-world-review-1` (commit `7294023`). Run from
the repository root, for example:

```sh
uv run python path/to/lag.py
```

| Script | Finding | What it does | Runtime |
|---|---|---|---|
| `lag.py` | R1 | Adds a sixth state, `dT/dt = (T(r) − T)/τ_T`, to the five-stock model and prints the leading eigenvalue of the mixed state for τ_T from 0.001 to 3000 yr, at f = 0 and 0.5. Reproduces the ledger's 119.57-yr mode first. | seconds |
| `lag_nl.py` | R1 | Integrates that six-state system from a 0.1% kick in log-biomass coordinates. | ~1 min |
| `nbox.py supply\|lag\|invade` | R1, R2 | Nine equal climate-tracking habitats with local temperatures `T + δ_j`, shared methane, cell exchange 10⁻³ yr⁻¹, optional thermal lag. Local temperatures are clipped to the declared 273–303.15 K physiology domain. Edit the `spread` tuples for the ±10, ±14 and ±18 K invasion cases. | 1–3 min each |
| `robust.py` | R3 | One-at-a-time changes to the reference physiology, then the team's 243-set grid for MSB and MSP in the coupled reference structure. | seconds |
| `mc.py` | R3, R10 | 4000 draws of Kotsyurbenko Table 2 V_max and K_m from their published 95% intervals (normal, independent), switch temperature for each. | ~1 min |
| `fband.py` | R4 | Supply band with a stable mixed state against the acetate-to-methane fraction f. | ~3 min |
| `cases.py` | R12 | Reference biology on Arney cases A–D. | seconds |
| `c07.py` | C07 | Independent recomputation of the focal invasion transient. | seconds |
| `last.py` | R3, R5, R6 | MSP coupled equilibria; capacity ratios `Q/V` by temperature; supply and loss fluxes in molecules cm⁻² s⁻¹. | seconds |
| `doi.py`, `find.py` | Literature | Crossref lookups by DOI and by title. `dois_checked.txt` and `title_queries.txt` are the inputs used. | seconds |

`nbox_*.jsonl` hold the summary lines those runs printed. Cell counts use the
repository's convention (3×10⁻¹³ g per cell, 5.1×10¹⁸ cm², reference habitat
volume). These are reviewer diagnostics, not qualified experiments: single
solver, no convergence study, nine boxes.
