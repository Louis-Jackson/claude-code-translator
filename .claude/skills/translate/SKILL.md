---
name: translate
description: Manage the translation daemon and view translations. Usage — /translate start, /translate stop, /translate show, /translate watch, /translate list, /translate status.
arguments: action
allowed-tools:
  - Bash(*)
  - Read
---

Manage the claude-code-translator daemon and view translations.

The project root is at `!`git -C ~/.claude/../claude-code-translator rev-parse --show-toplevel 2>/dev/null || echo "$HOME/claude-code-translator"``.

Current daemon status: !`pgrep -fa 'watch_sessions.py' || echo 'not running'`
Active sessions: !`ls ~/.claude/sessions/*.json 2>/dev/null | wc -l` sessions

## Actions

Based on `$action` (default: "status"):

### `start`
Start the polling daemon in the background. The daemon watches all Claude Code transcript files and auto-translates new assistant messages.

```bash
cd ~/claude-code-translator
nohup env UV_CACHE_DIR=.uv-cache uv run --with-requirements requirements.txt python scripts/watch_sessions.py >> /tmp/ccs-daemon.log 2>&1 &
echo "Daemon started (PID: $!)"
```

Verify it started by checking the log:
```bash
sleep 2 && tail -3 /tmp/ccs-daemon.log
```

### `stop`
Stop the running daemon:
```bash
pkill -f 'watch_sessions.py'
```

### `restart`
Stop then start.

### `status`
Show daemon status and recent log:
```bash
echo "=== Daemon ==="
pgrep -fa 'watch_sessions.py' || echo "Not running"
echo ""
echo "=== Recent log ==="
tail -10 /tmp/ccs-daemon.log 2>/dev/null || echo "No log file"
echo ""
echo "=== Active sessions ==="
```
Then run `ccs list` or the equivalent Python command to show sessions.

### `show`
Show the latest translation for the current project:
```bash
cd ~/claude-code-translator && UV_CACHE_DIR=.uv-cache uv run --with-requirements requirements.txt python scripts/show.py --cwd "$PWD"
```
Note: Use the user's actual working directory, not the translator project directory.

### `watch`
Start live-watching translations for the current project. Tell the user to run this in a separate terminal:
```bash
ccs watch
```

### `list`
List all active sessions:
```bash
cd ~/claude-code-translator && UV_CACHE_DIR=.uv-cache uv run --with-requirements requirements.txt python scripts/show.py --list
```

### `log`
Show the full daemon log:
```bash
cat /tmp/ccs-daemon.log 2>/dev/null || echo "No log file"
```

### `once`
Translate the latest message right now (one-shot):
```bash
cd ~/claude-code-translator && UV_CACHE_DIR=.uv-cache uv run --with-requirements requirements.txt python scripts/watch_sessions.py --once
```

## If no action matches
Show available actions and current status.
