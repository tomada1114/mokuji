"""The left pane: FILES directory tree and TOC heading tree."""

from __future__ import annotations

import enum
import os
from typing import TYPE_CHECKING, ClassVar

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
    from rich.text import Text
    from textual.app import ComposeResult
    from textual.widgets._directory_tree import DirEntry
    from textual.widgets._tree import TreeNode

    from .._document import Document

NO_HEADINGS = "(no headings)"
NOT_MARKDOWN = "(not a Markdown file)"

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
    """Directory tree that hides ``.git`` and dims non-Markdown entries."""

    class OpenInNewTab(Message):
        """The user asked to open the cursor file in a new tab."""

        def __init__(self, path: Path) -> None:
            self.path = path
            super().__init__()

    BINDINGS: ClassVar[list[BindingType]] = [
        *_VIM_TREE_BINDINGS,
        Binding("h", "collapse_current", "collapse", show=False),
        Binding("l", "expand_current", "expand", show=False),
        Binding("o", "open_new_tab", "open in new tab", show=False),
    ]

    def action_open_new_tab(self) -> None:
        """Post a request to open the cursor file in a new tab."""
        node = self.cursor_node
        if node is not None and node.data is not None and node.data.path.is_file():
            self.post_message(self.OpenInNewTab(node.data.path))

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """Hide ``.git`` directories; everything else stays visible."""
        return [path for path in paths if path.name != ".git"]

    def render_label(
        self, node: TreeNode[DirEntry], base_style: Style, style: Style
    ) -> Text:
        """Dim non-Markdown files and unreadable entries."""
        label = super().render_label(node, base_style, style)
        entry = node.data
        if entry is None:
            return label
        path = entry.path
        is_dimmed_file = path.is_file() and not is_markdown(path)
        is_unreadable = not os.access(path, os.R_OK)
        if is_dimmed_file or is_unreadable:
            label.stylize("dim")
        return label

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
