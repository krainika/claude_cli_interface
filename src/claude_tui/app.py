"""ClaudeTUIApp — the main Textual application."""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Label, Static

from claude_tui.api import stream_response
from claude_tui.attachments import AttachmentError, load_attachment
from claude_tui.config import config, save_api_key
from claude_tui.screens.help_screen import HelpScreen
from claude_tui.screens.key_prompt import KeyPromptScreen
from claude_tui.screens.session_picker import SessionPickerScreen
from claude_tui.session import (
    ChatMessage,
    DocumentContent,
    ImageContent,
    Session,
    TextContent,
)
from claude_tui.widgets.attachment_bar import AttachmentBar
from claude_tui.widgets.chat_view import ChatView
from claude_tui.widgets.input_bar import InputBar, SmartTextArea
from claude_tui.widgets.message_bubble import MessageBubble
from claude_tui.widgets.status_bar import StatusBar


class ClaudeTUIApp(App):
    """Full-screen terminal UI for Claude."""

    CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"

    BINDINGS = [
        Binding("ctrl+s", "send_message", "Send", show=True),
        Binding("ctrl+n", "new_session", "New", show=True),
        Binding("ctrl+o", "open_session", "Open", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    TITLE = "Claude TUI"

    def __init__(self) -> None:
        super().__init__()
        self._session = Session()
        self._model = config.default_model
        self._system = config.system_prompt
        self._pending_attachments: list[Path] = []
        self._streaming = False
        self._total_tokens = 0

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Horizontal(
            Label("Claude TUI", id="header-title"),
            Label(self._session.title, id="header-session"),
            id="app-header",
        )
        yield ChatView(id="chat-view")
        yield AttachmentBar(id="attachment-bar")
        yield InputBar(id="input-bar")
        yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._update_header()
        self._update_status()
        if not config.has_api_key:
            self.call_after_refresh(self._prompt_for_api_key)
        else:
            self.status_bar.set_ready()
        self.input_bar.text_area.focus()

    def _prompt_for_api_key(self) -> None:
        def on_key_entered(key: str | None) -> None:
            if key:
                save_api_key(key)
                config.api_key = key
                self.status_bar.set_ready()
            else:
                self.status_bar.set_error("No API key set — run /key to enter one")

        self.push_screen(KeyPromptScreen(), on_key_entered)

    # ------------------------------------------------------------------
    # Widget accessors
    # ------------------------------------------------------------------

    @property
    def chat_view(self) -> ChatView:
        return self.query_one("#chat-view", ChatView)

    @property
    def input_bar(self) -> InputBar:
        return self.query_one("#input-bar", InputBar)

    @property
    def status_bar(self) -> StatusBar:
        return self.query_one("#status-bar", StatusBar)

    @property
    def attachment_bar(self) -> AttachmentBar:
        return self.query_one("#attachment-bar", AttachmentBar)

    # ------------------------------------------------------------------
    # Header & status helpers
    # ------------------------------------------------------------------

    def _update_header(self) -> None:
        try:
            self.query_one("#header-session", Label).update(self._session.title)
            self.sub_title = self._session.title
        except Exception:
            pass

    def _update_status(self) -> None:
        self.status_bar.set_model(self._model)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_send_message(self) -> None:
        """Triggered by Ctrl+S or the Send button."""
        if self._streaming:
            return
        raw = self.input_bar.get_text().strip()
        if not raw and not self._pending_attachments:
            return
        # Handle slash commands
        if raw.startswith("/"):
            handled = self._handle_slash_command(raw)
            if handled:
                self.input_bar.clear()
                return
        self._do_send(raw)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            self.action_send_message()

    def on_smart_text_area_file_paste(self, event: SmartTextArea.FilePaste) -> None:
        """Handle drag-and-drop file paths pasted into the input area."""
        for path in event.paths:
            self._attach_file(str(path))

    def action_new_session(self) -> None:
        self._session = Session()
        self.chat_view.clear_messages()
        self.attachment_bar.clear()
        self._pending_attachments.clear()
        self._total_tokens = 0
        self._update_header()
        self.status_bar.set_ready()
        self.input_bar.clear()

    def action_open_session(self) -> None:
        def on_session_selected(session: Session | None) -> None:
            if session is None:
                return
            self._load_session(session)

        self.push_screen(SessionPickerScreen(), on_session_selected)

    # ------------------------------------------------------------------
    # Slash command handling
    # ------------------------------------------------------------------

    def _handle_slash_command(self, raw: str) -> bool:
        """
        Parse and execute a slash command.
        Returns True if the command was handled (so the caller clears input).
        """
        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        match cmd:
            case "/help":
                self.push_screen(HelpScreen())
                return True
            case "/key":
                self._prompt_for_api_key()
                return True
            case "/clear":
                self.action_new_session()
                return True
            case "/model":
                if not arg:
                    self.status_bar.set_error("Usage: /model <model-id>")
                    return True
                self._model = arg.strip()
                self._update_status()
                self.status_bar.set_status(f"Model set to {self._model}")
                return True
            case "/system":
                if not arg:
                    self.status_bar.set_error("Usage: /system <prompt text>")
                    return True
                self._system = arg.strip()
                self.status_bar.set_status("System prompt updated")
                return True
            case "/attach":
                if not arg:
                    self.status_bar.set_error("Usage: /attach <file-path>")
                    return True
                self._attach_file(arg.strip())
                return True
            case _:
                return False

    def _attach_file(self, path_str: str) -> None:
        p = Path(path_str).expanduser()
        try:
            # Validate by loading (will raise on error)
            load_attachment(p)
            self._pending_attachments.append(p)
            self.attachment_bar.add_attachment(p.name)
            self.status_bar.set_status(f"Attached: {p.name}")
        except AttachmentError as e:
            self.status_bar.set_error(str(e))

    # ------------------------------------------------------------------
    # Sending a message
    # ------------------------------------------------------------------

    def _do_send(self, text: str) -> None:
        """Build the user message, add to chat, start streaming worker."""
        # Build content blocks
        content_blocks = []
        for path in self._pending_attachments:
            try:
                block = load_attachment(path)
                content_blocks.append(block)
            except AttachmentError as e:
                self.status_bar.set_error(str(e))
                return

        if text:
            content_blocks.append(TextContent(text=text))

        if not content_blocks:
            return

        # Add user message to session & chat
        user_msg = ChatMessage(role="user", content=content_blocks)
        self._session.add_message(user_msg)
        self.chat_view.add_message("user", self._render_user_text(content_blocks, text))

        # Clear input and attachments
        self.input_bar.clear()
        self.attachment_bar.clear()
        self._pending_attachments.clear()

        # Update header with new title (set after first message)
        self._update_header()

        # Add assistant bubble (streaming target)
        assistant_bubble = self.chat_view.add_message("assistant", "")

        # Disable input while streaming
        self._streaming = True
        self.input_bar.set_enabled(False)
        self.status_bar.set_streaming()

        # Launch async worker
        self.run_worker(self._stream_worker(assistant_bubble), exclusive=False, exit_on_error=False)

    def _render_user_text(self, blocks: list, text: str) -> str:
        """Build Markdown text to display in the user bubble."""
        parts = []
        for block in blocks:
            if isinstance(block, ImageContent):
                parts.append("*[image attached]*")
            elif isinstance(block, DocumentContent):
                if block.media_type == "application/pdf":
                    parts.append(f"*[PDF: {block.filename}]*")
                else:
                    parts.append(block.data)
        if text:
            parts.append(text)
        return "\n\n".join(parts)

    async def _stream_worker(self, bubble: MessageBubble) -> None:
        """Async Textual worker that calls the API and streams tokens."""
        try:
            api_messages = self._session.to_api_messages()

            token_count = 0

            def on_chunk(accumulated: str) -> None:
                nonlocal token_count
                token_count = len(accumulated.split())  # rough estimate
                self.call_later(bubble.stream_update, accumulated)
                self.call_later(self.status_bar.set_streaming, token_count)
                self.call_later(lambda: self.chat_view.scroll_end(animate=False))

            full_text, total_tokens = await stream_response(
                messages=api_messages,
                model=self._model,
                system=self._system,
                max_tokens=config.max_tokens,
                on_chunk=on_chunk,
            )

            self._total_tokens += total_tokens

            # Finalize the bubble (remove streaming cursor)
            self.call_later(bubble.finalize, full_text)

            # Save assistant message to session
            assistant_msg = ChatMessage(
                role="assistant",
                content=[TextContent(text=full_text)],
            )
            self._session.add_message(assistant_msg)

            # Persist session to disk
            self._session.save(config.sessions_dir)

            self.call_later(self.status_bar.set_ready, self._total_tokens)

        except Exception as e:
            error_msg = str(e)
            self.call_later(bubble.finalize, f"*Error: {error_msg}*")
            self.call_later(self.status_bar.set_error, error_msg)

        finally:
            self._streaming = False
            self.call_later(self.input_bar.set_enabled, True)
            self.call_later(self.input_bar.text_area.focus)

    # ------------------------------------------------------------------
    # Session loading
    # ------------------------------------------------------------------

    def _load_session(self, session: Session) -> None:
        self._session = session
        self.chat_view.clear_messages()
        self._total_tokens = 0

        for msg in session.messages:
            text = self._build_display_text(msg)
            self.chat_view.add_message(msg.role, text)

        self._update_header()
        self.status_bar.set_ready(self._total_tokens)
        self.input_bar.clear()

    def _build_display_text(self, msg: ChatMessage) -> str:
        parts = []
        for block in msg.content:
            if isinstance(block, TextContent):
                parts.append(block.text)
            elif isinstance(block, ImageContent):
                parts.append("*[image]*")
            elif isinstance(block, DocumentContent):
                if block.media_type == "application/pdf":
                    parts.append(f"*[PDF: {block.filename}]*")
                else:
                    parts.append(block.data)
        return "\n\n".join(parts)
