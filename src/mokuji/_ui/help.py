"""The full keybinding reference modal (the ``?`` key)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

HELP_TEXT = """\
READING              NAVIGATION
j/k   scroll         e     file tree
d/u   half page      t     table of contents
f/b   page           gt/gT next/prev tab
gg/G  top/bottom     1-9gt Nth tab
/     search         x     close tab
n/N   next/prev      C-o/C-i back/forward
r     reload         Enter follow link/open

Ctrl+g toggle key guide    q quit

press ? or Esc to close\
"""

FOOTER_HIDDEN_NOTE = "footer hidden — Ctrl+g to restore"


class HelpScreen(ModalScreen[None]):
    """Centered modal listing every keybinding grouped by category."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("question_mark", "dismiss_help", "close", show=False),
        Binding("escape", "dismiss_help", "close", show=False),
        Binding("q", "dismiss_help", "close", show=False),
    ]

    def __init__(self, *, footer_hidden: bool = False) -> None:
        """Remember whether to point out the hidden footer (req 2.7)."""
        super().__init__()
        self._footer_hidden = footer_hidden

    def compose(self) -> ComposeResult:
        """Lay out the bordered help panel."""
        body = HELP_TEXT
        if self._footer_hidden:
            body = f"{body}\n\n{FOOTER_HIDDEN_NOTE}"
        with Vertical(id="help-panel"):
            yield Static("mokuji — keys", id="help-title")
            yield Static(body, id="help-body")

    def action_dismiss_help(self) -> None:
        """Close the modal."""
        self.dismiss()
