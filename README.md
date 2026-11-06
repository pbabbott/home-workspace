# home-workspace

Workspace for my home projects.

## Devcontainer

`.devcontainer/` is the superset of the devcontainers from `home-web-apps`, `home-playbooks` and `home-kubernetes`.

**Tools:** Node 22 + pnpm 10.15.0, Docker-in-Docker (buildx), kubectl, helm, minikube, kubectx/kubens, k9s, flux, flux-operator (v0.45.1), kubeseal, istioctl (1.25.2), skaffold, terraform, ansible + ansible-lint + pre-commit, Go, uv, yq (v4.44.1), 1Password CLI, GitHub CLI, Claude Code, starship, ffmpeg, smbclient.

**Setup:**

1. `cp .devcontainer/devcontainer.env .devcontainer/.env` and fill in the secrets (`.env` is gitignored).
2. Make sure `~/media` exists on the host (it is bind-mounted).
3. Reopen the folder in the container.

**Repos:** run `scripts/repos.sh` to clone `home-web-apps`, `home-playbooks` and `home-kubernetes` into this directory (gitignored; each keeps its own git history). `--pull` fast-forwards them, `--status` summarizes them.

**Not done yet:**

- The `~/.ssh` bind mount (omitted on purpose, see the comment in `devcontainer.json`).
- `pnpm install` / Playwright setup and Turbo remote-cache auth (need `home-web-apps` present; see TODOs in the init scripts).
