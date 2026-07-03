"""Tests for mokuji._files."""

from __future__ import annotations

import pytest

from mokuji._errors import DocumentLoadError
from mokuji._files import (
    MARKDOWN_SUFFIXES,
    MAX_FILE_SIZE,
    FileKind,
    classify_file,
    is_markdown,
)


class TestIsMarkdown:
    @pytest.mark.parametrize(
        "name",
        [
            pytest.param("README.md", id="md"),
            pytest.param("notes.markdown", id="markdown"),
            pytest.param("UPPER.MD", id="uppercase-suffix"),
        ],
    )
    def test_markdown_suffixes_return_true(self, tmp_path, name):
        assert is_markdown(tmp_path / name)

    @pytest.mark.parametrize(
        "name",
        [
            pytest.param("script.py", id="python"),
            pytest.param("LICENSE", id="no-suffix"),
            pytest.param("archive.md.bak", id="md-not-last-suffix"),
        ],
    )
    def test_other_suffixes_return_false(self, tmp_path, name):
        assert not is_markdown(tmp_path / name)


class TestModuleConstants:
    def test_max_file_size_is_two_megabytes(self):
        assert MAX_FILE_SIZE == 2 * 1024 * 1024

    def test_markdown_suffixes_cover_md_and_markdown(self):
        assert frozenset({".md", ".markdown"}) == MARKDOWN_SUFFIXES


class TestClassifyFile:
    def test_markdown_file_returns_markdown(self, tmp_path):
        path = tmp_path / "doc.md"
        path.write_text("# hello\n", encoding="utf-8")
        assert classify_file(path) is FileKind.MARKDOWN

    def test_plain_text_file_returns_text(self, tmp_path):
        path = tmp_path / "config.toml"
        path.write_text("key = 'value'\n", encoding="utf-8")
        assert classify_file(path) is FileKind.TEXT

    def test_empty_markdown_file_returns_markdown(self, tmp_path):
        path = tmp_path / "empty.md"
        path.write_text("", encoding="utf-8")
        assert classify_file(path) is FileKind.MARKDOWN

    def test_nul_byte_in_head_returns_binary(self, tmp_path):
        path = tmp_path / "blob.bin"
        path.write_bytes(b"PK\x00\x03rest of archive")
        assert classify_file(path) is FileKind.BINARY

    def test_nul_byte_beyond_first_8kib_returns_text(self, tmp_path):
        path = tmp_path / "tail-nul.log"
        path.write_bytes(b"a" * 8192 + b"\x00")
        assert classify_file(path) is FileKind.TEXT

    def test_binary_markdown_suffix_returns_binary(self, tmp_path):
        path = tmp_path / "fake.md"
        path.write_bytes(b"\x00\x01\x02")
        assert classify_file(path) is FileKind.BINARY

    def test_file_at_size_limit_returns_text(self, tmp_path):
        path = tmp_path / "exact.txt"
        path.write_bytes(b"a" * MAX_FILE_SIZE)
        assert classify_file(path) is FileKind.TEXT

    def test_file_over_size_limit_returns_too_large(self, tmp_path):
        path = tmp_path / "huge.md"
        path.write_bytes(b"a" * (MAX_FILE_SIZE + 1))
        assert classify_file(path) is FileKind.TOO_LARGE

    def test_missing_file_raises_document_load_error(self, tmp_path):
        path = tmp_path / "missing.md"
        with pytest.raises(DocumentLoadError, match=r"missing\.md"):
            classify_file(path)

    def test_missing_file_error_chains_oserror(self, tmp_path):
        path = tmp_path / "missing.md"
        with pytest.raises(DocumentLoadError) as excinfo:
            classify_file(path)
        assert isinstance(excinfo.value.__cause__, OSError)
