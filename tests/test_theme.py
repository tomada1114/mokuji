"""Tests for mokuji._theme."""

from __future__ import annotations

import pytest

from mokuji import _theme
from mokuji._theme import SUMI_THEME

EXPECTED_TOKENS = {
    "BG": "#16161e",
    "BG_PANEL": "#1a1b26",
    "BG_CHROME": "#1f2335",
    "BG_HOVER": "#292e42",
    "BG_SELECTION": "#33467c",
    "TEXT": "#c0caf5",
    "TEXT_SECONDARY": "#a9b1d6",
    "TEXT_MUTED": "#737aa2",
    "TEXT_FAINT": "#565f89",
    "ACCENT": "#7aa2f7",
    "ACCENT_ALT": "#bb9af7",
    "ACCENT_CYAN": "#7dcfff",
    "ACCENT_ORANGE": "#ff9e64",
    "SUCCESS": "#9ece6a",
    "WARNING": "#e0af68",
    "ERROR": "#f7768e",
}


class TestSumiTokens:
    @pytest.mark.parametrize(
        ("token", "value"),
        [
            pytest.param(token, value, id=token)
            for token, value in EXPECTED_TOKENS.items()
        ],
    )
    def test_token_constant_has_exact_hex_value(self, token, value):
        assert getattr(_theme, token) == value


class TestSumiTheme:
    def test_theme_is_named_sumi_and_dark(self):
        assert SUMI_THEME.name == "sumi"
        assert SUMI_THEME.dark is True

    def test_theme_maps_core_fields_to_tokens(self):
        assert SUMI_THEME.primary == _theme.ACCENT
        assert SUMI_THEME.background == _theme.BG
        assert SUMI_THEME.surface == _theme.BG_CHROME
        assert SUMI_THEME.panel == _theme.BG_PANEL
        assert SUMI_THEME.foreground == _theme.TEXT
        assert SUMI_THEME.accent == _theme.ACCENT_ALT
        assert SUMI_THEME.success == _theme.SUCCESS
        assert SUMI_THEME.warning == _theme.WARNING
        assert SUMI_THEME.error == _theme.ERROR
