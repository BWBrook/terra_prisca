# Haze-world estimands

Claude (Opus 5.5), 11 November 2026. This file says what each haze-world
result estimates, and which phrasings it supports. It sits upstream of
[synthesis.md](synthesis.md) and any brief, article or agent guide made from
it. Codex agrees or amends it before any product cites it. Claim IDs refer
to [claims.csv](claims.csv).

Codex (GPT-6) amended the interpretation scopes after independent checks on
11 November 2026. Each result is conditional on its **named model version**;
the precursor and competition models do not share identical physiology.

1. **Climate.** Temperature follows the extracted Arney response **instantly**,
   with the declared
   low/high-methane closures. C01 pools cases A–D; later competition results
   use case B. These are fixed-background experiments, not an evolving Earth.
   Every old stability result is conditional on this closure. Temperature
   response slower than the critical lag destabilizes the fixed-product reference;
   the external-review revision tests its physical realisation separately.
2. **Physiology.** The precursor uses an assumed thermal growth curve. The
   competition model uses transferred acetogen/methanogen kinetics, yields
   and maintenance, with named below-4 °C continuations. The reference
   methanogen/acetogen capacity ratio is a transferred scenario, not a
   dimensionally recovered calibration. Its alternative dry-mass value
   can move the crossing off the extracted cooling branch.
3. **Budgets and habitat.** Donor supply, habitat volume, product activities
   and methane loss are scenario assumptions. The competition baseline has
   a 10,000-year lifetime; precursor evolution also tests other loss shapes.
   Local hydrogen exits to a prescribed zero-H₂ atmosphere, without
   photochemical hydrogen return. The atmosphere's hydrogen/redox budget is
   open. Pinning through acetate routing requires a non-methane acetate sink;
   differential permanent biomass export can leave a narrow pinning band even
   at complete acetate recycling. The source record does not estimate the
   Archean recycling fraction.
4. **Turnover.** The competition experiments assign both guilds the same
   constant loss rate `L`. Its effects do not establish that physiology or
   adaptation cannot also move or remove the competitive crossing.

## E1. Set point (C01, C06, C12)

**Estimand.** The temperature of a locally stable equilibrium of the
deterministic model, and its contrast with a matched control.

- **Allowed:** "in the model, the mixed community holds the climate near
  281.5 K, 8 K warmer than a methanogen-only world, under instantaneous
  temperature"; "joint physiology selects the break-even resource crossing;
  changing turnover moves that crossing under fixed remaining parameters".
- **Not allowed:** "the Archean surface was 281 K"; "acetogens warmed the
  early Earth by 8 K"; "the model predicts Archean temperature".

## E2. Regime map (C12, C13)

**Estimand.** The stable equilibria at each `(L, f)` and the root-located
boundaries between regimes. Basins are known only for the checked starts.

- **Allowed:** "at `f=0`, stable mixed and acetogen-only equilibria coexist
  between the stated lower and upper boundaries". Report the separate
  pure-guild bistability interval and the assumed climate branch.
- **Not allowed:** treating the lower onset as bistability at every larger
  turnover. The mixed set-point range refers to root-delimited branch
  limits, not the extrema of the original sampled grid.
- **Not allowed:** "the only attractors"; any statement about global
  attractors from the map alone. The `f = 0.9` continuum relaxation cycle
  stays out of every finite-population claim.

## E3. Finite outcomes (C07, C08, C09)

**Estimand.** Endpoints of the specified finite-census variant, with its
stated removal threshold, census interval and immigration. C07's history
contrast is the closed single-habitat `f=0/0.5` comparison, not every
recycling fraction or immigration setting. C08's limitation concerns the
tested mean-preserving, climate-tracking geometry at those fractions;
other recycling settings include supported coexisting counterexamples.

- **Allowed:** "invasion history selects the surviving guild under the
  census rule"; "competitive exclusion outruns the climate response".
- **Not allowed:** calling C07's distinct absorbing census outcomes
  "climate bistability": absorption does not establish two stable continuum
  climates. Assess continuous equilibria and invasion stability separately.
  Also unsupported: "refuges existed in the Archean"; "all climate-tracking
  refuges fail"; "all buffered-refuge runs reach the same mixed state". C09's key paired rescue result concerns its
  specified subset, not the entire experiment. Refuges and dormancy are
  sufficient to protect in some tested transients, not universally.

## E4. Survival probability (C10, C11, C16, C17)

**Estimand.** The probability that one guild survives the first window of
a recorded, uncensored environment, under the stated birth–death split and
cell-count conversion.

- **Allowed:** "50% first-window survival needs about 230 cells at the
  minimum in the specified bottleneck". Distinguish the exact multitype
  calculation from the single-type identity and its approximate reduction.
  The minimum is global across habitats, including runs with a small refuge;
  a global count must not be described as the count inside that refuge.
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
  Subcell minima describe continuum expectations; a deeper minimum does not
  show a change in finite fate when both paths already imply likely loss.

## E7. Oscillation (C20, C21, C22, C27)

**Estimand.** The linear mode of the reference mixed state, plus finite
trajectories observed from specific starts.

