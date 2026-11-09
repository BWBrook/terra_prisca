# Methane-loss steepness: recovered evidence and remaining gap

Codex (GPT-6), 9 November 2026. A quantitative **haze-free benchmark** is
recovered. A matched local loss elasticity for Arney's 2016 case B near
CH₄/CO₂ = 0.2 is still unavailable. No production loss law is changed.

The required quantity is n = d ln F_required / d ln r along a specified
steady photochemical scenario. At fixed CO₂ and total pressure this is also
the logarithmic slope against methane surface mixing ratio or partial
pressure. It is not a slope against methane column without a column mapping.
Nor is a reduction of loss at fixed methane a measurement of this slope.

## A published quantitative benchmark without haze

[Akahori, Watanabe & Tajika (2024)](https://doi.org/10.3847/1538-4357/ad47f3),
published Figure 6a, supplies imposed methane source versus surface partial
pressure. Read-offs compare about 5.3–21.4 Tmol C yr⁻¹ along each fixed-CO₂
curve:

| CO₂ (bar) | Approximate methane partial pressures (bar) | Finite-secant n | Conservative read-off envelope |
|---:|---|---:|---:|
| 0.01 | 3.8 × 10⁻⁶ to 2.2 × 10⁻⁴ | 0.344 | 0.263–0.453 |
| 0.03 | 4.4 × 10⁻⁶ to 4.0 × 10⁻⁴ | 0.309 | 0.239–0.400 |
| 0.10 | 5.7 × 10⁻⁶ to 7.0 × 10⁻⁴ | 0.289 | 0.225–0.372 |

The plotted cases exclude substantial haze deposition, and all read-offs
have r < 0.03. Photochemistry uses a fixed vertical temperature profile with
surface temperature about 277 K; panel (f)'s varying greenhouse temperature
is diagnosed separately. Backgrounds include 2.8-Ga sunlight, S/S₀ = 0.8,
1-bar total pressure and H₂ source 10¹⁰ molecules cm⁻² s⁻¹. OH limitation
produces sublinearity without haze. Use imposed net source, not the gross
destruction panel: the published model also reforms methane internally.

These are **finite secants, not local derivatives or confidence intervals**.
The envelopes allow ±5 native pixels per endpoint and ±2 per calibrated tick.
They show sublinearity over a broad haze-free range, rather than bounding
the derivative at any particular point. The published figure differs from
the earlier preprint; only the final journal figure is used here.

Data: [six read-offs](akahori2024_figure6a_points.csv),
[calibration, conditions and source hashes](akahori2024_secants.json).
Recompute the numbers with:

```sh
uv run python models/haze_world/evidence/check_loss_secants.py
```

The final PDF and extracted native image are kept under
`local/haze/loss_elasticity_sources/`, with filenames and SHA-256 values in
the metadata. The numerical decimals reflect the calculation, not equivalent
precision in the plotted observations. Boundary settings inherited from the
paper's cited model were not independently rebuilt in this recovery.

## Arney 2018: threshold anchors, not a loss slope

[Arney et al. (2018)](https://doi.org/10.1089/ast.2017.1666), Figures 4–5,
express the same haze optical depth against methane flux and surface ratio.
Pairing their highlighted τ₁₉₀ = 1 contours for the 2.7-Ga Sun, 1 bar and
1× organic-sulfur source gives:

| CO₂ mixing ratio | Required methane flux (molecules cm⁻² s⁻¹) | CH₄/CO₂ |
|---:|---:|---:|
| 0.010 | 2.86 × 10¹¹ | 0.305 |
| 0.018 | 3.16 × 10¹¹ | 0.272 |

These are slices of interpolated plotted contours, not raw simulations.
Approximate reading envelopes are ±0.006 dex in flux and ±0.015 dex in
ratio, excluding interpolation/model uncertainty. Accepted-manuscript vector
positions visually agree with final journal figures. The graph's first
ratio differs from the text's rough 0.2; both are retained as distinct
targets. [Provenance and limits](arney2018_threshold_anchors.json) identify
the versions and hashes.

Each background yields only one paired point: **do not difference the two
rows to infer elasticity**, since CO₂ changes. Filled-colour band pairing
was rejected for calibration because normalizations and interpolation meshes
differ. The chemistry includes organic-sulfur sources and differs from 2016;
even the 0.018 slice is not a matched case-B run. Its ratio is outside the
2016 case-B extracted interval. No accessible per-run output grid was found.

## What can be carried into haze-world

The benchmark establishes that sublinear source–abundance response is
physically represented in published anoxic photochemistry. It justifies
exploring shallow losses. It does **not** select n = 0.2, validate the log
law, identify haze self-shielding as the cause, or calibrate the hazy branch
around r = 0.2. Even a local derivative there would constrain only the local
loss shape; an equilibrium displacement also depends on its normalization
and curvature over the range traversed.

For the next empirical step, reconstruct a net source–ratio curve under one
explicit photochemical configuration, keeping stellar spectrum, background
gas sources, redox boundaries, thermal profile and aerosol treatment together.
Reproduce a published curve before transporting it to the Arney climate
closure. The current H result remains conditional on the assumed loss family.

## Other leads checked

- [Pavlov, Brown & Kasting (2001)](https://doi.org/10.1029/2000JE001448):
  the inspected primary text treats a haze-free methane source–loss relation
  at CO₂ mixing ratio 0.006; methane and H₂ change together. It does not
  provide a matched hazy case-B slope. No quantitative digitization is used.
- [Zahnle, Claire & Catling (2006)](https://doi.org/10.1111/j.1472-4669.2006.00085.x):
  Figure 5 varies O₂ at fixed methane, while Figure 6 plots other fluxes.
  Neither is the required methane-loss derivative at fixed background.
- [Kharecha, Kasting & Siefert (2005)](https://doi.org/10.1111/j.1472-4669.2005.00049.x):
  full source was not recovered through the tested routes. Aggregate flux
  and abundance ranges are not converted into a slope.
