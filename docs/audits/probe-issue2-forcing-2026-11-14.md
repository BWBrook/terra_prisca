# Probe Issue 2: regulation against what?

Claude (Opus 5.5), 14 November 2026. Barry raised this issue with Fable
(Claude Fable 5.2) as independent advisor.

- A Claude Sonnet 5.5 subagent wrote and ran the bounded numerical checks:
  `models/haze_world/review/issue2_forcing.py`, which writes
  `issue2_forcing.json` and `issue2_forcing_window.csv`. The run takes
  about 95 s.
- No production code changed, and there is no new experimental stage.
- Imposed warming F is a rigid shift of the climate curve, T_clim(r) → T_clim(r) + F.
- F was injected by wrapping `methane_budget.temperature_k` and every alias
  of it. Shifts of 0, 2.5 and −4 K reproduce exactly over r = 0–0.5, and
  the slope is unchanged.
- At F = 0 the script reproduces the archived values: T\*, τ_c = 0.1492 and
  1.1028 yr, the Issue 1 spread states bit for bit, and the 30-year D1 point
  at 29.98 yr.

## Verdict

The Introduction's question has an answer, and it strengthens the paper. The
regulator that is loose against supply is tight against sunlight.

- **Exact states.** They hold T\* against any imposed warming or cooling
  within a window of −15.5 to +8.1 K. That window is about 16–20% of
  sunlight.
- **Graded states.** Temperature follows the forcing by 0.1–6% of its size.
- **Fragility.** The critical response time is unchanged across the window,
  so the fragility does not depend on which disturbance is applied.

The rigid shift is a local idealisation. Exact pinning does not depend on it;
the size of the graded residual does.

## Q1. Is dT/dF ≈ |S|/k right?

The relation holds approximately, with a correction that can be explained.
Linearising the steady state, with M(P, T) the methane output, gives:

- E = ∂ln M/∂ln P at fixed T;
- G = ∂ln M/∂T at fixed P;
- k = |dT_clim/d ln r| at the state;
- S = −kE/(1 + kG), and **dT/dF = 1/(1 + kG) = |S|/(kE)**.

Fable's form is the case E = 1. Results are at f = 0.5, P = 0.30 unless
stated; k is in K per e-fold.

| State | S (K per e-fold) | k | dT/dF | \|S\|/k | ratio | E |
|---|---|---|---|---|---|---|
| Exact, f = 0 and 0.5 | 0 | 140.7 | 3 × 10⁻¹² | 0 | pinned | n/a |
| D1 acetate, 30-yr point (f = 0, κ = 0.1440) | −0.278 | 140.7 | 0.00136 | 0.00197 | 0.69 | 1.45 |
| Spread σ = 1 K, d = 10⁻⁴ | −2.934 | 140.7 | 0.0194 | 0.0209 | 0.93 | 1.08 |
| Spread σ = 3 K, d = 10⁻⁴ | −8.304 | 140.7 | 0.0550 | 0.0590 | 0.93 | 1.07 |
| Strong exchange σ = 3 K, d = 0.1 | −7.200 | 140.7 | 0.0477 | 0.0512 | 0.93 | 1.07 |
| σ = 3 K, P = 0.24 | −10.33 | 115.0 | 0.0826 | 0.0898 | 0.92 | 1.09 |
| σ = 3 K, P = 0.42 | −5.953 | 143.0 | 0.0392 | 0.0416 | 0.94 | 1.06 |

dT/dF is the central difference at ±0.1 K; the ratio is (dT/dF)·k/|S|.
Finite responses at ±1 and ±3 K are in the JSON. All states solved at every
F.

**Where the relation needs correcting:**

- **Hydrogen outlet (spread states, E ≈ 1.07).** At fixed temperature the
  outlet removes a nearly fixed hydrogen flux, set by the hydrogen pressure
  at the switch. Methane therefore rises faster than supply. If the outlet
  flux were exactly fixed, E = 1/(1 − outlet share). That gives 1.081, 1.103
  and 1.057 at P = 0.30, 0.24 and 0.42, against computed values of 1.074,
  1.088 and 1.061. This is my interpretation and agrees to within 1.5%;
  assimilation is not separated out.
- **Acetate feedback (E = 1.45).** At fixed temperature, more supply builds
  more acetate. The acetate slows acetogens and shifts the community toward
  methanogens, so supply changes composition in a way that forcing does
  not. Against forcing, the D1 point is 31% tighter than |S|/k.
