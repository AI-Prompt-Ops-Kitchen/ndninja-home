#!/usr/bin/env bash
# Rasengan Phase 4 — Install git hooks and deploy wrapper
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="${SCRIPT_DIR}/hooks"
GIT_HOOKS_DIR="${HOME}/.git/hooks"
LOCAL_BIN="${HOME}/.local/bin"

echo "=== Rasengan Phase 4: CI/CD Hooks Installer ==="
echo

# 1. Install git hooks to home repo
if [ -d "${HOME}/.git" ]; then
  mkdir -p "${GIT_HOOKS_DIR}"

  for hook in post-commit pre-push; do
    src="${HOOKS_DIR}/${hook}"
    dst="${GIT_HOOKS_DIR}/${hook}"
    if [ -f "$src" ]; then
      cp "$src" "$dst"
      chmod +x "$dst"
      echo "[OK] Installed ${hook} → ${dst}"
    else
      echo "[SKIP] ${src} not found"
    fi
  done
else
  echo "[SKIP] No ~/.git directory found"
fi

echo

# 2. Symlink deploy-hook.sh to ~/.local/bin/rasengan-deploy
mkdir -p "${LOCAL_BIN}"
DEPLOY_SRC="${SCRIPT_DIR}/deploy-hook.sh"
DEPLOY_DST="${LOCAL_BIN}/rasengan-deploy"

if [ -f "$DEPLOY_SRC" ]; then
  chmod +x "$DEPLOY_SRC"
  ln -sf "$DEPLOY_SRC" "$DEPLOY_DST"
  echo "[OK] Linked rasengan-deploy → ${DEPLOY_DST}"
else
  echo "[SKIP] ${DEPLOY_SRC} not found"
fi

echo
echo "=== Installation complete ==="
echo
echo "Git hooks installed to: ${GIT_HOOKS_DIR}/"
echo "Deploy wrapper: rasengan-deploy <service> <script> [args...]"
echo
echo "Test with:"
echo "  git commit --allow-empty -m 'test: rasengan phase 4'"
echo "  rasengan-deploy test echo 'hello deploy'"
