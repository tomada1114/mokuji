"""The sumi color theme — fixed tokens from the mokuji visual design."""

from __future__ import annotations

from textual.theme import Theme

BG = "#16161e"
BG_PANEL = "#1a1b26"
BG_CHROME = "#1f2335"
BG_HOVER = "#292e42"
BG_SELECTION = "#33467c"

TEXT = "#c0caf5"
TEXT_SECONDARY = "#a9b1d6"
TEXT_MUTED = "#737aa2"
TEXT_FAINT = "#565f89"

ACCENT = "#7aa2f7"
ACCENT_ALT = "#bb9af7"
ACCENT_CYAN = "#7dcfff"
ACCENT_ORANGE = "#ff9e64"

SUCCESS = "#9ece6a"
WARNING = "#e0af68"
ERROR = "#f7768e"

SUMI_THEME = Theme(
    name="sumi",
    dark=True,
    primary=ACCENT,
    accent=ACCENT_ALT,
    foreground=TEXT,
    background=BG,
    surface=BG_CHROME,
    panel=BG_PANEL,
    success=SUCCESS,
    warning=WARNING,
    error=ERROR,
    variables={
        "block-hover-background": BG_HOVER,
        "block-cursor-background": BG_SELECTION,
        "block-cursor-blurred-background": BG_HOVER,
        "text-muted": TEXT_MUTED,
        "text-secondary": TEXT_SECONDARY,
        "text-faint": TEXT_FAINT,
        "accent-cyan": ACCENT_CYAN,
        "accent-orange": ACCENT_ORANGE,
    },
)
