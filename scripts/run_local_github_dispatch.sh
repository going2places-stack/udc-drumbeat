#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/clawagent/Documents/ChatGPT/UDC - Drumbeat Posts"
LOG_DIR="$REPO_DIR/logs"
LOCK_DIR="/tmp/udc-drumbeat-gh-dispatch.lock"
REPO="going2places-stack/udc-drumbeat"
WORKFLOW="UDC Evergreen Drumbeat"
GH="/opt/homebrew/bin/gh"

mkdir -p "$LOG_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[$(date)] Another GitHub dispatch run is active; exiting." >> "$LOG_DIR/local-github-dispatch.log"
  exit 0
fi
trap 'rmdir "$LOCK_DIR"' EXIT

cd "$REPO_DIR"

{
  echo "[$(date)] Triggering GitHub workflow dispatch for $WORKFLOW."
  "$GH" workflow run "$WORKFLOW" --repo "$REPO" -f dry_run=0 -f platforms= -f allow_partial=0
  echo "[$(date)] Dispatch submitted."
} >> "$LOG_DIR/local-github-dispatch.log" 2>&1
