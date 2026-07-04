"""Per-tab state and pure tab arithmetic/label helpers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from .._document import Document


@dataclass(slots=True)
class TabState:
    """Everything mokuji remembers about one open tab."""

    document: Document
    tab_id: str
    history: list[tuple[Path, str | None]] = field(default_factory=list)
    history_index: int = 0
    scroll_y: float = 0.0


def tab_labels(paths: Sequence[Path]) -> list[str]:
    """Build tab labels: 1-based index + name, disambiguated with the parent dir.

    The index matches ``<N>gt`` (also 1-based) so the tab bar tells the
    user exactly which digits to type.
    """
    counts = Counter(path.name for path in paths)
    names = [
        f"{path.name} ({path.parent.name})" if counts[path.name] > 1 else path.name
        for path in paths
    ]
    return [f"{index} {name}" for index, name in enumerate(names, start=1)]


def next_tab_index(active: int, count: int | None, total: int) -> int:
    """Return the target index for ``gt`` / ``<N>gt`` (count is 1-based)."""
    if count is not None:
        return count - 1 if 1 <= count <= total else active
    return (active + 1) % total


def prev_tab_index(active: int, total: int) -> int:
    """Return the target index for ``gT``."""
    return (active - 1) % total
