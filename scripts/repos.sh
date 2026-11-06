#!/usr/bin/env bash
# Manage the nested sibling repos. Idempotent.
#   scripts/repos.sh            clone any missing repos
#   scripts/repos.sh --pull     also `git pull --ff-only` (skips dirty repos)
#   scripts/repos.sh --status   show branch / ahead-behind / dirty for each
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export GIT_TERMINAL_PROMPT=0

OWNER_URL="https://github.com/pbabbott"
REPOS=(home-web-apps home-playbooks home-kubernetes)

mode="clone"
case "${1:-}" in
  "") ;;
  --pull) mode="pull" ;;
  --status) mode="status" ;;
  *) echo "Usage: $0 [--pull|--status]" >&2; exit 2 ;;
esac

for r in "${REPOS[@]}"; do
  dir="$ROOT/$r"
  if [ ! -d "$dir/.git" ]; then
    if [ "$mode" = "status" ]; then echo "$r: not cloned"; continue; fi
    echo "$r: cloning"
    git clone "$OWNER_URL/$r.git" "$dir"
    continue
  fi
  dirty=""; [ -n "$(git -C "$dir" status --porcelain)" ] && dirty=" (dirty)"
  branch="$(git -C "$dir" rev-parse --abbrev-ref HEAD)"
  case "$mode" in
    status)
      ab="$(git -C "$dir" rev-list --left-right --count '@{u}...HEAD' 2>/dev/null | awk '{print "behind "$1", ahead "$2}')"
      echo "$r: $branch${ab:+ [$ab]}$dirty" ;;
    pull)
      if [ -n "$dirty" ]; then echo "$r: skipped pull$dirty"; else echo "$r: pulling $branch"; git -C "$dir" pull --ff-only; fi ;;
    *) echo "$r: present ($branch)$dirty" ;;
  esac
done
