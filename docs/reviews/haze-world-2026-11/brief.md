# External review brief: the haze-world model

*Written by Claude (Opus 5.5) for Barry W. Brook, 11 November 2026. Both
reviewers receive this brief unchanged.*

Thank you for taking this on. You are one of two independent reviewers. The
other reviewer is a model from a different developer, and neither of you
will see the other's report. Neither of you took part in building this work.
That independence is why we asked you, so please use it.

## Who we are and what this is

[Terra Prisca](../../vision.md) is an open research programme on why Earth
stayed habitable through the Precambrian and early Phanerozoic. It first
rebuilds classic Earth-system models faithfully, then extends them in
labelled variants. Barry W. Brook, an ecologist and modeller, facilitates and
reviews the work. Two AI systems built it:

- **Claude (Opus 5.5, Anthropic):** design, specifications, predictions
  and reviews.
- **Codex (GPT-6, OpenAI):** most of the implementation, experiments,
  archives and audits.

The two cross-checked each other throughout. The repository is public and
holds the full record, including our correspondence.

The work under review is **haze-world**. It is a new model, not a
reconstruction. It couples Archean microbial ecology to the methane–haze
climate response that Arney et al. (2016) published for 2.7 Ga. The work
falls into two parts:

- **Stages 1–2.** A single methanogen guild with a methane budget and an
  evolving thermal optimum.
- **Stage 3 onward.** Acetogens and hydrogenotrophic methanogens compete for
  hydrogen, using measured strain physiology. The stage 3 work then adds:
  - explicit population and methane coupling;
  - finite populations;
  - refuges;
  - demographic bottlenecks;
  - turnover;
  - dormancy;
  - competitive kinetic evolution.

The evidence is now ready for a paper, and Barry will lead the writing.
**Before we write, we want to know what is wrong, weak, overclaimed, missing
or misframed.** We also want to know what is genuinely new and worth telling.

## What we think we found

This is our current position. It is what you are reviewing, not a view to
adopt.

1. **A restoring thermostat.** On the haze-cooling branch of Arney's climate
   response, more methane makes the planet colder. Hydrogen competition there
   gives a restoring thermostat: acetogens win when it is cold and
   methanogens when it is warm.
2. **An ecological set point.** Cell turnover, not a tolerance limit, sets
   the temperature the thermostat holds.
3. **Exclusion outruns the climate.** A losing guild is excluded within
   years, but the climate responds over millennia. In finite populations an
   invasion can therefore eliminate a participant before the climate turns
   in its favour.
4. **Memory.** Temperature-buffered refuges, or dormant seed banks with
   half-lives near 1% of the unfavourable interval, can retain the losing
   guild. Short-lived, growth-triggered dormancy can make losses worse.
5. **A damped oscillation.** The thermostat is a weakly damped oscillator,
   with a period of about 120 years in model units.
6. **Partial evolutionary robustness.** Kinetic adaptation shifts the set
   point but keeps it at the reference turnover. Elsewhere it can remove it.
   The temperature dependences that the evolving trait cannot reach are what
   preserve it. The single-guild thermostat in stages 1–2 does not survive
   evolution.

Each result is conditional on the assumptions named in the estimands file.
We have already retracted or narrowed several claims; the ledger records
them.

## Snapshot and ground rules

- **Repository:** `https://github.com/BWBrook/terra_prisca`. Review tag
  `haze-world-review-1`:

  ```bash
  git clone https://github.com/BWBrook/terra_prisca.git
  cd terra_prisca
  git checkout haze-world-review-1
  ```

- **Read-only.** Do not push, open pull requests or issues, or comment on
  the repository. Within your local checkout you may run anything. Keep
  scratch code and outputs in an untracked folder or outside the checkout.
- **Environment.** Python with `uv`. `uv run pytest` runs the test suite
  (843 tests; allow several minutes).
- **What you can run.** Compact results (CSV and JSON), audit scripts and
  manifests are committed. About 2 GB of raw trajectories are not: they sit
  in an ignored `local/` directory, pinned by checksum. Some checks therefore
  cannot be rerun from raw data. Say so where that limits you. Do not run
  the long experiment producers unless a check really needs them. Short
  targeted recomputations are more valuable.
- **Independence.** Please form your own view before reading
  `docs/correspondence/`. It is the history of our reasoning, and reading it
  early will anchor you.
- **Sources.** Cite literature by DOI, with each DOI checked against its
  registered metadata. Mark anything you could not verify. Do not quote more
  than a sentence from any paper.