- **Allowed:** "with instantaneous temperature and fixed products, the
  `f=0` mixed state is weakly damped (period about 120 years)"; "some invasion
  paths kept cycling beside a stable
  equilibrium under cubic switching".
- **Not allowed:** "limit cycle", "attractor", or "basin" for the dormancy
  cycles; "a physically delayed climate retains that stability";
  "Archean climate oscillated on a 120-year period"; "linear
  switching removes the cycles", since two controls are unresolved.

## E8. Endpoint state (C23, C26)

- **Allowed:** "macrostate stationary, dormant bank unresolved".
- **Not allowed:** "settled"; "banks decaying at `εL`" (refuted, C26).

## E9. Repeated bottlenecks (C24)

- **Allowed:** "a small conditional one-cycle hazard".
- **Not allowed:** "survives millions of cycles", unless a regeneration
  argument or coupled demographic calculation supports it.

## E10. Coexistence versus regulation (C14, C15)

Report global coexistence, methane supply, autonomous bulk competition and
restorative regulation separately. A sink can emit methane and influence
global temperature while contributing negligible bulk competitive activity.
C14's 0.28 K is a refuge-only forcing diagnostic above the switch, not the
width of a coexistence window or the temperature difference of two full
endpoints. C15 establishes weak bulk participation and failure to pin the
bulk at its switch; it does not establish zero climate effect.

## E11. Single-guild precursor (C01–C04)

**Estimand.** Equilibria and adaptive-dynamics endpoints of the one-guild
budget model, plus the specified strain-resolved supply-decline trajectories.
Unconstrained fixed-peak adaptation, a hard optimum floor and a growth-rate
trade-off are different scenarios.

- **Allowed:** "unconstrained optimum evolution with fixed peak growth
  erases the tolerance-edge signature in these experiments". A hard floor
  can restore buffering, while the growth-rate trade-off can retain it under
  shallow methane loss without a floor. C04 concerns fixed-optimum,
  no-mutation unconstrained strains dying during warming on the way to the
  greenhouse peak; it is not mortality of all methanogens at the peak.
- **Not allowed:** extending C02 to the two-guild switch. E13 now reports
  the restricted competitive-kinetics evolution test; it can shift, remove
  or retain a crossing. Neither family establishes a general response to
  selection on all physiological traits.

## E12. Persistence through displacement (C07, C09, C17)

**Estimand.** Retention or rescue of a losing guild through the specified
invasion transients. Refuges and dormancy are two mechanisms that can bridge
rapid population decline and slow climate adjustment in this model.

- **Allowed:** "a single-temperature competitive climate thermostat can
  need biological memory during an invasion"; "an equilibrium can exist while an invasion fails to
  reach it in the finite-census variant".
- **Not allowed:** a theorem that every competitive thermostat requires a
  refuge or dormant bank, or that either mechanism guarantees a common
  endpoint. The no-refuge/no-dormancy mixed equilibrium has a stable positive
  neighbourhood under the reference dynamics and can persist without an
  extra store when it starts there. Immigration is another rescue mechanism.
  Per-guild first-bottleneck survival does not establish joint recovery.

## E13. Competitive kinetic evolution (KE1–KE7)

**Estimand.** Best-response kinetic positions within the measured 4–30 °C
trait interval, their feasible joint trait–climate equilibria, frozen-trait
five-stock ecological stability with instantaneous temperature, and evolutionary convergence under the
specified per-cell mutational-supply ratios. S4 concerns rare-mutant growth
in each fixed resident environment. The
[implementation choices](../competitive-evolution-methods.md) distinguish
smooth, corner and projected boundary cases.

- **Allowed:** "within the stated kinetic family, adaptation shifted,
  removed or preserved a feasible competitive crossing", according to the
  recorded results; "no grid mutant had positive growth beyond the declared
  tolerance at the checked community".
- **Not allowed:** identifying a static pressure crossing with a feasible
  or stable climate equilibrium; inferring a methanogen-only world without
  checking its ecological state and invasion fitness; calling a numerical
  centered derivative at a corner a canonical Jacobian.
- Both guilds share the same Arrhenius parameter E in C29–C37. Unequal
  constraint strengths can reverse the competitive feedback; the common-E
  grid does not establish resistance to that change.
- Thresholds, maintenance, yields, turnover and the Arrhenius parameter E
  do not evolve in this family. Their non-evolution is a model assumption,
  not proof of a fundamental evolutionary constraint. The rate multiplier
  is phenomenological and does not calibrate a biological cold-adaptation
  cost. Actual temperatures below 4 °C use the named reference continuation;
  traits below 4 °C are excluded.
- The prescribed S2 controls freeze functions at 30 °C and change their
  levels as well as their slopes. Disappearance in such a control does not
  by itself establish which temperature dependence is necessary. Any extra
  matched-value or slope decomposition is a separate diagnostic and does
  not replace the fixed KE predictions.
- Canonical time and relative mutational supply are uncalibrated. A branch
  lost during continuation is not a measured extinction event. S5 must state
  when the assumed ecological branch stops existing or being stable.
- **Not allowed:** "evolution cannot break the thermostat"; "thermodynamics
  makes the Archean set point evolutionarily stable"; generalizing this
  trait family to selection on maintenance, yields or cessation energetics.
