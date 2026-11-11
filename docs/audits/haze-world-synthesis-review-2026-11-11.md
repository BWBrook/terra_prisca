# Haze-world synthesis: independent claims and interpretation review

Codex (GPT-6), 11 November 2026. Review of Claude's synthesis at `0ee03ed`
and checkout `6042391`. All eighteen provisional rows were checked against
specific source tables, raw records or separate calculations. All support a
**qualified** statement after the repairs below. Together with the six
previously supported rows, the ledger now has twenty-four supported claims,
three refuted claims and one superseded claim. Support refers to the stated
model, inputs and analysis; it is not independent empirical validation.

## Findings and dispositions

| Finding | Independent check | Disposition | Owner |
|---|---|---|---|
| Thesis: every competitive thermostat needs a memory | Reconstructed stable, abundant unrefuged mixed equilibrium and its five-stock spectra | Restrict to retention/recovery through the studied destructive invasions; add E12. No universal necessity or sufficiency theorem. | Codex |
| C01: pooled result labelled case B only | Independent scalar roots from A–D climate and atmosphere inputs | Correct scope to 78 pooled rows, only 18 B; retain approximate cold-edge offsets. | Codex |
| C02: evolution erases regulation stated without structural qualifications | Separate selection gradient and constant-capture balance | Restrict to feasible interior fixed-peak unconstrained optimum family. | Codex |
| C03: floor described as the only restoration mechanism | Independent floor roots/derivatives and H recount | Retain F thresholds; include the growth-rate trade-off's shallow-loss buffering. | Codex |
| C04: methanogens generally die at the peak | Full zero-mutation U subset and independent viable-supply minima | Restrict to eighteen fixed-optimum controls; deaths occur during warming toward the peak. | Codex |
| C05: feedback sign conflated with stability | Independent pressure crossings and climate slopes | Support restoring sign conditional on reduced methane routing; do not infer full stability from sign. | Codex |
| C06: warmer mixture versus control | Independent resource/methane allocation balance and two five-point derivative scales | Support conditional contrast and local stability; controls disable acetogens, not full-community bistability. | Codex |
| C07: invasion history generalized over recycling and initial states | Endpoint recount plus checksum-pinned focal trajectory | Restrict to closed f=0/0.5 starts; pin the 20-year example to f=0.5. | Codex |
| C08: every climate-tracking refuge fails | Recount includes nine matching f=0.9 coexisting pairs | Replace by domain limitation of the tested lower-recycling mean-preserving geometry; retain counterexamples. | Codex |
| C09: all192 outcomes described as one mixed state | Full inventory and six key opposite-history pairs compared stock by stock | Twelve key runs support matching mixtures; the full inventory includes 69 single-guild endpoints. | Codex |
| C10: exchange threshold treated like a counterfactual census experiment | Independent fit/interpolation and threshold recount | Support the specified first-window cut; distinguish posthoc global count crossing from rerunning local censuses. | Codex |
| C11: global minimum described as inside the refuge | Independent grouped global minimum | Preserve numeric refutation; locate it in a run with 0.5% refuge area, not in the refuge itself. | Codex |
| C12: branch limits confused with sampled range or physiological independence | Independent break-even root and full inventory recount | Name branch limits separately from grid extrema; turnover acts under fixed transferred physiology. | Codex |
| C13: bistability asserted at every higher turnover | Separate onset root and higher-loss monostable counterexamples | Give bounded mixed/acetogen and pure-guild intervals, excluding marginal endpoints. | Codex |
| C14: 0.28K called an extension of the temperature window | Recomputed fixed-refuge-flux forcing and actual endpoint | Label as establishment diagnostic above the switch; actual mixture remains pinned and diagnostic uses bridge. | Codex |
| C15: immigrant-supported sink said to have no climate effect | Recomputed catabolic shares and local growth | Separate negligible bulk participation from methane forcing; revise E10. | Codex |
| C21: cycling beside stable root | SHA-checked raw ranges and independent two-scale spectra | Support finite recurrence; distinguish the spatial census hybrid from unculled paths. | Codex |
| C22: linear-law controls | Independent final-window recount and actual-clock checks | Three controls damp over20kyr; two remain unresolved. Timeouts supply no biological outcome. | Codex |
| C23: bank partition | Independent weighted-symmetric bank propagation, rather than original augmented exponential | Confirm56/41/31/0 and all failed frozen-root forecasts; retain original strict flags. | Codex |
| C16–C20,C24: already supported rows | Scalar backward ODE/quadrature, half-life and ratio algebra, table minima, independent physical Jacobians and branching counterexample | Retain support with explicit single-type, first-window and local-model limits. Q at f=0 rounds to about128. | Codex |
| Evolutionary hypothesis assumes the crossing survives | A crossing can move out of the supported branch or disappear as physiology changes | Leave preservation and loss as competing, untested hypotheses. | Codex |
| Claims checker crashes on extreme evidence exponents and accepts numeric identifier prefixes | Regression controls for identifier boundaries, extreme exponents and scientific-display precision | Repair repository copy; five tests pass. | Codex |

## Evidence and reproduction

The bounded audit reports and their runnable checkers retain exact selectors,
input/raw checksums, values and source identities:

- [Single-guild precursors](../../models/haze_world/review/synthesis-precursors-audit-2026-11-11.md): C01–C04.
- [Community coupling and refuges](../../models/haze_world/review/synthesis-communities-audit-2026-11-11.md): C05–C11 and the memory counterexample.
- [Turnover and dormancy](../../models/haze_world/review/synthesis-turnover-audit-2026-11-11.md): C12–C15,C21–C23.
- [Core algebra and modes](../../models/haze_world/review/synthesis-core-audit-2026-11-11.md): C16–C20,C24.

No original physical source, trajectory, classifier, extinction rule or
probability was changed. The new checkers add no long trajectories or raw
arrays. Their raw dependencies already belong to the accepted payloads.
Ledger evidence now names specific CSV/JSON outputs and independent audit
records rather than relying on model-page summaries. Verification stamps
refer to committed evidence, with reproduction commands for the new checks.

Run the four `synthesis-*-audit-2026-11-11.py` files with project `uv`, then:

```sh
uv run pytest tests/test_claims_checker.py -q
python3 tools/claims.py check models/haze_world/synthesis/claims.csv models/haze_world/synthesis/synthesis.md
```

The edits touch interpretation, the ledger, the synthesis, standalone audit
code and the numeric checker. Physical-model tests were not rerun: no model
code changed. Claude reconciles the revised synthesis before paper products.
The two unresolved warm-refuge linear-law checks remain deferred, since the
qualified claims do not depend on their outcome.

## Tool follow-up

The living-paper skill recommends fixing general checker bugs in its source
before updating vendored copies. Barry's instruction against unsolicited
personal-skill changes takes precedence here. The necessary repair is local
to `tools/claims.py`; an upstream skill update is an explicit follow-up,
not a completed task or an additional gate on this audit. Numeric checking
still cannot certify the meaning of a sentence; the semantic corrections
above are the reason for independent review.
