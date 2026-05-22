#!/usr/bin/env python3
"""Watch Claude Code session transcripts and auto-translate new assistant messages.

This is a workaround for the VS Code extension not supporting Notification hooks.
It uses inotify to monitor transcript JSONL files for changes and triggers
translation when a new assistant message with stop_reason="end_turn" appears.

Usage:
    python scripts/watch_sessions.py          # watch all projects
    python scripts/watch_sessions.py --once   # translate latest message and exit
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.translation_paths import cache_dir, latest_translation_path, project_label


CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
SESSIONS_DIR = CLAUDE_DIR / "sessions"

# Track translated messages by their uuid to avoid duplicates
_translated_uuids = set()
# Track file sizes to only read new content
_file_offsets = {}
# Track failed translations for retry: uuid -> {filepath, retries_left}
_retry_queue = {}
MAX_RETRIES = 3


def log(msg):
    """Print timestamped log message."""
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_config():
    """Load configuration from config.json with secrets from .env."""
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")

    if "qianwen" not in config:
        config["qianwen"] = {}
    config["qianwen"].setdefault("api_key", os.environ.get("QIANWEN_API_KEY", ""))

    if "baidu" not in config:
        config["baidu"] = {}
    config["baidu"].setdefault("api_key", os.environ.get("BAIDU_API_KEY", ""))
    config["baidu"].setdefault("app_id", os.environ.get("BAIDU_APP_ID", ""))

    return config


def get_active_sessions():
    """Get active session info from session metadata files.

    Returns a dict mapping sessionId -> {cwd, pid, project_slug}.
    """
    sessions = {}
    if not SESSIONS_DIR.exists():
        return sessions

    for meta_file in SESSIONS_DIR.glob("*.json"):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            sid = data.get("sessionId")
            if sid:
                sessions[sid] = {
                    "cwd": data.get("cwd", ""),
                    "pid": data.get("pid"),
                }
        except (json.JSONDecodeError, OSError):
            continue

    return sessions


def find_project_cwd_for_transcript(transcript_path):
    """Derive the project cwd from the transcript path and session metadata.

    Transcript paths look like:
      ~/.claude/projects/<project-slug>/<sessionId>/subagents/<agent>.jsonl
      ~/.claude/projects/<project-slug>/<sessionId>.jsonl

    We extract the sessionId, look it up in session metadata to get the cwd.
    """
    path = Path(transcript_path)
    parts = path.parts

    # Try subagents path: .../projects/<slug>/<sessionId>/subagents/<agent>.jsonl
    for i, part in enumerate(parts):
        if part == "subagents" and i >= 2:
            session_id = parts[i - 1]
            sessions = get_active_sessions()
            session = sessions.get(session_id)
            if session:
                return session.get("cwd")
            break

    # Try top-level path: .../projects/<slug>/<sessionId>.jsonl
    # The filename (without .jsonl) is the sessionId
    session_id = path.stem
    sessions = get_active_sessions()
    session = sessions.get(session_id)
    if session:
        return session.get("cwd")

    return None


# Minimum text length to translate a tool_use message.
# Short tool_use messages are usually just "Let me check..." with no real content.
MIN_TOOL_USE_TEXT_LENGTH = 80


def get_last_assistant_message(filepath):
    """Read the last translatable assistant message from a JSONL file.

    Translatable messages:
      - stop_reason=end_turn  — always (final response)
      - stop_reason=tool_use  — only when the message contains meaningful text
        (e.g. Claude explaining a decision or asking for approval)

    Returns (uuid, text, cwd) or (None, None, None) if not found.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return None, None, None

    # Iterate backwards to find the last completed assistant message
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg = entry.get("message", {})
        if msg.get("role") != "assistant" or msg.get("type") != "message":
            continue

        stop_reason = msg.get("stop_reason")
        if stop_reason not in ("end_turn", "tool_use"):
            continue

        uuid = entry.get("uuid", "")
        content_parts = msg.get("content", [])
        text = ""
        for part in content_parts:
            if part.get("type") == "text":
                text += part.get("text", "")

        text = text.strip()
        if not text:
            continue

        # For tool_use messages, only translate if there's substantial text
        # (skip short messages like "Let me read the file.")
        if stop_reason == "tool_use" and len(text) < MIN_TOOL_USE_TEXT_LENGTH:
            continue

        return uuid, text, entry.get("sessionId")

    return None, None, None


def check_new_content(filepath):
    """Check if a JSONL file has new content since last check.

    Returns list of new lines, or empty list if no new content.
    """
    filepath = str(filepath)
    try:
        current_size = os.path.getsize(filepath)
    except OSError:
        return []

    last_offset = _file_offsets.get(filepath, 0)
    if current_size <= last_offset:
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            f.seek(last_offset)
            new_data = f.read()
        _file_offsets[filepath] = current_size
        return [line for line in new_data.strip().split("\n") if line.strip()]
    except OSError:
        return []


def has_new_translatable_message(new_lines):
    """Check if any new lines contain a translatable assistant message."""
    for line in new_lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = entry.get("message", {})
        if msg.get("role") != "assistant" or msg.get("type") != "message":
            continue

        stop_reason = msg.get("stop_reason")
        if stop_reason == "end_turn":
            return True
        if stop_reason == "tool_use":
            # Only trigger for messages with substantial text
            text = ""
            for part in msg.get("content", []):
                if part.get("type") == "text":
                    text += part.get("text", "")
            if len(text.strip()) >= MIN_TOOL_USE_TEXT_LENGTH:
                return True
    return False


