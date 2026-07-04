"""The left pane: FILES directory tree and TOC heading tree."""

from __future__ import annotations

import enum
import os
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import DirectoryTree, Static, Tree

from .._document import Heading
from .._files import (
    FileKind,
    is_hidden_by_default,
    is_markdown,
    matching_descendant_paths,
)
from .._search import smart_case_contains

if TYPE_CHECKING:
    from collections.abc import Iterable

    from rich.style import Style
    from textual.app import ComposeResult
    from textual.widgets._directory_tree import DirEntry
    from textual.widgets._tree import TreeNode

    from .._document import Document

NO_HEADINGS = "(no headings)"
NO_FILE_OPEN = "(no file open)"
NOT_MARKDOWN = "(not a Markdown file)"
NO_MARKDOWN_FILES = "(no markdown files)"
NO_FILTER_MATCHES = "(no matches)"
EMPTY_DIRECTORY = "(empty)"

_VIM_TREE_BINDINGS: list[BindingType] = [
    Binding("j", "cursor_down", "down", show=False),
    Binding("k", "cursor_up", "up", show=False),
    Binding("G", "scroll_end", "bottom", show=False),
    Binding("slash", "app.open_tree_filter", "filter", show=False),
    Binding("escape", "app.focus_content", "back to content", show=False),
]


class SidebarMode(enum.Enum):
    """Which tree the left pane is currently showing."""

    FILES = "files"
    TOC = "toc"


class FilesTree(DirectoryTree):
    """Directory tree that hides non-Markdown files behind a toggle."""

    class FilterToggled(Message):
        """The Markdown-only filter was switched on or off."""

        def __init__(self, show_all: bool) -> None:
            self.show_all = show_all
            super().__init__()

    BINDINGS: ClassVar[list[BindingType]] = [
        *_VIM_TREE_BINDINGS,
        Binding("h", "collapse_current", "collapse", show=False),
        Binding("l", "expand_current", "expand", show=False),
        Binding("full_stop", "toggle_filter", "toggle all files", show=False),
    ]

    def __init__(self, path: Path, *, id: str | None = None) -> None:  # noqa: A002 — Textual's own widget id parameter name
        super().__init__(path, id=id)
        self.show_all = False
        self._filter_keep: set[Path] | None = None

    def on_focus(self) -> None:
        """Land the cursor on the first line so focus is visible immediately.

        A fresh Tree has no cursor (``cursor_line == -1``) until a key or
        click moves it, which makes tabbing into the pane look like a no-op.
        """
        if self.cursor_line == -1:
            self.cursor_line = 0

    async def action_toggle_filter(self) -> None:
        """Toggle between Markdown-only and all-files views (the ``.`` key)."""
        self.show_all = not self.show_all
        self.post_message(self.FilterToggled(self.show_all))
        await self.reload()

    async def apply_type_filter(self, query: str) -> None:
        """Narrow the tree to *query* matches and their ancestor dirs (req U1b)."""
        self._filter_keep = (
            matching_descendant_paths(Path(self.path), query, show_all=self.show_all)
            if query
            else None
        )
        await self.reload()
        if self._filter_keep is not None:
            await self._reveal_filter_matches(self.root)

    async def clear_type_filter(self) -> None:
        """Restore the full tree after Esc cancels the type-to-filter."""
        self._filter_keep = None
        await self.reload()

    async def _reveal_filter_matches(self, node: TreeNode[DirEntry]) -> None:
        """Expand ancestor directories so nested matches become visible.

        ``reload()`` alone only re-populates already-expanded directories;
        this walks down from *node*, expanding (and thereby loading) each
        child that the filter kept, so a match several levels deep is
        reachable without the user manually expanding every ancestor.
        """
        if self._filter_keep is None:
            return
        for child in list(node.children):
            if child.data is None or child.data.path not in self._filter_keep:
                continue
            if child.allow_expand and not child.is_expanded:
                await self.reload_node(child)
            if child.children:
                await self._reveal_filter_matches(child)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """Hide ``.git``; hide dotfiles/build-noise/non-Markdown unless showing all.

        When a type-to-filter query is active (``/``), also hide anything
        outside the precomputed match/ancestor set (req U1b).
        """
        visible = [path for path in paths if path.name != ".git"]
        if not self.show_all:
            visible = [path for path in visible if not is_hidden_by_default(path)]
        if self._filter_keep is not None:
            visible = [path for path in visible if path in self._filter_keep]
        return visible

    def render_label(
        self, node: TreeNode[DirEntry], base_style: Style, style: Style
    ) -> Text:
        """Dim non-Markdown files, unreadable entries, and placeholders."""
        entry = node.data
        if entry is None:
            label = Text(str(node.label), style=style)
            label.stylize("dim")
            return label
        label = super().render_label(node, base_style, style)
        path = entry.path
        is_dimmed_file = path.is_file() and not is_markdown(path)
        is_unreadable = not os.access(path, os.R_OK)
        if is_dimmed_file or is_unreadable:
            label.stylize("dim")
        return label

    async def _on_tree_node_expanded(self, event: Tree.NodeExpanded[DirEntry]) -> None:
        """Add a placeholder leaf when an expanded directory shows nothing.

        The stock loader never populates a directory whose (filtered)
        content is empty, so without this the only feedback for expanding
        such a directory is the folder icon changing.
        """
        await super()._on_tree_node_expanded(event)
        node = event.node
        if node.children or node.data is None:
            return
        label = self._placeholder_label(node.data.path)
        if label is not None:
            node.add_leaf(label, data=None)

    def _placeholder_label(self, path: Path) -> str | None:
        if not path.is_dir():
            return None
        try:
            entries = list(path.iterdir())
        except OSError:
            return None
        if not entries:
            return EMPTY_DIRECTORY
        if any(self.filter_paths(entries)):
            return None
        return NO_MARKDOWN_FILES

    def action_collapse_current(self) -> None:
        """Collapse the cursor directory, or step to its parent."""
        node = self.cursor_node
        if node is None:
            return
        if node.allow_expand and node.is_expanded:
            node.collapse()
        elif node.parent is not None:
            self.cursor_line = node.parent.line

    def action_expand_current(self) -> None:
        """Expand the cursor directory."""
        node = self.cursor_node
        if node is not None and node.allow_expand and not node.is_expanded:
            node.expand()


