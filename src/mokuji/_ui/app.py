"""Application shell for mokuji: layout, bindings, and event wiring."""

from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING, ClassVar

from textual.app import App
from textual.binding import Binding, BindingType
from textual.containers import Horizontal
from textual.widgets import DirectoryTree, Input, Markdown, Static, Tabs, Tree

from .._document import ExternalLink, InternalLink, resolve_link
from .._state import is_first_run, mark_tour_seen
from .._theme import SUMI_THEME
from .footer import TREE_HINTS, KeyGuide
from .help import HelpScreen
from .keys import KeySequenceMachine
from .navigator import TabNavigator
from .search import SearchController, SearchInput
from .sidebar import FilesTree, Sidebar, SidebarMode, TocTree
from .style import APP_CSS
from .tour import TourScreen, tutorial_path
from .tree_filter import TreeFilterController
from .viewer import ViewerPane

if TYPE_CHECKING:
    from pathlib import Path

    from textual import events
    from textual.app import ComposeResult

    from .._document import Heading

NARROW_WIDTH = 80
TINY_WIDTH = 40
TINY_HEIGHT = 10


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
        Binding("question_mark", "help", "help"),
        Binding("ctrl+g", "toggle_guide", "toggle key guide", show=False),
    ]

    def __init__(self, root: Path, initial_file: Path | None = None) -> None:
        """Create the app rooted at *root*, optionally opening *initial_file*."""
        super().__init__()
        self._root = root.resolve()
        self._initial_file = initial_file.resolve() if initial_file else None
        self._navigator = TabNavigator(self)
        self._search = SearchController(self)
        self._tree_filter = TreeFilterController(self)
        self._keys = KeySequenceMachine(
            scroll_top=self._gg_scroll_top,
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
        # Keep Tab strictly a tree <-> content toggle; the bar itself is
        # driven by gt/gT and mouse clicks, so it never needs focus.
        tabs.can_focus = False
        yield tabs
        with Horizontal(id="main"):
            yield Sidebar(self._root, id="sidebar")
            yield ViewerPane(id="viewer")
        yield KeyGuide(id="footer")
        search_input = SearchInput(id="search-input", placeholder="search")
        search_input.display = False
        yield search_input
        too_small = Static("terminal too small", id="too-small")
        too_small.display = False
        yield too_small

    async def on_mount(self) -> None:
        """Activate the sumi theme, open the initial file, and set focus.

        With a file open the viewer gets focus (start reading); without one
        the FILES tree does, so a file can be picked without pressing Tab.
        """
        self.register_theme(SUMI_THEME)
        self.theme = "sumi"
        if self._initial_file is not None:
            self.query_one(ViewerPane).focus()
            await self.open_path(self._initial_file)
        else:
            await self.query_one(ViewerPane).show_empty()
            self.query_one(FilesTree).focus()
        if is_first_run():
            mark_tour_seen()
            self.push_screen(TourScreen(), self._on_tour_closed)

    def on_resize(self, event: events.Resize) -> None:
        """Auto-collapse the sidebar on narrow terminals (req 2.1)."""
        too_small = event.size.width < TINY_WIDTH or event.size.height < TINY_HEIGHT
        self.query_one("#too-small", Static).display = too_small
        narrow = event.size.width < NARROW_WIDTH
        if narrow == self._narrow:
            return
        self._narrow = narrow
        sidebar = self.query_one(Sidebar)
        sidebar.remove_class("-overlay")
        if narrow and sidebar.has_focus_within:
            self.query_one(ViewerPane).focus()
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
        """Open a file chosen in the FILES tree and move focus to it.

        Every file opens in its own tab (the tab is focused instead when
        the file is already open), so browsing never replaces a document
        the user was reading. Focus only moves when the file actually
        became the active document, so a failed open (e.g. permission
        denied) leaves the tree focused.
        """
        event.stop()
        await self.open_in_new_tab(event.path)
        document = self._navigator.active_document
        if document is not None and document.path == event.path.resolve():
            self.query_one(ViewerPane).focus()

    def on_files_tree_filter_toggled(self, event: FilesTree.FilterToggled) -> None:
        """Flash the new tree filter state (the ``.`` key)."""
        event.stop()
        self.flash("showing all files" if event.show_all else "markdown files only")

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

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Confirm the search query or type-to-filter typed into the footer."""
        if event.input.id != "search-input":
            return
        event.stop()
        if self._tree_filter.is_active:
            await self._tree_filter.submit(event.value)
        else:
            self._search.submit(event.value)

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Live-narrow the tree while the type-to-filter input is open (req U1b)."""
        if event.input.id != "search-input" or not self._tree_filter.is_active:
            return
        event.stop()
        await self._tree_filter.on_query_changed(event.value)

    def action_open_search(self) -> None:
        """Open the search input over the footer (the ``/`` key)."""
        self._search.open_input()

    def action_open_tree_filter(self) -> None:
        """Open the search input for tree type-to-filter (``/`` in a tree)."""
        self._tree_filter.open_input()

    async def action_cancel_search(self) -> None:
        """Cancel the search input or tree filter (escape while typing)."""
        if self._tree_filter.is_active:
            await self._tree_filter.cancel()
        else:
            self._search.cancel_input()

    def action_search_next(self) -> None:
        """Jump to the next match (the ``n`` key)."""
        self._search.next()

    def action_search_prev(self) -> None:
        """Jump to the previous match (the ``N`` key)."""
        self._search.prev()

    def action_dismiss_search(self) -> None:
        """Clear search highlights and state (escape in the content pane)."""
        self.dismiss_search()

    def dismiss_search(self) -> None:
        """Drop any active search; called on every navigation."""
        self._search.dismiss()

    def search_snapshot(self) -> tuple[str, int] | None:
        """Return the active search's ``(query, index)``, if any (req U2)."""
        return self._search.snapshot()

    def restore_search(self, query: str, index: int) -> None:
        """Re-run a stashed search against the newly rendered document (req U2)."""
        self._search.restore(query, index)

    def on_descendant_focus(self, event: events.DescendantFocus) -> None:
        """Keep the footer hints matched to the focused region (req 2.7)."""
        footer = self.query_one(KeyGuide)
        if isinstance(event.widget, FilesTree | TocTree):
            footer.set_default(TREE_HINTS)
        elif isinstance(event.widget, ViewerPane):
            footer.set_default(self._search.status_text)

    def action_help(self) -> None:
        """Open the full keybinding reference (the ``?`` key)."""
        guide_hidden = not self.query_one(KeyGuide).display
        self.push_screen(HelpScreen(guide_hidden=guide_hidden), self._on_help_closed)

    def _on_help_closed(self, open_tour: bool | None) -> None:
        """Open the welcome tour when help was dismissed with ``w``."""
        if open_tour:
            self.push_screen(TourScreen(), self._on_tour_closed)

    def _on_tour_closed(self, open_tutorial: bool | None) -> None:
        """Open the bundled tutorial when the tour finished with Enter."""
        if open_tutorial:
            self.call_next(self._open_tutorial)

    async def _open_tutorial(self) -> None:
        # A new tab keeps whatever document the user already had open.
        await self.open_in_new_tab(tutorial_path())
        self.query_one(ViewerPane).focus()

    def action_toggle_guide(self) -> None:
        """Show or hide the footer key guide (ctrl+g, session-scoped)."""
        footer = self.query_one(KeyGuide)
        footer.display = not footer.display

    async def action_reload(self) -> None:
        """Re-read the current file from disk (the ``r`` key)."""
        await self._navigator.reload()

    def action_toggle_files(self) -> None:
        """Toggle the left pane in FILES mode (req 2.1)."""
        self._toggle_pane(SidebarMode.FILES)

    def action_toggle_toc(self) -> None:
        """Toggle the left pane in TOC mode (req 2.1)."""
        self._toggle_pane(SidebarMode.TOC)

    def action_focus_content(self) -> None:
        """Return focus to the content pane; dismiss a narrow overlay too."""
        if self._narrow:
            sidebar = self.query_one(Sidebar)
            sidebar.display = False
            sidebar.remove_class("-overlay")
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

    async def open_link(self, path: Path, *, anchor: str | None = None) -> None:
        """Navigate to *path* in the current tab (never hijacks another tab)."""
        await self._navigator.open_link(path, anchor=anchor)

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
            if not target.path.is_relative_to(self._root):
                self.flash(f"link outside project: {href}")
                return
            if not target.path.exists():
                self.flash(f"not found: {href}")
                return
            await self.open_link(target.path, anchor=target.anchor)
            return
        self.flash(f"unsupported link: {href}")

    def flash(self, message: str) -> None:
        """Show a transient footer message (the single feedback channel)."""
        self.query_one(KeyGuide).flash(message)

    def _gg_scroll_top(self) -> None:
        """Route ``gg`` to whichever pane is focused (req B5).

        A focused FILES/TOC tree gets its cursor moved to the first
        node; otherwise the viewer scrolls to the top, as before.
        """
        focused = self.focused
        if isinstance(focused, FilesTree | TocTree):
            focused.action_scroll_home()
            return
        self.query_one(ViewerPane).scroll_top()

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
        """Focus-or-toggle the left pane in *mode* (req U6).

        Hidden -> show and focus the tree. Visible in *mode* but not
        focused -> just focus the tree (the pane is already visible;
        don't hide something the user hasn't looked at yet). Visible in
        *mode* and focused -> hide it. Visible in a different mode ->
        switch to *mode* and focus, as before.
        """
        sidebar = self.query_one(Sidebar)
        if sidebar.display and sidebar.mode is mode:
            if self.focused is sidebar.active_tree:
                sidebar.display = False
                sidebar.remove_class("-overlay")
                self.query_one(ViewerPane).focus()
            else:
                sidebar.active_tree.focus()
            return
        if mode is SidebarMode.TOC:
            sidebar.set_document(self.query_one(ViewerPane).document)
        sidebar.show_mode(mode)
        sidebar.set_class(self._narrow, "-overlay")
        sidebar.display = True
        sidebar.active_tree.focus()
