"""Tests for the Vim-style key sequence machine."""

from __future__ import annotations

import pytest

from mokuji._ui.keys import KeySequenceMachine


@pytest.fixture
def recorder():
    class Recorder:
        def __init__(self):
            self.calls: list[object] = []
            self.machine = KeySequenceMachine(
                scroll_top=lambda: self.calls.append("top"),
                tab_next=lambda count: self.calls.append(("next", count)),
                tab_prev=lambda: self.calls.append("prev"),
            )

    return Recorder()


class TestKeySequenceMachine:
    def test_gg_triggers_scroll_top(self, recorder):
        assert recorder.machine.handle("g") is True
        assert recorder.machine.handle("g") is True
        assert recorder.calls == ["top"]

    def test_gt_triggers_tab_next_without_count(self, recorder):
        recorder.machine.handle("g")
        assert recorder.machine.handle("t") is True
        assert recorder.calls == [("next", None)]

    def test_count_gt_passes_count(self, recorder):
        recorder.machine.handle("3")
        recorder.machine.handle("g")
        recorder.machine.handle("t")
        assert recorder.calls == [("next", 3)]

    def test_multi_digit_count_accumulates(self, recorder):
        recorder.machine.handle("1")
        recorder.machine.handle("2")
        recorder.machine.handle("g")
        recorder.machine.handle("t")
        assert recorder.calls == [("next", 12)]

    def test_g_then_shift_t_triggers_tab_prev(self, recorder):
        recorder.machine.handle("g")
        assert recorder.machine.handle("T") is True
        assert recorder.calls == ["prev"]

    def test_t_without_pending_g_is_not_consumed(self, recorder):
        assert recorder.machine.handle("t") is False
        assert recorder.calls == []

    def test_other_key_clears_pending_and_is_not_consumed(self, recorder):
        recorder.machine.handle("g")
        assert recorder.machine.handle("j") is False
        recorder.machine.handle("g")
        assert recorder.calls == []

    def test_digit_after_g_restarts_count(self, recorder):
        recorder.machine.handle("g")
        recorder.machine.handle("2")
        recorder.machine.handle("g")
        recorder.machine.handle("t")
        assert recorder.calls == [("next", 2)]

    def test_reset_clears_all_pending_state(self, recorder):
        recorder.machine.handle("4")
        recorder.machine.handle("g")
        recorder.machine.reset()
        recorder.machine.handle("t")
        assert recorder.calls == []
