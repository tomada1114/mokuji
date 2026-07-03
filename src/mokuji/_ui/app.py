"""Application shell for mokuji: layout, bindings, and event wiring."""

from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING, ClassVar

from textual.app import App
from textual.binding import Binding, BindingType
from textual.containers import Horizontal
from textual.widgets import DirectoryTree, Input, Markdown, Tabs, Tree

from .._document import ExternalLink, InternalLink, resolve_link
from .._theme import SUMI_THEME
from .footer import KeyGuide
from .keys import KeySequenceMachine
from .navigator import TabNavigator
from .sidebar import FilesTree, Sidebar, SidebarMode, TocTree
from .style import APP_CSS
from .viewer import ViewerPane

if TYPE_CHECKING:
    from pathlib import Path

    from textual import events
    from textual.app import ComposeResult

    from .._document import Heading

NARROW_WIDTH = 80


class MokujiApp(App[None]):
    """The mokuji TUI application."""

    CSS = APP_CSS

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "quit"),
        Binding("e", "toggle_files", "files"),
        Binding("t", "toggle_toc", "toc"),
        Binding("x", "close_tab", "close tab"),
        Binding("ctrl+o", "history_back", "back"),
        Binding("ctrl+i", "history_forward", "forward"),
    ]

    def __init__(self, root: Path, initial_file: Path | None = None) -> None:
        """Create the app rooted at *root*, optionally opening *initial_file*."""
        super().__init__()
        self._root = root.resolve()
        self._initial_file = initial_file.resolve() if initial_file else None
        self._navigator = TabNavigator(self)
        self._keys = KeySequenceMachine(
            scroll_top=lambda: self.query_one(ViewerPane).scroll_top(),
            tab_next=self._navigator.tab_next,
            tab_prev=self._navigator.tab_prev,
        )
        self._narrow = False

    @property
    def tab_count(self) -> int:
        """Number of open tabs."""
        return self._navigator.tab_count

    @property
    def active_tab_index(self) -> int:
        """Index of the active tab (0 when no tabs are open)."""
        return self._navigator.active_index

    def compose(self) -> ComposeResult:
        """Lay out the tab bar, sidebar, viewer, and footer key guide."""
        tabs = Tabs(id="tabs")
        tabs.display = False
        yield tabs
        with Horizontal(id="main"):
            yield Sidebar(self._root, id="sidebar")
            yield ViewerPane(id="viewer")
        yield KeyGuide(id="footer")

    async def on_mount(self) -> None:
        """Activate the sumi theme, focus the viewer, and open the initial file."""
        self.register_theme(SUMI_THEME)
        self.theme = "sumi"
        self.query_one(ViewerPane).focus()
        if self._initial_file is not None:
            await self.open_path(self._initial_file)
        else:
            await self.query_one(ViewerPane).show_empty()

    def on_resize(self, event: events.Resize) -> None:
        """Auto-collapse the sidebar on narrow terminals (req 2.1)."""
        narrow = event.size.width < NARROW_WIDTH
        if narrow == self._narrow:
            return
        self._narrow = narrow
        sidebar = self.query_one(Sidebar)
        sidebar.remove_class("-overlay")
        sidebar.display = not narrow

    def on_key(self, event: events.Key) -> None:
        """Feed keys to the Vim-style sequence machine (gg, gt, gT, Ngt)."""
        if isinstance(self.focused, Input):
            self._keys.reset()
            return
        if self._keys.handle(event.key):
            event.prevent_default()
            event.stop()

    async def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Open a file chosen in the FILES tree."""
        event.stop()
        await self.open_path(event.path)

    async def on_files_tree_open_in_new_tab(
        self, event: FilesTree.OpenInNewTab
    ) -> None:
        """Open a tree file in a new tab (the ``o`` key)."""
        event.stop()
        await self.open_in_new_tab(event.path)

    def on_tree_node_selected(self, event: Tree.NodeSelected[Heading]) -> None:
        """Jump to the heading chosen in the TOC tree."""
        if not isinstance(event.control, TocTree):
            return
        event.stop()
        heading = event.node.data
        if heading is None:
            return
        self._navigator.jump_to_anchor(heading.slug, line=heading.line)
        self.query_one(ViewerPane).focus()

    async def on_viewer_pane_confirm_large(
        self, event: ViewerPane.ConfirmLarge
    ) -> None:
        """Load a too-large file after the user confirmed with Enter."""
        event.stop()
        await self.open_path(event.path, allow_large=True)

    async def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        """Route Markdown links through mokuji's link resolution."""
        event.prevent_default()
        event.stop()
        await self.follow_link(event.href)

    async def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Switch tab state when the tab bar activates another tab."""
        index = self._navigator.index_of_tab_id(event.tab.id)
        if index is not None and index != self._navigator.active_index:
            await self._navigator.switch_to(index)

    def action_toggle_files(self) -> None:
        """Toggle the left pane in FILES mode (req 2.1)."""
        self._toggle_pane(SidebarMode.FILES)

    def action_toggle_toc(self) -> None:
        """Toggle the left pane in TOC mode (req 2.1)."""
        self._toggle_pane(SidebarMode.TOC)

    def action_focus_content(self) -> None:
        """Return focus to the content pane."""
        self.query_one(ViewerPane).focus()

    async def action_close_tab(self) -> None:
        """Close the current tab (the ``x`` key)."""
        await self._navigator.close_tab()

    async def action_history_back(self) -> None:
        """Go back in the active tab's jump history (ctrl+o)."""
        await self._navigator.history_step(-1)

    async def action_history_forward(self) -> None:
        """Go forward in the active tab's jump history (ctrl+i)."""
        await self._navigator.history_step(1)

    async def open_path(
        self, path: Path, *, allow_large: bool = False, anchor: str | None = None
    ) -> None:
        """Open *path* in the current tab, focusing an existing tab if open."""
        await self._navigator.open_path(path, allow_large=allow_large, anchor=anchor)

    async def open_in_new_tab(self, path: Path) -> None:
        """Open *path* in a new tab, focusing an existing tab if open."""
        await self._navigator.open_in_new_tab(path)

    async def follow_link(self, href: str) -> None:
        """Follow a Markdown link per req 2.8."""
        document = self._navigator.active_document
        if document is None:
            return
        target = resolve_link(document.path, href)
        if isinstance(target, ExternalLink):
            self._open_external(target.url)
            return
        if isinstance(target, InternalLink):
            if not target.path.exists():
                self.flash(f"not found: {href}")
                return
            await self.open_path(target.path, anchor=target.anchor)
            return
        self.flash(f"unsupported link: {href}")

    def flash(self, message: str) -> None:
        """Show a transient footer message (the single feedback channel)."""
        self.query_one(KeyGuide).flash(message)

    def _open_external(self, url: str) -> None:
        try:
            opened = webbrowser.open(url)
        except OSError:
            opened = False
        if opened:
            self.flash("opened in browser")
        else:
            self.flash(f"could not open browser: {url}")

    def _toggle_pane(self, mode: SidebarMode) -> None:
        sidebar = self.query_one(Sidebar)
        if sidebar.display and sidebar.mode is mode:
            sidebar.display = False
            sidebar.remove_class("-overlay")
            self.query_one(ViewerPane).focus()
            return
        if mode is SidebarMode.TOC:
            sidebar.set_document(self.query_one(ViewerPane).document)
        sidebar.show_mode(mode)
        sidebar.set_class(self._narrow, "-overlay")
        sidebar.display = True
        sidebar.active_tree.focus()