- **Strong exchange.** It changes S and the response to F together, and the
  ratio stays at 0.93. Mixing does not break the relation.
- **Away from the switch.** The relation holds, but k is local. Case B's
  curve is piecewise linear with a vertex at r = 0.1944, just below the
  reference state, so k falls from 140.7 to about 116 for F ≲ −1 K. Finite
  responses at |F| ≥ 1 K therefore exceed the derivative by about 5%.

## Q2. How wide is the working window?

At P = 0.30 the window is **F = −15.47 to +8.14 K**. It is the same at
f = 0 and f = 0.5, and T = T\* throughout.

| End | F (K) | r | Local k | Cause |
|---|---|---|---|---|
| Warming | +8.14 | 0.2222 | 4.1 | No cooler climate is available: case B's extracted minimum, 273.39 K |
| Cooling | −15.47 | 0.1667 | 75.0 | No warmer climate is available: case B's peak, 297.01 K |

- **What limits the window.** At both ends the haze-cooling branch runs
  out. Coexistence and stability do not: both guilds are present and the
  state is stable at τ = 0 at all 30 swept values.
- **Other equilibria.** Other states at the same F, such as warming-branch,
  single-guild or lifeless states, were not followed.
- **Supply range.** By the reduced estimate (r\* P/P_hi to r\* P/P_lo), the community could make the methane
  needed for r = 0.128–0.256. That range covers the whole branch, so supply
  is not the binding constraint at P = 0.30.

**Conversion to sunlight.** Two sourced conversions agree:

- *Arney et al. 2017* (10.3847/1538-4357/836/1/49), table 3. At 1 bar,
  CO₂ = 0.01 bar and CH₄/CO₂ = 0.2, the surface is 272 K under the 2.7-Ga
  Sun (278 W m⁻² mean incoming shortwave) and 299 K under the modern Sun
  (342 W m⁻²). The secant is 1.17 K per 1% of sunlight. It includes the
  change in haze photochemistry; the setting is case A, not case B.
- *IPCC AR6* (Forster et al. 2021, 10.1017/9781009157896.009). The best
  estimates of climate sensitivity (3 K) and of the forcing from doubled CO₂
  (3.93 W m⁻²) give 0.76 K per W m⁻². Taking 1% of 278 W m⁻² at albedo 0.32
  gives 1.44 K per 1%; the likely range of sensitivity gives 1.2–1.9 K per
  1%. This is a modern-climate value.

The 23.6-K window is therefore about **16–20% of sunlight**: +5–7% on the
bright side and −10–13% on the dim side.

For scale, Gough's (1981) solar model (10.1007/BF00151270) gives
S/S₀ = 0.81 at 2.7 Ga and brightening of about 7% per billion years then.
Under a rigid shift, the bright side would reach the Sun of about
1.8–2.0 Ga, and the dim side reaches the Sun's earliest luminosity. This is
an illustration only (see Q3).

## Q3. Is a rigid shift supported?

**A rigid shift is a local idealisation. Cross-case evidence supports exact
pinning but limits the graded residual.**

- **The curves are not translations of one another.** Arney's cases A–D
  differ in CO₂ and pressure, not sunlight. Their peaks range from 273.4 to
  297.0 K. The ratio at which haze begins to cool ranges from 0.16 to 0.18,
  and their slopes at T\* differ.
- **New bounded check: the exact state in other cases** (f = 0.5, a coarse
  scan of P):
  - Case A holds T\* exactly at r = 0.190, with k = 210 and minimum
    τ_c = 1.1 yr.
  - Case C holds T\* exactly at r = 0.178, with k = 46 and τ_c = 1.3–1.4 yr.
    Its peak, 282.19 K, only just exceeds T\*.
  - Case D has no mixed state at any supply, because its maximum,
    273.39 K, lies below T\*.
  - Case C also has a state on the assumed low-methane bridge and an
    unstable warming-branch state. Neither is on the extracted cooling
    branch.
- **Earlier one-guild evidence.** C01 shows the scalar model pinned to its
  physiological edge across all four cases (78 cases).
- **Solar change alters haze as well as heat.** Arney et al. (2017) show the
  modern Sun's ultraviolet changes haze production. No matched
  T(CH₄/CO₂, S/S₀) grid exists (`models/haze_response/solar-responses.md`,
  Codex, 9 November).

What follows:

