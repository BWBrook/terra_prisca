# Lessons for reconstruction pairs

Written by the Budyko–Sellers pair (Claude Opus 5.5 and Codex GPT-6, November
2026) for the next pair to build a base model from [`vision.md`](vision.md).
The standard is set by [`models/daisyworld`](../models/daisyworld/README.md) and
[`models/budyko_sellers`](../models/budyko_sellers/README.md). Read one of them
end to end before you start.

## Sources and licences

- Verify every source against its registered metadata (Crossref, DataCite)
  before use. Some papers carry two DOIs. Budyko (1969) has one at Tellus A and
  one at Wiley, so record both.
- Read the licence on the publisher's article page. Crossref often has no
  licence field. Budyko's Tellus A page states CC BY 4.0, so its scan may appear
  in an overlay. Sellers' AMS scan is copyrighted: it stays in `local/`, and its
  overlay plots only digitised values, never the scan itself. Link the licence
  and the page it was read from on the model page.
- Record each source PDF's SHA-256 and the `local/sources/<model>/` path the
  scripts expect, so anyone holding the same file can rerun the scores.
- If a publisher blocks automated download, ask Barry for the file. Do not work
  around the block.

## Digitising traps

- **Traces jump between curves** wherever curves cross or run close. In Sellers'
  Fig. 7, curve g, traced from its end, ran onto curve a, and h ran onto f.
  Seed each trace on a feature only that curve has, such as a crest. Then test
  that the trace stays on its own curve where its neighbours are close:
  [`test_fidelity_against_scan`](../tests/test_sellers1969.py).
- **Dashed curves need explicit gap handling.**
  [`track`](../src/terra_prisca/budyko_sellers/digitise.py) can bridge the gaps,
  but it can switch onto a neighbouring solid curve. Sellers' curve h kept its
  identity when its isolated dashes were selected by size and elongation, with
  reference lines and labels excluded:
  [`dash_pixels`](../src/terra_prisca/budyko_sellers/scan_sellers1969.py),
  `DASHES`.
- **Tick labels, minus signs and curve labels** join traces that pass near
  them. Mask them, and assert that they are masked:
  [`scan_budyko1969.py`](../src/terra_prisca/budyko_sellers/scan_budyko1969.py)
  `drop`, and the φ₀ label check in
  [`test_fidelity_against_scan`](../tests/test_budyko1969.py).
- **Lines drawn through plotted symbols** pick up the symbols' ink. Exclude each
  whole symbol and the area around it before interpolating the rest of the
  line:
  [`observed_at`](../src/terra_prisca/budyko_sellers/fidelity_sellers1969.py).
- Check every trace by eye on a native-resolution overlay before scoring it.
  An RMSE cannot show that a trace is on the wrong curve.

## Scoring rules

- Score each printed curve two ways. The column error is in data units
  ([`column_median`](../src/terra_prisca/budyko_sellers/digitise.py)). The
  two-way pixel distance is [`chamfer`](../src/terra_prisca/budyko_sellers/digitise.py).
- Never score a model curve beyond the range it was computed over. `np.interp`
  extends a curve silently by repeating its end values. Count the columns a
  curve doesn't cover, leave them out, and score competing readings on the same
  columns: [`column_errors` and `score`](../src/terra_prisca/budyko_sellers/fidelity_budyko1969.py),
  [`test_no_equilibrium_is_invented_off_the_branch`](../tests/test_budyko1969.py).
  A solver asked for an equilibrium off its branch returns NaN, not the
  branch's end value.
- Declare in advance the controls relevant to each experiment: no feedback, no
  transport, no change or fixed albedo, and **the calibration target offered as
  the solution**. Report ties and failures as they fall; never tune the score
  to force a rejection. Sellers' observed temperatures tie with the
  reconstruction. The present-state fit therefore shows agreement but cannot
  distinguish the model from its calibration target. The transports and the
  perturbation experiments discriminate more strongly.
- State fit in measured numbers (RMSE, maximum error, columns used), never as
  "within the line width".
- Outputs are byte-reproducible CSVs with LF line endings. The reviewer
  regenerates them and compares them byte for byte.

## Choosing between readings the source leaves open

- Let the source's own derivation decide first. Budyko derives his global
  equation from zero net transport for the Earth as a whole, which holds only
  with an insolation-weighted planetary albedo. That reading stands even though
  another reading fits two curves better:
  [`test_faithful_transport_sums_to_zero`](../tests/test_budyko1969.py).
- Let the fit decide only what the text leaves genuinely open, and say when it
  did. Test coupled choices together: Budyko's 30-day month and
  insolation-weighted albedo were misleading when varied one at a time. The
  joint comparison is in
  [`budyko1969_readings.csv`](../models/budyko_sellers/fidelity/budyko1969_readings.csv).
- Keep every rejected reading as a scored row next to the faithful one
  (`READINGS` in each fidelity module). Give each its own line in the choices
  table, with the reason. The table should show where an alternative does
  better.
- Check every conservation law the source implies, and turn each check into a
  test.

## What cross-review caught, and what to check first

Codex's review of the first build (board thread 167, BS-R1 to R10) found these.
Check them before asking for review.

1. Each trace is on its own curve (R1).
2. The global balance closes under the faithful reading (R2).
3. At a discontinuity, use the value the source specifies at the boundary,
   separately from either side. Check the public profile at its solved
   boundary against the defining equation:
   [`test_ice_edge_holds_boundary_temperature`](../tests/test_budyko1969.py).
   Check the root's residual; neither grid interpolation nor a converged solver
   guarantees the right boundary value (R3). Budyko's edge temperature was
   5 °C out because albedo 0.62 was used at the boundary instead of 0.50.
4. Every threshold or constant you supply is recorded as an interpretive
   choice, with scored alternatives (R4).
5. Search for further equilibria from different starts and along different
   continuation paths. Report the roots found as found; do not imply the count
   is exhaustive unless that is established. State the heat-capacity
   assumptions behind any stability result, and keep local stability separate
   from claims about where trajectories end or which basins they fall in:
   [`growth_rates`](../src/terra_prisca/budyko_sellers/sellers1969.py),
   [`test_curve_i_has_three_equilibria`](../tests/test_sellers1969.py) (R5).
6. A law re-anchored to today can behave differently on the side the source
   never ran. Restrict the reported reconstruction to the side the source
   computed, and say that the direct solver still permits the other side (R6).
7. Before calling a source inconsistent, compare like with like: belt centres
   against endpoints, and rounded prose against the figure (R7, R8).
8. Every control promised on the board is in the table (R9).
9. Scores never clamp a curve beyond its computed range (follow-up to R4).
