# Applied Issue 4: Codex review

Codex (GPT-6), 16 November 2026. Reviews `1a2358c`, `624c9cf` and
`b0f113b` at `51b11e0`, following board posts 3501 and 3509. The open
main-message sentence is excluded from this review, as Barry requested.

**Decision:** the applied numerical results, sink budget and C67–C68 pass.
Make the short wording corrections below before closing the technical issue.
No new modelling, source search or numerical review cycle is needed.

## What passes

- The original parts, supply windows, state sweep and forcing arrays are
  exactly unchanged from `3628035`. Original sink fields agree within
  10⁻¹⁴; no physical model was retuned.
- All four new combined-export/feasibility rows independently recompute.
  The fixed export is correctly identified as 27.7262 Tmol
  CH₄-equivalent yr⁻¹, split between acetate and biomass. The 20.1875-Tmol
  acetate example is correctly tied to f = 0.5. The reference-supply
  feasibility limit is correctly stated.
- All seven finite temperature spans and the rounded S8c entries agree
  with the saved five supply positions. All twelve S8d entries reproduce.
  C67–C68's source script and JSON match stamped commit `1a2358c` byte for
  byte.
- Both existing independent bounded checks pass. Apart from the expected
  changed input hash, their numerical outputs are identical to the previous
  review receipts. This includes the narrow exact f = 1 state's stability
  at a 30-year response time.
- The full-product label, sampled nature of the range/tolerance relation,
  feasibility-versus-stability distinction for the imposed-warming windows,
  analytical-only biomass recycling, and loss of the exact plateau rather
  than every capture effect are now stated correctly.
- Four targeted paper/ESM/table/figure tests pass. The claims checker
  reports 68 claims, 37 cited, zero errors and 26 uncited-claim warnings.

## Corrections

1. **Make the iron comparison in equivalent units.** Draft §4.4,
   lines 523–526, compares 20 Tmol acetate yr⁻¹ directly with sulfate and
   iron recycling. Sulfate is one-for-one; Fe(III) is eight-for-one.
   The comparison becomes correct when that conversion is visible:

   > In the reference case at f = 0.5 the sink takes about 20 Tmol acetate
   > a year. Oxidising it would require about 20 Tmol sulfate or 160 Tmol
   > Fe(III) a year. These requirements exceed the published new-sulfate
   > and modelled iron-recycling fluxes, although neither budget caps gross
   > oxidant cycling.

   The existing “several times” iron comparison is justified for the
   **161.5-Tmol Fe(III) requirement**, which is 5.1–14.5 times the cited
   11.1–31.4-Tmol recycling scenarios. It is not a comparison of the
   20-Tmol acetate count with those iron counts. S8 already has the correct
   conversion; carry it into the main text.

2. **Reconcile the old and new stability statements.** The abstract,
   lines 26–28, places “two decades” immediately before “the 36 ... all ...
   seven years or less”. Identify the latter as the **original sampled
   inventory**, so readers do not mistake it for the enlarged f sweep.
   This is a scope qualification, not a change to either numerical result.

   ESM S8's coexistence-interval paragraph, line 351, still says “stability
   at f = 1 was not assessed here”, immediately before S8c assesses it.
   Replace that ending with: “The interval itself is a positivity
   condition; sampled stability margins are reported in table S8c.”

3. **Label the finite excursion's actual span.** S8c's header at ESM
   line 370 says “full-product excursion over window”. Use **“over 5–95%
   of the exact window”** in the header or caption and its generator in
   `esm_tables.py`. The numbers are finite sampled excursions, not the
   full boundary-to-boundary change. No new points are needed.

## Source wording

The closing sentence of the new §4.4 paragraph correctly leaves ancient
acetate recovery unresolved. Keep that scope throughout its opening:
**“acetate and dead biomass can return as methane”** is supported by the
cited model assumption and demonstrated pathway; “on an anoxic planet ...
tend to” suggests a general default that these sources do not establish.
The one-word qualification avoids reintroducing the withdrawn inference
about f through prose.

Also make explicit, in §4.4 or the conditions, that the oxidant comparison
does not close a planetary redox budget. A short sentence suffices:
**“Oxidant regeneration and any accompanying reductants would also have to
enter a planetary methane budget.”** This is the source-pass limitation
already recorded in the previous review, not a request to implement that
budget. A caveat about gross cycling alone addresses throughput, but does
not say whether regeneration returns reducing power to the methane system.

## Verification and hand-off

```sh
uv run python docs/audits/probe-issue4-budget-check-2026-11-16.py --output /tmp/terra-issue4-applied-budget.json
uv run python docs/audits/probe-issue4-dynamics-check-2026-11-16.py --output /tmp/terra-issue4-applied-dynamics.json
uv run pytest -q tests/test_paper_esm.py tests/test_paper_table_s1.py tests/test_paper_transient_figures.py
uv run python tools/claims.py check models/haze_world/synthesis/claims.csv models/haze_world/paper/03c-full-draft.md models/haze_world/paper/esm/esm.md
```

No manuscript, main-message record, model, ledger or original evidence
receipt was edited. Claude can apply these wording corrections and close
Issue 4's technical review without further numerical work. The first
main-message sentence remains open for Barry and Fable.
