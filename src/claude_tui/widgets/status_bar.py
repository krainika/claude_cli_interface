"""StatusBar — shows model info, token count, and streaming status."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Label


class StatusBar(Widget):
    """Docked status bar at the bottom of the screen."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
        background: $panel;
        layout: horizontal;
        padding: 0 1;
    }
    StatusBar > #status-left {
        width: 1fr;
        color: $text-muted;
    }
    StatusBar > #status-right {
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Ready", id="status-left")
        yield Label("", id="status-right")

    def set_status(self, text: str) -> None:
        self.query_one("#status-left", Label).update(text)

    def set_model(self, model: str) -> None:
        self.query_one("#status-right", Label).update(model)

    def set_streaming(self, token_count: int = 0) -> None:
        text = f"Streaming… {token_count} tokens" if token_count else "Streaming…"
        self.query_one("#status-left", Label).update(text)

    def set_ready(self, token_count: int = 0) -> None:
        text = f"Ready  ({token_count} tokens)" if token_count else "Ready"
        self.query_one("#status-left", Label).update(text)

    def set_error(self, message: str) -> None:
        self.query_one("#status-left", Label).update(f"[red]Error: {message}[/red]")
