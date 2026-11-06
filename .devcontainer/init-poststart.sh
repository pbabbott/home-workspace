#!/usr/bin/env bash
# Runs on every container start — keep this fast so the IDE does not hang.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "Make git trust workspace directory"
_gitconfig_global_ok() {
  [ -d "$HOME/.gitconfig" ] && return 1
  [ ! -e "$HOME/.gitconfig" ] && return 0
  [ -f "$HOME/.gitconfig" ] && [ -w "$HOME/.gitconfig" ] && return 0
  return 1
}
if _gitconfig_global_ok; then
  git config --global --add safe.directory /workspaces/home-workspace
  git config --global --add safe.directory "/workspaces/home-workspace/*"
  git config --global push.autoSetupRemote true
  git config --global credential.helper store
else
  echo "Skipping git config --global (no writable ~/.gitconfig — using bind-mounted read-only config)"
fi

echo "Creating project aliases"
mkdir -p /home/vscode/.oh-my-zsh/custom
cp .devcontainer/files/aliases.zsh /home/vscode/.oh-my-zsh/custom/home-workspace-aliases.zsh

echo "Setting up starship"
mkdir -p /home/vscode/.config
cp .devcontainer/files/starship.toml /home/vscode/.config/starship.toml

echo "Overwriting .zshrc file"
cp .devcontainer/files/.zshrc /home/vscode/.zshrc

echo "Setting up Turbo remote cache auth"
if [ -f "$REPO_ROOT/home-web-apps/scripts/turbo-auth.sh" ]; then
  (
    cd "$REPO_ROOT/home-web-apps"
    . scripts/turbo-auth.sh 2>/dev/null || true
    if [ -n "${TURBO_TOKEN:-}" ]; then
      printf 'export TURBO_TOKEN="%s"\nexport TURBO_API="%s"\nexport TURBO_TEAM="%s"\n' \
        "$TURBO_TOKEN" "$TURBO_API" "$TURBO_TEAM" > /home/vscode/.turbo-env
      echo "Turbo auth configured"
    else
      echo "Turbo auth skipped (op unavailable or not signed in)"
    fi
  )
else
  echo "Turbo auth skipped (home-web-apps not cloned)"
fi

echo "Configuring Claude"
CLAUDE_JSON="$HOME/.claude.json"
if [ -f "$CLAUDE_JSON" ]; then
  tmp=$(mktemp)
  jq '.hasCompletedOnboarding = true' "$CLAUDE_JSON" > "$tmp" && mv "$tmp" "$CLAUDE_JSON"
else
  printf '{"hasCompletedOnboarding":true}\n' > "$CLAUDE_JSON"
fi
