"""Vim-style multi-key sequence machine (``gg``, ``gt``, ``gT``, ``<N>gt``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

_COUNT_DIGITS = frozenset("123456789")


class KeySequenceMachine:
    """Tracks pending count digits and a pending ``g`` between key presses.

    Textual has no chord bindings, so multi-key sequences are resolved here
    (Vim-like: no timeout; any non-sequence key clears the pending state).
    """

    def __init__(
        self,
        *,
        scroll_top: Callable[[], None],
        tab_next: Callable[[int | None], None],
        tab_prev: Callable[[], None],
    ) -> None:
        """Wire the sequence completions to their app actions."""
        self._scroll_top = scroll_top
        self._tab_next = tab_next
        self._tab_prev = tab_prev
        self._count = ""
        self._saw_g = False

    def reset(self) -> None:
        """Forget any pending sequence state."""
        self._count = ""
        self._saw_g = False

    def handle(self, key: str) -> bool:
        """Process *key*; return whether the machine consumed it."""
        if key == "g":
            if self._saw_g:
                self.reset()
                self._scroll_top()
            else:
                self._saw_g = True
            return True
        if self._saw_g and key in {"t", "T"}:
            count = int(self._count) if self._count else None
            self.reset()
            if key == "t":
                self._tab_next(count)
            else:
                self._tab_prev()
            return True
        if key in _COUNT_DIGITS:
            if self._saw_g:
                self.reset()
            self._count += key
            return True
        self.reset()
        return False
