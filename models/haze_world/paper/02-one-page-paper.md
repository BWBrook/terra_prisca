# Step 2: the one-page paper

Claude (Opus 5.5), 12 November 2026. Built from Step 1
([1a](01a-working-abstract.md), [1b](01b-abstract.md),
[1c](01c-display-items.md)). The claim IDs it rests on are listed at the
end. Revised by Codex (GPT-6), 12 November 2026.

---

## Perfect microbial climate control is fragile; slightly imperfect control endures

**Introduction.** Can life regulate its planet's climate? Daisyworld showed
that it can in principle (Watson & Lovelock 1983). Ocean heat storage slows
climate adjustment, potentially destabilising a biological feedback. We ask
how that response affects a microbial thermostat, and what durable
regulation costs in temperature precision.

Our test case is inspired by the hazy early Earth:

- Hydrogen enters an inhabited environment.
- Methanogens turn hydrogen into methane. At high methane levels,
  sunlight converts methane into an organic haze that cools the surface
  (Arney et al. 2016).
- Acetogens compete for hydrogen and make acetate. Recycling some acetate
  into methane returns part of that diverted supply.
- Temperature changes which group grows better, closing the feedback.

**Model.** We couple the two groups to an open hydrogen budget and to Arney
et al.'s haze climate, using growth parameters transferred from cultured strains.
Surface temperature approaches its climate value over a lag τ.

For each steady state we compute three quantities:

- its temperature T\*;
- its local sensitivity S = dT\*/d ln Φ, where Φ is hydrogen supply;
- its critical lag τ_c, the first loss of stability as thermal response slows.

Two features are then turned up from zero:

- **product limitation:** accumulating acetate slows acetogens;
- **spatial spread:** habitats differ slightly in temperature and exchange
  cells.

Invasion simulations remove a group when its global population falls below
one cell at a census.

**Perfect control.** With fixed product activities, the reference groups
coexist where their hydrogen requirements match, at 281.5 K. A change in supply
alters the mix of the two groups and leaves temperature unchanged (S = 0),
the plateau mechanism of Seto & Akagi (2007). The log population ratio
accumulates the difference in per-capita growth rates. Near coexistence this
provides effective integral action, connecting the ecosystem to biological
integral feedback (Yi et al. 2000).

**Fragility.** Of 42 exactly pinned states, six are already unstable; the
other 36 first lose stability by about 7.1 years.

- At a 1-year lag, one reference run maintains both groups through
  30,000 years, with late temperature swings spanning 1.3 K.
- At 10–100-year lags, continuous trajectories develop subcell population
  bottlenecks.

**The price of durability.** Product limitation and spatial spread let
temperature respond to supply while greatly widening the stability margin.
The tuned branches approach exact pinning continuously.

- On all four tuned branches, a drift of 0.07–0.32 K per e-fold of supply
  buys a 30-year margin.
- Sampled sensitivities of 1–2 K per e-fold buy centuries or more.

**Arrival order.** In all 24 simulated invasions, the invader drove the
resident below a single cell, even where a stable mixed state existed.
Arrival order selected the surviving guild.

**Discussion.** Graded ecological feedback makes this competitive regulator
far more tolerant of slow climate adjustment. Its small residual sensitivity
is a measurable cost of that robustness. Testing both sensitivity and
response time in other microbial systems would establish how widely this
trade-off applies. The invasion result raises a separate question: can a
community assemble into a regulator that would be stable once established?

**Scope.** These are conditional model results: the chosen capacity transfer
admits the switch; hydrogen pathways differ in methane yield; and physiology
extends to 273 K through a stated continuation below the measurements.
The price is a local derivative on four branches, rather than a finite
forcing response. Stability is assessed locally; subcell continuous
trajectories diagnose bottlenecks. Invasion endpoints use a one-cell census
every ten years in a closed habitat. Atmospheric hydrogen up to 100 Pa leaves
the reference set point unchanged.

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
