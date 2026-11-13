#!/usr/bin/env python3
"""Manage the Dashy dashboard links in the Helm-templated ConfigMap. Stdlib only (PyYAML optional, used only
to validate the rendered config).

The file is not valid YAML (Helm `{{ }}` blocks), so edits are line based and leave everything else untouched.

Run from the workspace root:
  dashy.py list [--section Apps]
  dashy.py add --section Apps --title "Home HUD" --url https://home-hud.abbottland.io \\
      --description "Home dashboard" --kind react --after "Diagram Maker" [--dry-run]
  dashy.py remove --section Apps --title "Home HUD"
  dashy.py move --title "Home HUD" --to-section Media [--after Plex]
  dashy.py check-icon hl-reactjs hl-npm sh-dashy

Item ids mirror Dashy's makeItemId (src/utils/config/SectionHelpers.js): `<index>_<charSum>_<slug>`, where index is
the 0-based position in the section, charSum is the sum of the char codes of the section *name*, and slug is the title
lowercased with everything but ASCII letters removed. Dashy recomputes ids on every load and ignores the ones in the
file, so they only matter for diff noise against UI exports (and usage-tracking keys).
After every write the Chart.yaml patch version is bumped (Flux needs it) and the chart is rendered with
`helm template` for every section-flag combination; on failure both files are restored.

Exit codes: 0 ok, 1 error (nothing written), 2 icon not found / usage.
"""
import argparse
import difflib
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DEFAULT_FILE = os.path.join(ROOT, "home-kubernetes/apps/base/platform/dashy/templates/configmap.yaml")

SEC_RE = re.compile(r"^ {6}- name: (.*)$")
ITEM_RE = re.compile(r"^ {10}- title: (.*)$")
BOUND_RE = re.compile(r"^( {6}\{\{-| {4}pages:)")
ID_RE = re.compile(r"^( +id: )(\d+)_(\d+)_(\w+)\s*$")

# Owner's icon preferences: React site -> reactjs logo, library -> npm logo, otherwise hl-<name> if it exists.
KIND_ICONS = {"react": "hl-reactjs", "library": "hl-npm"}
ICON_URLS = {
    "hl-": "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/{fmt}/{name}.{fmt}",
    # selfh.st path is inferred from the selfhst/icons repo layout, not from the Dashy docs
    "sh-": "https://cdn.jsdelivr.net/gh/selfhst/icons/{fmt}/{name}.{fmt}",
}


class Item:
    def __init__(self, title, start, end):
        self.title, self.start, self.end = title, start, end


class Section:
    def __init__(self, name, start):
        self.name, self.start, self.end, self.items = name, start, start + 1, []

    @property
    def num(self):
        return getattr(self, "_num", None)


def unq(v):
    v = v.strip()
    if v.startswith('"'):
        try:
            return json.loads(v)
        except ValueError:
            return v.strip('"')
    return v.strip("'")


def quote(v):
    """Plain scalar when safe, double-quoted otherwise."""
    if re.search(r"(: | #)|^[\s\-?:,\[\]{}#&*!|>'\"%@`]|\s$", v) or v == "":
        return json.dumps(v, ensure_ascii=False)
    return v


def slug(title):
    """Dashy's makeItemId: whitespace -> '-', then everything except ASCII letters/spaces is dropped, lowercased.
    Net effect: letters only (digits and punctuation vanish), e.g. "Pi-hole 6" -> "pihole"."""
    return re.sub(r"[^a-zA-Z]", "", title).lower()


def section_num(name):
    """Dashy's charSum: sum of the UTF-16 code units of the section *name* (Apps = 404, Media = 480)."""
    b = name.encode("utf-16-le")
    return sum(int.from_bytes(b[i:i + 2], "little") for i in range(0, len(b), 2))


def parse(lines):
    sections = []
    for i, line in enumerate(lines):
        m = SEC_RE.match(line)
        if m:
            sections.append(Section(unq(m.group(1)), i))
    for k, sec in enumerate(sections):
        end = len(lines)
        for j in range(sec.start + 1, len(lines)):
            if SEC_RE.match(lines[j]) or BOUND_RE.match(lines[j]):
                end = j
                break
        sec.end = end
        starts = [j for j in range(sec.start + 1, end) if ITEM_RE.match(lines[j])]
        for n, s in enumerate(starts):
            e = starts[n + 1] if n + 1 < len(starts) else end
            sec.items.append(Item(unq(ITEM_RE.match(lines[s]).group(1)), s, e))
        for it in sec.items:
            for j in range(it.start, it.end):
                m = ID_RE.match(lines[j])
                if m:
                    sec._num = int(m.group(3))
                    break
            if sec.num is not None:
                break
    return sections


def find_section(sections, name):
    for s in sections:
        if s.name.lower() == name.lower():
            return s
    die(f"unknown section {name!r}; sections: {', '.join(s.name for s in sections)}")


