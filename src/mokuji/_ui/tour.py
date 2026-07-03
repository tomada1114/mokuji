"""The welcome tour: a first-run onboarding carousel (help ``w`` key).

Each page pairs a miniature mock of the real layout with the canonical
key rows imported from ``help.py`` — the single source of truth for
keybindings. When a binding changes there, the pages update themselves;
only the mock art and ``tutorial.md`` need a manual pass, and the
drift-guard test in ``tests/test_tour.py`` fails until they get one.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

from .._theme import ACCENT, TEXT_FAINT, TEXT_MUTED, TEXT_SECONDARY
from .help import FILES_AND_TOC, READING, SEARCH, TABS_AND_HISTORY, format_column

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from .help import Section


def tutorial_path() -> Path:
    """Path to the bundled hands-on tutorial document.

    mokuji is always installed on-disk (wheel/editable), so the package
    resource resolves to a real filesystem path.
    """
    return Path(str(resources.files("mokuji").joinpath("tutorial.md")))


@dataclass(frozen=True, slots=True)
class TourPage:
    """One carousel page: title, mock art, one-liner, and its key rows."""

    title: str
    mock: str
    blurb: str
    section: Section


_F = TEXT_FAINT
_A = ACCENT
_T = TEXT_SECONDARY

_MOCK_WELCOME = "\n".join(
    (
        f"[{_F}]┌────────┬──────────────────────────┐[/]",
        f"[{_F}]│ FILES  │[/][{_T}]  # A quiet reader        [/][{_F}]│[/]",
        f"[{_F}]│ ▸ a.md │                          │[/]",
        f"[{_F}]│   b.md │[/][{_T}]  Markdown, rendered for  [/][{_F}]│[/]",
        f"[{_F}]│        │[/][{_T}]  comfortable reading …   [/][{_F}]│[/]",
        f"[{_F}]├────────┴──────────────────────────┤[/]",
        f"[{_F}]│[/] [{_A}]j/k[/] [{_F}]scroll ·[/] [{_A}]t[/] [{_F}]toc ·"
        f"[/] [{_A}]?[/] [{_F}]help       │[/]",
        f"[{_F}]└───────────────────────────────────┘[/]",
    )
)

_MOCK_SIDEBAR = "\n".join(
    (
        f"[{_F}]┌[/] [{_A}]e[/] [{_F}]— FILES ────┐   ┌[/] [{_A}]t[/]"
        f" [{_F}]— TOC ──────┐[/]",
        f"[{_F}]│[/][{_T}] ▸ docs/       [/][{_F}]│   │[/][{_T}] Reading       [/][{_F}]│[/]",
        f"[{_F}]│[/][{_A}]   README.md   [/][{_F}]│   │[/][{_T}] ├ The basics  [/][{_F}]│[/]",
        f"[{_F}]│[/][{_T}]   notes.md    [/][{_F}]│   │[/][{_T}] └ Going far   [/][{_F}]│[/]",
        f"[{_F}]└───────────────┘   └───────────────┘[/]",
    )
)

_MOCK_TABS = "\n".join(
    (
        f"[{_T}]  README.md  [/][bold {_A}] guide.md [/][{_T}]  notes.md  [/]",
        f"[{_F}]             [/][{_A}]━━━━━━━━━━[/]",
        "",
        f"[{_F}]  ← ctrl+o        history        ctrl+i →[/]",
    )
)

_MOCK_SEARCH = "\n".join(
    (
        f"[{_T}]  … a paper [/][bold {_A}]lantern[/][{_T}] reads best in a …  [/]",
        f"[{_F}]            ▲ match 1/3[/]",
        f"[{_F}]┌───────────────────────────────────┐[/]",
        f"[{_F}]│[/] [{_A}]/[/] [{_T}]lantern▌                        [/][{_F}]│[/]",
        f"[{_F}]└───────────────────────────────────┘[/]",
    )
)

_MOCK_FINISH = "\n".join(
    (
        "",
        f"[{_F}]        ── that's the whole map ──[/]",
        "",
        f"[{_T}]     press [/][bold {_A}]Enter[/][{_T}] to open a hands-on[/]",
        f"[{_T}]     tutorial and try the keys yourself[/]",
        "",
    )
)

FINISH_SECTION: Section = (
    "whenever you need it",
    (
        ("?", "open the full key reference"),
        ("w", "replay this tour (from the help screen)"),
        ("C-g", "show / hide the key guide"),
    ),
)

PAGES: tuple[TourPage, ...] = (
    TourPage(
        title="welcome to mokuji",
        mock=_MOCK_WELCOME,
        blurb="A readability-first Markdown reader. Everything is a "
        "keystroke away — starting with plain Vim-style reading.",
        section=READING,
    ),
    TourPage(
        title="files & table of contents",
        mock=_MOCK_SIDEBAR,
        blurb="One sidebar, two modes: browse the directory you launched "
        "in, or jump around the open document by heading.",
        section=FILES_AND_TOC,
    ),
    TourPage(
        title="tabs & history",
        mock=_MOCK_TABS,
        blurb="Keep several documents open and walk your jump history "
        "back and forth, per tab, just like in Vim.",
        section=TABS_AND_HISTORY,
    ),
    TourPage(
        title="search",
        mock=_MOCK_SEARCH,
        blurb="Substring search with smart case: lowercase matches "
        "anything, add a capital to match exactly.",
        section=SEARCH,
    ),
    TourPage(
        title="you're all set",
        mock=_MOCK_FINISH,
        blurb="Forget a key? The reference and this tour are always one "
        "keystroke away.",
        section=FINISH_SECTION,
    ),
)

_HINTS_MIDDLE = (
    f"[bold {ACCENT}]l[/] next [{TEXT_FAINT}]·[/] [bold {ACCENT}]h[/] back"
    f" [{TEXT_FAINT}]·[/] [bold {ACCENT}]Esc[/] skip"
)
_HINTS_LAST = (
    f"[bold {ACCENT}]Enter[/] open the tutorial [{TEXT_FAINT}]·[/]"
    f" [bold {ACCENT}]h[/] back [{TEXT_FAINT}]·[/]"
    f" [bold {ACCENT}]Esc[/] start reading"
)


def page_dots(index: int, total: int) -> str:
    """Render the ``● ○ ○`` progress dots plus an ``n/total`` counter."""
    dots = "  ".join("●" if i == index else "○" for i in range(total))
    return f"[{ACCENT}]{dots}[/]   [{TEXT_MUTED}]{index + 1}/{total}[/]"


class TourScreen(ModalScreen[bool]):
    """Carousel modal; dismisses ``True`` to open the bundled tutorial."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("l,right", "next_page", "next", show=False),
        Binding("h,left", "prev_page", "back", show=False),
        Binding("enter", "advance", "next / finish", show=False),
        Binding("escape,q", "skip", "skip", show=False),
    ]

    def __init__(self) -> None:
        """Start the carousel on the first page."""
        super().__init__()
        self._index = 0

    def compose(self) -> ComposeResult:
        """Lay out the tour panel: title, mock, blurb, keys, dots, hints."""
        with Vertical(id="tour-panel"):
            yield Static(id="tour-title")
            yield Static(id="tour-mock")
            yield Static(id="tour-blurb")
            yield Static(id="tour-keys")
            yield Static(id="tour-dots")
            yield Static(id="tour-hints")

    def on_mount(self) -> None:
        """Render the first page."""
        self._show_page()

    @property
    def page_index(self) -> int:
        """Index of the page currently shown."""
        return self._index

    def action_next_page(self) -> None:
        """Go to the next page (``l``); no-op on the last page."""
        if self._index < len(PAGES) - 1:
            self._index += 1
            self._show_page()

    def action_prev_page(self) -> None:
        """Go to the previous page (``h``); no-op on the first page."""
        if self._index > 0:
            self._index -= 1
            self._show_page()

    def action_advance(self) -> None:
        """Enter: next page, or finish into the tutorial on the last one."""
        if self._index == len(PAGES) - 1:
            self.dismiss(True)
        else:
            self.action_next_page()

    def action_skip(self) -> None:
        """Close the tour without opening the tutorial."""
        self.dismiss(False)

    def _show_page(self) -> None:
        page = PAGES[self._index]
        last = self._index == len(PAGES) - 1
        self.query_one("#tour-title", Static).update(page.title)
        self.query_one("#tour-mock", Static).update(page.mock)
        self.query_one("#tour-blurb", Static).update(page.blurb)
        self.query_one("#tour-keys", Static).update(format_column((page.section,)))
        self.query_one("#tour-dots", Static).update(page_dots(self._index, len(PAGES)))
        self.query_one("#tour-hints", Static).update(
            _HINTS_LAST if last else _HINTS_MIDDLE
        )
