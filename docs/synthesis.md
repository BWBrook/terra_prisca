# What the reconstructions show so far

*Living document, started 26 November 2026 after the fifth model family was
reconstructed. Update it as each new family is added.*

Terra Prisca rebuilds the classic models of Earth's long-term habitability,
one published paper at a time, before building anything new on them
([`vision.md`](vision.md)). Five families are now reconstructed:

| Family | Papers | Question |
|---|---|---|
| [Daisyworld](../models/daisyworld/README.md) | Watson & Lovelock (1983) | Can life regulate climate without foresight? |
| [Energy balance](../models/budyko_sellers/README.md) | Budyko (1969); Sellers (1969) | When does the ice-albedo feedback run away to a frozen planet? |
| [Weathering thermostat](../models/walker_hays_kasting/README.md) | Walker, Hays & Kasting (1981) | Can silicate weathering offset the faint young Sun? |
| [Biosphere lifespan](../models/biosphere_lifespan/README.md) | Lovelock & Whitfield (1982); Caldeira & Kasting (1992) | How long can plants keep going as the Sun brightens? |
| [Oxygen bistability](../models/goldblatt_lenton_watson/README.md) | Goldblatt, Lenton & Watson (2006) | Why did oxygen jump at the Great Oxidation instead of creeping up? |

Each reconstruction follows one standard
([`reconstruction-lessons.md`](reconstruction-lessons.md)). The *faithful*
build uses the equations and constants exactly as printed. Every choice the
paper leaves open is recorded with its reason. Alternatives that depart from
the printed text are kept as separately named *readings*. The model is scored
against the paper's own figures, digitised from the scan or, for vector
figures, read exactly from the drawing. *Nulls*, deliberately wrong models
such as a constant or a shifted curve, show how large a score has to be to
mean a miss. Each family was reviewed by an agent from another lab before it
was merged.

This page asks the same three questions of each family. What holds? What can
the printed paper alone not reproduce? What stays open? It then draws out the
patterns that run across all five.

## The five families

### Daisyworld: Watson & Lovelock (1983)

**What holds.** Black and white daisies hold the planet's temperature nearly
constant over a wide range of solar luminosity, as the paper shows. The
occupied branches of Figs 1b–d and 2 lie on the printed curves, and the
luminosities at which daisies establish agree to 0.001 (on a luminosity axis
running 0.5–1.7). The analytical coexistence temperatures, 27.5 °C and
17.5 °C, are reproduced to 10⁻⁶ °C.

**What the printed paper cannot reproduce on its own.** Fig. 1a, the
single-species "neutral daisy" run. The stated model lets neutral daisies
persist only between luminosities 0.770 and 1.144. The printed hump has the
right height but extends to 1.23, where the planet is at 42 °C and no daisy can
grow. No numerical procedure tested reproduces it while keeping the other
panels. The populations in the other panels collapse 0.007–0.022 later in
luminosity than the model's, the direction incomplete settling would push
them.

**What stays open.** The cause of Fig. 1a: a separate run that had not
settled, an unstated procedure, or an error in the original.

### Energy balance: Budyko (1969) and Sellers (1969)

**What holds.** Both papers' central result: a few per cent less sunlight
sends the ice to the equator.
- *Budyko.* The runaway comes at a 1.65% cut in radiation, against 1.63% in
  the figure and "1.6%" in the text, with the ice edge at 51.5°. Every
  perturbed temperature profile is within 1 °C RMS of the printed one.
- *Sellers.* Today's climate is rebuilt from his tables alone, to 0.58 °C RMS.
  The jump to ice comes at S = 1.9573 against his 1.9544, 0.15% apart, and
  the frozen planet sits at −100 °C, as he says.

**What the printed paper cannot reproduce on its own.**
- *Budyko.* His insolation table Q(φ) is not printed, and the printed ice-edge
  branch is straighter than the model's: 2.3° further south at a 1.5% cut. Q(φ)
  is the likeliest cause. His Fig. 3 labels the computed and observed
  temperature profiles in the opposite way to what Figs 4 and 6 use.
