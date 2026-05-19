# Claude Code Translation Plugin

[简体中文](./README.md)

**Keep Claude Code conversations in English while reading a local Chinese translation.**

This plugin hooks into [Claude Code](https://docs.anthropic.com/en/docs/claude-code) after Claude responds. It reads the latest English assistant message from the transcript, translates it to Chinese through Qianwen or Baidu, and writes the translation to a local Markdown file. On graphical desktops, it can also show a Tkinter side-by-side window. The Chinese translation is not added back to Claude Code's context.

## Features

- **Output-only**: Type English prompts and keep Claude's context in English.
- **Terminal-Friendly**: Writes the latest translation to a project-scoped file under `~/.cache/claude-code-translator/projects/.../latest_translation.md` by default.
- **Optional Popup**: On graphical desktops, switch to an 800x600 local side-by-side Tkinter window.
- **Flexible**: Supports **Qianwen (Alibaba)** and **Baidu** translation APIs.
- **Controllable**: Optionally asks before translating and includes a copy button for the Chinese result.

![Claude Code Translator Screenshot](./screenshot.png)

## Installation

### Prerequisites
- Python 3.8+
- [uv](https://docs.astral.sh/uv/) to manage Python dependencies without installing `pip`
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- Qianwen API key (get one at [阿里云百炼](https://bailian.console.aliyun.com/)) OR
- Baidu AI Translation API key (get one at [百度翻译开放平台](https://fanyi-api.baidu.com/))

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. **Clone the Project**
   ```bash
   git clone https://github.com/Louis-Jackson/claude-code-translator.git
   cd claude-code-translator
   ```

   You do not need to run `pip install`. The installer writes a Claude Code hook that runs through `uv run --with-requirements requirements.txt ...`.

2. **Configure API Key**
   Rename `config.example.json` to `config.json` and add your API key.
   
   *Using Qianwen (Recommended):*
   ```json
   {
     "provider": "qianwen",
     "qianwen": { "api_key": "sk-..." }
   }
   ```
   *Using Baidu:*
   ```json
   {
     "provider": "baidu",
     "baidu": { "api_key": "...", "app_id": "..." }
   }
   ```

3. **Install Hooks**
   ```bash
   python3 install.py
   ```

   To run the installer itself through uv:
   ```bash
   uv run python install.py
   ```

The installer only registers the `Notification` output translation hook. It does not install an input translation hook, so Claude only sees the prompts you type. Restart Claude Code for changes to take effect.

By default, server mode separates translations by project and writes to:

```bash
~/.cache/claude-code-translator/projects/<project-slug>/latest_translation.md
```

Watch the current project's translation from the project directory:

```bash
python3 scripts/watch_translation.py
```

### tmux Side Pane

If you use Claude Code inside tmux, open a right-side translation pane from each project directory:

```bash
python3 scripts/tmux_translation_pane.py
```

The default pane width is 40%. You can pass another width:

```bash
python3 scripts/tmux_translation_pane.py 50%
```

The pane watches the current project's translation file and refreshes whenever Claude finishes a translated response. You can run multiple Claude Code/tmux windows for different projects, and each project will see its own translations.

You can also run the watcher manually:

```bash
python3 scripts/watch_translation.py
```

To watch the legacy global translation file:

```bash
python3 scripts/watch_translation.py --global
```

If you have a Linux graphical desktop and want popups, install Tkinter and set `output_mode`:

```bash
sudo apt install python3-tk
```

```json
{
  "output_mode": "popup"
}
```

## Configuration (`config.json`)

| Option | Description | Default |
| :--- | :--- | :--- |
| `provider` | `qianwen` or `baidu` | `qianwen` |
| `translate_output` | Show a popup with Chinese translation of Claude's response (with Copy button)? | `true` |
| `output_mode` | Output mode: `file` or `popup` | `file` |
| `project_scoped_output` | Separate translation files by Claude Code's current project directory | `true` |
| `interactive_output` | Ask before translating Claude's response? | `false` |
| `debug` | Write hook debug logs to `~/.cache/claude-code-translator/` | `false` |

## Uninstallation

```bash
python3 install.py --uninstall
```
