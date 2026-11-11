"""Keep a paper's renderings tied to one claims ledger (vendored from the living-paper skill).

    python3 tools/claims.py check LEDGER DOC...   # ledger, evidence and every citation in DOCs
    python3 tools/claims.py stamp LEDGER ID...    # record the latest commit touching each claim's evidence

The ledger (CSV) holds one row per claim: id, status, claim, value, basis, evidence, commit, reproduce,
limit, superseded_by. Documents cite claims in two ways:

- `[428.8]{.C27}` binds the text to C27. Each number in the bracket must equal one of C27's values
  at the precision shown, so a changed value breaks every document that quotes it. `[]{.C15}` cites
  without a number. A superseded or refuted claim may be cited only with `.superseded` added, as in
  `[452.6]{.C35 .superseded}`. Spans are invisible in rendered PDF and DOCX.
- A bare `C27` (the agent guide) is checked for existence only.

A shown number matches a value when the value rounds (half up) to it at the precision shown, so `[11]{.C22}` matches a
value of 10.6 without a separate `~11` entry.

Strict bindings (value-bindings.csv) select one row, or aggregate rows with {"where": {...}, "aggregate": {"op":
"count"|"min"|"max", "column": ...}}. A selector may add {"abs": true} or {"scale": 100} so that unsigned or percentage
prose binds to signed or proportional evidence.

In `value`, a number prefixed with `~` is derived (a difference, a rounding) and is not looked for in
the evidence files. Every other value number must appear, at its precision, in at least one evidence
file. A current claim whose evidence changed after its recorded commit is reported as stale.
"""

import csv
import decimal
import json
import re
import subprocess
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["id", "status", "claim", "value", "basis", "evidence", "commit", "reproduce", "limit", "superseded_by"]
BINDING_FIELDS = ["binding_id", "claim_id", "evidence", "selector", "value_column", "estimand", "display_values"]
STATUS = {"supported", "provisional", "refuted", "superseded"}
NUMBER = re.compile(r"(?<![\w.])(~?)([−-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\d)|[−-]?\d+(?:\.\d+)?(?:e[−-]?\d+)?)")
PLAIN = re.compile(r"(?<![\w.])(~?)([−-]?\d+(?:\.\d+)?(?:e[−-]?\d+)?)")
SPAN = re.compile(r"(?<!!)\[([^\[\]]*)\]\{([^}]*)\}")
BARE = re.compile(r"(?<![\w.{-])C\d{2,3}\b")


def numbers(text, prose=True):
    out = []
    for tilde, raw in (NUMBER if prose else PLAIN).findall(text):
        out.append((tilde == "~", Decimal(raw.replace(",", "").replace("−", "-"))))
    return out


def same(shown, canonical):
    exp = shown.as_tuple().exponent
    step = Decimal(1).scaleb(exp) if isinstance(exp, int) and exp < 0 else Decimal(1)
    if abs(canonical - shown) > step:
        return False
    return canonical.quantize(step, ROUND_HALF_UP) == shown


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)


def load(ledger):
    with open(ledger, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FIELDS:
            sys.exit(f"{ledger}: columns must be {','.join(FIELDS)}")
        return list(reader)


def load_bindings(path):
    """Read the optional value-to-evidence binding sidecar."""
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != BINDING_FIELDS:
            sys.exit(f"{path}: columns must be {','.join(BINDING_FIELDS)}")
        rows = []
        for row in reader:
            try:
                row["selector_json"] = json.loads(row["selector"])
                row["display_json"] = json.loads(row["display_values"])
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}: {row.get('binding_id', '')}: invalid JSON: {exc}") from exc
            rows.append(row)
        return rows


def _csv_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _matches(row, selector):
    """Apply equality selectors, including an explicit equality-any group."""
    for key, expected in selector.items():
        if isinstance(expected, list):
            if row.get(key, "") not in {str(value) for value in expected}:
                return False
        elif expected is None:
            if row.get(key, "") != "":
                return False
        elif row.get(key, "") != str(expected):
            return False
    return True


def _selected_rows(path, selector):
    """Return rows selected by an equality selector and its optional aggregate."""
    if not isinstance(selector, dict):
        raise ValueError("selector must be a JSON object")
    where = selector.get("where", {k: v for k, v in selector.items() if k not in {"abs", "scale"}})
    if not isinstance(where, dict):
        raise ValueError("selector.where must be an object")
    if not where:
        raise ValueError("selector must contain at least one equality field")
    rows = _csv_rows(path)
    selected = [row for row in rows if _matches(row, where)]
    return selected, selector.get("aggregate")


