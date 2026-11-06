# Devcontainer

Superset of the devcontainers from `home-web-apps`, `home-playbooks` and `home-kubernetes`.

For the host-dependent items (mounts, env file) and whether each is on or off, see [TOGGLES.md](TOGGLES.md).

## Tools

Node 22 + pnpm 10.15.0, Docker-in-Docker (buildx), kubectl, helm, minikube, kubectx/kubens, k9s, flux, flux-operator (v0.45.1), kubeseal, istioctl (1.25.2), skaffold, terraform, ansible + ansible-lint + pre-commit, Go, uv, yq (v4.44.1), 1Password CLI, GitHub CLI, Claude Code, starship, ffmpeg, smbclient.

## Env

`devcontainer.env` is the template; copy it to `.env` (gitignored) and fill in the secrets.

## Lifecycle

- **Create:** runs `scripts/setup-web-apps.sh` (`pnpm install` + Playwright) if `home-web-apps` is already cloned.
- **Every start:** sets up Turbo remote-cache auth when `home-web-apps` is present and 1Password (`op`) is signed in.
