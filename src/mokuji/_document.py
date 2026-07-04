"""Document model: loading, heading extraction, and link resolution."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlsplit

from ._errors import DocumentLoadError
from ._files import FileKind, classify_file, is_markdown

if TYPE_CHECKING:
    from pathlib import Path

MAX_TOC_LEVEL = 4

_ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*$")
_TRAILING_HASHES = re.compile(r"\s+#+\s*$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_SLUG_DISALLOWED = re.compile(r"[^\w\s-]")


@dataclass(frozen=True, slots=True)
class Heading:
    """One TOC entry extracted from a Markdown document."""

    level: int
    text: str
    slug: str
    line: int


@dataclass(frozen=True, slots=True)
class Document:
    """An immutable snapshot of a file as loaded from disk."""

    path: Path
    text: str
    kind: FileKind
    headings: tuple[Heading, ...]


@dataclass(frozen=True, slots=True)
class InternalLink:
    """A link to a file on disk, optionally with a heading anchor."""

    path: Path
    anchor: str | None


@dataclass(frozen=True, slots=True)
class ExternalLink:
    """An http/https link to open in the OS browser."""

    url: str


@dataclass(frozen=True, slots=True)
class UnsupportedLink:
    """A link with a scheme mokuji cannot follow (mailto: etc.)."""

    href: str


LinkTarget = InternalLink | ExternalLink | UnsupportedLink


def slugify(text: str) -> str:
    """Return the GitHub-style anchor slug for a heading text."""
    lowered = _SLUG_DISALLOWED.sub("", text.lower())
    return lowered.replace(" ", "-")


def extract_headings(text: str) -> tuple[Heading, ...]:
    """Extract H1-H4 ATX headings, skipping fenced code blocks.

    Duplicate slugs get ``-1``, ``-2``... suffixes, matching GitHub's
    anchor disambiguation.
    """
    headings: list[Heading] = []
    slug_counts: dict[str, int] = {}
    fence_marker: str | None = None
    for line_number, line in enumerate(text.splitlines()):
        fence = _FENCE.match(line)
        if fence:
            marker = fence.group(1)[0]
            if fence_marker is None:
                fence_marker = marker
            elif marker == fence_marker:
                fence_marker = None
            continue
        if fence_marker is not None:
            continue
        match = _ATX_HEADING.match(line)
        if match is None:
            continue
        level = len(match.group(1))
        if level > MAX_TOC_LEVEL:
            continue
        heading_text = _TRAILING_HASHES.sub("", match.group(2))
        slug = slugify(heading_text)
        seen = slug_counts.get(slug, 0)
        slug_counts[slug] = seen + 1
        if seen:
            slug = f"{slug}-{seen}"
        headings.append(
            Heading(level=level, text=heading_text, slug=slug, line=line_number)
        )
    return tuple(headings)


def load_document(path: Path, *, allow_large: bool = False) -> Document:
    """Load *path* into a :class:`Document`.

    BINARY and (unconfirmed) TOO_LARGE files load with empty text — the
    viewer renders a notice for them instead of content.

    Args:
        path: File to read.
        allow_large: Load files over the size limit anyway (after the user
            confirmed, req 2.2).

    Raises:
        DocumentLoadError: If the file cannot be read (chained from the
            underlying ``OSError``).
    """
    kind = classify_file(path)
    if kind is FileKind.BINARY or (kind is FileKind.TOO_LARGE and not allow_large):
        return Document(path=path, text="", kind=kind, headings=())
    if kind is FileKind.TOO_LARGE:
        kind = FileKind.MARKDOWN if is_markdown(path) else FileKind.TEXT
    try:
        raw = path.read_bytes()
    except OSError as error:
        message = f"cannot read: {path}"
        raise DocumentLoadError(message) from error
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
    headings = extract_headings(text) if kind is FileKind.MARKDOWN else ()
    return Document(path=path, text=text, kind=kind, headings=headings)


def resolve_link(base: Path, href: str) -> LinkTarget:
    """Resolve a Markdown *href* found in the document at *base*.

    Relative paths resolve against ``base.parent``; ``Path.resolve()``
    clamps ``..`` traversal at the filesystem root.
    """
    parts = urlsplit(href)
    if parts.scheme in {"http", "https"}:
        return ExternalLink(url=href)
    if parts.scheme:
        return UnsupportedLink(href=href)
    anchor = unquote(parts.fragment) or None
    if not parts.path:
        return InternalLink(path=base.resolve(), anchor=anchor)
    target = (base.parent / unquote(parts.path)).resolve()
    return InternalLink(path=target, anchor=anchor)
