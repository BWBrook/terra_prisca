# Temperature-buffered refuges under one methane atmosphere

Codex (GPT-6, OpenAI), 10 November 2026. Implements Claude (Opus 5.5)'s
[buffered-refuge specification](buffered-refuge-spec.md), following the
[two-habitat model](refuge-coupling.md). Physical source is frozen at
`87103f7`. The [implementation notes](buffered-implementation-notes.md) record
the interpretation of the design before the main matrix.

**Status: implementation and numerical controls are built; scientific results
await qualification.** The Results section below is reserved for the main
experiment, the B2 assessment and the permitted sensitivity comparisons.
Predictions B1–B5 are hypotheses, not requirements for accepting the code.

## Question and thermal assumptions

Can the biosphere supply its own rescue from either invasion direction?
The earlier geometry tied every habitat to global temperature through fixed
offsets. A cold refuge that remained favorable through the greenhouse peak
could then become colder than the defined physiology after haze cooling.
This variant prescribes refuge temperatures independently of the surface.

The generic [physical model](../../src/terra_prisca/haze_world/habitat_coupling.py)
accepts any number of habitats. A `tracking` habitat uses `T(r)+delta`; a
`buffered` habitat uses a fixed temperature. The default arrangement is:

| Habitat | Area weight | Temperature rule |
|---|---:|---|
| Bulk | 0.96 | Global Arney case-B response `T(r)`, with no offset |
| Warm refuge | 0.02 | Fixed 286 K |
| Cold refuge | 0.02 | Fixed 278 K |

Single-refuge configurations give the bulk weight 0.98; without refuges its
weight is one. Zero-area habitats are inactive and have zero local stocks.
Donor supply per area and effective habitat volume per area remain uniform.
Hydrogen and acetate stay local; only cells disperse.

Fixed refuge temperatures represent external heat baths. The model does not
calculate the heat flux maintaining them, a water-column energy balance, or
hydrothermal circulation. No compensating temperature shift is imposed on the
bulk. In the default three-habitat arrangement,

    mean(T_habitat) − T(r) = 0.02 [286 + 278 − 2 T(r)].

Across 273.39–297.008 K this expression ranges from +0.3444 to −0.60032 K.
Exact trajectory extrema are reported. A small mean departure is bookkeeping,
not evidence of energy conservation or a calibration of Archean refuge area.

The bulk retains the existing 273–277.15 K cold continuation. Refuge
temperatures are inside the measured 277.15–303.15 K window. The inherited
283 K low-methane bridge, high-methane plateau and 10,000-year linear methane
lifetime remain assumptions. Physiological support and published radiative
support are separate flags. A domain exit in this prescribed buffered design
must be investigated; it is not assigned a settled endpoint or repaired by
adding an extrapolation.

## Stocks, exchange and reducing equivalents

There are `4N+1` physical stocks. With three habitat slots they are

    [p_b, XA_b, XM_b, A_b, p_w, XA_w, XM_w, A_w,
     p_c, XA_c, XM_c, A_c, r].

Hydrogen pressure `p` is in Pa, biomass `X` in gDW/L, acetate `A` in mol/L,
and shared atmospheric methane `r` is the CH₄/CO₂ ratio. Time is years.
The guilds are acetogens A and hydrogen-using methanogens M. Acetate recycling
is prescribed, so methane production from acetate can continue after the
explicit M guild disappears; its consumers are not a third population.

Each habitat uses the [existing local metabolism](population-coupling.md) at
its own temperature: uptake, maintenance, yield, assimilation and turnover.
Writing `U_ij` for annual uptake, `C_ij` for its catabolic part after biomass
assimilation, and `mu_ij` for annual biological net growth,

    kappa dp_j/dt = J_annual − sum_i U_ij − k_out,annual (p_j−p_atm),
    dX_ij/dt      = mu_ij X_ij + d sum_k w_k (X_ik−X_ij),
    dA_j/dt       = C_Aj/4 − (k_rec,j + k_other,j) A_j,
    dr/dt         = Gamma sum_j w_j [C_Mj/4 + k_rec,j A_j]
                    + abiotic methane − L(r).

The atmospheric hydrogen boundary stays fixed, and the reference acetate
residence is one year. Exchange conserves each guild's weighted biomass.
The internal H₂-equivalent inventory is

    sum_j w_j [kappa p_j + alpha_A X_Aj + alpha_M X_Mj + 4 A_j]
      + 4 r/Gamma.

External donor input, hydrogen exchange, biomass/acetate exports, abiotic
methane and atmospheric loss close its balance. Atmospheric terms are counted
once. Census removals export the reducing equivalents of discarded cells.
Fixed refuge temperature removes radiative `dT/dr`; under product feedback,
local rates can still respond chemically to shared methane activity.

## Numerical controls and initialization

Historical two-habitat source remains unchanged. Two tracking patches recover
its right-hand side exactly; selected trajectories are compared within the
existing tolerances. Zero refuge areas recover the single-habitat equations.
Tests also cover conservative exchange, redox balance, fixed-temperature
derivatives and the distinction between radiative and chemical methane effects.

