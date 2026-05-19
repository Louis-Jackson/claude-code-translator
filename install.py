#!/usr/bin/env python3
"""Installation script for Claude Code Translation Plugin.

This script adds an output-translation hook to ~/.claude/settings.json.
The installed hook reads Claude Code's English responses and shows a local
Chinese translation window without adding that translation to Claude's context.
"""

import json
import shlex
import shutil
import sys
from pathlib import Path


def get_claude_settings_path():
    """Get the path to Claude settings file."""
    home = Path.home()
    return home / '.claude' / 'settings.json'


def get_hook_commands():
    """Get the hook command configurations."""
    # Get absolute path to hooks directory
    project_dir = Path(__file__).resolve().parent
    hooks_dir = project_dir / 'hooks'
    requirements_path = project_dir / 'requirements.txt'
    uv_cache_dir = project_dir / '.uv-cache'
    input_hook = hooks_dir / 'translate_input.py'
    output_hook = hooks_dir / 'translate_output.py'

    python_executable = sys.executable or 'python3'
    uv_executable = shutil.which('uv')
    input_command = _uv_command(uv_executable, project_dir, requirements_path, uv_cache_dir, input_hook)
    output_command = _uv_command(uv_executable, project_dir, requirements_path, uv_cache_dir, output_hook)

    if not uv_executable:
        input_command = _python_command(python_executable, input_hook)
        output_command = _python_command(python_executable, output_hook)

    return {
        "input": input_command,
        "output": output_command,
        "uses_uv": bool(uv_executable),
        "legacy_input": _legacy_commands(input_hook, project_dir, requirements_path, uv_cache_dir),
        "legacy_output": _legacy_commands(output_hook, project_dir, requirements_path, uv_cache_dir),
    }


def _python_command(python_executable, script_path):
    """Build a Linux-safe hook command."""
    return f"{shlex.quote(str(python_executable))} {shlex.quote(str(script_path))}"


def _uv_command(uv_executable, project_dir, requirements_path, uv_cache_dir, script_path):
    """Build a uv-managed hook command."""
    if not uv_executable:
        return None

    return " ".join([
        f"UV_CACHE_DIR={shlex.quote(str(uv_cache_dir))}",
        shlex.quote(str(uv_executable)),
        "run",
        "--directory",
        shlex.quote(str(project_dir)),
        "--with-requirements",
        shlex.quote(str(requirements_path)),
        "python",
        shlex.quote(str(script_path)),
    ])


def _legacy_commands(script_path, project_dir, requirements_path, uv_cache_dir):
    """Commands used by older versions of this installer."""
    script_str = str(script_path).replace('\\', '/')
    commands = {
        f'python "{script_str}"',
        f'python3 "{script_str}"',
        f'python {shlex.quote(script_str)}',
        f'python3 {shlex.quote(script_str)}',
        _python_command(sys.executable or 'python3', script_path),
        _python_command('/usr/bin/python3', script_path),
    }

    uv_executable = shutil.which('uv')
    if uv_executable:
        commands.add(_uv_command(uv_executable, project_dir, requirements_path, uv_cache_dir, script_path))

    return commands


def _hook_entry(command):
    """Create a Claude Code command hook entry."""
    return {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": command
            }
        ]
    }


def _remove_commands(settings, hook_name, commands):
    """Remove only this plugin's hook commands, preserving other user hooks."""
    hook_groups = settings.get('hooks', {}).get(hook_name)
    if not hook_groups:
        return False

    removed = False
    kept_groups = []
    for group in hook_groups:
        original_hooks = group.get('hooks', [])
        kept_hooks = [
            hook for hook in original_hooks
            if not (
                hook.get('type') == 'command'
                and hook.get('command') in commands
            )
        ]

        if len(kept_hooks) != len(original_hooks):
            removed = True

        if kept_hooks:
            updated_group = dict(group)
            updated_group['hooks'] = kept_hooks
            kept_groups.append(updated_group)

    if kept_groups:
        settings['hooks'][hook_name] = kept_groups
    else:
        del settings['hooks'][hook_name]

    if not settings.get('hooks'):
        settings.pop('hooks', None)

    return removed


def _load_settings(settings_path):
    """Load Claude settings or return an empty settings object."""
    if settings_path.exists():
        with open(settings_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def _write_settings(settings_path, settings):
    """Write Claude settings."""
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def install_hooks():
    """Install output translation hook to Claude settings."""
    settings_path = get_claude_settings_path()

    settings = _load_settings(settings_path)

    # Ensure hooks section exists
    if 'hooks' not in settings:
        settings['hooks'] = {}

    hooks = get_hook_commands()
    known_input_commands = {hooks["input"], *hooks["legacy_input"]}
    known_output_commands = {hooks["output"], *hooks["legacy_output"]}

    # Remove old input hook from this plugin so Claude only sees what you type.
    _remove_commands(settings, 'UserPromptSubmit', known_input_commands)

    # Avoid duplicate output hooks while preserving unrelated Notification hooks.
    if 'hooks' not in settings:
        settings['hooks'] = {}
    _remove_commands(settings, 'Notification', known_output_commands)
    if 'hooks' not in settings:
        settings['hooks'] = {}
    settings['hooks'].setdefault('Notification', []).append(_hook_entry(hooks["output"]))

    # Write settings back
    _write_settings(settings_path, settings)

    print(f"Output translation hook installed successfully to: {settings_path}")
    print("\nConfigured hooks:")
    print(f"  - Notification: {hooks['output']}")
    if hooks["uses_uv"]:
        print("\nDependencies will be managed by uv when the hook runs.")
    else:
        print("\nuv was not found. Install dependencies manually or install uv and rerun this installer.")
    print("\nInput translation is not installed. Claude Code will only see the English prompts you type.")
    print("\nTo disable output translation, set 'translate_output': false in config.json")
    print("\nRestart Claude Code for changes to take effect.")


def uninstall_hooks():
    """Remove translation hooks from Claude settings."""
    settings_path = get_claude_settings_path()

    if not settings_path.exists():
        print("No Claude settings file found. Nothing to uninstall.")
        return

    settings = _load_settings(settings_path)
    if not settings:
        print("Invalid or empty settings file. Nothing to uninstall.")
        return

    if 'hooks' not in settings:
        print("No hooks configured. Nothing to uninstall.")
        return

    hooks = get_hook_commands()
    known_input_commands = {hooks["input"], *hooks["legacy_input"]}
    known_output_commands = {hooks["output"], *hooks["legacy_output"]}

    hooks_removed = False
    hooks_removed |= _remove_commands(settings, 'UserPromptSubmit', known_input_commands)
    hooks_removed |= _remove_commands(settings, 'Notification', known_output_commands)

    if hooks_removed:
        _write_settings(settings_path, settings)

        print("Translation hooks uninstalled successfully.")
    else:
        print("No translation hooks found. Nothing to uninstall.")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == '--uninstall':
        uninstall_hooks()
    else:
        install_hooks()


if __name__ == '__main__':
    main()
