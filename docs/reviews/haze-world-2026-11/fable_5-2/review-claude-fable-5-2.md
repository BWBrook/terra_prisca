# External review of the haze-world model

## 1. Header

- **Reviewer:** Claude Fable 5.2 (`claude-fable-5-2`, Anthropic), 11 November 2026.
- **Commit reviewed:** `7294023`, tag `haze-world-review-1`, clean checkout.
- **Time:** about two and a half hours in one session.
- **Independence.** I took no part in building this work. I am, however, an
  Anthropic model, the same developer as the designer (Claude Opus 5.5), so
  treat agreement between us as weaker evidence than agreement with the
  other reviewer. I used no subagents and did not use Codex. I formed the
  views below before opening `docs/correspondence/`; my only contact with it
  was one late search for "thermal inertia / heat capacity", to check that
  finding R1 had not already been dealt with (one hit, restating that
  temperature is quasi-static).
- **What I ran** (scripts and outputs in
  `review-claude-fable-5-2-checks.zip`, beside this file):
  - `uv run pytest`: 843 passed in 141 s.
  - `python3 tools/claims.py check …`: 37 claims, 0 errors, 0 warnings.
  - `synthesis-communities-audit-2026-11-11.py`: runs in under a second from
    committed tables.
  - Independent recomputation, from the public model functions, of the
    reference equilibria and spectra (C05, C06, C20) and the focal invasion
    transient (C07).
  - New reviewer experiments: a thermal lag on the climate closure; nine
    habitats with a spread of temperatures; a parameter-window and
    measurement-uncertainty analysis of the competitive crossing; the supply
    band against acetate fate; the reference biology on Arney cases A–D.
  - Crossref lookups for every DOI in section 5.
- **What I did not run.** The long producers. The 2 GB of raw trajectories
  under `local/` are absent, so I could not check any SHA-pinned raw record.
  I read but did not recompute stages 1–2 (C01–C04), the refuge, bottleneck
  and dormancy inventories (C08–C11, C14–C19, C21–C24) or the evolution maps
  (C29–C37). My statements about those rest on the pages, the code and the
  committed tables.

## 2. Verdict

The numerics are sound: everything I recomputed matched the ledger to the
printed digits, the tests pass, and the prediction–refutation record is
honest. The work is **not yet sound to write up under its current thesis**.
The headline results (a stiff set point, a locally stable weakly damped
thermostat, exclusion that outruns the climate, and a consequent need for
memory) all rest on one idealisation that the experiments never relax: every
microbe on the planet lives at the instantaneous global-mean temperature.
Relaxing either half of it changes the results. With any thermal inertia
beyond about two months the reference mixed state is linearly unstable and,
under the model's own census rule, destroys itself (R1). With a modest spread
of habitat temperatures the instability and the extinction bottleneck both
disappear, and so does the pinned set point (R2). Before writing, run those
two analyses properly, and promote three conditions into the thesis: the
physiological window in which the crossing exists (R3), the non-methane
acetate sink it requires (R4), and the open atmospheric hydrogen budget
(R5). After that I would write one paper, about the competitive thermostat
as an integral controller and what a real planet does to it, with memory as
a secondary result.

## 3. Findings

