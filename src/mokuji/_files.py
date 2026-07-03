"""File classification helpers, free of any UI dependency."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from ._errors import DocumentLoadError

if TYPE_CHECKING:
    from pathlib import Path

MAX_FILE_SIZE = 2 * 1024 * 1024
MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})

_BINARY_SNIFF_BYTES = 8 * 1024


class FileKind(enum.Enum):
    """How a file should be presented in the viewer."""

    MARKDOWN = "markdown"
    TEXT = "text"
    BINARY = "binary"
    TOO_LARGE = "too_large"


def is_markdown(path: Path) -> bool:
    """Return whether *path* has a Markdown suffix (case-insensitive)."""
    return path.suffix.lower() in MARKDOWN_SUFFIXES


def classify_file(path: Path) -> FileKind:
    """Classify *path* for display.

    Binary detection (a NUL byte in the first 8 KiB) wins over the size
    limit so an undisplayable file never triggers a load confirmation.

    Raises:
        DocumentLoadError: If the file cannot be inspected (chained from
            the underlying ``OSError``).
    """
    try:
        with path.open("rb") as handle:
            head = handle.read(_BINARY_SNIFF_BYTES)
        size = path.stat().st_size
    except OSError as error:
        message = f"cannot read: {path}"
        raise DocumentLoadError(message) from error
    if b"\x00" in head:
        return FileKind.BINARY
    if size > MAX_FILE_SIZE:
        return FileKind.TOO_LARGE
    if is_markdown(path):
        return FileKind.MARKDOWN
    return FileKind.TEXT
