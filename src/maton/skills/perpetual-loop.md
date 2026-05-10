# The Perpetual Loop

Architecture for autonomous, continuous maton operation.

This document is written for LLM agents. If you are an LLM being asked to set up a perpetual loop for a maton, this document tells you everything you need to know. If the target platform is not macOS, read the Platform Implementations section and adapt.

---

## Overview

A maton's perpetual loop has three components:

1. **The Hitch** — an OS-native scheduler that invokes the maton repeatedly
2. **The Dispatcher** — a skill (`skills/dispatch.md`) that finds and executes the next unit of work
3. **The State** — structured YAML files (`backlog.yaml`, `schedule.yaml`, `guardrails.yaml`) that the dispatcher reads and writes

The loop: hitch fires → dispatcher reads state → picks a task → executes → updates state → decides whether to self-reschedule → exits.

---

## The Hitch

The hitch is the mechanism that causes the dispatcher to run. It has three behaviors:

### 1. Self-Rescheduling

When the dispatcher finishes and wants to run again immediately (e.g., more tasks in the backlog), it touches a **trigger file**:

```bash
touch ~/.maton/hitch/trigger
```

The hitch watches this file. When it changes, the dispatcher is invoked again.

### 2. Deadman Timer

A fixed-interval timer (default: 10 minutes) fires the dispatcher regardless of the trigger file. This catches:

- Dispatcher crashed before touching trigger
- Dispatcher hung and was killed by timeout
- Trigger file mechanism failed for any reason

The deadman timer is a safety net, not the primary scheduling mechanism.

### 3. External Triggering

Any program — a cron job, a webhook handler, a human typing a command — can trigger the dispatcher by touching the trigger file:

```bash
touch ~/.maton/hitch/trigger
```

This is the universal interface. No API, no IPC, no sockets. A file touch.

### How They Work Together

| Scenario | What Happens |
|---|---|
| Dispatcher finishes, has more work | Touches trigger → runs again immediately |
| Dispatcher finishes, no more work | Does NOT touch trigger → deadman fires in ≤10 min |
| Dispatcher crashes mid-task | Lock file has stale PID → deadman fires → new run starts |
| External program wants immediate run | Touches trigger → runs within seconds |
| Machine was asleep, wakes up | Deadman timer fires → dispatcher checks for work |

---

## The Runner

The runner is a shell script that sits between the hitch and the dispatcher. It handles:

- **Locking**: prevents concurrent dispatcher runs
- **Lock recovery**: detects stale locks from crashed processes
- **Trigger cleanup**: clears the trigger file at start (we're running now)
- **Driver invocation**: calls the LLM driver (e.g., OpenCode) with the dispatcher prompt
- **Logging**: timestamps to a log file

### Reference Implementation (bash)

```bash
#!/bin/bash
set -euo pipefail

# === Configuration ===
# Adapt these paths to your maton instance.
MATON_HOME="$HOME/.maton"
HITCH_DIR="$MATON_HOME/hitch"
INSTANCE_DIR="$MATON_HOME/matons/liftomaton"  # ← your instance name
LOCK_FILE="$HITCH_DIR/lock"
TRIGGER_FILE="$HITCH_DIR/trigger"
LOG_FILE="$HITCH_DIR/runner.log"
MAX_RUNTIME=300  # seconds — kill the driver if it exceeds this

log() { echo "$(date -Iseconds) $1" >> "$LOG_FILE"; }

# === Lock ===
if [ -f "$LOCK_FILE" ]; then
    pid=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        log "SKIP: already running (PID $pid)"
        exit 0
    fi
    log "WARN: stale lock (PID $pid), reclaiming"
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# === Clear trigger ===
rm -f "$TRIGGER_FILE"

# === Run dispatcher ===
log "START: dispatcher"

timeout "$MAX_RUNTIME" opencode run \
    -q \
    -c "$INSTANCE_DIR" \
    --dangerously-skip-permissions \
    "$(cat "$INSTANCE_DIR/skills/dispatch.md")" \
    || log "WARN: dispatcher exited with code $?"

log "END: dispatcher"
```

### LLM Driver Invocation

The runner invokes the LLM driver non-interactively. The reference implementation uses OpenCode.

#### OpenCode (reference)

```bash
opencode run -q -c "$INSTANCE_DIR" --dangerously-skip-permissions "$(cat dispatch.md)"
```

Flags:
- `run "prompt"` — non-interactive mode, no TUI, execute and exit
- `-q` — suppress spinner (clean for scripts/logs)
- `-c /path` — set working directory to the maton instance
- `--dangerously-skip-permissions` — auto-approve tool use (file writes, git, etc.). Required because non-interactive mode auto-rejects permissions by default. The maton's `guardrails.yaml` serves as the safety layer instead.

Optional:
- `-f json` — JSON output format (useful if you want to parse the response)
- `-m provider/model` — override model (e.g., `-m local-gemma/gemma-4-31b-it`)

#### Performance: warm server mode

To avoid cold-starting MCP servers on every dispatch cycle, run a persistent OpenCode server:

```bash
# Start once (e.g., in the launchd plist as a separate service, or in the runner)
opencode serve --port 4096

# Each dispatch cycle connects to the warm server
opencode run --attach http://localhost:4096 -q --dangerously-skip-permissions "$(cat dispatch.md)"
```

This eliminates MCP initialization overhead (~5-30s per invocation).

#### Known issue: process hanging

Some model/provider combinations cause `opencode run` to hang after completion (OpenCode issue #17516). The `timeout` in the runner script handles this — the process is killed and the deadman timer will retry.

#### Other drivers

| Driver | Non-Interactive Invocation |
|---|---|
| OpenCode | `opencode run -q "prompt"` |
| Claude CLI | `claude -p "prompt"` |
| Direct API | `curl` / Python script calling model API |

If your driver doesn't support non-interactive mode, wrap it: write a small script that reads the dispatcher prompt, calls the model API, and executes the returned actions.

---

## Platform Implementations

### macOS — launchd

launchd is the native macOS scheduler. It supports both timed intervals and file-watch triggers natively.

#### Plist Template

Save to `~/Library/LaunchAgents/com.maton.<instance-name>.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.maton.liftomaton</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/elow/.maton/hitch/runner.sh</string>
    </array>

    <!-- Deadman timer: fire every 600 seconds (10 min) -->
    <key>StartInterval</key>
    <integer>600</integer>

    <!-- Self-reschedule / external trigger: fire when this file is touched -->
    <key>WatchPaths</key>
    <array>
        <string>/Users/elow/.maton/hitch/trigger</string>
    </array>

    <!-- Logging -->
    <key>StandardOutPath</key>
    <string>/Users/elow/.maton/hitch/launchd-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/elow/.maton/hitch/launchd-stderr.log</string>

    <!-- Environment -->
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>HOME</key>
        <string>/Users/elow</string>
    </dict>
</dict>
</plist>
```

#### Installation

```bash
# Create hitch directory
mkdir -p ~/.maton/hitch

# Copy runner.sh and make executable
cp runner.sh ~/.maton/hitch/runner.sh
chmod +x ~/.maton/hitch/runner.sh

# Install plist (symlink so edits to the source propagate)
ln -sf ~/.maton/hitch/com.maton.liftomaton.plist ~/Library/LaunchAgents/

# Load
launchctl load ~/Library/LaunchAgents/com.maton.liftomaton.plist

# Verify
launchctl list | grep maton
```

#### Management

```bash
# Stop
launchctl unload ~/Library/LaunchAgents/com.maton.liftomaton.plist

# Force immediate run
launchctl kickstart gui/$(id -u)/com.maton.liftomaton

# Or just touch the trigger
touch ~/.maton/hitch/trigger

# View logs
tail -f ~/.maton/hitch/runner.log
```

### Linux — systemd

Use a systemd timer (deadman) + a systemd path unit (trigger watcher).

#### Service Unit (`~/.config/systemd/user/maton.service`)

```ini
[Unit]
Description=Maton Dispatcher

[Service]
Type=oneshot
ExecStart=%h/.maton/hitch/runner.sh
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=HOME=%h
```

#### Timer Unit (`~/.config/systemd/user/maton.timer`)

```ini
[Unit]
Description=Maton Deadman Timer

[Timer]
OnBootSec=60
OnUnitActiveSec=600

[Install]
WantedBy=timers.target
```

#### Path Unit (`~/.config/systemd/user/maton-trigger.path`)

```ini
[Unit]
Description=Maton Trigger Watcher

[Path]
PathChanged=%h/.maton/hitch/trigger

[Install]
WantedBy=paths.target
```

#### Installation

```bash
systemctl --user daemon-reload
systemctl --user enable --now maton.timer maton-trigger.path
```

### Linux — cron (fallback)

If systemd is not available, use cron for the deadman timer. No native file-watch, so polling only.

```crontab
*/10 * * * * ~/.maton/hitch/runner.sh
```

For trigger support without systemd, use `inotifywait` in a background process:

```bash
while inotifywait -e modify ~/.maton/hitch/trigger 2>/dev/null; do
    ~/.maton/hitch/runner.sh
done
```

### Windows — Task Scheduler

Use `schtasks` for the deadman timer. For trigger support, use a PowerShell `FileSystemWatcher`.

```powershell
# Deadman timer (runs every 10 min)
schtasks /create /tn "Maton" /tr "%USERPROFILE%\.maton\hitch\runner.bat" /sc minute /mo 10

# Trigger watcher (run in background)
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = "$env:USERPROFILE\.maton\hitch"
$watcher.Filter = "trigger"
Register-ObjectEvent $watcher Changed -Action {
    & "$env:USERPROFILE\.maton\hitch\runner.bat"
}
```

---

## Filesystem Layout

```
~/.maton/
├── hitch/                          # Loop infrastructure (not git-tracked)
│   ├── runner.sh                   # Wrapper script
│   ├── trigger                     # Touch to request immediate run
│   ├── lock                        # PID file (prevents concurrent runs)
│   ├── runner.log                  # Runner output log
│   ├── com.maton.<name>.plist      # macOS launchd plist
│   └── launchd-stdout.log          # launchd stdout capture
└── matons/
    └── <instance-name>/            # The maton instance (git repo)
        ├── .git/
        ├── AGENTS.md
        ├── Maton.md
        ├── self.md
        ├── user.md
        ├── backlog.yaml            # Task queue
        ├── schedule.yaml           # Recurring tasks
        ├── guardrails.yaml         # Permission model
        ├── journal/
        ├── logs/                   # git-ignored
        ├── skills/
        │   ├── dispatch.md         # The dispatcher prompt
        │   └── update.md
        └── knowledge/              # Persistent learned context
            └── projects.yaml
```

The `hitch/` directory lives outside the maton instance because:
- It's platform-specific (plist vs systemd vs cron)
- It contains runtime artifacts (lock files, logs) that don't belong in git
- Multiple matons could share hitch infrastructure

The maton instance remains a clean git repo with only the state files that matter.

---

## Cooldown

Sometimes the dispatcher should NOT run again immediately, even on deadman timer. Examples:
- All tasks done, nothing scheduled for hours
- Rate limit on external APIs
- Human requested quiet hours

The runner script checks `~/.maton/hitch/cooldown` (if it exists). Format:

```
2026-05-09T22:00:00-04:00
```

If current time is before the cooldown timestamp, the runner exits without invoking the dispatcher. The dispatcher writes this file when it decides to pause.

---

## Security Notes

- The runner script runs as the user, with the user's permissions.
- The trigger file is writable by the user. If multi-user trigger is needed, adjust permissions.
- The LLM driver may have network access. The `guardrails.yaml` file constrains what the dispatcher is *instructed* to do, but enforcement depends on the driver's capabilities. True sandboxing requires OS-level controls (e.g., macOS sandbox profiles, Linux namespaces).
- Guardrails are advisory for now — they rely on the LLM following instructions. Hardware enforcement is a future concern.
