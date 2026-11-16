# Pressure test, Issue 4: where does the diverted hydrogen go?

Claude (Opus 5.5), 16 November 2026. The issue was raised by Barry with Fable
in chat. The rules are as for Issues 1–3: address, fix or dispute with
evidence; small bounded checks only; wording for Barry's decision.

**Evidence.**
- Check: `models/haze_world/review/issue4_acetate_fate.py`, with its results in
  `issue4_acetate_fate.json`, evidence commit `2b6134a`.
- Ledger: C67 and C68.
- Method: production equilibrium, delay-margin and rigid-shift code. No new
  model, variant or experimental stage.

## Summary

The regulator is a hydrogen valve, and the paper should say so.

- **Mass balance.** At fixed supply, the methane the climate needs is fixed.
  Exact control holds T\* by sending all supply above the methanogen-only
  level somewhere other than methane. At the reference supply that is about
  20 Tmol of acetate a year whatever f is: 31% of biotic methane, in reducing
  equivalents.
- **What f sets.** f does not set how much hydrogen must be diverted. It sets
  the most the acetogen route can divert, and so the width of the window.
- **With no sink.** If acetate and dead biomass both return as methane, the
  two routes give identical methane and the community controls nothing.
- **What recycling buys.** As f rises, the window narrows and the exact margin
  lengthens in proportion: τ_c(Q − 1) ≈ 1.0–1.1 yr. Recycling trades the
  range of supply the regulator can absorb for tolerance of a slow climate.

## Q1. Fable's estimate, and how the three reported quantities move with f

**The estimate is right to within 5%.** The window ratio
Q = P_A/P_M from S8b is
(e + n/(fη_A))/(e + n/η_M), with:
- η_A = 0.8949 and η_M = 0.9413;
- the atmospheric outlet e equal to 12% of the methane need n.

Dropping e gives Fable's η_M/(fη_A) = 1.052/f. Because e is common to both
ends, the exact ratio is slightly smaller:

| f | Q exact | 1.052/f | Q/(Q−1), eq. (3.1) | imposed-warming window (K) |
|---|---|---|---|---|
| 0 | unbounded | — | 1 | 23.6 (C63) |
| 0.5 | 1.996 | 2.104 | 2.00 | 23.6 |
| 0.7 | 1.453 | 1.503 | 3.21 | 23.6 |
| 0.9 | 1.152 | 1.169 | 7.57 | 16.6 |
| 1 | 1.047 | 1.052 | 22.4 | 6.6 |

So Q is a factor of 2.0 at f = 0.5, 15% at f = 0.9 and 4.7% at f = 1.

**The three reported quantities.** The table below covers f = 0.5–1 at window
positions of 5–95%. All states are homogeneous with ℓ = 10⁻³ h⁻¹.

| f | τ_c exact, fixed products (yr) | mid-window τ_c × (Q−1) (yr) | acetate-feedback \|S\| mid-window (K per e-fold) |
|---|---|---|---|
| 0.5 | 1.11–1.88 | 1.10 | 1.33 |
| 0.6 | 1.57–2.54 | 1.07 | 1.75 |
| 0.7 | 2.29–3.57 | 1.04 | 2.39 |
| 0.8 | 3.59–5.43 | 1.02 | 3.50 |
| 0.9 | 6.61–9.73 | 1.01 | 5.94 |
| 0.95 | 10.3–15.0 | 1.00 | 8.70 |
| 1 | 21.3–30.7 | 1.00 | 15.4 |

- **Supply range.** It narrows as Q − 1.
- **Critical response time.** It lengthens as 1/(Q − 1).
  - The exact margin is lowest mid-window and rises 1.4–1.7× towards the
    edges.
  - At f = 1 exact control alone tolerates responses of 21–31 years, close to
    the paper's 30-year benchmark, but only over a 4.7% range of supply.
- **Graded sensitivity.** Acetate-feedback states at the reference κ move
  temperature by roughly the same ~1 K across the window: |S| × ln Q is
  0.70–0.92 K. Squeezing that change into a narrower window raises |S|
  from 1.3 to 15 K per e-fold.
  - These states stay durable: τ_c was not detected through 10⁴ yr, except
    48 and 130 yr at the upper edge for f = 0.5 and 0.6.
  - For habitat spread, the factor Q/(Q − 1) in eq. (3.1) rises from 2.0 to
    22. |S| is then capped by the climate slope k = 140.7 K per e-fold.
  - The tuned 30-year dial points were not recomputed at higher f. Because
    exact states already tolerate longer lags there, the dial needed for a
    30-year margin should shrink, but this is not shown.
- **Imposed warming.** This shrinks much less than supply. The haze climate
  is steep (k = 140.7 K per e-fold of methane ratio), so even a narrow range
  of methane covers many kelvin: the window is about k·ln Q, capped by the
  branch. It is 24 K up to f = 0.7, 17 K at 0.9 and 7 K at 1.

