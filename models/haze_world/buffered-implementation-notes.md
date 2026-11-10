# Buffered refuges: implementation decisions before the main matrix

Codex (GPT-6), 10 November 2026. Implements the specification in `4720c65`.

- The generic N-patch model is a separate named variant. Historical two-patch
  source remains unchanged and is used for exact RHS and trajectory regressions.
- Main and sensitivity designs retain the specified 96 and 72 cases. The
  zero-exchange control is interpreted as each configuration crossed with all
  three acetate fractions and both directions: 24 controls, kept separate.
- Starts are conditional pure-resident equilibria, positive in every active
  habitat and stable with the competing guild disabled. The highest-r stable
  candidate is selected if the finite scalar/seeded search finds several;
  ambiguity is retained. Both habitats receive the same invader density,
  so the weighted global dose stays 10⁻¹² gDW/L. Zero-area habitats are inactive.
- B1/B2 concern the positive low-exchange main cases, not the isolated d=0
  controls. Sensitivities wait until main outcomes have been qualified and B2
  assessed. A discrepancy between finite censused trajectories is not alone
  evidence of multiple stable equilibria in the uncensored ODE.
- The path-extreme result in the preceding review comprises 38 completed
  protected runs and eight protected domain-censored prefixes. It is evidence
  motivating B1, not a general sufficiency theorem. Local culls in different
  habitats at different times do not by themselves imply global extinction;
  the new summaries use simultaneous global absence.
- A low-methane-to-hazy transition crosses the greenhouse maximum. At f=0.9
  the acetogen-only start is already hazy, so the peak argument and B3's
  proposed one-sided history do not automatically apply. The full declared
  grid is retained, including this test of the literal B3 statement.
- B4's cell export to recipient j is d w_j N_source, and the source population
  varies during the transient. The grid tests rescue down to 10⁻⁹/year;
  it does not calibrate or test a universal 10⁻²⁵/year threshold. One/year is
  not automatically rapid relative to every local competitive advantage.
- Buffered temperatures remove radiative dT/dr, while product activities may
  still respond chemically to atmospheric methane. Fixed temperatures are
  imposed habitat conditions, not a closed planetary heat budget or evidence
  that the specified refuge areas existed on Archean Earth.
- The bulk retains the existing cold continuation and low-methane bridge.
  Refuges remain inside the measured window. The exact weighted temperature
  departure is reported rather than used as an energy-conservation claim.
- B5's primary comparator is the matched conditional acetogen-only equilibrium
  at the same refuge configuration. The secondary comparator is the completed
  no-refuge invasion at the same fraction, exchange and activity scheme. This
  distinction was fixed before inspecting the 90%-conversion outcomes; the
  second comparison includes the effect of changing habitat temperatures.

Numerical stock coordinates preserve exact absence and nonnegative inventories.
With exchange, each guild uses total biomass and all N explicit allocations;
no last fraction is reconstructed by subtracting nearly equal numbers.
Dense minima describe accepted numerical flows and explicit census jumps,
not solver trials. Their numerical searches are not interval-certified.
