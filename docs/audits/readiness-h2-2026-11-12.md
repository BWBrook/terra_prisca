# Independent atmospheric-hydrogen check for readiness

Codex (GPT-6), 12 November 2026. Bounded independent check of C59 and X8;
no production source, original result or ledger row was changed.

**Disposition:** C59 can support closing X8 as a conditional open-boundary
diagnostic. The source replays all 28 committed rows exactly. Its 26 mixed
roots are accepted and in the declared temperature support; maximum actual
per-cell balance residual is 1.26e-11/year. The source selects mixed roots
without explicitly filtering their status, but that omission is not material
on this grid. It should not be assumed harmless for arbitrary future inputs.

## Independent fixed-chemistry balances

At a positive mixed equilibrium, each guild requires

    q_i = m_i + L/Y_i
    R*_A(T) = R*_M(T).

I solved the R-star equality directly from the strain functions, rather than
calling the production mixed-state constructor. The reference crossing is
281.534822805 K and its local hydrogen pressure is 22.486299981 Pa. The
cooling-branch climate segment then fixes methane ratio r. These quantities
contain no atmospheric hydrogen pressure.

Define c_i=q_i-a_i L, the catabolic uptake remaining after assimilation.
With the fixed reference recycling fraction f, the two steady budgets are

    q_A X_A + q_M X_M = J + k(P_atm-p*)
    (f c_A X_A + c_M X_M)/4
      = [loss(r)-abiotic]/[conversion * hours_per_year].

Solving these two linear equations reproduces every positive fixed-chemistry
mixture with maximum scaled state difference 1.57e-12. Setting X_M=0 gives
the positive reference branch's upper atmospheric pressure:

    P_atm,upper = p* + [q_A X_A,required - J]/k.

At f=.5 this is **157.3269654 Pa**. The algebraic continuation at 200 Pa
requires negative methanogen biomass, so the reported absence there is
supported by reference-branch feasibility, rather than merely a failed root
search. At f=0 the same balance has no finite upper-pressure boundary.
This does not certify absence of every conceivable other branch or model.

## Separate dynamic check

I assembled physical flows separately and used five-point finite differences
for the fixed-temperature stock Jacobian and the biological-temperature
column. At 100 Pa, the first critical lags are:

| Fixed chemistry | Independent lag, yr | Relative difference from C59 |
|---|---:|---:|
| f=0 | 0.1188438496 | -6.4e-10 |
| f=.5 | 1.1851463666 | -4.4e-11 |

The same independent matrices for products chemistry at both f values have
negative leading real parts at lags 0, 1, 100 and 10,000 years. These selected
checks agree with the reported finite-grid censoring, not a theorem of
stability for every lag.

## Wording limits

- Report the critical lags quantitatively. The f=0 change is small in years
  but about 20% relatively, so "barely" should not become "negligible".
- The atmospheric boundary imports hydrogen when P_atm exceeds the local
  pressure. At 200 Pa, the fixed reference receives 5.92e-7 mol/L/hour from
  that reservoir in addition to its nominal 1e-6 donor source. This is a
  prescribed external reservoir, not a photochemically closed atmosphere.
- The raw supply derivative varies the nominal donor input while holding
  atmospheric pressure fixed. A smaller product-chemistry derivative at high
  pressure should not be labelled stronger regulation without retaining that
  forcing definition and the changed operating point.
- No Archean atmospheric pressure, global hydrogen budget or universal
  robustness conclusion is calibrated by this sensitivity.

## Reproduction

```sh
uv run python models/haze_world/review/check_atmospheric_h2.py \
  --output /tmp/terra-C59-replayed.json
uv run python docs/audits/readiness-h2-2026-11-12.py
```

The companion JSON retains every root's status and balance checks, independent
fixed-state solutions, the boundary calculation, four dynamic comparisons
and source/input hashes. It preserves the source result unchanged.
