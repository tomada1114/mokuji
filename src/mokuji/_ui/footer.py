"""The one-line key guide footer with a transient flash channel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.content import Content
from textual.widgets import Static

from .._theme import ACCENT, TEXT_FAINT

if TYPE_CHECKING:
    from textual.timer import Timer

KeyHint = tuple[str, str]
TieredHint = tuple[str, str, int]

_SEPARATOR = f" [{TEXT_FAINT}]·[/] "
_SEPARATOR_CELLS = 3

CONTENT_HINTS: tuple[TieredHint, ...] = (
    ("j/k", "scroll", 0),
    ("d/u", "page", 1),
    ("gg/G", "top/bottom", 2),
    ("/", "search", 0),
    ("e", "file tree", 0),
    ("t", "toc", 1),
    ("gt", "tab", 1),
    ("x", "close tab", 2),
    ("C-o/C-i", "history", 3),
    ("r", "reload", 3),
    ("?", "help", 0),
    ("q", "quit", 0),
)

TREE_HINTS: tuple[TieredHint, ...] = (
    ("j/k", "move", 0),
    ("h/l", "collapse/expand", 2),
    ("Enter", "open in new tab", 0),
    ("Esc", "back to content", 1),
    ("Tab", "switch focus", 2),
    (".", "all files", 0),
    ("e", "close pane", 0),
    ("?", "help", 0),
)

FLASH_SECONDS = 3.0

MAX_GUIDE_LINES = 3


def format_hints(hints: tuple[KeyHint, ...]) -> str:
    """Render ``(key, label)`` pairs as markup: accented keys, muted labels."""
    return _SEPARATOR.join(f"[bold {ACCENT}]{key}[/] {label}" for key, label in hints)


def _wrap(hints: tuple[KeyHint, ...], width: int) -> tuple[tuple[KeyHint, ...], ...]:
    lines: list[tuple[KeyHint, ...]] = []
    current: list[KeyHint] = []
    used = 0
    for key, label in hints:
        cells = len(key) + 1 + len(label)
        needed = cells if not current else cells + _SEPARATOR_CELLS
        if current and used + needed > width:
            lines.append(tuple(current))
            current = [(key, label)]
            used = cells
        else:
            current.append((key, label))
            used += needed
    if current:
        lines.append(tuple(current))
    return tuple(lines)


def wrap_hints(
    hints: tuple[TieredHint, ...], width: int, max_lines: int = MAX_GUIDE_LINES
) -> tuple[tuple[KeyHint, ...], ...]:
    """Wrap *hints* into at most *max_lines* rows of *width* terminal cells.

    Every hint is shown when it wraps within the cap; only when even
    wrapping cannot fit are the highest tiers dropped, one at a time.
    Tier 0 is the floor: it is returned even when it exceeds the cap, so
    a degenerate footer crops rather than going blank.
    """
    for level in sorted({tier for _, _, tier in hints}, reverse=True):
        chosen = tuple((key, label) for key, label, tier in hints if tier <= level)
        wrapped = _wrap(chosen, width)
        if len(wrapped) <= max_lines:
            return wrapped
    return _wrap(tuple((key, label) for key, label, tier in hints if tier == 0), width)


class KeyGuide(Static):
    """Always-visible footer showing the keys that work right now."""

    def __init__(self, *, id: str | None = None) -> None:  # noqa: A002 — Textual's own widget id parameter name
        super().__init__(id=id)
        self._default: str | tuple[TieredHint, ...] = CONTENT_HINTS
        self._flash_timer: Timer | None = None

    def on_mount(self) -> None:
        """Show the content-focus hints by default."""
        self.update(self._render_default())

    def on_resize(self) -> None:
        """Re-pick the hint tier for the new width (flashes stay put)."""
        if self._flash_timer is None:
            self.update(self._render_default())

    def set_default(self, value: str | tuple[TieredHint, ...] | None) -> None:
        """Set the persistent footer text (``None`` restores the key hints).

        *value* is either literal text (e.g. the search status) or a tiered
        hint set that re-fits itself on resize. An in-flight flash keeps
        the screen until its timer restores the (new) persistent text.
        """
        self._default = value if value is not None else CONTENT_HINTS
        if self._flash_timer is None:
            self.update(self._render_default())

    def flash(self, message: str) -> None:
        """Show *message* for a few seconds, then restore the persistent text.

        The message is treated as plain text: file paths and search queries
        may contain ``[``, which would otherwise be parsed as markup. It is
        padded to the height of the hints it covers so the footer does not
        jump while the flash is up.
        """
        padding = "\n" * self._render_default().count("\n")
        self.update(Content(message + padding))
        if self._flash_timer is not None:
            self._flash_timer.stop()
        self._flash_timer = self.set_timer(FLASH_SECONDS, self._restore_default)

    def _render_default(self) -> str:
        if isinstance(self._default, str):
            return self._default
        # ``size`` is the content area, so padding is already excluded.
        lines = wrap_hints(self._default, self.size.width)
        return "\n".join(format_hints(line) for line in lines)

    def _restore_default(self) -> None:
        self._flash_timer = None
        self.update(self._render_default())
