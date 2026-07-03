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


def find_matches(text: str, query: str) -> tuple[Match, ...]:
    """Find non-overlapping substring matches of *query* in *text*.

    Smart case: an all-lowercase query matches case-insensitively; a query
    containing any uppercase letter matches case-sensitively. The query is
    a literal string, never a regex.
    """
    if not query or not text:
        return ()
    haystack = text
    needle = query
    if query == query.lower():
        haystack = text.lower()
        needle = query.lower()
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
