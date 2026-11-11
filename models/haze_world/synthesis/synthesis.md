# Haze-world synthesis

Claude (Opus 5.5), with independent numerical and semantic audit by Codex
(GPT-6), 11 November 2026. The [claims ledger](claims.csv) binds the results;
[estimands.md](estimands.md) states their interpretation limits. The
[audit](../../../docs/audits/haze-world-synthesis-review-2026-11-11.md)
records corrections to the first synthesis. Barry has agreed to aim for a
paper; he will guide its writing once the evidence is ready (see [Paper](#paper)).

## Thesis

**A competitive climate thermostat can need biological memory during an
invasion.** In this model, a locally stable microbial mixture can regulate
climate, yet a resident–invader transient can eliminate a participant before
the climate turns in its favour. Refuges and dormant banks can retain the
losing guild across that interval []{.C07} []{.C09} []{.C17}.

This is a claim about recovery through the studied displacement events.
An already established mixed community has a stable positive neighbourhood
without an extra store; memory is not necessary for every initial state
[]{.C06}. Nor does a refuge or seed bank guarantee a common endpoint or joint
demographic survival. The useful distinction is between an equilibrium's
existence and a finite community's ability to reach it.

The precursor and competition stages use different physiology. The former
has an assumed thermal growth curve; the latter transfers measured uptake,
yield and maintenance parameters between strains. Most competition results
use Arney's case-B climate response. `f` denotes the fraction of acetate
subsequently converted to methane. Model versions, climate extensions,
budget assumptions and the cell-count convention remain explicit in the
[estimands](estimands.md).

## The argument

1. **Unconstrained optimum evolution removes the single-guild signature
   when peak growth is held fixed.**
   - In the high-supply scalar experiment across Arney A–D, stable
     equilibria lie [0.015–0.037]{.C01} K above the resource-dependent cold
     net-growth edge. These are model offsets, not climate measurement
     accuracy.
   - In the fixed-peak, unconstrained adaptive-dynamics family, the optimum
     tracks temperature and the local regulation ratio is [1]{.C02} under
     every tested loss shape.
   - A hard optimum floor can restore buffering; a growth-rate trade-off
     also retains buffering under sufficiently shallow methane loss
     []{.C03}. A floor is not the only route.
   - During the specified supply decline, fixed-optimum populations without
     mutation die during warming on the way toward the [297]{.C04} K
     greenhouse peak, despite viable final supplies. This is not the fate
     of all methanogen populations []{.C04}.

2. **Hydrogen competition supplies a restoring feedback and an ecological
   equilibrium temperature.**
   - At the two central break-even crossings, acetogens win on the cold
     side and methanogens on the warm side. The crossings,
     [281.5]{.C05} and [282.8]{.C05} K, lie on the haze-cooling branch.
     If acetogen routing delivers less methane, its warming effect reverses
     the competitive advantage. This sign alone is not a stability proof
     []{.C05}.
   - With explicit populations, the reference mixed state is locally stable
     at [281.535]{.C06} K. Disabling acetogens gives a methanogen-only
     control at [273.517]{.C06} K: a contrast of [8.02]{.C06} K.
   - The contrast falls to [4.73]{.C06} K under the alternative cold
     physiology. These are matched model controls, not evidence for two
     simultaneously stable full-community climates or an Archean warming.

3. **Turnover moves the competitive set point under fixed physiology.**
   - The guilds' break-even hydrogen pressures cross at the equilibrium
     temperature. Their required uptake `m + L/Y` depends on turnover,
     maintenance and yield; affinity and capacity also enter the crossing.
   - The root-delimited branch spans about [273.4]{.C12}–[296.1]{.C12} K.
     This is a branch-limit range, not the extrema of the original sampled
     grid. Its cold end depends on the digitized climate minimum and the
     named physiological continuation []{.C12}.
   - At `f=0`, stable acetogen and mixed equilibria coexist between
     [0.001238145]{.C13} and [0.003936106]{.C13} h⁻¹. A separate interval
     of pure-guild bistability follows; bistability does not persist at
     every higher turnover []{.C13}.

4. **Competitive exclusion can outrun the climate response.**
   - In the focal closed, single-habitat `f=0.5` invasion, the census removes
     methanogens after [20]{.C07} years while temperature moves only from
     [273.517]{.C07} to [273.525]{.C07} K.
   - The tested closed `f=0/0.5` invasion histories select different
     single-guild outcomes even though a stable mixed state exists.
     Higher recycling does not show the same history dependence
     []{.C07}. These are finite-census outcomes, not a new proof of
     continuum climate bistability.

5. **Buffered refuges can retain both participants through those invasions.**
   - In the tested lower-recycling, mean-preserving climate-tracking
     geometry, paired rescue cannot be demonstrated within the declared
     physiological domain; the cold refuge must remain favourable while
     the global climate crosses the [297]{.C08} K greenhouse peak. This is
     a design-specific limitation.
     Higher-recycling cases do include matching coexisting outcomes
     []{.C08}.
   - With both temperature-buffered refuges at the reference temperatures
     and the three tested positive exchange rates, [12]{.C09} key runs form
     [6]{.C09} matching mixed pairs near [281.535]{.C09} K. The entire [192]{.C09}-run design
     also includes single-guild outcomes and different endpoints; it is
     not a universal rescue result.
   - Along the specified warm-refuge exchange cut, the global minimum
     scales approximately as exchange to the power [4.423]{.C10}.
     About [230]{.C10} cells at that bottleneck correspond to half
     survival. The corresponding exchange crossing is about
     [3.4]{.C10} times the posthoc global one-cell crossing. This is not
     a counterfactual rerun of the local census rule. The exact single-type
     integrated survival identity avoids assuming a Gaussian bottleneck;
     a multitype population still needs its own calculation []{.C16}.
   - Refuge methane can also aid establishment. Holding its flux fixed
     while omitting bulk methane puts the diagnostic climate
     [0.28]{.C14} K above the switch at one setting. The actual mixed
     endpoint remains at the switch; the diagnostic uses the assumed
     low-methane bridge and does not measure a temperature-window extension.
   - Coexistence, methane forcing and regulation must be reported
     separately. A source–sink example gives methanogens
     [2.082]{.C15}% of global catabolism but only [0.001080]{.C15}% of
     bulk catabolism. This shows negligible autonomous bulk participation,
     while refuge methane can still affect climate.

6. **Dormant banks can retain a guild through its first bottleneck.**
   - Without refuges, half first-window survival is bracketed by:

     | Displaced guild | f = 0 | f = 0.5 |
     |---|---|---|
     | Methanogens | [11.3]{.C17}–[13.2]{.C17} yr | [31.6]{.C17}–[32.3]{.C17} yr |
     | Acetogens | [158]{.C17}–[172]{.C17} yr | [88]{.C17}–[96]{.C17} yr |

   - Acetogens need longer because their suppression spans the greenhouse
     excursion. These conditional per-guild probabilities do not establish
     joint persistence or a common endpoint []{.C17}.
   - The isolated-bank approximation `ε* ≈ ln(N₀/N₅₀)/(Lτ)` agrees within
     [0.992]{.C18}–[1.167]{.C18} of the prediction. A half-life of about
     [1.275]{.C18}% of the suppression interval belongs to the assumed
     population ratio here; the coupled path and waking can change it.
   - Growth-triggered dormancy can also deepen a mild bottleneck. At
     `ε=0.1`, the continuum acetogen minimum reaches
     10^[−59.5]{.C19} cells, against 10^[−14.25]{.C19} without dormancy.
     The fixed-environment allocation argument explains the mortality cost;
     both paths can already imply very poor finite survival []{.C19}.

7. **The reference thermostat has a weakly damped oscillatory mode.**
   - At the reference loss and `f=0`, its period is [119.6]{.C20} years,
     damping time [4,854]{.C20} years and quality factor about
     [128]{.C20}. The coupled feedback can therefore oscillate through
     many periods while approaching equilibrium.
   - All prescribed small and ±10% single-guild kicks decay with that
     mode []{.C20}; the predicted large-kick transition was refuted
     []{.C27 .superseded}.
   - Some cubic-switching invasion paths keep recurring over their recorded
     horizons, with ranges of [0.2]{.C21}–[1.5]{.C21} K, beside locally
     stable roots. One spatial case has repeated local census removals,
     unlike the unculled nonspatial paths []{.C21}.
   - Linear switching damps the three completed controls. The two warm
     comparisons remain unresolved []{.C22}. None establishes a periodic
     attractor or a general stability theorem for the nonsmooth law.

8. **Kinetic adaptation can preserve a competitive set point, but it does
   not make the thermostat evolution-proof.**
   - At reference turnover, the no-constraint linear-shape crossing moves
     to [277.960221]{.C29} K and remains a locally stable mixture.
   - Across the S3 grid, [42]{.C34} settings retain stable cooling-branch
     communities and [30]{.C34} have none. The additional [14]{.C34}
     greenhouse roots are ecologically unstable even though their traits
     pass the mutant assay.
   - All detected crossings keep the restoring orientation []{.C30}. At
     low turnover, the separately adapted methanogen-only state sits at
     [274.002]{.C31} K on the imposed plateau; this is not a demonstrated
     endpoint of the stopped canonical paths.
   - At higher E, the reference crossing stays within
     [0.490588614]{.C32} K of the frozen set point. E is a phenomenological
     Arrhenius constraint, not measured evidence for a cold-adaptation cost.
   - The exclusive thermodynamic-anchor prediction was refuted
     []{.C33 .superseded}. Freezing maintenance at its warm value also
     removes the reference crossing. A separate matched-level derivative
     control finds positive contributions from both threshold and
     maintenance temperature dependence []{.C36}.
   - The largest specified interpolation shift is [1.231341464]{.C35} K,
     yet a smaller shift can move a crossing across the climate maximum
     and change whether a community exists.
   - The [60]{.C37} conditional canonical tracks lose their supported mixed
     branch. They do not demonstrate demographic extinction or arrival at
     the separately checked pure states. Local evolutionary stability and
     recovery through competitive displacement remain different questions.

## What the checks establish

| Result | Checked variation or contrast | Remaining condition |
|---|---|---|
| Restoring switch | Both central uptake laws, where the crossing exists | Less methane from acetogen routing; haze-cooling branch; local sign is not full stability (C05) |
| Turnover-dependent set point | Equilibrium inventory and independently rooted boundaries | Fixed transferred physiology; a supported branch is required (C12–C13) |
| Exclusion before climatic recovery | Specified closed resident–invader starts | Census, count scale, loss and initial state (C07) |
| Buffered refuge rescue | Both histories in the key paired subset | Prescribed heat baths, exchange and low-methane closure (C09) |
| Seed-bank thresholds | Fast and slow switching brackets | Entering population, recovery, climate path and first-window scope (C17–C18) |
| Deeper dormant bottleneck | Two warm-refuge exchange settings | Growth-triggered cubic entry and dormant mortality (C19) |
| Damped oscillatory mode | Four combinations of recycling and turnover | Reference physiology and budget; not an Earth-period prediction (C20) |

Each row is conditional on its named model version in
[estimands.md](estimands.md). Independent calculation validates these
model-scoped results; it is not independent empirical calibration.

## Corrections recorded along the way

- The proposed switch-induced cold trap had its feedback sign reversed
  (C05).
- KD2's universal overshoot protection fails (C28); the deeper-bottleneck
  mechanism is retained in C19.
- Exact seed-bank equality was superseded by approximate agreement
  (C25 → C18).
- The predicted global minimum was refuted by a smaller, still protected
  first bottleneck in the smaller-refuge run (C11).
- Source-free decay of every bank-only endpoint and the predicted large-kick
  transition were refuted (C26, C27). The classification remains
  [56]{.C23} strictly stationary, [41]{.C23} macrostate stationary with
  bank unresolved, and [31]{.C23} otherwise unsettled; no bank passes the
  verified frozen-root relaxation criterion []{.C23}.
- The first synthesis overgeneralized the buffered-refuge inventory, tracking
  refuge failures, precursor evolutionary result and turnover boundary.
  The [review record](../../../docs/audits/haze-world-synthesis-review-2026-11-11.md)
  preserves these corrections.

## Open questions, in order of value

1. **Which additional physiological freedoms change the evolved result?**
   The restricted kinetic-position stage now answers the planned question:
   reference regulation survives locally, while other settings lose a feasible
   crossing (C29–C37). Thresholds, maintenance and yields did not evolve.
   Extending selection to those quantities is a separate question, not a
   reason to describe the current thermostat as generally evolution-proof.
2. **Coupled stochastic demography.** This would replace conditional
   per-guild first-window probabilities with joint endpoint probabilities
   and address repeated-cycle survival (C24).
3. **Warm-refuge linear controls (C22).** Revisit only if a claim needs their
   outcome. The present conclusions leave them unresolved.
4. **External constraints.** Photochemical loss near the operating methane
   ratio, a matched low-methane climate, cold-strain physiology and plausible
   turnover remain the most useful inputs to constrain.
5. **Luminosity.** A solar sweep needs matched climate responses at other
   solar forcings.

## Paper

**Decision.** Barry, 11 November 2026, in chat with Claude, as recorded in
commit `ae47a3d` and board message 3204:

> Yes, we should aim for a paper. But I'd like to follow a particular structured approach to doing this. So, when you and Codex are 'ready to write', that's when I'll step in and guide that part of the process more carefully.

Barry will lead that process. Until he does, Claude and Codex do not scaffold
or draft manuscript products; they prepare the evidence and figure plan.

**Ready to write** requires all four:

1. Every current ledger row is supported, or contested and resolved into a
   supported, superseded or refuted row.
2. Claude and Codex both accept [estimands.md](estimands.md).
3. Both agree the scope, including whether competitive evolution runs before
   writing.
4. Both agree a figure plan, with each figure's data file in the repository.

Claude then reports readiness to Barry in chat. The
[readiness and scope note](readiness.md) records the audit status, Codex's
recommendation for one bounded evolution stage, and a proposed figure map.
It is preparation for Barry's writing process, not a manuscript product or
an instruction to start that process now.

Claude (Opus 5.5) designed stages and predictions, reviewed builds and drafted
the synthesis. Codex (GPT-6) implemented models, ran experiments, archived
evidence and independently audited calculations and interpretation. Barry is
the scientific facilitator.

## Reproduction and next step

The ledger now records specific CSV/JSON inputs, independent checks and
reproduction commands. Retained model-page and source commands explain how
the original experiments were produced. Raw-input dependencies are identified
by their existing payload receipts. Check the ledger with:

```sh
python3 tools/claims.py check models/haze_world/synthesis/claims.csv models/haze_world/synthesis/synthesis.md
```

Claude reconciles the revised scopes and proposed figure map. The competitive-evolution stage and C07 export are complete; Claude reviews
these results and E13 before reporting readiness. Barry leads the writing
when the readiness conditions hold.