| ID | Severity | Type | Claims | Finding | Basis | Remedy |
|---|---|---|---|---|---|---|
| R1 | major | correctness; missing analysis | C06, C20, C05; brief items 1, 5 | The mixed state is stable only because temperature follows methane instantly. A first-order thermal lag longer than 0.15 yr (f = 0) or about 1.1 yr (f = 0.5) makes it an unstable focus; at a 3-yr lag a 0.1% kick grows until acetogens fall below 10⁻²⁵ global cells within 12 kyr, with temperature moving only ±1 K. | **verified** (`lag.py`, `lag_nl.py`, `nbox.py lag`; reproduces the 119.57-yr, 4,854-yr mode at zero lag) | Add a heat-capacity state (mixed-layer and deep-ocean time constants) as a named variant; report the stability boundary in (τ_T, f, L). One to two days. |
| R2 | major | scope; framing | C06, C07, C09, C12, C17; E1, E3, E12; thesis | A single habitat temperature produces the stiffness, the fragility and the need for memory together. With nine tracking habitats spread ±3–6 K, the lag instability vanishes and populations never leave 10²⁵ cells, but temperature is no longer pinned: it slides 5–10 K across the supply band. With a spread wide enough to span the invasion transient (±10 K for displaced methanogens, ±18 K for displaced acetogens) neither guild passes through a bottleneck. | **verified** (`nbox.py`; nine boxes, one solver, clipped at the 273–303.15 K physiology limits) | A distributed-habitat variant (latitude bands or a temperature distribution, with seasonal range as a sensitivity), run with R1's lag. Two to four days. Likely changes the thesis. |
| R3 | major | scope or overclaim | C05, C06, C12, C29; brief items 1–2 | The restoring crossing lies on the case-B cooling branch in 76 of the team's own 243 MSB parameter sets (31%). The reference methanogen capacity ratio, 0.74, is the per-culture ratio; the per-dry-mass ratio that matches the model's units, 0.38, puts the crossing at 297.08 K, just above the branch. The orientation (acetogens cold) is robust; existence is not. | **verified** (`robust.py`) | State the window (γ, Y_M, L, f) in the thesis and estimands; add a robustness figure. Hours. |
| R4 | major | scope | C06, C07, C12, C13, C20; all f = 0 and 0.5 results | The thermostat regulates against supply only over a factor of about 1/f: 2.0 at f = 0.5, 1.14 at 0.9, 1.05 at 0.98. Most headline numbers use f = 0 or 0.5, which need half or all of acetate's electrons to leave the methane pathway for good. The repository's own evidence (cold lake sediment making methane from acetate at 4 °C; burial efficiency 0.2–2%) points to f near 1. | **verified** for the band (`fband.py`); **reasoned** for the Archean value | Put the sink requirement in the thesis; name candidate sinks; add a variant in which acetate consumers are explicit or electrons are tracked to burial. Days. |
| R5 | major | missing physics; novelty | general | Hydrogen enters locally and leaves to an atmosphere held at zero H₂; methane photolysis returns no hydrogen and escape does not close the budget. Published Archean ecosystem models do the reverse. The reference supply, 1.5×10¹² H₂ cm⁻² s⁻¹, also implies a biological (fermentative) source, which makes acetate directly. | **reasoned**; flux **verified** (`last.py`) | Either couple a minimal atmospheric H₂–CH₄ redox budget, or argue explicitly why the local-habitat geometry applies. Engage Kharecha 2005, Ozaki 2018, Sauterey 2020. Days to weeks; the discussion is required either way. |
| R6 | major | framing or overclaim | C12; E1; brief item 2 | "Turnover, not a tolerance limit, sets the temperature" misdescribes the mechanism. At the reference the crossing occurs where the methanogen's required uptake m + L/Y approaches its cold capacity (60% of V_max at 4 °C against 13% for the acetogen). That is the classical chemostat crossing between an affinity specialist and a rate specialist, selected by dilution rate. Turnover is one of several quantities that place it and the least constrained. | **verified** decomposition (`last.py`, `robust.py`); **reasoned** framing | Reword E1 and item 2: the set point is the R\* crossing temperature. Cite chemostat theory. Hours. |
| R7 | major | novelty; framing | thesis; C06, C20 | The mechanism is integral rein control: the guild ratio integrates the temperature error, which gives zero steady-state error across the supply band and a marginally damped loop. This is known from the two-daisy Daisyworld and from physiology, and thermal inertia is known to make Daisyworld oscillate. The synthesis cites none of it. | **reasoned** | Reframe around integral control; cite Saunders et al. 1998, Nevison et al. 1999, Weaver & Dyke 2012. Hours. |
| R8 | minor | overclaim | C29–C37; brief item 6 | With E = 0 the evolved uptake kinetics carry no temperature dependence, so the evolved crossing at 277.96 K rests entirely on two assumed laws (fixed-energy thresholds with assumed anchors, shared Arrhenius maintenance). "A set point survives selection insofar as its temperature dependence lies outside the traits under selection" is close to a tautology. | **reasoned** from `evolved_kinetics.py` and C36; **verified** that the reference crossing survives removal of both assumed laws (278.65 K) | Say so plainly; shorten the stage to a section. For a like-for-like test, let cold capacity trade against warm capacity. |
| R9 | minor | overclaim | C18; brief item 4 | The "half-life near 1% of the interval" rule is ln 2 / ln(N₀/N₅₀) = 0.693/54.35: a planetary population can lose 78 halvings. It is arithmetic on exponential decay, not a property of dormancy. | **reasoned** | Present it as that; note it is logarithmically insensitive to habitat volume and cell mass. |
| R10 | minor | documentation; overclaim | C05, C06, C10, C13, C29 | Nine-digit temperatures and a 4.423187496 exponent sit beside a set point whose uptake-assay uncertainty alone is ±1.4 K (95% interval 279.2–284.4 K). | **verified** (`mc.py`) | Keep digits in the ledger for regression; round in every product and give the ±1.4 K. |
| R11 | minor | scope | C05, C06, C12, C20 | Case B's whole cooling branch is four digitised vertices; the reference state sits on one drawn segment with slope about −720 K per unit ratio. The oscillation period, the damping and the bistability boundaries inherit that slope. | **reasoned** from `figure4.csv` | Sweep the local slope (×0.5, ×2) and the methane lifetime (6–19 kyr). Hours. |
| R12 | suggestion | understated | C05, C06 | Two strengths are understated. The same 281.535 K mixed state exists and is stable on Arney cases A and C (at the one supply I tried), so the set point is independent of the climate curve. And the less cold-adapted strain MSP, the one for which the source reports a cold reversal, gives a stable mixed state at 290.285 K and a crossing on the branch in 148 of 148 grid sets where methanogens win when warm. `competition-switches.md` reports "none" for it only because its window stops at 290 K. | **verified** (`cases.py`, `robust.py`, `last.py`) | Show set-point invariance across cases A–C as the regulation result; carry MSP as a second reference. Hours. |
| R13 | suggestion | framing | C21, C22 | The persistent cycles under cubic dormancy switching may be the same delay instability as R1, with the bank acting as the lag. | **suspected** | Check whether cycle onset tracks bank residence time. |
| R14 | minor | reproducibility; documentation | general | The ledger's reproduce commands re-derive numbers from committed tables rather than from the model. "Reference" means f = 0.5 in code but f = 0 for the 120-yr period (153 yr at f = 0.5). `README.md` is an 80-line changelog paragraph. Details in answer 6. | **verified** | A `reproduce-core` script; assumption tags in the ledger; a rewritten README. A day. |

