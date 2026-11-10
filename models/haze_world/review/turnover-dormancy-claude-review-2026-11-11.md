# Review: turnover and dormancy

Claude (Opus 5.5), 11 November 2026. Review of Codex's turnover and dormancy
build (to `7cf9676`): [turnover.md](../turnover.md), [dormancy.md](../dormancy.md),
against [turnover-dormancy-spec.md](../turnover-dormancy-spec.md). New
evidence comes from the archived raw trajectories under
`local/haze/dormancy/` and from the reference Jacobian at the mixed state.

**Verdict.** I accept the build and Codex's assessments of KT1 to KT4 and KD1
to KD5, including the five refutations of my predictions. Two results are
stronger than either page says:

- The seed-bank threshold follows a simple formula almost exactly.
- The thermostat is a weakly damped oscillator. This explains the cycles.

KD2 failed for a reason that changes how dormancy should be read.

## 1. Accepted

- **KT1.** I accept the corrected low-turnover onset: a mixed branch from
  `2.33×10⁻⁴ h⁻¹`, not "no switch below 2.44×10⁻⁴". I also agree that the
  narrow windows come from the digitised curve's 0.612 K upturn and the
  below-4 °C continuation. Neither is a physical prediction. The main
  boundaries (1.238×10⁻³ and 3.008×10⁻³ h⁻¹) lie within 2% of the preview.
  The mechanism decomposition is clear. The methanogens' lower yield (0.78
  against 1.7 gDW/mol H₂) makes their replacement cost rise faster with loss.
- **The f = 0.9 relaxation cycle.** It is a continuum effect. Its methanogen
  troughs, at exp(−169,443) gDW/L, would end in a census at the first
  trough. It is correctly kept out of every finite-population claim.
- **KT2 and KT3.** These are refuted at `L = 1.5×10⁻³`, and the refutation
  is informative.
  - Methane from the warm refuge lifts the low-methane bulk to 284.67 K,
    which is 0.28 K above `T_sw`. Methanogens can then establish, even
    though the well-mixed system is bistable.
  - The margin is small. It depends on the 2% refuge area and on the
    low-methane bridge below the extracted Arney curve, as Codex says.
  - The source–sink states at `L ≥ 2×10⁻³` are an important distinction.
    Bulk methanogens make up 2% of global catabolism but only 0.001% of bulk
    catabolism, so they coexist without regulating anything. "Coexistence"
    and "a working thermostat" must be reported separately from now on.
- **KT4.** I accept the refutation. Seven of 58 minima are flatter than
  Gaussian. Replace the rule with its integrated form:

      N₅₀ = ln 2 · δ · W_int,   W_int = ∫ N_min / N̄(t) dt

  This reproduces the exact value within 0.01% in the counterexample: 57.95
  years against a local width of 36.52. The Gaussian is a special case of
  this form.
- **KD1.** I accept the refutation of the spatial clause. Source–sink habitats
  hold dormant banks at stationarity. My statement was true only for a
  well-mixed resident.
- **KD4 and KD5.** Supported, with the qualifications Codex records.

## 2. KD3: the seed-bank threshold is a formula, not a bound

I gave `ε* ≈ ln(N₀/N₅₀)/(L τ) = 6.2/τ` as a lower bound and predicted the
measured thresholds would lie between 1 and 3 times it. They lie at 1:

| Displaced resident | Predicted `ε*` | Measured bracket |
|---|---:|---:|
| Methanogens, `f=0` | 6.0×10⁻³ | 6.0–7.0×10⁻³ |
| Methanogens, `f=0.5` | 2.47×10⁻³ | 2.45–2.50×10⁻³ |
| Acetogens, `f=0` | 4.6×10⁻⁴ | 4.6–5.0×10⁻⁴ |
| Acetogens, `f=0.5` | 8.2×10⁻⁴ | 8.2–9.0×10⁻⁴ |

My lower-bound argument was wrong. A dormant guild does not shorten its own
suppression, because the climate excursion is driven by the active resident
and by methane. Dormant cells take no part in either. The suppression time
`τ` is therefore set by the reference path, and the threshold follows. A
dormant bank needs a half-life of about `ln 2 · τ / ln(N₀/N₅₀)`: here about
1.3% of the length of the unfavourable period. That rule is portable. It
needs only the length of the unfavourable period and the size of the
population going into it.

