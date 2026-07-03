"""Application shell for mokuji."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.app import App
from textual.binding import Binding, BindingType
from textual.widgets import Input

from .._document import load_document
from .._theme import BG_CHROME, SUMI_THEME, TEXT_MUTED
from .footer import KeyGuide
from .viewer import ViewerPane

if TYPE_CHECKING:
    from pathlib import Path

    from textual import events
    from textual.app import ComposeResult

_COUNT_DIGITS = frozenset("123456789")


class MokujiApp(App[None]):
    """The mokuji TUI application."""

    CSS = f"""
    Screen {{
        background: $background;
    }}
    ViewerPane {{
        background: $background;
        align-horizontal: center;
    }}
    ViewerPane > .content {{
        max-width: 100;
        width: 100%;
        padding: 0 2;
        background: $background;
    }}
    ViewerPane > .notice {{
        color: {TEXT_MUTED};
        text-align: center;
        padding: 2 2;
    }}
    KeyGuide {{
        dock: bottom;
        height: 1;
        background: {BG_CHROME};
        color: {TEXT_MUTED};
        padding: 0 1;
    }}
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "quit"),
    ]

    def __init__(self, root: Path, initial_file: Path | None = None) -> None:
        """Create the app rooted at *root*, optionally opening *initial_file*."""
        super().__init__()
        self._root = root.resolve()
        self._initial_file = initial_file.resolve() if initial_file else None
        self._pending_count = ""
        self._pending_g = False

    def compose(self) -> ComposeResult:
        """Lay out the viewer and the footer key guide."""
        yield ViewerPane(id="viewer")
        yield KeyGuide(id="footer")

    async def on_mount(self) -> None:
        """Activate the sumi theme, focus the viewer, and open the initial file."""
        self.register_theme(SUMI_THEME)
        self.theme = "sumi"
        viewer = self.query_one(ViewerPane)
        viewer.focus()
        if self._initial_file is not None:
            await viewer.show_document(load_document(self._initial_file))

    def on_key(self, event: events.Key) -> None:
        """Drive the Vim-style multi-key sequence machine (gg, gt, gT, Ngt)."""
        if isinstance(self.focused, Input):
            self._clear_key_sequence()
            return
        key = event.key
        if key == "g":
            event.prevent_default()
            event.stop()
            if self._pending_g:
                self._clear_key_sequence()
                self.query_one(ViewerPane).scroll_top()
            else:
                self._pending_g = True
            return
        if self._pending_g and key in {"t", "T"}:
            event.prevent_default()
            event.stop()
            count = int(self._pending_count) if self._pending_count else None
            self._clear_key_sequence()
            if key == "t":
                self._tab_next(count)
            else:
                self._tab_prev()
            return
        if key in _COUNT_DIGITS:
            event.prevent_default()
            event.stop()
            if self._pending_g:
                self._clear_key_sequence()
            self._pending_count += key
            return
        self._clear_key_sequence()

    def _clear_key_sequence(self) -> None:
        self._pending_count = ""
        self._pending_g = False

    def _tab_next(self, count: int | None) -> None:
        """Switch to the next (or *count*-th) tab; single-document for now."""

    def _tab_prev(self) -> None:
        """Switch to the previous tab; single-document for now."""