### Evidence for the verified findings

**R1.** I added `dT/dt = (T(r) − T)/τ_T` to the five-stock model and used the
repository's flux functions unchanged. At τ_T → 0 the leading pair is
−2.06×10⁻⁴ ± 0.05255i yr⁻¹ (period 119.57 yr, damping 4,854 yr), as in C20.
The real part crosses zero at τ_T = 0.15 yr for f = 0 and between 1 and 3 yr
for f = 0.5, matching the estimate τ_c ≈ 2γ/ω² for a lagged double
integrator (0.149 and 1.10 yr).

| τ_T (yr) | f = 0: e-folding of growth | f = 0.5 |
|---:|---:|---:|
| 0.1 | stable | stable |
| 1 | 856 yr | stable |
| 3 | 266 yr | 643 yr |
| 30 | 77 yr | 105 yr |
| 300 | 107 yr | 130 yr |
| 3000 | 212 yr | 252 yr |

Integrated from a 0.1% kick at f = 0 and τ_T = 3 yr, temperature after
12 kyr ranges over 280.49–282.61 K while acetogens reach 10⁻²⁵·⁸ global
cells and methanogens 10¹⁵·⁴. At τ_T = 30 yr acetogens pass 10⁻⁴⁰⁰ gDW L⁻¹
within 6 kyr. The amplitude was still growing when I stopped. Under the
one-cell census this is a thermostat that eliminates one of its own
components from an arbitrarily small disturbance. A surface mixed layer
responds over a few years and the deep ocean over centuries, so the stable
regime is not the physical one. The cause is structural: population share
integrates the temperature error and methane integrates the share, so the
loop has almost no damping to spend on a delay. The weak damping the team
reports as a property (Q ≈ 128) is the warning sign.

