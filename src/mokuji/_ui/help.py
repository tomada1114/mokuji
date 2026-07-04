"""The full keybinding reference modal (the ``?`` key)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

from .._theme import ACCENT, TEXT_FAINT, TEXT_MUTED

if TYPE_CHECKING:
    from textual.app import ComposeResult

KeyRow = tuple[str, str]
Section = tuple[str, tuple[KeyRow, ...]]

READING: Section = (
    "reading",
    (
        ("j / k", "scroll one line"),
        ("d / u", "half page down / up"),
        ("f / b", "full page down / up"),
        ("Space", "full page down"),
        ("gg / G", "jump to top / bottom"),
        ("r", "reload the file"),
    ),
)

TABS_AND_HISTORY: Section = (
    "tabs & history",
    (
        ("gt / gT", "next / previous tab"),
        ("1-9 gt", "go to tab 1-9"),
        ("x", "close current tab"),
        ("C-o / C-i", "back / forward"),
    ),
)

FILES_AND_TOC: Section = (
    "files & toc",
    (
        ("e / t", "focus files / toc pane (press again to hide)"),
        ("Tab", "switch tree ↔ content"),
        ("Enter", "open in new tab / jump to heading"),
        ("h / l", "collapse / expand folder"),
        (".", "toggle non-Markdown files"),
        ("/", "filter tree by name"),
        ("Esc", "return to content"),
    ),
)

SEARCH: Section = (
    "search",
    (
        ("/", "open the search input"),
        ("Enter", "jump to the first match"),
        ("n / N", "next / previous match"),
        ("Esc", "cancel / clear the search"),
        ("S", "search across all files"),
    ),
)

LEFT_SECTIONS: tuple[Section, ...] = (READING, TABS_AND_HISTORY)
RIGHT_SECTIONS: tuple[Section, ...] = (FILES_AND_TOC, SEARCH)

CLOSE_HINTS = (
    f"[bold {ACCENT}]? / Esc / q[/] close this help"
    f" [{TEXT_FAINT}]·[/] [bold {ACCENT}]Ctrl+g[/] show / hide the key guide"
    f" [{TEXT_FAINT}]·[/] [bold {ACCENT}]w[/] welcome tour"
)

GUIDE_HIDDEN_NOTE = "key guide hidden — press Ctrl+g to bring it back"


def _format_section(section: Section, key_width: int) -> str:
    title, rows = section
    lines = [f"[bold {TEXT_MUTED}]{title.upper()}[/]"]
    lines += [f"[bold {ACCENT}]{key.ljust(key_width)}[/]{label}" for key, label in rows]
    return "\n".join(lines)


def format_column(sections: tuple[Section, ...]) -> str:
    """Render *sections* as one markup block with an aligned key column."""
    key_width = max(len(key) for _, rows in sections for key, _ in rows) + 2
    return "\n\n".join(_format_section(section, key_width) for section in sections)


class HelpScreen(ModalScreen[bool]):
    """Centered modal listing every keybinding grouped by category.

    Dismisses ``True`` when the user asked for the welcome tour (``w``),
    ``False`` on a plain close.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("question_mark", "dismiss_help", "close", show=False),
        Binding("escape", "dismiss_help", "close", show=False),
        Binding("q", "dismiss_help", "close", show=False),
        Binding("w", "open_tour", "welcome tour", show=False),
    ]

    def __init__(self, *, guide_hidden: bool = False) -> None:
        """Remember whether to point out the hidden key guide (req 2.7)."""
        super().__init__()
        self._guide_hidden = guide_hidden

    def compose(self) -> ComposeResult:
        """Lay out the bordered help panel: title, key columns, close hints."""
        with Vertical(id="help-panel"):
            yield Static("mokuji — keys", id="help-title")
            with Horizontal(id="help-columns"):
                yield Static(format_column(LEFT_SECTIONS), id="help-left")
                yield Static(format_column(RIGHT_SECTIONS), id="help-right")
            if self._guide_hidden:
                yield Static(GUIDE_HIDDEN_NOTE, id="help-note")
            yield Static(CLOSE_HINTS, id="help-close")

    def action_dismiss_help(self) -> None:
        """Close the modal."""
        self.dismiss(False)

    def action_open_tour(self) -> None:
        """Close the modal, asking the app to open the welcome tour."""
        self.dismiss(True)
