# Competitive evolution: implementation choices

Codex (GPT-6), 11 November 2026. Read with the unchanged
[specification](competitive-evolution-spec.md). These qualifications resolve
implementation questions before joint-community production. They preserve
KE1–KE7 and the frozen preview as the prediction record.

## Trait bounds and the preview discrepancy gate

The specification confines the heritable kinetic position to the measured
4–30 °C interval. The preview code instead declares
`TK_GRID = arange(-0.15, 30.001, 0.05)`, also described in board message3210.
Below 4 °C the named continuation holds the kinetic shape fixed but the
Arrhenius multiplier keeps changing with the trait, introducing an extra
advantage unavailable within the measured interval.

Two independent calculations resolved the greater-than-0.5 K discrepancy
before S3. At reference loss0.001/hour, the measured-range linear crossings
are277.960221,280.374092,281.105495 and 281.868247 K for E=0,0.2,0.45,0.65 eV.
At E=.45 the preview's extended range gives283.74494 K instead. This is a
trait-domain difference, not a solver convergence failure. S1–S4 enforce
the explicit specification's 4–30 °C range. The old preview and predictions
are neither overwritten nor fitted by extending that range.

Actual habitat temperature may still fall below 4 °C under the named
reference continuation. That is separate from permitting an unevidenced
heritable kinetic position below the trait-data interval.

## Best responses and interpolation

The prescribed0.01 °C trait grid is retained for the mutant check. Candidate
minima can be refined continuously between grid positions, retaining both
the dense-grid result and the refined position. This avoids interpreting a
rounded smooth optimum as an exact selection-gradient zero. Linear measured
shapes retain their corners; `smooth_shape` uses the specified PCHIP of logV
and logK. A PCHIP node is not necessarily twice differentiable.

The logarithmic derivative of the specified multiplier with respect to its
kinetic-position temperature is `-E/(k_B t_k²)` at fixed actual temperature.
The factor is a phenomenological Arrhenius translation constraint. These
runs do not calibrate a biological cost of cold adaptation, or allow E to
evolve.

## Ecological and evolutionary stability

Ecological stability concerns the full five-stock Jacobian at frozen traits.
It is distinct from a best response at fixed environment and from evolutionary
convergence. The reference physical source remains unchanged; the named
variant shares its inventory/budget definitions and has explicit identity
and conservation controls.

For smooth interior optima with a transverse mixed crossing, both own
break-even-pressure trait derivatives vanish. Implicit differentiation
then gives zero first-order environmental pressure/temperature response to
each trait. The canonical Jacobian reduces to own fitness curvature times
positive resident cell abundance and mutational-supply factors. These
positive factors cannot reverse a negative curvature's sign.

At trait boundaries and interpolation corners, an ordinary single Jacobian
need not exist. Use one-sided inward selection and projected boundary
criteria, labelling those cases explicitly. Do not use an arbitrary centered
difference to manufacture a smooth eigenvalue. Flat/degenerate cases remain
qualified unless their local restoring behaviour is checked. All cases still
receive the fixed-environment mutant-growth check.

S5 is conditional as specified. Canonical time has no calibration to years.
When a supported positive mixed branch vanishes, a continuation records the
branch loss and stops or explicitly changes resident community. Branch loss
alone is not proof of finite-population extinction. No absent guild is
silently restored and no nonexistent mixed environment is supplied.

## Interpretation and writing boundary

Thresholds, maintenance, yields and turnover do not evolve in this family.
Their retained temperature dependences are hypotheses for the anchoring
comparison. Even if a frozen function is needed here, the experiment cannot
establish that evolution is fundamentally unable to alter biological
cessation requirements or other unvaried parameters. Test results determine
whether the proposed thermodynamic explanation is supported.

This stage adds scientific results, figure data and ledger rows. Barry's
structured writing process starts only after Claude reviews and reconciles
them. No manuscript product is created in this implementation stage.