- *Sellers.* Two inputs are unstated (the ocean fraction of each belt and a
  vapour-pressure formula); neither changes any score. His curve i, with 3%
  less sunlight and doubled heat exchange, is the middle of three equilibria,
  and under an equal heat capacity in every belt that middle root is unstable.
  Sellers plotted it as a climate; the paper does not mention the other two.
  Near the jump to ice his states run about 2 °C colder than the model's, for
  reasons neither unstated input explains.

**What stays open.** Budyko's Q(φ) table; which Fig. 3 curve is the computed
one; Sellers' ocean fractions; the near-threshold offset; and where
trajectories from Sellers' unstable root actually go, which needs a
time-dependent model with stated heat capacities.

### Weathering thermostat: Walker, Hays & Kasting (1981)

**What holds.** Everything the paper computes. Fig. 2 is reproduced from the
printed equations alone, with nothing fitted: 0.005–0.009 decades RMS in CO₂
and 0.11–0.22 K in temperature. Every derived constant follows from its stated
ingredients, all five qualitative claims hold, and "about a half" of the
faint-Sun cooling is removed at the faint-Sun end, as stated.

**What the printed paper cannot reproduce on its own.** How its greenhouse
law, eq. (5), was fitted to Owen et al. (1979). A two-point fit through
today's row and the 4.25 Gyr row, after a 5 K shift, comes closest
(exponent 0.367 against the printed 0.364), but the paper states neither the
shift nor the rows. Two printed slips are corrected by the paper's own
evidence: the text's 265 K is 267 K by its own equation, and Fig. 1a's runoff
axis, labelled in cm yr⁻¹, is plotted in mm yr⁻¹.

**What stays open.** The origins of eq. (4) (Rodgers & Walshaw 1966) and of the
14.1 K precipitation e-folding (Sellers 1965); how Meybeck (1979) averaged the
river classes behind Table 1; and the thermostat's response time, which the
paper never computes.

### Biosphere lifespan: Lovelock & Whitfield (1982) and Caldeira & Kasting (1992)

**What holds.**
- *Lovelock & Whitfield.* Their CO₂ line is their stated rule, √CO₂ falling
  linearly with luminosity, to 4.0 px RMS. "About 100 Myr" holds: the rule
  gives 80 Myr and the printed lines 106–114 Myr.
- *Caldeira & Kasting.* Their Box 1 reproduces all five curves of Fig. 2
  (median 2.4 px) once one unprinted quantity is fitted. The stated lifespans
  then hold to their rounding: 0.49 Gyr for a world of C₃ plants, 0.86 Gyr
  ("0.9") to the C₄ limit.
- *Between the two.* Swapping one ingredient at a time attributes the ninefold
  gap between their times to the CO₂ limit: ×5.5 from the CO₂ law, ×2.2 from
  the plants and their threshold, and ×0.8 from the Sun law.

**What the printed paper cannot reproduce on its own.**
- *Lovelock & Whitfield.* The text's 7,000 ppm starting CO₂ should read
  70,000 ppm; the printed line starts at 71,900, and their cited source gives
  0.070 bar. Their luminosity law survives only as the drawn line.
- *Caldeira & Kasting.* How strongly sulphur acidifies soil water as CO₂ falls.
  The printed figure needs the acidity to fall to 0.172 of today's by the
  10 ppm kink; the constants traced to the paper's sources give a weaker fall
  and a C₄ limit at 0.77 Gyr. Eight unfitted readings of the sulphur chemistry
  were scored: the best of them match either the shape of the curves or the
  timing of the kink, and the fitted quantity is needed to match both.

**What stays open.** The constants and conventions Caldeira & Kasting used
for the sulphur term (Chameides 1984; Stumm & Morgan 1981); Newkirk's (1980)
luminosity law; Hart (1978); and the source of Lovelock & Whitfield's
"2/3 power" alternative.

### Oxygen bistability: Goldblatt, Lenton & Watson (2006)

**What holds.** The bistability, quantitatively, and both of the paper's
triggers. With the oxidation polynomial at full precision, every Fig. 2 curve
lies within 0.030 pt of the published vector drawing and every Fig. 3 trace
within 0.021 pt, where shifted nulls miss by 11–15 pt. At modern productivity
two stable states coexist for reductant inputs of
1.337–5.519 × 10¹¹ mol yr⁻¹. A modest fall in reductant input, or a small rise
in productivity, switches oxygen from below 10⁻⁵ to above 10⁻² of the present
atmospheric level within 1 Myr, and the return takes 3–7 Myr. Fable (Claude)
rebuilt the steady states, folds and both transients independently and agrees
with every number checked.

