# Devcontainer Toggles

Goal: keep this devcontainer very easy to spin up. Anything that depends on the host
(mounts, files, env) starts **off** and is toggled on piecemeal when needed.

Update this file whenever something is toggled on or off.

## Host mounts (`devcontainer.json` → `mounts`)

| Mount | Status | Host requirement | Notes |
| --- | --- | --- | --- |
| `~/.gitconfig` → `/home/vscode/.gitconfig` (read-only) | OFF | `~/.gitconfig` must exist | `init-poststart.sh` falls back to writing a container-local global config |
| `~/.claude` → `/home/vscode/.claude` | ON | `~/.claude` must exist | Claude Code auth/settings |
| `~/media` → `/home/vscode/media` | OFF | `~/media` must exist | Container fails to start if missing |
| `~/.ssh` → `/home/vscode/.ssh` | OFF (not yet added) | `~/.ssh` must exist | Source repos: home-playbooks mounted read-write; home-web-apps and home-kubernetes read-only |

## Host files / env

| Item | Status | Host requirement | Notes |
| --- | --- | --- | --- |
| `runArgs: --env-file .devcontainer/.env` | OFF | `.devcontainer/.env` must exist (gitignored) | Create with `cp .devcontainer/devcontainer.env .devcontainer/.env`. Was ON; container failed to start when the file was missing |

## Env vars (`devcontainer.env` template)

| Variable | Status | Notes |
| --- | --- | --- |
| `CLAUDE_CODE_OAUTH_TOKEN` | OFF | Commented out in `devcontainer.env`; re-add when needed. Only takes effect if the `--env-file` runArg is also ON |

## Pending / TODO

- Turbo remote cache auth in `init-poststart.sh` (once home-web-apps is in the workspace).

## Changelog

- 2026-11-05: Commented out `CLAUDE_CODE_OAUTH_TOKEN` in `devcontainer.env`.
- 2026-11-05: Disabled `--env-file` runArg (startup failed: `.devcontainer/.env` missing).
- 2026-11-05: Re-enabled the `.claude` mount.
- 2026-11-05: Commented out `.gitconfig`, `.claude`, and `media` mounts for easier startup.
