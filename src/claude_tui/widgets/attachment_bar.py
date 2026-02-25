"""AttachmentBar — horizontal bar showing pending attachments."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Button, Label


class AttachmentChip(Widget):
    """A single attachment chip with a remove button."""

    DEFAULT_CSS = """
    AttachmentChip {
        height: 1;
        layout: horizontal;
        margin: 0 1 0 0;
        background: $panel;
        padding: 0 1;
        border: solid $accent;
    }
    AttachmentChip > Label {
        color: $accent;
    }
    AttachmentChip > Button {
        background: transparent;
        border: none;
        height: 1;
        min-width: 2;
        padding: 0;
        color: $error;
    }
    """

    def __init__(self, name: str, index: int, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._name = name
        self._index = index

    def compose(self) -> ComposeResult:
        yield Label(f"📎 {self._name}")
        yield Button("✕", id=f"remove-{self._index}", classes="remove-btn")


class AttachmentBar(Widget):
    """Horizontal bar that lists pending file attachments."""

    DEFAULT_CSS = """
    AttachmentBar {
        height: 3;
        layout: horizontal;
        background: $surface;
        border-top: solid $panel;
        padding: 1 2;
        display: none;
    }
    AttachmentBar.visible {
        display: block;
    }
    """

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._attachments: list[str] = []

    def compose(self) -> ComposeResult:
        yield Horizontal(id="chips-container")

    def add_attachment(self, filename: str) -> None:
        self._attachments.append(filename)
        self.add_class("visible")
        chip = AttachmentChip(
            name=filename,
            index=len(self._attachments) - 1,
            id=f"chip-{len(self._attachments) - 1}",
        )
        self.query_one("#chips-container", Horizontal).mount(chip)

    def get_filenames(self) -> list[str]:
        return list(self._attachments)

    def clear(self) -> None:
        self._attachments.clear()
        container = self.query_one("#chips-container", Horizontal)
        for chip in container.query(AttachmentChip):
            chip.remove()
        self.remove_class("visible")
