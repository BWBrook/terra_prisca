# [Worktree model/goldblatt-lenton-watson] Goldblatt, Lenton & Watson (2006): sources, fidelity targets, build and review

Board discussion 194, status open.

## Message 3756 · Claude@[host] (claude-opus-5-5) · note

Time: 2026-11-25T01:02:30.035202+00:00

Barry, in chat on 25 November 2026, quoted exactly: "Next: Goldblatt, Lenton & Watson (2006), on its own branch, to the same standard. Verify the citation through Crossref and tell me which PDFs you need. Keep the faithful build as printed, put departures in named readings, and end the page with what holds, what the source got wrong, and what stays open. Ask Gemini for a review before merge."

**Citation, verified through Crossref:** Goldblatt, C., Lenton, T. M. & Watson, A. J. (2006). Bistability of atmospheric oxygen and the Great Oxidation. *Nature* 443(7112), 683–686. doi:10.1038/nature05169. Crossref lists 30 references.

**Branch and code location:**
- Branch: `model/goldblatt-lenton-watson`, in its own worktree, cut from `main` at `f217e3c`.
- Model code: `src/terra_prisca/goldblatt_lenton_watson/`.
- Model page: `models/goldblatt_lenton_watson/`.

**Sources requested from Barry:** the article and its Supplementary Information. I'll name any further sources after reading the Methods and SI. The candidates from the reference list are:
- Catling et al. (2001) for hydrogen escape;
- Holland (2002) for the reductant flux;
- the Pavlov et al. photochemistry papers;
- Kharecha et al. (2005).

**Plan, under `docs/reconstruction-lessons.md`:**
- The faithful build follows the printed equations and parameters, with every interpretive choice recorded.
- Departures go in named readings.
- Each printed figure is digitised and scored with declared nulls.
- The page ends with what holds, what the source got wrong and what stays open.
- No coupling to other models.
- Codex reviews each stage. Gemini reviews before merge, at Barry's request.

The fidelity targets follow once the paper is in hand.

Next: Barry — supply the article and SI PDFs
