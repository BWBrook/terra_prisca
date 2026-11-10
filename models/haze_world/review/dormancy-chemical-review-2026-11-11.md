# Chemical Newton rows: prefix qualification

Codex, 11 November 2026. The named helper is
[`dormancy_chemical_integration.py`](../../../src/terra_prisca/haze_world/dormancy_chemical_integration.py),
SHA256 `75c538cb2bfabf0e8b497d6f7b60e8714ab2a69880d8836ec5201ac05b626cd1`.
The [verified snapshot](dormancy-chemical-qualification-2026-11-11.json)
qualifies the bounded controls, two uncensored prefixes and two completed
100,000-year census flows. The full census records both retain their strict
**unsettled** labels; numerical completion does not establish an equilibrium.

## The defect

A positive-chart active allocation can underflow to root zero while a real
dormant population remains. At a source-free zero root, chemical production
is proportional to `z²/(H_other + z²)`, whose root derivative is exactly zero.
The frozen `7046fc9b` matrix instead probes the smallest positive floating
root. Its retained producer log can be much larger than the acetate log, so
that probe creates an overflowing chemical rate or derivative.

The bounded counterexample has hydrogen pressure 21 Pa, a positive dormant
acetogen bank, active acetogen root zero and acetate log coordinate −3000.
The exact physical RHS is finite: active-stage rate zero, chemical rate −1.
The old matrix fails with a nonfinite matrix; the new chemical/root derivative
is zero and its matrix is finite. This explains the stalled methane-invasion
prefixes without changing their biology.

## Repair and limits

The helper replaces positive-chemical Newton rows with their allocation
algebra. Primitive coefficient and loss gradients remain numerical and reuse
the frozen matrix's flux probes. The own-active derivative uses `sum(other h)`
directly, avoiding cancellation when a sole allocation is a redundant gauge.
Other allocation rows retain the frozen analytic treatment.

Zero **linear** producers are different: their first derivative can genuinely
exceed floating range. That requests the existing accepted-state chemical
chart conversion, preserving the decoded amount and inventory bitwise. It
never substitutes zero or caps a derivative. A separate threshold-free hook
pairs a positive chemical chart with an exactly zero linear producer when
accepted migration or waking supplies it. The absolute-year-1000 control
with a positive `1e-100 mol/L` pool verifies that recovery; the source-free
control requests no unnecessary conversion.

Typed metadata distinguishes Newton conditioning from producer arrival,
records actual trial and accepted times where applicable, and binds the
accepted-state hash to the bitwise conversion. The helper reuses the frozen
`7046fc9b` accepted driver and `ee65a5d0` progress recovery in private namespaces.
Physical RHS, biological and census rules, solver tolerances and old source
files remain unchanged. Global guild logs remain available; existing stage
underflow and nonpropagated chemical-tail limitations still apply.

## Completed checks

All **15 focused tests pass**. They include the zero-root counterexample,
root/linear gauge invariance, genuine linear-zero overflow, cause-labelled
stock-preserving conversion, unequal habitats with and without dispersal,
mixed charts and total coordinates −50/0/15, independent physical-Radau flow,
redox/minimum checks, censuses and the arrival edge. An independent Codex
review of the same final source reran all 15 tests and found no consequential
issue in the mathematics or private-driver composition.

| Canonical uncensored prefix | End-to-end time | Accepted pieces | RHS evaluations |
|---|---:|---:|---:|
| `0025`: no refuge, M into A, epsilon 0.003; 3,000 yr | 6.71 s | 2,260 | 3,912 |
| `0041`: no refuge, M into A, epsilon 0.0003; 15,000 yr | 23.41 s | 10,343 | 15,830 |

Both have nonnegative stocks, finite present-guild logs, dense minima bounded
by samples, sampled redox residual at most `1.74e-18`, and zero recorded solver-failure retries,
positivity refinements or progress restarts. The old unfinished 3,000-year calculation had
not returned after about an hour; that is a stalled-work comparison, not a
controlled hardware speedup ratio.

Case 0041 also exercises genuine conditioning. Its own-root derivative has
log magnitude **727.829**, above floating range, at trial year 1,483.299. The
driver converts the saved accepted chemical chart at year **1,475.695** with
all decoded stocks and inventory unchanged. This event is labelled as a
Newton request and applied conversion. It is not silently discarded.

The canonical fingerprints are:

- `0025`: `1fc0915fecdc3ba79b632755dea21ad8383c6b47e06e49328205d863665e3842`
- `0041`: `13bd6b59e5767b9ca64f40bc7080e7a8929394214632fd117a2e487459e0227d`

The JSON retains complete source, receipt, payload, observer and execution
hashes. These prefixes supply numerical inputs to the first-window analysis;
they do not by themselves determine finite-population survival probabilities
or long-run climate outcomes.

## Completed full-flow controls

| Case and platform | Wall time | Accepted pieces | Strict settling status |
|---|---:|---:|---|
| 0012, Mac; warm refuge, exchange `1e-6/yr` | 4,155 s | 1,257,989 | unsettled |
| 0010, Linux; warm refuge, exchange `1e-9/yr` | 250 s | 20,806 | unsettled |

Both use epsilon 0.03, no acetate recycling and acetogens invading methanogens.
Their receipts and payload hashes verify against the unchanged chemical source
graph. Both have finite nonnegative sampled physical stocks, dense minima
bounded by samples, sampled redox residual below `1e-16` and bitwise stock and
inventory preservation at every recorded chemical conversion. The JSON keeps
compact event counts and archive hashes rather than copying the large event
histories into the repository.

Case 0012 completes all 100,000 years. Its climate is **281.744 K** at the end,
but its last 20,000 years span **1.482 K**, with 90 changes in census occupancy.
Both guilds remain represented, with ongoing loss and re-establishment of
local warm-refuge acetogens. The run records 1,301 such culls, 1,773 chemical
chart conversions, 18 failed-step retries and four native zero-time recoveries.
These observations qualify full numerical flow and preserve a materially
unsettled ecological state; they do not support calling that endpoint a
stable mixed equilibrium.

The independent Linux case 0010 ends at **273.484171207 K**, with only
methanogens present. Its final stocks differ from the previously selected
`7046fc9b` Mac case by at most `1.28e-10` in absolute model units, and the
maximum shared-time temperature difference is `1.43e-6 K`. The strict
all-stock label differs despite this close physical agreement, so both labels
and source epochs are retained. The Linux control does not replace the
historically selected Mac receipt.

Completed census fingerprints:

- 0012 Mac: `14f5c49a3088e852d97f80363fccb5c42ba6988ea03778e4ebf7c140c0430d2a`
- 0010 Linux: `02158faa467fa03b43b8361b339e0d35a15e23982c22da44373746160eef71ed`

These controls establish neither completion of the remaining experimental grid
nor convergence of the nonstationary cases. The earlier source epochs and
valid completed records remain intact.

```sh
uv run pytest -q tests/test_dormancy_chemical_integration.py
uv run python models/haze_world/review/dormancy_chemical_qualification_check.py
```

The checker verifies the two prefix receipts, both completed full-flow receipts,
payloads and available recorded execution sidecars. It also compares the separate
Linux case 0010 with the retained selected Mac record and reruns only the
bounded synthetic counterexample. It
starts no new trajectories. New trajectories use
`python -m terra_prisca.haze_world.dormancy_chemical_experiments`; their protocol
fingerprints record platform and numerical provenance separately.
