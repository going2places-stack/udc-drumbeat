#!/usr/bin/env bash
set -euo pipefail

LABEL="com.unofficialdc.drumbeat.github-dispatch"
REPO_DIR="/Users/clawagent/Documents/ChatGPT/UDC - Drumbeat Posts"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
RUNNER="$REPO_DIR/scripts/run_local_github_dispatch.sh"

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$RUNNER</string>
  </array>
  <key>StartCalendarInterval</key>
  <array>
    <dict>
      <key>Hour</key>
      <integer>9</integer>
      <key>Minute</key>
      <integer>20</integer>
    </dict>
    <dict>
      <key>Hour</key>
      <integer>9</integer>
      <key>Minute</key>
      <integer>35</integer>
    </dict>
    <dict>
      <key>Hour</key>
      <integer>9</integer>
      <key>Minute</key>
      <integer>50</integer>
    </dict>
    <dict>
      <key>Hour</key>
      <integer>10</integer>
      <key>Minute</key>
      <integer>15</integer>
    </dict>
  </array>
  <key>StandardOutPath</key>
  <string>$REPO_DIR/logs/github-dispatch.out.log</string>
  <key>StandardErrorPath</key>
  <string>$REPO_DIR/logs/github-dispatch.err.log</string>
  <key>WorkingDirectory</key>
  <string>$REPO_DIR</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
PLIST

chmod +x "$RUNNER"
plutil -lint "$PLIST"

launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl enable "gui/$(id -u)/$LABEL"

echo "Installed $LABEL at $PLIST"
echo "Logs:"
echo "  $REPO_DIR/logs/local-github-dispatch.log"
echo "  $REPO_DIR/logs/github-dispatch.out.log"
echo "  $REPO_DIR/logs/github-dispatch.err.log"
