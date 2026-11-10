# First-bottleneck threshold precision

Four no-refuge threshold settings were repeated with tenfold tighter
relative tolerance (`2e-9`) and a one-year maximum physical step. These are
separate uncensored numerical controls; they replace no selected trajectory.
All use the same cubic switching law, population scale, physical parameters
and chemical-Jacobian source. Their original first rare resident windows
are closed and remain inside the extracted Arney climate domain. The
microbial response still includes its named below-4 °C continuation where
needed.

The [read-only checker](dormancy_threshold_precision_check.py) verifies the
protocols, receipt and payload hashes, then recomputes all four survival
calculations from the saved profiles. It also doubles the rate-sampling
interval and halves the maximum step of the backward probability equation.
It starts no physical integrations.

| Displaced guild | Recycling | Dormant loss ratio | Original survival | Tighter physical control |
|---|---:|---:|---:|---:|
| Methanogens | 0 | 0.006 | 0.78694523 | 0.78694521 |
| Methanogens | 0.5 | 0.002499 | 0.46997191 | 0.46997135 |
| Acetogens | 0 | 0.00046 | 0.98188169 | 0.98188171 |
| Acetogens | 0.5 | 0.00082 | 0.98762493 | 0.98763890 |

The largest probability difference is `1.40e-5`. Doubling the rate spacing
changes log surviving-lineage intensity by at most `3.69e-4`; halving the
probability step changes it by at most `7.31e-8`. The largest common-time
temperature difference is `0.00020 K`. Window boundaries and sampled minimum
times agree in every pair. Full source graphs, global count differences and
the observed controller hash are in the
[evidence file](dormancy_threshold_precision_check.json).

In particular, the value below one half at `epsilon=0.002499` is resolved
under these numerical controls. This tests the literal `0.0025` lower edge
of the pre-run prediction at the default cell-count scale. It does not make
that approximate prediction a theorem or calibrate the count scale. Habitat
volume, cell mass, physiology and switching-law assumptions remain separate
uncertainties. These are conditional first-window probabilities, not the
probability of a mixed community reaching a long-term endpoint.

```sh
uv run python models/haze_world/review/dormancy_threshold_precision_check.py
```
