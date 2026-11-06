# Devcontainer

Superset of the devcontainers from `home-web-apps`, `home-playbooks` and `home-kubernetes`.

For the host-dependent items (mounts, env file) and whether each is on or off, see [TOGGLES.md](TOGGLES.md).

## Tools

Node 22 + pnpm 10.15.0, Docker-in-Docker (buildx), kubectl, helm, minikube, kubectx/kubens, k9s, flux, flux-operator (v0.45.1), kubeseal, istioctl (1.25.2), skaffold, terraform, ansible + ansible-lint + pre-commit, Go, uv, yq (v4.44.1), 1Password CLI, GitHub CLI, Claude Code, starship, ffmpeg, smbclient.

## Env

`devcontainer.env` is the template; copy it to `.env` (gitignored) and fill in the secrets.

## Lifecycle

**On create** (`init-postcreate.sh`, once):

- Clones oh-my-zsh plugins (autosuggestions, you-should-use, kubectl-prompt).
- Sets up the docker buildx builder and installs binfmt for cross-platform builds.
- Installs `flux-operator` and `flux-operator-mcp` (default v0.45.1, override with `FLUX_OPERATOR_TOOLS_VERSION`).
- Runs `scripts/setup-web-apps.sh` (`pnpm install` + Playwright) if `home-web-apps` is already cloned; otherwise skips it, so run it manually after `scripts/repos.sh`.

**On every start** (`init-poststart.sh`):

- Adds `safe.directory` entries (workspace and nested repos) and a few global git settings, unless `~/.gitconfig` is a read-only bind mount.
- Copies the aliases, starship config and `.zshrc` from `files/` (this overwrites `~/.zshrc`).
- Writes Turbo remote-cache vars to `~/.turbo-env` when `home-web-apps` is cloned and `op` is signed in; skips otherwise.
- Marks Claude Code onboarding as completed in `~/.claude.json`.