**Is S8a's statement general?** Yes, within the tested range (f = 0.5–1, every
sampled window position, homogeneous states): recycling narrows the window and
lengthens the margin by matching factors. It is one trade. Below f = 0.5 the
1/(Q − 1) law does not apply, since the window has no upper end at f = 0. The
margin at f = 0 is set by other terms (0.15 yr at the reference).

## Q2. Exported biomass recycled to methane

The model exports lost biomass (η_i < 1). Let a fraction b of that biomass
return as methane at one CH₄ per four hydrogen equivalents. The routes'
methane yields per hydrogen taken up then become:
- methanogens: [η_M + b(1 − η_M)]/4;
- acetogens: [fη_A + b(1 − η_A)]/4.

| f | Q, b = 0 | Q, b = 0.5 | Q, b = 1 |
|---|---|---|---|
| 0 | unbounded | 16.7 | 8.63 |
| 0.5 | 2.00 | 1.85 | 1.73 |
| 0.9 | 1.15 | 1.12 | 1.09 |
| 1 | 1.047 | 1.022 | 1.000 |

- **At moderate f** biomass recycling matters little.
- **At f = 1** biomass export is the regulator's only lever, and recycling it
  closes the window.
- **With anoxic burial.** Kharecha et al.'s bulk burial efficiency of 0.2–2%
  implies b ≈ 0.98–0.998 if all remineralisation ends in methane. At f = 1
  that leaves Q − 1 ≈ 0.1% and a warming window of about 0.1 K.
- **Not computed.** The dynamical model has no b term, so margins with b > 0
  were not computed. By the Q1 law they would lengthen as 1/(Q − 1), but this
  is not shown.

## Q3. What must be true for f to be well below 1

A route counts as a sink only if it takes acetate's reducing equivalents out
of the methane system for longer than methane takes to respond. At the
reference supply the sink must take about 20 Tmol of acetate a year (C68),
whatever f is. That is roughly:
- 20 Tmol of sulfate a year, at one sulfate per acetate;
- or 160 Tmol of Fe(III) a year, at eight per acetate.

This planetary scale follows the assumed 10⁴-year methane lifetime and moves
inversely with it.

| Candidate sink | What it needs | Evidence file |
|---|---|---|
| Sulfate reduction | Sulfate delivered to the H₂-fed habitats at about the acetate flux | Lovley & Klug (1983): sulfate reducers win acetate and H₂ even at 60–105 μM in modern lakes. No Archean sulfate supply or concentration. |
| Fe(III) reduction | Ferric iron (photoferrotrophy or UV oxidation) at eight times the acetate flux | Silent |
| O₂, nitrate | Free oxidants | Silent; implicitly absent on an anoxic planet |
| Burial or long storage of acetate | Acetate retained for longer than the methane response | Silent on acetate. Bulk organic burial 0.2–2% (Kharecha et al. 2005) is not 1 − f. |
| Export to consumer-free settings | A sink there, or accumulation | The evidence file notes that missing consumers alone give accumulation, not a stationary flux |
| Assimilation by heterotrophs | That biomass then buried or oxidised | Covered by b (Q2) |

Against these:
- Kharecha et al. (2005) assume acetotrophic recycling.
- Syntrophic oxidation needs no acetoclastic organism (Zinder & Koch 1984).
- Fournier & Gogarten (2008) cannot exclude an ancient cleavage pathway.

**Two complications the model does not represent.**
- An oxidant that removes acetate would also feed sulfate- or iron-reducers
  that compete for H₂ directly. That is a third hydrogen sink, which changes
  the community, not just f.
- Syntrophic H₂ that escaped to space instead of reaching methanogens would
  be a sink. Syntrophy, however, requires its H₂ to be drawn down locally.

**Range supported.**
- For a strictly anoxic, sulfate-poor hazy Earth, the evidence supports f
  near 1 as the default. It also supports b near 1 on the bulk-burial figure.
- f well below 1 needs an oxidant supply of tens of Tmol a year, co-located
  with the hydrogen-fed habitats. The file neither supports nor excludes that.
- The file says f = 0 and 1 are end-members, "Neither is a best estimate."

**Where the evidence is silent:**
- Archean sulfate and Fe(III) delivery rates and where they reached;
- acetate residence times in Archean sediments and water columns;
- cold syntrophic kinetics;
- the fate of biomass beyond bulk burial;
- whether acetate-oxidising guilds would also take H₂.

## Q4. Proposed wording (for Barry's decision)

The regulator is strong only where hydrogen has a non-methane sink. Without
one it does not exist, and the paper should state this as its central
condition. Against changes in supply the sink sets the regulator's whole
range. Against imposed warming its effect is weaker, because the haze climate
is steep; the regulator vanishes only when acetate and biomass are both
recycled.

