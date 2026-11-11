## Fable 5.2 review

I've finished reviewing the core model, ledger and physiology evidence, and I'm now running targeted checks on the most fragile claims, starting with whether the "locally stable" thermostat holds up under thermal inertia.

The thermostat model only turns unstable once thermal inertia exceeds about two months; I reproduced their 119.6-year mode first, then added the lag. Next I'll work through the turnover, finite-population, dormancy and evolution stages.

The robustness sweep is done: the crossing's orientation holds, but its existence on the climate branch does not, at 31% of the team's MSB grid. I'm propagating the published uptake-kinetics uncertainty next, then reading the dormancy and survival code.

Claim C07 reproduces exactly, with methanogens dropping below one global cell at 18.335 years. Next I'm building a small multi-habitat test to see whether varied habitat temperatures remove the instability and the extinction bottleneck.

A spread of ±3–6 K in habitat temperatures removes the lag instability and the population crashes, though the temperature now drifts with supply. I'm fixing a numerical guard next to finish the invasion case.

Checking literature now: verifying each DOI against Crossref's registered metadata (several I recalled from memory were wrong, so I'm resolving them by title search instead).

Literature mostly resolved and verified. Final checks now: acetate-fate evidence, whether the team already discussed thermal lag, and the ledger's own reproduce commands — then I write the report.

The review is written: [review-claude-fable-5-2.md](docs/reviews/haze-world-2026-11/review-claude-fable-5-2.md), with the scripts behind every verified finding in `review-claude-fable-5-2-checks.zip` beside it.

**Verdict.** The numerics are sound, but the work is not ready to write up under its current thesis. Everything I recomputed matched the ledger to the printed digits (C05, C06, C07, C20), and all 843 tests pass. The problem is that the headline results all rest on one idealisation the experiments never relax: every microbe lives at the instantaneous global-mean temperature.

**The two findings that matter most (both verified by running the repository's own model functions):**

- **Thermal inertia destabilises the thermostat (R1).** With a temperature lag longer than about two months (f = 0) or about a year (f = 0.5), the "locally stable" mixed state becomes unstable. At a 3-year lag, a 0.1% disturbance grows until acetogens fall below 10⁻²⁵ global cells within 12,000 years, while temperature moves only ±1 K.
- **A spread of habitat temperatures removes both the fragility and the set point (R2).** With nine habitats spread ±3–6 K:
  - the lag instability vanishes and both guilds stay above 10²⁵ cells;
  - the temperature is no longer pinned at 281.5 K and slides 5–10 K across the supply band.

  With a wider spread (±10 K for displaced methanogens, ±18 K for displaced acetogens), the invasion bottleneck disappears as well. So the need for "memory" is created by the single-temperature assumption.

**Three conditions that belong in the thesis:**

- **Narrow physiological window (R3).** The restoring crossing lies on the climate branch in 31% of the team's own MSB parameter grid. The dimensionally consistent capacity ratio (0.38 rather than 0.74) puts it just off the branch.
- **Acetate sink (R4).** The thermostat regulates supply over a factor of only about 1/f: 2.0 at f = 0.5 but 1.05 at f = 0.98, and the repository's own evidence points to f near 1.
- **Open hydrogen budget (R5).** Hydrogen leaves to an atmosphere held at zero H₂, with no return from methane photolysis. This one is argued, not run.

**What holds up or is understated:**

- The acetogen-cold orientation is robust.
- The crossing survives all 4,000 draws from the published uptake-assay uncertainty, which puts the set point at 281.5 ± 1.4 K.
- The same set point appears on Arney cases A and C.
- The MSP strain gives a more robust thermostat than the chosen reference; it was dismissed only because the scan window stopped 0.3 K short.

**Story.** I recommend one paper, reframed around competitive replacement as an integral controller and what a real planet does to it, with memory as a secondary result. The mechanism has direct precedents the synthesis does not cite (integral rein control, chemostat competition theory, inertia-driven oscillation in Daisyworld). The report lists about 55 references; every DOI was checked against Crossref, and the one book, one proceedings paper and two recollections I could not verify are flagged.

**Limits of this review:**

- I am an Anthropic model, like the designer, so my agreement is weaker evidence than the other reviewer's.
- I did not rerun the long producers or recompute stages 1–2, the refuge, bottleneck and dormancy inventories, or the evolution maps.
- The raw trajectories under `local/` were not available.
- My new experiments are reviewer diagnostics (one solver, nine boxes), not qualified runs.