def _binding_value(binding, evidence_path):
    selected, aggregate = _selected_rows(evidence_path, binding["selector_json"])
    if aggregate is None:
        if len(selected) != 1:
            raise ValueError(f"selector matched {len(selected)} rows, expected exactly one")
        value = selected[0].get(binding["value_column"], "")
        if value == "":
            raise ValueError(f"selected row has no value in {binding['value_column']}")
        return [_transform(Decimal(value.replace("−", "-")), binding["selector_json"])]
    if not isinstance(aggregate, dict) or aggregate.get("op") not in {"count", "min", "max"}:
        raise ValueError("aggregate op must be count, min or max")
    if not selected:
        raise ValueError("aggregate selector matched no rows")
    column = aggregate.get("column", binding["value_column"])
    values = [row.get(column, "") for row in selected]
    if any(value == "" for value in values):
        raise ValueError(f"aggregate column {column} contains blank values")
    if aggregate["op"] in {"min", "max"}:
        numbers = [Decimal(v.replace("−", "-")) for v in values]
        return [_transform(min(numbers) if aggregate["op"] == "min" else max(numbers), binding["selector_json"])]
    if aggregate.get("distinct", False):
        values = list(dict.fromkeys(values))
    return [Decimal(len(values))]


def _transform(value, selector):
    """Optional display transforms: {"abs": true} for unsigned prose, {"scale": 100} for percentages."""
    if selector.get("abs"):
        value = abs(value)
    if "scale" in selector:
        value = value * Decimal(str(selector["scale"]))
    return value


def check_bindings(path, by_id, docs, errors):
    """Check strict value bindings and return binding rows indexed by token."""
    rows = load_bindings(path)
    by_token = {}
    for row in rows:
        token = row["binding_id"]
        claim = row["claim_id"]
        if not re.fullmatch(r"V\d{3}", token):
            errors.append(f"{path}: {token}: binding_id must be V followed by three digits")
        if token in by_token:
            errors.append(f"{path}: duplicate binding_id {token}")
        by_token[token] = row
        if claim not in by_id:
            errors.append(f"{path}: {token}: unknown claim {claim}")
        evidence = row["evidence"].strip()
        evidence_path = ROOT / evidence
        if not evidence or not evidence_path.is_file():
            errors.append(f"{path}: {token}: evidence {evidence} does not exist")
            continue
        if not isinstance(row["selector_json"], dict):
            errors.append(f"{path}: {token}: selector must be a JSON object")
        if not isinstance(row["display_json"], list) or not row["display_json"]:
            errors.append(f"{path}: {token}: display_values must be a non-empty JSON list")
        try:
            source_values = _binding_value(row, evidence_path)
            displays = [Decimal(str(value).replace("−", "-")) for value in row["display_json"]]
            if len(displays) != len(source_values):
                raise ValueError(f"display_values has {len(displays)} values; source has {len(source_values)}")
            for shown, source in zip(displays, source_values):
                if not same(shown, source):
                    raise ValueError(f"displayed {shown} does not match source {source}")
        except (ValueError, KeyError, TypeError, decimal.InvalidOperation) as exc:
            errors.append(f"{path}: {token}: {exc}")
    strict = {row["claim_id"] for row in rows}
    for doc in docs:
        text = re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), Path(doc).read_text())
        for m in SPAN.finditer(text):
            classes = re.findall(r"\.([\w-]+)", m.group(2))
            claims = [c for c in classes if re.fullmatch(r"C\d{2,3}", c)]
            tokens = [c for c in classes if re.fullmatch(r"V\d{3}", c)]
            if not claims:
                continue
            where = f"{doc}:{text.count(chr(10), 0, m.start()) + 1}"
            shown = numbers(m.group(1))
            if shown and len(tokens) > 1:
                errors.append(f"{where}: numeric {claims[0]} span has multiple .V### bindings")
                continue
            if tokens:
                token = tokens[0]
                binding = by_token.get(token)
                if binding is None:
                    errors.append(f"{where}: unknown binding {token}")
                    continue
                if binding["claim_id"] != claims[0]:
                    errors.append(f"{where}: {token} binds {binding['claim_id']}, not {claims[0]}")
                    continue
            if claims[0] not in strict:
                continue
            if shown and len(tokens) != 1:
                errors.append(f"{where}: strict numeric {claims[0]} span requires exactly one .V### binding")
                continue
            if not shown:
                if tokens:
                    errors.append(f"{where}: {tokens[0]} binds a span with no numeric value")
                continue
            token = tokens[0]
            binding = by_token.get(token)
            if binding is None:
                errors.append(f"{where}: unknown binding {token}")
                continue
            displays = [Decimal(str(value).replace("−", "-")) for value in binding["display_json"]]
            if len(shown) != len(displays) or any(shown[i][1] != displays[i] for i in range(len(shown))):
                errors.append(f"{where}: {token} display_values do not match the cited numeric span")
    return by_token