**§2.2.** Replace "a fraction f is recycled into methane and the rest leaves
by other routes:" with:

> a fraction f becomes methane, by acetate cleavage or by syntrophic
> oxidation followed by hydrogenotrophy, and the rest leaves the methane
> system, oxidised by an electron acceptor such as sulfate or exported and
> buried:

After "Their difference makes competition matter to climate.", add:

> This difference is the regulator's lever. At fixed supply the climate needs
> a fixed methane flux, so exact control holds T\* by sending the hydrogen
> above the methanogen-only level to a sink other than methane. If acetate
> and lost biomass both returned as methane, the two routes would yield the
> same methane and competition would not affect climate. We report f = 0 and
> 0.5, and f up to 1 in ESM S8.

**Table 1, acetate-fate row.**

| Field | Proposed text |
|---|---|
| Basis | Assumption: removal over 1 yr; fraction f to methane, the rest to a non-methane sink (oxidant, export or burial); lost biomass exported |
| Role | Sets the methane-yield contrast between routes, and so the supply window |
| Condition | Needs a non-methane hydrogen sink, about 20 Tmol acetate yr⁻¹ at the reference supply. The window ratio falls from 2.0 (f = 0.5) to 1.15 (0.9) and 1.05 (1), and closes at f = 1 if biomass also returns as methane |

**§4.4.** Open the section with:

> The regulator needs a fate for hydrogen other than methane. On an anoxic
> planet the default fate of acetate and of dead biomass is methane. An
> Archean carbon-cycle model assumes acetate recycling (Kharecha et al.
> 2005), syntrophic oxidation recovers acetate as methane without
> acetate-cleaving organisms (Zinder & Koch 1984), and bulk organic burial
> may have been only 0.2–2% (Kharecha et al. 2005). Acetate leaves the
> methane system only through an oxidant, such as sulfate (Lovley & Klug
> 1983) or ferric iron, or by export and burial. At the reference supply
> that sink must take about 20 Tmol of acetate a year, a third of the biotic
> methane flux in reducing equivalents. As recycling approaches completeness
> the supply window narrows from a factor of 2.0 to 1.05, and the window of
> imposed warming from 24 to 7 K. If biomass returns as methane too, both
> close. Where oxidants reached hydrogen-fed habitats, and in what amount,
> therefore sets where an Archean regulator could act.

Add to the mats paragraph's test sentence: "…and the share of acetate
oxidised by sulfate or iron rather than converted to methane would test the
condition itself." The ferric-iron citation is pending a source pass (Codex).

**§4.6.** Replace "The reference coexistence plateau requires different
effective methane yields; here those yields depend on recycling and biomass
retention." with:

> The regulator requires the two routes to differ in methane yield, and so a
> sink for hydrogen other than methane; the headline results use f = 0 and
> 0.5. As f rises towards 1 the supply window narrows as Q − 1 and the exact
> critical response time lengthens as 1/(Q − 1), from about 1 year at
> f = 0.5 to 21–31 years at f = 1. Graded states then follow supply more
> steeply (ESM S8).

**Abstract.** Recommend a change. After "…as hydrogen supply changes.", add:

> This needs a fate for hydrogen other than methane: if acetate returns as
> methane, the two routes converge. As acetate recycling rises from half to
> complete, the supply range held exactly shrinks from a factor of two to 5%,
> while the tolerated climate response time grows from about one year to two
> decades.

The "about seven years or less" sentence stays true of the 36 states it
counts, which use f ≤ 0.9. The new sentence shows that this limit depends on
f. Likewise C54's "no states between", the gap between exact states
(τ_c ≤ 7.08 yr) and graded states (≥ 331 yr), describes the C0/C1 inventory
only. Exact states at f = 0.95–1 fall inside that gap, at 10–31 yr. The draft
does not assert the gap, so no text changes. C54's limit field should record
the scope.

**Main message.** Recommend changing the first sentence to state the
condition (48 words in total):

> Microbes can hold a planet's temperature if some hydrogen avoids becoming
> methane, but exact control fails when climate responds slowly. …

The alternative is to leave the main message and carry the condition in the
abstract and §4.4. That is weaker: Barry's test was that if the regulator is
strong only where a sink exists, it is the central condition, and the
evidence says it is.

**ESM S8, on application.**
- Add a table with Q, τ_c, |S| and the imposed-warming window against f
  (C67).
- Add the biomass-recycling table (C68).
- State the 1/(Q − 1) law.

**Not done.**
- No dynamical biomass-recycling variant.
- No third hydrogen-consuming guild.
- The tuned 30-year dial points were not recomputed at higher f.
- Planetary oxidant supplies are not compared with the 20 Tmol yr⁻¹. That
  needs a verified source pass, which Codex is asked for.
