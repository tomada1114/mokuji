"""Repo-wide Markdown search modal (the capital ``S`` key)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.content import Content
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from .._repo_search import search_repo
from .._theme import ACCENT
from .footer import format_hints

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult

    from .._repo_search import Hit, RepoSearchResults

MIN_QUERY_CHARS = 2

HINTS = format_hints((("Up/Down", "move"), ("Enter", "open"), ("Esc", "close")))


class RepoSearchScreen(ModalScreen[tuple["Hit", str] | None]):
    """Centered modal: search every Markdown file under the app root.

    Dismisses ``(selected Hit, query)`` so the caller can open the file
    and seed the in-file search, or ``None`` on a plain close (mirrors
    HelpScreen's dismiss-a-value pattern).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss_screen", "close", show=False),
        Binding("up", "cursor_up", "up", show=False),
        Binding("down", "cursor_down", "down", show=False),
    ]

    def __init__(self, root: Path) -> None:
        """Create the modal, searching Markdown files under *root*."""
        super().__init__()
        self._root = root
        self._results: RepoSearchResults | None = None
        self._results_query: str | None = None
        self._selected = 0

    def compose(self) -> ComposeResult:
        """Lay out the query input, live results body, and key hints."""
        with Vertical(id="repo-search-panel"):
            yield Input(placeholder="search all files", id="repo-search-input")
            yield Static(id="repo-search-body")
            yield Static(HINTS, id="repo-search-hints")

    def on_mount(self) -> None:
        """Focus the query input and show the initial placeholder body."""
        self.query_one("#repo-search-input", Input).focus()
        self._render_body()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Re-scan (in a worker) as the query changes."""
        event.stop()
        query = event.value
        self._selected = 0
        if len(query) < MIN_QUERY_CHARS:
            self._results = None
            self._results_query = None
            self._render_body()
            return
        self._render_body()
        self._search_worker(query)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter: open the selected hit, seeding the in-file search."""
        event.stop()
        if self._results is None or not self._results.hits:
            return
        self.dismiss((self._results.hits[self._selected], event.value))

    def action_cursor_up(self) -> None:
        """Move the selection to the previous hit, wrapping."""
        self._move_selection(-1)

    def action_cursor_down(self) -> None:
        """Move the selection to the next hit, wrapping."""
        self._move_selection(1)

    def action_dismiss_screen(self) -> None:
        """Esc: close with no change."""
        self.dismiss(None)

    def _move_selection(self, delta: int) -> None:
        if self._results is None or not self._results.hits:
            return
        self._selected = (self._selected + delta) % len(self._results.hits)
        self._render_body()

    @work(exclusive=True, group="repo-search")
    async def _search_worker(self, query: str) -> None:
        results = search_repo(self._root, query)
        self._apply_results(query, results)

    def _apply_results(self, query: str, results: RepoSearchResults) -> None:
        if query != self.query_one("#repo-search-input", Input).value:
            return  # superseded by a newer keystroke
        self._results = results
        self._results_query = query
        self._selected = 0
        self._render_body()

    def _render_body(self) -> None:
        body = self.query_one("#repo-search-body", Static)
        query = self.query_one("#repo-search-input", Input).value
        if len(query) < MIN_QUERY_CHARS:
            body.update("keep typing to search…")
            return
        if self._results is None or self._results_query != query:
            body.update("searching…")
            return
        if not self._results.hits:
            body.update(Content(f"no matches for {query!r}"))
            return
        body.update(self._format_results(self._results))

    def _format_results(self, results: RepoSearchResults) -> Content:
        header = f"{results.match_count} matches · {results.file_count} files"
        if results.truncated:
            header += f" · showing first {len(results.hits)} · refine query"
        content = Content(f"{header}\n\n")
        last_path = None
        for index, hit in enumerate(results.hits):
            if hit.path != last_path:
                content += Content(f"> {hit.path}\n")
                last_path = hit.path
            marker = "▸" if index == self._selected else " "
            prefix = Content(f"{marker} {hit.line + 1:>5} | ")
            excerpt = Content(hit.text).stylize(
                f"bold {ACCENT}", hit.span_start, hit.span_end
            )
            content += prefix + excerpt + Content("\n")
        return content
