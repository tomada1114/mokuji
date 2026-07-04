"""Tab and history navigation: owns all TabState and the Tabs widget sync."""

from __future__ import annotations

from itertools import count
from typing import TYPE_CHECKING

from textual.widgets import Markdown, Tab, Tabs

from .._document import load_document
from .._errors import DocumentLoadError
from .sidebar import FilesTree, Sidebar, SidebarMode
from .tabs import TabState, next_tab_index, prev_tab_index, tab_labels
from .viewer import ViewerPane

if TYPE_CHECKING:
    from pathlib import Path

    from .._document import Document
    from .app import MokujiApp


class TabNavigator:
    """Drives tab lifecycle, per-tab jump history, and anchor jumps."""

    def __init__(self, app: MokujiApp) -> None:
        """Attach to *app*, which supplies the widgets and flash channel."""
        self._app = app
        self._states: list[TabState] = []
        self._active = 0
        self._uid = count()

    @property
    def tab_count(self) -> int:
        """Number of open tabs."""
        return len(self._states)

    @property
    def active_index(self) -> int:
        """Index of the active tab (0 when no tabs are open)."""
        return self._active

    @property
    def active_document(self) -> Document | None:
        """The document shown in the active tab, if any."""
        if not self._states:
            return None
        return self._states[self._active].document

    def index_of_tab_id(self, tab_id: str | None) -> int | None:
        """Map a Tabs widget tab id back to a state index."""
        for index, state in enumerate(self._states):
            if state.tab_id == tab_id:
                return index
        return None

    async def open_path(
        self, path: Path, *, allow_large: bool = False, anchor: str | None = None
    ) -> None:
        """Open *path* in the current tab, focusing an existing tab if open."""
        resolved = path.resolve()
        existing = self._find_tab(resolved)
        if existing is not None and existing != self._active:
            await self.switch_to(existing)
            if anchor:
                self.jump_to_anchor(anchor)
            return
        await self._navigate_current(resolved, anchor, allow_large=allow_large)

    async def open_link(self, path: Path, *, anchor: str | None = None) -> None:
        """Navigate to *path* within the CURRENT tab (Markdown link following).

        Unlike :meth:`open_path` (used by tree/search opens), this never
        switches to another tab that already has *path* open — Ctrl+o
        must return to where the user was reading, not into some other
        tab's history.
        """
        await self._navigate_current(path.resolve(), anchor)

    async def open_in_new_tab(self, path: Path) -> None:
        """Open *path* in a new tab, focusing an existing tab if open."""
        resolved = path.resolve()
        existing = self._find_tab(resolved)
        if existing is not None:
            if existing != self._active:
                await self.switch_to(existing)
            return
        document = self._load_or_flash(resolved)
        if document is None:
            return
        self._save_scroll()
        state = TabState(
            document=document,
            tab_id=f"tab-{next(self._uid)}",
            history=[(resolved, None)],
        )
        self._states.append(state)
        self._active = len(self._states) - 1
        tabs = self._app.query_one(Tabs)
        await tabs.add_tab(Tab(state.document.path.name, id=state.tab_id))
        tabs.active = state.tab_id
        self._update_tab_bar()
        await self._render_active()

    async def close_tab(self) -> None:
        """Close the current tab; the last close shows the empty state."""
        if not self._states:
            return
        state = self._states.pop(self._active)
        if self._states:
            self._active = min(self._active, len(self._states) - 1)
        else:
            self._active = 0
        await self._app.query_one(Tabs).remove_tab(state.tab_id)
        if not self._states:
            await self._app.query_one(ViewerPane).show_empty()
            sidebar = self._app.query_one(Sidebar)
            sidebar.set_document(None)
            self._update_tab_bar()
            sidebar.show_mode(SidebarMode.FILES)
            sidebar.display = True
            self._app.query_one(FilesTree).focus()
            return
        self._app.query_one(Tabs).active = self._states[self._active].tab_id
        self._update_tab_bar()
        await self._render_active(restore_scroll=True)

    async def reload(self) -> None:
        """Re-read the active document from disk, keeping scroll (req 2.4)."""
        if not self._states:
            return
        state = self._states[self._active]
        path = state.document.path
        if not path.exists():
            self._app.flash(f"file no longer exists: {path.name}")
            return
        self._save_scroll()
        document = self._load_or_flash(path, allow_large=True)
        if document is None:
            return
        state.document = document
        await self._render_active(restore_scroll=True)
        self._app.flash("reloaded")

    async def history_step(self, delta: int) -> None:
        """Move back (-1) or forward (+1) in the active tab's history."""
        if not self._states:
            return
        state = self._states[self._active]
        target = state.history_index + delta
        if not 0 <= target < len(state.history):
            return
        path, anchor = state.history[target]
        document = self._load_or_flash(path)
        if document is None:
            return
        state.history_index = target
        state.document = document
        state.scroll_y = 0.0
        await self._render_active(anchor=anchor)

    async def switch_to(self, index: int) -> None:
        """Activate the tab at *index*, preserving scroll positions."""
        self._save_scroll()
        self._active = index
        state = self._states[index]
        tabs = self._app.query_one(Tabs)
        if tabs.active != state.tab_id:
            tabs.active = state.tab_id
        await self._render_active(restore_scroll=True)

    def tab_next(self, tab_count: int | None) -> None:
        """Schedule a switch for ``gt`` / ``<N>gt``."""
        if len(self._states) > 1:
            index = next_tab_index(self._active, tab_count, len(self._states))
            if index != self._active:
                self._app.call_next(self.switch_to, index)

    def tab_prev(self) -> None:
        """Schedule a switch for ``gT``."""
        if len(self._states) > 1:
            index = prev_tab_index(self._active, len(self._states))
            self._app.call_next(self.switch_to, index)

    def jump_to_anchor(self, anchor: str, *, line: int | None = None) -> None:
        """Scroll the viewer to *anchor*, preferring Markdown anchors."""
        viewer = self._app.query_one(ViewerPane)
        markdown = viewer.query(Markdown)
        if markdown and markdown.first().goto_anchor(anchor):
            return
        document = viewer.document
        if line is None and document is not None:
            heading = next((h for h in document.headings if h.slug == anchor), None)
            line = heading.line if heading else None
        if line is None or document is None or not document.text:
            self._app.flash(f"anchor not found: {anchor}")
            return
        total_lines = max(1, document.text.count("\n"))
        target = round(line / total_lines * viewer.max_scroll_y)
        viewer.scroll_to(y=target, animate=False)

    async def _navigate_current(
        self, path: Path, anchor: str | None, *, allow_large: bool = False
    ) -> None:
        document = self._load_or_flash(path, allow_large=allow_large)
        if document is None:
            return
        entry = (path, anchor)
        if not self._states:
            state = TabState(
                document=document,
                tab_id=f"tab-{next(self._uid)}",
                history=[entry],
            )
            self._states.append(state)
            self._active = 0
            tabs = self._app.query_one(Tabs)
            await tabs.add_tab(Tab(path.name, id=state.tab_id))
            tabs.active = state.tab_id
        else:
            state = self._states[self._active]
            if state.history[state.history_index] != entry:
                del state.history[state.history_index + 1 :]
                state.history.append(entry)
                state.history_index += 1
            state.document = document
            state.scroll_y = 0.0
        self._update_tab_bar()
        await self._render_active(anchor=anchor)

    async def _render_active(
        self, *, anchor: str | None = None, restore_scroll: bool = False
    ) -> None:
        self._app.dismiss_search()
        state = self._states[self._active]
        viewer = self._app.query_one(ViewerPane)
        await viewer.show_document(state.document)
        self._app.query_one(Sidebar).set_document(state.document)
        if anchor:
            self._app.call_after_refresh(self.jump_to_anchor, anchor)
        elif restore_scroll:
            scroll_y = state.scroll_y
            self._app.call_after_refresh(
                lambda: viewer.scroll_to(y=scroll_y, animate=False)
            )

    def _load_or_flash(
        self, path: Path, *, allow_large: bool = False
    ) -> Document | None:
        try:
            return load_document(path, allow_large=allow_large)
        except DocumentLoadError as error:
            if isinstance(error.__cause__, PermissionError):
                self._app.flash(f"permission denied: {path.name}")
            else:
                self._app.flash(str(error))
            return None

    def _find_tab(self, path: Path) -> int | None:
        for index, state in enumerate(self._states):
            if state.document.path == path:
                return index
        return None

    def _save_scroll(self) -> None:
        if self._states:
            self._states[self._active].scroll_y = self._app.query_one(
                ViewerPane
            ).scroll_y

    def _update_tab_bar(self) -> None:
        tabs = self._app.query_one(Tabs)
        labels = tab_labels([s.document.path for s in self._states])
        for state, label in zip(self._states, labels, strict=True):
            tabs.query_one(f"#{state.tab_id}", Tab).label = label
        tabs.display = len(self._states) > 1
