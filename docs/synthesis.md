# What the reconstructions show so far

*Living document, started 26 November 2026 after the fifth model family was
reconstructed. Update it as each new family is added.*

Terra Prisca rebuilds the classic models of Earth's long-term habitability,
one published paper at a time, before building anything new on them
([`vision.md`](vision.md)). Five families, seven papers, are now
reconstructed:

| Family | Papers | Question |
|---|---|---|
| [Daisyworld](../models/daisyworld/README.md) | Watson & Lovelock (1983) | Can life regulate climate without foresight? |
| [Energy balance](../models/budyko_sellers/README.md) | Budyko (1969); Sellers (1969) | When does the ice-albedo feedback run away to a frozen planet? |
| [Weathering thermostat](../models/walker_hays_kasting/README.md) | Walker, Hays & Kasting (1981), "WHK" | Can silicate weathering offset the faint young Sun? |
| [Biosphere lifespan](../models/biosphere_lifespan/README.md) | Lovelock & Whitfield (1982); Caldeira & Kasting (1992) | How long can plants keep going as the Sun brightens? |
| [Oxygen bistability](../models/goldblatt_lenton_watson/README.md) | Goldblatt, Lenton & Watson (2006), "GLW" | Why did oxygen jump at the Great Oxidation instead of creeping up? |

Each reconstruction follows one standard
([`reconstruction-lessons.md`](reconstruction-lessons.md)):
- The *faithful* build uses the equations and constants exactly as printed.
  Every choice the paper leaves open is recorded with its reason, and
  alternatives are kept as separately named *readings*.
- The model is scored against the paper's own figures. Scanned figures are
  digitised and distances measured in pixels of the scan (px). Figures
  published as vector drawings are read exactly, and distances measured in
  typographic points (pt, 1/72 inch on the printed page).
- *Nulls*, deliberately wrong models such as a constant, a shifted curve or a
  run with the forcing left out, show how large a score has to be to mean a
  miss.
- Each family is reviewed by an agent from another lab before it is merged.

This page asks three questions of each family. What holds? What can the
printed paper alone not reproduce? What stays open? It then draws out the
patterns that run across all five.

## The five families

### Daisyworld: Watson & Lovelock (1983)

**What holds.** Black and white daisies hold the planet's temperature nearly
constant over a wide range of solar luminosity, as the paper shows. The
occupied branches of Figs 1b–d and 2 lie on the printed curves (median
distance 0 px), and the analytical coexistence temperatures, 27.5 °C and
17.5 °C, are reproduced to 10⁻⁶ °C.

