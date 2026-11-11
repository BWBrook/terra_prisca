# B4: the dormant bank is not a linear thermal lag

Codex, 12 November 2026. This implements the bounded B4 diagnostic after
review of the [Stage B specification](../dynamic-realisation-spec.md).
The original PB7 prediction is retained unchanged. The frozen reference
dormancy equations are not smoothed or otherwise modified.

## Design correction before the runs

The mixed state has positive active biomasses X_i*, zero dormant stocks Z_i*,
and zero net growth n_i*. Let κ be the switching factor and L_y the active
loss rate in inverse years. Close to this state, the clipped linear ramp gives

    σ_i = κ max(−n_i, 0),    ρ_i = κ max(n_i, 0),
    active_i' = reference_i' − σ_i X_i + ρ_i Z_i,
    bank_i' = σ_i X_i − ρ_i Z_i − ε L_y Z_i.

The one-sided directional derivative at the mixed state therefore contains
κ X_i* max(−Dn_i·v, 0). This is homogeneous but not additive in the
perturbation v, so **there is no ordinary Jacobian**. A centered finite
difference would average different physical sectors and invent a matrix that
is not the derivative of this vector field.

Wake-up is second order at this state: both ρ_i* and Z_i* vanish.
Consequently no first-order feedback from dormant cells to active cells
exists. With the active coordinates first, each directional sector has the form

    [ A_sector       0       ]
    [ B_sector   −ε L_y I₂   ].

Changing ε changes only the two real bank-decay eigenvalues. It cannot move
an active complex pair across the imaginary axis. The full piecewise
variational equation has an ε-independent active subsystem as well, so this
is not merely a property of selecting one sector.

With the cubic ramp, entry and waking are second order in net growth. Its
ordinary Jacobian is the unchanged five-stock reference matrix plus the two
bank-decay modes. Thus a dormant pool can affect finite excursions without
being an added linear thermal-response state at this particular equilibrium.

The requested ε-driven local Hopf test is therefore inapplicable to the
existing linear ramp, and its proposed causal mechanism is refuted
analytically. Sector spectra below are diagnostics, not a certificate of
nonsmooth local stability. The recorded cubic paths do not establish a
limit cycle or a cycle bifurcation.

## Implementation and qualification

`dormancy_lag.py` computes all four linear-ramp entry sectors and the cubic
ordinary matrix at thirteen logarithmically spaced ε values from 10⁻⁴ to 10⁻¹,
with f=0, L=0.001/hour and κ=10. The reference ecological Jacobian and
net-growth gradients are finite differences in scaled physical coordinates;
the switching derivatives and triangular block structure are analytic.

Regression tests exercise the non-additivity of the linear directional
derivative, compare each sector against a one-sided derivative of the actual
physical RHS, check the triangular spectra, and recover the cubic reference
block. These tests do not silently replace the nonsmooth law with a smooth one.

The loss rate is converted to years before assigning a putative bank lag:
0.001/hour = 8.766/year, so τ=1/(ε L_y) is about 11.4 years at ε=.01.
It is not 1/(ε×0.001) years. Bank lifetime is a disappearance timescale;
the finite active–dormant cycling time also depends on κ, the growth path,
entry and wake-up, so equating the two is itself a diagnostic hypothesis.

## Reproduction and outputs

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache MPLCONFIGDIR=/tmp/terra-prisca-mpl \
  uv run python -m terra_prisca.haze_world.dormancy_lag
uv run pytest tests/test_dormancy_lag.py
```

Outputs are `figures/dynamic_realisation/dormancy_lag.csv`,
`dormancy_cycle_comparison.csv` and `dormancy_lag_manifest.json`.
The manifest pins model, data, specification and recorded-cycle inputs.
Cycle comparisons use each record's actual ε, L and switching factor, and
distinguish the two well-mixed cases from the warm-refuge example. The
recorded periods are finite-trajectory measurements, compared with a linear
thermal mode; matching periods would not prove a common mechanism.

## B4 result

The 65 matrix rows have no ε-driven complex-pair crossing. All four active
sector spectra remain independent of ε. The cubic reference pair has period
119.57 years and damping time about 4,854 years throughout this ε range;
the two added bank modes are real. Sector-by-sector decay does not by itself
certify the switching system's nonsmooth stability.

| Recorded cubic case | Bank lifetime, years | Recorded period, years | Thermal-mode period, years | Recorded/thermal | Within 30% |
|---|---:|---:|---:|---:|---|
| 0024, well mixed, ε=.003, L=.001/hour | 38.03 | 140.43 | 180.47 | 0.778 | yes |
| 0126, well mixed, ε=.001, L=.002/hour | 57.04 | 130.61 | 193.92 | 0.674 | no |
| 0012, warm refuge, ε=.03, L=.001/hour | 3.80 | 442.60 | 122.21 | 3.622 | unassessed: different habitat geometry |

The second well-mixed case misses the fixed 30% criterion: its recorded
period is 32.6% shorter than the thermal-mode period. Thus the matched-period
clause fails independently of the local-mechanism problem. Case 0012 remains
a visibly unmatched diagnostic and is not counted as a matched failure.
The thermal comparators at these bank lifetimes are unstable modes; a
linear mode's period is not an attracting thermal-cycle prediction.

PB7's proposed local ε-Hopf mechanism is refuted for the specified equations,
and its 30% period clause is refuted by the well-mixed higher-turnover case.
Neither statement denies the recorded finite recurrent paths or establishes
their alternative mechanism.
