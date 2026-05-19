#!/usr/bin/env python3
"""Notification hook for translating Claude's English output to Chinese."""

import sys
import json
import os
import io
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.qianwen_client import QianwenClient
from lib.baidu_client import BaiduClient


def continue_hook():
    """Tell Claude Code to continue without adding context."""
    print(json.dumps({"result": "continue"}))


def get_log_path(filename):
    """Return a Linux-friendly debug log path under ~/.cache."""
    cache_dir = Path.home() / '.cache' / 'claude-code-translator'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / filename


def get_latest_translation_path():
    """Return the fallback file path for the latest translation."""
    return get_log_path('latest_translation.md')


def write_translation_file(original, translated, usage):
    """Write translation to a local file when the GUI cannot be shown."""
    usage_lines = []
    if usage:
        usage_lines = [
            "",
            "## Usage",
            "",
            f"- Total tokens: {usage.get('total_tokens', 0)}",
            f"- Prompt tokens: {usage.get('prompt_tokens', 0)}",
            f"- Completion tokens: {usage.get('completion_tokens', 0)}",
        ]

    content = "\n".join([
        "# Claude Code Translation",
        "",
        "## Original",
        "",
        original,
        "",
        "## Chinese Translation",
        "",
        translated,
        *usage_lines,
        "",
    ])

    path = get_latest_translation_path()
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path


def debug_log(config, message):
    """Write debug logs only when explicitly enabled."""
    if not config.get('debug', False):
        return

    try:
        with open(get_log_path('output_hook.log'), 'a', encoding='utf-8') as f:
            f.write(message)
    except Exception:
        pass


def error_log(message):
    """Best-effort error logging outside Claude's context."""
    try:
        with open(get_log_path('output_hook_error.log'), 'a', encoding='utf-8') as f:
            f.write(message)
    except Exception:
        pass


def import_dialogs():
    """Import Tkinter dialogs lazily so hooks can skip safely without Tk."""
    from lib.dialogs import show_confirm_dialog, show_translation_result
    return show_confirm_dialog, show_translation_result


def get_translation_client(config):
    """Get the appropriate translation client based on config.

    Args:
        config: Configuration dictionary

    Returns:
        Translation client instance
    """
    provider = config.get('provider', 'qianwen')

    if provider == 'baidu':
        baidu_config = config['baidu']
        return BaiduClient(
            api_key=baidu_config['api_key'],
            app_id=baidu_config['app_id']
        )
    else:
        # Default to qianwen
        qianwen_config = config['qianwen']
        return QianwenClient(
            base_url=qianwen_config['base_url'],
            api_key=qianwen_config['api_key'],
            model=qianwen_config['model']
        )


def load_config():
    """Load configuration from config.json."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'config.json'
    )
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Main hook handler."""
    try:
        config = load_config()

        # Read input from stdin
        # Ensure we are reading UTF-8
        try:
            if hasattr(sys.stdin, 'buffer'):
                sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
        except Exception:
            pass

        raw_input = sys.stdin.read().strip()
        if raw_input.startswith('\ufeff'):
            raw_input = raw_input[1:]
        input_data = json.loads(raw_input)

        debug_log(config, json.dumps(input_data, ensure_ascii=False, indent=2) + "\n\n")

        # Check if this is an assistant message notification
        # Check if this is an idle prompt notification (meaning Claude finished responding)
        notification_type = input_data.get('notification_type', '')
        if notification_type not in ['idle_prompt', 'permission_prompt']:
            # Not a relevant event
            continue_hook()
            return

        # Get the transcript path
        transcript_path = input_data.get('transcript_path', '')
        if not transcript_path or not os.path.exists(transcript_path):
            continue_hook()
            return

        # Read the last line of the transcript file
        last_assistant_message = ""
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Iterate backwards to find the last assistant message
                for line in reversed(lines):
                    try:
                        entry = json.loads(line)
                        msg = entry.get('message', {})
                        if msg.get('role') == 'assistant' and msg.get('type') == 'message':
                            # Found the last assistant message
                            content_list = msg.get('content', [])
                            for content in content_list:
                                if content.get('type') == 'text':
                                    last_assistant_message += content.get('text', '')
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            error_log(f"Error reading transcript: {e}\n")
            continue_hook()
            return

        if not last_assistant_message:
            # No assistant message found
            continue_hook()
            return

        # Check if output translation is enabled
        if not config.get('translate_output', True):
            continue_hook()
            return

        # Initialize client based on provider
        client = get_translation_client(config)

        # Skip if message is already primarily Chinese
        # (We check if it has significant Chinese content to avoid double translation)
        chinese_char_count = sum(1 for c in last_assistant_message if '\u4e00' <= c <= '\u9fff')
        if chinese_char_count > len(last_assistant_message) * 0.3:
            continue_hook()
            return

        # Check if interactive mode is enabled
        interactive_output = config.get('interactive_output', True)
        show_confirm_dialog = None
        show_translation_result = None

        if interactive_output:
            try:
                show_confirm_dialog, show_translation_result = import_dialogs()
            except Exception as e:
                error_log(f"Tkinter dialogs unavailable before confirmation: {e}\n")
                continue_hook()
                return

            # Ask user if they want to translate
            # Use the first 500 chars for preview
            preview_msg = last_assistant_message[:500] + "..." if len(last_assistant_message) > 500 else last_assistant_message
            try:
                should_translate = show_confirm_dialog(preview_msg)
            except Exception as e:
                error_log(f"Unable to show confirmation dialog: {e}\n")
                continue_hook()
                return

            if not should_translate:
                # User declined translation
                continue_hook()
                return

        debug_log(config, f"Translating message (len={len(last_assistant_message)}):\n{last_assistant_message}\n\n")

        # Translate to Chinese
        translated, usage = client.translate(last_assistant_message, 'Chinese')

        debug_log(
            config,
            f"Translation result (len={len(translated)}):\n{translated}\nUsage: {usage}\n\n",
        )

        # Show result in a standalone window
        if show_translation_result is None:
            try:
                _, show_translation_result = import_dialogs()
            except Exception as e:
                error_log(f"Tkinter dialogs unavailable for result window: {e}\n")
                write_translation_file(last_assistant_message, translated, usage)
                continue_hook()
                return

        try:
            show_translation_result(last_assistant_message, translated, usage)
        except Exception as e:
            error_log(f"Unable to show translation result dialog: {e}\n")
            write_translation_file(last_assistant_message, translated, usage)
        
        # Continue without adding context to Claude (since we showed it to user)
        continue_hook()

    except Exception as e:
        # On error, log to stderr and continue normally
        error_log(f"Error: {e}\n")
        print(f"Output translation hook error: {e}", file=sys.stderr)
        continue_hook()


if __name__ == '__main__':
    main()
