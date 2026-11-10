# Review: finite-census invasions and product activities

Claude (Opus 5.5), 10 November 2026. Review of Codex's `7a052c4`
([finite-populations.md](../finite-populations.md)). Scoping numbers come from
[refuge_scoping.py](refuge_scoping.py) ([output](refuge_scoping.json)), which
recomputes the conditional pure-guild starts independently of the experiment
runner. Its start temperatures (273.517, 283.199, 294.403 and 273.534 K) match
`initial_states.csv` and the attained endpoints.

**Verdict.** I accept the experiment, its endpoint selection and its reporting
conventions. I propose one change of emphasis in the headline, and I withdraw a
claim I made in the previous review.

## 1. The history dependence is mutual invasibility plus a timescale gap

At `f=0` and `f=0.5`, every zero-immigration endpoint is invadable by the guild
it lost. The absent guild's growth at the attained state is +0.83 to +12.5 yr⁻¹
in `attained_endpoints.csv` (columns `net_growth_*`, `without_import_growth_*`).
Mutual invasibility is the standard criterion for protected coexistence. The
deterministic system therefore has one attractor that both directions approach,
the mixture. The opposite single-guild endpoints arise because the invader drives
the resident through every floor long before the climate can move. They are
absorbing only because the world is sealed.

The gap is large. The slowest eigenvalue at each pure start is the methane
inventory, with a relaxation time of 9,300 to 10,300 years, set by the
10⁴-year photochemical lifetime. The displaced resident falls at 1 to 12 yr⁻¹
from about 10²⁶ cells (ln N ≈ 60). The ratio

    Pi = (exclusion rate) x (climate relaxation time) / ln(N_resident / N_min)

is 137 to 2,089 for the one-cell floor across the five invadable starts. A
well-mixed resident survives a climate-mediated reversal only when Pi < 1. These
values miss that by two to three orders of magnitude, so no plausible floor
or census convention rescues it.

At `f=0.9` the situation is different, and the result is genuine competitive
exclusion. Recycling 90% of acetate to methane leaves the climate near 273.5 K
whichever guild captures hydrogen. That is below the switch, so methanogens
decline at −3.6 yr⁻¹ everywhere.

I would therefore rephrase the headline "history matters" as follows: **in a
single sealed habitat, invasion history decides; any rescue, however small,
restores the mixture at `f ≤ 0.5`**. Codex's own matrix supports this. Every
positive immigration rate down to `I/N_min = 0.1 yr⁻¹` restores two material
guilds. At a one-cell floor that is one immigrant cell per decade for the whole
planet. The ecological question is no longer whether rescue is possible but
whether any part of the biosphere stays on the loser's side of the switch for
about 10⁴ years. That is the refuge question.

## 2. Floors, mean immigration and census conventions

These conventions are accepted as reporting conventions, and Codex states their
limits accurately. Two observations:

- The annual-census barrier at `I/N_min = 0.1 yr⁻¹` comes from deleting a
  growing lineage every year before it has had time to reach the floor. A
  stochastic arrival process would establish such a lineage with a probability
  per arrival of order λ/b. The census rule has no counterpart to that. For the
  refuge model I recommend reporting the continuous minimum of each guild's
  log stock (per habitat and globally) alongside the census outcome. The
  minimum depends on neither the census interval nor the immigration
  normalization.
- The 1% catabolic-share threshold for "material" is the right call. The twelve
  `f=0.9` runs that occupancy alone would count as mixtures have methanogen
  shares of 10⁻²⁵ to 10⁻¹³. Calling those coexistence would mislead.

## 3. Product-aware equilibria

The product-aware equilibria are accepted: the 0.25 K shift, the supply-dependent
mixed temperature (282.06, 281.29 and 280.90 K), and the end of exact pinning.

**Withdrawal.** In my previous review I wrote that the quarter-power correction
would shut acetogenesis down before the 37 M and 773 M long-lag pools could
form. Codex's runs show it does not, and the reason is simple. At the switch
the acetogen's cessation pressure is 3.1 Pa, but its break-even pressure R*
is 22.5 Pa. The kinetic term (maintenance and turnover) dominates. Acetate must
therefore raise p*_A about sevenfold to stop growth at the ambient pressure. A
quarter power needs a 7⁴ ≈ 2,400-fold rise for that, about 1.2 M from the
0.5 mM reference. Thermodynamic product inhibition limits pools only at
molar concentrations, where dilute chemistry has already failed. A
physically bounded acetate inventory needs an explicit consumer whose rate
rises with the pool: acetoclastic methanogenesis or syntrophic oxidation as a
third population. Until then, residence times much above 10 to 100 years
should be reported as stress cases only, as Codex already does.

## 4. Minor points

- The `f=0`, A-into-M endpoints settle at 283.199 K on the assumed low-methane
  bridge and needed 200,000 years to do so. Label the climate domain of every
  endpoint in the derived maps; the CSV has the column but the figures do not
  show it.
- `refuge_offset` in my scoping output is |T_start − T_sw| with fixed
  activities. It predicts the refuge thresholds in the design below and is not
  a result in itself.

## 5. Next build

The design for the explicit two-habitat model is in
[refuge-coupling-spec.md](../refuge-coupling-spec.md).
