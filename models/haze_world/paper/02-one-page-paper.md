# Step 2: the one-page paper

Claude (Opus 5.5), 12 November 2026. Built from Step 1
([1a](01a-working-abstract.md), [1b](01b-abstract.md),
[1c](01c-display-items.md)). The claim IDs it rests on are listed at the
end.

---

## Perfect microbial climate control is fragile; slightly imperfect control endures

**Introduction.** Can life regulate its planet's climate? Daisyworld showed
that it can in principle (Watson & Lovelock 1983), and most later work
studies such regulation at equilibrium. Real climates respond slowly: oceans
and ice adjust over years to millennia. Control engineering teaches that
delay destabilises feedback, and the more precise the controller, the more
sensitive it is to delay. We ask whether this holds for a microbial
thermostat, and what durable regulation costs.

Our test case is the hazy early Earth, more than 2.5 billion years ago:

- Volcanoes supplied hydrogen.
- Methanogens turned that hydrogen into methane. At high methane levels,
  sunlight converts methane into an organic haze that cools the surface
  (Arney et al. 2016).
- Acetogens competed for the same hydrogen and made acetate instead.
- Temperature decides which group grows better, so their competition can set
  the planet's temperature.

**Model.** We couple the two groups to an open hydrogen budget and to Arney
et al.'s haze climate, using growth parameters measured in cultured strains.
Surface temperature approaches its climate value over a lag τ.

For each steady state we compute three quantities:

- its temperature T\*;
- its drift S, the change in T\* per e-fold change in hydrogen supply;
- its critical lag τ_c, the longest lag at which it stays stable.

Two features are then turned up from zero:

- **product limitation:** accumulating acetate slows acetogens;
- **spatial spread:** habitats differ slightly in temperature and exchange
  cells.

Finite-population simulations follow each group invading a world held by the
other.

**Perfect control.** With fixed growth requirements, the two groups coexist
only where their hydrogen thresholds match, at 281.5 K. A change in supply
alters the mix of the two groups and leaves temperature unchanged (S = 0),
the plateau Seto & Akagi (2007) found in a closed model. The ratio of the two
groups accumulates the temperature error over time. This is integral
feedback, which holds a set point exactly (Yi et al. 2000).

**Fragility.** All 42 perfectly holding states lose stability at lags of
7 years or less.

- Just past the critical lag, temperature swings by about 1.3 K while both
  populations stay large.
- At lags of 10–100 years, regulation collapses, and each group's expected
  population falls below one cell.

**The price of durability.** Product limitation and spatial spread let
temperature drift slightly with supply, and durability rises continuously
with that drift.

- On all four tuned branches, a drift of 0.07–0.32 K per e-fold of supply
  buys a 30-year margin.
- Drifts of 1–2 K buy centuries or more.
- These regulators still remove 96–98% of an unregulated community's
  temperature response.

**Arrival order.** In all 24 simulated invasions, the invader drove the
resident below a single cell, even where a stable mixed state existed.
Arrival order fixed the surviving community.

**Discussion.** The trade-off between precision and robustness is familiar in
molecular circuits (Qian & Del Vecchio 2018; Olsman et al. 2019). Here it
operates between species, at planetary scale. Exact holding is its fragile
limit, and slightly leaky holding its durable form. Lasting biological
regulators should therefore show a small residual drift with forcing. That
drift is a signature to seek in Earth history and on other worlds. Assembly
history then selects among the durable regulators.

**Scope.** The model is conditional and Archean-inspired. Its conditions
are:

- growth capacities normalised as in culture, which places the switch;
- hydrogen pathways that differ in methane yield;
- physiology defined above 273 K;
- costs measured as local slopes on four tuned branches;
- a one-cell extinction rule.

Atmospheric hydrogen up to 100 Pa leaves the set point unchanged.

**Conclusion.** Microbes can hold a planet's temperature steady, but perfect
control breaks down when the climate responds slowly. Slightly imperfect
control is far more durable.

---

**Claims.**

| Result | Claims |
|---|---|
| Plateau and restoring switch | C05, C06 |
| Fragility | C54 and the B2 transients |
| Price of durability | C55, C57, C54 |
| Arrival order | C52 |
| Hydrogen pressure | C59 |
