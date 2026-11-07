#!/usr/bin/env bash
# Fetch kubeconfigs from the cluster controllers over SSH and merge them into ~/.kube/config.
# Adapted from home-web-apps/scripts/get-kube-config-file.sh.
#
#   scripts/get-kubeconfig.sh                 all clusters below
#   scripts/get-kubeconfig.sh prod-gen3       just the named clusters
#   scripts/get-kubeconfig.sh --list          list known clusters
#   KUBE_CONTEXT_AFTER_MERGE=prod-gen2 scripts/get-kubeconfig.sh   (default: first fetched cluster)
#
# Cluster/user/context names are prefixed with the label so merged configs never collide; each
# context is named exactly the label (kubectx-friendly). Existing ~/.kube/config is backed up, and
# contexts of clusters NOT fetched this run are kept.
# yq (mikefarah v4) is used, not kubectl -o json, because kubectl redacts cert data in JSON output.
set -euo pipefail

SSH_USER="${KUBE_SSH_USER:-firebolt}"

# label|host|command that prints the kubeconfig on the controller
CLUSTERS=(
  "prod-gen2|192.168.6.24|cat ~/.kube/config"
  "prod-gen3|192.168.6.41|sudo cat /etc/rancher/k3s/k3s.yaml"
  # "nonprod-gen2|192.168.6.31|cat ~/.kube/config"   # powered off
)

die() { echo "error: $*" >&2; exit 1; }
TMP=()
trap 'for f in "${TMP[@]:-}"; do [[ -n "$f" ]] && rm -f -- "$f"; done' EXIT

command -v yq >/dev/null || die "yq (mikefarah v4) is required"
command -v kubectl >/dev/null || die "kubectl is required"

if [[ "${1:-}" == "--list" ]]; then
  for c in "${CLUSTERS[@]}"; do IFS='|' read -r l h _ <<<"$c"; echo "$l ($h)"; done
  exit 0
fi

want=("$@")
selected=()
for c in "${CLUSTERS[@]}"; do
  IFS='|' read -r label _ <<<"$c"
  if ((${#want[@]} == 0)); then selected+=("$c"); continue; fi
  for w in "${want[@]}"; do [[ "$w" == "$label" ]] && selected+=("$c"); done
done
((${#selected[@]} > 0)) || die "no matching clusters (see --list)"

mkdir -p "$HOME/.kube"
dest="$HOME/.kube/config"
[[ -f "$dest" ]] && cp -a "$dest" "${dest}.bak.$(date +%Y%m%d%H%M%S)"

fetched=()
first=""
for c in "${selected[@]}"; do
  IFS='|' read -r label host cmd <<<"$c"
  [[ -n "$first" ]] || first="$label"
  raw="$(mktemp)"; out="$(mktemp)"; TMP+=("$raw" "$out")
  echo "fetching ${SSH_USER}@${host} -> context ${label}"
  ssh -o BatchMode=yes -o ConnectTimeout=10 "${SSH_USER}@${host}" "$cmd" >"$raw"
  # k3s writes https://127.0.0.1:6443; point it at the controller.
  sed -i "s#https://127\.0\.0\.1:#https://${host}:#" "$raw"
  [[ "$(yq e '.contexts | length' "$raw")" -gt 0 ]] || die "no contexts in kubeconfig from $host"
  export MYPREFIX="$label"
  yq e '
    .clusters |= map(.name = strenv(MYPREFIX) + "-" + .name) |
    .users |= map(.name = strenv(MYPREFIX) + "-" + .name) |
    .contexts |= map(
      .context |= (.cluster = strenv(MYPREFIX) + "-" + .cluster | .user = strenv(MYPREFIX) + "-" + .user) |
      .name = strenv(MYPREFIX)) |
    .current-context = strenv(MYPREFIX)
  ' "$raw" >"$out"
  fetched+=("$out")
done

# Keep other clusters' entries from the existing config; fresh fetches win (listed first).
files=("${fetched[@]}")
if [[ -f "$dest" ]]; then
  old="$(mktemp)"; TMP+=("$old")
  cp "$dest" "$old"
  for c in "${selected[@]}"; do
    IFS='|' read -r label _ <<<"$c"
    export MYPREFIX="$label"
    yq e -i '
      .clusters |= map(select(.name | test("^" + strenv(MYPREFIX) + "-") | not)) |
      .users |= map(select(.name | test("^" + strenv(MYPREFIX) + "-") | not)) |
      .contexts |= map(select(.name != strenv(MYPREFIX)))
    ' "$old"
  done
  files+=("$old")
fi

new="$HOME/.kube/config.new.$$"; TMP+=("$new")
KUBECONFIG="$(IFS=:; echo "${files[*]}")" kubectl config view --flatten >"$new"
chmod 600 "$new"
mv "$new" "$dest"
echo "wrote $dest (contexts: $(kubectl config get-contexts -o name | paste -sd, -))"
kubectl config use-context "${KUBE_CONTEXT_AFTER_MERGE:-$first}"
