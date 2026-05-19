#!/usr/bin/env python3
"""Watch and render the latest Claude Code translation file in a terminal pane."""

import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.translation_paths import latest_translation_path


def try_render_markdown(content):
    """Render Markdown with rich when available."""
    try:
        from rich.console import Console
        from rich.markdown import Markdown
    except Exception:
        return False

    console = Console(force_terminal=True)
    console.print(Markdown(content))
    return True


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


def resolve_watch_path(args):
    """Resolve watch path from CLI args."""
    if args and args[0] == "--global":
        return latest_translation_path()
    if args:
        return Path(args[0]).expanduser()
    return latest_translation_path(Path.cwd())


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

    if try_render_markdown(content):
        return

    if shutil.which("glow"):
        subprocess.run(["glow", "-"], input=content, text=True, check=False)
    elif shutil.which("bat"):
        subprocess.run(["bat", "--style=plain", "--paging=never", str(path)], check=False)
    else:
        print(content, flush=True)


def main():
    """Watch latest translation file and refresh on changes."""
    path = resolve_watch_path(sys.argv[1:])
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