class TocTree(Tree[Heading]):
    """Heading tree for the active document."""

    BINDINGS: ClassVar[list[BindingType]] = _VIM_TREE_BINDINGS

    def __init__(self) -> None:
        super().__init__("TOC", id="toc-tree")
        self.show_root = False
        self.guide_depth = 2
        self._document: Document | None = None
        self._filter_query: str | None = None

    def on_focus(self) -> None:
        """Land the cursor on the first line so focus is visible immediately.

        Same rationale as :meth:`FilesTree.on_focus`.
        """
        if self.cursor_line == -1:
            self.cursor_line = 0

    def set_document(self, document: Document | None) -> None:
        """Rebuild the heading list for *document* (or a placeholder)."""
        self._document = document
        self._filter_query = None
        self._rebuild()

    def apply_type_filter(self, query: str) -> None:
        """Narrow the heading list to *query* matches (req U1b, flat list)."""
        self._filter_query = query or None
        self._rebuild()

    def clear_type_filter(self) -> None:
        """Restore the full heading list after Esc cancels the type-to-filter."""
        self._filter_query = None
        self._rebuild()

    def _rebuild(self) -> None:
        self.clear()
        document = self._document
        if document is None:
            self.root.add_leaf(NO_FILE_OPEN)
            return
        if document.kind is not FileKind.MARKDOWN:
            self.root.add_leaf(NOT_MARKDOWN)
            return
        if not document.headings:
            self.root.add_leaf(NO_HEADINGS)
            return
        headings = document.headings
        if self._filter_query is not None:
            headings = tuple(
                h for h in headings if smart_case_contains(h.text, self._filter_query)
            )
            if not headings:
                self.root.add_leaf(NO_FILTER_MATCHES)
                return
        for heading in headings:
            indent = "  " * (heading.level - 1)
            self.root.add_leaf(f"{indent}{heading.text}", data=heading)


class Sidebar(Vertical):
    """Container that swaps between the FILES tree and the TOC tree."""

    def __init__(self, root: Path, *, id: str | None = None) -> None:  # noqa: A002 — Textual's own widget id parameter name
        super().__init__(id=id)
        self._root = root
        self.mode = SidebarMode.FILES

    def compose(self) -> ComposeResult:
        """Lay out the pane header and both trees."""
        yield Static("FILES", id="sidebar-title")
        yield FilesTree(self._root, id="files-tree")
        yield TocTree()

    def on_mount(self) -> None:
        """Start in FILES mode."""
        self.show_mode(SidebarMode.FILES)

    def show_mode(self, mode: SidebarMode) -> None:
        """Switch the visible tree to *mode*."""
        self.mode = mode
        is_files = mode is SidebarMode.FILES
        self.query_one("#sidebar-title", Static).update("FILES" if is_files else "TOC")
        self.query_one(FilesTree).display = is_files
        self.query_one(TocTree).display = not is_files

    @property
    def active_tree(self) -> FilesTree | TocTree:
        """The tree matching the current mode."""
        if self.mode is SidebarMode.FILES:
            return self.query_one(FilesTree)
        return self.query_one(TocTree)

    def set_document(self, document: Document | None) -> None:
        """Refresh the TOC for the newly active document."""
        self.query_one(TocTree).set_document(document)
