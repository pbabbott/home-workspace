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

## Infra / host configuration
Hosts, VMs and k8s nodes in the homelab are configured by Ansible in `home-playbooks/`. Start at
`home-playbooks/README.md` ("Start here"), or go directly to:
- `home-playbooks/docs/HOSTS.md` – which host does what (Proxmox, Pis, NAS, VMs, k8s fleets)
- `home-playbooks/playbooks/README.md` – index of playbooks (DNS, Tailscale, Redis, k8s bootstrap, ...) and their status

Read these before answering ansible or host/VM questions, then the relevant playbook README.
Also see `home-playbooks/CLAUDE.md` (e.g. vault flag `-e @./vault.yml`).
