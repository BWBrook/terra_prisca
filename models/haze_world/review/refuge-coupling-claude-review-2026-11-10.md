# Review: two habitats under one methane atmosphere

Claude (Opus 5.5), 10 November 2026. Review of Codex's refuge build
(`99a5146` to `d76a39c`, [refuge-coupling.md](../refuge-coupling.md)). The new
check is [refuge_path_criterion.py](refuge_path_criterion.py)
([output](refuge_path_criterion.json)). It reads the published
`selected_main.csv` and `selected_subsets.csv` and no raw data.

**Verdict.** I accept the build, the reporting and Codex's verdicts on P1 to P5,
with one restatement of P1 and one acknowledged error in P5. The domain failures
are a property of the habitat-temperature mapping I specified, not of the biology
or of Codex's implementation. The design that answers the two-way question
within supported physiology is in [buffered-refuge-spec.md](../buffered-refuge-spec.md).

## 1. P1 failed because I used the start temperature, not the path extreme

Climate response to rising methane is not monotonic. Arney's curve rises from
283 K at low methane to a greenhouse peak of **297.00 K** (r = 0.167) before
haze cools it to the 273.4 K plateau. Every methanogen invasion of an
acetogen world crosses that peak. My threshold for that direction used the
starting temperature (294.4 K at `f=0.5`). The path requires a cold patch below
the switch at 297.0 K, which means an offset above 15.5 K, not 12.87 K.

Restated with the path extreme: a refuge protects only if it stays on the
loser's side of the switch along the whole recorded path. That means the cold
patch's path maximum is below T_sw, or the warm patch's path minimum is above
it. Applied to all 148 supported runs with nonzero contrast:

| Direction | Protected along path | Unprotected |
|---|---|---|
| M into A | 19 survived, **0 lost** | 88 lost, 8 survived |
| A into M | 27 survived, **0 lost** | 2 lost, 4 survived |

Protection along the whole path is therefore **sufficient in 46 of 46 runs**.
`main_0267` (cold offset 13.5 K) is lost at the peak, as Codex found. The same
geometry at 20 K (offset 18 K, `main_0273` and `main_0275`) keeps acetogens at
about 10²⁵ cells until the cold patch reaches the 273 K support floor at year
6,538.

Path protection is not necessary. The twelve unprotected survivors are of two
kinds:

- **Four near-switch runs** (A into M at 8.4 K). The warm patch sits 0.099 K
  below the switch, and the exclusion rate there scales with that gap. The
  integrated decline stays far above one cell while the climate moves in the
  methanogens' favour. The right criterion is integrated growth,
  ∫λ dt > −ln(N₀/N_min), which reduces to the timescale ratio Pi of my
  previous review. My threshold statement conflated instantaneous protection
  with survival.
- **Eight zero-exchange runs** (M into A, `d=0`). In each, the invader was
  culled in the cold patch early and could never return. These are the
  census-isolated partitions Codex identified: stationary under the census,
  invadable in the continuum (+7.14 yr⁻¹ at 5 K). I agree they should not count
  as rescue. Future grids should keep `d=0` only as a control.

## 2. P2 cannot be tested with climate-tracking offsets inside supported physiology

This is a geometric result, not a gap in the search.

- **A into M has no supported start at any nonzero contrast** (60 of 60
  configurations at each `f`). The methanogen-only world is at 273.5 K. The
  area-mean constraint means any warm refuge cools the bulk below the 273 K
  continuation floor. Only the supplemental 5% warm refuges, with a 0.4 K bulk
  shift, stay above it.
- **M into A must clear the 297 K peak.** That needs a cold offset above
  15.5 K. When the haze later cools the planet toward the mixture near 282 K,
  that same offset puts the refuge near 266 K. That is below anything the model
  defines.

With refuge temperatures tied to the global mean by constant offsets, no single
geometry can protect both guilds in both directions without leaving 273 to
303 K. Real refuges need not track the mean. Hydrothermal mixing zones are set by
fluid mixing. Deep or ice-covered water is held near its freezing point or its
density maximum. Both are buffered against surface climate. Fixing refuge
temperatures, while the bulk tracks Arney's curve with no offset, removes the
problem. The bulk then has exactly the single-habitat model's support, and the
refuges stay inside the measured window by construction.

## 3. Points accepted

- **P5 correction.** I wrote that fast exchange approaches a community "at the
  area-mean conditions". That is wrong: it averages local growth across distinct
  temperatures and resources. Codex's regression control shows the difference.
- **P3** is confirmed with a negligible climate effect (0.048 K). That is an
  ecological result, not a climatic one, and the page states it that way.
- **The rescue's global temperature** (281.95 K, with the cold habitat pinned
  near the switch rather than the global mean) supports P4's distinction
  between local and global pinning.
- **Numerical evidence.** I have not rerun trajectories. The 72 zero-contrast
  matches against the single-habitat controls, and the Radau prefix check, are
  adequate for these conclusions.

## 4. Correction to the page

The results table gives "P1 refuted as both necessary and sufficient". The
start-temperature version is refuted on both counts. The path-extreme version is
sufficient in every tested case and fails as a necessary condition only near the
switch and at zero exchange. I would add that sentence and a pointer to this
check.
