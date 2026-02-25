"""HelpScreen — modal showing key bindings and slash commands."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Markdown

HELP_TEXT = """\
# Claude TUI — Help

## Key Bindings
| Key | Action |
|-----|--------|
| `Ctrl+S` | Send message |
| `Ctrl+N` | New session |
| `Ctrl+O` | Open session picker |
| `Ctrl+Q` | Quit |
| `Tab` | Focus next widget |
| `Escape` | Close modal / cancel |

## Slash Commands
| Command | Description |
|---------|-------------|
| `/attach <path>` | Attach a file or image to the next message |
| `/clear` | Clear the current conversation |
| `/model <name>` | Switch the Claude model |
| `/system <text>` | Set a custom system prompt |
| `/help` | Show this help screen |
| `/key` | Update the Anthropic API key |

## Models
- `claude-opus-4-6` — most capable
- `claude-sonnet-4-6` — balanced (default)
- `claude-haiku-4-5-20251001` — fastest

## Attachments
- **Images**: jpg, png, gif, webp (≤ 5 MB)
- **PDFs**: pdf (≤ 5 MB)
- **Text/Code**: any text file (≤ 200 KB)

Sessions are auto-saved to `~/.claude_tui/sessions/`.
"""


class HelpScreen(ModalScreen[None]):
    """Modal help screen."""

    BINDINGS = [
        Binding("escape", "dismiss(None)", "Close", show=True),
        Binding("q", "dismiss(None)", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Markdown(HELP_TEXT)
            yield Button("Close", id="close-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)
