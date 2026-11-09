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
- `home-playbooks/docs/HOSTS.md` – which host does what. Hosts have Harry Potter names; look here when one comes up:
  `chimaera` (Proxmox, runs prod gen2 k8s), `hogwarts` (new primary Proxmox, gen3), `room_of_requirement` (Asustor NAS: Redis, Postgres, NFS, media),
  `bananapi` (Pi-hole DNS, Tailscale), `dumbledore` (Raspberry Pi 4, ARM/quorum node, offline), `elder_wand` (Windows gaming PC),
  `marauders_map` (dev VM), `home_assistant` (192.168.4.37:8123, not Ansible-managed; proxied publicly via k8s `home-assistant` ns), `eero` (router), `tf-*-k8s-*` (k8s VMs), HAProxy LXCs (ingress: `.29` gen3 = public + LAN since 2026-11-09, `.28` gen2 = LAN only, retiring)
- `home-playbooks/playbooks/README.md` – index of playbooks and their status. Dirs: `kubernetes-gen2/` (k8s bootstrap + Flux), `dns/` (Pi-hole),
  `tailscale/` (remote access), `redis/` (NAS), `prometheus/` (host exporters), `workstation/` (dev VM), `ansible-template-ubuntu-noble/` (VM template),
  `proxmox-chimaera/` (disk tuning); unfinished/legacy: `shutdown/`, `host_updates/`, `pironman/`, `ping/`

Read these before answering ansible or host/VM questions, then the relevant playbook README.
Also see `home-playbooks/CLAUDE.md` (e.g. vault flag `-e @./vault.yml`).

## Cluster access
`scripts/get-kubeconfig.sh [prod-gen2|prod-gen3]` merges controller kubeconfigs into `~/.kube/config` (context names = cluster labels). Add new clusters to the `CLUSTERS` array in that script.
