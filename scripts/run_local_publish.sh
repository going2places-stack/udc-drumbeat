#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/clawagent/Documents/ChatGPT/UDC - Drumbeat Posts"
LOG_DIR="$REPO_DIR/logs"
ENV_FILE="$REPO_DIR/.env"
LOCK_DIR="/tmp/udc-drumbeat-local.lock"
PYTHON="$REPO_DIR/.venv/bin/python"

mkdir -p "$LOG_DIR"

DRY_RUN_OVERRIDE="${DRY_RUN-}"
ALLOW_PARTIAL_OVERRIDE="${ALLOW_PARTIAL-}"
PLATFORMS_OVERRIDE_OVERRIDE="${PLATFORMS_OVERRIDE-}"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[$(date)] Another local publish run is active; exiting." >> "$LOG_DIR/local-publish.log"
  exit 0
fi
trap 'rmdir "$LOCK_DIR"' EXIT

cd "$REPO_DIR"

if [ ! -f "$ENV_FILE" ]; then
  echo "[$(date)] Missing $ENV_FILE. Local publish cannot run." >> "$LOG_DIR/local-publish.log"
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

if [ -n "$DRY_RUN_OVERRIDE" ]; then
  DRY_RUN="$DRY_RUN_OVERRIDE"
fi
if [ -n "$ALLOW_PARTIAL_OVERRIDE" ]; then
  ALLOW_PARTIAL="$ALLOW_PARTIAL_OVERRIDE"
fi
if [ -n "$PLATFORMS_OVERRIDE_OVERRIDE" ]; then
  PLATFORMS_OVERRIDE="$PLATFORMS_OVERRIDE_OVERRIDE"
fi

export DRY_RUN="${DRY_RUN:-0}"
export ALLOW_PARTIAL="${ALLOW_PARTIAL:-0}"
export PLATFORMS_OVERRIDE="${PLATFORMS_OVERRIDE:-}"

{
  echo "[$(date)] Starting local publish. DRY_RUN=$DRY_RUN ALLOW_PARTIAL=$ALLOW_PARTIAL PLATFORMS_OVERRIDE=$PLATFORMS_OVERRIDE"
  set +e
  "$PYTHON" post_today.py
  result=$?
  set -e
  echo "[$(date)] post_today.py exited with $result"

  today="$(TZ=America/New_York date +%F)"
  if [ "$DRY_RUN" != "1" ] && [ -f "posted/$today.md" ]; then
    git add "posted/$today.md" || true
    git diff --cached --quiet || git commit -m "archive: $today"
    git push || true
  fi

  exit "$result"
} >> "$LOG_DIR/local-publish.log" 2>&1
