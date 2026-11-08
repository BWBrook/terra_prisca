# Terra Prisca: agent guide

Reconstructions and re-imaginings of simulations of the Precambrian and early
Phanerozoic Earth system, developed in the open by Barry W. Brook, Claude and
Codex. Read [`docs/vision.md`](docs/vision.md) first: it holds the aims, the
lineage of models and the agreed order of work.

## Conventions

- Python with `uv`. Run tests with `uv run pytest`. Regenerate a model's
  figures with its module's `__main__` (see the model page under `models/`).
- Model code lives in `src/terra_prisca/<model>/`; each model family's
  human-facing page (source, equations, interpretive choices, fidelity report,
  figures) lives in `models/<model>/README.md`.
- A faithful reconstruction stays faithful. Departures from a source go in
  clearly named variants, never as silent edits to the faithful version.
- Record every interpretive choice the source leaves open, with the reason.
- Source PDFs and other third-party material stay in `local/` (gitignored).
  Cite by DOI.
- Coordination and review happen on the correspondence board (project
  `terra-prisca`); accepted decisions are recorded in the repository.
