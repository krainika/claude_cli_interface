"""ChatView — scrollable container for MessageBubble widgets."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from claude_tui.widgets.message_bubble import MessageBubble


class ChatView(VerticalScroll):
    """Scrollable container that holds all MessageBubble widgets."""

    DEFAULT_CSS = """
    ChatView {
        padding: 0 1;
    }
    ChatView > .empty-hint {
        color: $text-muted;
        text-align: center;
        margin-top: 4;
    }
    ChatView > .empty-hint.hidden {
        display: none;
    }
    """

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._bubble_count = 0

    def compose(self) -> ComposeResult:
        yield Static(
            "Start a conversation — press Ctrl+S to send",
            classes="empty-hint",
            id="empty-hint",
        )

    @property
    def _hint(self) -> Static:
        return self.query_one("#empty-hint", Static)

    def _show_hint(self) -> None:
        self._hint.remove_class("hidden")

    def _hide_hint(self) -> None:
        self._hint.add_class("hidden")

    def add_message(self, role: str, text: str = "", model: str = "Claude") -> MessageBubble:
        """Mount a new MessageBubble and return it."""
        self._hide_hint()
        self._bubble_count += 1
        bubble = MessageBubble(
            role=role,
            initial_text=text,
            model=model,
            id=f"bubble-{self._bubble_count}",
        )
        self.mount(bubble)
        self.scroll_end(animate=False)
        return bubble

    def clear_messages(self) -> None:
        """Remove all bubbles and restore the empty hint."""
        for bubble in self.query(MessageBubble):
            bubble.remove()
        # Do NOT reset _bubble_count — remove() is async so old widgets linger
        # briefly in the DOM; keeping the counter monotonic avoids duplicate IDs.
        self._show_hint()
