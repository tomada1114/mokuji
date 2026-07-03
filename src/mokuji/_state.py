"""First-run state persistence — pure: no Textual imports.

The only state mokuji keeps between runs is a marker file recording that
the welcome tour has been shown, stored under the XDG state directory
(``$XDG_STATE_HOME/mokuji``, defaulting to ``~/.local/state/mokuji``).
"""

from __future__ import annotations

import os
from pathlib import Path

_MARKER_NAME = "tour-seen"


def _state_dir() -> Path:
    """Return the mokuji state directory per the XDG base-dir spec."""
    xdg_state = os.environ.get("XDG_STATE_HOME", "").strip()
    base = Path(xdg_state) if xdg_state else Path.home() / ".local" / "state"
    return base / "mokuji"


def is_first_run() -> bool:
    """Return whether the welcome tour has never been marked as seen."""
    return not (_state_dir() / _MARKER_NAME).exists()


def mark_tour_seen() -> None:
    """Record that the welcome tour was shown.

    Failures are swallowed on purpose: on a read-only or misconfigured
    home the worst outcome must be "the tour shows again next launch",
    never a crash at startup.
    """
    try:
        directory = _state_dir()
        directory.mkdir(parents=True, exist_ok=True)
        (directory / _MARKER_NAME).touch()
    except OSError:
        pass