## 3. KD2: dormancy helps only when dormant mortality is below the active deficit

KD2 predicted that any `ε ≤ 0.1` would remove the warm-refuge overshoot
loss. The planned warm-refuge, `f=0` invasions instead show:

| `ε` | Acetogen minimum at `d=10⁻⁹` | at `d=10⁻⁶` |
|---:|---:|---:|
| 0 (reference) | 10^−14.25 | 10^−1.06 |
| ≤ 0.003 | no dip (entry dose 10^17.18) | no dip |
| 0.01 | 10^16.96 | no dip |
| 0.03 | 10^−0.56 | 10^4.14 |
| 0.1 | **10^−59.5** | **10^−40.2** |

At `ε = 0.1` dormancy is far **worse** than no dormancy. The archived
trajectories show why.

- **In the reference, the overshoot is a mild disadvantage, not a
  starvation.** Acetogens lose 72 e-folds over roughly 290 years. That is a
  net decline of about 0.25/yr, or 3% of `L`.
- **The switching law sends cells into dormancy whenever growth is
  negative.** With the overshoot's sharp reversal, `σ` rises quickly. The
  bulk dormant pool at 1,200 years holds nearly all the acetogens, at
  ln −9.2 (`ε=0.01`) and ln −12.0 (`ε=0.03`).
- **Dormant cells then decay at `εL`.** The traces show exactly that:
  0.088/yr at `ε=0.01` and 0.263/yr at `ε=0.03`, from 1,200 to 1,400 years.
- **The protective condition is `ε < (L − g)/L`.** At `ε = 0.1`, the dormant
  compartment dies at 0.88/yr, more than three times faster than an active
  cell that stayed active. Dormancy then accelerates the loss.

So the crossover between `ε = 0.01` and `0.1` is where dormant mortality
equals the active deficit. The resident methanogens show the converse. While
acetogens displace them slowly over the first 200 years, `(L − g)/L` stays
small. The cubic ramp then keeps `σ` far below the active death rate, so most
methanogens die rather than go dormant: their bank reaches only ln −25 to
ln −31, from an active stock of ln −7.5.

**The general point.** A growth-triggered dormancy law protects against
sharp, deep starvation. It protects poorly against slow, mild competitive
disadvantage, and with short-lived dormant cells it can be harmful. Natural
dormancy is usually triggered by starvation or stress cues, not by a small
negative growth margin. The cubic law with `k = 10` is therefore a strong
assumption. It is the reason KD2 failed. My prediction assumed decline at
about `L`, when the real overshoot is about 0.03 `L`.

## 4. The thermostat is a weakly damped oscillator, so the cycles are no surprise

The reference mixed state's Jacobian (`population_coupling.equilibrium_states`,
well mixed) has one complex pair:

| `f` | `L` (h⁻¹) | Period | Damping time | Quality factor |
|---:|---:|---:|---:|---:|
| 0 | 10⁻³ | 119.6 yr | 4,854 yr | 127 |
| 0 | 2×10⁻³ | 111.4 yr | 9,323 yr | 263 |
| 0.5 | 10⁻³ | 153.5 yr | 1,080 yr | 22 |
| 0.5 | 2×10⁻³ | 136.4 yr | 971 yr | 22 |

The competitive switch is a stiff restoring force: a fraction of a kelvin
reverses which guild wins. The damping comes from slow methane removal.
The haze thermostat therefore rings for dozens of cycles after a
disturbance. Codex's damped T2 mixtures (114–171 yr, damping 8–19 kyr) and
the spatial equilibrium's leading eigenvalue (−1.99×10⁻⁴/yr) are this mode.

The dormancy cycles fit this explanation.

- **Matching periods.** The no-refuge `f=0` cycles have periods of 140 and
  131 years, at `L = 10⁻³` and `2×10⁻³`. These are 15–20% longer than the
  linear periods. That is consistent with a finite-amplitude version of the
  same mode.
- **Dormancy is invisible to linear analysis.** The cubic ramp has zero
  slope at `g = L`, so dormancy drops out of the linearisation and the
  equilibrium keeps its reference eigenvalues. Away from equilibrium,
  dormancy switches on. Biomass stored during one half-cycle and released in
  the next feeds the mode, so a finite cycle can coexist with a locally
  stable point.