- **Publication.** Your report may be published in this repository with
  your model name, as part of an open record of human–AI research.

## Where to start

1. `models/haze_world/synthesis/synthesis.md`: the argument, with every
   result cited to a claim ID.
2. `models/haze_world/synthesis/claims.csv`: 37 claims. Each has evidence
   paths, a verifying commit, a reproduce command and a limit.
3. `models/haze_world/synthesis/estimands.md`: what each result may and may
   not claim. This is our own over-claiming guard, so test it too.
4. `models/haze_world/README.md`, then the stage pages it links in order.
   Each stage has a specification with predictions fixed before the runs,
   then results, then our review. Look especially at:
   - `population-coupling.md`;
   - `finite-populations.md`;
   - `buffered-refuges.md`;
   - `bottleneck-test.md`;
   - `turnover.md`;
   - `dormancy.md`;
   - `competitive-evolution.md`.
5. **Source handling:**
   - `models/haze_response/` (the Arney extraction);
   - `models/haze_world/evidence/` (physiology and loss evidence);
   - `docs/haze-world-groundwork.md`.
6. **Code:** `src/terra_prisca/haze_world/`. Of most interest are
   `population_coupling.py`, `two_guilds.py`, `habitat_coupling.py`,
   `branching.py`, `dormancy.py` and `evolved_kinetics.py`.

## What we would like from you, in priority order

1. **Is the science right?** Examine:
   - the model formulation and its units and budgets;
   - the quasi-static coupling to Arney's response, including our
     low-methane bridge and high-methane plateau;
   - the transfer of measured strain physiology to Archean habitats,
     especially the continuation below 4 °C;
   - the birth–death and branching treatment of survival;
   - the dormancy switching law;
   - the trait family in the evolution stage.

   Where a choice is defensible but arbitrary, say whether it drives a
   headline result.
2. **Do the claims follow from the evidence?** Choose the claims you think
   most fragile and try to reproduce or break them. Check that each claim's
   wording stays within its limit and its estimand. Note any claim we have
   understated, as well as any we have overstated.
3. **Novelty and significance.** Set the work against the relevant
   literature:
   - Daisyworld and Gaian regulation;
   - Archean haze and methane climate;
   - hydrogen thresholds and acetogen–methanogen competition;
   - resource-ratio (R*) competition theory;
   - microbial seed banks;
   - eco-evolutionary feedback on climate.

   What here is new, what is already known, and what have we missed that a
   referee would expect us to cite?
4. **The strongest objection.** What would a sceptical expert referee say
   first? Which single assumption is most likely to overturn the main
   conclusions if it is wrong? Which one additional analysis or source would
   most strengthen the work?
5. **The story.** Is our framing the most interesting and defensible one:
   an ecological set point, plus memory for recovery through displacement?
   Is there a better story in these results? Should it be one paper or two?
   What belongs in the main text and what in a supplement?
6. **Reproducibility and record.** Could a newcomer reproduce the main
   results from the repository? Is the claims ledger useful, or
   bureaucratic? Where is the documentation misleading, stale or
   inconsistent?

Be adversarial. We do not need praise, and "this holds up" is a useful
finding when you have tested it. Disagree with us wherever you think we are
wrong, including about this brief's own summary.

## Your report

Write one Markdown file. If you cannot write files, return it as your reply.
It should contain the following.

1. **Header:**
   - your model name and version;
   - the commit you reviewed;
   - roughly how long you spent;
   - what you ran.
2. **Verdict:** one paragraph. Is the work sound enough to write up, after
   which changes?
3. **Findings table**, most severe first, one row per finding:

   | Column | Content |
   |---|---|
   | ID | R1, R2, … |
   | Severity | critical, major, minor or suggestion |
   | Type | correctness, scope or overclaim, novelty, missing analysis, framing, reproducibility or documentation |
   | Claims | the affected claim IDs, or "general" |
   | Finding | one or two sentences |
   | Basis | **verified** (you ran or recomputed something; say what), **reasoned** (argument from the materials) or **suspected** (worth checking; not established) |
   | Remedy | what would fix it, and roughly how costly |

4. **Answers** to each of the six questions above. Keep them brief where the
   findings table already covers the point.
5. **Literature:** works we should engage, each with its DOI and whether you
   verified it.
6. **What would change your view:** for your two or three most important
   findings, the evidence that would show you were wrong.

Thank you. A clear, critical report from you now will save a far longer
argument with referees later.
