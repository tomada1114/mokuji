"""The content pane: renders one document as Markdown or plain text."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.binding import Binding, BindingType
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widgets import Markdown, Static

from .._files import FileKind

if TYPE_CHECKING:
    from pathlib import Path

    from textual.widget import Widget

    from .._document import Document

BINARY_NOTICE = "binary file — cannot display"
EMPTY_NOTICE = "(empty file)"
EMPTY_STATE_TEXT = "mokuji\n読 · read your docs\n\ne browse files   ·   ? help"


def too_large_notice(size: int) -> str:
    """Return the confirmation notice for a file over the size limit."""
    megabytes = size / (1024 * 1024)
    return f"large file ({megabytes:.1f} MB) — press Enter to load"


class ViewerPane(VerticalScroll):
    """Scrollable reading column showing the active tab's document."""

    class ConfirmLarge(Message):
        """The user confirmed loading a file over the size limit."""

        def __init__(self, path: Path) -> None:
            self.path = path
            super().__init__()

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "confirm_large", "confirm load", show=False),
        Binding("j", "scroll_down", "scroll down", show=False),
        Binding("k", "scroll_up", "scroll up", show=False),
        Binding("d", "half_page_down", "half page down", show=False),
        Binding("u", "half_page_up", "half page up", show=False),
        Binding("f", "page_down", "page down", show=False),
        Binding("space", "page_down", "page down", show=False),
        Binding("b", "page_up", "page up", show=False),
        Binding("G", "scroll_bottom", "bottom", show=False),
    ]

    def __init__(self, *, id: str | None = None) -> None:  # noqa: A002 — Textual's own widget id parameter name
        super().__init__(id=id)
        self.document: Document | None = None

    async def show_empty(self) -> None:
        """Clear the pane and show the no-file-open state (req 3.3)."""
        self.document = None
        await self.remove_children()
        await self.mount(Static(EMPTY_STATE_TEXT, classes="content notice empty-state"))

    async def show_document(self, document: Document) -> None:
        """Replace the pane's content with a rendering of *document*."""
        self.document = document
        await self.remove_children()
        await self.mount(self._build_content(document))
        self.scroll_home(animate=False)

    def scroll_top(self) -> None:
        """Jump to the top of the document (the ``gg`` motion)."""
        self.scroll_home(animate=False)

    def action_half_page_down(self) -> None:
        """Scroll half a viewport towards the end."""
        self.scroll_relative(y=self.container_size.height // 2, animate=False)

    def action_half_page_up(self) -> None:
        """Scroll half a viewport towards the top."""
        self.scroll_relative(y=-(self.container_size.height // 2), animate=False)

    def action_confirm_large(self) -> None:
        """Ask the app to load the pending too-large document."""
        document = self.document
        if document is not None and document.kind is FileKind.TOO_LARGE:
            self.post_message(self.ConfirmLarge(document.path))

    def action_scroll_bottom(self) -> None:
        """Jump to the end of the document (the ``G`` motion)."""
        self.scroll_end(animate=False)

    def _build_content(self, document: Document) -> Widget:
        if document.kind is FileKind.BINARY:
            return Static(BINARY_NOTICE, classes="content notice")
        if document.kind is FileKind.TOO_LARGE:
            size = document.path.stat().st_size
            return Static(too_large_notice(size), classes="content notice")
        if not document.text:
            return Static(EMPTY_NOTICE, classes="content notice")
        if document.kind is FileKind.MARKDOWN:
            return Markdown(document.text, classes="content", open_links=False)
        return Static(Text(document.text), classes="content plain-text")
