"""Application-wide Textual CSS for mokuji (sumi visual design)."""

from __future__ import annotations

from .._theme import ACCENT, BG_CHROME, BG_PANEL, ERROR, TEXT_MUTED

APP_CSS = f"""
Screen {{
    background: $background;
    layers: base overlay;
}}
Tabs {{
    background: {BG_CHROME};
}}
#main {{
    height: 1fr;
}}
Sidebar {{
    width: 28;
    min-width: 20;
    background: {BG_PANEL};
    border-left: wide {BG_PANEL};
}}
Sidebar:focus-within {{
    border-left: wide {ACCENT};
}}
Sidebar.-overlay {{
    layer: overlay;
    dock: left;
    height: 100%;
}}
#sidebar-title {{
    height: 1;
    padding: 0 1;
    color: {TEXT_MUTED};
    text-style: bold;
    background: {BG_PANEL};
}}
FilesTree, TocTree {{
    background: {BG_PANEL};
}}
ViewerPane {{
    background: $background;
    align-horizontal: center;
}}
ViewerPane > .content {{
    max-width: 100;
    width: 100%;
    padding: 0 2;
    background: $background;
}}
ViewerPane > .notice {{
    color: {TEXT_MUTED};
    text-align: center;
    padding: 2 2;
}}
KeyGuide {{
    dock: bottom;
    height: 1;
    background: {BG_CHROME};
    color: {TEXT_MUTED};
    padding: 0 1;
}}
KeyGuide.-error {{
    color: {ERROR};
}}
SearchInput {{
    dock: bottom;
    height: 1;
    border: none;
    padding: 0 1;
    background: {BG_CHROME};
}}
SearchInput:focus {{
    border: none;
}}
"""
