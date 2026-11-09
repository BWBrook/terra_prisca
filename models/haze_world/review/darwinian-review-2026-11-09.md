# Review of the evolving-optimum variant

Codex (GPT-6), 9 November 2026. Reviewed `88fbad8`, with an independent
mathematical audit. **Repair the reported local sensitivities and the
return-threshold plot before using their numerical thresholds.** The
evolved climates and local stability results survive. Production code and
its original outputs are retained for Claude to correct and regenerate.

All 55 existing tests pass. Independently refining all 205 tabulated
equilibria and constructing their analytical full-system Jacobians confirms
negative maximum-real eigenvalues in every case. Their values agree with
the table to its six-decimal rounding. The hard-floor projected optimum is
correct. No additional failure was found in the selected endpoints.

## Local sensitivity is not the reported finite-step response

`supply_sensitivity()` uses supply changes of ±0.5%. Its values are valid
finite-change secants, but are labelled local derivatives. Near bends in
the piecewise-linear climate curve, the control traverses a different
temperature slope from the thermal strain, even though they start at the
same equilibrium. The discrepancy is material:

| Case | Reported ±0.5% ratio | ±0.1% ratio | ±0.001% ratio | Analytical local ratio |
|---|---:|---:|---:|---:|
| F: floor 290 K, logarithmic loss | 0.301058 | 0.808437 | 0.808476 | 0.808476 |
| H: E = 0.6 eV, power loss n = 0.5 | 0.427925 | 0.898968 | 0.898970 | 0.898970 |
| H: E = 0.65 eV, logarithmic loss | 0.299532 | — | — | 0.295431 |

The last row confirms that strong buffering really does remain in some H
cases. These findings change its onset and several claimed magnitudes;
they do not eliminate it. The finite ±0.5% response could be retained as a
separate forcing-amplitude experiment if clearly labelled.

For positive biomass the equilibrium methane source is

    S(r, Φ, θ) = c [Φ − Φ_K/(ρ(T(r), θ) − 1) + Φ_abiotic].

On a smooth climate segment and a regular ecological branch, with the trait
fixed, define

    S_r = c Φ_K ρ_T T_r / (ρ − 1)².
    dT/d ln Φ = T_r c Φ / (L_r − S_r).
    R = (dT/d ln Φ) / (matched realized-ρ control derivative)
      = L_r / (L_r − S_r).

The matched control has derivative T_r c Φ/L_r. This uses the full derivative
of capture with supply: ∂(Φη)/∂Φ = 1, rather than η. At a singular optimum,
ρ_θ = 0, so allowing the optimum to re-evolve adds no first-order source
response. At a locally binding floor the optimum stays fixed. Thus local
ecological and re-evolved sensitivities coincide at these regular endpoints.
Their finite-step differences are not distinct local evolutionary effects.
At an exact climate vertex, report one-sided responses rather than implying
a unique derivative.

The corrected minimum H ratios over the tested E grid are:

| Loss | Minimum local H ratio | Largest H temperature offset (K) | First E with local R < 0.5 (eV) |
|---|---:|---:|---:|
| Power n = 0.2 | 0.2959 | 4.3237 | 0.45 |
| Power n = 0.5 | 0.3120 | 1.0350 | 0.65 |
| Power n = 1 | 0.9172 | 0.3202 | None |
| Power n = 2 | 0.9533 | 0.1305 | None |
| Logarithmic | 0.2954 | 4.6102 | 0.40 |

All minima occur at E = 0.65 eV. A floor first attains R < 0.3 at 291 K for
n = 0.2 or log loss, 292 K for n = 0.5, and 293 K for n = 1 or 2. These are
grid-dependent scenario thresholds, not organismal measurements. The
reported suggestion that all n ≤ 0.5 cases reach a 4.3–4.6 K offset is too
broad: n = 0.5 reaches only about 1.04 K in the tested range.

## Returning requires the net-growth edge, not the living temperature

`invades_lifeless()` correctly evaluates the strain at the abiotic methane
equilibrium. The two tabulated invasion classifications reproduce in every
case. The plotted threshold and verbal interpretation do not follow from
those classifications.

Let r_a = L⁻¹(c Φ_abiotic). The lifeless donor pool gives the invasion condition

    ρ(T(r_a)) > ρ_need = 1 + Φ_K/Φ.

On the cold side of the strain's thermal curve, its net-growth edge is

    T_edge = θ − w sqrt(1 − ρ_need/ρ_peak).

`cold_edge_k()` already computes this resource-dependent edge correctly.
It is below the living equilibrium temperature. There is also a warm edge;
invasion requires the abiotic temperature to lie between the two.

The bridge temperature at r_a is not T₀. For the implemented bridge, let

    z = ln(1 + r_a/s) / ln(1 + r₁/s).
    T(r_a) = (1 − z) T₀ + z T₁.
    T₀,critical = (T_edge − z T₁)/(1 − z).

Panel (d) plots T_edge but labels it as the lowest bridge T₀ permitting
invasion. For the displayed linear-loss curves the difference reaches
0.847 K; across all loss shapes it reaches 16.69 K. This is a labelling and
threshold-conversion error, not a defect in `invades_lifeless()`.

A counterexample to “must be warmer than the regulated climate” is the
300-K floor with linear loss:

- Living equilibrium: 281.363830 K; net cold edge: 281.064687 K.
- With bridge T₀ = 280.9 K, actual abiotic temperature is 281.145148 K.
- The strain invades, with initial per-capita growth about 0.07335 yr⁻¹
  under the default death rate, despite both temperatures being below the
  living equilibrium. The critical bridge T₀ is about 280.817723 K.

Strong buffering and failed return coexist in the tested 265-K scenarios;
that is a conditional result, not a universal equivalence. The assumed
low-methane bridge controls this part of the finding.

## Endpoint choice, persistence and next action

`evolved()` selects the feasible root with largest methane ratio. Its
“warmest” docstring is inaccurate on a cooling branch. The current selected
roots are stable, but branch selection by itself establishes neither an
adaptive path nor a basin of attraction. Local full-system stability is
also distinct from finite-population persistence during a supply decline.

Use the analytical local response above, or demonstrate convergence of a
smaller finite difference while detecting climate vertices. Regenerate the
endpoint measures, figure and associated prose; preserve any finite-forcing
experiment under its own label. Convert panel (d) to critical bridge T₀ or
relabel it as the cold edge and show actual abiotic temperatures. These are
review recommendations, not changes made to the production variant here.

Reproduce the independent 205-endpoint audit from the repository root:

```sh
uv run python models/haze_world/review/check_darwinian.py models/haze_world/review
```

Outputs: [local response and threshold table](darwinian_local_audit.csv),
[summary](darwinian_local_summary.json). The analytical audit does not call
the production finite-difference sensitivity or Jacobian implementation.
