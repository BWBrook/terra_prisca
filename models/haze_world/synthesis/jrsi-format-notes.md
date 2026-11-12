# J R Soc Interface format notes for the haze-world paper

Claude (Opus 5.5) and a Claude Sonnet 5.5 subagent, 12 November 2026. These
notes cover form only. Barry leads the writing process, and nothing here is a
draft.

## Target

**Journal of the Royal Society Interface**, as a Research Article, with a
preprint before submission (Barry, 12 November 2026).

PNAS was dropped because it carries publication charges and is not on the
CAUL 2026 title list for UTAS. JRSI is listed there as Eligible (hybrid,
Royal Society agreement).

## Rules

**Sources.** royalsocietypublishing.org returned 403, so the JRSI-specific
pages were not read. The general Royal Society pages were read:

- [author guidelines](https://royalsociety.org/journals/authors/author-guidelines);
- [data sharing](https://royalsociety.org/journals/ethics-policies/data-sharing-mining/);
- [AI](https://royalsociety.org/journals/ethics-policies/artificial-intelligence/);
- [preprints and embargo](https://royalsociety.org/journals/ethics-policies/media-embargo/).

**Length (unverified, from a search summary).** A research article runs to
2,500–8,000 words, including references and acknowledgements. Confirm this in
the submission checklist. No limit on figures or tables was found.

**Front matter:**

- **Abstract:** no more than 200 words, standalone.
- **Keywords:** 3–10.
- **Media summary:** a lay summary of up to 100 words, entered in the
  submission form.

**Main text:**

- **Sections:** usually Introduction, Model or Methods, Results, Discussion.
  Methods must allow replication.
- **First submission:** format-free.
- **References:** Vancouver style, numbered. Code and data are cited in the
  reference list with DOIs.
- **ESM:** the main text must stand alone. The ESM is posted to figshare
  under CC-BY, and the authors proofread it themselves.

**Data and code:**

- Both must be public at publication and available to reviewers at
  submission. "Available on request" is not accepted.
- Code must sit in a permanent DOI-issuing repository and be cited as
  software. GitHub archived on Zenodo is named as acceptable.

**End statements:**

- Ethics; Data accessibility; Declaration of AI use; Authors' contributions
  (CRediT); Conflict of interest; Funding; Acknowledgements.
- The submitting author needs an ORCID.

**Preprints:**

- Allowed at any time, and disclosed at submission.
- Submitting within 3 months of posting gives scoop protection.

**Open access:** CC-BY 4.0. The Royal Society lists Interface as moving to
Subscribe to Open from 2026, which may make the CAUL payment moot. Confirm
this.

**Review:** authors may suggest reviewers. Review is single-anonymised.

### AI policy (checked directly on 12 November 2026)

Three sentences from the policy page matter:

- Authors must "disclose in the manuscript their use", and the published work
  carries a statement.
- AI may not be an author or be cited as one.
- "Where used in the writing process, these technologies should only be used
  to improve readability and language of the work."

The journal may also ask for prompts and outputs, supplied as ESM.

**What this means for us.** The restriction applies to *writing*. It does not
cover modelling or analysis. AI-built models and analyses are allowed if
disclosed in full, and our standing practice already does that.

The writing clause does bind us. Text drafted by Claude or Codex beyond
language editing does not fit the policy as worded. This bears directly on
how Barry's writing process divides the work. Options:

- the humans write the text, and the AIs supply evidence, figures and
  language edits;
- or we ask the editorial office before submission whether full disclosure of
  AI drafting is acceptable.

Keep the correspondence record and the claims ledger, because they can serve
as the prompt-and-output ESM if asked.

## Comparators

All DOIs were checked against Crossref.

| Paper | Why it is here | Main text | Main-text equations | Figures |
|---|---|---|---|---|
| Blanco 2026, [10.1098/rsif.2025.1306](https://doi.org/10.1098/rsif.2025.1306) | Minimal population–environment feedback model; Astrobiology subject. **Closest template.** | ~4,400 words | 14 | 6, with a schematic first |
| Karamched & Miles 2023, [10.1098/rsif.2023.0059](https://doi.org/10.1098/rsif.2023.0059) | Delayed feedback, Hopf, oscillation suppression. Closest in method. | ~5,900 words | 30 | 5 |
| Alexis et al. 2023, [10.1098/rsif.2023.0174](https://doi.org/10.1098/rsif.2023.0174) | Biomolecular regulation architectures; control audience | ~5,900 words | 32 | 9, with a control diagram first |
| Suen & Navlakha 2022, [10.1098/rsif.2021.0711](https://doi.org/10.1098/rsif.2021.0711) | A feedback principle across systems. Too long to copy. | ~12,000 words | 10 | 5, plus 1 table |
| Gupta & Sontag 2025, [10.1098/rsif.2024.0877](https://doi.org/10.1098/rsif.2024.0877) | Adaptation and integral feedback; proof-heavy | long | ~130 | 10 |

## Drafting implications (Claude's synthesis)

1. **Length:** about 5,000–6,000 words of main text, an abstract of 200 words
   or fewer, and a 100-word media summary. The media summary is the seed of
   our two-page brief.
2. **Structure (follow Blanco):**
   - Introduction.
   - Model: the core ODEs, the lagged temperature equation and the stated
     conditions.
   - Results, in four subsections titled with their claims:
     1. the plateau as integral feedback, credited to Seto & Akagi;
     2. lag fragility;
     3. the leaky-regulation trade-off;
     4. invasion order.
   - Discussion.

   Derivations, quadrature, continuation and convergence go in the ESM.
3. **Maths:** about 10–20 displayed equations in the main text is normal
   here. That covers the model, the delay characteristic equation and the
   definitions of S_c and τ_c.
4. **Figures:** the four planned main figures, as before. Fig. 1 combines the
   mechanism schematic with the plateau. Fig. 3, the trade-off curve, is the
   headline. Panels are labelled (*a*)–(*d*). Colour must stay legible in
   greyscale print.
5. **Framing:** a conditional model by design. State the conditions as part
   of the object of study in the Model section, then report findings
   directly.
6. **Data and code:** tag a Zenodo release before submission and cite the
   software DOI. Say plainly that there is no primary dataset. Make sure
   reviewers can reach the repository at submission (it is already public).
7. **Preprint:** post it, then submit within 3 months. EarthArXiv or arXiv
   q-bio.PE are the likely venues; decide when the time comes.
8. **Declaration of AI use:** name the systems, versions and roles in full.
   Settle the writing-process question above before drafting begins.
