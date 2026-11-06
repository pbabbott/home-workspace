# home-workspace

Workspace for my home projects. It is the entry point for cross-repo work on:

- `home-web-apps/` – web apps (pnpm/Turbo monorepo)
- `home-playbooks/` – Ansible/Terraform playbooks
- `home-kubernetes/` – Kubernetes/Flux manifests

Each is its own git repo, cloned (gitignored) into this directory.

## Getting started

1. `cp .devcontainer/devcontainer.env .devcontainer/.env` and fill in the secrets (`.env` is gitignored).
2. Reopen the folder in the container (see [.devcontainer/README.md](.devcontainer/README.md)).
3. `scripts/repos.sh` to clone the three repos. `--pull` fast-forwards them, `--status` summarizes them.
4. `scripts/setup-web-apps.sh` to run `pnpm install` + Playwright for `home-web-apps`.