def find_item(sec, title):
    for it in sec.items:
        if it.title.lower() == title.lower():
            return it
    die(f"no item {title!r} in {sec.name!r}; items: {', '.join(i.title for i in sec.items)}")


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def renumber(lines, name):
    sec = find_section(parse(lines), name)
    for idx, it in enumerate(sec.items):
        for j in range(it.start, it.end):
            m = ID_RE.match(lines[j])
            if m:
                lines[j] = f"{m.group(1)}{idx}_{m.group(3)}_{m.group(4)}"
                break
        else:
            die(f"item {it.title!r} in {sec.name!r} has no id line")


def insert_pos(sec, after):
    if not sec.items:
        die(f"section {sec.name!r} has no items to anchor an insert")
    return find_item(sec, after).end if after else sec.items[-1].end


def check_icon(name):
    """Returns 'found', 'missing', 'unverifiable' or 'error: ...'."""
    prefix = next((p for p in ICON_URLS if name.startswith(p)), None)
    if not prefix:
        return "unverifiable"  # fas/emoji/si-/mdi-/URL icons are not checked
    bare = name[len(prefix):]
    saw_404 = False
    for fmt in ("svg", "png"):
        req = urllib.request.Request(ICON_URLS[prefix].format(fmt=fmt, name=bare), method="HEAD")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    return "found"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                saw_404 = True
                continue
            return f"error: HTTP {e.code}"
        except Exception as e:  # network failure is not the same as "missing"
            return f"error: {e}"
    return "missing" if saw_404 else "error: no response"


def pick_icon(args):
    if args.icon:
        return args.icon
    if args.kind:
        return KIND_ICONS[args.kind]
    guess = "hl-" + re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")
    res = check_icon(guess)
    if res == "found":
        return guess
    die(f"no icon given and {guess!r} is {res}; pass --icon (hl-/sh-/fas ...) or --kind react|library", 2)


def read(path):
    with open(path) as f:
        return f.read().split("\n")


def bump_chart(chart_path):
    text = open(chart_path).read()
    m = re.search(r"^version: (\d+)\.(\d+)\.(\d+)\s*$", text, re.M)
    if not m:
        die(f"no `version: x.y.z` in {chart_path}")
    new = f"{m.group(1)}.{m.group(2)}.{int(m.group(3)) + 1}"
    return text[: m.start()] + f"version: {new}" + text[m.end():], f"{m.group(0).split(': ')[1].strip()} -> {new}"


def validate(chart_dir):
    """Render the chart for every section-flag combination and sanity check the rendered conf.yml."""
    if not shutil.which("helm"):
        print("warning: helm not installed, skipped render validation", file=sys.stderr)
        return
    try:
        import yaml
    except ImportError:
        yaml = None
        print("warning: PyYAML missing, only checking that helm renders", file=sys.stderr)
    for media, apps in itertools.product(("true", "false"), repeat=2):
        cmd = ["helm", "template", "dashy", chart_dir, "--set", f"sections.mediaEnabled={media}",
               "--set", f"sections.appsEnabled={apps}"]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode:
            die(f"helm template failed (media={media}, apps={apps}): {p.stderr.strip()}")
        if not yaml:
            continue
        try:
            docs = [d for d in yaml.safe_load_all(p.stdout) if d]
            cm = next(d for d in docs if d.get("kind") == "ConfigMap")
            conf = yaml.safe_load(cm["data"]["conf.yml"])
            ids = [i["id"] for s in conf["sections"] for i in s["items"]]
            for s in conf["sections"]:
                for i in s["items"]:
                    if not {"title", "url", "icon", "id"} <= set(i):
                        raise ValueError(f"item {i.get('title')!r} is missing a field")
        except Exception as e:
            die(f"rendered conf.yml invalid (media={media}, apps={apps}): {e}")
        if len(ids) != len(set(ids)):
            die(f"duplicate ids in rendered conf.yml (media={media}, apps={apps})")


def commit_edit(path, old_lines, new_lines, args):
    old, new = "\n".join(old_lines), "\n".join(new_lines)
    diff = "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), "a/configmap.yaml", "b/configmap.yaml"))
    chart_path = os.path.join(os.path.dirname(os.path.dirname(path)), "Chart.yaml")
    chart_old = open(chart_path).read()
    chart_new, bump = bump_chart(chart_path)
    sys.stdout.write(diff or "(no changes)\n")
    print(f"Chart.yaml version {bump}")
    if args.dry_run or not diff:
        print("dry run: nothing written" if args.dry_run else "")
        return
    open(path, "w").write(new)
    open(chart_path, "w").write(chart_new)
    if not args.no_validate:
        try:
            validate(os.path.dirname(chart_path))
        except SystemExit:
            open(path, "w").write(old)
            open(chart_path, "w").write(chart_old)
            print("restored configmap.yaml and Chart.yaml", file=sys.stderr)
            raise
    print("written. Commit in home-kubernetes (separate repo): git -C home-kubernetes diff")


