"""The content pane: renders one document as Markdown or plain text."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.binding import Binding, BindingType
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widgets import Markdown, Static

from .._files import FileKind
from .._theme import ACCENT_ORANGE, BG, WARNING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from textual.widget import Widget

    from .._document import Document
    from .._search import Match

BINARY_NOTICE = "binary file — cannot display"
LARGE_FILE_UNAVAILABLE_NOTICE = "large file — no longer available"
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
        Binding("slash", "app.open_search", "search", show=False),
        Binding("n", "app.search_next", "next match", show=False),
        Binding("N", "app.search_prev", "previous match", show=False),
        Binding("escape", "app.dismiss_search", "clear search", show=False),
        Binding("r", "app.reload", "reload", show=False),
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

    def scroll_to_line(self, line: int) -> None:
        """Scroll so *line* (0-based source line) is roughly in view."""
        document = self.document
        if document is None or not document.text:
            return
        total_lines = max(1, document.text.count("\n"))
        target = round(line / total_lines * self.max_scroll_y)
        self.scroll_to(y=target, animate=False)

    def show_matches(self, matches: Sequence[Match], current_index: int) -> None:
        """Highlight search matches inline (plain-text documents only)."""
        static = self._plain_text_static()
        if static is None or self.document is None:
            return
        text = Text(self.document.text)
        for index, match in enumerate(matches):
            color = ACCENT_ORANGE if index == current_index else WARNING
            text.stylize(f"{BG} on {color}", match.start, match.end)
        static.update(text)

    def clear_matches(self) -> None:
        """Remove inline search highlights (plain-text documents only)."""
        static = self._plain_text_static()
        if static is not None and self.document is not None:
            static.update(Text(self.document.text))

    def _plain_text_static(self) -> Static | None:
        results = self.query(".plain-text")
        if results:
            return results.first(Static)
        return None

    def _build_content(self, document: Document) -> Widget:
        if document.kind is FileKind.BINARY:
            return Static(BINARY_NOTICE, classes="content notice")
        if document.kind is FileKind.TOO_LARGE:
            try:
                size = document.path.stat().st_size
            except OSError:
                return Static(LARGE_FILE_UNAVAILABLE_NOTICE, classes="content notice")
            return Static(too_large_notice(size), classes="content notice")
        if not document.text:
            return Static(EMPTY_NOTICE, classes="content notice")
        if document.kind is FileKind.MARKDOWN:
            return Markdown(document.text, classes="content", open_links=False)
        return Static(Text(document.text), classes="content plain-text")
