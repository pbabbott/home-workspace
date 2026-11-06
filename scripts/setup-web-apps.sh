#!/usr/bin/env bash
# Install home-web-apps dependencies and Playwright browsers. Safe to re-run.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/home-web-apps"
echo "Installing dependencies"
pnpm install
echo "Installing Playwright browsers and system dependencies"
pnpm --filter @abbottland/fui-components exec playwright install --with-deps chromium
