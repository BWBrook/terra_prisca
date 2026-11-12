# Stage D: precedents and framing

Claude (Opus 5.5), 12 November 2026. This answers review finding X9. It
compares haze-world with its closest precedent at the level of equations,
and places the Stage B results within control theory. DOIs were checked
against Crossref metadata on 12 November 2026. Unless stated otherwise, my
statements about a source's content rest on the source itself (Seto & Akagi)
or on its title and abstract (all others). The control-theory papers must be
read in full before the manuscript cites their results in detail.

## Seto & Akagi (2007): the static mechanism is precedented

[Seto & Akagi (2007)](https://doi.org/10.1016/j.jtbi.2007.05.013), *J. Theor.
Biol.* 248, 267–274.

**Their model:**

- two species compete for one resource in a **closed** system, with
  `R = R_init − N₁ − N₂`;
- growth rate `bᵢ(T) μᵢ(R) − d`, with an **identical** parabolic thermal
  response `b(T)` and different Monod curves (a gleaner–opportunist
  trade-off);
- temperature is algebraic: `T = T_b + Σ Eᵢ Nᵢ`.

**What they find.** Coexistence requires `R₁* = R₂*`. That fixes
`R_coex = (r₁K₂ − r₂K₁)/(r₂ − r₁)`, independent of T. It also fixes `T_reg`
through `b(T_reg) = d/μ(R_coex)`, which gives two roots, one either side of
the optimum. Across a range of background temperature `T_b`, the realised
temperature therefore sits on an exactly flat plateau. The guild proportions
absorb the forcing. A Jacobian analysis gives which root is stable,
depending on the sign of `E₁`.

**What carries over to haze-world.** Exact pinning by R* equality, with the
community composition absorbing the forcing, is their mechanism. Our
reference thermostat is an instance of it. The paper must say so plainly and
must not claim the static set point as new.

**What differs:**

| | Seto & Akagi (2007) | Haze-world |
|---|---|---|
| Thermal response | Identical in both species; T enters only through `b(T)` | Different, measured strain physiology. The switch comes from crossing R* curves, not a shared optimum. |
| Resource | Closed, recycled | Open hydrogen supply with an outlet. The forcing is supply, not background temperature. |
| Climate link | Linear, instantaneous, `T = T_b + E N` | Methane stock with a finite lifetime, a published nonlinear haze response, and an explicit thermal lag |
| Product chemistry | None | Acetate and methane activities, and the fate of acetate (`f`) |
| Dynamics | Local stability at zero lag | Delay margins, the pinning–robustness trade-off, nonlinear transients |
| Assembly | Not studied | Invasions, finite populations, refuges, dormancy |
| Calibration | Generic | Archean case B; physiology transferred from strains |

**What is new is the dynamics.** Seto & Akagi establish the plateau. They do
not ask what climate inertia does to it, or what a graded mechanism costs.
That is our main contribution (C54–C57).

## Control theory: exact pinning is integral feedback

**Precedents:**

- [Yi, Huang, Simon & Doyle (2000)](https://doi.org/10.1073/pnas.97.9.4649),
  *PNAS* 97, 4649–4653. Robust perfect adaptation in bacterial chemotaxis
  through integral feedback.
- [Khammash (2021)](https://doi.org/10.1016/j.cels.2021.05.020), *Cell
  Systems* 12, 509–521. A review of perfect adaptation in biology.
- **Our regulator.** A supply-independent set point maintained by
  re-sorting composition is robust perfect adaptation. The guild log-ratio
  integrates the fitness difference, as Codex's correction states. In
  control language, exact pinning is integral action.

**Two opposing guilds as reins:**

- [Saunders, Koeslag & Wessels (1998)](https://doi.org/10.1006/jtbi.1998.0746),
  *J. Theor. Biol.* 194, 163–173. Integral rein control in physiology.
- **Our regulator.** Each guild alone pushes climate one way. On the
  haze-cooling branch, methanogens cool by adding methane, and acetogens warm
  by diverting hydrogen away from methane. Their opposition gives control in
  both directions.
- **Before writing.** This framing should be checked against the full paper.

**Hard limits and leaky integrators:**

- [Olsman et al. (2019)](https://doi.org/10.1016/j.cels.2019.06.001), *Cell
  Systems* 9, 49–63.e16. Hard limits and performance trade-offs in antithetic
  integral feedback.
- [Qian & Del Vecchio (2018)](https://doi.org/10.1098/rsif.2017.0902),
  *J. R. Soc. Interface* 15, 20170902. Leaky integration through dilution.
- **The connection.** Together these titles mark a literature on two
  questions: the trade-offs that integral feedback faces in biochemical
  networks, and what happens when the integrator leaks. Our product feedback
  and habitat spread are both leaks. C57's price, 0.07–0.32 K per e-fold of
  supply for a 30-year delay margin, is an ecological case of that
  trade-off.
- **What is new.** Our framing claim is limited to this: an ecological
  climate regulator shows a quantified trade-off between precision and
  robustness, of the kind known in molecular control. Their specific results
  must not be borrowed before both papers are read.

## Biotic regulation and timescales

- **Daisyworld:** [Watson & Lovelock (1983)](https://doi.org/10.1111/j.1600-0889.1983.tb00031.x),
  *Tellus B* 35, 284–289. Already reconstructed in this repository.
- **Timescales:** [Weaver & Dyke (2012)](https://doi.org/10.1016/j.jtbi.2012.07.034),
  *J. Theor. Biol.* 313, 172–180. The importance of timescales for the
  emergence of environmental self-regulation.
  - Its title and subject make it the direct precedent for our lag result.
  - The comparison should state what differs: our timescale separation is
    between exclusion (years) and climate (millennia). The instability comes
    from inertia in the thermal response.
- **Ecosystem–atmosphere comparators:**
  - [Sauterey et al. (2020)](https://doi.org/10.1038/s41467-020-16374-7),
    *Nat. Commun.* 11. Coupled methane-cycling ecosystems and the Archean
    atmosphere. As Codex noted, its acetogens use CO, so it is not the same
    experiment.
  - [Kharecha, Kasting & Siefert (2005)](https://doi.org/10.1111/j.1472-4669.2005.00049.x),
    *Geobiology* 3, 53–76.
  - [Ozaki et al. (2018)](https://doi.org/10.1038/s41561-017-0031-2),
    *Nat. Geosci.* 11, 55–59.

  These bear on the open hydrogen budget (X8).
- **Climate response:** [Arney et al. (2016)](https://doi.org/10.1089/ast.2015.1422),
  *Astrobiology* 16, 873–899.
- **Competition theory:** [Armstrong & McGehee (1980)](https://doi.org/10.1086/283553),
  *Am. Nat.* 115, 151–170.

## The framing this supports

**One paper.** The proposed thesis:

> Hydrogen competition between acetogens and methanogens can regulate Archean
> climate on the haze-cooling branch. With fixed thresholds, exclusion acts as
> integral feedback: it holds temperature exactly against supply, as in Seto
> and Akagi's plateau, but that precision is fragile to climate inertia.
> Self-limitation through acetate, or spread in habitat temperature, makes the
> integrator leak. A small, calculable loss of precision then buys
> robustness. Assembly is history-dependent, so which regulator a planet
> realises depends on memory.

**Conditions, stated up front:**

- the crossing exists only under the culture capacity normalisation (X4);
- regulation needs a sink that keeps acetate from methane (X7);
- the evolution results assume a common thermal cost (X10).
