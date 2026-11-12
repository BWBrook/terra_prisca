# Step 1: working abstract (key questions)

Claude (Opus 5.5), 12 November 2026. This is a working document for Barry's
paper-reconstruction process. It is for reference during drafting, not for
submission. The target journal is J R Soc Interface. Claim IDs refer to
[`../synthesis/claims.csv`](../synthesis/claims.csv).

## Why are you doing this?

Whether life can regulate planetary climate is a question that goes back to
Daisyworld. Biotic thermostats are almost always analysed at equilibrium, so
two things remain unknown: whether they survive the slow response of climate,
and what robustness costs them.

## What are your aims and research questions?

**Core aim:** can competition for hydrogen between acetogens and methanogens
regulate the climate of a hazy early Earth, and do so robustly?

**Sub-questions:**

1. Does exact regulation survive a lag in the climate's response?
2. How much precision must be given up to buy robustness?
3. Does the order of community assembly choose the regulator?

## What hypotheses underpin them?

- **H1.** Exact set-point holding is integral feedback. Integral action adds
  phase lag, so exact biotic regulation should destabilise at short climate
  lags.
- **H2.** Leaks in the integrator, such as product self-limitation or a
  spread of habitat temperatures, should trade a small loss of precision for
  a large, continuously rising gain in delay margin.
- **H3.** Exclusion has no coexistence buffer, so invasion outcomes should
  depend on arrival order. These are priority effects.

## What did you do?

**The model.** Two microbial guilds draw on an open hydrogen supply. They are
coupled to the methane–haze climate of Arney et al. (2016), with an explicit
thermal lag.

**The analyses:**

- linear stability and critical delays;
- continuation along graded "leak" dials;
- resolved habitat continua;
- finite-population invasion transients.

## What did you find?

- **Exact regulation is fragile.** Every exactly holding state lost stability
  at lags of 7 years or less (C54).
- **Graded regulation is robust.** A sensitivity of 0.07–0.32 K per e-fold of
  supply bought a 30-year margin, and 1–2 K bought centuries (C57, C54).
- **Invasion order decided the residents** in all 24 runs (C52).

## What do the results mean?

- **Exact biotic regulation is a fragile limit.** Persistent regulators must
  be leaky.
- **Robustness is cheap but not free.** It rises continuously as precision is
  given up, with no threshold.
- **History matters.** Which regulator a planet gets depends on how its
  community assembled.

**Scope.** This is a conditional, Archean-inspired model. It is not a
calibrated reconstruction.

## What is it good for, and how does it generalise?

Any biological feedback acting on a slow environment faces this
precision–robustness trade-off: Gaian regulation, microbial biogeochemistry,
engineered ecosystems, and biosignatures on other worlds. The delay-margin
analysis carries over directly to them.

## Notes for later steps

- **H1–H3 were partly prespecified.** Some of our sharper predictions failed:
  - a universal power law (C56);
  - the weak-mode formula at refinement points (C58);
  - a threshold on the local gain (C46, C49).

  The paper should keep these as honest counterexamples, not hide them.
- **Seto & Akagi (2007) own the static plateau.** Our novelty is the answers
  to sub-questions 1–3.
- **Long-standing question:** can life regulate its planet, and is that
  regulation robust? The paper should open there, with the Archean as the
  motivating case.
