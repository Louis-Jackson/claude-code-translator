# Claude Code Translation Plugin

[简体中文](./README.md)

**Keep Claude Code conversations in English while reading a local Chinese translation.**

This plugin hooks into [Claude Code](https://docs.anthropic.com/en/docs/claude-code) after Claude responds. It reads the latest English assistant message from the transcript, translates it to Chinese through Qianwen or Baidu, and writes the translation to a local Markdown file. On graphical desktops, it can also show a Tkinter side-by-side window. The Chinese translation is not added back to Claude Code's context.

## Features

- **Output-only**: Type English prompts and keep Claude's context in English.
- **Terminal-Friendly**: Writes the latest translation to `~/.cache/claude-code-translator/latest_translation.md` by default.
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

By default, server mode writes the latest translation to:

```bash
~/.cache/claude-code-translator/latest_translation.md
```

Read it with:

```bash
cat ~/.cache/claude-code-translator/latest_translation.md
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
| `interactive_output` | Ask before translating Claude's response? | `false` |
| `debug` | Write hook debug logs to `~/.cache/claude-code-translator/` | `false` |

## Uninstallation

```bash
python3 install.py --uninstall
```