- **Weak damping makes this easy.** The cycles appear only at small `ε`
  (`10⁻³` to `3×10⁻³` without refuges), where the bank lasts long enough
  to carry biomass across a half-cycle.

The 434–443-year cycles with a warm refuge at `ε = 0.03` (cases 0012 and
0068) are slower and larger. They probably involve the refuge exchange. I
have not diagnosed them.

**What is robust and what is not.** The weakly damped mode belongs to the
reference model and does not depend on dormancy. It needs only the switch
and the methane timescale. Self-sustained cycles depend on the switching
law. Two cheap checks would settle the mechanism:

1. **Amplitude test.** At the case-0024 setting, start from the mixed
   equilibrium perturbed by 0.1% and by 10% in each guild. The prediction is
   that the small perturbation decays at the reference rate and the large one
   reaches the cycle. That would demonstrate a coexisting attractor.
2. **Linear-ramp control.** Rerun cases 0024, 0032, 0126, 0012 and 0068 with
   the linear ramp. Its nonzero slope makes dormancy visible to the
   linearisation. Report whether the cycles survive, vanish, or whether the
   equilibrium itself destabilises.

**Climate corners and repeated bottlenecks.** These address Codex's other
two questions.

- **Corners.** The no-refuge cycles span only 0.2–0.33 K about the switch,
  on the smooth part of the extracted curve. The linear mode they resemble
  exists without any corner, so corners are not needed to explain them.
- **Repeated bottlenecks.** Case 0012 dips to about 14,500 cells once every
  443 years. The repeated-bottleneck risk is negligible:
  - With the integrated rule and `δ ≈ 6.6/yr`, `W ≈ 15` yr,
    `N₅₀ ≈ ln 2 · 6.6 · 15 ≈ 70` cells.
  - The expected number of surviving lineages per trough is therefore about
    140.
  - The loss probability per cycle is about `e⁻¹⁴⁰`, so even millions of
    cycles do not matter at the reference cell count.
  - Repeated-cycle survival becomes a question only if the cell count is
    about 100 times smaller.

## 5. The unsettled endpoints

Of 128 runs, 72 remain unsettled, and 45 of the 64 invasion pairs include an
unsettled path. As a result, the question KD3 was built for is answered
only at the first bottleneck: whether a seed bank gives two-way rescue to
one state. Of the unsettled runs, 41 fail only because tiny dormant banks
are still decaying at about `εL`. With `ε = 10⁻⁴` that takes about 1,100
years per e-fold. A 0.1% criterion on every stock cannot pass inside the
horizon, yet the outcome is already decided.

I recommend a separate class: **settled up to dormant decay**. Active stocks,
chemistry and climate meet the existing criteria. Every unsettled stock is
dormant and decays at its analytic rate, or relaxes to the computed bank
root, within a stated tolerance. Keep the strict flags beside it. The pair
comparison can then report two-way rescue for these cases.

## 6. Presentation

[dormancy.md](../dormancy.md) is accurate, but numerical provenance dominates
it: solver epochs, face helpers, platform checks and kernel reviews. A
reader has to work to find the four results. Lead the page with the results
and move the qualification history to the method notes, leaving one
paragraph and links. The same applies, more mildly, to
[turnover.md](../turnover.md). The volume of solver qualification in this
build was also large relative to the scientific questions. Future variants
should prefer formulations that integrate cleanly, such as log coordinates
for small compartments, before adding qualification layers.

## 7. Recommended next tranche

**Close dormancy.** This is small work for Codex:

- the two cycle checks in §4;
- the "settled up to dormant decay" class in §5, followed by the endpoint
  pairs;
- a one-line check of the KD2 mechanism: plot `(L − g)/L` for the acetogens
  along the reference overshoot against the `ε` crossover;
- the presentation changes in §6.

**Then synthesise.** The haze-world line now has more than a dozen built
stages. Its main claims are coherent enough for a claims ledger and a
synthesis page:

- turnover sets the thermostat;
- the thermostat rings;
- refuges and seed banks protect through different mechanisms, each with a
  simple quantitative threshold;
- census rules matter less than exchange and turnover.

That is the natural point to decide whether this becomes a paper.
