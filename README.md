# Terra Prisca

> **Status:** developed in the open as a working record. This is work in progress: contents may change, and nothing here is peer-reviewed unless stated.

Why has Earth stayed habitable for about four billion years under a Sun that has
brightened by roughly 30%? Terra Prisca ("ancient Earth") explores that question
by reconstructing classic simulations of the Precambrian and early Phanerozoic
Earth system, scoring each against its published results, and then reimagining
them. The project is exploratory and grows as a tree of ideas; the aims, the
lineage of models and the agreed order of work are in
[`docs/vision.md`](docs/vision.md).

| Model | Status | Page |
|---|---|---|
| Daisyworld, Watson & Lovelock (1983) | Faithful reconstruction done and independently reviewed; agrees with published Figs 1b–d and 2 on occupied branches and transitions; the cause of a Fig. 1a discrepancy is unresolved | [`models/daisyworld`](models/daisyworld/README.md) |
| Archean haze-world (Daisyworld re-imagining) | Next | — |

## Getting started

```bash
uv sync
uv run pytest
uv run python -m terra_prisca.daisyworld.figures_1983
```

## Data

Small inputs and derived tables live beside each model under `models/`. Source
papers and other third-party material are not redistributed: they live in
`local/` (gitignored) and are cited by DOI, with checksums where a check depends
on a specific scan.

## How this work is done

Developed by Barry W. Brook with AI collaborators: Claude (Anthropic; Claude Opus
5.5 in Claude Code) and Codex (OpenAI). Barry sets direction and reviews; Claude
wrote the vision, the Daisyworld reconstruction, the fidelity check against the
digitised 1983 figures, and the tests. Codex (GPT-6) independently reviewed the
equations, solver and fidelity claims, added reproducible negative controls,
and researched the haze-world literature. See the
[review](models/daisyworld/review/2026-11-08.md) and
[haze-world groundwork](docs/haze-world-groundwork.md). Discussion among the
three takes place on a shared correspondence board,
published in `docs/correspondence/` as reviewed snapshots.

## Citation

See [`CITATION.cff`](CITATION.cff). Releases of paper-grade milestones carry a
Zenodo DOI.

## Licence

Code is released under the [MIT Licence](LICENSE). Text, figures and data created for this project are released under [CC BY-SA 4.0](LICENSE-CONTENT). Third-party material keeps its own terms where stated.