**What the printed paper cannot reproduce on its own.**
- Fig. 1a, the single-species "neutral daisy" run. The stated model lets
  neutral daisies persist only between luminosities 0.770 and 1.144 (in units
  of today's Sun). The printed hump has the right height but extends to 1.23,
  where the planet is at 42 °C and no daisy can grow. No numerical procedure
  tested reproduces it while keeping the other panels.
- The exact luminosities of the transitions. Establishment agrees to 0.001;
  collapses come 0.007–0.022 later in the paper than in the model, and white
  daisies re-establish 0.037 later on the way down. Incomplete settling would
  push them that way.

**What stays open.** The cause of Fig. 1a: a separate run that had not
settled, an unstated procedure, or an error in the original.

### Energy balance: Budyko (1969) and Sellers (1969)

**What holds.** Both papers' central result: a few per cent less sunlight
sends the ice to the equator.
- *Budyko.* The runaway comes at a 1.65% cut in radiation, against 1.63% in
  the figure and "1.6%" in the text, with the ice edge at 51.5°. Every
  perturbed temperature profile is within 1 °C RMS of the printed one, and
  the ice-free profile within 1.1 °C.
- *Sellers.* Today's climate is rebuilt from his tables alone, to 0.58 °C RMS.
  His solar constant S, 2.00 ly min⁻¹ (cal cm⁻² min⁻¹) today, sends the planet to
  ice at 1.9573 in the model against his 1.9544, 0.15% apart, and the frozen
  planet sits at −100 °C, as he says. Once frozen, it stays frozen: at
  S = 3.00, half as much sunlight again as today, it is still at −78 °C.

**What the printed paper cannot reproduce on its own.**
- *Budyko.* His insolation by latitude, Q(φ), is not printed, and the printed
  ice-edge branch is straighter than the model's: 2.3° further south at a
  1.5% cut. Q(φ) is the likeliest cause. His Fig. 3 labels the computed and
  observed temperature profiles the opposite way round from what Figs 4 and 6
  use, and the paper does not settle which is right.
- *Sellers.* Two inputs are unstated: the ocean fraction of each latitude
  circle, and a vapour-pressure formula. Varying them moves the fit to his
  Figs 2 and 3 (the RMS error in ocean heat transport rises from 0.90 to
  1.34 kly yr⁻¹ with band-mean ocean fractions) and changes no conclusion.
  His text gives 28 °C for the equator-to-pole temperature difference with
  doubled heat exchange, where his own Fig. 7 shows 20.9 °C and the model
  20.8 °C. His curve i, with 3% less sunlight and doubled heat exchange, is
  the middle of three equilibria; with equal heat capacity in every belt,
  that middle root is unstable, and the paper presents it as a climate. Near
  the jump to ice his states run about 2 °C colder than the model's. Neither
  band-mean ocean fractions nor a different vapour-pressure formula explains
  that offset.

**What stays open.** Budyko's Q(φ) table; which of his Fig. 3 curves is the
computed one; Sellers' own ocean fractions, which would test the
near-threshold offset; and where trajectories from Sellers' unstable root go,
which needs a time-dependent model with stated heat capacities.

### Weathering thermostat: Walker, Hays & Kasting (1981)

**What holds.** Everything the paper computes. Its Fig. 2, the CO₂ level and
surface temperature needed as the Sun brightens, is reproduced from the
printed equations alone, with nothing fitted: 0.005–0.009 decades RMS in CO₂
and 0.11–0.22 K in temperature. Every derived constant follows from its
stated ingredients, all five qualitative claims hold, and the feedback removes
"about a half" of the faint-Sun cooling at the faint-Sun end, as stated.

**What the printed paper cannot reproduce on its own.**
- How its CO₂ greenhouse law, eq. (5), was fitted to the radiative–convective
  runs of Owen et al. (1979). A fit through today's row and the 4.25 Gyr row,
  after a 5 K shift, comes closest (exponent 0.367 against the printed
  0.364), but the paper states neither the shift nor the rows. The law itself
  is printed in full, so the model reruns exactly.
- Two slips, corrected by the paper's own evidence. The text's 265 K is
  267 K by its own temperature equation, eq. (6). Fig. 1a's runoff axis,
  labelled in cm yr⁻¹, is plotted in mm yr⁻¹: only mm makes it agree with
  Table 1.

**What stays open.**
- The origins of the water-vapour greenhouse law, eq. (4) (Rodgers & Walshaw
  1966), and of the 14.1 K precipitation e-folding (Sellers 1965).
- How Meybeck (1979) averaged the river classes behind Table 1. Fig. 1a and
  Table 1 agree in 12 of 13 cells; the tropical 30–120 mm yr⁻¹ class implies
  162 mm yr⁻¹, which is a contradiction only if the class means are matched
  arithmetic averages.
- How fast the thermostat acts, which the paper never computes.

### Biosphere lifespan: Lovelock & Whitfield (1982) and Caldeira & Kasting (1992)

**What holds.**
- *Lovelock & Whitfield.* The paper has no equations; its model is a stated
  rule, √CO₂ falling linearly with luminosity between two dated anchors, and
  a drawn straight line for the Sun. The printed CO₂ line follows the rule to
  4.0 px RMS, and "about 100 Myr" holds: the rule gives 80 Myr and the
  printed lines 106–114 Myr.
- *Caldeira & Kasting.* The radiative fits of their Box 1 (the paper's boxed
  set of model equations) reproduce the hot phase directly, to within
  0.007 Gyr at 50–97 °C. With one unprinted quantity fitted (below), every
  curve of Fig. 2 lies within a median 2.4 px, and the stated lifespans hold
  to their rounding: 0.49 Gyr for a world of C₃ plants and 0.86 Gyr ("0.9")
  to the CO₂ limit of C₄ plants.
- *Between the two.* Swapping one ingredient at a time between the two
  faithful builds (80 Myr against 767 Myr to the plants' CO₂ limit, a ×9.6
  gap) attributes ×5.5 to the CO₂ law, ×2.2 to the plants and their
  threshold, and ×0.8 to the Sun law. Inside the CO₂ law, Caldeira &
  Kasting's stronger greenhouse and their weathering balance with a soil-CO₂
  pump contribute comparably: as productivity falls, weathering weakens and
  the Earth warms by 7–12 K on the way to the limit.

**What the printed paper cannot reproduce on its own.**
- *Lovelock & Whitfield.* The text's 7,000 ppm starting CO₂ should read
  70,000 ppm: the printed line starts at 71,900, and their cited source gives
  0.070 bar. Their luminosity law, from Newkirk (1980), survives only as the
  drawn line.
- *Caldeira & Kasting.* How strongly sulphur dioxide acidifies soil water as
  CO₂ falls. The equilibrium constants are cited, not printed. The printed
  figure needs the acidity to fall to 0.172 of today's by the kink where CO₂
  reaches the C₄ limit of 10 ppm; constants traced to the cited sources give
  a weaker fall and the C₄ limit at 0.77 Gyr. Eight unfitted readings of the
  sulphur chemistry were scored: the best match either the shape of the
  curves or the timing of the kink, and the fitted quantity is needed to
  match both. Two smaller slips: the text's "<0.2 Gyr" from 50 to 100 °C is
  0.227 Gyr to 97 °C in its own figure (0.226 Gyr in the model), and its
  "present level of 350 p.p.m." is 320 ppm in the model.

**What stays open.** The carbonate and sulphur constants Caldeira & Kasting
used (Stumm & Morgan 1981; Chameides 1984), and their unit and equilibration
conventions for SO₂; Newkirk's luminosity law; Hart (1978), the source of the
70,000 ppm anchor; and the source of Lovelock & Whitfield's "2/3 power"
alternative.

### Oxygen bistability: Goldblatt, Lenton & Watson (2006)

**What holds.** The bistability, quantitatively, and both of the paper's
triggers. Oxygen is measured in PAL, the present atmospheric level, and r is
the supply of reductants (mainly iron) that consume it.
- With the oxidation polynomial at full precision, every Fig. 2 curve lies
  within 0.030 pt of the published vector drawing, where shifted nulls miss
  by 10–15 pt.
- With the organic-burial constant β read from Fig. 3d, every main-panel
  trace of Fig. 3, and the oxygen and methane of both zooms, lies within
  0.021 pt (methane on the left-hand PAL scale; 0.11–0.25 pt on the
  captioned atm scale). The runs with the forcing left out miss the oxygen
  traces by 26–28 pt.
- At modern productivity two stable states coexist for r between
  1.337 × 10¹¹ and 5.519 × 10¹¹ mol yr⁻¹. A modest fall in r, or a 3% rise in
  productivity, switches oxygen from below 10⁻⁵ PAL to above 10⁻² PAL within
  1 Myr. Stepping r up to 7.5 × 10¹¹–10¹² mol yr⁻¹ switches it back in
  4.1–6.6 Myr, inside the stated 3–7 Myr.
- Claude Fable 5.2 (Anthropic), working in a separate session, rebuilt the
  steady states, folds and both transients independently and agrees with
  every number checked (reported by Barry W. Brook, 26 November 2026).

**What the printed paper cannot reproduce on its own.**
- The printed four-decimal polynomial. Its rounding moves the bistable range
  to 3.30 × 10¹¹–3.43 × 10¹², and neither Fig. 3 trigger can then be rerun.
  Goldblatt's later correction supplies the full coefficients; the paper's
  own Supplementary Fig. 3 recovers the bistability limits to 1%.
- The escape coefficient. The figures were drawn with 2.03 × 10⁻⁵ yr⁻¹, about
  half the 3.77 × 10⁻⁵ of the source it was scaled from. The later correction
  gives 3.7 × 10⁻⁵, which moves the bistable range to
  2.44 × 10¹¹–1.01 × 10¹² and keeps both triggers working.
- β for Fig. 3c–d. Those panels need 0.0020; the burial numbers in the
  Supplementary Information give 0.0027.
- The 4–9 °C of cooling. The runs the paper depicts give a twofold methane
  fall and 2.5–3.5 K; starting from the top of the iron-input range gives a
  5.35-fold fall and 6.9–8.5 K.
- Smaller slips. The Fig. 2b caption's reductant input is ten times too
  small. Supplementary Fig. 3 labels as the oxidation parameter Ψ a quantity
  half as large. "1 × 10⁹ PAL" should read 10⁻⁹ (the simplified and full
  equations agree above about 10⁻⁸). The stated transition times, 150 and
  50 kyr, differ threefold where the printed zooms switch together. The zoom
  panels of the redox budget sit 4–12% away from the main panels.

**What stays open.** Why β is 0.0020; which run gave 4–9 °C; which forcing
the reverse switch used (closer to the upper fold it takes 12–25 Myr); how
"transition time" was clocked; what the biological thresholds mean
operationally; and how the escape coefficients were derived.

## Patterns across the five

### Every headline conclusion survives

Daisy homeostasis, the ice-albedo runaway, the weathering thermostat, a finite
biosphere lifespan set by falling CO₂, and the bistability of oxygen all
reproduce from the equations as printed, or once the unprinted input or
corrected parameter is supplied. The quantitative claims these papers are
remembered for hold to the precision they were stated, with the exceptions
listed under each family.

### What a paper prints in full reruns; what it cites is where the gaps are

Everything the seven papers print in full reproduces: Budyko's and Sellers'
balances, WHK's equations, Lovelock & Whitfield's rule, Caldeira & Kasting's
radiative fits, and GLW's equations. The gaps sit in numbers a paper took from
elsewhere and printed in part or not at all:

| Paper | Taken from elsewhere | Effect |
|---|---|---|
| Budyko | insolation by latitude | the ice-edge branch's shape, within 2.3° |
| Sellers | ocean fraction of each latitude circle | small changes to Figs 2–3, no conclusion changed |
| WHK | how eq. (5) was fitted to Owen et al. | nothing: the law is printed in full |
| Lovelock & Whitfield | Newkirk's luminosity law | survives only as the drawn line |
| Caldeira & Kasting | carbonate and sulphur constants | one quantity fitted; C₄ limit at 0.77 Gyr without it |
| GLW | the fit to photochemical models, printed to four decimals | Fig. 3 cannot be rerun without the author's later correction |

GLW is the clearest case: compressing a larger model into a polynomial and
rounding it lost the printed result. The one gap of a different kind is
Daisyworld's Fig. 1a, which no stated procedure produces. Archiving code and
full-precision parameters with a paper closes this kind of gap.

### Prose slips; computed figures hold

Each family has places where the prose, a caption or an axis label disagrees
with the paper's own computed figure or equations. In each of these the
reconstruction sides with the computed result:

| Paper | Prose, caption or label | The paper's own figure or equations | Reconstruction |
|---|---|---|---|
| Sellers | doubled-exchange equator–pole difference, 28 °C | Fig. 7 shows 20.9 °C | 20.8 °C |
| WHK | ΔT = −18 K "or T = 265 K" | eq. (6) gives 267 K | 267.0 K |
| WHK | runoff axis in cm yr⁻¹ | agrees with Table 1 only in mm yr⁻¹ | mm yr⁻¹ |
| Lovelock & Whitfield | starting CO₂ 7,000 ppm | line starts at 71,900 ppm | 70,000 ppm fits |
| Caldeira & Kasting | 50 to 100 °C in "<0.2 Gyr" | figure takes 0.227 Gyr to 97 °C | 0.226 Gyr |
| GLW | Fig. 2b dashed curve at r = 3 × 10¹⁰ | drawn curve is r = 3 × 10¹¹ | 3 × 10¹¹ fits to 0.023 pt |
| GLW | Supplementary Fig. 3 axis "Ψ" | line sits at Ψ/2 | Ψ/2 |
| GLW | transitions in 150 and 50 kyr | the two zooms switch together | switches together |

The drawings themselves depart from the equations, or from each other, in
four places: Daisyworld's Fig. 1a; GLW's budget zooms, 4–12% off its main
panels; Lovelock & Whitfield's CO₂ line, 2.3% steeper than their rule (it
passes 354 ppm today, against the rule's 320); and their glaciations, drawn
at 4 °C against the text's 5–10 °C. Budyko's Fig. 3, whose labels disagree
with his Figs 4 and 6, is unresolved.

### Tipping points survive; their exact positions are the most sensitive numbers

Every threshold the papers report is found in the reconstruction: the daisy
transitions, Budyko's and Sellers' runaways to ice, the plants' CO₂ limits,
and GLW's folds. Their exact positions are where small unprinted details show
first:
- Daisyworld's populations lie on the printed curves, while its collapse and
  re-establishment luminosities differ by 0.007–0.037.
- Sellers' jump to ice agrees to 0.15% of S, while the states just above it
  run 2 °C cold.
- Caldeira & Kasting's hot phase reproduces to 0.5%; the C₄ limit moves 11%
  with the sulphur constants.
- GLW's folds match the drawing with the full-precision polynomial and move
  by factors of 2.5–6 with the printed one.

Near a threshold the system relaxes slowly and the curves are steep, so small
differences in procedure or input show there first.

### Three of the five families turn on more than one stable state

Daisyworld, Budyko–Sellers and GLW are all about hysteresis: a system pushed
past a threshold stays in its new state when the push is removed. Budyko and
GLW identified their unstable branches and used them in the argument, and GLW's
stability analysis reproduces exactly. Sellers presented an unstable root as
a climate. The two thermostat families, WHK and the lifespan papers, have a
single equilibrium at each brightness and move smoothly along it.

### What stays open lies mostly one citation upstream

Most open items need a source that sits behind the paper:

| Source | Would settle |
|---|---|
| Budyko's insolation table, probably from the *Atlas of the Heat Balance of the Earth* (1963) | the shape of the printed ice-edge branch |
| Sellers (1965), *Physical Climatology* | Sellers' ocean fractions and near-threshold offset; WHK's 14.1 K |
| Rodgers & Walshaw (1966) | WHK's eq. (4) |
| Meybeck (1979) | WHK's Table 1 averaging |
| Newkirk (1980); Hart (1978) | Lovelock & Whitfield's luminosity law and CO₂ anchor |
| Stumm & Morgan (1981); Chameides (1984) | Caldeira & Kasting's carbonate and sulphur constants |

The rest need the original authors' runs or code: Daisyworld's Fig. 1a,
Caldeira & Kasting's SO₂ conventions, GLW's β, the run behind its 4–9 °C, its
reverse forcing, and the clocks and thresholds it leaves undefined.

## Scope and limits

- "Holds" means the model reproduces what the paper printed. Whether the
  paper's physics describes the real Earth is a separate question, which the
  re-imaginings in [`vision.md`](vision.md) take up.
- A model's fit to today's state says little on its own: where a model is
  calibrated to today, observations fit about as well as the model does
  (Sellers' observed temperatures score 0.55 °C against the model's 0.58 °C).
  The tests that discriminate are the perturbed runs and the nulls.
- Scores are in each figure's own units: px of a scan, pt of a vector drawing,
  or degrees and decades where a curve was digitised to values. They compare
  readings within a family against that family's nulls and are not comparable
  across families.
- Each family was built and cross-reviewed between Claude (Anthropic) and
  Codex (OpenAI). Gemini 4 Carbon (Google) also reviewed WHK, the
  biosphere-lifespan family and GLW, and Claude Fable 5.2 rebuilt the
  biosphere-lifespan and GLW families independently. The patterns above rest
  on seven papers: enough to suggest them, too few to establish them as rules
  for the field.
- Sources not in hand are listed above as open items. Where the
  reconstructions use them, they rely on the papers' own statements or on
  secondary compilations citing them.

## Who wrote this page

Claude (Opus 5.5, Anthropic) drafted it from the five model pages at Barry
W. Brook's request. Gemini 4 Neon (Google, through the Antigravity command
line) reviewed it (findings SYN-G1 to G15, board thread 197), and the
findings are addressed here.
