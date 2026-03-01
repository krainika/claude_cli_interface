"""MessageBubble widget — wraps Textual Markdown for chat messages."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Markdown
from textual.widget import Widget


class MessageBubble(Widget):
    """A single chat message bubble (user or assistant)."""

    DEFAULT_CSS = """
    MessageBubble {
        margin: 0;
        padding: 0;
    }
    MessageBubble.user {
        background: $primary 10%;
    }
    MessageBubble.assistant {
        background: $surface;
    }
    MessageBubble > Markdown {
        background: transparent;
        padding: 0 1;
        margin: 0;
    }
    """

    _PREFIXES = {"user": "**You:** ", "assistant": "**Claude:** "}

    def __init__(self, role: str, initial_text: str = "", **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.role = role
        self._text = initial_text
        self.add_class(role)

    def compose(self) -> ComposeResult:
        yield Markdown(self._build(self._text), id=f"md-{self.id}")

    def _build(self, text: str, cursor: bool = False) -> str:
        prefix = self._PREFIXES.get(self.role, "")
        body = (text + " ▋") if cursor else (text or "")
        return prefix + body

    @property
    def _markdown(self) -> Markdown:
        return self.query_one(f"#md-{self.id}", Markdown)

    def stream_update(self, full_text: str) -> None:
        """Called from call_later; updates Markdown with the full accumulated text."""
        self._text = full_text
        self._markdown.update(self._build(full_text, cursor=True))

    def finalize(self, full_text: str) -> None:
        """Called when streaming is complete — removes the cursor."""
        self._text = full_text
        self._markdown.update(self._build(full_text or "*[empty response]*"))