**R2.** Nine equal habitats at `T + δ_j`, `δ` evenly spaced, cells exchanged
at 10⁻³ yr⁻¹, methane shared, f = 0.5 unless stated.

| Supply potential | Single habitat | ±3 K spread | ±6 K spread |
|---:|---:|---:|---:|
| 0.24 | 281.535 K | 283.78 K | 286.03 K |
| 0.30 | 281.535 K | 281.54 K | 281.54 K |
| 0.36 | 281.535 K | 280.04 K | 278.54 K |
| 0.44 | 281.535 K | 278.54 K | 275.55 K |

The values step by one box offset because nine boxes are discrete; a
continuum would slide smoothly. Each habitat is won outright by one guild,
and the global temperature settles where the fraction of acetogen habitats
supplies the right methane. That is proportional control with a range set
by the spread of habitat temperatures, not a set point.

With a 3-yr lag at f = 0, a ±3 K spread leaves a residual wobble of 0.03 K;
±6 K with a 300-yr lag leaves 0.5 K. Both guilds stay above 10²⁵·⁶ cells.

Global minima during the two invasions (continuum values, log₁₀ cells):

| Spread | Methanogens displaced (start 273.5 K) | Acetogens displaced (start 294.4 K) |
|---:|---:|---:|
| 0 | −3117 | −34,505 |
| ±6 K | −573 | −16,541 |
| ±10 K | 25.0 | −8,151 |
| ±14 K | 25.3 | −781 |
| ±18 K | not run | 25.3 |

The bottleneck goes once some habitat stays on the displaced guild's side of
the crossing throughout the transient. Displaced acetogens need the larger
spread because the climate crosses the 297 K peak. Earth's meridional and
seasonal ranges exceed both. The team's climate-tracking refuge stage (C08)
reached the edge of this result and recorded it as a domain limitation.

**R3.** One-at-a-time changes to the reference, switch temperature in K:

| Change | Switch | Change | Switch |
|---|---:|---|---:|
| reference | 281.535 | constant thresholds | 278.171 |
| capacity ratio 0.38 | 297.077 | no maintenance T-dependence | 279.049 |
| capacity ratio 1.5 | none | both of those | 278.647 |
| Y_M = 0.4 | 293.909 | MSP | 290.285 |
| Y_M = 1.7 | none | first-order acetogen | 282.780 |
| L = 10⁻⁴ or 10⁻² h⁻¹ | none | L = 3×10⁻⁴ / 3×10⁻³ | 277.151 / 291.921 |

Every crossing found has acetogens on the cold side (M-cold in 2 of 243 MSB
sets and 5 of 243 MSP sets). Among the 161 MSB sets in which methanogens win
at 20 and 30 °C, 70 have a restoring crossing on the branch. Drawing
Kotsyurbenko's V_max and K_m from their published 95% intervals (4,000
draws) never removes the reference crossing and gives a standard deviation
of 1.44 K. So the crossing is robust to assay noise and fragile to the
transferred scales (γ, Y_M) and to L.

**C07 holds.** Recomputing the focal invasion gives methanogens below one
global cell at 18.335 yr and 273.525251 K at year 20, as recorded.

## 4. Answers

### 1. Is the science right?

