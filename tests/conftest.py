"""Shared test fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    """Keep app state out of the real home and mute the welcome tour.

    Every pilot test would otherwise trip the first-run tour modal (and
    write a marker under ``~/.local/state``). Tour tests opt back in by
    deleting the marker via the ``first_run`` fixture.
    """
    state_home = tmp_path / "xdg-state"
    marker_dir = state_home / "mokuji"
    marker_dir.mkdir(parents=True)
    (marker_dir / "tour-seen").touch()
    monkeypatch.setenv("XDG_STATE_HOME", str(state_home))
    return marker_dir / "tour-seen"


@pytest.fixture
def first_run(_isolated_state):
    """Make the app believe it has never shown the welcome tour."""
    _isolated_state.unlink()
    return _isolated_state
