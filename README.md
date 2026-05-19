# Claude Code 翻译插件

[English](./README_en.md) | [加入讨论](https://github.com/iChenwin/claude-code-translator/issues)

**保持 Claude Code 英文沟通，同时在本地查看中文译文。**

这是一个非侵入式的 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 输出翻译 Hook。它会在 Claude 回复结束后读取英文回复，通过通义千问或百度 API 翻译成中文，并在本地写入 Markdown 文件；有图形桌面时也可以切换为 Tkinter 弹窗。中文译文不会写回 Claude Code 的上下文。

## 主要特性

- **只翻译输出**：你可以直接用英文和 Claude Code 沟通，Claude 不会看到本地中文译文。
- **终端友好**：默认将最近一次译文写入 `~/.cache/claude-code-translator/latest_translation.md`，适合 SSH/服务器环境。
- **可选弹窗**：有图形桌面时可切换为 800x600 左右双栏 Tkinter 窗口。
- **双引擎支持**：内置 **通义千问 (Qianwen)** 和 **百度翻译** 支持。
- **交互可控**：可在翻译前确认，也支持一键复制中文译文。

![Claude Code Translator Screenshot](./screenshot.png)

## 快速开始

### Prerequisites
- Python 3.8+
- [uv](https://docs.astral.sh/uv/)：用于自动准备 Python 依赖，避免手动安装 `pip`
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- Qianwen API key (get one at [阿里云百炼](https://bailian.console.aliyun.com/)) OR
- Baidu AI Translation API key (get one at [百度翻译开放平台](https://fanyi-api.baidu.com/))

安装 uv：
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. **下载项目**
   ```bash
   git clone https://github.com/Louis-Jackson/claude-code-translator.git
   cd claude-code-translator
   ```

   不需要执行 `pip install`。安装脚本会让 Claude Code Hook 通过 `uv run --with-requirements requirements.txt ...` 自动准备依赖。

2. **配置 API Key**
   将 `config.example.json` 重命名为 `config.json` 并填入密钥。
   
   *使用通义千问 (推荐):*
   ```json
   {
     "provider": "qianwen",
     "qianwen": { "api_key": "你的阿里云DashScope-Key" }
   }
   ```
   *使用百度翻译:*
   ```json
   {
     "provider": "baidu",
     "baidu": { "api_key": "你的百度翻译api_key", "app_id": "你的百度翻译app_id" }
   }
   ```

3. **安装 Hook**
   ```bash
   python3 install.py
   ```

   如果你希望安装脚本本身也通过 uv 运行：
   ```bash
   uv run python install.py
   ```

安装脚本只会注册 `Notification` 输出翻译 Hook，不会注册输入翻译 Hook。重启 Claude Code 即可生效。

默认服务器模式会把最近一次译文写入：

```bash
~/.cache/claude-code-translator/latest_translation.md
```

查看译文：

```bash
cat ~/.cache/claude-code-translator/latest_translation.md
```

### tmux 分屏查看

如果你在 tmux 里使用 Claude Code，可以打开右侧实时译文 pane：

```bash
python3 scripts/tmux_translation_pane.py
```

默认右侧 pane 宽度为 40%。也可以指定宽度：

```bash
python3 scripts/tmux_translation_pane.py 50%
```

这个 pane 会实时刷新 `~/.cache/claude-code-translator/latest_translation.md`。主 pane 继续运行 Claude Code，右侧只用于阅读中文译文。

如果不想自动分屏，也可以手动运行 watcher：

```bash
python3 scripts/watch_translation.py
```

如果你有 Linux 图形桌面，并想用弹窗，可安装 Tkinter 并设置 `output_mode`：

```bash
sudo apt install python3-tk
```

```json
{
  "output_mode": "popup"
}
```

## 配置选项 (`config.json`)

| 选项Key | 说明 | 默认值 |
| :--- | :--- | :--- |
| `provider` | 翻译服务商 (`qianwen` 或 `baidu`) | `qianwen` |
| `translate_output` | 是否将 Claude 的英文回复翻译回中文显示 | `true` |
| `output_mode` | 输出方式：`file` 或 `popup` | `file` |
| `interactive_output` | 翻译 Claude 回复前是否先弹窗确认 | `false` |
| `debug` | 是否将 Hook 调试日志写入 `~/.cache/claude-code-translator/` | `false` |

## 卸载

```bash
python3 install.py --uninstall
```