- **Formulation, units, budgets.** Correct as far as I checked. The R\*
  algebra, the mixed-state allocation, the redox residual and the Jacobians
  are consistent, and my independent six-state extension reproduces the
  five-state spectrum in the zero-lag limit.
- **Quasi-static coupling.** This is where the science is wrong for a
  planet, though right for the declared model (R1). The bridge and plateau
  do not drive the mixed set point; they drive the single-guild controls,
  the 8.02 K contrast, the bistability boundaries and every invasion
  history. The 8 K contrast is therefore the least secure headline number,
  which the team already half-says (4.73 K under the other continuation).
- **Physiology transfer.** The continuation below 4 °C does not touch the
  reference set point (8.4 °C, inside the measured range). What drives the
  result is the transfer of absolute scale: A. woodii yield and maintenance,
  a methanogen yield that matches a 65 °C thermophile's (3.1 g per mol CH₄,
  divided by four; my inference from the evidence table), and a capacity ratio
  chosen on a per-culture basis (R3). The source paper reports that MSB keeps
  its low-hydrogen advantage at every temperature measured; the model's MSB
  crossing comes from the imposed turnover and yields, not from that
  observation (R6).
- **Birth–death treatment.** Sound, and standard: a time-inhomogeneous
  linear birth–death process in a recorded environment, whose survival
  integral is Kendall's (1948). Cite it. My objection is to the input, not
  the method: a 10²³-fold synchronous collapse of a planetary population is
  what a single well-mixed box produces (R2), so the 230-cell and d^4.42
  results are precise answers to a question the planet does not pose.
- **Dormancy switching.** Defensible but generous: entry and waking respond
  to realised net growth with perfect sensing, and dormant cells pay no
  maintenance. It does not drive a headline result, because the seed-bank
  threshold is the arithmetic in R9.
- **Trait family.** Arbitrary, and it drives the evolution headline (R8).
  A "kinetic position" treats one strain's reaction norm as a line of
  genotypes; 16 of the 42 optima sit on interpolation nodes.

### 2. Do the claims follow from the evidence?

Within the declared model, yes; the ledger's limits are careful and I found
no claim that exceeds its own limit. The problem is one level up. The
estimands guard against reading model temperatures as Archean temperatures,
but no estimand states that habitat temperature equals instantaneous
global-mean temperature, that f must be well below one, or that the crossing
exists in a minority of the sensitivity grid. Specific wording I would
change:

- E1 "turnover sets the competitive set point": see R6.
- E7 "the model thermostat is weakly damped": add "with instantaneous
  temperature; it is unstable with thermal inertia".
- E12 "can need biological memory during an invasion": add "when all
  habitats share one temperature".
- Brief item 5: the 120-yr period belongs to f = 0, not to the code's
  reference (f = 0.5: 153 yr, Q = 22).

Understated: set-point invariance across climate cases and the MSP result
(R12), and robustness to assay uncertainty (R3).

### 3. Novelty and significance

- **Known.** Negative feedback between haze cooling and methanogen activity
  has been discussed since the 2008 haze papers, as the groundwork note
  says. Coupled microbial–methane–climate models exist, and Sauterey et al.
  (2020) include acetogens and acetotrophs, as I recall it. Regulation by
  two competing types that integrate an environmental error is the
  Daisyworld mechanism, formalised as integral rein control. The dependence
  of competitive outcome on temperature and dilution rate is 1970s chemostat
  theory. Thermal inertia producing oscillation in Daisyworld is published.
  Responsive dormancy and seed banks have a large literature.
- **New, as far as I can tell.** A set point defined by an R\* crossing
  between two metabolic guilds with measured uptake kinetics, on a published
  haze response, where the guild that wins in the cold warms the planet. The
  quantified gap between exclusion time and climate time. The demonstration
  that unconstrained optimum evolution erases a tolerance-edge thermostat
  while a competitive one is carried by terms the trait cannot reach (once
  stated without overreach). And the method: predictions fixed before runs,
  with refutations kept.