**What the printed paper cannot reproduce on its own.**
- The printed four-decimal polynomial. Its rounding moves the bistable range
  to 3.30 × 10¹¹–3.43 × 10¹², and neither Fig. 3 trigger can then be rerun.
  Goldblatt's later correction supplies the full coefficients; the paper's
  own Supplementary Fig. 3 recovers the bistability limits to 1%.
- The escape coefficient. The figures were drawn with 2.03 × 10⁻⁵ yr⁻¹, about
  half the 3.77 × 10⁻⁵ of the source it was scaled from. The later correction
  gives 3.7 × 10⁻⁵, which moves the bistable range to
  2.44 × 10¹¹–1.01 × 10¹² and keeps both triggers working.
- The organic-burial constant β. The figures need 0.0020; the Supplementary
  Information's burial numbers give 0.0027.
- The 4–9 °C of cooling. The runs the paper depicts give a twofold methane
  fall and 2.5–3.5 K; starting from the top of the iron-input range gives a
  5.35-fold fall and 6.9–8.5 K.
- Smaller slips: the Fig. 2b caption's reductant input is ten times too small;
  Supplementary Fig. 3 labels as Ψ a quantity half as large; "1 × 10⁹ PAL"
  should read 10⁻⁹ (the simplified and full equations agree above about
  10⁻⁸); the stated transition times differ threefold where
  the printed zooms switch together.

**What stays open.** Why β is 0.0020; which run gave 4–9 °C; how
"transition time" was clocked; what the biological thresholds mean
operationally; and how the escape coefficients were derived.

## Patterns across the five

### Every headline conclusion survives

Daisy homeostasis, the ice-albedo runaway, the weathering thermostat, a finite
biosphere lifespan set by falling CO₂, and the bistability of oxygen all
reproduce from the equations as printed, or with the one missing quantity
supplied. The quantitative claims these papers are remembered for hold to the
precision they were stated, with the exceptions listed under each family.

### Thresholds are the best-preserved numbers

The tipping points reproduce more tightly than anything else:

| Threshold | Paper | Reconstruction |
|---|---|---|
| Daisy establishment (luminosity) | 0.714 | 0.713 |
| Budyko runaway (radiation cut) | 1.63% | 1.65% |
| Sellers jump to ice (S) | 1.9544 | 1.9573 |
| GLW folds (reductant input at modern productivity) | as drawn | within 0.008 decades of the drawing |

The behaviour just beside a threshold is the most fragile: daisies collapse
0.007–0.022 late, and Sellers' states near the jump run 2 °C cold. Close to a
threshold the system relaxes slowly and the curves are steep, so small
differences in procedure or input show up there first.

### When a paper disagrees with itself, the drawing is right

Each family has places where the prose, a caption or an axis label disagrees
with the paper's own figure or equations. In every case but one, the
reconstruction sides with the drawn result:

| Family | Prose, caption or label | The paper's own figure or equations | Reconstruction |
|---|---|---|---|
| Budyko | Fig. 3: dashed curve is the computed profile | Figs 4 and 6 draw the solid one as computed | matches the solid one |
| Sellers | K×2 equator–pole difference 28 °C | Fig. 7 curve g, 20.9 °C | 20.8 °C |
| WHK | ΔT = −18 K "or T = 265 K" | eq. (6) gives 267 K | 267.0 K |
| WHK | runoff axis in cm yr⁻¹ | values agree with Table 1 only in mm yr⁻¹ | mm yr⁻¹ |
| Lovelock & Whitfield | 7,000 ppm | line starts at 71,900 ppm | 70,000 ppm fits |
| Caldeira & Kasting | 50 to 100 °C in "<0.2 Gyr" | figure takes 0.227 Gyr to 97 °C | 0.226 Gyr |
| GLW | Fig. 2b dashed curve at r = 3 × 10¹⁰ | drawn curve is r = 3 × 10¹¹ | 3 × 10¹¹ fits to 0.023 pt |
| GLW | Supplementary Fig. 3 axis "Ψ" | line sits at Ψ/2 | Ψ/2 |
| GLW | transitions in 150 and 50 kyr | the two zooms switch together | switches together |

