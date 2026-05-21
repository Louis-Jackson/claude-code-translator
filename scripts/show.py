#!/usr/bin/env python3
"""Show or list Claude Code translations by session.

Usage:
    python scripts/show.py                # show latest translation for $PWD project
    python scripts/show.py --watch        # live-watch translation for $PWD project
    python scripts/show.py --list         # list all active sessions with their projects
    python scripts/show.py --session ID   # show translation for a specific session
    python scripts/show.py --all          # show translations for all active sessions
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.translation_paths import (
    cache_dir,
    latest_translation_path,
    project_label,
    project_slug,
)

CLAUDE_DIR = Path.home() / ".claude"
SESSIONS_DIR = CLAUDE_DIR / "sessions"


def get_all_sessions():
    """Get all session metadata, grouped by cwd."""
    sessions = []
    if not SESSIONS_DIR.exists():
        return sessions

    for meta_file in SESSIONS_DIR.glob("*.json"):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            pid = data.get("pid", 0)
            alive = os.path.exists(f"/proc/{pid}")
            data["alive"] = alive
            data["meta_file"] = str(meta_file)
            sessions.append(data)
        except (json.JSONDecodeError, OSError):
            continue

    return sessions


def get_sessions_for_cwd(cwd):
    """Get sessions matching the given cwd."""
    cwd = str(Path(cwd).resolve())
    return [s for s in get_all_sessions() if s.get("cwd") == cwd]


def format_session_line(session):
    """Format a session as a display line."""
    pid = session.get("pid", "?")
    cwd = session.get("cwd", "?")
    sid = session.get("sessionId", "?")[:8]
    alive = session.get("alive", False)
    started = session.get("startedAt", 0)
    entrypoint = session.get("entrypoint", "?")

    started_str = ""
    if started:
        started_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(started / 1000))

    status = "\033[32m●\033[0m" if alive else "\033[31m○\033[0m"
    project_name = Path(cwd).name if cwd else "?"

    # Check if translation exists
    translation_path = latest_translation_path(cwd)
    has_translation = translation_path.exists()
    trans_indicator = " 📄" if has_translation else ""

    return (
        f"  {status} {sid}..  "
        f"PID={pid:<6}  "
        f"{entrypoint:<15}  "
        f"{project_name:<25}  "
        f"{started_str}"
        f"{trans_indicator}"
    )


def list_sessions():
    """List all sessions grouped by project."""
    sessions = get_all_sessions()
    if not sessions:
        print("No Claude Code sessions found.")
        return

    # Group by cwd
    by_cwd = {}
    for s in sessions:
        cwd = s.get("cwd", "unknown")
        by_cwd.setdefault(cwd, []).append(s)

    print("\033[1mClaude Code Sessions\033[0m")
    print()

    for cwd, group in sorted(by_cwd.items()):
        alive_count = sum(1 for s in group if s.get("alive"))
        slug = project_slug(cwd)
        translation_path = latest_translation_path(cwd)
        has_trans = translation_path.exists()

        header = f"\033[1m{Path(cwd).name}\033[0m ({cwd})"
        if has_trans:
            mtime = time.strftime(
                "%H:%M:%S", time.localtime(translation_path.stat().st_mtime)
            )
            header += f"  — last translation: {mtime}"

        print(header)
        for s in sorted(group, key=lambda x: x.get("startedAt", 0), reverse=True):
            print(format_session_line(s))
        print()

    print("Use \033[1m--watch\033[0m from a project directory to live-watch its translations.")
    print("Use \033[1m--watch --cwd /path/to/project\033[0m to watch a specific project.")


def render_markdown(content):
    """Render markdown content to terminal."""
    try:
        from rich.console import Console
        from rich.markdown import Markdown

        console = Console(force_terminal=True)
        console.print(Markdown(content))
        return True
    except ImportError:
        pass

    if shutil.which("glow"):
        subprocess.run(["glow", "-"], input=content, text=True, check=False)
        return True

    print(content)
    return True


def show_translation(cwd):
    """Show the latest translation for a project cwd."""
    path = latest_translation_path(cwd)
    if not path.exists():
        print(f"No translation found for {project_label(cwd)}")
        print(f"Expected at: {path}")
        return

    content = path.read_text(encoding="utf-8")
    render_markdown(content)


def clear_screen():
    print("\033[2J\033[H", end="", flush=True)


def watch_translation(cwd):
    """Live-watch translations for a project."""
    path = latest_translation_path(cwd)
    last_mtime_ns = object()

    print(f"Watching translations for: \033[1m{project_label(cwd)}\033[0m")
    print(f"File: {path}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            current_mtime_ns = path.stat().st_mtime_ns if path.exists() else None
            if current_mtime_ns != last_mtime_ns:
                clear_screen()
                if path.exists():
                    content = path.read_text(encoding="utf-8")
                    render_markdown(content)
                else:
                    print(f"Waiting for translation...")
                    print(f"Project: {project_label(cwd)}")
                    print(f"File: {path}")
                last_mtime_ns = current_mtime_ns
            time.sleep(0.5)
    except KeyboardInterrupt:
        clear_screen()
        print("Stopped watching.")


def main():
    parser = argparse.ArgumentParser(description="Show Claude Code translations by session.")
    parser.add_argument("--list", action="store_true", help="List all active sessions")
    parser.add_argument("--watch", action="store_true", help="Live-watch translation updates")
    parser.add_argument("--cwd", type=str, default=None, help="Project directory (defaults to $PWD)")
    parser.add_argument("--all", action="store_true", help="Show translations for all projects")
    args = parser.parse_args()

    if args.list:
        list_sessions()
        return

    if args.all:
        sessions = get_all_sessions()
        seen_cwds = set()
        for s in sessions:
            cwd = s.get("cwd")
            if cwd and cwd not in seen_cwds:
                seen_cwds.add(cwd)
                print(f"\n\033[1m{'=' * 60}\033[0m")
                print(f"\033[1m{Path(cwd).name}\033[0m ({cwd})")
                print(f"\033[1m{'=' * 60}\033[0m\n")
                show_translation(cwd)
        return

    cwd = args.cwd or os.getcwd()

    if args.watch:
        watch_translation(cwd)
    else:
        show_translation(cwd)


if __name__ == "__main__":
    main()
