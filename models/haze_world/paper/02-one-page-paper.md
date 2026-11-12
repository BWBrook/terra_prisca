# Step 2: the one-page paper

Claude (Opus 5.5), 12 November 2026. Built from Step 1
([1a](01a-working-abstract.md), [1b](01b-abstract.md),
[1c](01c-display-items.md)). The claim IDs it rests on are listed at the
end. Revised by Codex (GPT-6) for accuracy, then by Claude for plain style,
12 November 2026.

---

## Perfect microbial climate control is fragile; slightly imperfect control endures

**Introduction.** Can life regulate its planet's climate? Daisyworld showed
that it can in principle (Watson & Lovelock 1983). Real climates respond
slowly, because oceans store heat. A delayed response can destabilise
feedback. We ask how a slow climate response affects a microbial
thermostat, and what durable regulation costs in temperature precision.

Our test case is inspired by the hazy early Earth:

- A steady hydrogen supply feeds the microbes.
- Methanogens turn hydrogen into methane. At high methane levels, sunlight
  converts methane into an organic haze that cools the surface (Arney et al.
  2016).
- Acetogens compete for the same hydrogen and make acetate. Part of that
  acetate is later recycled into methane.
- Temperature decides which group grows faster, closing the loop.

**Model.** We couple the two groups to an open hydrogen budget and to Arney et
al.'s haze climate, with growth parameters taken from cultured strains.
Surface temperature approaches its climate value over a response time τ. For
each steady state we compute three things:

- its temperature T\*;
- its local sensitivity S, the temperature slope against proportional
  changes in hydrogen supply;
- its critical response time τ_c, when the steady state first loses
  stability as the climate response slows.

We then turn up two features from zero:

- acetate slowing its own producers;
- habitats that differ slightly in temperature and exchange cells.

Invasion simulations count a group as extinct when its population falls
below one cell.

**Perfect control.** In the reference case, the two groups coexist where their
hydrogen requirements match, at 281.5 K. A change in supply shifts the balance
between them and leaves temperature fixed (S = 0). This is the plateau
mechanism of Seto & Akagi (2007). Growth-rate differences keep shifting the balance between the
groups. Near coexistence, this acts like integral feedback, the
mechanism behind exact adaptation in cells (Yi et al. 2000).

**Fragility.** We found 42 perfectly holding states. Six are unstable outright,
and the other 36 first lose stability at response times of about 7 years or
less. The reference state loses stability at 0.15 years. At a 1-year
response time it keeps both groups alive for 30,000 years while temperature
swings span about 1.3 K; at 10–100 years the calculations reach populations
below one cell.

**The price of durability.** The two features let temperature follow supply
slightly, and that small sensitivity buys a large gain in stability. The
gain grows smoothly near the perfect-control limit on the tested branches.

- On all four tuned branches, 0.07–0.32 K per e-fold of supply buys
  tolerance of a 30-year response.
- Sensitivities of 1–2 K buy centuries or more.

**Arrival order.** In all 24 invasion runs, the invader drove the resident
extinct, including where a stable mixture of both groups exists. The order of
arrival chose the surviving group.

**Discussion.** Graded feedback makes a competitive microbial regulator far
more tolerant of slow climate, and its small residual sensitivity is the
measurable price. Measuring both sensitivity and response time in other
microbial and ecological feedbacks would show how widely this trade-off
holds. The invasion result opens a separate question: how does a community
assemble into a regulator that is stable once established?

**Scope.** These are results of a conditional model. The temperature switch
depends on how growth capacities transfer from culture. Regulation needs the
two hydrogen pathways to yield different amounts of methane. Physiology is
extended from the lowest measurement, 277 K, down to 273 K. The price of
durability is a local slope on four branches, and stability is local to each
steady state. Invasions run in a single closed habitat, with populations
counted every ten years. Atmospheric hydrogen up to 100 Pa leaves the set
point unchanged.

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
