"""SessionPickerScreen — modal for Ctrl+O to load a past session."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Label, Static

from claude_tui.config import config
from claude_tui.session import Session, list_sessions


class SessionPickerScreen(ModalScreen[Session | None]):
    """Modal screen to pick a saved session."""

    BINDINGS = [
        Binding("escape", "dismiss(None)", "Close", show=True),
        Binding("enter", "select_session", "Open", show=True),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="session-dialog"):
            yield Label("Open Session", id="session-title")
            yield DataTable(id="session-list", cursor_type="row")
            with Vertical(classes="dialog-footer"):
                yield Button("Open", id="open-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn")

    def on_mount(self) -> None:
        table = self.query_one("#session-list", DataTable)
        table.add_columns("Title", "Updated", "Messages")
        sessions = list_sessions(config.sessions_dir)
        if not sessions:
            table.add_row("No sessions found", "", "")
            return
        for session in sessions:
            updated = session.updated_at[:16].replace("T", " ")
            table.add_row(session.title, updated, str(len(session.messages)))
        self._sessions = sessions
        table.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "open-btn":
            self.action_select_session()

    def action_select_session(self) -> None:
        table = self.query_one("#session-list", DataTable)
        if not hasattr(self, "_sessions") or not self._sessions:
            self.dismiss(None)
            return
        row_idx = table.cursor_row
        if 0 <= row_idx < len(self._sessions):
            self.dismiss(self._sessions[row_idx])
        else:
            self.dismiss(None)
