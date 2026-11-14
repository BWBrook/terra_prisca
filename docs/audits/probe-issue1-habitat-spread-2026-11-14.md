# Probe Issue 1: where does a real planet sit on Figure 3?

Claude (Opus 5.5), 14 November 2026. Raised by Barry with Fable (Claude Fable
5.2) as independent advisor. A Claude Sonnet 5.5 subagent ran the finite
branches; a Codex (GPT-6.1 Sol) web job sourced the habitat numbers, which
were checked against Crossref and the primary figures. Bounded checks only:
no new experimental stage, no model code changed.

## Verdict

The issue stands. The proportionality is real and has a simple, exact
explanation, and it changes the paper's lesson. The price of durability is
not a small dial setting; habitat temperature spread sets it, and realistic
spreads make it large.

## Q1. Is the proportionality real, and why?

**Yes.** In the weak-mixing limit each habitat colder than T\* is held by
acetogens and each warmer one by methanogens. A steady state needs the
methane flux to keep r near r\* (the haze slope is steep). Supply therefore
fixes the share of methanogen-held habitats, and that share fixes where the
switch sits within the spread. Across the coexistence supply range,
temperature sweeps the whole habitat spread, from T\* + σ to T\* − σ.

Locally, with no fitted parameter:

1/|S| = 1/k + 1/|S_geo|,  |S_geo| = 2σ (P_lo/P) Q/(Q − 1),

where k = |dT_clim/dr|·r\* = 140.7 K per e-fold (the bare haze response), Q
= P_hi/P_lo is the homogeneous coexistence supply ratio (1.9955 at f = 0.5;
unbounded at f = 0, giving the factor 1), and P_lo = 0.229178. For any
distribution of habitat offsets, |S_geo| = 1/[p(δ_switch)·Δ], where p is the
density of habitats at the switch temperature and Δ the change in log
methane yield per unit methanogen share. **Precision is set by how many
habitats sit near the switch temperature.**

Evidence:

- `models/haze_world/review/issue1_geometric_check.py`: against all 40
  fixed-chemistry spread states in ESM S4, the 20 weak-mixing states
  (d ≤ 10⁻³ yr⁻¹) agree within −6% to +4%. At d = 0.1 mixing homogenises
  habitats and the formula overestimates |S| by up to 30%, as expected.
  Fable's form, 2σ/ln Q = 2.89σ, is the log-average of the same relation.
- `models/haze_world/review/issue1_spread_response.py` (finite branches,
  f = 0.5, fixed products, d = 10⁻⁴): at σ = 1 and 3 K the computed branch
  runs from T\* + σ to T\* − σ within 0.01 K. A reduced model (flux balance
  plus T_clim plus the methanogen share) matches the full continuum solution
  within 0.04, 0.13, 0.21 and 0.21 K inside the coexistence range at
  σ = 1, 3, 6 and 8 K. The reference state reproduces the archive
  (S = −2.934 K per e-fold, τ_c = 947.4 yr).

## Q2. Where do Archean habitats sit?

| Archetype | Spread (half-width) | Response time | Sources |
|---|---|---|---|
| Sunlit surface and shallow water | 14–21 K | ~4 yr (1.6–5.5) | Eager-Nash et al. 2023 fig. 7a: equator–pole 28–33 K with CO₂ alone, up to +8 K with CH₄; Mak et al. 2023 fig. 5: ~42 K (289 → 247 K) with haze at CH₄/CO₂ = 0.125; modern SST ~28 K (Kodera et al. 2016 fig. 2e); fast mode 4.1 yr (Geoffroy et al. 2013 table 4) |
| Deep water and sediments | ~2.7 K (modern abyssal −1.05 to 4.39 °C) | ~250 yr (126–698) | Sweetman et al. 2017 table 1 (World Ocean Atlas); slow mode 249 yr (Geoffroy et al. 2013 table 4) |

Diel swings in shallow mats are larger again (15–27 °C at Guerrero Negro;
Des Marais et al. 2003), but they are transient, not persistent offsets. No
published Archean deep-water spread exists; EONS assumes deep water 15 K
below the surface (Horne & Goldblatt 2024). An offset of that kind moves the
regulated surface temperature; it does not change the spread.

