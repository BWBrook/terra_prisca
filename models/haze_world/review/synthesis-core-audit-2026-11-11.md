# Audit of the previously supported synthesis rows

Codex (GPT-6), 11 November 2026. The [checker](synthesis-core-audit-2026-11-11.py)
and [output](synthesis-core-audit-2026-11-11.json) add algebra, short scalar
controls, independent finite-difference spectra and frozen-table recounts.
They change no physical model or original result.

- **C16:** solving a time-varying scalar backward survival equation agrees
  with independent quadrature of the integrated identity to about 1e-12.
  The identity is exact for a single-type linear birth–death process with
  Poisson entry. Its scalar reduction is not an exact multitype theorem.
  The retained comparison is 105.6362656 versus 105.6467556 cells, a
  0.0099293% discrepancy in one recorded multitype bottleneck.
- **C17:** all four fast-switching epsilon brackets are resolved
  first-bottleneck crossings. Recomputing `ln(2)/(8.766 epsilon)` reproduces
  all eight half-life bounds. This verifies the conversion and selected
  brackets; the original rare-lineage source and count assumptions remain.
  It does not establish a common community endpoint.
- **C18:** recomputing the bracket/approximation ratios gives
  0.9919028–1.1666667. The assumed logarithmic population ratio 54.3492
  gives a half-life fraction 0.0127535857. This is an isolated-bank
  approximation with specified recovery, not a universal coefficient.
- **C19:** frozen first-bottleneck rows give acetogen log minima of
  −59.54897 versus −14.25233 at exchange10^-9/year, and −40.19012 versus
  −1.05593 at10^-6/year. These are continuum minima, not possible observed
  fractional-cell populations. The previously checked allocation identity
  is local; the extra loss need not change a finite outcome that was
  already very unlikely to survive.
- **C20:** independent centered physical Jacobians at two scales reproduce
  all four reference modes. At f=0,L=0.001/hour the period is119.56826yr,
  damping4853.910yr, and Q=127.5339 (about128; the earlier127 was a coarse
  approximation). The other three modes give periods111.44659,153.46004
  and136.42943yr. These are local model properties, not an empirical Earth
  timescale. Attribution of damping to a single parameter was not tested.
- **C24:** direct critical-branching arithmetic again gives extinction
  1.06488e-63 after one active interval and0.231194 after100, without a
  population reset. This is a counterexample to extrapolating a conditional
  one-cycle hazard; it is not a risk estimate for the coupled ecosystem.

The corrected claims remain supported at these scopes. Neither successful
software checks nor independent calculation supply independent empirical
validation of the climate or microbial inputs.

```sh
UV_CACHE_DIR=/tmp/terra-prisca-uv-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run python models/haze_world/review/synthesis-core-audit-2026-11-11.py
```
