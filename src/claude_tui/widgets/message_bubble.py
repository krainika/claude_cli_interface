"""MessageBubble widget — wraps Textual Markdown for chat messages."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Markdown, Static
from textual.widget import Widget


class MessageBubble(Widget):
    """A single chat message bubble (user or assistant)."""

    DEFAULT_CSS = """
    MessageBubble {
        margin: 0 0 1 0;
        padding: 0;
    }
    MessageBubble.user {
        align: right middle;
    }
    MessageBubble.assistant {
        align: left middle;
    }
    MessageBubble > .bubble-header {
        text-style: bold;
        margin: 0 1;
    }
    MessageBubble.user > .bubble-header {
        color: $accent;
    }
    MessageBubble.assistant > .bubble-header {
        color: $success;
    }
    MessageBubble > Markdown {
        margin: 0 1;
        padding: 0 1;
        background: transparent;
    }
    """

    def __init__(self, role: str, initial_text: str = "", **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.role = role
        self._text = initial_text
        self.add_class(role)

    def compose(self) -> ComposeResult:
        label = "You" if self.role == "user" else "Claude"
        yield Static(label, classes="bubble-header")
        yield Markdown(self._text or "▋", id=f"md-{self.id}")

    @property
    def _markdown(self) -> Markdown:
        return self.query_one(Markdown)

    def stream_update(self, full_text: str) -> None:
        """Called from call_later to update the Markdown widget with accumulated text."""
        self._text = full_text
        # Show streaming cursor when text is non-empty
        display = full_text + " ▋" if full_text else "▋"
        self._markdown.update(display)

    def finalize(self, full_text: str) -> None:
        """Called when streaming is complete — removes cursor."""
        self._text = full_text
        self._markdown.update(full_text or "*[empty response]*")
