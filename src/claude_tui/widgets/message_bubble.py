"""MessageBubble widget — wraps Textual Markdown for chat messages."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Markdown
from textual.widget import Widget


class MessageBubble(Widget):
    """A single chat message bubble (user or assistant)."""

    DEFAULT_CSS = """
    MessageBubble {
        width: 100%;
        margin: 0;
        padding: 0;
    }
    MessageBubble.user {
        background: transparent;
        margin: 0 0 0 0;
        padding: 0;
        height: auto;
    }
    MessageBubble.user > Markdown {
        background: transparent;
        padding: 0 1;
        margin: 0;
    }
    MessageBubble.assistant {
        border: round $primary;
        border-title-color: $text;
        border-title-align: center;
        margin: 1 0;
        padding: 0 1;
        height: auto;
    }
    MessageBubble.assistant > Markdown {
        background: transparent;
        padding: 0;
        margin: 0;
    }
    """

    def __init__(
        self,
        role: str,
        initial_text: str = "",
        model: str = "Claude",
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.role = role
        self._text = initial_text
        self._model = model
        self.add_class(role)

    def compose(self) -> ComposeResult:
        yield Markdown(self._build(self._text), id=f"md-{self.id}")

    def on_mount(self) -> None:
        if self.role == "assistant":
            self.border_title = self._model

    def _build(self, text: str, cursor: bool = False) -> str:
        body = (text + " ▋") if cursor else (text or "")
        if self.role == "user":
            return f"**You:** {body}"
        return body

    @property
    def _markdown(self) -> Markdown:
        return self.query_one(f"#md-{self.id}", Markdown)

    def stream_update(self, full_text: str) -> None:
        """Sync helper used when calling from outside an async context."""
        self._text = full_text
        self._markdown.update(self._build(full_text, cursor=True))

    async def async_stream_update(self, full_text: str) -> None:
        """Await the Markdown update so layout is settled before scrolling."""
        self._text = full_text
        await self._markdown.update(self._build(full_text, cursor=True))

    async def async_finalize(self, full_text: str) -> None:
        """Await final Markdown update — removes streaming cursor."""
        self._text = full_text
        await self._markdown.update(self._build(full_text or "*[empty response]*"))

    def finalize(self, full_text: str) -> None:
        """Sync finalize for non-streaming contexts."""
        self._text = full_text
        self._markdown.update(self._build(full_text or "*[empty response]*"))
