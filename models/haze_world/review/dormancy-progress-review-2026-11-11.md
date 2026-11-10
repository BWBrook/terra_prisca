# Native zero-time recovery: scoped qualification

Codex, 11 November 2026. The separately named helper is
[`dormancy_progress_integration.py`](../../../src/terra_prisca/haze_world/dormancy_progress_integration.py),
SHA256 `ee65a5d01009bb376146f64b883d3d6ec52670fb2bb2326bb2a4331e63d589a4`.
The [qualification manifest](dormancy-progress-qualification-2026-11-11.json)
records inputs, complete source hashes and raw/receipt identities.
**The 100,000-year case-0012 census endpoint remains pending.**

## What failed and what changes

The frozen `7046fc9b` helper failed on Linux at year 2,228.136 in
`dormancy_0012`: no acetate recycling, warm refuge, dormant-loss fraction
0.03, cell exchange `1e-6 /yr`, acetogens invading methanogens. A captured
state showed a populated dormant acetogen bank, not a globally extinct guild.
Both guilds remained present. A fresh solver at the same absolute time, with
unchanged stocks and charts, advanced another year successfully.

The native solver can report success without advancing time. Its returned
coordinates can nevertheless differ from the previously accepted coordinates.
The frozen driver treated that notification as an immediate error. The new
wrapper marks a **nonterminal** zero-time return as a failed numerical step.
The existing driver then rolls back to its saved accepted state, refines and
restarts. Terminal zero-time completion is unchanged.

The helper imports the frozen analytic-Jacobian implementation and substitutes
only its constructor through a private namespace. It changes no physical RHS,
stock, chart, tolerance or census rule. Events retain actual RHS/native times,
accepted and returned coordinate hashes, and the retry limit the unchanged
driver will choose. An unrepresentable retry is reported, not disguised by
inventing a trial time. Runtime errors retain their event records.

## Evidence that is complete

Seven focused tests pass. They cover ordinary bitwise flow and minima,
nonzero active-plus-dormant census removal and its inventory ledger, rollback
with both unchanged and changed native coordinates, restoration of the step
ceiling, terminal completion and truthful failed-refinement events.
Independent review of this same helper source found no consequential time or
state defect; six tests had been independently rerun at that checkpoint. The
additional changed-native-state control subsequently passed locally.

The uncensored 1,800-year case-0012 prefix completes in **40.97 seconds**. Its
first rare linear acetogen window closes at **1,254–1,456 years**, with its
minimum at year 1,363. Methanogens never become globally rare. A separate
1,600-year frozen-helper control is bitwise identical in sampled times,
physical stocks and guild/active/dormant logs through year 1,500, covering the
entire first window. The minimum expected acetogen count is about 13,700
(`log10 N = 4.13737534`); probability and count-scale interpretation belong to
the separately recorded first-window analysis.

| Profile | Fingerprint |
|---|---|
| Canonical progress-helper prefix, 1,800 yr | `7fe687cc871d854c5c338e9cc4dfce5a2ad38e3ff1f30bd43f2884f0846f4b4f` |
| Frozen-helper control, 1,600 yr | `45bbd395ab35fc9efa6e8d36df19d9ff7cb3629079d48007d3a0d8f04930a36e` |

The canonical prefix contains one actual zero-time recovery at
**1,785.5324977695 years**, after the first window has closed. Native and last
RHS times both equal the accepted time; native reported step size is zero.
The accepted coordinate hash is
`3e0ee6d8329aa09fa86d48221d13ac4660cea83e85baf2e206e12949cf6c4fbe`;
the discarded returned hash is
`2febc398845f01f8c28a892af89d12396ce369c280a6b89c5ad12c70c013bf47`.
The unchanged retry rule chooses **5 years**, which is representable. The
restart completes the prefix. This demonstrates why rollback is necessary;
the same-time native coordinate correction is not accepted as physical flow.
The frozen helper's attempted 1,800-year prefix fails at this edge and creates
no valid receipt. Both valid profiles above are retained.

## What remains unresolved

A formal Mac attempt at the full 100,000-year progress-helper census reached a
600-second wall guard without a result. It wrote **no valid census receipt**.
That controller did not retain traceback locals, so its accepted horizon is
unknown. Its diagnostic's empty event list came from a missing-attribute
fallback on `TimeoutError`; it does **not** prove that no zero-time events
occurred. The unchanged long attempt was not repeated on the Mac.

A first Linux run of the progress helper is continuing with a read-only
constructor observer, recorded controller hash and standard expected-source
checks. At this note's snapshot it had passed the former Linux failure and
reached confirmed entry time **2,730.011 years**, with one progress restart.
It has no arbitrary wall abort; negligible progress is paused for review.
Its final formal endpoint and receipt, rather than elapsed time or a passed
intermediate pole, are required for full-case qualification.

```sh
uv run pytest -q tests/test_dormancy_progress_integration.py
uv run python -m terra_prisca.haze_world.dormancy_progress_experiments \
  --mode uncensored --years 1800 --case-id dormancy_0012 --workers 1
uv run python -m terra_prisca.haze_world.dormancy_jacobian_experiments \
  --mode uncensored --years 1600 --case-id dormancy_0012 --workers 1
```

These checks qualify the closed first-window input and the demonstrated
progress recovery. They do not establish the long-run climate, census
endpoint or convergence of case 0012.