- **Missed.** Rein and integral control; chemostat competition theory;
  Nevison et al. on inertia; Weaver & Dyke on timescales; the seed-bank
  literature; the contribution of acetate to methanogenesis in cold
  sediments. See section 5.

### 4. The strongest objection

A sceptical referee says first: "This is a chemostat, not a planet. One
box, one temperature, one dilution rate, no heat capacity, no atmosphere
for hydrogen. Your fragility and your memory are what a chemostat does when
you change its temperature."

The single assumption most likely to overturn the conclusions is that all
habitats sit at the instantaneous global-mean temperature. I have shown it
overturns items 1–5 of the brief in part (R1, R2). Second is the acetate
sink (R4): if f is near one the thermostat regulates over a few per cent of
supply.

The one analysis that would most strengthen the work is the distributed-
habitat model with thermal inertia. It would tell you whether a finite-gain
competitive feedback, with persistence supplied by ordinary heterogeneity,
still warms and steadies a hazy planet. If it does, that is a stronger and
more defensible paper than the present one.

### 5. The story

The current thesis, that a competitive thermostat can need biological
memory, is defensible only for the homogeneous limit, and a referee will
see that the need is created by the idealisation. I would not lead with it.

A better story is in the same results: **competitive replacement between
two hydrogen-using guilds acts as an integral controller of a hazy climate,
with a set point fixed by their physiology and independent of the climate
curve.** Then take it through what a planet does to it: inertia makes it
oscillate; heterogeneity damps the oscillation, removes the invasion
bottleneck and turns integral control into graded control; acetate fate and
turnover bound where it operates. The exclusion–climate timescale gap (C07)
is the figure that explains why all of this matters. Memory by dormancy
becomes one paragraph: seed banks need to last only about 1/80 of a bad
interval because planetary populations are large.

One paper. Main text: mechanism and set point (C05, C06), conditions for
existence (R3, R4, C12–C13 as one regime figure), dynamics with inertia and
heterogeneity (C20 plus the new work), the timescale gap (C07), and a short
evolution section (C02 against C29 and C36). Supplement: stages 1–2 beyond
C02, the finite-census inventories, bottleneck exponents and branching
checks, the dormancy stage, the refuge inventories and the endpoint
classifications (C08–C11, C14–C19, C21–C24). The dormancy stage has about
thirty modules and its residue is 41 "bank unresolved" and 31 "otherwise
unsettled" endpoints; it has cost more than it returns.

### 6. Reproducibility and record

- A newcomer can install, pass the tests and recompute the central
  equilibria in minutes from `population_coupling.equilibrium_states`. I did
  so without help. There is no single entry point that says so; add one.
- The ledger is useful, and I used it constantly. Three changes would make
  it more than bookkeeping. Tag each claim with the assumptions it depends
  on (bridge, plateau, continuation, f, L, γ, single temperature). Separate
  model results from process notes: C16, C22, C23 and C24 record identities
  and unresolved states, which a paper does not claim. And note that most
  "basis" entries are recounts by the building system; that is verification
  of arithmetic, not of the science.
- The reproduce commands for supported claims rerun audits over committed
  tables. That is fine for a ledger check but it is not reproduction from
  the model, and C26–C28 point at long producers.
- Stale or inconsistent documentation:
  - `README.md` opens with a status dated 10 November and an 80-line
    paragraph that narrates every stage; its results sections describe the
    placeholder stage-1 physiology at length before a reader reaches the
    model that matters.
  - `competition-switches.md` reports "none" for MSP at reference affinity;
    the crossing is at 290.285 K, 0.3 K outside the scan window.
  - "Reference" is f = 0.5 in `population_coupling.reference()` and f = 0 in
    C20 and the brief.
  - The last paragraph of `synthesis.md` still says Claude will review the
    evolution stage before reporting readiness.
  - `competitive-evolution.md` has missing spaces throughout ("full72-setting",
    "The252-setting map finds166", "measured4–30").
  - `Params` carries stage-1 fields that the coupled model ignores.

## 5. Literature

