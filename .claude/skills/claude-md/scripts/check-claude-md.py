#!/usr/bin/env python3
"""Lint a CLAUDE.md: size vs budget, headings, backticked paths and markdown links that don't exist,
and (optionally) that required names appear in the text. Stdlib only.

Local usage:
  check-claude-md.py path/to/CLAUDE.md
  check-claude-md.py home-kubernetes/CLAUDE.md --names dashy,arc,external-dns,hogwarts

Exit 1 on missing paths/links or missing names; size over budget only warns. A path flagged because it is
intentionally gone (e.g. "removed archive/") or generated (e.g. `dist/`) is expected: judge, do not blindly fix.
"""
import argparse
import os
import re
import subprocess
import sys

ap = argparse.ArgumentParser(description="Lint a CLAUDE.md.")
ap.add_argument("file")
ap.add_argument("--names", default="", help="comma-separated names that must appear in the text")
args = ap.parse_args()
if not os.path.isfile(args.file):
    sys.exit(f"no such file: {args.file}")

f = os.path.abspath(args.file)
names = [n for n in args.names.split(",") if n]
fdir = os.path.dirname(f)
text = open(f).read()
lines = text.split("\n")

def git_root(d):
    try:
        return subprocess.check_output(["git", "-C", d, "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return d

repo = git_root(fdir)
workspace = os.path.dirname(repo)
nested = fdir != repo
budget, hard = (40, 60) if nested else (100, 120)
content = [l for l in lines if l.strip()]
print(f"{os.path.relpath(f)}: {len(lines)} lines ({len(content)} non-blank), {'nested' if nested else 'root'} budget ~{budget}")
status = 0
if len(lines) > hard:
    print(f"  WARN over budget: extract detail to docs/ and leave one-line pointers (> {hard} lines)")
elif len(lines) > budget + 15:
    print(f"  NOTE above the ~{budget} line target")

print("  headings: " + " | ".join(re.findall(r"^#{1,3} (.+)$", text, re.M)))

# Backticked tokens that look like repo paths
cand = set()
for t in re.findall(r"`([^`\n]+)`", text):
    t = t.strip()
    if re.search(r"[<>*{}$|\s=:]|^https?:|^~|^-|\.\.\.|^\d+\.\d+", t):
        continue
    if "/" in t or re.search(r"\.(md|sh|py|ya?ml|json|tf|toml|mdc)$", t):
        if re.match(r"^[\w.][\w./-]*$", t):
            cand.add(t)
links = {l for l in re.findall(r"\]\((?!https?:|#|mailto:)([^)#\s]+)", text)}

def tracked(root):
    try:
        out = subprocess.check_output(["git", "-C", root, "ls-files", "-co", "--exclude-standard"], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return set()
    ents = set()
    for e in out.split("\n"):
        parts = e.split("/")
        for i in range(1, len(parts) + 1):
            ents.add("/".join(parts[:i]))
    return ents

# Shorthand like `base/` or `check-manifest.sh` is fine when it matches the tail of a real path in this repo.
suffixes = tracked(repo)
for base in {repo, workspace}:  # sibling repos (when the file is in a nested repo) and child repos (workspace root)
    for d in sorted(os.listdir(base)):
        sub = os.path.join(base, d)
        if os.path.isdir(sub) and os.path.exists(os.path.join(sub, ".git")) and sub != repo:
            suffixes |= tracked(sub)

def exists(p):
    if any(os.path.exists(os.path.normpath(os.path.join(r, p))) for r in (fdir, repo, workspace)):
        return True
    q = p.rstrip("/")
    return any(e == q or e.endswith("/" + q) for e in suffixes)

missing = sorted(p for p in cand | links if not exists(p))
if missing:
    status = 1
    print("  MISSING paths (not found relative to the file, repo root, workspace root, or as the tail of any repo path):")
    for p in missing:
        print("    " + p)
else:
    print(f"  paths ok ({len(cand | links)} checked)")

if names:
    low = text.lower()
    absent = [n for n in names if not re.search(r"(?<![\w-])" + re.escape(n.lower()) + r"(?![\w-])", low)]
    if absent:
        status = 1
        print("  NAMES not found in text: " + ", ".join(absent))
    else:
        print(f"  names ok ({len(names)} checked)")
sys.exit(status)
