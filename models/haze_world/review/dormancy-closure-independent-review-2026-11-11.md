# Independent review of the dormancy closure checks

Codex, 11 November 2026. This bounded review inspected the new tail assessment
and cycle-control design without editing the frozen physical model, changing
the original 128 strict labels, or repeating the long trajectories. The final
tail reconciliation includes the retained-log source guard, recomputation of
stationary banks for archived resident roots and the conservative one-cell
floor in root-pair comparisons. Its 11 focused tests pass independently. All
counts and bank-error ranges below are unchanged by these repairs. The final
cycle consistency read covers the returned flows and distinguishes unsuccessful
attempts from completed integration.

The tail classification is scientifically sound at its stated scope. The
active and chemical stocks, total guild stocks, occupancy and climate retain
the original tolerances. The stricter affine-bank check tests whether the
resolved dormant trajectory is explained by coefficients frozen at a nearby
root. Its error normalization by the observed bank range prevents a changing
bank from passing solely because it contributes little total biomass. That
is a fair test for this stronger explanation. It is not a necessary test for
eventual convergence, and a failure does not demonstrate instability.

In the reviewed output all 41 candidates pass the macro criteria and nearby
root comparison, but none passes the bank forecast. Across their 82 failing
dormant stocks the largest forecast error is 0.124 to 44,875 times the
observed range, against the fixed 0.001 criterion. The appropriate result is
therefore **macro stationary with unresolved dormant banks**, not verified
linear decay. The 41 pairs with both macro states stationary, of which 25
agree, are finite endpoint comparisons. The original strict counts remain
19 pairs stationary and 10 agreeing.

I independently checked the bank matrix against the frozen physical RHS in
positive no-refuge and warm-refuge states. The largest absolute discrepancy
was 3.5e-18 gDW/L/year; weighted dormant migration balanced to 5.4e-28
gDW/L/year. The pressure, biomass, methane and time units in the diagnostic
normalizations are consistent with the physical model. The positive-state
RHS with the macro solver's trial extension equalled the original RHS
bitwise in both states.

The reduced LSODA cycle control uses those unchanged equations and rejects
negative accepted/sample stocks, rare global guilds and sampled local census
removal. These are sampled guards, not a positivity or domain certificate
between observations. Its supported use is a bounded macroscopic control;
the frozen positive-coordinate producer remains necessary through rare
population stages. The completed 1,000-year small-perturbation LSODA and
Radau controls have identical initial arrays and sample times. After checking
both raw hashes, I obtained maximum differences of 4.49e-13 in methane ratio,
7.29e-10 Pa hydrogen pressure, 1.09e-12 gDW/L active acetogens and 6.08e-13
gDW/L active methanogens. This is strong numerical agreement for that control.

Report amplitude and linear-law runs as decay or persistence over their
actual horizons. Neither sampled decay from eight selected perturbations nor
a finite-duration oscillation establishes the presence or absence of other
cycle basins. The Face-to-macro and positive-coordinate continuation controllers
are now retained with their initial states, handoff times and source hashes.
The linear resident roots are residual-qualified starts; their
nonsmooth conditional stability has not been established by the cubic helper.

The final cycle summary is consistent with its receipts and raw arrays. I
checked receipt identities, all 12 completed raw hashes, increasing saved
times and the reported start, end and completed duration. All eight fixed
30,000-year cubic perturbations decay: fitted periods are 119.542–119.568
years and damping times 4,853.85–4,874.81 years. Cases 0024, 0032 and 0126
have complete original-start linear controls from zero to 20,000 years with
decreasing late-window amplitudes. Case 0068 returns only zero to 2,000 years;
case 0012 returns no completed original-start flow. Both warm-refuge switch-only
attempts begin at the recorded cubic time 80,000 years and return no further
flow: start and end are both 80,000 years, and completed duration is zero.
Those attempts supply no 80,000-year linear-law trajectory. The matched
nonspatial controls support dependence on the switching law; the warm-refuge
linear-law outcomes remain unresolved. I accept those finite-record conclusions.

Reviewed final tail source snapshot:
`612e5c3042a9582ac846a4025ca49dde9f8991b0b0503897bd7671a71231203f`,
tail design `01b7a0c02d56b989a4cb2cbb11b9dd8e6af7b133105475ac87ff20bd88765a37`,
tail output `663a28ba05feaf5b05a96ef2bf5a6ca93f1e1187ed614cf55487db015cdeea65`,
and cycle module `c8d4ee0b14a7f4a2282bf6f2d46030420a98fb7b5f9aa5b44e16fe36ada08aca`.
The final cycle summary is
`69bba83c73a06db5b6c5f791d532dceac4a1bd6c9ff16457217137d93bc81cad`,
its analysis is `3599b49d2f79ad1814d043f5076d1b2a417278f43dbbc9dd54c566d789a22aeb`,
and its design is `928358c6893a92909f43775eb3c91f8636126e86efc5dcac2ed0a4967bdb3ea7`.
The matched control receipts are `amplitude_0_0.001_3face17ad935.json`
and `amplitude_0_0.001_8b0e817891b1.json` under the ignored
`local/haze/dormancy_cycle_closure/` directory.
