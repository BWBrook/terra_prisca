# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Build the bibliography from its DOI ledger (vendored from the living-paper skill).

    uv run tools/refs.py build [DIR]   # DIR/dois.txt + manual.yaml -> DIR/refs.yaml (DIR defaults to references/)

references/dois.txt (one DOI per line) is the ledger: add a DOI there, rebuild, cite the printed key.
Metadata comes from Crossref's CSL-JSON, or from doi.org content negotiation for DataCite DOIs; works without a
DOI go in references/manual.yaml. Years are print years where Crossref records one.
Keys follow Better BibTeX's auth.lower + year + three-word short title, so a Zotero export matches.
"""

import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

REFS = Path(__file__).resolve().parents[1] / "references"
# Better BibTeX's default skipWords, so keys match a Zotero export of the same DOIs.
STOP = set("""a ab aboard about above across after against al along amid among an and anti around as at before behind
below beneath beside besides between beyond but by d da das de del dell dello dei degli della delle dem den der des
despite die do down du during ein eine einem einen einer eines el en et except for from gli i il in inside into is l la
las le les like lo los near nor of off on onto or over past per plus round save since so some sur than the through to
toward towards un una unas under underneath une unlike uno unos until up upon versus via von while whilst with within
without yet zu zum""".split())
TYPES = {"journal-article": "article-journal", "book-chapter": "chapter", "proceedings-article": "paper-conference",
         "posted-content": "article", "monograph": "book"}
KEEP = ["type", "title", "author", "issued", "container-title", "volume", "issue", "page", "article-number",
        "publisher", "DOI", "URL"]


def _get(url, headers):
    req = urllib.request.Request(url, headers={"User-Agent": "living-paper-refs/0.2", **headers})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 4:
                raise
            time.sleep(2 ** attempt * 2)


def fetch(doi):
    """CSL-JSON from Crossref; DataCite and other agencies through doi.org content negotiation."""
    quoted = urllib.parse.quote(doi, safe="/")
    try:
        return _get(f"https://api.crossref.org/works/{quoted}/transform/application/vnd.citationstyles.csl+json", {})
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    return _get(f"https://doi.org/{quoted}", {"Accept": "application/vnd.citationstyles.csl+json"})


def ascii_fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def markup(s):
    s = re.sub(r"</?(i|em)>", "*", s)
    s = re.sub(r"<sub>(.*?)</sub>", r"~\1~", s)
    s = re.sub(r"<sup>(.*?)</sup>", r"^\1^", s)
    return re.sub(r"<[^>]+>", "", s).strip()


def key(entry):
    family = ascii_fold(entry["author"][0].get("family", entry["author"][0].get("literal", ""))).lower()
    family = re.sub(r"[^a-z-]", "", family)
    year = entry["issued"]["date-parts"][0][0]
    words = [w for w in re.findall(r"[A-Za-z0-9-]+", ascii_fold(re.sub(r"<[^>]+>", "", entry["title"])))
             if w.lower() not in STOP]
    # Better BibTeX keeps each word's own casing (SHCal20, AustArch) and only capitalises its first letter.
    return f"{family}{year}" + "".join((w[:1].upper() + w[1:]).replace("-", "") for w in words[:3])


def clean(raw):
    entry = {k: raw[k] for k in KEEP if raw.get(k)}
    entry["type"] = TYPES.get(entry["type"], entry["type"])
    for k in ("title", "container-title"):
        if isinstance(entry.get(k), list):
            entry[k] = entry[k][0]
        if k in entry:
            entry[k] = markup(entry[k])
    entry["author"] = [{x: a[x] for x in ("family", "given", "literal") if a.get(x)} for a in raw["author"]]
    for a in entry["author"]:
        if "given" in a:
            # Pandoc drops a bare one-letter given name ("N"); write initials with periods ("N.").
            a["given"] = re.sub(r"\b([A-Z])(?=\s|$)", r"\1.", a["given"])
    # The print year, as journals cite it; Crossref's "issued" is often the earlier online-first date.
    issued = raw.get("published-print") or raw.get("issued") or raw.get("published-online")
    entry["issued"] = {"date-parts": [issued["date-parts"][0][:1]]}
    if entry.get("DOI"):
        entry["DOI"] = entry["DOI"].lower()
        entry.pop("URL", None)
    entry["page"] = entry.get("page", "").replace("-", "–") or None
    return {k: v for k, v in entry.items() if v}


def build(refs=None):
    global REFS
    REFS = Path(refs).resolve() if refs else REFS
    dois = [d.strip().lower() for d in (REFS / "dois.txt").read_text().splitlines()
            if d.strip() and not d.startswith("#")]
    if len(set(dois)) != len(dois):
        sys.exit("duplicate DOI in dois.txt")
    entries, failed = [], []
    for d in dois:
        try:
            entries.append(clean(fetch(d)))
        except (urllib.error.URLError, KeyError, TypeError, ValueError) as exc:
            failed.append(f"{d}: {exc}")
    if failed:
        sys.exit("refs.yaml not written; these DOIs failed (fix them or move them to manual.yaml):\n  "
                 + "\n  ".join(failed))
    entries += yaml.safe_load((REFS / "manual.yaml").read_text())["references"] or []
    out, seen = [], set()
    for e in entries:
        k = e.pop("id", None) or key(e)
        if k in seen:
            # Disambiguate as Better BibTeX does: a letter suffix on the later work. Check the cited key afterwards.
            base = k
            k = next(base + c for c in "abcdefghijklmnopqrstuvwxyz" if base + c not in seen)
            print(f"warning: key {base} already used; {e.get('DOI', e.get('title', ''))} is {k}", file=sys.stderr)
        seen.add(k)
        out.append({"id": k, "citation-key": k, **e})
    out.sort(key=lambda e: e["id"])
    text = yaml.safe_dump({"references": out}, allow_unicode=True, sort_keys=False, width=200)
    (REFS / "refs.yaml").write_text("---\n" + text + "...\n")
    for e in out:
        print(e["id"], e.get("DOI", ""))


if __name__ == "__main__":
    if sys.argv[1:2] != ["build"] or len(sys.argv) > 3:
        sys.exit(__doc__)
    build(sys.argv[2] if len(sys.argv) == 3 else None)