def cmd_list(args):
    lines = read(args.file)
    for sec in parse(lines):
        if args.section and sec.name.lower() != args.section.lower():
            continue
        print(f"{sec.name}  (charSum {section_num(sec.name)}, {len(sec.items)} items)")
        for idx, it in enumerate(sec.items):
            blk = lines[it.start:it.end]
            id_ = next((ID_RE.match(l).group(0).split("id: ")[1] for l in blk if ID_RE.match(l)), "?")
            icon = next((l.split("icon: ", 1)[1] for l in blk if l.strip().startswith("icon:")), "?")
            print(f"  {idx}. {it.title:<22} {icon:<20} {id_}")


def cmd_add(args):
    lines = read(args.file)
    old = list(lines)
    sections = parse(lines)
    sec = find_section(sections, args.section)
    for s in sections:
        if any(i.title.lower() == args.title.lower() for i in s.items):
            die(f"{args.title!r} already exists in {s.name!r}")
    icon = pick_icon(args)
    res = check_icon(icon)
    if res == "missing":
        die(f"icon {icon!r} not found in the icon repo", 2)
    if res.startswith("error"):
        print(f"warning: could not verify icon {icon!r} ({res})", file=sys.stderr)
    pos = insert_pos(sec, args.after)
    block = [f"          - title: {quote(args.title)}"]
    if args.description:
        block.append(f"            description: {quote(args.description)}")
    block += [f"            icon: {quote(icon)}", f"            url: {quote(args.url)}",
              f"            target: {args.target}", f"            id: 0_{section_num(sec.name)}_{slug(args.title)}"]
    lines[pos:pos] = block
    renumber(lines, sec.name)
    commit_edit(args.file, old, lines, args)


def cmd_remove(args):
    lines = read(args.file)
    old = list(lines)
    sec = find_section(parse(lines), args.section)
    it = find_item(sec, args.title)
    del lines[it.start:it.end]
    renumber(lines, sec.name)
    commit_edit(args.file, old, lines, args)


def cmd_move(args):
    lines = read(args.file)
    old = list(lines)
    sections = parse(lines)
    src = next((s for s in sections if any(i.title.lower() == args.title.lower() for i in s.items)), None)
    if not src:
        die(f"no item {args.title!r} in any section")
    dst = find_section(sections, args.to_section)
    if dst is src:
        die("source and destination sections are the same")
    it = find_item(src, args.title)
    block = lines[it.start:it.end]
    for n, l in enumerate(block):
        m = ID_RE.match(l)
        if m:
            block[n] = f"{m.group(1)}0_{section_num(dst.name)}_{slug(args.title)}"
    del lines[it.start:it.end]
    renumber(lines, src.name)
    dst = find_section(parse(lines), args.to_section)
    pos = insert_pos(dst, args.after)
    lines[pos:pos] = block
    renumber(lines, dst.name)
    commit_edit(args.file, old, lines, args)


def cmd_check_icon(args):
    bad = 0
    for name in args.names:
        res = check_icon(name)
        print(f"{name}: {res}")
        bad |= res != "found" and res != "unverifiable"
    sys.exit(2 if bad else 0)


def main():
    ap = argparse.ArgumentParser(description="Manage Dashy links in the home-kubernetes configmap.")
    ap.add_argument("--file", default=DEFAULT_FILE, help="configmap.yaml (Chart.yaml is expected two dirs up)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def writer(p):
        p.add_argument("--dry-run", action="store_true", help="print the diff only")
        p.add_argument("--no-validate", action="store_true", help="skip helm render validation")

    p = sub.add_parser("list")
    p.add_argument("--section")
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("add")
    p.add_argument("--section", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--icon", help="explicit icon, e.g. hl-plex, sh-dashy, 'fas fa-cog'")
    p.add_argument("--kind", choices=sorted(KIND_ICONS), help="react -> hl-reactjs, library -> hl-npm")
    p.add_argument("--after", help="title of the item to insert after (default: end of section)")
    p.add_argument("--target", default="newtab", choices=["newtab", "sametab", "modal", "workspace"])
    writer(p)
    p.set_defaults(fn=cmd_add)

    p = sub.add_parser("remove")
    p.add_argument("--section", required=True)
    p.add_argument("--title", required=True)
    writer(p)
    p.set_defaults(fn=cmd_remove)

    p = sub.add_parser("move")
    p.add_argument("--title", required=True)
    p.add_argument("--to-section", required=True)
    p.add_argument("--after")
    writer(p)
    p.set_defaults(fn=cmd_move)

    p = sub.add_parser("check-icon")
    p.add_argument("names", nargs="+")
    p.set_defaults(fn=cmd_check_icon)

    args = ap.parse_args()
    if not os.path.isfile(args.file):
        die(f"no such file: {args.file}")
    args.fn(args)


if __name__ == "__main__":
    main()
