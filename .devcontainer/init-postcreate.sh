#!/usr/bin/env bash
# Runs once when the dev container is created (not on every open).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "Fetching oh-my-zsh plugins"
ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
export GIT_TERMINAL_PROMPT=0
_plugins=(
  "https://github.com/zsh-users/zsh-autosuggestions|${ZSH_CUSTOM}/plugins/zsh-autosuggestions"
  "https://github.com/MichaelAquilina/zsh-you-should-use.git|${ZSH_CUSTOM}/plugins/you-should-use"
  "https://github.com/superbrothers/zsh-kubectl-prompt.git|${ZSH_CUSTOM}/plugins/zsh-kubectl-prompt"
)
for _pair in "${_plugins[@]}"; do
  IFS='|' read -r _url _dest <<<"$_pair"
  [ -d "$_dest" ] || git clone --depth 1 "$_url" "$_dest"
done
unset _pair _url _dest _plugins

echo "Setting up docker buildx"
if ! docker buildx inspect mybuilder > /dev/null 2>&1; then
  docker buildx create --use --name mybuilder --driver docker-container
else
  docker buildx use mybuilder
fi

echo "Installing binfmt for cross-platform builds"
docker run --privileged --rm tonistiigi/binfmt --install all

# Flux Operator CLI + flux-operator-mcp (pin to match cluster charts; override via FLUX_OPERATOR_TOOLS_VERSION)
FLUX_OPERATOR_TOOLS_VERSION="${FLUX_OPERATOR_TOOLS_VERSION:-v0.45.1}"
FO_VER="${FLUX_OPERATOR_TOOLS_VERSION#v}"
case "$(uname -m)" in
  x86_64) FO_ARCH=amd64 ;;
  aarch64) FO_ARCH=arm64 ;;
  *)
    echo "Skipping flux-operator tools install: unsupported arch $(uname -m)"
    FO_ARCH=""
    ;;
esac
if [ -n "$FO_ARCH" ]; then
  FO_BASE="https://github.com/controlplaneio-fluxcd/flux-operator/releases/download/${FLUX_OPERATOR_TOOLS_VERSION}"
  if [ ! -f /usr/local/bin/flux-operator ]; then
    echo "Installing flux-operator ${FLUX_OPERATOR_TOOLS_VERSION} (${FO_ARCH})"
    curl -fsSL --connect-timeout 15 --max-time 120 "${FO_BASE}/flux-operator_${FO_VER}_linux_${FO_ARCH}.tar.gz" | tar xz -C /tmp
    sudo install -m 0755 "/tmp/flux-operator" /usr/local/bin/flux-operator
    rm -f "/tmp/flux-operator"
  fi
  if [ ! -f /usr/local/bin/flux-operator-mcp ]; then
    echo "Installing flux-operator-mcp ${FLUX_OPERATOR_TOOLS_VERSION} (${FO_ARCH})"
    curl -fsSL --connect-timeout 15 --max-time 120 "${FO_BASE}/flux-operator-mcp_${FO_VER}_linux_${FO_ARCH}.tar.gz" | tar xz -C /tmp
    sudo install -m 0755 "/tmp/flux-operator-mcp" /usr/local/bin/flux-operator-mcp
    rm -f "/tmp/flux-operator-mcp"
  fi
fi

# home-web-apps deps. Repos are cloned manually (scripts/repos.sh), so skip if not present yet;
# re-run `bash scripts/setup-web-apps.sh` after cloning.
if [ -d "$REPO_ROOT/home-web-apps" ]; then
  bash "$REPO_ROOT/scripts/setup-web-apps.sh" || echo "home-web-apps setup failed; re-run scripts/setup-web-apps.sh"
else
  echo "Skipping home-web-apps setup (not cloned; run scripts/repos.sh then scripts/setup-web-apps.sh)"
fi