def check_ledger(rows, errors, warnings):
    ids = [r["id"] for r in rows]
    for i in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"duplicate id {i}")
    by_id = {r["id"]: r for r in rows}
    evidence_numbers = {}
    for r in rows:
        cid = r["id"]
        if not re.fullmatch(r"C\d{2,3}", cid):
            errors.append(f"{cid}: id must be C followed by two or three digits")
        if r["status"] not in STATUS:
            errors.append(f"{cid}: status '{r['status']}' not in {sorted(STATUS)}")
        if r["status"] == "superseded" and r["superseded_by"] not in by_id:
            errors.append(f"{cid}: superseded_by must name an existing claim")
        if not r["reproduce"].strip():
            errors.append(f"{cid}: no reproduce command")
        paths = [p.strip() for p in r["evidence"].split(";") if p.strip()]
        if not paths:
            errors.append(f"{cid}: no evidence")
        missing = [p for p in paths if not (ROOT / p).exists()]
        for p in missing:
            errors.append(f"{cid}: evidence {p} does not exist")
        if not r["commit"] or git("cat-file", "-e", f"{r['commit']}^{{commit}}").returncode:
            errors.append(f"{cid}: commit '{r['commit']}' not found; run stamp")
        elif git("merge-base", "--is-ancestor", r["commit"], "HEAD").returncode:
            errors.append(f"{cid}: commit {r['commit']} is not an ancestor of HEAD (rebased or amended?); run stamp")
        elif not missing and r["status"] in {"supported", "provisional"} and (git("diff", "--quiet", r["commit"], "--", *paths).returncode
                              or git("diff", "--quiet", "HEAD", "--", *paths).returncode):
            warnings.append(f"{cid}: evidence changed since {r['commit']}; reverify, then stamp")
        if missing or r["status"] in {"superseded", "refuted"}:
            continue
        pool = []
        for p in paths:
            if p not in evidence_numbers:
                files = [ROOT / p] if (ROOT / p).is_file() else sorted((ROOT / p).rglob("*.*"))
                evidence_numbers[p] = [n for fp in files if fp.suffix in {".csv", ".md", ".json", ".txt", ".tsv"}
                                       for _, n in numbers(fp.read_text(errors="ignore"), fp.suffix == ".md")]
            pool += evidence_numbers[p]
        pool = set(pool)
        for derived, n in numbers(r["value"]):
            if not derived and not any(same(n, e) for e in pool):
                errors.append(f"{cid}: value {n} not found in its evidence (prefix ~ if derived)")
    return by_id


def check_doc(path, by_id, cited, errors):
    text = re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), Path(path).read_text())
    for m in SPAN.finditer(text):
        classes = re.findall(r"\.([\w-]+)", m.group(2))
        ids = [c for c in classes if re.fullmatch(r"C\d{2,3}", c)]
        if not ids:
            continue
        where = f"{path}:{text.count(chr(10), 0, m.start()) + 1}"
        if len(ids) > 1:
            errors.append(f"{where}: one claim per span")
            continue
        r = by_id.get(ids[0])
        if r is None:
            errors.append(f"{where}: unknown claim {ids[0]}")
            continue
        cited.add(ids[0])
        old = r["status"] in {"superseded", "refuted"}
        if old != ("superseded" in classes):
            errors.append(f"{where}: {ids[0]} is {r['status']}; "
                          + ("mark the citation .superseded" if old else "drop .superseded"))
        canon = [n for _, n in numbers(r["value"])]
        for _, n in numbers(m.group(1)):
            if not any(same(n, c) for c in canon):
                errors.append(f"{where}: '{m.group(1)}' quotes {n}, not a value of {ids[0]} ({r['value']})")
    for m in BARE.finditer(SPAN.sub("", text)):
        if m.group(0) not in by_id:
            errors.append(f"{path}: unknown claim {m.group(0)}")
        cited.add(m.group(0))


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in {"check", "stamp"}:
        sys.exit(__doc__)
    ledger = sys.argv[2]
    rows = load(ledger)
    if sys.argv[1] == "stamp":
        targets = set(sys.argv[3:])
        for r in rows:
            if r["id"] in targets:
                paths = [p.strip() for p in r["evidence"].split(";") if p.strip()]
                r["commit"] = git("log", "-1", "--format=%h", "--", *paths).stdout.strip()
                targets.discard(r["id"])
        if targets:
            sys.exit(f"unknown ids: {sorted(targets)}")
        with open(ledger, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        return
    errors, warnings, cited = [], [], set()
    by_id = check_ledger(rows, errors, warnings)
    for doc in sys.argv[3:]:
        check_doc(doc, by_id, cited, errors)
    bindings = Path(ledger).with_name("value-bindings.csv")
    if bindings.exists():
        check_bindings(bindings, by_id, sys.argv[3:], errors)
    for cid, r in by_id.items():
        if r["status"] in {"supported", "provisional"} and cid not in cited:
            warnings.append(f"{cid}: not cited in any document")
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("error:", e)
    counts = {s: sum(r["status"] == s for r in rows) for s in sorted(STATUS)}
    print(f"{len(rows)} claims {counts}; {len(cited)} cited; {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