The exception is Daisyworld's Fig. 1a, where the drawing itself departs from
the stated model. Elsewhere the computed figures are the more reliable record,
and the prose carries the slips.

### Reproducibility leaks where a paper embeds a fit to a larger model

Four of the seven papers (Watson & Lovelock, Budyko, Sellers, Lovelock &
Whitfield) are self-contained equations. Each reruns from the printed page,
supplied at most with a standard input the paper names but does not tabulate,
such as Budyko's insolation profile or Sellers' ocean fractions. Daisyworld's
Fig. 1a is the one result among them that no stated procedure gives. Three
papers embed a fit to a bigger model they did not print:
- WHK's greenhouse law is a fit to Owen et al.'s radiative–convective runs.
  The fit is printed in full, so the model reruns exactly; only its derivation
  is undocumented.
- Caldeira & Kasting's Box 1 fits a radiative–convective model and soil
  chemistry. One quantity in it is unprinted and has to be fitted to their
  figure.
- Goldblatt, Lenton & Watson's oxidation polynomial fits photochemical model
  runs. Printed to four decimals, it loses the result; the author's later
  correction restores it.

The pattern sharpens with time. The 1969–1983 models are a handful of
equations a reader can rerun from the page; the 1992 and 2006 models carry
compressed versions of other models, and those compressions are where the
printed record falls short. The full-precision numbers survived for GLW
because the author published them later. Archiving code and full-precision
parameters with the paper closes this gap.

### What stays open lies mostly one citation upstream

Most open items need a source that sits behind the paper:

| Source | Would settle |
|---|---|
| Budyko's insolation table, probably from the *Atlas of the Heat Balance of the Earth* (1963) | the straighter printed ice-edge branch |
| Sellers (1965), *Physical Climatology* | Sellers' ocean fractions and near-threshold offset; WHK's 14.1 K |
| Rodgers & Walshaw (1966) | WHK's eq. (4) |
| Meybeck (1979) | WHK's Table 1 averaging |
| Newkirk (1980); Hart (1978) | Lovelock & Whitfield's luminosity law and CO₂ anchor |
| Chameides (1984); Stumm & Morgan (1981) | Caldeira & Kasting's sulphur constants |

The remaining open items need the original authors' runs: Daisyworld's
Fig. 1a, GLW's β and the run behind 4–9 °C, and the clocks and thresholds that
GLW leaves undefined.

### Four of the five families turn on more than one stable state

Daisyworld, Budyko–Sellers and GLW are all about hysteresis: a system that,
pushed past a threshold, stays in its new state when the push is removed.
Budyko and GLW drew their unstable branches and used them in the argument;
GLW's stability analysis reproduces exactly. Sellers plotted an unstable root
as a climate. The two thermostat families, WHK and the
lifespan papers, have a single equilibrium at each brightness and move
smoothly along it.

## Scope and limits

- "Holds" means the model reproduces what the paper printed. Whether the
  paper's physics describes the real Earth is a separate question, which the
  re-imaginings in [`vision.md`](vision.md) take up.
- Scores are in each figure's own units: pixels of the scanned page for the
  older papers, points of the vector drawing for GLW, and degrees or decades
  where a curve was digitised to values. They compare readings within a
  family, against that family's nulls, and are not comparable across
  families.
- Each family was built and cross-reviewed between Claude (Anthropic) and
  Codex (OpenAI). Gemini 4 Carbon (Google) also reviewed WHK, the
  biosphere-lifespan family and GLW, and Fable (Claude) rebuilt the
  biosphere-lifespan and GLW families independently. The patterns above rest on seven papers,
  which is enough to suggest them and too few to establish them as rules for
  the field.
- Sources that were not in hand are listed above as open items; the
  reconstructions rely on the papers' own statements about them.

## Who wrote this page

Claude (Opus 5.5, Anthropic) drafted it from the five model pages, at Barry
W. Brook's request. Gemini 4 Carbon (Google, through Antigravity) reviewed it;
the review is on the correspondence board.
