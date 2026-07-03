"""The one-line key guide footer."""

from __future__ import annotations

from textual.widgets import Static

CONTENT_HINTS = (
    "j/k scroll · d/u page · / search · e files · t toc · gt tab · ? help · q quit"
)


FLASH_SECONDS = 3.0


class KeyGuide(Static):
    """Always-visible footer showing the keys that work right now."""

    def on_mount(self) -> None:
        """Show the content-focus hints by default."""
        self.update(CONTENT_HINTS)

    def flash(self, message: str) -> None:
        """Show *message* for a few seconds, then restore the key hints."""
        self.update(message)
        self.set_timer(FLASH_SECONDS, lambda: self.update(CONTENT_HINTS))
