# Claude Code Translation Plugin

[简体中文](./README.md)

**Keep Claude Code conversations in English while reading a local Chinese translation.**

This plugin hooks into [Claude Code](https://docs.anthropic.com/en/docs/claude-code) after Claude responds. It reads the latest English assistant message from the transcript, translates it to Chinese through Qianwen or Baidu, and shows a local Tkinter side-by-side window. The Chinese translation is not added back to Claude Code's context.

## Features

- **Output-only**: Type English prompts and keep Claude's context in English.
- **Local Side-by-Side Window**: Shows the English original and Chinese translation in an 800x600 local window.
- **Flexible**: Supports **Qianwen (Alibaba)** and **Baidu** translation APIs.
- **Controllable**: Optionally asks before translating and includes a copy button for the Chinese result.

![Claude Code Translator Screenshot](./screenshot.png)

## Installation

### Prerequisites
- Python 3.8+
- A Linux graphical desktop session
- Tkinter: on Debian/Ubuntu, install `sudo apt install python3-tk`
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- Qianwen API key (get one at [阿里云百炼](https://bailian.console.aliyun.com/)) OR
- Baidu AI Translation API key (get one at [百度翻译开放平台](https://fanyi-api.baidu.com/))

1. **Clone & Install Dependencies**
   ```bash
   git clone https://github.com/iChenwin/claude-code-translator.git
   cd claude-code-translator
   python3 -m pip install -r requirements.txt
   ```

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

The installer only registers the `Notification` output translation hook. It does not install an input translation hook, so Claude only sees the prompts you type. Restart Claude Code for changes to take effect.

> On Linux, a graphical desktop session is required for the Tkinter window, such as an available `$DISPLAY` or Wayland session. Without a GUI, set `interactive_output` to `false`; if the result window cannot open, the hook writes the latest translation to `~/.cache/claude-code-translator/latest_translation.md`.

## Configuration (`config.json`)

| Option | Description | Default |
| :--- | :--- | :--- |
| `provider` | `qianwen` or `baidu` | `qianwen` |
| `translate_output` | Show a popup with Chinese translation of Claude's response (with Copy button)? | `true` |
| `interactive_output` | Ask before translating Claude's response? | `false` |
| `debug` | Write hook debug logs to `~/.cache/claude-code-translator/` | `false` |

## Uninstallation

```bash
python3 install.py --uninstall
```
