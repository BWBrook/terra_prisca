# Evolving thermal tolerance: scope

Claude, 9 November 2026. This scopes the haze-world's evolutionary variant
after Codex's [budget review](review/2026-11-09.md). It sets the climate, loss
and extinction assumptions for a production variant. The scratch preview
has an [independent evolutionary review](review/evolution-review-2026-11-09.md)
by Codex; its conditional result and limits are incorporated below.

## Question

The draft's result 1 places the equilibrium at the methanogens' cold
net-growth edge. Robertson & Robinson
([1998](https://doi.org/10.1006/jtbi.1998.0799)) showed that adaptation can
erode Daisyworld's regulation. Lenton & Lovelock
([2000](https://doi.org/10.1006/jtbi.2000.2105)) replied that constraints on
adaptation restore it. We test two things in haze-world:

1. whether the cold-edge equilibrium survives selection on the thermal
   optimum;
2. whether the cold trap (result 3) survives evolution and explicit
   extinction.

## Preview: unconstrained selection removes the thermostat

At the resident's equilibrium (D\*, T\*), a rare mutant grows when
ρ_m(T\*) > ρ_r(T\*). It then draws the donor below the resident's
D\* = K/(ρ − 1). Selection therefore acts on growth at the prevailing
temperature. A mutant at rarity has no leading-order effect on the shared
climate in this well-mixed growth-trait model. Selection nevertheless depends
on the climate created by the resident. The invasion ranking assumes a common
donor affinity K; allowing K to evolve changes the ranking.

For E = 0, below the optimum the selection gradient ∂ ln ρ/∂T_opt is negative.
T_opt falls
until T_opt = T\*. With no peak-growth trade-off (E = 0), growth then equals
the temperature-independent control's ρ = 10. Capture is exactly the same
finite value in both, and their equilibrium balances coincide.

The hotter-is-better trade-off, ρ_max ∝ exp[(E/k)(1/T_ref − 1/T_opt)], has
qualitative motivation in Knies et al. ([2009](https://doi.org/10.1086/597224))
and Dell et al. ([2011](https://doi.org/10.1073/pnas.1015178108)). Knies studied
bacteriophages; Dell's within-species temperature sensitivities do not measure
our across-optimum trade-off. Neither calibrates E or w for methanogens.
The singular strategy has T_opt − T\* = x, where
E/(k T_opt²) = 2x/(w² − x²). The original scope used T\*² in error; the
preview's numerical derivative was correct. Under linear loss the resulting
climate is near, rather than identical to, the fixed-ρ control. Evolved peak
growth also differs from that control, requiring a matched-capacity comparison.
See the [thermal evidence](evidence/thermal-margins.md).

[`review/evolution_preview.py`](review/evolution_preview.py) records the
scratch run, with output in
[`evolution_preview.json`](review/evolution_preview.json). The run uses
case B, starts from a cold edge of 281 K and holds w at 20 K.

| Potential ratio | E (eV) | T\* start → end (K) | T_opt end (K) | η end | Passive T (K) |
|---:|---:|---|---:|---:|---:|
| 0.22 | 0 | 281.30 → 273.44 | 273.44 | 0.996 | 273.44 |
| 0.22 | 0.32 | 281.30 → 273.48 | 281.39 | 0.987 | 273.44 |
| 0.22 | 0.65 | 281.31 → 273.76 | 285.68 | 0.956 | 273.44 |
| 0.30 | 0–0.65 | 281.1 → 274.00 | 274.0–285.9 | 0.97–1.00 | 274.00 (plateau) |

At potential ratio 0.22 the whole evolutionary path stays inside Arney's
extracted interval, so removal of the original cold-edge set point uses no
climate extrapolation. The approximate 8–12 K H margins are model outcomes,
not measured universal margins in methanogens.

**Implication.** In this model the biotic cold-edge equilibrium is not
evolutionarily stable unless adaptation is constrained. Two features remain
under evolution:
- supply limitation;
- the abiotic cap from haze, its cooling branch and self-limitation.

The question is which constraints and loss laws leave a temperature signal,
and whether that signal provides regulation against external changes. This
preview does not establish that haze alone regulates climate or that biological
constraints must be wholly non-evolvable to matter.

## Assumptions for the build

**Climate.**
- The primary scenario is case B at a potential ratio of 0.22. Both endpoints
  and the path between them lie inside Arney's interval. Every step records
  its domain, and a run that leaves the interval is reported as extrapolated.
- The cold-trap and rescue experiments need the low-methane bridge. They run
  as labelled scenarios with T₀ swept.
- Eager-Nash et al. (2023) give a separate haze-free 3D reference for the same
  epoch and similar sunlight (S/S₀ = 0.809 versus Arney's 0.81), with a 1-bar
  background atmosphere. Pressure conventions, clouds and ice also differ.
  Our chosen log-CO₂ interpolation of their zero-methane checkpoints to case
  B's 0.018 bar is about 282.6 K; it is not a published case-B baseline or a
  validated replacement for the bridge.
- The draft's default T₀ of 265 K is therefore about 18 K colder than the
  nearest published scenario. At T₀ = 283 K the bistable band in the
  regimes grid needs cold edges of 284 K or higher, so the default 281-K edge
  has no trap.

**Loss.**
- First-order loss with τ swept over 6–19 kyr, conditional on Arney's
  aggregate onset flux, using the potential-ratio axis. The constant column
  conversion c remains an approximation to N′(r).
- For E = 0, a feasible regular interior singularity has exactly the same
  capture and equilibrium balance as the constant-ρ control for any loss
  law. This does not prove existence or global reachability.
- For E > 0, increasing loss alone is insufficient: a smooth increasing
  logarithmic law, normalized to leave the same control climate, gives an
  evolved climate 4.61 K above it at E = 0.65 eV, inside Arney's interval.
  This is a mathematical sensitivity, not recovered photochemistry. See the
  [reproducible counterexample](review/evolution-review-2026-11-09.md).
- Rescue timing depends on τ and on storage, so those runs sweep τ.

**Time scales.**
- Codex's eigenvalues put local ecological–methane relaxation at decades in
  the reviewed reference run; climate is algebraic here, with no independent
  relaxation time. Assuming slower, small-step adaptation lets stage 1 use monomorphic adaptive dynamics
  (Geritz et al. [1998](https://doi.org/10.1023/A:1006554906681)).
- Mutation supply is not calibrated. Results are reported against trait
  change, not years, until it is.

**Extinction.**
- The repaired continuum model has none: log biomass survives any decline.
- Stage 2 adds a demographic floor B_min, below which a strain is removed.
  Extinction of the entire population is absorbing without immigration;
  individual trait bins may be repopulated by mutation from surviving strains.
  The threshold is swept over many orders of magnitude relative to B\*.
- Mutation enters as diffusion on a T_opt grid, with mutational variance
  swept.
- Rescue follows Gomulkiewicz & Holt
  ([1995](https://doi.org/10.1111/j.1558-5646.1995.tb05971.x)): during a
  supply decline, does adaptation outrun the fall in biomass?

**Constraint scenarios.**

| Label | Constraint | Expected outcome |
|---|---|---|
| U | None; fixed peak growth and K | Same balance as the passive control at a feasible interior singularity; the linear-loss preview reaches it |
| F | Hard floor T_opt ≥ T_floor | Conditional constrained set point. The floor is an assumption, not a measured universal bound |
| H | Hotter-is-better, E = 0–0.65 eV | Near the fixed-ρ control under linear loss, with model margins around 8–12 K for E > 0; other increasing losses can retain a contrast |
| C | Homoacetogens and methanogens share H₂; reaction energetics fixed, biological kinetics and energy requirements strain-specific | Open. Benchmark the [published uptake competition](evidence/hydrogen-competition.md) before coupling it to climate; no evolution-proof thermostat is established |

## Stages

1. **`darwinian.py`, a named variant.** Monomorphic adaptive dynamics for
   scenarios U, F and H. Check the exact singular-strategy formula, invasion
   criterion and domain record. Add matched-capacity controls and loss-shape
   sensitivities. Figures show T\* against trait change and the endpoint
   against the constraint; arbitrary trait steps are not interpreted as years.
2. **Strain-resolved model with B_min and mutation.** Test rescue under
   declining supply, and whether cold-tolerant strains escape the cold trap
   across T₀ scenarios.
3. **Scenario C.** First reproduce strain-specific uptake competition, then
   couple a shared H₂ resource and explicit acetate fate to methane. Test
   sensitivity or adaptation of biological energy and kinetic requirements;
   fixed chemical energetics alone does not fix organismal thresholds. The
   donor-limited methanogen treatment of Kharecha et al.
   ([2005](https://doi.org/10.1111/j.1472-4669.2005.00049.x)) supplies a related
   framework, not a calibration of these strains.

DOIs were checked against Crossref on 9 November 2026.
