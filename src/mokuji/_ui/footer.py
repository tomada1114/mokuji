"""The one-line key guide footer with a transient flash channel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.widgets import Static

if TYPE_CHECKING:
    from textual.timer import Timer

CONTENT_HINTS = (
    "j/k scroll · d/u page · / search · e files · t toc · gt tab · ? help · q quit"
)

FLASH_SECONDS = 3.0


class KeyGuide(Static):
    """Always-visible footer showing the keys that work right now."""

    def __init__(self, *, id: str | None = None) -> None:  # noqa: A002 — Textual's own widget id parameter name
        super().__init__(id=id)
        self._default = CONTENT_HINTS
        self._flash_timer: Timer | None = None

    def on_mount(self) -> None:
        """Show the content-focus hints by default."""
        self.update(self._default)

    def set_default(self, text: str | None) -> None:
        """Set the persistent footer text (``None`` restores the key hints).

        An in-flight flash keeps the screen until its timer restores the
        (new) persistent text.
        """
        self._default = text or CONTENT_HINTS
        if self._flash_timer is None:
            self.update(self._default)

    def flash(self, message: str) -> None:
        """Show *message* for a few seconds, then restore the persistent text."""
        self.update(message)
        if self._flash_timer is not None:
            self._flash_timer.stop()
        self._flash_timer = self.set_timer(FLASH_SECONDS, self._restore_default)

    def _restore_default(self) -> None:
        self._flash_timer = None
        self.update(self._default)
