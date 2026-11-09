# Evolving thermal tolerance: scope

Claude, 9 November 2026. This scopes the haze-world's evolutionary variant
after Codex's [review](review/2026-11-09.md). It fixes the climate, loss and
extinction assumptions before any code is written. A scratch preview has
already answered the first question.

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
temperature. The methane each strain releases changes the climate for every
strain alike, so selection cannot act on that effect.

Below the optimum the selection gradient ∂ ln ρ/∂T_opt is negative. T_opt falls
until growth at T\* is close to its maximum, η → 1, and the system reaches the
passive, supply-limited state.

The hotter-is-better trade-off, ρ_max ∝ exp[(E/k)(1/T_ref − 1/T_opt)], has
support in Knies et al. ([2009](https://doi.org/10.1086/597224)) and
Dell et al. ([2011](https://doi.org/10.1073/pnas.1015178108)). It moves the
singular strategy to T_opt − T\* = x, the root of E/(kT\*²) = 2x/(w² − x²).
This is the familiar pattern of organisms living below their optimum. It does
not move the climate.

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
extracted interval, so the 8-K loss of regulation uses no climate
extrapolation.

**Implication.** In this model the biotic cold-edge equilibrium is not
evolutionarily stable unless adaptation is constrained. Two features remain
under evolution:
- supply limitation;
- the abiotic cap from haze, its cooling branch and self-limitation.

The question is no longer whether methanogens regulate. It becomes which
non-evolvable constraint, if any, leaves a temperature signal in the methane
budget.

## Assumptions for the build

**Climate.**
- The primary scenario is case B at a potential ratio of 0.22. Both endpoints
  and the path between them lie inside Arney's interval. Every step records
  its domain, and a run that leaves the interval is reported as extrapolated.
- The cold-trap and rescue experiments need the low-methane bridge. They run
  as labelled scenarios with T₀ swept.
- Eager-Nash et al. (2023) give a reference point under the same epoch,
  S/S₀ and 1-bar pressure. Their simulations are haze-free and 3D, so this is
  a cross-model comparison, not a splice. Interpolated in log CO₂ to case B's
  0.018 bar, their zero-methane baseline is about 282.6 K.
- The draft's default T₀ of 265 K is therefore about 18 K colder than the
  nearest published scenario. At T₀ = 283 K the bistable band in the
  regimes grid needs cold edges of 284 K or higher, so the default 281-K edge
  has no trap.

**Loss.**
- First-order loss with τ swept over 6–19 kyr, conditional on Arney's
  aggregate onset flux, using the potential-ratio axis. The constant column
  conversion c remains an approximation to N′(r).
- The preview's endpoint needs only η → 1. It therefore holds for any
  monotone loss law: the loss law moves the passive temperature, not the
  loss of regulation.
- Rescue timing depends on τ and on storage, so those runs sweep τ.

**Time scales.**
- Codex's eigenvalues put ecological and climate relaxation at decades.
  Adaptive change is slower, so stage 1 can use monomorphic adaptive dynamics
  (Geritz et al. [1998](https://doi.org/10.1023/A:1006554906681)).
- Mutation supply is not calibrated. Results are reported against trait
  change, not years, until it is.

**Extinction.**
- The repaired continuum model has none: log biomass survives any decline.
- Stage 2 adds a demographic floor B_min, below which a strain is removed and
  does not return. It is swept over many orders of magnitude relative to B\*.
- Mutation enters as diffusion on a T_opt grid, with mutational variance
  swept.
- Rescue follows Gomulkiewicz & Holt
  ([1995](https://doi.org/10.1111/j.1558-5646.1995.tb05971.x)): during a
  supply decline, does adaptation outrun the fall in biomass?

**Constraint scenarios.**

| Label | Constraint | Expected outcome |
|---|---|---|
| U | None | Passive state. The preview shows this |
| F | Hard floor T_opt ≥ T_floor | Set point at the floor's cold edge. Regulation is then the constraint itself |
| H | Hotter-is-better, E = 0–0.65 eV | Passive climate with an 8–12 K safety margin. The preview shows this |
| C | Homoacetogens compete with methanogens for H₂. The temperature dependence of the reaction energetics cannot evolve ([Conrad & Wetter 1990](https://doi.org/10.1007/bf00291281); [Kotsyurbenko et al. 2001](https://doi.org/10.1111/j.1574-6941.2001.tb00893.x)) | Open. This is the most plausible way a temperature signal could survive evolution |

## Stages

1. **`darwinian.py`, a named variant.** Monomorphic adaptive dynamics for
   scenarios U, F and H. Tests cover the singular-strategy formula and the
   domain record. Figures show T\* against trait change and the endpoint
   against the constraint.
2. **Strain-resolved model with B_min and mutation.** Test rescue under
   declining supply, and whether cold-tolerant strains escape the cold trap
   across T₀ scenarios.
3. **Scenario C.** Build it only if stages 1 and 2 confirm that regulation
   depends on constraints that cannot evolve. Its thermodynamics follow the
   donor-limited methanogen treatment of Kharecha et al.
   ([2005](https://doi.org/10.1111/j.1472-4669.2005.00049.x)).

DOIs were checked against Crossref on 9 November 2026.
