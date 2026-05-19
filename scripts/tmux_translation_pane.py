#!/usr/bin/env python3
"""Open a tmux pane that watches the latest translation file."""

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    """Create a right-side tmux pane for translation output."""
    if "TMUX" not in os.environ:
        print("This command must be run inside tmux.", file=sys.stderr)
        print("Start tmux first, then run: python3 scripts/tmux_translation_pane.py", file=sys.stderr)
        return 1

    if not shutil.which("tmux"):
        print("tmux command not found.", file=sys.stderr)
        return 1

    script_path = Path(__file__).resolve().with_name("watch_translation.py")
    translation_path = Path.home() / ".cache" / "claude-code-translator" / "latest_translation.md"
    pane_size = sys.argv[1] if len(sys.argv) > 1 else "40%"

    command = " ".join([
        "python3",
        shlex.quote(str(script_path)),
        shlex.quote(str(translation_path)),
    ])

    subprocess.run([
        "tmux",
        "split-window",
        "-h",
        "-l",
        pane_size,
        command,
    ], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
