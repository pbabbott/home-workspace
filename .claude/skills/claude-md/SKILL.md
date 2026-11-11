---
name: claude-md
description: Create, update or restructure a CLAUDE.md in any of the home-* repos so it follows the owner's conventions (short, link-first, domain facts surfaced by name). Use when asked to update/add/trim/reorganize a CLAUDE.md, to "document X so Claude knows", to onboard a new repo or directory, or after a reorganization that may have left CLAUDE.md paths stale.
allowed-tools: Read, Edit, Write, Bash, Grep, Glob
---

A CLAUDE.md exists for **discoverability**: it is loaded every session, so it must surface the things Claude
cannot guess (names, roles, hard rules) and point at everything else. Gold standards, read them as live examples
before editing: `home-kubernetes/CLAUDE.md` and `home-playbooks/CLAUDE.md` (~90-100 lines each). Full checklist and
templates: `references/patterns.md`.

## Steps

1. **Locate and read.** The target CLAUDE.md (repo root, or a directory's own), the repo `README.md`, and the
   `docs/` layout. Note tool-managed blocks (`<!-- BEGIN:... -->`) and user-authored sections (restrictions, model
   routing): preserve them verbatim.
2. **Classify every piece of content** you are about to add or move:
   - **Domain fact Claude can't guess** (host, workload, script, IP, role, gotcha): keep **inline**, one line: name +
     its role in *this* homelab. This is what lets a prompt like "check my dashy in prod" resolve. Important items get
     their own bullet with a sentence or two (e.g. external-dns); minor ones are listed by name only.
   - **Procedure or convention longer than ~3 lines**: write it to a doc under `docs/` (extend an existing doc first;
     follow the repo's doc folders/naming) and leave a one-line pointer: `` `docs/x.md` — what it covers and when to read it``.
   - **Catalogue** (scripts, apps): a manifest table in the directory's own CLAUDE.md, or a by-name list at root.
   - **Strict rule for one directory**: state it explicitly in that directory's own CLAUDE.md. Explicit conventions
     are fine there; that is what scoped files are for.
   - **Generic description of a tool/app Claude already knows**: drop it. Describe the role in this infra instead.
3. **Place it** using the root section order (Layout, domain facts, by-name inventory, Scripts, agents/skills,
   documentation map, rules of the road). Edit in place; never append a near-duplicate. Don't duplicate volatile data
   owned by another doc (IP tables, per-app summaries): name it, point at the owner, say "keep it updated".
4. **Hold the budget.** Root files ~100 lines (warn above ~120); nested files ~40 unless they are a manifest. Over
   budget means extract detail to `docs/`, not delete the pointer.
5. **Keep related files in sync** in the same change: the README counterpart, manifests/inventories the file lists,
   docs folder maps. If you introduce a "keep X in sync with Y" rule, offer an enforcement hook (precedent:
   `scripts/check-manifest.sh` + `.pre-commit-config.yaml` in home-kubernetes and home-playbooks).
6. **Verify**, then fix real problems:
   `.claude/skills/claude-md/scripts/check-claude-md.py <file> [--names a,b,c]` (run from the workspace root)
   reports size, headings, backticked paths/links that don't exist, and required names missing from the text. Pass
   `--names` with the workloads/hosts/scripts the change touched. Paths that are intentionally gone (history notes) or
   generated (`dist/`) are expected hits; judge them.
7. **Report tersely**: which CLAUDE.md changed, which doc received the detail, anything you deliberately left alone.

## Rules

- Never write long-form procedure, examples or rationale into a CLAUDE.md; extract it.
- Every path, command and name in the file must exist; stale references are worse than none. Re-run the checker after
  any reorganization.
- Imperative one-liners for hard rules (Never/Do not) with the reason; destructive operations name the exact script/host.
- Bold the "read before X" docs and name the trigger situation.
- Fence off history (archived/retired things get one line: "history, don't restore unless asked"); no meta
  instructions like "Be brief".
- A new directory CLAUDE.md is welcome when a directory needs strict conventions; give it a one-line pointer from the
  parent file. Pick the nested template in `references/patterns.md`.
- Don't touch other repos' files unless asked; each repo commits separately (see the workspace `CLAUDE.md`).
