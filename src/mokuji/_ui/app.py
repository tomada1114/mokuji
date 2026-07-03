"""Application shell for mokuji."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.app import App
from textual.binding import Binding, BindingType
from textual.containers import Horizontal
from textual.widgets import DirectoryTree, Input, Markdown, Tree

from .._document import load_document
from .._errors import DocumentLoadError
from .._theme import ACCENT, BG_CHROME, BG_PANEL, ERROR, SUMI_THEME, TEXT_MUTED
from .footer import KeyGuide
from .sidebar import Sidebar, SidebarMode, TocTree
from .viewer import ViewerPane

if TYPE_CHECKING:
    from pathlib import Path

    from textual import events
    from textual.app import ComposeResult

    from .._document import Heading


_COUNT_DIGITS = frozenset("123456789")

NARROW_WIDTH = 80


class MokujiApp(App[None]):
    """The mokuji TUI application."""

    CSS = f"""
    Screen {{
        background: $background;
        layers: base overlay;
    }}
    #main {{
        height: 1fr;
    }}
    Sidebar {{
        width: 28;
        min-width: 20;
        background: {BG_PANEL};
        border-left: wide {BG_PANEL};
    }}
    Sidebar:focus-within {{
        border-left: wide {ACCENT};
    }}
    Sidebar.-overlay {{
        layer: overlay;
        dock: left;
        height: 100%;
    }}
    #sidebar-title {{
        height: 1;
        padding: 0 1;
        color: {TEXT_MUTED};
        text-style: bold;
        background: {BG_PANEL};
    }}
    FilesTree, TocTree {{
        background: {BG_PANEL};
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
    KeyGuide.-error {{
        color: {ERROR};
    }}
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "quit"),
        Binding("e", "toggle_files", "files"),
        Binding("t", "toggle_toc", "toc"),
    ]

    def __init__(self, root: Path, initial_file: Path | None = None) -> None:
        """Create the app rooted at *root*, optionally opening *initial_file*."""
        super().__init__()
        self._root = root.resolve()
        self._initial_file = initial_file.resolve() if initial_file else None
        self._pending_count = ""
        self._pending_g = False
        self._narrow = False

    def compose(self) -> ComposeResult:
        """Lay out the sidebar, viewer, and footer key guide."""
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
            await self._open_path(self._initial_file)

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

    async def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Open a file chosen in the FILES tree."""
        event.stop()
        await self._open_path(event.path)

    def on_tree_node_selected(self, event: Tree.NodeSelected[Heading]) -> None:
        """Jump to the heading chosen in the TOC tree."""
        if not isinstance(event.control, TocTree):
            return
        event.stop()
        heading = event.node.data
        if heading is None:
            return
        viewer = self.query_one(ViewerPane)
        self._jump_to_heading(viewer, heading.slug, heading.line)
        viewer.focus()

    async def on_viewer_pane_confirm_large(
        self, event: ViewerPane.ConfirmLarge
    ) -> None:
        """Load a too-large file after the user confirmed with Enter."""
        event.stop()
        await self._open_path(event.path, allow_large=True)

    def action_toggle_files(self) -> None:
        """Toggle the left pane in FILES mode (req 2.1)."""
        self._toggle_pane(SidebarMode.FILES)

    def action_toggle_toc(self) -> None:
        """Toggle the left pane in TOC mode (req 2.1)."""
        self._toggle_pane(SidebarMode.TOC)

    def action_focus_content(self) -> None:
        """Return focus to the content pane."""
        self.query_one(ViewerPane).focus()

    async def _open_path(self, path: Path, *, allow_large: bool = False) -> None:
        try:
            document = load_document(path, allow_large=allow_large)
        except DocumentLoadError as error:
            self._flash_load_error(path, error)
            return
        await self.query_one(ViewerPane).show_document(document)
        self.query_one(Sidebar).set_document(document)

    def _flash_load_error(self, path: Path, error: DocumentLoadError) -> None:
        if isinstance(error.__cause__, PermissionError):
            self.query_one(KeyGuide).flash(f"permission denied: {path.name}")
        else:
            self.query_one(KeyGuide).flash(str(error))

    def _jump_to_heading(self, viewer: ViewerPane, slug: str, line: int) -> None:
        """Scroll the viewer to a heading, preferring anchor navigation."""
        document = viewer.document
        markdown = viewer.query(Markdown)
        if markdown and markdown.first().goto_anchor(slug):
            return
        if document is None or not document.text:
            return
        total_lines = max(1, document.text.count("\n"))
        target = round(line / total_lines * viewer.max_scroll_y)
        viewer.scroll_to(y=target, animate=False)

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

    def _clear_key_sequence(self) -> None:
        self._pending_count = ""
        self._pending_g = False

    def _tab_next(self, count: int | None) -> None:
        """Switch to the next (or *count*-th) tab; single-document for now."""

    def _tab_prev(self) -> None:
        """Switch to the previous tab; single-document for now."""
