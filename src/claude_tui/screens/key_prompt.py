"""KeyPromptScreen — modal to enter the Anthropic API key on first run."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class KeyPromptScreen(ModalScreen[str | None]):
    """Prompt the user to enter their Anthropic API key."""

    DEFAULT_CSS = """
    KeyPromptScreen {
        align: center middle;
    }
    #key-dialog {
        width: 70;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 2 3;
    }
    #key-dialog Label {
        margin-bottom: 1;
    }
    #key-dialog .hint {
        color: $text-muted;
        margin-bottom: 1;
    }
    #key-dialog Input {
        margin-bottom: 1;
    }
    #key-dialog .buttons {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }
    #key-dialog .buttons Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss(None)", "Cancel", show=True),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="key-dialog"):
            yield Label("Anthropic API Key", id="key-title")
            yield Label(
                "Enter your API key — it will be saved to ~/.claude_tui/.env",
                classes="hint",
            )
            yield Input(
                placeholder="sk-ant-...",
                password=True,
                id="key-input",
            )
            with Vertical(classes="buttons"):
                yield Button("Save", id="save-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn")

    def on_mount(self) -> None:
        self.query_one("#key-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self._submit()
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        key = self.query_one("#key-input", Input).value.strip()
        if key:
            self.dismiss(key)
        else:
            self.query_one("#key-input", Input).focus()