def translate_message(text, config, project_cwd=None):
    """Translate a message using the configured provider."""
    from hooks.translate_output import get_translation_client, write_translation_file

    # Skip if already mostly Chinese
    chinese_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    if chinese_count > len(text) * 0.3:
        log("Message is already Chinese, skipping.")
        return

    client = get_translation_client(config)
    translated, usage = client.translate(text, "Chinese")

    # Determine scoped project cwd
    scoped_cwd = project_cwd if config.get("project_scoped_output", True) else None
    path = write_translation_file(text, translated, usage, scoped_cwd)
    log(f"Translation written to {path}")


def process_transcript(filepath, config):
    """Check a transcript file for new messages and translate if needed."""
    uuid, text, session_id = get_last_assistant_message(filepath)
    if not uuid or not text:
        return

    if uuid in _translated_uuids:
        return

    if not config.get("translate_output", True):
        return

    project_cwd = find_project_cwd_for_transcript(filepath)
    log(f"New assistant message in {Path(filepath).name} (project: {project_label(project_cwd)})")
    log(f"Message preview: {text[:80]}...")

    _do_translate(uuid, text, config, project_cwd, filepath)


def _do_translate(uuid, text, config, project_cwd, filepath, retries_left=MAX_RETRIES):
    """Attempt translation with retry tracking on failure."""
    try:
        translate_message(text, config, project_cwd)
        _translated_uuids.add(uuid)
        _retry_queue.pop(uuid, None)
    except Exception as e:
        if retries_left > 0:
            log(f"Translation error (will retry, {retries_left} left): {e}")
            _retry_queue[uuid] = {
                "filepath": str(filepath),
                "project_cwd": project_cwd,
                "text": text,
                "retries_left": retries_left - 1,
            }
        else:
            log(f"Translation failed after {MAX_RETRIES} retries: {e}")
            _retry_queue.pop(uuid, None)


def process_retries(config):
    """Retry any failed translations."""
    if not _retry_queue:
        return

    for uuid, info in list(_retry_queue.items()):
        if uuid in _translated_uuids:
            _retry_queue.pop(uuid, None)
            continue

        log(f"Retrying translation ({info['retries_left']} retries left)...")
        _do_translate(
            uuid,
            info["text"],
            config,
            info["project_cwd"],
            info["filepath"],
            info["retries_left"],
        )


def find_all_transcript_files():
    """Find all existing JSONL transcript files (both main and subagent)."""
    if not PROJECTS_DIR.exists():
        return []
    # Main conversation transcripts: projects/<slug>/<sessionId>.jsonl
    files = list(PROJECTS_DIR.glob("*/*.jsonl"))
    # Subagent transcripts: projects/<slug>/<sessionId>/subagents/<agent>.jsonl
    files.extend(PROJECTS_DIR.glob("*/*/subagents/*.jsonl"))
    return files


def watch_sessions(config, poll_interval=1):
    """Main watch loop using file-size polling.

    inotify does not reliably detect writes from the Claude Code VS Code
    extension (likely due to buffered / memory-mapped I/O), so we poll
    transcript file sizes every *poll_interval* seconds instead.
    """
    # Initialize file offsets for existing files to avoid translating old messages
    for f in find_all_transcript_files():
        _file_offsets[str(f)] = os.path.getsize(str(f))

    log("Watching transcript files for changes (polling)...")
    log("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(poll_interval)

            # Reload config each cycle so toggling translate_output works live
            try:
                config = load_config()
            except Exception:
                pass

            # Discover all transcript files (picks up new sessions automatically)
            for filepath in find_all_transcript_files():
                new_lines = check_new_content(filepath)
                if not new_lines:
                    continue

                if has_new_translatable_message(new_lines):
                    process_transcript(filepath, config)

            # Retry any previously failed translations
            process_retries(config)

    except KeyboardInterrupt:
        log("Stopping watcher.")


def run_once(config):
    """Translate the latest message from the most recently modified transcript."""
    transcripts = find_all_transcript_files()
    if not transcripts:
        log("No transcript files found.")
        return

    # Sort by modification time, most recent first
    transcripts.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    for transcript in transcripts:
        uuid, text, session_id = get_last_assistant_message(transcript)
        if uuid and text:
            project_cwd = find_project_cwd_for_transcript(transcript)
            log(f"Latest message from {transcript.name} (project: {project_label(project_cwd)})")
            translate_message(text, config, project_cwd)
            return

    log("No assistant messages found in any transcript.")


def main():
    parser = argparse.ArgumentParser(description="Watch Claude Code sessions and auto-translate.")
    parser.add_argument("--once", action="store_true", help="Translate latest message and exit")
    args = parser.parse_args()

    config = load_config()
    if not config.get("translate_output", True):
        log("Translation is disabled in config.json (translate_output=false)")
        return

    if args.once:
        run_once(config)
    else:
        watch_sessions(config)


if __name__ == "__main__":
    main()
