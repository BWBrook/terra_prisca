# Terra Prisca: vision

*Living document. Started 8 November 2026 from the opening conversation between
Barry W. Brook and Claude (Opus 5.5). Revise it as the project grows; do not
let it go stale.*

## The question

Why has Earth stayed habitable for about four billion years? The Sun has
brightened by roughly 30% since the Archean. Over that time the planet passed
through snowball glaciations, the Great Oxidation Event, the Neoproterozoic
oxygenation, the Cambrian radiation and the greening of the continents, and
liquid water and life persisted throughout. Whether that persistence reflects
regulation by the biota (Gaia), abiotic thermostats, selection on planetary
outcomes, or plain luck is still argued.

Terra Prisca ("ancient Earth") explores simulations of Earth through the
Cryptozoic (Hadean to Proterozoic) and the early Phanerozoic. The scope is
deliberately open. There is no fixed endpoint: ideas branch, get built, get
tested, and either grow or are left as documented dead ends.

## How we work

1. **Reconstruct before reimagining.** Each classic model is first rebuilt as
   faithfully as the published record allows. Fidelity means agreeing
   quantitatively with the published figures and tables, not just looking
   similar. Each reconstruction records every interpretive choice the paper
   left open.
2. **Then branch.** Variants live beside the faithful version and are
   labelled as departures from it.
