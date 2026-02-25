"""InputBar — TextArea + Send button, docked at the bottom."""

from __future__ import annotations

from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, TextArea


class SmartTextArea(TextArea):
    """TextArea that intercepts file-path pastes for drag-and-drop support."""

    class FilePaste(Message):
        """Posted when all pasted content resolves to existing file paths."""

        def __init__(self, paths: list[Path]) -> None:
            super().__init__()
            self.paths = paths

    async def _on_paste(self, event: events.Paste) -> None:
        """Intercept paste: if every pasted line is a real file path, post FilePaste."""
        text = event.text.strip()
        if not text:
            return

        # Each line may be a path, possibly shell-quoted or with trailing spaces
        lines = [line.strip().strip("'\"") for line in text.splitlines() if line.strip()]
        file_paths: list[Path] = []
        for line in lines:
            try:
                p = Path(line).expanduser().resolve()
                if p.exists() and p.is_file():
                    file_paths.append(p)
            except (OSError, ValueError):
                pass

        if file_paths and len(file_paths) == len(lines):
            # Every pasted item is a file — treat as drag-and-drop, skip text insertion
            self.post_message(self.FilePaste(file_paths))
        else:
            # Normal paste — delegate to TextArea's built-in handler
            await super()._on_paste(event)


class InputBar(Widget):
    """Bottom input area with a multi-line TextArea and Send button."""

    DEFAULT_CSS = """
    InputBar {
        height: auto;
        max-height: 10;
        dock: bottom;
        border-top: solid $panel;
        background: $surface;
        padding: 0 1;
        layout: horizontal;
    }
    InputBar > SmartTextArea {
        height: auto;
        min-height: 1;
        max-height: 8;
        border: none;
        background: $surface;
        padding: 0 1;
        width: 1fr;
    }
    InputBar > Button {
        height: 3;
        min-width: 8;
        margin: 0 0 0 1;
        align-vertical: middle;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "send", "Send", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield SmartTextArea(id="input-area", language=None)
        yield Button("Send", id="send-btn", variant="primary")

    @property
    def text_area(self) -> SmartTextArea:
        return self.query_one("#input-area", SmartTextArea)

    def get_text(self) -> str:
        return self.text_area.text

    def clear(self) -> None:
        self.text_area.clear()
        self.text_area.focus()

    def set_enabled(self, enabled: bool) -> None:
        self.text_area.disabled = not enabled
        btn = self.query_one("#send-btn", Button)
        btn.disabled = not enabled
