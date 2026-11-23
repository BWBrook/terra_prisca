# Life span of the biosphere

Two papers ran the silicate-weathering thermostat of
[Walker, Hays & Kasting (1981)](../walker_hays_kasting/README.md) forward in
time to ask how long the biosphere has left:

- Lovelock & Whitfield (1982), *Nature* 296, 561–563: about 100 Myr.
- Caldeira & Kasting (1992), *Nature* 360, 721–723: about 0.9 Gyr to the C₄
  limit, 0.5 Gyr for a C₃-only world.

This page holds both faithful reconstructions and, separately, an analysis
that swaps one ingredient at a time between them to attribute the gap
between their lifespans.

Status: **Lovelock & Whitfield approved by Codex (1d7cd5d); Caldeira &
Kasting approved by Codex (19efb5e); ingredient swap in review** (board
thread 183).

## Sources

All citations were checked against Crossref on 16 November 2026.

- Lovelock, J. E. & Whitfield, M. (1982). Life span of the biosphere.
  *Nature* 296(5857), 561–563.
  [doi:10.1038/296561a0](https://doi.org/10.1038/296561a0).
  Publisher PDF supplied by Barry: three pages of 220-ppi colour JPEG scans
  with an OCR layer, SHA-256
  `d763245eb2867e041766f6a6ab2d04013b30749eeb938d794b6c8c07477eeab3`.
- Caldeira, K. & Kasting, J. F. (1992). The life span of the biosphere
  revisited. *Nature* 360(6406), 721–723.
  [doi:10.1038/360721a0](https://doi.org/10.1038/360721a0).
  Publisher PDF supplied by Barry: three pages of 650-ppi bilevel scans with
  an OCR layer, SHA-256
  `3fc7926249fdb3faa961e21f3d34029b68e7f7ec1e7549ad6cb34904a250b7b9`.
- Equation and data sources, also in hand:
  - Owen, Cess & Ramanathan (1979), [doi:10.1038/277640a0](https://doi.org/10.1038/277640a0);
  - Gough (1981), [doi:10.1007/BF00151270](https://doi.org/10.1007/BF00151270);
  - Volk (1987), [doi:10.2475/ajs.287.8.763](https://doi.org/10.2475/ajs.287.8.763);
  - Kasting (1988), [doi:10.1016/0019-1035(88)90116-9](https://doi.org/10.1016/0019-1035(88)90116-9);
  - Kasting, Whitmire & Reynolds (1993), [doi:10.1006/icar.1993.1010](https://doi.org/10.1006/icar.1993.1010);
  - Caldeira (1991), [doi:10.1130/0091-7613(1991)019<0204:CPCPAT>2.3.CO;2](https://doi.org/10.1130/0091-7613(1991)019%3C0204:CPCPAT%3E2.3.CO;2).
- Lovelock & Whitfield's luminosity source, Newkirk (1980), *Geochim.
  Cosmochim. Acta Suppl.* 13, 293, is not in hand.
- Caldeira & Kasting's sources for the equilibrium constants are not in hand:
  Stumm & Morgan, *Aquatic Chemistry* (Wiley, 1981), for carbonate, and
  Chameides (1984), *J. Geophys. Res.* 89, 4739–4755,
  [doi:10.1029/JD089iD03p04739](https://doi.org/10.1029/JD089iD03p04739),
  for sulphur. Sander's Henry's-law compilation (henrys-law.org, read
  21 November 2026) lists Chameides' Henry constants: 1.216 M atm⁻¹ for SO₂
  and 0.0314 M atm⁻¹ for CO₂.
- Secondary sources for those constants, as one-page extracts placed by Codex
  in `local/sources/biosphere_lifespan/`:
  - Butler, J. N. (1991). *Carbon Dioxide Equilibria and Their Applications*,
    Table 2.2, p. 17: Stumm & Morgan's selected carbonate constants (K_H, K₁,
    K₂; the table's footnote credits them also with the calcite solubility
    product, unused here), 0–50 °C, and pK_w, which the footnote traces to
    Sillén & Martell's compilation rather than to Stumm & Morgan.
    Routledge reissue [doi:10.1201/9781315138770](https://doi.org/10.1201/9781315138770).
    Extract SHA-256 `b2f843005745bf08159cbc3c49e6ccb5fcadc344b4c888b0dcdb7052ff6af063`.
  - Sellegri, K. et al. (2003). Contribution of gaseous and particulate
    species to droplet solute composition at the Puy de Dôme, France.
    *Atmos. Chem. Phys.* 3, 1509–1522, Table 5, p. 1517: S(IV) dissociation
    constants attributed to Chameides (1984).
    [doi:10.5194/acp-3-1509-2003](https://doi.org/10.5194/acp-3-1509-2003).
    Extract SHA-256 `4c4a8b2c9af892fd575e5fac0aac0aa07bb6978c70932a2cb01519801e9417e3`.

All of these are copyrighted and are not redistributed. Place them in
`local/sources/biosphere_lifespan/`; the scan scripts refuse any file with a
different hash. The overlay figures plot values digitised from the scans,
never the scans themselves.

## Code

| File | Contents |
|---|---|
| [`lw1982.py`](../../src/terra_prisca/biosphere_lifespan/lw1982.py) | Lovelock & Whitfield's rule, its readings, a variant and a control |
| [`scan_lw1982.py`](../../src/terra_prisca/biosphere_lifespan/scan_lw1982.py) | Calibration and tracing of their Fig. 2 |
| [`fidelity_lw1982.py`](../../src/terra_prisca/biosphere_lifespan/fidelity_lw1982.py) | Scores, lifespans, band and claims; writes `fidelity/lw1982_*` |
| [`figures_lw1982.py`](../../src/terra_prisca/biosphere_lifespan/figures_lw1982.py) | The reconstructed Fig. 2; writes `figures/lw1982_fig2.*` |
| [`tests/test_lw1982.py`](../../tests/test_lw1982.py) | Anchors, closed forms, the WHK import, controls, and the scan test |
| [`ck1992.py`](../../src/terra_prisca/biosphere_lifespan/ck1992.py) | Caldeira & Kasting's Box 1 model, its readings, the C₃ run and controls |
| [`scan_ck1992.py`](../../src/terra_prisca/biosphere_lifespan/scan_ck1992.py) | Calibration and tracing of their Fig. 2 |
| [`fidelity_ck1992.py`](../../src/terra_prisca/biosphere_lifespan/fidelity_ck1992.py) | Scores, two-way distances, events and claims; writes `fidelity/ck1992_*` |
| [`figures_ck1992.py`](../../src/terra_prisca/biosphere_lifespan/figures_ck1992.py) | The reconstructed Fig. 2; writes `figures/ck1992_fig2.*` |
| [`tests/test_ck1992.py`](../../tests/test_ck1992.py) | Equations, root uniqueness, present-day closure, the WHK import, controls, and the scan test |
| [`ingredient_swap.py`](../../src/terra_prisca/biosphere_lifespan/ingredient_swap.py) | The analysis swapping ingredients between the two models; writes `swap/ingredient_swap*` |
| [`tests/test_ingredient_swap.py`](../../tests/test_ingredient_swap.py) | Endpoints equal the faithful models, weathering balance in each cell, Shapley sums, threshold invariance |

```bash
uv run python -m terra_prisca.biosphere_lifespan.figures_lw1982
uv run python -m terra_prisca.biosphere_lifespan.fidelity_lw1982
uv run python -m terra_prisca.biosphere_lifespan.figures_ck1992
uv run python -m terra_prisca.biosphere_lifespan.fidelity_ck1992
uv run python -m terra_prisca.biosphere_lifespan.ingredient_swap
uv run pytest tests/test_lw1982.py tests/test_ck1992.py tests/test_ingredient_swap.py
```

Every committed CSV is regenerated byte for byte by the tests.

## Lovelock & Whitfield (1982)

### The model as published

The paper has no equations. Its arithmetic is stated in the text and drawn in
Fig. 2, as straight lines against time t (Myr from the present):

1. **The Sun.** Luminosity rises along a straight line, after Newkirk (1980),
   from about 0.71 of today's at −4,000 Myr to about 1.15 at +2,000 Myr.
2. **CO₂ at constant temperature.** "A linear relationship between the square
   root of the CO₂ pressure and the solar luminosity for a constant mean
   temperature", anchored at a stated partial pressure 3,500 Myr ago
   (refs 4 and 17: Owen et al. 1979 and Hart 1978) and 320 ppm today.
3. **The limit.** 150 ppm is "the lower limit tolerable for photosynthesis".
   Extrapolating the decline, it "will be reached in about 100 Myr".

Fig. 2 also draws a band of probable past mean temperatures. It is set by
stated assumptions about prokaryote limits and glaciations, not computed.
Fig. 1 is a conceptual diagram of the biological and geological feedback loop
and carries no numbers, so Fig. 2 and the text supply every quantitative
target.

With luminosity linear in time and √C linear in luminosity, √C is linear in
time, and the luminosity slope cancels:

  Δt = 3,500 Myr × (√320 − √150) / (√C_past − √320).

The span to the limit therefore depends on the two dated anchors and the
shape of the rule, not on how fast the Sun brightens. A Sun law of a different
shape does change it (below).

### Interpretive choices

| Choice | Adopted | Reason |
|---|---|---|
| Luminosity law | Straight line, L = 1 + 0.0733 t/Gyr | The paper gives no formula and Newkirk (1980) is not in hand. The printed Sun line is straight to 0.55 px RMS, and its slope is read from the scan. Gough's (1981) curved law and Owen et al.'s linear 75% at 4,500 Myr are scored as nulls |
| CO₂ 3,500 Myr ago | **70,000 ppm** | The text prints 7,000 ppm, citing Owen et al. (1979) and Hart (1978). Owen et al.'s Table 1 gives 0.070 bar at 3.5 Gyr and attributes its CO₂ history to Hart, which is not in hand. The printed line starts at 71,900 ppm, and only 70,000 gives the stated span. 7,000 is kept as a scored, rejected reading |
| "2/3 power relationship" | C^(2/3) linear in L, with the same anchors | The natural reading of "a 2/3 power relationship might be more appropriate" in place of the square root. WHK's published eq. (6) implies a different law (below) |
| Constant temperature | Implicit in the rule | The paper has no climate model. The WHK reading supplies one through the [`whk1981`](../../src/terra_prisca/walker_hays_kasting/whk1981.py) import |
| WHK's P₀ | 320 ppm | WHK leave P₀ as "present"; Lovelock & Whitfield's present is 320 ppm |
| The limit | 150 ppm exactly | As stated |
| Where a rule ends | No value (NaN) | The two-point rules end where C^power would reach zero (the faithful one at +254 Myr). WHK eq. (6) at constant temperature ends where it would need P ≤ 0 (+503 Myr). Every lifespan falls inside its rule's domain; nothing is extrapolated past it |
| Changing the Sun law | Keep the two dated CO₂ anchors and recalibrate the rule on the new luminosities | This keeps the source's own calibration (CO₂ at two dates) fixed while the law changes. Freezing the CO₂–luminosity coefficient instead and swapping only the slope would mix a change of calibration with a change of law; that comparison is not used |

**Readings of the compensation rule** (`READINGS` in `lw1982.py`):

- **faithful**: √C linear in L, through 70,000 ppm at −3,500 Myr and 320 ppm
  today.
- **text_7000**: the same rule through the text's 7,000 ppm.
- **two_thirds**: C^(2/3) linear in L.
- **linear_c**: C linear in L.
- **whk_constant_T**: WHK eq. (6) with ΔT = 0 and ΔT_e = 253(L^¼ − 1) K.
  This is the departure from a two-point rule that the WHK import makes
  explicit: P^0.364 is linear in ΔT_e, which makes the CO₂ needed 3,500 Myr ago
  128,000 ppm rather than 70,000.

**Variants** (`VARIANTS`), kept for the ingredient-swap analysis and not
readings of Lovelock & Whitfield:

- **whk_feedback** lets temperature float, with WHK's full equilibrium at
  V/V₀ = 1. Lovelock & Whitfield assume constant temperature.
- **gough_sun** replaces the straight Sun by Gough's (1981) law, keeping the
  two dated anchors.

**Control**, **no_brightening**: a constant Sun. CO₂ stays at 320 ppm and the
limit is never reached.

### Results

![Reconstruction of Fig. 2](figures/lw1982_fig2.png)

| Rule | CO₂ 3,500 Myr ago (ppm) | Time to 150 ppm (Myr) | Rule ends (Myr) |
|---|---|---|---|
| **Faithful** (√C linear in L, 70,000 ppm) | 70,000 | **80** | 254 |
| Text's 7,000 ppm | 7,000 | 300 | 952 |
| 2/3 power | 70,000 | 39 | 99 |
| C linear in L | 70,000 | 8.5 | 16 |
| WHK eq. (6) at constant temperature | 128,000 | 120 | 503 |
| *Variant:* WHK feedback, temperature free | 25,700 | 461 | — |
| *Variant:* Gough (1981) Sun, same anchors | 70,000 | 61 | 192 |
| *Control:* constant Sun | 320 | never | — |

- **The stated "about 100 Myr" holds.** The faithful rule gives 80 Myr. The
  printed lines meet the printed limit at 106 Myr if the main CO₂ line is
  extended, and at 114 Myr along the stroke drawn beyond the present, which
  continues the same line.
- **How fast the Sun brightens does not matter; the shape of its law does.**
  Any straight Sun gives 80 Myr. Gough's curved law, re-anchored on the same
  two dates, gives 61 Myr: it brightens more slowly in the past and faster
  today, relative to its own 3,500-Myr change.
- **The span depends strongly on the shape of the rule.** With the same two
  anchors, the 2/3 power halves it and a linear rule cuts it tenfold. The
  2/3 power, the alternative the paper names, leaves the span at tens of Myr,
  which bears out the paper's claim that it would not change the qualitative
  conclusion.
- **WHK's own climate makes the window longer.** Holding temperature constant
  under WHK's eq. (6) gives 120 Myr. Letting temperature rise as WHK's
  feedback dictates gives 461 Myr, because warming then speeds weathering
  instead of requiring CO₂ to fall to hold temperature fixed.

### Fidelity against the published paper

**Calibration.** Fig. 2 has three vertical scales sharing one set of ticks on
the middle axis: luminosity 0.7–1.2 and √CO₂ 0–300 (labels on either side),
and time ticks on the bottom frame. The frame lines are exactly vertical and
horizontal, so each scale is a linear map fitted to its own ticks. The largest
tick residuals are 0.79 px (time), 0.47 px (luminosity) and 0.53 px (√CO₂).
The temperature scale (0–100 °C) has labels but no ticks; it is calibrated on
the frame, and each label then sits within 0.8 °C (4 px) of its value.

**Lines.** Each straight line is traced by following ink within a window
about a seeded guess, ±4 px (±2 px for the stroke beyond t = 0 and the limit
line), and refitting. A column is used only when its window holds a single run
of ink at most 4 px tall. Columns where a second stroke enters the window
(crossings, labels) are dropped and counted. Columns 615–625, where the CO₂
stroke and the limit line share ink, are excluded from both. The main Sun and
CO₂ fits change by less than 2×10⁻⁴ px/px between windows of ±2 and ±8 px
(`fidelity/lw1982_lines.csv`).

| Line | Traced span | Straightness (RMS about own fit) | Reading |
|---|---|---|---|
| Sun | −3,975 to +1,987 Myr | 0.49 px | L = 0.9989 + 0.0734 t/Gyr |
| CO₂ | −3,456 to −20 Myr | 0.33 px | √C from 268.1 (71,900 ppm) to 18.8 at t = 0 (354 ppm) |
| CO₂ beyond the present | +14 to +248 Myr (17 columns) | 0.33 px | the same line: slope within 0.8% of the main CO₂ line |
| CO₂ limit | +49 to +1,157 Myr | 0.24 px | √C = 11.2 (124 ppm), 1.0 px below √150 |

**Scores** (`fidelity/lw1982_fidelity.csv`), over every traced column:

| Line | Reading | RMSE | RMSE (px) | Times the faithful |
|---|---|---|---|---|
| Sun | **faithful: straight, 0.0733/Gyr** | 0.0016 | **0.78** | 1 |
| Sun | null: Gough (1981) | 0.022 | 10.6 | 14 |
| Sun | null: Owen et al., linear 0.0556/Gyr | 0.037 | 18.0 | 23 |
| Sun | null: constant Sun | 0.152 | 73.1 | 94 |
| CO₂ | **faithful** | 4.1 √ppm | **4.0** | 1 |
| CO₂ | 2/3 power | 12.5 | 12.0 | 3.0 |
| CO₂ | WHK eq. (6), constant temperature | 32.3 | 31.1 | 7.8 |
| CO₂ | C linear in L | 36.7 | 35.3 | 8.9 |
| CO₂ | text's 7,000 ppm | 107.7 | 103.6 | 26 |
| CO₂ | null: constant 320 ppm | 145.4 | 139.9 | 35 |

**Two-way pixel distances** (`fidelity/lw1982_two_way.csv`), over each traced
line's span. Model to ink is measured at model samples under 0.5 px apart;
samples in dropped columns (710 for the Sun line, 150 for CO₂) are excluded
and counted, and no gap is bridged. Ink to model takes every traced ink pixel
(884 and 544) to the nearest model sample anywhere in the span.

| Line | Reading | Model to ink: median / p95 (px) | Ink to model: median / p95 (px) |
|---|---|---|---|
| Sun | **faithful** | **0.54 / 1.04** | **0.62 / 1.43** |
| Sun | null: Gough (1981) | 4.2 / 21.2 | 4.5 / 20.5 |
| Sun | null: Owen et al. linear | 12.5 / 30.6 | 13.1 / 31.6 |
| CO₂ | **faithful** | **2.6 / 5.0** | **3.0 / 5.5** |
| CO₂ | 2/3 power | 10.0 / 14.4 | 10.5 / 14.9 |
| CO₂ | WHK eq. (6), constant temperature | 6.6 / 61.3 | 7.1 / 47.0 |
| CO₂ | C linear in L | 30.1 / 41.7 | 30.8 / 42.3 |
| CO₂ | text's 7,000 ppm | 76.5 / 145.1 | 88.6 / 167.0 |

The faithful Sun slope is read from this same line, so its 0.78 px measures
how straight the line is, not an independent prediction. What the score tests
is that the printed luminosity is linear and that the two published laws in
hand are not it.

The faithful CO₂ rule lies 3.8 √ppm (3.6 px) below the printed line on
average. The printed line is 2.3% steeper (−0.0721 against −0.0705 √ppm per
Myr) and passes 354 ppm, rather than 320, at t = 0. That is 1 px at the
present and 6–7 px at the line's start.

![Overlay](fidelity/lw1982_overlay.png)

**The temperature band** (`fidelity/lw1982_band.csv`):

| Feature | Printed | Text |
|---|---|---|
| Archaean upper limit, −3,500 to −2,400 Myr | 39.9 °C | 40 °C |
| Archaean lower limit | 15.0 °C | 15 °C |
| Upper limit after the −2,300 Myr glaciation | 25.0 °C | "20–30 °C" |
| Lower limit after it | 15.0 °C | glacial 5–10 °C, interglacials 5–15 °C higher |
| Six glaciation minima (−2,301, −955, −803, −626, −440, −284 Myr) | 4.0–4.2 °C | glaciations at 5–10 °C |

**Stated numbers** (`fidelity/lw1982_claims.csv`):

| Statement | Stated | Reconstructed |
|---|---|---|
| 150 ppm reached in | about 100 Myr | 80 Myr (rule); 106–114 Myr (printed lines) |
| CO₂ 3,500 Myr ago | 7,000 ppm | 71,900 ppm (printed line, at −3,456 Myr) |
| CO₂ today | 320 ppm | 354 ppm (printed line) |
| CO₂ limit | 150 ppm | 124 ppm (printed line, 1.0 px) |
| Sun's rise since the Earth formed | 30% | 33% of today's at −4,500 Myr on the printed line, or 49% of the young Sun's. The line starts at −4,000 Myr, where it gives 29% |
| Without the CO₂ decline, temperature "might by now have exceeded 50 °C" | 50 °C | 40 °C under WHK eq. (6), with CO₂ held at 70,000 ppm |

## Caldeira & Kasting (1992)

### The model as published

Box 1 of the paper gives every equation. Time t is in Gyr from the present,
pressures in bar and temperatures in K.

1. **The Sun.** S(t) = S₀/(1 − 0.38 t/τ₀), with τ₀ = 4.55 Gyr and
   S₀ = 1,368 W m⁻²: a fit to A. I. Boothroyd's standard solar model.
2. **Energy balance.** (1 − a)S/4 = σT_eff⁴ and T = T_eff + ΔT.
3. **Greenhouse and albedo.** ΔT(T, ψ), with ψ = log₁₀ P_atm, and a(T), are
   least-squares fits to 143 runs of Kasting's radiative–convective model
   over 0–100 °C and 10⁻⁸–10⁻² bar. The stated mean errors are under 0.5 K
   and under 0.01. Clouds are held fixed.
4. **Weathering.** F/F₀ = (a_H/a_H,₀)^0.5 exp((T − T₀)/13.7 K). Here a_H is
   the H⁺ activity of rain water in equilibrium with soil CO₂ and 0.2 ppb of
   atmospheric SO₂. The 13.7 K comes from Walker, Hays & Kasting (1981).
5. **Soil CO₂.** P_soil/P_soil,₀ = (Π/Π₀)(1 − P_atm,₀/P_soil,₀) +
   P_atm/P_soil,₀, from Volk (1987, his eq. 11), with P_soil,₀ = 10 P_atm,₀.
6. **Productivity.** Π/Π_max = (1 − ((T − 25 °C)/25 °C)²) (P_atm − P_min)/
   (P₁/₂ + P_atm − P_min). This is Volk's Michaelis–Menten law (his eq. 12)
   times C&K's temperature factor. Π_max = 2Π₀ and P_min = 10 ppm (C₄
   plants). P₁/₂ is fixed by Π = Π₀ at T₀ = 15 °C and P_atm,₀ = 320 ppm.
7. **Solution.** Weathering is held at today's rate, F = F₀, until P_atm
   falls to 1 ppm; P_atm then stays there.

At each time the model solves F = F₀ for P_atm, with T taken from the
climate fits. CO₂ falls as the Sun brightens. Productivity falls with it, and
so does the soil-CO₂ gradient, so T must rise to keep weathering at the
modern rate. Once P_atm is below P_min, Π = 0 and P_soil = P_atm. Once P_atm
reaches 1 ppm, T depends on eqs (1)–(5) alone.

**Departures from Walker, Hays & Kasting** (imported from
[`whk1981`](../../src/terra_prisca/walker_hays_kasting/whk1981.py)):

- **Weathering.** WHK use (P/P₀)^0.3 on atmospheric CO₂; C&K use
  a_H^0.5 on soil CO₂. Since a_H ∝ P^0.5 when carbonate dominates, WHK's law
  is a_H^0.6: this is the "implied exponent of 0.6" in the text, reproduced
  as 0.3/0.5. Only the 13.7 K e-folding is imported, as `ck1992.EFOLD_K`.
- **Climate.** WHK's linear eqs (3)–(6), with T_e = 253 K and T_s = 285 K,
  are replaced by eqs (2)–(5): Stefan–Boltzmann, a temperature-dependent
  albedo and a radiative–convective greenhouse.
- **Reference temperature.** WHK's T₀ = 285 K becomes 15 °C (288.15 K).
- **Biology.** WHK have none. Soil CO₂ and productivity are new.

### Interpretive choices

| Choice | Adopted | Reason |
|---|---|---|
| Present-day closure | **T₀ = the fits' own present temperature, 287.89 K** | Eqs (1)–(5) put today at 287.89 K, which rounds to the stated 15 °C but is not 288.15 K. With T₀ = 288.15 K, F = F₀ cannot hold at 320 ppm: the model starts at 335 ppm with Π/Π₀ = 1.017. With the printed equations, the printed Π/Π₀ (1.002 at t = 0) favours closing at 287.89 K: with the SO₂ factor refitted under each reading, 288.15 K ties on P_soil and T but misses Π by 6.7 px against 1.6 (`fidelity/ck1992_coupled.csv`). This identifies the closure only for the equations as printed. Codex (CK-R3) closed today at 288.15 K instead by adding 0.067 K to eq. (4) at 320 ppm, tapering to zero at 1 ppm; after the same refit, that version fits Π about as well (1.7 px). The printed P_atm at t = 0 (324 ppm) is not used: 320 against 335 ppm is 3.3 px, inside the 4.1 px residual of the log axis |
| Equilibrium constants | **Traced to the paper's sources, at 25 °C.** Carbon system and water: pK_H 1.47, pK₁ 6.352, pK₂ 10.329, pK_w 13.999. S(IV): K_H 1.23 M atm⁻¹, K₁ 1.7×10⁻² M, K₂ 6.3×10⁻⁸ M | The paper takes the carbon system from Stumm & Morgan (1981) and sulphur from Chameides (1984); neither is in hand. The carbonate values are from Butler (1991), Table 2.2, which tabulates Stumm & Morgan's selections; pK_w comes from the same table, where Butler traces it to Sillén & Martell, not to Stumm & Morgan. The S(IV) dissociations are from Sellegri et al. (2003), Table 5, which attributes them to Chameides. The SO₂ Henry constant, 1.23 M atm⁻¹, is the top of Sellegri et al.'s compiled range and agrees with Sander's two-figure listing of Chameides (1.2×10⁻² mol m⁻³ Pa⁻¹, or 1.216 M atm⁻¹, 3,100 K); 1.216 would move the C₄ limit 1 Myr later. These are secondary attributions, not readings of the primary sources. The constants are held at 25 °C, the temperature of the dissolution experiments the text cites. Two alternatives are scored: following T (Butler's table interpolated; van 't Hoff for sulphur), and the textbook set used in the first build (K₁ 1.23×10⁻², K₂ 6.61×10⁻⁸) |
| Strength of the SO₂ term | **Faithful: ×1. Reading `so2_fitted`: ×0.283** | This choice decides the low-CO₂ phase (below). The fitted factor puts the model's 10 ppm kink at the printed kink (0.863 Gyr). At the kink, Π = 0 and P_soil = P_atm = 10 ppm. The climate puts T there at 299.93 K, so eq. (6) requires a_H(kink)/a_H(today) = exp(−2(T − T₀)/13.7 K) = **0.172**. That ratio is what the figure fixes, independently of the chemistry. Its translation into today's sulphur contribution depends on the chemistry model: sulphur balances 2.4% of today's soil-water H⁺ with constants at 25 °C, and 5.2% with constants that follow T. Both reproduce the kink. The other printed features were left out of this one-parameter fit, but the figure had already been examined when the reading was chosen. It was added after the first scores, not declared in advance (board message 3627) |
| Charge balance | [H⁺] = [HCO₃⁻] + 2[CO₃²⁻] + [HSO₃⁻] + 2[SO₃²⁻] + [OH⁻], with activity taken as concentration | Fresh rain water, as the text describes it. Bar is taken as atm (1.3%) |
| P₁/₂ | Eq. (8) through Π₀ at (T₀, 320 ppm), temperature factor included: 205.6 ppm | As stated. Volk's eq. (13), (Π_max/Π₀ − 1)(P₀ − P_min) = 310 ppm, omits the temperature factor and is scored as a reading |
| Π outside its range | Zero below P_min and outside 0–50 °C | The temperature factor is negative beyond 50 °C and the CO₂ factor below P_min. A negative productivity has no meaning, and the caption says P_soil = P_atm once P_atm is too low |
| C₃ world | A separate run with P_min = 150 ppm and P₁/₂ recalibrated (112.7 ppm) | The caption calls it "a C₃-only world with P_min = 150 p.p.m." The time at which the C₄ run passes 150 ppm (0.19 Gyr) is reported alongside |
| The 1 ppm floor | P_atm is held at 1 ppm whenever F at 1 ppm already reaches F₀; a level below the floor is never reached | As stated. F − F₀ changes sign once in P_atm between 1 ppm and 10⁻² bar at every time tested, so the root is unique. F is not monotonic in P_atm everywhere: late on, high CO₂ warms T towards 50 °C and Π falls, but only where F is 6–9 times F₀ |
| σ | 5.670×10⁻⁸ W m⁻² K⁻⁴ | Not stated |
| Range of the fits | T is reported only up to 373.15 K | The fits cover 0–100 °C, and the figure stops at 373 K |
| ψ | log₁₀ | A natural log puts today at 283 K |

**Readings** (`READINGS` in `ck1992.py`), each scored:

- **faithful**: as above.
- **so2_fitted**: the SO₂ term ×0.283, fitted to the printed kink.
- **textbook**: the constants of the first build.
- **t0_printed**: T₀ = 288.15 K.
- **chemistry_T**: equilibrium constants follow T.
- **so2_half**, **so2_double**: the SO₂ term ×0.5 and ×2.
- **volk_p_half**: Volk's P₁/₂.

**C₃ world** (`C3`): P_min = 150 ppm, P₁/₂ recalibrated.

**Controls** (`CONTROLS`):

- no SO₂;
- productivity held at Π₀ (Volk's case W3);
- WHK weathering on atmospheric CO₂, with no soil;
- CO₂ held at 320 ppm;
- constant Sun.

**Sensitivity rows** (fidelity only): eq. (4) ±0.5 K and eq. (5) +0.01, their
stated mean errors, and eq. (4) +0.5 K with eq. (5) +0.005708 together
(Codex, CK-R3).

### Results

![Reconstruction of Fig. 2](figures/ck1992_fig2.png)

| Quantity | Stated | Faithful | Textbook constants | SO₂ fitted to the kink | Printed (Fig. 2) |
|---|---|---|---|---|---|
| C₃ world reaches 150 ppm | ~0.5 Gyr | 0.42 | 0.44 | 0.49 | — |
| P_atm reaches 10 ppm (the C₄ limit) | 0.9 Gyr | 0.77 | 0.79 | 0.863 (fitted) | 0.863 |
| P_atm reaches 1 ppm | ~1 Gyr | 0.93 | 0.96 | 1.023 | 1.024 |
| Π/Π₀ falls to 0.05 | — | 0.69 | 0.71 | 0.75 | 0.73 |
| T at 0.9 Gyr | — | 296.3 K | 297.3 K | 300.1 K | 300.2 K |
| T at the floor where weathering exceeds supply | "above 300 K" | 296.3 K | 297.3 K | 300.3 K | — |
| T reaches 50 °C | ~1.5 Gyr | 1.32 | 1.32 | 1.32 | 1.33 |
| T reaches 80 °C | ~1.5 Gyr | 1.46 | 1.46 | 1.46 | 1.47 |
| T from 50 to 97 °C | < 0.2 Gyr (to 100 °C) | 0.226 | 0.226 | 0.226 | 0.227 |

- **The hot phase is reproduced from eqs (1)–(5) as printed.** Once P_atm
  sits at 1 ppm, T crosses 50, 80, 90 and 97 °C within 0.007 Gyr of the
  printed curve. This holds under every reading, because none of them changes
  the climate. Near 340–360 K, dT/d ln S reaches about 2,700 K, so the
  figure constrains the energy balance tightly, but jointly. Shifting eq. (4)
  by +0.5 K alone moves T by 20–25 px. Adding 0.005708 to eq. (5) as well
  restores the fit, to within 0.2 px of the faithful reading (CK-R3). The
  figure therefore cannot measure either fit's error against the 143 climate
  runs; it shows that the printed pair reproduces the printed curve.
- **The low-CO₂ phase depends on how acid rain water is at low soil CO₂.**
  The SO₂ term sets a floor under a_H. A stronger floor stops a_H falling
  with P_soil, so T rises less to keep weathering at the modern rate, and the
  10 ppm limit comes sooner. With the source-traced constants, the model
  reaches 10 ppm at 0.77 Gyr and 1 ppm at 0.93 Gyr, and its merged
  P_soil = P_atm curve lies 65 px from the printed one. The textbook set of
  the first build gives 0.79 and 0.96 Gyr. With the SO₂ term ×0.283, fitted
  to the kink alone, the features left out of the fit land on the figure: 1 ppm
  at 1.023 Gyr (printed 1.024), T at 0.9 Gyr of 300.1 K (300.2), and Π/Π₀ = 0.05
  at 0.745 Gyr (0.735, 0.011 Gyr later). The floor threshold becomes 300.3 K
  ("above 300 K") and the C₃ world reaches 150 ppm at 0.49 Gyr ("~0.5").
  Every printed curve lies within a median 2.4 px of the model.
- **The paper's "0.9 Gyr" of constant temperature is an energy-budget
  estimate** (Codex, CK-R4). The text gives 20.4 W m⁻² of infrared trapping
  by 320 ppm of CO₂. Removing that much trapping offsets the Sun's
  brightening, (1 − a₀)(S − S₀)/4 = 20.4 W m⁻², at **0.940 Gyr**. The coupled
  run is a different calculation: T rises 8–12 K over the same 0.9 Gyr (12 K
  in the figure).
- **Declining productivity lengthens the span relative to constant
  productivity.** With Π held at Π₀ (Volk's case W3), the 10 ppm limit comes
  at 0.50 Gyr instead of 0.77. As Π falls, so does the soil-CO₂ gradient, and
  T must rise further to keep weathering at the modern rate. WHK's weathering
  law on atmospheric CO₂, with no soil or biology, gives 0.91 Gyr, but its
  P_atm curve lies 34 px from the printed one.

### Fidelity against the published paper

**Calibration** (`fidelity/ck1992_calibration.csv`). Fig. 2 is a 650-ppi
bilevel scan, rotated and sheared by a few pixels across the figure. Each
panel's frame lines are fitted (horizontal slopes 0.0033 and 0.0037, vertical
−0.0050 and −0.0055). Pixels are mapped to u = x − k_v y and v = y − k_h x,
and each scale is a linear map of u or v fitted to its ticks:

- time: the 15 inward ticks on each panel's top frame, 0.1–1.5 Gyr;
- pCO₂: the five decade ticks, 1–10,000 ppm;
- S/S₀: all 21 ticks;
- Π/Π₀ and T: all 11 ticks each.

The largest tick residuals are 2.2–4.1 px (0.25 K on the T axis). The printed
ticks are unevenly spaced by a few pixels, so this, not the trace, limits the
absolute accuracy.

**Traces.** Each curve is traced from knots read off the scan, by refining a
dense polyline along its normals. A sample is kept only when its ±10 px
normal window holds one ink run at most 13 px thick. Samples are dropped and
counted at:

- the crossings (P_soil and P_atm with S/S₀; Π with T);
- the junction of P_soil and P_atm;
- the stretch of P_soil that its label's subscript touches;
- the frames.

Each trace has 109–766 centres and at most five samples dropped for any other
reason.

**Two-way distances** (`fidelity/ck1992_two_way.csv`) run from the model,
drawn on the calibrated axes, to the traced centres and back. Model samples
are 0.25 px apart; samples inside excluded boxes are dropped and counted, and
no gap is bridged. A reading is scored only on the trace centres at times
where both it and the faithful reading have a value, in both directions.
Above 373.15 K, the top of the fits' range, a reading has none: the fixed-CO₂
control loses 112 of the 766 T centres and eq. (4) +0.5 K loses 68. The
faithful reading is scored on the same centres, so each row is paired. Every
reading, tabulated or a callable Sun curve, is drawn over the same time span
with exact endpoints.

| Curve | Reading | Centres used | Model to trace: median / p95 (px) | Trace to model: median / p95 (px) | Faithful, same centres: trace to model |
|---|---|---|---|---|---|
| P_soil | **faithful** | 415/415 | 17.5 / 92.6 | 13.3 / 64.2 | — |
| P_soil | textbook constants | 415/415 | 10.1 / 61.8 | 8.8 / 44.8 | 13.3 / 64.2 |
| P_soil | **SO₂ fitted** | 415/415 | **2.4 / 4.9** | **2.3 / 5.1** | 13.3 / 64.2 |
| P_soil | Volk's P₁/₂ | 415/415 | 29.2 / 92.2 | 27.4 / 64.9 | 13.3 / 64.2 |
| P_soil | null: Π held at Π₀ | 415/415 | 105 / 241 | 151 / 489 | 13.3 / 64.2 |
| P_atm | **faithful** | 331/331 | 6.0 / 66.0 | 6.0 / 33.2 | — |
| P_atm | **SO₂ fitted** | 331/331 | **1.2 / 3.4** | **1.0 / 3.5** | 6.0 / 33.2 |
| P_atm | null: WHK weathering | 331/331 | 33.9 / 43.6 | 32.3 / 43.9 | 6.0 / 33.2 |
| P_atm | null: CO₂ fixed | 331/331 | 141 / 275 | 151 / 310 | 6.0 / 33.2 |
| P_soil = P_atm | **faithful** | 109/109 | 64.6 / 65.0 | 65.4 / 112 | — |
| P_soil = P_atm | textbook constants | 109/109 | 47.3 / 48.1 | 47.9 / 76.4 | 65.4 / 112 |
| P_soil = P_atm | **SO₂ fitted** | 109/109 | **1.4 / 2.6** | **1.3 / 2.7** | 65.4 / 112 |
| P_soil = P_atm | null: no SO₂ | 109/109 | 55.0 / 91.3 | 111 / 191 | 65.4 / 112 |
| S/S₀ | **eq. (1)** | 638/638 | **1.7 / 4.3** | **1.6 / 4.7** | — |
| S/S₀ | null: Gough (1981) | 638/638 | 5.1 / 9.6 | 5.1 / 9.9 | 1.6 / 4.7 |
| S/S₀ | null: Lovelock & Whitfield's straight line | 638/638 | 50.9 / 126 | 60.8 / 138 | 1.6 / 4.7 |
| Π/Π₀ | **faithful** | 510/510 | 4.7 / 19.1 | 4.9 / 21.4 | — |
| Π/Π₀ | **SO₂ fitted** | 510/510 | **1.6 / 6.2** | **1.6 / 6.2** | 4.9 / 21.4 |
| Π/Π₀ | Volk's P₁/₂ | 510/510 | 40.2 / 53.1 | 42.6 / 69.8 | 4.9 / 21.4 |
| Π/Π₀ | null: Π held at Π₀ | 510/510 | — (on the frame) | 458 / 846 | 4.9 / 21.4 |
| T | **faithful** | 766/766 | 3.6 / 28.0 | 3.6 / 28.1 | — |
| T | **SO₂ fitted** | 766/766 | **2.2 / 4.7** | **2.1 / 4.9** | 3.6 / 28.1 |
| T | eq. (4) + 0.5 K | 698/766 | 25.0 / 68.4 | 19.8 / 57.4 | 3.6 / 29.2 |
| T | eq. (4) + 0.5 K, eq. (5) + 0.005708 | 766/766 | 3.7 / 28.9 | 3.8 / 29.2 | 3.6 / 28.1 |
| T | null: CO₂ fixed | 654/766 | 138 / 211 | 142 / 213 | 3.6 / 29.4 |

The column errors in data units (`fidelity/ck1992_fidelity.csv`) cover the
stretches flatter than 2 px/px, with the faithful reading rescored on the
same points. The SO₂-fitted reading scores 0.009 decades (P_atm), 0.022
(P_soil), 0.0054 (Π/Π₀) and 0.46 K (T), against 0.10, 0.38, 0.017 and
1.30 K for the faithful reading. The fixed-CO₂ control scores 22.9 K on the
559 shallow T points where it has values, against 1.32 K for the faithful
reading on the same points.

![Overlay](fidelity/ck1992_overlay.png)

**Coupled choices** (`fidelity/ck1992_coupled.csv`). Each alternative is
rescored with the SO₂ factor refitted to the kink under it, so that none is
judged against a base that misses the low-CO₂ phase. Distances are model to
trace (median):

| Base reading | SO₂ factor | a_H(kink)/a_H(today) | Sulphur share of today's H⁺ | Π/Π₀ at t = 0 (printed 1.002) | Median px: P_soil / P_atm / Π / T |
|---|---|---|---|---|---|
| **Faithful: source-traced constants at 25 °C, T₀ = 287.89 K** | 0.283 | 0.172 | 2.4% | 1.000 | 2.4 / 1.2 / 1.6 / 2.2 |
| T₀ = 288.15 K | 0.310 | 0.179 | 2.7% | 1.017 | 1.9 / 2.2 / 6.7 / 1.9 |
| Constants follow T | 0.397 | 0.172 | 5.2% | 1.000 | 2.4 / 1.3 / 4.3 / 2.1 |
| Textbook constants | 0.391 | 0.172 | 2.4% | 1.000 | 2.4 / 1.2 / 1.6 / 2.2 |
| Textbook constants following T | 0.548 | 0.172 | 5.2% | 1.000 | 2.3 / 1.2 / 4.0 / 2.1 |
| Volk's P₁/₂ | 0.283 | 0.172 | 2.4% | 0.879 | 14.0 / 8.4 / 32.1 / 1.9 |

The kink fixes the same acidity ratio under every chemistry. Once the SO₂
factor is refitted, the two constant sets are indistinguishable. Constants
held at 25 °C fit Π somewhat better than constants that follow T.

**Printed features** (`fidelity/ck1992_events.csv`), read from the traces:

| Feature | Printed | Faithful | SO₂ fitted | T₀ = 288.15 K |
|---|---|---|---|---|
| P_atm at t = 0 | 324 ppm | 320 | 320 | 335 |
| P_soil at t = 0 | 3,316 ppm | 3,200 | 3,200 | 3,265 |
| Π/Π₀ at t = 0 | 1.002 | 1 | 1 | 1.017 |
| T at t = 0 | 288.3 K | 287.9 | 287.9 | 288.1 |
| Kink in P_atm | 0.863 Gyr at 9.97 ppm | 0.767 | 0.863 | 0.774 |
| P_atm reaches 1 ppm | 1.024 Gyr | 0.932 | 1.023 | 0.939 |
| Π/Π₀ falls to 0.05 | 0.735 Gyr | 0.689 | 0.745 | 0.696 |
| T at 0.9 Gyr | 300.2 K | 296.3 | 300.1 | 296.6 |
| T reaches 300 K | 0.873 Gyr | 1.018 | 0.882 | 1.018 |

The printed T curve runs almost flat near 300 K. Moving the level by the T
axis's tick residual (±0.25 K) moves the printed crossing from 0.853 to
0.991 Gyr, and a horizontal cut at 300 K meets ink over 0.84–1.00 Gyr
(Codex, CK-R6). The 300 K timing is therefore weakly fixed; T at 0.9 Gyr is
the better-conditioned comparison.

**Stated numbers** (`fidelity/ck1992_claims.csv`):

| Statement | Stated | Reconstructed |
|---|---|---|
| WHK's implied exponent on a_H | 0.6 | 0.6 (0.3/0.5) |
| S rises at | ~0.12 W m⁻² Myr⁻¹ | 0.114 today; mean 0.124 over 0.9 Gyr |
| C&K's reading of L&W: √P falls to zero at | 1.017 S₀ | 1.0186 S₀ from the faithful L&W rule |
| Trapping by 320 ppm implied by L&W | ~4 W m⁻² | 4.07, with (1 − a₀)(0.017)S₀/4 and a₀ = 0.300 from eq. (5) |
| Reducing CO₂ could hold T constant for | 0.9 Gyr | 0.940 Gyr for the stated 20.4 W m⁻² to offset the Sun |
| Trapping by 320 ppm in C&K's model | 20.4 W m⁻² | not reproducible: needs the radiative–convective model |
| With negligible CO₂, T exceeds 50 °C after | ~1.5 Gyr | 1.46 Gyr at 0.01 ppm (the fits' lower bound); 1.32 at the 1 ppm floor |
| Ocean loss at 6×10¹¹ H cm⁻² s⁻¹ | ~1 Gyr | 0.97 Gyr for 1.4×10²¹ kg of water (not stated) |

## Ingredient swap: what separates the two lifespans

This is an analysis built on the two faithful reconstructions, not a
reconstruction. It lives in its own module,
[`ingredient_swap.py`](../../src/terra_prisca/biosphere_lifespan/ingredient_swap.py),
which imports `lw1982` and `ck1992` and changes neither. Its outputs are in
`swap/`.

Lovelock & Whitfield give the biosphere 80 Myr; Caldeira & Kasting give it
767 Myr, 9.6 times longer. Three ingredients separate them. Each has one
setting in each paper:

| Ingredient | Lovelock & Whitfield | Caldeira & Kasting |
|---|---|---|
| Sun law | Straight line, 0.0733 per Gyr (read from their Fig. 2) | Eq. (1), S = S₀/(1 − 0.38t/4.55) |
| CO₂ law | √CO₂ falls linearly with luminosity between dated anchors, holding temperature constant | Weathering balances a fixed volcanic supply; temperature is free; plants raise soil CO₂ (eqs 1–8) |
| Plants and threshold | C₃: life ends at 150 ppm | C₄: life ends at 10 ppm, the P_min of eq. (8) |

**Method.** Both models are sequences of equilibria, so each lifespan is set
by the brightening S*/S₀ at which CO₂ first meets the threshold, and the Sun
law turns S* into time. All eight combinations of the two papers' settings
are run (`swap/ingredient_swap_cells.csv`). The change from one paper to the
other is then shared among the ingredients by Shapley values: each
ingredient's effect, averaged over the six orders in which the three swaps
can be made. Because the ingredients act as factors on the lifespan, the
shares are computed in ln(lifespan); the same averages in Myr are given too.
Each ingredient's smallest and largest effect, over all the contexts in
which it can be swapped, shows how much its effect depends on the others.

### Interpretive choices

| Choice | Reading | Reason |
|---|---|---|
| Ingredients | Three, as tabulated; any finer change sits inside one of them | Each is a choice one paper made differently from the other |
| Plants and threshold together | The C₃/C₄ swap changes the threshold and, in C&K's model, P_min of eq. (8) | Both papers set the threshold at the plants' compensation point; tested below, the lifespan at that threshold does not depend on the rest of eq. (8) |
| Swapping the Sun under L&W's rule | The two dated anchors (320 ppm today, 70,000 ppm 3,500 Myr ago) are kept and the rule is re-anchored on the new Sun, as in L&W's Gough variant | The anchors are what L&W state. Eq. (1) is evaluated at −3.5 Gyr, outside the span C&K use it for; it has Gough's form, which runs back to the Sun's birth |
| Swapping the Sun under C&K's law | Exact: their CO₂ depends on time only through S, so S* is found under eq. (1) and the straight line is inverted at S* | Needs no change to `ck1992` |
| Attribution | Shapley values in ln(lifespan); Myr as a second view | Shares in ln sum to the whole and do not depend on swap order |
| C&K's constant-temperature step | T held at T₀ = 287.89 K, the faithful reading | Same reference as the faithful model |

### Results

| Ingredient | Shapley factor | Share of the change (ln) | Shapley, Myr | Range of factors over contexts |
|---|---|---|---|---|
| CO₂ law | **×5.50** | 75% | +523 | ×4.47 to ×6.87 |
| Plants and threshold | **×2.18** | 35% | +246 | ×1.81 to ×2.61 |
| Sun law | **×0.80** | −10% | −83 | ×0.76 to ×0.85 |

The three factors multiply to 9.58, the full ratio of 767 to 80.0 Myr. The
Myr column sums to the full 687 Myr.

**The eight combinations** (`swap/ingredient_swap_cells.csv`), lifespan in
Myr. Each single swap is one step along an edge of this cube.

| CO₂ law | Plants and threshold | L&W's straight Sun | C&K's eq. (1) Sun |
|---|---|---|---|
| L&W's rule | C₃, 150 ppm | **80.0** (L&W) | 61.6 |
| L&W's rule | C₄, 10 ppm | 209 | 160 |
| C&K's weathering with plants | C₃, 150 ppm | 500 | 423 (C&K's C₃ run) |
| C&K's weathering with plants | C₄, 10 ppm | 934 | **767** (C&K) |

From L&W's end, swapping one ingredient alone gives:
- the Sun law, ×0.77;
- the plants and threshold, ×2.61;
- the CO₂ law, ×6.24.

From C&K's end, swapping one back gives:
- the Sun law, ×1.22;
- the plants and threshold, ×0.55;
- the CO₂ law, ×0.21.

![Ingredient swap](swap/ingredient_swap.png)

- **The CO₂ law accounts for three-quarters of the gap.** On the like-for-like
  C₃ comparison, under one Sun, it lengthens L&W's 61.6 Myr to C&K's 423 Myr.
- **The plants and threshold roughly double the lifespan.** The effect is ×2.6
  under L&W's rule and ×1.8 under C&K's full law. Under C&K's greenhouse at
  constant T, or with the soil pump held, it is about ×3.5 (139 to 486 Myr,
  147 to 498 Myr). It falls to ×1.8 only once the plants are in, because the
  pump switching off lengthens the 150 ppm case (×2.87) more than the 10 ppm
  case (×1.54).
- **C&K's Sun brightens faster and shortens every lifespan.** It rises 0.0835
  per Gyr today against 0.0733 and steepens with time. Under L&W's rule the
  factor also carries the re-anchoring: eq. (1) puts the Sun at 0.774 of
  today's brightness 3.5 Gyr ago, against 0.743 on the straight line.

**The CO₂ law, step by step** (`swap/ingredient_swap_co2_steps.csv`, eq. (1)
Sun). The steps are nested, not interchangeable. The greenhouse swap is
defined only at constant temperature, because L&W's rule gives no
temperature. The soil pump is defined only once temperature is free.

| Step | C₃, 150 ppm: Myr (factor) | C₄, 10 ppm: Myr (factor) | S*/S₀ (C₃ / C₄) | T − T₀ at the threshold, K (C₃ / C₄) |
|---|---|---|---|---|
| L&W's rule, T constant | 61.6 | 160 | 1.0052 / 1.0135 | 0 by assumption |
| C&K's greenhouse and albedo, eqs (2)–(5), T constant | 139 (×2.26) | 486 (×3.04) | 1.0118 / 1.0423 | 0 / 0 |
| C&K's weathering, T free, soil pump held at Π₀ | 147 (×1.06) | 498 (×1.03) | 1.0125 / 1.0434 | 0.17 / 0.32 |
| C&K's weathering with plants (faithful) | 423 (×2.87) | 767 (×1.54) | 1.0366 / 1.0684 | 7.1 / 8.3 |

- **Greenhouse.** Lowering CO₂ from 320 to 150 ppm offsets 0.52% of
  brightening under L&W's rule (re-anchored on eq. (1); 0.59% on their own
  straight Sun) but 1.18% under C&K's radiative fits. Lowering it to 10 ppm
  offsets 1.35% (1.53%) and 4.23%. L&W's square-root rule gives each
  e-fold of CO₂ a warming proportional to √CO₂, so low CO₂ buys little. This
  is the gap C&K pointed to when they set L&W's implied 4 W m⁻² of CO₂
  trapping against their own 20.4 W m⁻² (*Stated numbers*, above).
- **Freeing temperature adds almost nothing while the soil pump is held.**
  With Π fixed, soil CO₂ (P_soil₀ − P₀ + P) barely changes as atmospheric CO₂
  falls. Weathering then hardly responds to CO₂ and holds temperature within
  0.2–0.3 K of T₀ at the threshold, nearly where a perfect thermostat would. Freeing temperature and weakening the pump
  are therefore not separable in C&K's model, and the gain is given to the two
  together.
- **The soil pump is what lengthens C&K's lifespans.** At the threshold the
  plants stop growing (Π = 0), so soil CO₂ falls to the atmospheric value and
  weathering weakens. The Earth must be 7–8 K warmer, and so the Sun
  brighter, before weathering can draw CO₂ down to the threshold. The step is
  ×2.87 for C₃ and ×1.54 for C₄.

**Only the pump being off matters at the threshold** (tested). Because both
thresholds sit at P_min, where Π = 0, the shape of eq. (8) does not matter:
- C₃ plants reach 10 ppm at the same time as C₄ plants (0.7670 Gyr);
- Volk's half-saturation constant gives the same 10 ppm and 150 ppm times as
  C&K's own.

Splitting the plants ingredient into curve and threshold therefore depends
on the order (`swap/ingredient_swap_side.csv`):
- swapping the C₄ curve first, with the threshold still at 150 ppm, shortens
  the lifespan from 423 to 193 Myr (×0.46), and lowering the threshold to
  10 ppm then gives ×3.98;
- lowering the threshold first gives the whole effect, and the curve then
  changes nothing.

**Side branch: WHK weathering** (neither paper). Replacing C&K's weathering
with WHK's law on atmospheric CO₂ (exponent 0.3, no soil pump), with
temperature free, gives 274 Myr to 150 ppm and 914 Myr to 10 ppm under
eq. (1). That is shorter than C&K's C₃ run (423 Myr) but longer than their
C₄ value (767 Myr).

### What the swap shows

Three-quarters of the gap between 80 Myr and 0.77 Gyr lies in the CO₂ law.
Inside it, two parts are of comparable size, and which is larger depends on
the plants:
- **Greenhouse strength** (×2.26 for C₃, ×3.04 for C₄). C&K's radiative fits
  give low CO₂ two to three times more warming than L&W's square-root rule.
- **The soil pump switching off** (×2.87 for C₃, ×1.54 for C₄). When the
  plants stop growing, weathering weakens, and the Earth warms by 7–8 K
  before CO₂ reaches the threshold.

Of the other two ingredients:
- **The threshold.** C₄ plants' lower limit about doubles the lifespan.
- **The Sun law.** C&K's faster-brightening Sun takes back a fifth.

**Limits of the attribution.** The Shapley shares hold for these three
ingredients and the two papers' settings; a finer or different split would
share the gap differently. The steps of the CO₂ law are nested in the order
the models allow, not chosen, and their factors depend on the plants. The
attribution uses the faithful readings of both papers: L&W's 70,000 ppm past
anchor and C&K's source-traced constants. With the SO₂ term fitted to C&K's
printed kink, C&K's lifespan is 863 Myr instead of 767. Rerun for that
reading, the factors become ×6.29 for the CO₂ law (77% of the change), ×2.16
for the plants and threshold (32%) and ×0.80 for the Sun (−10%).

## What holds

### Lovelock & Whitfield (1982)

- **Fig. 2's CO₂ line is the stated rule:** √CO₂ linear in luminosity, from
  70,000 ppm 3,500 Myr ago to 320 ppm today. It fits to 4.0 px RMS (ink to
  model: median 3.0 px, p95 5.5 px). The four alternative rules and the
  constant-CO₂ null miss by 3 to 35 times as much.
- **The Sun line is straight,** rising 7.3% of today's luminosity per Gyr. The
  two published laws in hand, Gough's (1981) and Owen et al.'s, miss it by 14
  and 23 times as much.
- **"About 100 Myr" holds.** The rule gives 80 Myr and the printed lines meet
  the printed limit at 106–114 Myr.
- **The temperature band is drawn at the stated limits** (40, 15, 25 and
  15 °C, each within 0.1 °C).
- **The 2/3-power alternative leaves the conclusion intact.** It halves the
  span to 39 Myr.

### Caldeira & Kasting (1992)

- **Box 1 reproduces Fig. 2,** once one quantity the paper does not print is
  fixed: how much acidity falls between today and the 10 ppm kink, which
  depends on the sulphur term. Fitted to the printed kink alone, it brings all
  five printed curves within a median 2.4 px and a p95 of 6.3 px. The features
  left out of the fit land on the figure: P_atm reaches 1 ppm within 0.001 Gyr,
  T at 0.9 Gyr comes within 0.12 K, and Π/Π₀ reaches 0.05 within 0.011 Gyr.
  Holding productivity fixed, using WHK's weathering law, or fixing CO₂ each
  miss the P_atm and T curves by 6 to 90 times as much at the 95th
  percentile.
- **The hot phase follows from eqs (1)–(5) as printed,** to within 0.007 Gyr
  at 50, 80, 90 and 97 °C. The figure fixes the energy balance tightly, but
  it cannot separate the greenhouse fit from the albedo fit.
- **The Sun is eq. (1).** The printed S/S₀ lies within a median 1.6 px of it.
  Gough's (1981) law misses by three times as much, and Lovelock & Whitfield's
  straight line by 30.
- **The stated lifespans hold to their rounding, with the fitted sulphur
  term.** The C₃ world reaches 150 ppm at 0.49 Gyr ("~0.5"), the C₄ limit
  comes at 0.86 Gyr ("0.9"), and the 1 ppm floor at 1.02 Gyr ("~1 Gyr"). With
  the source-traced constants they come at 0.42, 0.77 and 0.93 Gyr.
- **The "0.9 Gyr" of constant temperature is the paper's own energy budget:**
  20.4 W m⁻² of CO₂ trapping offsets the brightening Sun at 0.94 Gyr.
- **C&K's reading of Lovelock & Whitfield checks out against our
  reconstruction.** Their √P ∝ 1.017S₀ − S compares with 1.0186 from the
  faithful L&W rule, and ~4 W m⁻² of trapping comes out at 4.07 W m⁻².
- **Smaller statements check out.** The exponent of 0.6 implied by WHK is
  reproduced, as are 0.114–0.124 W m⁻² Myr⁻¹ for the Sun's rise ("~0.12") and
  0.97 Gyr for ocean loss ("~1 Gyr").

## What the source got wrong or left inconsistent

### Lovelock & Whitfield (1982)

- **The text's 7,000 ppm should read 70,000 ppm.**
  - Owen et al.'s Table 1, one of the two references the text cites for it,
    gives 0.070 bar and attributes the value to Hart (1978), the other.
  - The printed line starts at 71,900 ppm.
  - Taken literally, 7,000 ppm gives 300 Myr, three times the stated span,
    and misses the printed line by 26 times as much as 70,000 does.
- **The glaciations are drawn to 4 °C,** about 5 px below the 5–10 °C the text
  gives for them.

### Caldeira & Kasting (1992)

- **"From 50 °C to 100 °C in <0.2 Gyr."** The paper's own figure takes
  0.227 Gyr to go from 50 to 97 °C, the highest level the trace reaches; the
  reconstruction takes 0.226 Gyr.
- **"The present level of 350 p.p.m."** appears in the text, but the model
  uses 320 ppm.

## What stays open

### Lovelock & Whitfield (1982)

- **The luminosity law.** Newkirk (1980) is not in hand, so the printed line
  is the only record of it. With the two dated anchors, a straight law of any
  slope gives 80 Myr; a curved law does not, and Gough's (1981) gives 61 Myr.
  Whether Newkirk's law is straight, or was straightened for the figure, would
  settle how much of the span rests on that drafting.
- **Hart (1978)** is not in hand. The 0.070 bar anchor is checked through
  Owen et al.'s Table 1, which attributes it to Hart.
- **Why the printed CO₂ line runs 2.3% steeper than the rule** and passes 354
  rather than 320 ppm today. It may be drafting, or a slightly different
  anchor.
- **The source of the "2/3 power".** WHK's published eq. (6) implies that
  P^0.364 is linear in ΔT_e at constant temperature, which is neither a square
  root nor a 2/3 power. The paper cites WHK "in the press", so the remark may
  refer to a different draft.
- **"Might by now have exceeded 50 °C".** The paper gives no climate model.
  WHK eq. (6) gives 40 °C; a more sensitive greenhouse would give more.

### Caldeira & Kasting (1992)

- **The acid chemistry at low soil CO₂.** This is the one ingredient that
  moves the CO₂-limited lifespan:
  - with the constants traced to the paper's sources, the C₄ limit comes at
    0.77 Gyr;
  - with the textbook set of the first build, at 0.79 Gyr;
  - the printed figure requires a_H to fall to 0.172 of today's by the kink.
    That holds with an SO₂ term 0.28 times as strong (sulphur 2.4% of
    today's soil-water H⁺, constants at 25 °C) or 0.40 times (5.2%, constants
    following T), and gives 0.86 Gyr.

  Chameides (1984) and Stumm & Morgan (1981) are not in hand. The constants
  used are secondary attributions (Butler 1991; Sellegri et al. 2003; Sander's
  compilation). Whether the difference lies in the constants, in how SO₂ was
  dissolved, or in the temperature at which the constants were evaluated
  cannot be settled without C&K's own values.
- **How today was closed.** With the printed equations, the figure favours
  closing at the fits' present, 287.89 K, which rounds to the stated 15 °C. A
  small adjustment to eq. (4) that closes at 288.15 K instead fits about as
  well (CK-R3), so the figure does not identify which was done.
- **The 20.4 W m⁻² of trapping by 320 ppm, and 3.4 W m⁻² for doubled CO₂,**
  come from the radiative–convective model itself, not from the fits in
  Box 1, and are not reproduced here.
- **"Exceed 50 °C after ~1.5 Gyr"** is stated "with negligible atmospheric
  CO₂", and the fits give 1.46 Gyr at 0.01 ppm, their lower bound. The model as
  run holds 1 ppm and reaches 50 °C at 1.32 Gyr, as Fig. 2 does (1.33). Which
  case the sentence means is open.
- **The 1 Gyr ocean-loss estimate** uses an ocean mass that the paper does not
  state; 1.4×10²¹ kg gives 0.97 Gyr.