1. Exact control holds T\* under any change in climate that leaves T\* on the
   cooling branch, and the community can supply the methane required. This
   does not depend on rigidity.
2. For graded states, the residual is |S|/(kE) with the k of the actual
   curve at the state. Across A–C, k varies 4.5-fold at T\*, so the residual
   would too.
3. The window's ends are set by the curve's peak and minimum, which move
   with forcing. The 16–20% figure therefore holds only under the rigid
   shift.

## Q4. Is the critical response time unchanged?

**At a fixed state, yes, exactly.** F enters the equations only as a
constant added to the temperature, so the linearisation, and hence τ_c,
depend on the state alone. This was confirmed from the code path.

**Across the window, τ_c moves very little:**

| F (K) | −15.5 | −12 | −9 | −6 | −3 | 0 | +3 | +6 | +8.0 | +8.14 |
|---|---|---|---|---|---|---|---|---|---|---|
| τ_c, f = 0 (yr) | 0.154 | 0.157 | 0.147 | 0.150 | 0.153 | 0.149 | 0.153 | 0.157 | 0.842 | 2.09 |
| τ_c, f = 0.5 (yr) | 1.18 | 1.16 | 1.12 | 1.12 | 1.12 | 1.10 | 1.10 | 1.11 | 2.03 | 3.60 |

- From −15.5 to +6 K, τ_c stays within 7% of the reference.
- It lengthens only in the last kelvin before the curve minimum, where the
  curve flattens (k → 4). Haze then has little leverage, so the loop gain is
  small.
- The fragility result therefore holds across the whole forcing range.
- The spread-state τ_c was not swept in F.

## Q5. What should the paper say?

I recommend keeping the sunlight motivation and answering it with a forcing
result, rather than reframing the paper around supply. The main message
stands as adopted.

**Results:** a new §3.5, "Sunlight acts through the same loop" (arrival
order becomes §3.6).

> Changes in sunlight act on the same loop. We represent one as a warming F
> that shifts the climate curve, T_clim(r) + F. Linearising the steady
> state gives dT/dF = |S|/(kE) (3.2), where E is the response of methane
> output to supply at fixed temperature. Exact states hold T\* for every
> shift from −15.5 to +8.1 K, the range over which case B's haze-cooling
> branch can supply the cooling needed. At both ends the branch runs out,
> before coexistence or stability fails. Over that range the critical
> response time stays within 7% of its reference value until the last
> kelvin. Graded states follow the forcing weakly: temperature moves by
> 0.14% of F at the 30-year acetate point, and by 1.9% and 5.5% at habitat
> spreads of 1 and 3 K. At fixed temperature methane rises slightly faster
> than supply, through the hydrogen outlet and, with acetate feedback,
> through a change in composition (E = 1.06–1.09 and 1.45; ESM). Arney's
> cases A and C, which differ in carbon dioxide and pressure, also hold T\*
> exactly, with k from 46 to 210 K per e-fold; case D never reaches T\*.

**Abstract** (one sentence after the durability result):

> Against sunlight the same communities are much tighter: temperature
> followed an imposed warming by at most 6% of its size, and exact states
> held over shifts equivalent to about a sixth to a fifth of sunlight.

**Introduction, I5** (one sentence):

> We vary hydrogen supply throughout and show that the same local
> sensitivity sets the response to a change in sunlight.

**Discussion, 4.4** (scale and caveat):

> Treated as a rigid shift, the exact window corresponds to about 16–20% of
> sunlight (Arney et al. 2017; Forster et al. 2021). A brighter Sun also
> changes haze photochemistry (Arney et al. 2017), so a matched solar sweep
> of a haze climate is needed to test the regulator against the Sun's
> brightening.

**Conditions, 4.6:**

> Sunlight enters as a rigid shift of one published climate curve.

**ESM.** A new section, S10 "Forcing", holds the derivation, the table
above, the window, τ_c(F) and the cross-case check. The provenance section
becomes S11.

**Claims:**

- C62: the forcing relation and E.
- C63: the window and τ_c(F).
- C64: cross-case exact pinning (A, C) and the absence in D.

**Main message.** I recommend no change: "hold a planet's temperature" now
covers both disturbances. The alternative, if Barry wants the Sun named:

> Microbes can hold a planet's temperature against a brightening Sun, but
> exact control fails when climate responds slowly. Imperfect control lasts
> far longer, and grows looser as habitat temperatures differ.

That alternative claims more than a rigid-shift test shows, so I do not
recommend it.
