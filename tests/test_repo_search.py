"""Tests for mokuji._repo_search: the pure repo-wide search walker."""

from __future__ import annotations

from pathlib import Path

from mokuji._repo_search import (
    MAX_HITS_PER_FILE,
    MAX_TOTAL_HITS,
    search_repo,
)


def _write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class TestSearchRepo:
    def test_finds_matches_across_multiple_files_with_correct_lines(self, tmp_path):
        _write(tmp_path, "a.md", "line one\nneedle here\n")
        _write(tmp_path, "docs/b.md", "top\nneedle again\nbottom\n")
        results = search_repo(tmp_path, "needle")
        by_path = {hit.path: hit for hit in results.hits}
        assert by_path[Path("a.md")].line == 1
        assert by_path[Path("docs/b.md")].line == 1
        assert results.match_count == 2
        assert results.file_count == 2
        assert not results.truncated

    def test_hit_path_is_relative_to_root(self, tmp_path):
        _write(tmp_path, "docs/guide.md", "needle\n")
        results = search_repo(tmp_path, "needle")
        assert results.hits[0].path == Path("docs/guide.md")
        assert not results.hits[0].path.is_absolute()

    def test_excerpt_includes_accented_span_offsets(self, tmp_path):
        _write(tmp_path, "a.md", "some needle text\n")
        results = search_repo(tmp_path, "needle")
        hit = results.hits[0]
        assert hit.text[hit.span_start : hit.span_end] == "needle"

    def test_no_matches_returns_empty_results(self, tmp_path):
        _write(tmp_path, "a.md", "nothing to find\n")
        results = search_repo(tmp_path, "zzzq")
        assert results.hits == ()
        assert results.match_count == 0
        assert results.file_count == 0
        assert not results.truncated

    def test_smart_case_lowercase_query_is_case_insensitive(self, tmp_path):
        _write(tmp_path, "a.md", "Needle\nneedle\nNEEDLE\n")
        results = search_repo(tmp_path, "needle")
        assert results.match_count == 3

    def test_smart_case_uppercase_query_is_case_sensitive(self, tmp_path):
        _write(tmp_path, "a.md", "Needle\nneedle\n")
        results = search_repo(tmp_path, "Needle")
        assert results.match_count == 1

    def test_non_markdown_files_are_skipped(self, tmp_path):
        _write(tmp_path, "script.py", "needle\n")
        results = search_repo(tmp_path, "needle")
        assert results.hits == ()

    def test_git_directory_is_never_searched(self, tmp_path):
        _write(tmp_path, ".git/COMMIT_EDITMSG.md", "needle\n")
        results = search_repo(tmp_path, "needle")
        assert results.hits == ()

    def test_binary_file_with_markdown_suffix_is_skipped(self, tmp_path):
        path = tmp_path / "fake.md"
        path.write_bytes(b"\x00\x01needle\x02")
        results = search_repo(tmp_path, "needle")
        assert results.hits == ()

    def test_dotfiles_and_ignore_set_dirs_are_still_searched(self, tmp_path):
        """Repo search ignores the tree's display filter (decisions.md)."""
        _write(tmp_path, ".github/notes.md", "needle\n")
        _write(tmp_path, "node_modules/pkg/readme.md", "needle\n")
        results = search_repo(tmp_path, "needle")
        assert results.file_count == 2

    def test_per_file_hits_are_capped(self, tmp_path):
        text = "\n".join("needle" for _ in range(MAX_HITS_PER_FILE + 10)) + "\n"
        _write(tmp_path, "a.md", text)
        results = search_repo(tmp_path, "needle")
        file_hits = [hit for hit in results.hits if hit.path == Path("a.md")]
        assert len(file_hits) == MAX_HITS_PER_FILE
        assert results.match_count == MAX_HITS_PER_FILE + 10
        assert results.truncated

    def test_total_hits_are_capped(self, tmp_path):
        per_file = MAX_HITS_PER_FILE
        needed_files = MAX_TOTAL_HITS // per_file + 2
        text = "\n".join("needle" for _ in range(per_file)) + "\n"
        for index in range(needed_files):
            _write(tmp_path, f"f{index}.md", text)
        results = search_repo(tmp_path, "needle")
        assert len(results.hits) == MAX_TOTAL_HITS
        assert results.truncated

    def test_empty_query_returns_empty_results(self, tmp_path):
        _write(tmp_path, "a.md", "some text\n")
        results = search_repo(tmp_path, "")
        assert results.hits == ()
        assert results.match_count == 0
