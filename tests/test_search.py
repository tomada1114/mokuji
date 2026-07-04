"""Tests for mokuji._search."""

from __future__ import annotations

import pytest

from mokuji._search import (
    Match,
    find_matches,
    line_text_with_span,
    smart_case_contains,
    windowed_excerpt,
)


class TestFindMatches:
    def test_empty_query_returns_no_matches(self):
        assert find_matches("some text", "") == ()

    def test_empty_text_returns_no_matches(self):
        assert find_matches("", "query") == ()

    def test_single_match_reports_offsets_and_line(self):
        matches = find_matches("alpha\nbeta\n", "beta")
        assert matches == (Match(start=6, end=10, line=1),)

    def test_lowercase_query_matches_case_insensitively(self):
        matches = find_matches("Alpha ALPHA alpha", "alpha")
        assert len(matches) == 3

    def test_uppercase_query_matches_case_sensitively(self):
        matches = find_matches("Alpha ALPHA alpha", "Alpha")
        assert matches == (Match(start=0, end=5, line=0),)

    def test_query_absent_returns_no_matches(self):
        assert find_matches("alpha beta", "gamma") == ()

    def test_matches_are_non_overlapping(self):
        matches = find_matches("aaaa", "aa")
        assert matches == (Match(start=0, end=2, line=0), Match(start=2, end=4, line=0))

    def test_regex_metacharacters_are_literal(self):
        assert find_matches("abc", "a.c") == ()
        assert find_matches("a.c", "a.c") == (Match(start=0, end=3, line=0),)

    def test_line_numbers_are_zero_based_across_lines(self):
        text = "x\nx\nx\n"
        matches = find_matches(text, "x")
        assert [m.line for m in matches] == [0, 1, 2]

    def test_unicode_query_matches_by_codepoint_offsets(self):
        text = "序文\n目次 mokuji\n"
        matches = find_matches(text, "目次")
        assert matches == (Match(start=3, end=5, line=1),)

    def test_match_dataclass_is_frozen(self):
        match = Match(start=0, end=1, line=0)
        with pytest.raises(AttributeError):
            match.start = 5  # type: ignore[misc]


class TestLineTextWithSpan:
    def test_first_line_span_is_relative_to_line_start(self):
        text = "hello world\n"
        match = Match(start=6, end=11, line=0)
        line, start, end = line_text_with_span(text, match)
        assert (line, start, end) == ("hello world", 6, 11)

    def test_later_line_span_is_relative_to_that_lines_start(self):
        text = "alpha\nneedle here\nomega\n"
        (match,) = find_matches(text, "needle")
        line, start, end = line_text_with_span(text, match)
        assert (line, start, end) == ("needle here", 0, 6)

    def test_last_line_without_trailing_newline(self):
        text = "alpha\nbeta"
        match = Match(start=6, end=10, line=1)
        line, start, end = line_text_with_span(text, match)
        assert (line, start, end) == ("beta", 0, 4)


class TestWindowedExcerpt:
    def test_short_line_is_returned_verbatim(self):
        excerpt, start, end = windowed_excerpt("hello world", 6, 11, max_chars=60)
        assert (excerpt, start, end) == ("hello world", 6, 11)

    def test_long_line_is_windowed_around_the_match(self):
        line = "x" * 100 + "needle" + "y" * 100
        excerpt, start, end = windowed_excerpt(line, 100, 106, max_chars=20)
        assert excerpt.startswith("…")
        assert excerpt.endswith("…")
        assert excerpt[start:end] == "needle"
        assert len(excerpt) <= 22

    def test_match_near_line_start_has_no_leading_ellipsis(self):
        line = "needle" + "y" * 100
        excerpt, start, end = windowed_excerpt(line, 0, 6, max_chars=20)
        assert not excerpt.startswith("…")
        assert excerpt.endswith("…")
        assert excerpt[start:end] == "needle"

    def test_match_near_line_end_has_no_trailing_ellipsis(self):
        line = "x" * 100 + "needle"
        excerpt, start, end = windowed_excerpt(line, 100, 106, max_chars=20)
        assert excerpt.startswith("…")
        assert not excerpt.endswith("…")
        assert excerpt[start:end] == "needle"


class TestSmartCaseContains:
    def test_empty_needle_always_matches(self):
        assert smart_case_contains("anything", "")

    def test_lowercase_needle_matches_case_insensitively(self):
        assert smart_case_contains("Alpha Beta", "alpha")
        assert smart_case_contains("ALPHA BETA", "alpha")

    def test_uppercase_needle_matches_case_sensitively(self):
        assert smart_case_contains("Alpha Beta", "Alpha")
        assert not smart_case_contains("alpha beta", "Alpha")

    def test_absent_needle_does_not_match(self):
        assert not smart_case_contains("alpha beta", "gamma")
