"""File classification helpers, free of any UI dependency."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from ._errors import DocumentLoadError
from ._search import smart_case_contains

if TYPE_CHECKING:
    from pathlib import Path

MAX_FILE_SIZE = 2 * 1024 * 1024
MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})

IGNORED_DIR_NAMES = frozenset(
    {
        "node_modules",
        "__pycache__",
        "dist",
        "build",
        "target",
        ".tox",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
    }
)

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


def is_hidden_by_default(path: Path) -> bool:
    """Whether *path* is hidden by the FILES tree's default (Markdown-only) view.

    Dot-entries and the fixed build/tooling-noise ignore set are hidden
    regardless of kind; directories are otherwise always kept (so their
    Markdown descendants stay reachable); other files are hidden unless
    they are Markdown. ``.git`` is handled separately by the caller (it
    is hidden in both tree modes, not just the default one).
    """
    if path.name.startswith(".") or path.name in IGNORED_DIR_NAMES:
        return True
    if path.is_dir():
        return False
    return not is_markdown(path)


def matching_descendant_paths(root: Path, query: str, *, show_all: bool) -> set[Path]:
    """Find every path under *root* matching *query* (smart-case substring).

    Honors the same visibility rules as the FILES tree (``.git`` always
    hidden; dot-entries/ignore-set/non-Markdown also hidden unless
    *show_all*). Returns the matches themselves plus each match's
    ancestor directories up to (not including) *root*, so a caller can
    expand exactly those directories to reveal the matches. Returns an
    empty set for an empty *query*.
    """
    if not query:
        return set()
    keep: set[Path] = set()

    def visit(directory: Path) -> bool:
        found_any = False
        try:
            entries = directory.iterdir()
        except OSError:
            return False
        for entry in entries:
            if entry.name == ".git":
                continue
            if not show_all and is_hidden_by_default(entry):
                continue
            is_match = smart_case_contains(entry.name, query)
            child_has_match = visit(entry) if entry.is_dir() else False
            if is_match or child_has_match:
                keep.add(entry)
                found_any = True
        return found_any

    visit(root)
    return keep
