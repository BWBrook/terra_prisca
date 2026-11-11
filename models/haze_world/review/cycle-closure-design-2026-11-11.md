# Dormancy cycle closure: fixed design

This closes the two cycle checks in Claude's review §7. The existing physical
and numerical producer modules, earlier raw outputs and receipts remain frozen.
The initial machine-readable design is
`local/haze/dormancy_cycle_closure/plan.json`; this note records the bounded
execution choice agreed with the parent before the remaining linear controls.

1. At the recorded mixed root for case 0024, set both dormant pools to exactly
   zero. Perturb only one active guild at a time by −0.1%, +0.1%, −10% and +10%:
   eight fixed starts, each followed for 30,000 yr. Compare the decaying mode with
   the recorded 119.6 yr period and 4,854 yr damping time. These amplitudes stay fixed
   even if every start decays; no search for a start that cycles is planned.
2. Replace the cubic response only by the existing named linear response for
   cases 0024, 0032, 0126, 0012 and 0068. Retain each original invasion dose and
   resident branch, recovering the linear resident as a residual-qualified root.
   Its nonsmooth stability status remains unqualified. Follow the original start
   with the frozen positive-coordinate Face producer for 2,000 yr, then restart the
   same autonomous physical RHS at that accepted census time for 18,000 yr using
   guarded, reduced-stock SciPy LSODA. Thus the planned matched horizon is 20,000 yr,
   replacing the provisional 100,000 yr target because the positive-coordinate
   startup costs about 55 s per 2,000 yr. Report actual shorter horizons on failure.
3. If useful for distinguishing restoration from instability, screen the linear
   case 0024 mixed root with the same four small physical directions (±0.1% per
   active guild), exact-zero dormant stocks, and 20,000 yr. This supplies directional
   evidence rather than a stability certificate from one arbitrary Jacobian.

The reduced physical integration is restricted to macroscopic guilds. It rejects
any negative/nonfinite accepted endpoint or midpoint, a supported-domain failure,
any global guild below 10¹⁶ cells, and any required one-cell census removal.
It neither clips stocks nor changes physical tolerances, extinction or switching.
The original-start linear direct-stock smoke failed at 3.50 yr and is retained.
Three direct-stock amplitude trials also rejected negative dormant numerical
stocks; these use the frozen positive-coordinate Radau producer unchanged.
No failed receipt is overwritten. The positive-coordinate startup and each
continuation retain separate source and raw hashes, solver settings and horizons.

The cubic one-thousand-year smoke agrees between the guarded physical solver and
frozen Radau at common 10 yr samples (methane-ratio difference below 4.5×10⁻¹³).
The guarded solver's checks are sampled restrictions rather than a whole-piece
positivity certificate. No rare-lineage, basin, Floquet or global periodic-orbit
proof is sought. Final interpretation will distinguish decay, persistent
bounded recurrence and unresolved controls.

At most four local workers run concurrently, with BLAS restricted to one thread.
No remote resource changes or new numerical qualification layer are planned.
