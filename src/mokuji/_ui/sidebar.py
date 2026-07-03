"""The left pane: FILES directory tree and TOC heading tree."""

from __future__ import annotations

import enum
import os
from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import DirectoryTree, Static, Tree

from .._document import Heading
from .._files import FileKind, is_markdown

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from rich.style import Style
    from textual.app import ComposeResult
    from textual.widgets._directory_tree import DirEntry
    from textual.widgets._tree import TreeNode

    from .._document import Document

NO_HEADINGS = "(no headings)"
NOT_MARKDOWN = "(not a Markdown file)"
NO_MARKDOWN_FILES = "(no markdown files)"
EMPTY_DIRECTORY = "(empty)"

_VIM_TREE_BINDINGS: list[BindingType] = [
    Binding("j", "cursor_down", "down", show=False),
    Binding("k", "cursor_up", "up", show=False),
    Binding("escape", "app.focus_content", "back to content", show=False),
]


class SidebarMode(enum.Enum):
    """Which tree the left pane is currently showing."""

    FILES = "files"
    TOC = "toc"


class FilesTree(DirectoryTree):
    """Directory tree that hides non-Markdown files behind a toggle."""

    class OpenInNewTab(Message):
        """The user asked to open the cursor file in a new tab."""

        def __init__(self, path: Path) -> None:
            self.path = path
            super().__init__()

    class FilterToggled(Message):
        """The Markdown-only filter was switched on or off."""

        def __init__(self, show_all: bool) -> None:
            self.show_all = show_all
            super().__init__()

    BINDINGS: ClassVar[list[BindingType]] = [
        *_VIM_TREE_BINDINGS,
        Binding("h", "collapse_current", "collapse", show=False),
        Binding("l", "expand_current", "expand", show=False),
        Binding("o", "open_new_tab", "open in new tab", show=False),
        Binding("full_stop", "toggle_filter", "toggle all files", show=False),
    ]

    def __init__(self, path: Path, *, id: str | None = None) -> None:  # noqa: A002 — Textual's own widget id parameter name
        super().__init__(path, id=id)
        self.show_all = False

    def on_focus(self) -> None:
        """Land the cursor on the first line so focus is visible immediately.

        A fresh Tree has no cursor (``cursor_line == -1``) until a key or
        click moves it, which makes tabbing into the pane look like a no-op.
        """
        if self.cursor_line == -1:
            self.cursor_line = 0

    def action_open_new_tab(self) -> None:
        """Post a request to open the cursor file in a new tab."""
        node = self.cursor_node
        if node is not None and node.data is not None and node.data.path.is_file():
            self.post_message(self.OpenInNewTab(node.data.path))

    async def action_toggle_filter(self) -> None:
        """Toggle between Markdown-only and all-files views (the ``.`` key)."""
        self.show_all = not self.show_all
        self.post_message(self.FilterToggled(self.show_all))
        await self.reload()

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """Hide ``.git``; hide non-Markdown files unless showing all."""
        visible = [path for path in paths if path.name != ".git"]
        if self.show_all:
            return visible
        return [path for path in visible if path.is_dir() or is_markdown(path)]

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

    def on_focus(self) -> None:
        """Land the cursor on the first line so focus is visible immediately.

        Same rationale as :meth:`FilesTree.on_focus`.
        """
        if self.cursor_line == -1:
            self.cursor_line = 0

    def set_document(self, document: Document | None) -> None:
        """Rebuild the heading list for *document* (or a placeholder)."""
        self.clear()
        if document is None or document.kind is not FileKind.MARKDOWN:
            self.root.add_leaf(NOT_MARKDOWN)
            return
        if not document.headings:
            self.root.add_leaf(NO_HEADINGS)
            return
        for heading in document.headings:
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