DOIs (Crossref-checked): 10.1029/2022JD037544 (Eager-Nash; arXiv
2302.12518 read); 10.1029/2023JD039343 (Mak et al.; arXiv 2310.06818 read);
10.5194/acp-16-12925-2016 (Kodera); 10.1175/JCLI-D-12-00195.1 (Geoffroy);
10.1525/elementa.203 (Sweetman); 10.1029/2023GC011252 (Horne & Goldblatt);
NTRS 20030023599 (Des Marais). Charnay et al. 2013 (10.1002/jgrd.50808)
gives larger contrasts for an extreme cold case and is not used.

## Q3. What is left of regulation there?

- **Deep or sediment habitats (σ ≈ 3 K, τ ≈ 250 yr).** Durable: τ_c is
  3,500–4,800 yr at σ = 3 K over P = 0.30–0.42, and no loss was found
  through 10⁴ yr at P = 0.24. Precision is moderate: across the factor-two
  coexistence range, temperature moves through about 6 K (5.4 K computed),
  with S ≈ 7–10 K per e-fold. The habitat would hold its temperature within
  about ±3 K of T\*.
- **Surface habitats (σ ≈ 15–21 K, τ ≈ 4 yr).** The spread exceeds the
  physiology support (273–303.15 K), so the full model cannot be run there.
  The formula gives S ≈ 35–44 K per e-fold, against 141 K for the bare haze:
  a gain of only 3–4. A factor-two change in supply would move temperature
  by tens of kelvin, more than the 23-K haze-cooling branch. Little
  regulation remains. Durability is not the binding constraint.
- **Comparison without acetogens.** Over the same supply range, methanogens
  alone fall from 281.5 K to the 274-K haze floor and stay there; the
  plateau shape beyond Arney's last point is our assumption. The community's
  contribution is to hold temperature near T\*, about 8 K above that floor,
  within the band set by its spread.

`issue1_spread_response.png` shows the finite responses (σ = 1, 3, 6, 8 K)
against methanogens alone. A cleaned version of it is the proposed
replacement for the local tangents in figure 3*b*.

## Q4. Does the main message survive?

Not as worded. "Slightly imperfect control is far more durable" reads as if
a small, tunable loss of precision buys durability. That holds for nearly
uniform habitats (the 0.07–0.32 K per e-fold of the dial branches). On a
real planet, habitat spread imposes the imprecision. Surface habitats leave
little regulation; deep habitats give durable control within a few kelvin.

Proposed main message (25 words):

> Microbes can hold a planet's temperature, but exact control fails when
> climate responds slowly; durable control holds it only as tightly as
> habitats are uniform.

The durability result (C54, C57) stands unchanged. What changes is what the
price means.

## Wider and asymmetric spreads

**Admissible:**

1. Draw habitat offsets from a sourced distribution, such as an
   area-weighted zonal-mean profile from an Archean GCM, with any asymmetry
   it has.
2. Treat habitats outside the physiology support as inactive: no growth, and
   their hydrogen leaves by exchange.

Below 273 K these communities lack liquid water. Above 303.15 K the
transferred kinetics have no support. Because only the density of active
habitats at the switch and their cumulative share enter the steady state,
the result depends little on physiology away from T\*.

**Sensitivity check only:** a winner-only extension, in which acetogens win
every colder habitat and methanogens every warmer one beyond the support.

**Not defensible:** extrapolating the six-temperature kinetic tables
quantitatively beyond 4–30 °C.

## Proposed changes (for agreement before the text step)

1. **Results 3.4 and the ESM:** add the geometric relation and its fit (both
   checks), and add the finite responses.
2. **Discussion 4.4:** add the two archetypes with sources, and state where
   each sits.
3. **Figure 3:** replace (*b*) with the finite responses. Optionally mark the
   archetypes' response-time ranges on (*a*).
4. **Main message:** revise as above (Barry's decision).
5. **Claims:** new ledger entries for the geometric relation and the finite
   sweep.
