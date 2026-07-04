"""Smart-case plain-substring search over document text."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Match:
    """One occurrence of the query inside a document's text."""

    start: int
    end: int
    line: int


def _smart_case_pair(text: str, query: str) -> tuple[str, str]:
    """Lowercase both *text* and *query* iff *query* is itself all-lowercase."""
    if query == query.lower():
        return text.lower(), query.lower()
    return text, query


def smart_case_contains(haystack: str, needle: str) -> bool:
    """Whether *needle* occurs in *haystack*.

    Same smart-case rule as :func:`find_matches`: an all-lowercase
    *needle* matches case-insensitively; one with any uppercase letter
    matches case-sensitively.
    """
    if not needle:
        return True
    hay, need = _smart_case_pair(haystack, needle)
    return need in hay


def find_matches(text: str, query: str) -> tuple[Match, ...]:
    """Find non-overlapping substring matches of *query* in *text*.

    Smart case: an all-lowercase query matches case-insensitively; a query
    containing any uppercase letter matches case-sensitively. The query is
    a literal string, never a regex.
    """
    if not query or not text:
        return ()
    haystack, needle = _smart_case_pair(text, query)
    line_starts = [0]
    line_starts.extend(index + 1 for index, char in enumerate(text) if char == "\n")
    matches: list[Match] = []
    position = haystack.find(needle)
    while position != -1:
        end = position + len(needle)
        line = bisect_right(line_starts, position) - 1
        matches.append(Match(start=position, end=end, line=line))
        position = haystack.find(needle, end)
    return tuple(matches)


def line_text_with_span(text: str, match: Match) -> tuple[str, int, int]:
    """Return the full line containing *match* and the query's span within it.

    ``Match.start``/``end`` are offsets into the whole document, not the
    line, so callers that want to show the matched line (e.g. the
    footer status) need the line's own text and a line-relative span.
    """
    line_start = text.rfind("\n", 0, match.start) + 1
    line_end = text.find("\n", match.end)
    if line_end == -1:
        line_end = len(text)
    return (
        text[line_start:line_end],
        match.start - line_start,
        match.end - line_start,
    )


def windowed_excerpt(
    line: str, start: int, end: int, *, max_chars: int
) -> tuple[str, int, int]:
    """Trim *line* to at most *max_chars*, keeping ``[start, end)`` visible.

    Returns ``(excerpt, span_start, span_end)`` with the span re-based to
    the excerpt's own coordinates. An ellipsis marks a cut edge; the
    match is centered in the trimmed window when both edges are cut.
    """
    if len(line) <= max_chars:
        return line, start, end
    window = max(max_chars - (end - start), 0)
    lead = window // 2
    left = max(0, start - lead)
    right = min(len(line), left + window)
    left = max(0, right - window)
    prefix = "…" if left > 0 else ""
    suffix = "…" if right < len(line) else ""
    excerpt = f"{prefix}{line[left:right]}{suffix}"
    return excerpt, len(prefix) + (start - left), len(prefix) + (end - left)
