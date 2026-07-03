"""Tests for mokuji._search."""

from __future__ import annotations

import pytest

from mokuji._search import Match, find_matches


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