All DOIs below were resolved against Crossref on 11 November 2026 and the
registered title, authors, year and journal matched. I did not open full
texts in this session, so the one-line descriptions are from my prior
knowledge of each paper, and you should confirm them before citing.

**Regulation and Daisyworld**

- Watson & Lovelock 1983, Daisyworld. doi:10.1111/j.1600-0889.1983.tb00031.x
- Saunders 1994, regulation without selection in Daisyworld. doi:10.1006/jtbi.1994.1033
- Koeslag, Saunders & Wessels 1997, homeostasis with infinite gain. doi:10.1677/joe.0.1540187
- Saunders, Koeslag & Wessels 1998, integral rein control. doi:10.1006/jtbi.1998.0746
- Robertson & Robinson 1998, Darwinian Daisyworld (adaptation erases regulation; the precedent for C02). doi:10.1006/jtbi.1998.0799
- Lenton & Lovelock 2000, constraints on adaptation restore it (the precedent for C03). doi:10.1006/jtbi.2000.2105
- Nevison, Gupta & Klinger 1999, heat capacity gives self-sustained oscillations. doi:10.1034/j.1600-0889.1999.t01-3-00005.x
- Wood, Ackland, Dyke, Williams & Lenton 2008, review. doi:10.1029/2006RG000217
- McDonald-Gibson et al. 2008, regulation under minimal assumptions. doi:10.1016/j.jtbi.2007.12.016
- Weaver & Dyke 2012, timescales and the emergence of regulation. doi:10.1016/j.jtbi.2012.07.034
- Dyke & Weaver 2013. doi:10.1371/journal.pcbi.1003050
- Williams & Lenton 2008, regulation in networks of microbial ecosystems. doi:10.1073/pnas.0800244105
- Lenton et al. 2018, selection for Gaia across scales. doi:10.1016/j.tree.2018.05.006
- Nicholson et al. 2018, Gaian bottlenecks in model biospheres. doi:10.1093/mnras/sty658
- Chopra & Lineweaver 2016, the Gaian bottleneck. doi:10.1089/ast.2015.1387
- Alcabes, Olson & Abbot 2020, robustness of Gaian feedbacks. doi:10.1093/mnras/staa055
- Yi, Huang, Simon & Doyle 2000, perfect adaptation through integral feedback. doi:10.1073/pnas.97.9.4649

**Archean methane, haze and coupled ecosystems**

