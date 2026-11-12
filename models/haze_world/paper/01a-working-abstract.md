# Step 1a: working abstract (key questions)

Claude (Opus 5.5), 12 November 2026. This is a working document for Barry's
paper-reconstruction process. It is for reference during drafting, not for
submission. The target journal is J R Soc Interface. Claim IDs refer to
[`../synthesis/claims.csv`](../synthesis/claims.csv).

Reviewed and revised by Codex (GPT-6), 12 November 2026. The earlier draft
remains in Git; these are Step 1 revisions for Claude's review.

## Main message (24 words)

> Microbes can hold a planet's temperature steady, but perfect control breaks
> down when the climate responds slowly; slightly imperfect control is far
> more durable.

**Supporting results:**

- all 42 exact states are already unstable or first lose stability by about
  7.1 years (C54);
- on four tuned branches, a 30-year first-loss margin costs a local
  sensitivity of 0.07–0.32 K per e-fold of supply (C57).

**Invasion order (C52) is a separate assembly result.** It selects the
surviving guild in the closed, single-habitat runs. Those endpoints are
single-guild communities. Keep this as a short final Results section.

## Why are you doing this?

Daisyworld made planetary regulation by life a modelling question. We ask
how slow climate adjustment affects a competitive microbial regulator, and
what greater robustness costs in temperature precision.

## What are your aims and research questions?

**Core aim:** can competition for hydrogen between acetogens and methanogens
regulate the climate of a hazy early Earth, and do so robustly?

**Sub-questions:**

1. Does exact regulation survive a lag in the climate's response?
2. How much precision must be given up to buy robustness?
3. Does invasion order select the surviving guild in a finite community?

## What hypotheses underpin them?

These organise the paper's argument. They developed during the investigation;
the dated specifications below identify the subsequent prospective tests.

- **H1.** Competitive pinning has effective integral action near coexistence;
  slow climate adjustment can destabilise the reference mixture.
- **H2.** Product self-limitation and habitat-temperature spread can exchange
  exact pinning for a larger stability margin, increasing continuously near
  the exact limit.
- **H3.** During invasion, rapid competitive displacement can eliminate a
  resident before climate adjustment favours its return, making survival
  depend on arrival order.

## What did you do?

**The model.** Two microbial guilds draw on an open hydrogen supply. They are
coupled to the methane–haze climate of Arney et al. (2016), with an explicit
thermal lag.

**The analyses:**

- linear stability and first losses of stability as thermal response slows;
- continuation along graded "leak" dials;
- resolved habitat continua;
- invasion transients with an explicit extinction census.

## What did you find?

- **Exact regulation is fragile.** Six exact states were already unstable;
  the other 36 first lost stability by about 7.1 years (C54).
- **Graded regulation is robust.** A sensitivity of 0.07–0.32 K per e-fold of
  supply bought a 30-year margin, and 1–2 K bought centuries (C57, C54).
- **Invasion order selected the surviving guild** in all 24 census runs
  (C52).

## What do the results mean?

- **Exact pinning is fragile in this model.** Graded feedback greatly widens
  its stability margin.
- **Robustness has a small precision cost.** The tested branches approach
  the exact limit continuously.
- **Assembly and stability differ.** An established mixture can be stable
  even when invasion eliminates its resident guild.

**Scope.** This is a conditional, Archean-inspired model with transferred
strain kinetics, an imposed hydrogen budget and differential methane yields.
Sensitivities are local derivatives; invasion endpoints use a one-cell census
in a closed habitat. The model's physiology extends to 273 K using a named
continuation below the measurements at 277.15 K.

## What is it good for, and how does it generalise?

The analysis supplies a way to compare precision and stability in other
population–environment feedbacks. Whether they share this trade-off requires
their own response-time and feedback models.

## Notes for later steps

- **Prediction provenance.** H1 followed the reviewers' lag-instability
  finding. Stage B then specified mechanism tests (PB1–PB6); PB6 predicted
  resident loss in at least one invasion direction per setting. H2's
  continuity component was fixed in PD1 before D1/D2, after the on/off
  separation had been observed. These are staged prospective tests within
  an exploratory programme, not three hypotheses fixed before it began.
  Some sharper predictions failed:
  - a common power-law slope band (C56);
  - the weak-mode formula at refinement points (C58);
  - a threshold on the local gain (C46, C49).

  The paper should keep these as honest counterexamples, not hide them.
- **Control interpretation.** The log population ratio integrates the
  per-capita growth-rate difference. Calling it a temperature-error
  integrator or a literal leaky controller requires a further reduction.
- **Stability is local.** The critical lag is the first loss; later recovery
  can occur. A bounded oscillating trajectory can still regulate after its
  equilibrium becomes unstable.
- **Seto & Akagi (2007) own the static plateau.** Our novelty is the answers
  to sub-questions 1–3.
- **Long-standing question:** can life regulate its planet, and is that
  regulation robust? The paper should open there, with the Archean as the
  motivating case.
