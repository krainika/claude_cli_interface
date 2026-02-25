# Claude TUI

A full-screen terminal UI for the Anthropic Claude API — replicate the Claude desktop app experience without leaving your terminal or tmux session.

![Python](https://img.shields.io/badge/python-3.11+-blue) ![Textual](https://img.shields.io/badge/textual-0.80+-purple) ![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Live streaming** — responses stream token-by-token with a live cursor
- **Markdown rendering** — code blocks, tables, and formatting rendered inline
- **Session persistence** — conversations auto-saved to `~/.claude_tui/sessions/` as JSON
- **File attachments** — images, PDFs, and code files via `/attach` or drag-and-drop
- **Slash commands** — switch models, set system prompts, and more without leaving the TUI
- **Session picker** — reopen any past conversation with Ctrl+O

## Installation

Requires Python 3.11+.

```bash
git clone https://github.com/krainika/claude_cli_interface.git
cd claude_cli_interface
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Setup

On first run, the app will prompt you to enter your Anthropic API key. It is saved to `~/.claude_tui/.env` automatically, so you only need to do this once.

You can also set it manually via environment variable or a `.env` file in the project root:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

To update the key later, use the `/key` command from within the app.

## Usage

```bash
python -m claude_tui
```

Or if installed via the entry point:

```bash
claude-tui
```

## Key Bindings

| Key | Action |
|-----|--------|
| `Ctrl+S` | Send message |
| `Ctrl+N` | New session |
| `Ctrl+O` | Open session picker |
| `Ctrl+Q` | Quit |

## Slash Commands

| Command | Description |
|---------|-------------|
| `/attach <path>` | Attach a file or image |
| `/clear` | Clear the current conversation |
| `/model <name>` | Switch the Claude model |
| `/system <text>` | Set a custom system prompt |
| `/help` | Show help screen |
| `/key` | Update the Anthropic API key |

## Attachments & Drag-and-Drop

Use `/attach <path>` to attach a file, or simply **drag a file from Finder onto the terminal window** — the TUI detects the pasted path and attaches it automatically.

Supported types:
- **Images** — jpg, png, gif, webp (≤ 5 MB)
- **PDFs** — pdf (≤ 5 MB)
- **Text / code** — any UTF-8 file (≤ 200 KB)

## Configuration

All options can be set via environment variables or `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Your Anthropic API key (required) |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Default model |
| `CLAUDE_MAX_TOKENS` | `8096` | Max tokens per response |
| `CLAUDE_SYSTEM_PROMPT` | Built-in | Default system prompt |

## Stack

- [Textual](https://github.com/Textualize/textual) — TUI framework
- [anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python) — Official Anthropic SDK
- [python-dotenv](https://github.com/theskumar/python-dotenv) — `.env` file support
