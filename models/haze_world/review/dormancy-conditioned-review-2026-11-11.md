# Tolerance-conditioned Radau: bounded numerical qualification

The new numerical variant removes the dominant cost at two recorded states of
case 0125 without changing its physical equations, returned float RHS, error
tolerances, census or native endpoint positivity checks. This is a bounded
qualification of a chart choice and approximate Newton matrix. Independent
review and the parent experiment's original-start and rare-population controls
remain separate gates.

The helper is
`src/terra_prisca/haze_world/dormancy_conditioned_integration.py`, SHA-256
`39024878c87ed3ddbd385bbe586e5e872f85855f30010aca0a502671e5b64bbe`.
The producer flag is `radau_dormancy_tolerance_conditioning`. Its exact numerical
source extension has 13 files: the previous Radau producer's 11, plus this helper
and its separately owned runner. The earlier Radau helper remains unchanged at
`09be346c90c0fcb65ed6409f2de47ea1e4d3e2d542f3d6291eb7ae85a0bf6d2b`.

The rule uses the frozen square-root coordinate absolute tolerance, 10⁻¹², and
the original experiment's 10-year maximum step. Its fixed allocation cap is
10⁻²⁴ and its fixed allocation-rate cap is 10⁻²⁵ per year. It makes three changes:

- The original promotion-age predicate gains one condition: the linear
  allocation must exceed 10⁻²⁴. The private AST transformation verifies that
  exactly one predicate changed and that removing that condition restores the
  original AST. A changed upstream block shape fails closed.
- A present square-root stage whose absolute coordinate is at most 10⁻¹²
  requests the existing typed chart conversion. The decision uses an immutable
  copy of the accepted pre-step state, before native construction or Jacobian
  work. The inherited converter checks decoded physical stocks and global-total
  coordinate bits, and records every conversion in its existing event ledger.
- In a Jacobian evaluation, a present **linear** allocation is eligible only
  when 0 ≤ h ≤ 10⁻²⁴ and the absolute value of its unchanged pure linear float
  rate is at most 10⁻²⁵ per year. The approximate Newton matrix then loses that
  row and column's offdiagonal couplings, retaining its own diagonal. The gate
  uses the frozen flux, growth, community mean and migration expression; it
  never calls the side-effectful coordinate derivative. The actual ODE retains
  every source and coupling.

The caps are fixed numerical constants. A later precision control's requested
maximum step does not redefine them. Native Newton's iteration budget stays six.

The 34 targeted tests pass in 2.49 seconds. They cover bitwise RHS and ordinary
Jacobian identity in one and three habitats, active/dormant chart maps across
habitats, all gate exclusions, the retained diagonal and unaffected matrix
entries, absence of derivative calls in the matrix gate, AST identity and drift
rejection, accepted versus trial state handling, inherited rejection of negative
native endpoints, census inventory accounting, and the distinction between an
absent guild and a physically underflowed guild with retained finite logarithms.
The test source is `tests/test_dormancy_conditioned_integration.py`, SHA-256
`dd66327057a308c3375f89d10dd2be8038a8e03740183c2c9d95ba9f146cb667`.

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache \
MPLCONFIGDIR=/tmp/terra-prisca-mpl \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
uv run pytest -q tests/test_dormancy_conditioned_integration.py
```

The final helper was replayed for 100 years from each pinned accepted state,
with the original 10-year, one-cell census and no initial recensus. Exact saved
allocation and chemical charts were retained. Both endpoints and accepted-step
counts are bitwise identical to the preceding scratch implementation of the same
rule. These are private absolute-clock diagnostic controls, not canonical
full-horizon producer receipts.

| Recorded state | Final-helper runtime | Accepted pieces | RHS calls | Jacobians | Positivity refinements |
|---|---:|---:|---:|---:|---:|
| 36,731.521829 yr | 0.268 s | 48 | 382 | 11 | 5 |
| 2,724.482692 yr | 0.167 s | 30 | 229 | 5 | 2 |

The first control's frozen predecessor took 14.94 seconds, 1,434 accepted pieces
and 39,695 RHS calls. Both final controls used one inherited certified dense
extension and encountered zero negative native endpoints and zero native
failures. Their wall times were measured concurrently and are not a controlled
benchmark; the accepted-work reductions supply the stronger comparison. The
live-state control has one accepted root-to-linear conversion, preserving
physical stocks, global guild logs and global-total coordinates bitwise, with
no retained stage log lost.

The matched first control has identical temperature, hydrogen pressure and
active acetogen biomass. Acetate differs by 2.17 × 10⁻¹⁹ M and atmospheric ratio
by 3.25 × 10⁻¹⁹. Its microscopic dormant acetogen stock differs by
3.86 × 10⁻³² gDW/L, or 36% relative. The live control is compared with its initial
state, rather than a matched unmodified 100-year continuation. These checks
therefore do not establish rare-lineage, extinction-probability or universal
solver accuracy. They establish finite, positive bounded flow and the removal
of a specific numerical cost at the two recorded states.

The [compact review receipt](dormancy-conditioned-review-2026-11-11.json) records
the complete source graphs, AST hashes, input/raw/control hashes, fixed protocol,
work counters, stock differences and stock-preserving conversion event. Inputs
and raw outputs are in the ignored `local/haze/dormancy_conditioned_review/`.
The ignored controller
`local/haze/dormancy_trial_review/production_conditioned0125_probe.py` can repeat
the saved or `--live` control with a fresh `--output-dir`; it refuses to overwrite
an existing receipt. No predecessor source or receipt was rewritten.
