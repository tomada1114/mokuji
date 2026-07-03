"""In-file search: the footer input, match state, and n/N navigation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding, BindingType
from textual.widgets import Input

from .._search import find_matches
from .footer import KeyGuide
from .viewer import ViewerPane

if TYPE_CHECKING:
    from .._search import Match
    from .app import MokujiApp


class SearchInput(Input):
    """One-line search input shown in place of the footer."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "app.cancel_search", "cancel", show=False),
    ]


@dataclass(slots=True)
class ActiveSearch:
    """The confirmed query and its matches in the active document."""

    query: str
    matches: tuple[Match, ...]
    index: int


class SearchController:
    """Owns search state and keeps viewer highlights and footer in sync."""

    def __init__(self, app: MokujiApp) -> None:
        """Attach to *app*, which supplies the widgets and flash channel."""
        self._app = app
        self._active: ActiveSearch | None = None

    @property
    def is_active(self) -> bool:
        """Whether a confirmed search is currently showing matches."""
        return self._active is not None

    def open_input(self) -> None:
        """Show the search input over the footer and focus it."""
        self._app.query_one(KeyGuide).display = False
        search_input = self._app.query_one(SearchInput)
        search_input.value = ""
        search_input.display = True
        search_input.focus()

    def cancel_input(self) -> None:
        """Close the input without searching and restore the footer."""
        self._close_input()
        self.dismiss()

    def submit(self, query: str) -> None:
        """Confirm *query*: jump to the first match from the current position."""
        self._close_input()
        if not query:
            self.dismiss()
            return
        viewer = self._app.query_one(ViewerPane)
        document = viewer.document
        if document is None:
            return
        matches = find_matches(document.text, query)
        if not matches:
            self.dismiss()
            self._app.flash(f"no match: {query}")
            return
        current_line = self._current_line(viewer)
        index = next((i for i, m in enumerate(matches) if m.line >= current_line), 0)
        self._active = ActiveSearch(query=query, matches=matches, index=index)
        self._show_current()

    def next(self) -> None:
        """Jump to the next match, wrapping with a flash (req 2.6)."""
        self._step(1)

    def prev(self) -> None:
        """Jump to the previous match, wrapping with a flash (req 2.6)."""
        self._step(-1)

    def dismiss(self) -> None:
        """Clear highlights, match state, and the footer counter."""
        self._active = None
        self._app.query_one(ViewerPane).clear_matches()
        self._app.query_one(KeyGuide).set_default(None)

    def _step(self, delta: int) -> None:
        if self._active is None:
            return
        total = len(self._active.matches)
        index = self._active.index + delta
        if index >= total or index < 0:
            index %= total
            self._app.flash("search wrapped")
        self._active.index = index
        self._show_current()

    def _show_current(self) -> None:
        if self._active is None:
            return
        viewer = self._app.query_one(ViewerPane)
        match = self._active.matches[self._active.index]
        viewer.scroll_to_line(match.line)
        viewer.show_matches(self._active.matches, self._active.index)
        status = (
            f"match {self._active.index + 1}/{len(self._active.matches)}"
            f" · line {match.line + 1}"
        )
        self._app.query_one(KeyGuide).set_default(status)

    def _close_input(self) -> None:
        search_input = self._app.query_one(SearchInput)
        search_input.display = False
        self._app.query_one(KeyGuide).display = True
        self._app.query_one(ViewerPane).focus()

    @staticmethod
    def _current_line(viewer: ViewerPane) -> int:
        document = viewer.document
        if document is None or not document.text or viewer.max_scroll_y == 0:
            return 0
        total_lines = document.text.count("\n")
        return round(viewer.scroll_y / viewer.max_scroll_y * total_lines)
