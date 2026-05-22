---
name: translate-setup
description: Set up claude-code-translator on this machine — install hooks, shell aliases, and verify config.
allowed-tools:
  - Bash(*)
  - Read
  - Write
  - Edit
---

Set up the claude-code-translator on the current machine. Run these steps in order:

## 1. Check prerequisites

- Verify `uv` is installed: `which uv || pip install uv`
- Verify `python3` is available
- Check that `config.json` exists in the project root (it should — it's tracked in git).
- Check that `.env` exists. If not, copy from `.env.example` and tell the user to fill in their API key.

## 2. Install dependencies

Run from the project root:
```
uv pip install -r requirements.txt
```

## 3. Install the Notification hook

Run the install script:
```
python install.py
```

This registers the translation hook in `~/.claude/settings.json`.

**Note:** The Notification hook only works in the CLI (`claude` command), not in the VS Code extension. For VS Code, the user needs the polling daemon (step 5).

## 4. Install shell aliases

Write the following to `~/.bash_aliases` (append if the file exists, but avoid duplicating the `ccs` function if it's already there):

```bash
# Claude Code Translation shortcuts
ccs() {
    local cmd="${1:-show}"
    shift 2>/dev/null

    local base="$HOME/claude-code-translator"
    local uv="$HOME/.local/bin/uv"
    local real_cwd="$PWD"

    _ccs_run() {
        UV_CACHE_DIR="$base/.uv-cache" "$uv" run --directory "$base" --with-requirements "$base/requirements.txt" python "$@"
    }

    case "$cmd" in
        show)    _ccs_run "$base/scripts/show.py" --cwd "$real_cwd" "$@" ;;
        watch)   _ccs_run "$base/scripts/show.py" --watch --cwd "$real_cwd" "$@" ;;
        list)    _ccs_run "$base/scripts/show.py" --list "$@" ;;
        all)     _ccs_run "$base/scripts/show.py" --all "$@" ;;
        daemon)  _ccs_run "$base/scripts/watch_sessions.py" "$@" ;;
        *)       echo "Usage: ccs [show|watch|list|all|daemon]" ;;
    esac

    unset -f _ccs_run
}
```

Make sure `~/.bashrc` sources `~/.bash_aliases` (it usually does by default on Ubuntu/Debian).

## 5. Verify setup

- Run `python install.py` output to confirm hook is registered
- Run `ccs list` to verify the alias works
- Check `.env` has a valid API key (not the placeholder)

## 6. Print summary

Tell the user:
- For CLI: hooks are installed and will auto-translate after each response
- For VS Code: run `ccs daemon` in a terminal to start the polling watcher
- To view translations: run `ccs watch` from any project directory
- To toggle translation on/off: set `translate_output` in `config.json`
- API keys are stored in `.env` (never committed to git)
