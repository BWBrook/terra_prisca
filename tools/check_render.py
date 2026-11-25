"""Check the brief's length, which a clean build does not report (vendored from the living-paper skill).

    python3 tools/check_render.py --brief PDF [--max-pages 2]

The brief must print on one A4 sheet, double-sided: at most two pages. Needs Poppler's pdfinfo.
Missing glyphs need no check here: makedoc 2 fails the build and names the character.
"""

import re
import subprocess
import sys
from pathlib import Path


def pages(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", out, re.M).group(1))


def main(argv):
    if not argv or argv[0] in {"-h", "--help"}:
        sys.exit(__doc__)
    brief, limit = None, 2
    it = iter(argv)
    for a in it:
        if a == "--brief":
            brief = next(it)
        elif a == "--max-pages":
            limit = int(next(it))
        else:
            sys.exit(f"unknown argument {a}\n{__doc__}")
    if not brief or not Path(brief).exists():
        sys.exit(f"error: brief PDF {brief} not found; build it first")
    n = pages(brief)
    if n > limit:
        print(f"error: {brief}: {n} pages; the brief must fit {limit}")
        sys.exit(1)
    print(f"{brief}: {n} of {limit} pages")


if __name__ == "__main__":
    main(sys.argv[1:])
