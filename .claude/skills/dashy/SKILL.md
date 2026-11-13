---
name: dashy
description: Add, remove, move or list links on the Dashy dashboard (the Helm-templated ConfigMap in home-kubernetes). Use when asked things like "add home-hud to my dashy apps", "remove X from dashy", "move Plex to Apps", or "what's on my dashy".
allowed-tools: Read, Bash, Grep
---

The Dashy config is `home-kubernetes/apps/base/platform/dashy/templates/configmap.yaml` (Helm-templated, so not valid
YAML: never round-trip it through a YAML library, never rewrite it by hand). Use the script, run from the workspace root:

```
python3 .claude/skills/dashy/scripts/dashy.py list [--section Apps]
python3 .claude/skills/dashy/scripts/dashy.py add --section Apps --title "Home HUD" --url https://home-hud.abbottland.io \
    --description "Home dashboard" --kind react --after "Diagram Maker"
python3 .claude/skills/dashy/scripts/dashy.py remove --section Apps --title "Home HUD"
python3 .claude/skills/dashy/scripts/dashy.py move --title "Home HUD" --to-section Media [--after Plex]
python3 .claude/skills/dashy/scripts/dashy.py check-icon hl-reactjs sh-dashy
```

Add `--dry-run` first when unsure; it prints the diff and writes nothing. Sections: Central Admin, Cluster Admin, Media, Apps
(`list` shows them with their current items).

## Owner's preferences (apply when choosing arguments)
- **Links open in a new tab** (`target: newtab`, the default). Only Dashy-to-Dashy links use `sametab`.
- **Icons**: prefer `hl-` icons when one exists. React/Next.js site: `--kind react` (`hl-reactjs`). Library or package: `--kind library`
  (`hl-npm`). Otherwise omit `--icon` and the script tries `hl-<title-kebab>` and checks it exists; if not, pick a `sh-` icon (or `fas ...`)
  and pass `--icon` explicitly. Run `check-icon` on a candidate first.
- **Placement**: put the new item next to its siblings (`--after`), e.g. a new web app next to Diagram Maker. Default is the end of the section.
- **URLs are hardcoded** in the configmap (like the existing Apps/Media items); no values.yaml or helmrelease.yaml changes.
- Give a short `--description` in the same style as its neighbours.

## What the script handles for you
- Item `id` mirrors Dashy's own `makeItemId` (`src/utils/config/SectionHelpers.js`): `<index>_<charSum>_<slug>`. Index = position in
  the section (renumbered on every change), charSum = sum of the char codes of the section *name* (Apps = 404), slug = title lowercased
  with everything but letters removed (digits too). Dashy recomputes ids on every load and ignores the file's values, so they only matter
  to keep diffs against UI exports clean. Never edit ids by hand.
- Bumps the `Chart.yaml` patch version (Flux needs it to reconcile), prints the diff, renders the chart with `helm template`
  for all `mediaEnabled`/`appsEnabled` combinations, and restores both files if the render breaks.
- Refuses duplicate titles and unknown sections/items.

## After a change
`home-kubernetes` is a separate git repo: review with `git -C home-kubernetes diff`, then commit/push there (branch + PR per that repo's
rules) only when the user asks. Never commit it to the outer workspace repo. Flux applies it once merged.
