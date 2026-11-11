#!/usr/bin/env bash
set -euo pipefail
umask 077
LABEL="com.unofficialdc.drumbeat.local-publish"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME="$HOME/Library/Application Support/UDC Drumbeat"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$RUNTIME/scripts" "$RUNTIME/logs" "$RUNTIME/data" "$HOME/Library/LaunchAgents"
chmod 700 "$RUNTIME"
cp "$SOURCE_DIR/post_today.py" "$SOURCE_DIR/publishing_state.py" "$SOURCE_DIR/evergreen_queue.py" "$RUNTIME/"
cp "$SOURCE_DIR/data/approved_evergreen.json" "$RUNTIME/data/"
cp "$SOURCE_DIR/scripts/run_local_publish.sh" "$RUNTIME/scripts/"
cp "$SOURCE_DIR/.env" "$RUNTIME/.env"
chmod 600 "$RUNTIME/.env"
chmod 700 "$RUNTIME/scripts/run_local_publish.sh"
if [ ! -x "$RUNTIME/.venv/bin/python" ]; then
  /opt/homebrew/bin/python3 -m venv "$RUNTIME/.venv"
fi
"$RUNTIME/.venv/bin/python" -m pip install -q -r "$SOURCE_DIR/requirements.txt"

/usr/bin/python3 - "$PLIST" "$LABEL" "$RUNTIME" <<'PY'
import plistlib, sys
path, label, runtime = sys.argv[1:]
data = {
    'Label': label,
    'ProgramArguments': ['/bin/bash', runtime + '/scripts/run_local_publish.sh'],
    'WorkingDirectory': runtime,
    'EnvironmentVariables': {'PATH': '/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin'},
    'StartCalendarInterval': [{'Hour': 9, 'Minute': m} for m in (0, 5, 15, 30)],
    'StandardOutPath': runtime + '/logs/launchd.out.log',
    'StandardErrorPath': runtime + '/logs/launchd.err.log',
    'RunAtLoad': False,
}
with open(path, 'wb') as f:
    plistlib.dump(data, f)
PY
plutil -lint "$PLIST"
launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl enable "gui/$(id -u)/$LABEL"

# GitHub's native schedule is the independent backup; retire the broken bridge.
BRIDGE="com.unofficialdc.drumbeat.github-dispatch"
launchctl bootout "gui/$(id -u)/$BRIDGE" >/dev/null 2>&1 || true
launchctl disable "gui/$(id -u)/$BRIDGE"
echo "Installed $LABEL. Runtime and logs: $RUNTIME"
