# home-workspace

Tooling hub and entry point for cross-repo work. Three independent git repos are cloned
(gitignored) into this directory by `scripts/repos.sh`. Overview: `README.md`.

## Layout

- `home-web-apps/` – web apps (pnpm/Turbo monorepo)
- `home-playbooks/` – Ansible/Terraform/Packer for hosts, VMs and k3s nodes
- `home-kubernetes/` – Kubernetes/Flux manifests (workloads, DNS, ingress)
- `scripts/` – workspace helpers (below); `.claude/agents`, `.claude/skills` – see Agents and skills

## Hosts (Harry Potter names)
Hosts, VMs and k8s nodes are configured by Ansible/Terraform in `home-playbooks/`. Detail, IPs and
current state live in **`home-playbooks/docs/HOSTS.md` – read before answering host/VM questions** (keep it updated, not this list).

- Proxmox: `hogwarts` (primary, gen3), `chimaera` (reinstalled 2026-11-10; gen2 VMs destroyed; gen3 controller-3 + worker-3)
- `room_of_requirement` (Asustor NAS: Redis, Postgres, NFS, media), `bananapi` (Pi-hole DNS, Tailscale),
  `dumbledore` (Raspberry Pi 4, ARM/quorum node, offline), `elder_wand` (Windows gaming PC),
  `marauders_map` (dev VM), `eero` (router)
- `home_assistant` (192.168.4.37:8123): not Ansible-managed; proxied publicly via k8s `home-assistant` ns
- `tf-*-k3s-*`: gen3 k3s VMs; "controller1"/"worker3" mean these
- HAProxy LXCs: `.29` gen3 = public + LAN ingress since 2026-11-09; `.28` gen2 stopped 2026-11-09, awaiting removal

## Playbooks
**Read `home-playbooks/README.md` ("Start here"), then `home-playbooks/playbooks/README.md` (index + status) before ansible questions**,
then the relevant playbook README and `home-playbooks/CLAUDE.md` (e.g. vault flag `-e @./vault.yml`).
Dirs: `kubernetes-gen3/` (k3s + Flux), `dns/`, `tailscale/`, `redis/`, `prometheus/`, `workstation/`,
`hogwarts-shutdown/` and `chimaera-shutdown/` (clean power-off + restart), `ansible-template-ubuntu-noble/` (VM template).
History / unfinished, don't use unless asked: `kubernetes-gen2/` (retired), `proxmox-chimaera/` (obsolete except SSD power rule), `host_updates/`, `pironman/`, `ping/`.

## Kubernetes (`home-kubernetes/`)
Flux GitOps for the live `prod-gen3` k3s cluster (nodes are built by `home-playbooks/`, workloads come from here).
**Read `home-kubernetes/CLAUDE.md` before changing anything: it holds the infra overview, full workload index, agents and doc map.**
Layout: `clusters/prod-gen3/` (Flux entry points), `crds/`, `infra/` and `apps/` (each `base/` + `prod-gen3/` overlay, `<category>/<name>`), `docs/`.

- Apps by name: `ci-registry/` (arc CI runners, harbor), `public-sites/` (blog, home-hud, umami, fui-components, diagram-maker),
  `media/` (sonarr, radarr, prowlarr, qbittorrent, plex), `host-proxies/` (routes in front of `asustor`, `haproxy`, `home-assistant`, `proxmox`),
  `dev-ai/` (coder, openclaw, mcp-grafana), `platform/` (dashy, flux-gitops, podinfo)
- Infra: istio (ingress; Gateways `istio-ingress` = `*.local.abbottland.io`, `istio-ingress-public` = `*.abbottland.io`), external-dns (Cloudflare public, Pi-hole internal; never hand-create records),
  cert-manager, longhorn (app data) + `nas-storage` (NFS on `room_of_requirement`), 1Password operator (secrets), kube-prometheus-stack (Grafana)
