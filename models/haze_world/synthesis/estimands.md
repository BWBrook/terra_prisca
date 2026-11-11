# Haze-world estimands

Claude (Opus 5.5), 11 November 2026. This file says what each haze-world
result estimates, and which phrasings it supports. It sits upstream of
[synthesis.md](synthesis.md) and any brief, article or agent guide made from
it. Codex agrees or amends it before any product cites it. Claim IDs refer
to [claims.csv](claims.csv).

Every result below is conditional on four shared assumptions. Name them
once in any product, and again wherever a result depends on one more than
usual:

1. **Climate.** The quasi-static Arney et al. (2016) case-B response at
   2.7 Ga. The low-methane bridge and the high-methane plateau are ours.
2. **Physiology.** The reference acetogen and hydrogenotrophic methanogen
   parameters, including the continuation below 4 °C.
3. **Habitat.** Habitat volume, donor supply, product activities and the
   10,000-year methane lifetime are normalisations, not Archean estimates.
4. **Turnover.** Both guilds share one constant loss rate `L`.

## E1. Set point (C01, C06, C12)

**Estimand.** The temperature of a locally stable equilibrium of the
deterministic model, and its contrast with a matched control.

- **Allowed:** "in the model, the mixed community holds the climate near
  281.5 K, 8 K warmer than a methanogen-only world"; "turnover sets the
  set point".
- **Not allowed:** "the Archean surface was 281 K"; "acetogens warmed the
  early Earth by 8 K"; "the model predicts Archean temperature".

## E2. Regime map (C12, C13)

**Estimand.** The stable equilibria at each `(L, f)` and the root-located
boundaries between regimes. Basins are known only for the checked starts.

- **Allowed:** "bistable above `L = 1.24×10⁻³ h⁻¹` at `f = 0`".
- **Not allowed:** "the only attractors"; any statement about global
  attractors from the map alone. The `f = 0.9` continuum relaxation cycle
  stays out of every finite-population claim.

## E3. Finite outcomes (C07, C08, C09)

**Estimand.** Endpoints of the deterministic model with a one-cell,
ten-year census and no outside immigration.

- **Allowed:** "invasion history selects the surviving guild under the
  census rule"; "competitive exclusion outruns the climate response".
- **Not allowed:** "climate bistability" for C07, because the continuum
  equations have one stable mixed state; "refuges existed in the Archean".

## E4. Survival probability (C10, C11, C16, C17)

**Estimand.** The probability that one guild survives the first window of
a recorded, uncensored environment, under the stated birth–death split and
cell-count conversion.

- **Allowed:** "50% first-window survival needs about 230 cells at the
  minimum".
- **Not allowed:** a joint probability for both guilds; probability of a
  common endpoint; survival over later windows or many cycles (see E9).

## E5. Seed-bank rule (C17, C18)

**Estimand.** The dormant mortality at which first-window survival crosses
one half, and its approximation `ε* ≈ ln(N₀/N₅₀)/(Lτ)`.

- **Allowed:** "a half-life near 1.3% of the unfavourable interval, for
  the entering population here"; "approximate agreement (within 0.99–1.17
  of the prediction)".
- **Not allowed:** "exact"; "a universal 1.3% rule"; "dormant cells do not
  affect the climate path" (entry and waking do, through the active
  stocks). C25 records the superseded "exact" wording.

## E6. Harmful dormancy (C19, C28)

**Estimand.** The overshoot minimum under the growth-triggered cubic
switching law, with dormant death `εL`.

- **Allowed:** "short-lived dormancy deepened a mild competitive bottleneck
  in this model"; "growth-triggered entry is a strong assumption".
- **Not allowed:** "dormancy is harmful"; "the threshold is `ε = (L−g)/L`"
  as a coupled-system law. It is a fixed-environment allocation argument.

## E7. Oscillation (C20, C21, C22, C27)

**Estimand.** The linear mode of the reference mixed state, plus finite
trajectories observed from specific starts.

- **Allowed:** "the model thermostat is weakly damped (period about
  120 years)"; "some invasion paths kept cycling beside a stable
  equilibrium under cubic switching".
- **Not allowed:** "limit cycle", "attractor", or "basin" for the dormancy
  cycles; "Archean climate oscillated on a 120-year period"; "linear
  switching removes the cycles", since two controls are unresolved.

## E8. Endpoint state (C23, C26)

- **Allowed:** "macrostate stationary, dormant bank unresolved".
- **Not allowed:** "settled"; "banks decaying at `εL`" (refuted, C26).

## E9. Repeated bottlenecks (C24)

- **Allowed:** "a small conditional one-cycle hazard".
- **Not allowed:** "survives millions of cycles", unless a regeneration
  argument or coupled demographic calculation supports it.

## E10. Coexistence versus regulation (C14, C15)

Report global coexistence and bulk regulation as separate quantities in
every refuge result. A guild that persists only as an immigrant-supported
sink does not regulate the climate.

## E11. Single-guild precursor (C01–C04)

**Estimand.** Equilibria and adaptive-dynamics endpoints of the one-guild
budget model.

- **Allowed:** "evolution erases a tolerance-edge thermostat unless a
  constraint sets the edge".
- **Not allowed:** extending C02 to the two-guild switch. Whether selection
  erases a competition-set point is untested (synthesis, open question 2).
