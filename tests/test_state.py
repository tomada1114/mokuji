"""Tests for the first-run state persistence."""

from __future__ import annotations

from pathlib import Path

from mokuji._state import is_first_run, mark_tour_seen


class TestFirstRun:
    def test_is_first_run_true_without_marker(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        assert is_first_run() is True

    def test_mark_tour_seen_creates_marker_and_clears_first_run(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        mark_tour_seen()
        assert (tmp_path / "mokuji" / "tour-seen").is_file()
        assert is_first_run() is False

    def test_blank_xdg_state_home_falls_back_to_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_STATE_HOME", "  ")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        mark_tour_seen()
        assert (tmp_path / ".local" / "state" / "mokuji" / "tour-seen").is_file()

    def test_mark_tour_seen_swallows_oserror_and_stays_first_run(
        self, tmp_path, monkeypatch
    ):
        blocker = tmp_path / "state"
        blocker.write_text("not a directory", encoding="utf-8")
        monkeypatch.setenv("XDG_STATE_HOME", str(blocker))
        mark_tour_seen()  # must not raise
        assert is_first_run() is True