3. **A tree, not a pipeline.** The repository is organised so that
   independent ideas can grow without entangling each other (see
   [Structure](#structure)).
4. **Open from the first commit.** Code is MIT and text, figures and data are
   CC BY-SA 4.0. Correspondence between Barry, Claude and Codex is published
   as reviewed snapshots.

## A lineage of models to reconstruct

These models are successive attempts at the habitability question. Rebuilding
them in sequence gives a reproducible lineage in which each one makes the next
easier to understand. Citations are from memory unless marked verified, and are
checked against the source when each model is started.

| Model | Question it asked | What reconstructing it buys us | Status |
|---|---|---|---|
| Daisyworld: Watson & Lovelock (1983), *Tellus B* 35, 284–289 (verified) | Can life regulate climate without foresight? | The minimal feedback logic | **Reconstructed** (Figs 1b–d and 2 agree on occupied branches and transitions; cause of Fig. 1a discrepancy unresolved): [`models/daisyworld`](../models/daisyworld/README.md) |
| Budyko (1969) and Sellers (1969) energy-balance models | When does ice-albedo feedback run away? | Bistability, snowball Earth | Candidate |
| Walker, Hays & Kasting (1981), *J. Geophys. Res.* 86, 9776–9782 (verified via the 1983 reference list) | Can silicate weathering offset the faint young Sun? | The abiotic thermostat | Candidate |
| Lovelock & Whitfield (1982); Caldeira & Kasting (1992) | How long can the biosphere last? | The thermostat's end-game | Candidate |
| GEOCARB (Berner), COPSE (Bergman, Lenton & Watson 2004), SCION (Mills et al. 2021) | What did Phanerozoic CO₂ and O₂ do? | Proxy-constrained Earth-system models | Candidate |
| Goldblatt, Lenton & Watson (2006) | Why did O₂ jump rather than creep? | Oxygen bistability at the Great Oxidation Event | Candidate |

A novel simulation of our own should grow out of the gaps this lineage
exposes, rather than being designed up front.

## Daisyworld: reconstruction and re-imaginings

**Faithful reconstruction (first build).** Reproduce Figs 1a–d and 2 of
Watson & Lovelock (1983) quantitatively:
- parameters: albedos 0.25 (black daisies), 0.5 (bare ground) and 0.75 (white
  daisies); parabolic growth with its optimum at 22.5 °C; death rate γ = 0.3;
  flux S = 917 W m⁻²; heat-transfer parameter q′ = 20 K;
- method: integrate to steady state at each luminosity, sweeping luminosity up
  and down to expose hysteresis;
- record the interpretive choices: seeding rule, extinction threshold, step
  size and steady-state criterion.

Fidelity is measured against the published figures, digitised.

**Re-imaginings**, roughly in order of interest:

1. **Archean haze-world (agreed next build).** Explore methane-mediated
   climate feedback with finite biological production and atmospheric loss.
   Haze is a photochemical product of the same methane; it is not a second
   biological guild. Published climate responses include both warming and
   cooling, conditional on the background atmosphere and haze treatment.
   First recover those responses, then attach a biological budget. The
   [Arney et al. (2016) response family](../models/haze_response/README.md)
   is extracted at its fixed 2.7-Ga conditions. A [first coupled
   model](../models/haze_world/README.md) has an exact equilibrium elimination
   and an approximate scalar dynamics. Under its assumed biological and loss
   budget, stable equilibria can lie near the methanogens' net-growth threshold
   without climate extrapolation. The full ODE has distinct transients and
   basin limits. Separate Eager-Nash low-methane checkpoints are recovered;
   a matched Arney loss law and missing climate branch remain unavailable.
   Methane storage, loss and solar evolution need further evidence or explicit
   assumptions. An [adaptive-dynamics
   preview](../models/haze_world/evolution-scope.md) found that unconstrained
   selection on the thermal optimum removes the threshold equilibrium and
   leaves the passive climate when peak growth is fixed. The
   [independent review](../models/haze_world/review/evolution-review-2026-11-09.md)
   shows that a growth trade-off can retain a contrast under other increasing
   methane losses. The open question is which physiological and chemical
   constraints leave a temperature signal, and whether it regulates climate
   against changing conditions. The stage-1 variant answers part of this.
   Buffering against supply changes survives in two cases: with a
   hotter-is-better trade-off when methane loss rises weakly with abundance,
   and with a hard optimum floor high enough to become the set point. Both
   cases also open a cold trap unless the methane-free climate is warm.
   An [independent stage-1 review](../models/haze_world/review/darwinian-review-2026-11-09.md)
   confirmed the endpoint and stability calculations; the local supply
   responses and re-invasion thresholds have since been corrected to its
   analytical audit.
   A strain-resolved stage 2 adds mutation and explicit extinction. When
   supply declines, the haze clears and the planet passes back through the
   warm peak, so the methanogens' danger is heat rather than cold. Survival
   depends on whether the mutation supply can keep pace. The first H runs
   suggested evolutionary stranding, but an
   [extended review](../models/haze_world/review/strains-review-2026-11-09.md)
   found that all tested cold-baseline H cases eventually collapse, including
   the low-mutation controls: the final supply cannot support a stationary
   living state under the assumed bridge. Census and trait-grid choices
   change collapse times. Separate seed controls show that new mutations can
   rescue an initially declining clone; zero reproduction and total
   extinction are stronger barriers than negative net growth.
   This direction may lead to a paper.
2. **Evolving daisies.** Give the daisies a heritable optimum temperature and
   test whether regulation survives natural selection, the core of the
   critique by Robertson & Robinson (1998) and the replies from Lenton (1998)
   and others.
3. **Snowball Daisyworld.** Couple daisies to Budyko–Sellers ice-albedo
   feedback. Does biology widen or narrow the range of luminosities with no
   stable ice-free state?
4. **Spatial Daisyworld.** Run the model on a latitudinal grid or as a
   cellular automaton (von Bloh et al. 1997 and successors), which brings in
   pattern formation and spatial refugia.

Background reading: Wood et al. (2008), "Daisyworld: a review", *Reviews of
Geophysics*; Lenton & Lovelock (2001), "Daisyworld revisited"; Lenton et al.
(2018), "Selection for Gaia across multiple scales", *Trends in Ecology &
Evolution*; Tyrrell (2013), *On Gaia*.

## Languages and outputs

Decided 8 November 2026. Barry: "Python sounds right to me too, with Julia and
perhaps other languages (e.g., TS/Vite for a browser version?) being optional
for later work if we want to do more elaborate visualisations."

- **Python with `uv`** for core models. It runs on all of Barry's machines and
  is easy for both agents to work in.
- **Julia**, optional later. The PALEO framework already holds COPSE in Julia,
  which may matter for the carbon-cycle models. Julia is installed only on
  `mini`.
- **TypeScript/Vite browser explorers**, optional later. Daisyworld-class
  models are cheap enough to run live in the browser, so interactive
  explorers (luminosity slider; toggles for evolution and ice) are a natural
  way to communicate them.
- **Commodore 64 BASIC versions** of some of the early classic models, for the
  pleasure of running them on period-style hardware (Barry: "a C64 BASIC
  version of some of the early classic models would be fun"). Tokenise with
  `petcat`, validate in VICE, and save the THEC64 Mini for final hardware
  confirmation.

## Structure

- `src/terra_prisca/<model>/`: Python code, one subpackage per model family.
  Shared physics moves into a common module only when a second model needs it.
- `models/<model>/`: the human-facing page for each model family, covering the
  source, equations, interpretive choices, fidelity report, figures and
  variants.
- `tests/`: analytical and regression checks.
- `docs/`: this vision, decisions and correspondence snapshots.
- `local/`: untracked working material (source PDFs, scratch output).

## Open threads

- Explain the 1983 Fig. 1a discrepancy (see the Daisyworld page).
- Choose the haze-world's radiative scheme: a parameterised fit to published
  1D photochemical and climate results, or something more mechanistic.
- Decide whether the Budyko–Sellers energy-balance model comes before or after
  the haze-world, since the haze-world may need ice-albedo feedback anyway.