The [independent design audit](review/buffered-design-review.md) reconstructs
fluxes and a three-habitat equilibrium from shared source primitives, checking
the RHS, reducing equivalents and full spectrum. A separate
[Radau trajectory check](review/check_buffered_trajectory.py) uses different
biomass coordinates. These are independent numerical implementations with
common empirical inputs, not independent empirical validation.

Each invasion starts at a conditional equilibrium with only the resident
enabled, positive in every active habitat and locally stable. The
[equilibrium solver](../../src/terra_prisca/haze_world/habitat_equilibria.py)
uses finite scalar searches and seeded roots; multiple qualifying starts and
missing roots remain visible. The largest methane ratio is selected consistently
if several stable candidates are found. Search failure is not nonexistence.

The invader starts at 10⁻¹² gDW/L in every active habitat, preserving the same
weighted dose across configurations. There is no outside immigration.
Biomass dynamics are deterministic mean densities with scheduled removal,
not integer stochastic births or arrivals. Counts assume 3×10⁻¹³ gDW/cell
and the inherited effective global habitat volume. At each ten-year census,
a guild below one cell in a habitat is removed. Surviving populations elsewhere
can recolonize through exchange; global absence is absorbing.

The [integrator](../../src/terra_prisca/haze_world/habitat_integration.py)
retains positive/log stocks and exact absences. With exchange, total guild
biomass and all habitat allocations are explicit, avoiding subtraction of
nearly equal fractions. Minima use accepted dense-flow pieces, excluding
solver trials; their numerical searches are not interval-certified. Global
minima sum contemporaneous weighted stocks rather than separate local minima.
Local pre-removal minima, global pre-extinction minima and post-census zeros
have different meanings. All belong to the stated census-dependent trajectory.

## Predictions and experiments

The original specification fixes five hypotheses:

| ID | Prediction and discriminating comparison |
|---|---|
| B1 | Both refuges prevent either global extinction at `f≤0.5`, `d≤0.001/year`. Check simultaneous global minima and removals in both directions. |
| B2 | Under B1, opposing invasions reach one mixed endpoint near 281.5–282 K. Compare community stocks and methane as well as temperature. |
| B3 | One refuge gives one-sided rescue and retains invasion history. Test the literal claim, including the already-hazy 90%-conversion starts. |
| B4 | Rescue persists down to tested exchange `10⁻⁹/year`; stronger exchange may erode protection. No universal `10⁻²⁵/year` threshold is inferred. |
| B5 | A warm refuge permits methanogen persistence at 90% acetate conversion with a climate contrast below 0.1 K. Report material H₂ use separately from presence. |

B5's primary climate comparison is the endpoint minus the matched conditional
acetogen-only temperature in the same habitat configuration. A secondary
comparison uses the no-refuge invasion at the same `f`, exchange and activity
scheme where that control exists. This separates the ecological contrast from
the combined habitat and community effect. Unrun product-activity no-refuge
controls remain missing.

Main design: 96 attempts crossing `f=0/0.5/0.9`, four refuge configurations,
`d=10⁻⁹/10⁻⁶/10⁻³/1 per year`, and both directions. Separate zero-exchange
controls cross all configurations, fractions and directions: 24 attempts.

The sensitivity design has 72 attempts: 48 crossed refuge-temperature cases,
18 cases with 0.5% refuges, and six product-feedback cases. It follows the
qualified B2 assessment. If opposing endpoints differ under B1, longer settling,
equilibrium refinement, local stability and uncensored basin trajectories must
distinguish genuine multistability from census barriers before proceeding.

## Reproduction and evidence

```sh
uv run python -m terra_prisca.haze_world.buffered_experiments --stage pilot --workers 2
uv run python -m terra_prisca.haze_world.buffered_experiments --stage main --workers 4
uv run python -m terra_prisca.haze_world.buffered_experiments --stage controls --workers 4
```

After the B2 gate is qualified:

```sh
uv run python -m terra_prisca.haze_world.buffered_experiments --stage sensitivity --workers 4
uv run python models/haze_world/review/check_buffered_design.py
uv run python models/haze_world/review/check_buffered_trajectory.py
uv run pytest
```

The [runner](../../src/terra_prisca/haze_world/buffered_experiments.py) defaults
to 100,000 years, except 1,000-year pilots. `--years`, repeated `--case-id`,
`--raw-dir`, `--output` and `--collect-only` support extensions and recollection.
Each source/environment fingerprint identifies a raw record and completion
receipt. The collector verifies them before emitting public summaries and
manifests under `models/haze_world/figures/buffered_refuges/`; bulk records stay
in ignored `local/haze/buffered_refuges/`.

Stationarity requires at least 100,000 years; over the last 20,000 years,
relative stock spans and scaled derivatives must be below 0.001, temperature
span below 0.01 K, and census occupancy unchanged. A 1% catabolic-share rule
marks material contributions independently of occupancy. Keep longer horizons
in separate output directories so the original outcomes remain available.

## Results — pending qualified experiments

**Parent integration placeholder.** Add main/control/sensitivity qualification,
the B2 gate and any basin investigation, paired endpoint and climate contrasts,
global/local population minima, physiological/radiative domains, exact
habitat-mean temperature departures, figures, source hashes and archive receipt.
Then resolve B1–B5 with mechanisms. The numerical controls above do not supply
those outcomes or establish which refuges existed on early Earth.
