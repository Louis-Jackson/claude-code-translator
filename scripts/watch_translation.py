#!/usr/bin/env python3
"""Watch the latest Claude Code translation file in a terminal pane."""

import shutil
import subprocess
import sys
import time
from pathlib import Path


DEFAULT_PATH = Path.home() / ".cache" / "claude-code-translator" / "latest_translation.md"


def clear_screen():
    """Clear terminal screen."""
    print("\033[2J\033[H", end="", flush=True)


def render_waiting(path):
    """Render waiting state."""
    print("Claude Code Translator", flush=True)
    print("=" * 24, flush=True)
    print(flush=True)
    print("Waiting for translation file:", flush=True)
    print(str(path), flush=True)
    print(flush=True)
    print("Keep this pane open. It updates after Claude finishes a response.", flush=True)
    print("Press Ctrl+C to stop.", flush=True)


def render_content(path):
    """Render current translation file."""
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        render_waiting(path)
        return
    except Exception as exc:
        print(f"Unable to read {path}: {exc}", flush=True)
        return

    if shutil.which("bat"):
        subprocess.run(["bat", "--style=plain", "--paging=never", str(path)], check=False)
    else:
        print(content, flush=True)


def main():
    """Watch latest translation file and refresh on changes."""
    path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_PATH
    last_mtime_ns = object()

    while True:
        try:
            current_mtime_ns = path.stat().st_mtime_ns if path.exists() else None
            if current_mtime_ns != last_mtime_ns:
                clear_screen()
                render_content(path)
                last_mtime_ns = current_mtime_ns
            time.sleep(1)
        except KeyboardInterrupt:
            clear_screen()
            return


if __name__ == "__main__":
    main()
