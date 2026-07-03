"""The one-line key guide footer."""

from __future__ import annotations

from textual.widgets import Static

CONTENT_HINTS = (
    "j/k scroll · d/u page · / search · e files · t toc · gt tab · ? help · q quit"
)


class KeyGuide(Static):
    """Always-visible footer showing the keys that work right now."""

    def on_mount(self) -> None:
        """Show the content-focus hints by default."""
        self.update(CONTENT_HINTS)
