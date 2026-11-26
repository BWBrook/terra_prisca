"""Write a copy of a Markdown source that still works once its PDF leaves the repository.

Relative links become GitHub links pinned to the current commit, and long code spans (paths, commands) are
set with xurl's \\nolinkurl so they wrap at the margin. Every link target must exist at that commit, and
a linked file with uncommitted changes fails the build, so a pinned link never points at a version
the PDF does not describe.

    python3 tools/standalone_md.py SOURCE.md OUT.md [--draft]

--draft skips the uncommitted-changes check, for linting before a commit.
"""
import re
import subprocess
import sys
from pathlib import Path

LINK = re.compile(r"(\]\()([^)\s]+)(\))")
CODE = re.compile(r"(?<!`)`([^`\n]+)`(?![`{])")
SPECIAL = re.compile(r"[\\{}%#^~&$]")


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def main(source, out, flag=None):
    draft = flag == "--draft"
    source, out = Path(source).resolve(), Path(out).resolve()
    root = Path(git("rev-parse", "--show-toplevel", cwd=source.parent))
    sha = git("rev-parse", "HEAD", cwd=root)
    remote = git("remote", "get-url", "origin", cwd=root)
    repo = re.sub(r"^git@github\.com:|^https://github\.com/", "", remote).removesuffix(".git")
    problems = []

    def pin(m):
        target = m.group(2)
        if re.match(r"[a-z]+:|#", target):
            return m.group(0)
        path, _, anchor = target.partition("#")
        rel = (source.parent / path).resolve().relative_to(root).as_posix()
        kind = subprocess.run(["git", "cat-file", "-t", f"{sha}:{rel}"], cwd=root, capture_output=True, text=True).stdout.strip()
        if kind not in ("blob", "tree"):
            problems.append(f"{target}: not in commit {sha[:7]}")
        elif kind == "blob" and not draft and subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=root).returncode:
            problems.append(f"{target}: uncommitted changes; commit before building")
        url = f"https://github.com/{repo}/{'tree' if kind == 'tree' else 'blob'}/{sha}/{rel}".rstrip("/")
        return m.group(1) + url + ("#" + anchor if anchor else "") + m.group(3)

    def wrap(m):
        text = m.group(1)
        if len(text) < 16 or SPECIAL.search(text):
            return m.group(0)
        return "`" + " ".join(f"\\nolinkurl{{{w}}}" for w in text.split()) + "`{=latex}"

    body = source.read_text()
    body = CODE.sub(wrap, LINK.sub(pin, body))
    if problems:
        sys.exit("standalone_md: " + "; ".join(problems))
    header = f"---\nheader-includes: |\n  ```{{=latex}}\n  \\usepackage{{xurl}}\n  ```\n---\n\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header + body)
    print(f"{out.name}: links pinned to {repo}@{sha[:7]}")


if __name__ == "__main__":
    main(*sys.argv[1:])
