"""Pure repo-wide search: walk Markdown files under a root and find matches.

No Textual/UI imports (dependency rule); the modal screen that presents
these results lives in ``_ui/``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ._errors import DocumentLoadError
from ._files import FileKind, classify_file, is_markdown
from ._search import find_matches, line_text_with_span, windowed_excerpt

if TYPE_CHECKING:
    from collections.abc import Iterator

MAX_TOTAL_HITS = 200
MAX_HITS_PER_FILE = 20
EXCERPT_MAX_CHARS = 80


@dataclass(frozen=True, slots=True)
class Hit:
    """One matched line within a file, for repo-wide search results."""

    path: Path
    line: int
    text: str
    span_start: int
    span_end: int


@dataclass(frozen=True, slots=True)
class RepoSearchResults:
    """The (possibly capped) outcome of a repo-wide search."""

    hits: tuple[Hit, ...]
    match_count: int
    file_count: int
    truncated: bool


def search_repo(root: Path, query: str) -> RepoSearchResults:
    """Search every Markdown file under *root* for *query* (smart-case).

    ``.git`` is never descended into; binary and TOO_LARGE files are
    skipped (per :func:`_files.classify_file`). The tree's display
    filter (dot-entries, build-noise ignore set) does NOT apply here —
    repo-wide search scans every reachable Markdown file. Caps at
    :data:`MAX_TOTAL_HITS` hits total and :data:`MAX_HITS_PER_FILE` per
    file; ``truncated`` is set when either cap drops a match.
    """
    hits: list[Hit] = []
    match_count = 0
    file_count = 0
    truncated = False
    for path in _walk_markdown_files(root):
        try:
            if classify_file(path) is not FileKind.MARKDOWN:
                continue
            text = path.read_text(encoding="utf-8")
        except (DocumentLoadError, OSError, UnicodeDecodeError):
            continue
        matches = find_matches(text, query)
        if not matches:
            continue
        file_count += 1
        match_count += len(matches)
        relative = path.relative_to(root)
        for index, match in enumerate(matches):
            if index >= MAX_HITS_PER_FILE:
                truncated = True
                break
            if len(hits) >= MAX_TOTAL_HITS:
                truncated = True
                break
            line_text, start, end = line_text_with_span(text, match)
            excerpt, span_start, span_end = windowed_excerpt(
                line_text, start, end, max_chars=EXCERPT_MAX_CHARS
            )
            hits.append(
                Hit(
                    path=relative,
                    line=match.line,
                    text=excerpt,
                    span_start=span_start,
                    span_end=span_end,
                )
            )
        if len(hits) >= MAX_TOTAL_HITS:
            truncated = True
            break
    return RepoSearchResults(
        hits=tuple(hits),
        match_count=match_count,
        file_count=file_count,
        truncated=truncated,
    )


def _walk_markdown_files(root: Path) -> Iterator[Path]:
    """Yield every Markdown file under *root*, pruning ``.git`` entirely."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name != ".git")
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if is_markdown(path):
                yield path
