"""
Repo-wide markdown link verifier. Extracts the methodology that was described but never saved
as a file: REPO_MAP.md's own writeups/ section (§8) describes "a 100-link check via a Python
script comparing percent-encoded/decoded paths against os.path.exists" -- that script was run
ad hoc once and not committed. This is that script, generalized to every .md file in the repo
and reusable going forward (run it after any file move/rename, not just this one).

For every markdown-style link `[text](path)` or `[text](<path with spaces>)` in every .md file
(excluding the two third-party mirrors and any .git internals), resolves the target relative to
the linking file's own directory, percent-decodes it, and checks it exists on disk. Skips http(s)
URLs and same-file anchor links (#section).

Usage:
    python3 scripts/verify_md_links.py
"""
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {
    ROOT / "external_repos",
    ROOT / "data" / "external" / "statsbomb" / "open-data",
    ROOT / ".git",
}

# Matches both `](<path with spaces or parens>)` and plain `](path)` forms.
LINK_RE = re.compile(r"\]\(<([^>]+)>\)|\]\(([^)\s]+)\)")


def is_excluded(path: Path) -> bool:
    return any(excluded in path.parents or path == excluded for excluded in EXCLUDE_DIRS)


def find_md_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dpath = Path(dirpath)
        if is_excluded(dpath):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if not is_excluded(dpath / d)]
        for fn in filenames:
            if fn.endswith(".md"):
                yield dpath / fn


def check_file(md_path: Path):
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    base_dir = md_path.parent
    checked = 0
    broken = []
    for m in LINK_RE.finditer(text):
        target = m.group(1) or m.group(2)
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = target.split("#")[0]  # strip in-page anchors
        if not target:
            continue
        target = unquote(target)
        full = (base_dir / target).resolve()
        checked += 1
        if not full.exists():
            broken.append(target)
    return checked, broken


def main():
    total_checked = 0
    total_broken = 0
    files_with_breaks = []
    for md_path in sorted(find_md_files()):
        checked, broken = check_file(md_path)
        total_checked += checked
        if broken:
            total_broken += len(broken)
            files_with_breaks.append((md_path, broken))

    print(f"Checked {total_checked} links across the repo.\n")
    if not files_with_breaks:
        print("No broken links found.")
        return 0

    for md_path, broken in files_with_breaks:
        rel = md_path.relative_to(ROOT)
        print(f"{rel}: {len(broken)} broken link(s)")
        for b in broken:
            print(f"    {b}")
    print(f"\n{total_broken} broken link(s) across {len(files_with_breaks)} file(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
