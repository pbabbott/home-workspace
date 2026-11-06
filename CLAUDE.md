# home-workspace

Tooling hub and entry point for cross-repo work. Three independent git repos are cloned
(gitignored) into this directory by `scripts/repos.sh`:

- `home-web-apps/` – web apps (pnpm/Turbo monorepo)
- `home-playbooks/` – Ansible/Terraform playbooks
- `home-kubernetes/` – Kubernetes/Flux manifests

## Rules
- Each subdirectory is its own repo with its own branches and remotes. Commit and push per repo
  (`git -C home-kubernetes ...`); never commit their contents to this outer repo.
- Run repo tooling (pnpm, turbo, pre-commit, ansible) from inside the relevant repo, not the root.
- Read each repo's own README/CLAUDE.md before changing it.
- Use `scripts/repos.sh --status` for a cross-repo overview; `scripts/repos.sh` clones missing repos.
