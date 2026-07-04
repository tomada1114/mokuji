"""Type-to-filter for the FILES/TOC trees, sharing the footer search Input."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .footer import KeyGuide
from .search import SearchInput
from .sidebar import FilesTree, TocTree

if TYPE_CHECKING:
    from .app import MokujiApp


class TreeFilterController:
    """Narrows the focused FILES/TOC tree to nodes matching a typed query.

    Reuses the same footer :class:`SearchInput` as in-file search
    (design.md §2); ``MokujiApp`` dispatches to this controller instead
    of :class:`SearchController` while it owns the input.
    """

    def __init__(self, app: MokujiApp) -> None:
        """Attach to *app*, which supplies the widgets and focus state."""
        self._app = app
        self._tree: FilesTree | TocTree | None = None

    @property
    def is_active(self) -> bool:
        """Whether the input is currently open for tree filtering."""
        return self._tree is not None

    def open_input(self) -> None:
        """Show the search input over the footer, remembering the focused tree."""
        focused = self._app.focused
        if not isinstance(focused, FilesTree | TocTree):
            return
        self._tree = focused
        self._app.query_one(KeyGuide).display = False
        search_input = self._app.query_one(SearchInput)
        search_input.value = ""
        search_input.display = True
        search_input.focus()

    async def on_query_changed(self, query: str) -> None:
        """Live-narrow the tree as the query changes."""
        if self._tree is None:
            return
        if isinstance(self._tree, FilesTree):
            await self._tree.apply_type_filter(query)
        else:
            self._tree.apply_type_filter(query)

    async def submit(self, _query: str) -> None:
        """Enter: keep the filter, close the input, focus the first node."""
        tree = self._tree
        self._close_input()
        if tree is not None:
            tree.focus()
            if tree.cursor_line == -1 and tree.root.children:
                tree.cursor_line = 0

    async def cancel(self) -> None:
        """Esc: clear the filter, restore the full tree, close the input."""
        tree = self._tree
        self._close_input()
        if tree is not None:
            if isinstance(tree, FilesTree):
                await tree.clear_type_filter()
            else:
                tree.clear_type_filter()
            tree.focus()

    def _close_input(self) -> None:
        self._app.query_one(SearchInput).display = False
        self._app.query_one(KeyGuide).display = True
        self._tree = None