- Agents (in `home-kubernetes/.claude/agents/`): `flux-recover`, `istio-debug`, `longhorn-ops`, `secrets-ops`, `arc-debug`, `media-debug`; add an app with the `flux-app-add` skill
- Docs to start from: `home-kubernetes/docs/ai-reference/` (`secrets.md` for anything secret, `gen3-manual-steps.md` for node changes, `httproute-dns.md` for exposing an app)
- Cluster access: `scripts/get-kubeconfig.sh` below, then plain `kubectl`/`flux` (no ssh). `ImageUpdateAutomation` is running (resumed 2026-11-11, #39); don't hand-edit image tags it manages (see `home-kubernetes/CLAUDE.md`).

## Web apps (`home-web-apps/`)
TypeScript monorepo (pnpm workspaces + Turborepo): the apps that `home-kubernetes` deploys, built into images pushed to Harbor.
**Read `home-web-apps/CLAUDE.md` before changing anything: it holds the app/package index, dev guides (`docs/dev-guide-*.md`, `docs/test-guide-*.md`) and restrictions.**

- `apps/` by name: `blog`, `diagram-maker`, `home-hud` (Next.js frontends, public via `public-sites/` in k8s); `gluetun-sync` (qBittorrent port sync for the `media` VPN),
  `pi-led-api`, `video-api` + `video-worker`, `homelab-api` (Exodus Windows-to-NAS migration, Postgres on `room_of_requirement`), `backup-worker`, `harbor-cleanup`
- `packages/`: shared libs (`express`, `yaml-config`, `logger`, `next-middleware`, `fui-components` React lib + Storybook, `fui-icons`), DB layers (`homelab-db`, `video-db`, Drizzle),
  `source-access` (SMB driver), configs (`eslint-config`, `jest-presets`, `typescript-config`), `abctl` (CLI for Docker builds/secrets), base images `node-22-alpine`/`node-22-dev`
- CI: `.github/workflows/ci.yml` runs on PRs to `main` on self-hosted `prod-gen3-amd64-runner` pods (the `arc` workload in k8s): lint, format, build, docker-build (`sha-<sha7>` images), unit/integration/smoke/UI tests, Trivy scan, then `deploy-blog-preview`.
  `docker-publish.yml` retags to a production tag on push to `main`; `pr-teardown.yml` removes the preview namespace. Conventions (one 1Password secret, logic in `scripts/` not YAML): `home-web-apps/.github/CLAUDE.md`.
- Never run Playwright snapshot (UI screenshot) tests locally. Setup: `scripts/setup-web-apps.sh`; run pnpm/turbo from inside `home-web-apps/`.
- New image to deploy: the app lives here, the manifests in `home-kubernetes/apps/` (`flux-app-add` skill).

## Scripts
- `scripts/repos.sh` – clones missing repos; `--status` for a cross-repo overview.
- `scripts/setup-web-apps.sh` – pnpm install + Playwright browsers for `home-web-apps` (safe to re-run).
- `scripts/get-kubeconfig.sh [prod-gen2|prod-gen3]` – merges controller kubeconfigs into `~/.kube/config` (context = cluster label). New clusters go in its `CLUSTERS` array; `prod-gen2` is retired.

## Agents and skills
- `dns-expert` agent – how a hostname resolves (Cloudflare vs Pi-hole), exposing apps, drafting DNS entries.
- Repo-specific agents and skills live in each repo's own `.claude/` (e.g. the Kubernetes ones above).
- `claude-md` skill – create/update any CLAUDE.md in the workspace or home-* repos.

## Rules
- Each subdirectory is its own repo with its own branches and remotes. Commit and push per repo
  (`git -C home-kubernetes ...`); never commit their contents to this outer repo.
- Run repo tooling (pnpm, turbo, pre-commit, ansible) from inside the relevant repo, not the root.
- Read each repo's own README/CLAUDE.md before changing it.
- Keep this file current: when you add, remove or rename a host, playbook dir, k8s workload or category, web app or package, workflow, script, agent or skill in any repo, update the matching by-name list here in the same piece of work (use the `claude-md` skill). Names and roles only; detail stays in the owning repo's docs.
