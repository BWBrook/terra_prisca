# PNAS format notes for the haze-world paper

Claude (Opus 5.5) and a Claude Sonnet 5.5 subagent, 12 November 2026.
PNAS is the agreed first target (Barry, 12 November 2026). These notes cover
form only. Barry leads the writing process; nothing here is a draft.

## Rules (unverified against pnas.org)

pnas.org returned a bot-verification page to both the subagent and Claude's
browser, so these come from the PNAS Overleaf template and a third-party
summary. **Check them on pnas.org before drafting to length.**

- **Article type.** A Research Article (Direct Submission). A Brief Report,
  at about 1,600 words, is too small for our results.
- **Length.** About 6 journal pages is preferred, 12 at most. Six pages is
  roughly 4,000 words, 4 medium display items and 50 references.
- **Abstract.** At most 250 words.
- **Significance Statement.** 50–120 words, written for scientists outside
  the field.
- **Title.** Under 135 characters, with no acronyms.
- **Sections.** No Introduction heading. Then Results, Discussion, and
  Materials and Methods.
- **Self-contained main text.** The main file must stand alone. The SI is
  one unedited PDF.
- **Code and data.** They must be public, with a "Data, Materials, and
  Software Availability" statement and the archive cited in the references.
- **To check:**
  - PNAS's policy on disclosing AI use, which matters for our full
    statement of AI roles;
  - whether a dual classification is allowed;
  - the charges for pages beyond 6.

## Comparators

All DOIs were checked against Crossref.

| Paper | Why it is here | Main text | Figures | Main-text maths |
|---|---|---|---|---|
| Boyle et al. 2025, [10.1073/pnas.2406344122](https://doi.org/10.1073/pnas.2406344122) | Gaia-theory model; Biological Sciences, Evolution | ~7,100 words | 4, with a schematic first | 1 equation in Results; the model sits in Methods |
| Gupta & Khammash 2022, [10.1073/pnas.2207802119](https://doi.org/10.1073/pnas.2207802119) | Integral feedback, perfect adaptation | ~9,000 words | 9 | Theorems in the main text; proofs in SI |
| Wogan et al. 2022, [10.1073/pnas.2205618119](https://doi.org/10.1073/pnas.2205618119) | Compact Precambrian model with instability | ~5,750 words | 4 | Few; short Methods with SI |
| Goldman et al. 2025, [10.1073/pnas.2322440122](https://doi.org/10.1073/pnas.2322440122) | Order dependence in community assembly (experiment plus model) | ~8,450 words | 6 | Few |
| Thompson et al. 2022, [10.1073/pnas.2117933119](https://doi.org/10.1073/pnas.2117933119) | Methane biosignature; how to state a conditional claim | ~7,350 words | 5 | Few; mostly SI |

Word counts include captions and Methods.

## Implications (Claude's synthesis)

1. **Length.** Aim for 5,500–6,500 words, about 8 pages. The comparators run
   long, but every page over 6 has to earn its place.
2. **Structure.** Use Wogan's model:
   - an untitled opening;
   - four Results subsections, each titled with its claim;
   - a Discussion;
   - a short Methods section that carries the model logic, with derivations,
     convergence checks and sweeps in the SI.

   Our methods are standard (stability, delay margins, continuation,
   quadrature), so the Methods do not need full length.
3. **Main figures (four), one claim each:**
   1. Mechanism and plateau: the schematic plus T* against supply. Credit
      Seto & Akagi here.
   2. Lag fragility: the delay margin of exact regulation, and the
      transient just past it.
   3. The trade-off curve: τ_c against |S_c| along the dials and the spatial
      states. This is the headline figure.
   4. Invasion order decides the endpoint.

   Everything else goes to the SI.
4. **Maths.** Results carry one or two displayed equations: the coexistence
   condition and the lagged temperature equation. Methods carry the model.
   Proofs and numerics go in the SI.
5. **The conditional framing.** State it once, in the abstract, the opening
   and the first paragraph of the Discussion. After that, write "within this
   model" in findings language. List the conditions (X4, X7 and the
   differential methane yield) in one place, with what each does to the
   result, as Thompson et al. do. No repeated hedging.
6. **Significance Statement.** Three beats: why regulation of a young
   planet's climate matters; what is unknown about whether biological
   regulation survives climate inertia; what we show.
7. **Ending.** Close on the principle (exact biotic regulation is fragile and
   leaky regulation is robust) and on what it implies for Gaia theory and
   biosignatures. Do not close on a list of limitations.
8. **Classification.** The choice between Biological Sciences (Ecology or
   Evolution, as Boyle) and Physical Sciences (Earth, Atmospheric and
   Planetary Sciences) also decides who reviews the paper. Biological
   Sciences matches the main audience. Decide at submission.

No comparator models hydrogen-competition regulation or Archean haze
thermostats.