- Kharecha, Kasting & Siefert 2005 (already in the repository's bibliography; needs engaging in the argument). doi:10.1111/j.1472-4669.2005.00049.x
- Catling, Zahnle & McKay 2001, methane and hydrogen escape. doi:10.1126/science.1061976
- Ozaki et al. 2018, primitive photosynthesis and early climate. doi:10.1038/s41561-017-0031-2
- Sauterey et al. 2020. doi:10.1038/s41467-020-16374-7
- Sauterey et al. 2022, methanogen-driven cooling on early Mars. doi:10.1038/s41550-022-01786-w
- Haqq-Misra et al. 2008. doi:10.1089/ast.2007.0197
- Domagal-Goldman et al. 2008. doi:10.1016/j.epsl.2008.01.040
- Zerkle et al. 2012, bistable organic-rich atmosphere. doi:10.1038/ngeo1425
- Izon et al. 2017, haze episodes and biological regulation. doi:10.1073/pnas.1618798114
- Pavlov et al. 2001. doi:10.1130/0091-7613(2001)029<1003:ohiese>2.0.co;2
- Trainer et al. 2006. doi:10.1073/pnas.0608561103
- Wolf & Toon 2010. doi:10.1126/science.1183260
- Laakso & Schrag 2019. doi:10.1016/j.epsl.2019.06.022
- Thompson et al. 2022. doi:10.1073/pnas.2117933119
- Charnay et al. 2020, faint young Sun review. doi:10.1007/s11214-020-00711-9
- Held et al. 2010, fast and slow climate response times (for R1). doi:10.1175/2009jcli3466.1

**Hydrogen competition, thresholds and acetate fate**

- Cord-Ruwisch, Seitz & Conrad 1988, thresholds follow redox potential. doi:10.1007/bf00411655
- Lovley & Goodwin 1988. doi:10.1016/0016-7037(88)90163-9
- Hoehler et al. 1998, thermodynamic control of sediment hydrogen. doi:10.1016/s0016-7037(98)00106-9
- Conrad, Schütz & Babbel 1987. doi:10.1111/j.1574-6968.1987.tb02378.x
- Conrad 1999, share of hydrogen in methane production (for R4, R5). doi:10.1111/j.1574-6941.1999.tb00575.x
- Kotsyurbenko 2005, low-temperature methanogenic communities. doi:10.1016/j.femsec.2004.12.009
- Conrad 2023, temperature dependence in methanogenic environments. doi:10.3389/fmicb.2023.1232946
- Lever 2012, acetogens persist through substrate versatility, not hydrogen kinetics. doi:10.3389/fmicb.2011.00284
- Rothman et al. 2014, late origin of efficient acetoclastic methanogenesis (the best argument for low f, and contested). doi:10.1073/pnas.1318106111
- Wolfe & Fournier 2018, timing of methanogen evolution. doi:10.1038/s41559-018-0513-7

**Competition theory, seed banks, demography**

- Harder & Veldkamp 1971, competition outcome set by temperature and dilution rate. doi:10.1007/BF02218466
- Veldkamp & Jannasch 1972. doi:10.1002/jctb.2720220113
- Stewart & Levin 1973. doi:10.1086/282825
- Hsu, Hubbell & Waltman 1977. doi:10.1137/0132030
- Tilman 1982, *Resource Competition and Community Structure* (Princeton). **Not verified**; a book, no DOI checked.
- Cohen 1966, bet-hedging dormancy. doi:10.1016/0022-5193(66)90188-3
- Jones & Lennon 2010. doi:10.1073/pnas.0912765107
- Lennon & Jones 2011. doi:10.1038/nrmicro2504
- Morono et al. 2020, viability after 100 Myr. doi:10.1038/s41467-020-17330-1
- Kendall 1948, the generalised birth-and-death process (for C16). doi:10.1214/aoms/1177730285

**Not verified, from memory:** Harvey (2004), "Homeostasis and rein control:
from Daisyworld to active perception", Artificial Life IX proceedings. My
statement that volcanic hydrogen fluxes are one to two orders of magnitude
below the reference supply is a recollection of Kharecha et al. (2005), not
checked. So is my statement that the 2008 haze papers discuss a
temperature-dependent methanogen feedback.

## 6. What would change my view

- **R1 (thermal inertia).** I would withdraw it if a proper treatment showed
  the relevant temperature responds to methane within about two months, or
  if a damping process missing from my six-state test (for example product
  feedback on thresholds, or a hydrogen pool with real storage) moves the
  stability boundary beyond a few years of lag at both f values. A
  stability map in (τ_T, f, L) from the team's own solver would settle it.
  If the map shows instability only at f = 0, the finding narrows to that
  case.
- **R2 (heterogeneity).** I would be wrong about the thesis if a
  distributed-habitat model with realistic meridional and seasonal ranges
  still showed a guild passing through a demographic bottleneck during
  displacement, or still held the global temperature within about 1 K
  across the supply band. I would also reconsider if there is a good
  argument that Archean hydrogenotrophs occupied one thermally uniform
  habitat, such as a deep ocean with a narrow temperature range; then the
  single box is a fair model of the habitat, though R1 applies with a much
  longer lag.
- **R4 (acetate fate).** Evidence for a non-methane electron sink taking
  more than about a third of acetate under Archean conditions, or a
  defensible case that acetate was not converted to methane at all before a
  late origin of acetoclastic metabolism, would turn this from a major scope
  problem into a stated assumption with support. Conversely, a
  redox-closed variant in which the mixed band stays wide at f near one
  would show I have the mechanism wrong.
