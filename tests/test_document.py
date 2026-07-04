"""Tests for mokuji._document."""

from __future__ import annotations

import pytest

from mokuji._document import (
    Document,
    ExternalLink,
    Heading,
    InternalLink,
    UnsupportedLink,
    load_document,
    resolve_link,
)
from mokuji._errors import DocumentLoadError
from mokuji._files import MAX_FILE_SIZE, FileKind


def _write_md(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


class TestLoadDocument:
    def test_markdown_file_returns_markdown_document(self, tmp_path):
        path = _write_md(tmp_path, "doc.md", "# Title\n\nbody\n")
        document = load_document(path)
        assert document.kind is FileKind.MARKDOWN
        assert document.path == path
        assert document.text == "# Title\n\nbody\n"

    def test_text_file_has_no_headings(self, tmp_path):
        path = tmp_path / "script.py"
        path.write_text("# not a heading, a comment\n", encoding="utf-8")
        document = load_document(path)
        assert document.kind is FileKind.TEXT
        assert document.headings == ()

    def test_binary_file_returns_empty_text(self, tmp_path):
        path = tmp_path / "blob.bin"
        path.write_bytes(b"\x00\x01")
        document = load_document(path)
        assert document.kind is FileKind.BINARY
        assert document.text == ""
        assert document.headings == ()

    def test_large_file_without_allow_returns_too_large_placeholder(self, tmp_path):
        path = tmp_path / "huge.md"
        path.write_bytes(b"# a\n" + b"b" * MAX_FILE_SIZE)
        document = load_document(path)
        assert document.kind is FileKind.TOO_LARGE
        assert document.text == ""

    def test_large_file_with_allow_loads_content(self, tmp_path):
        path = tmp_path / "huge.md"
        path.write_bytes(b"# a\n" + b"b" * MAX_FILE_SIZE)
        document = load_document(path, allow_large=True)
        assert document.kind is FileKind.MARKDOWN
        assert document.text.startswith("# a\n")
        assert document.headings[0].text == "a"

    def test_missing_file_raises_chained_document_load_error(self, tmp_path):
        with pytest.raises(DocumentLoadError, match=r"missing\.md") as excinfo:
            load_document(tmp_path / "missing.md")
        assert isinstance(excinfo.value.__cause__, OSError)

    def test_invalid_utf8_markdown_falls_back_to_replacement(self, tmp_path):
        path = tmp_path / "bad.md"
        path.write_bytes(b"# ok\n\xff\xfe broken\n")
        document = load_document(path)
        assert document.kind is FileKind.MARKDOWN
        assert "�" in document.text

    def test_invalid_utf8_text_replaces_bytes(self, tmp_path):
        path = tmp_path / "bad.log"
        path.write_bytes(b"ok \xff end\n")
        document = load_document(path)
        assert document.kind is FileKind.TEXT
        assert "�" in document.text

    def test_read_failure_after_classify_raises_chained_error(
        self, tmp_path, monkeypatch
    ):
        path = _write_md(tmp_path, "gone.md", "# hi\n")

        def _fail(_self):
            raise PermissionError(13, "denied")

        monkeypatch.setattr(type(path), "read_bytes", _fail)
        with pytest.raises(DocumentLoadError, match=r"gone\.md") as excinfo:
            load_document(path)
        assert isinstance(excinfo.value.__cause__, OSError)

    def test_empty_markdown_file_has_no_headings(self, tmp_path):
        path = _write_md(tmp_path, "empty.md", "")
        document = load_document(path)
        assert document.text == ""
        assert document.headings == ()

    def test_document_is_immutable(self, tmp_path):
        document = load_document(_write_md(tmp_path, "a.md", "x\n"))
        with pytest.raises(AttributeError):
            document.text = "changed"  # type: ignore[misc]


class TestHeadingExtraction:
    def test_h1_to_h4_extracted_with_levels_and_lines(self, tmp_path):
        text = "# One\n\n## Two\n\n### Three\n\n#### Four\n"
        document = load_document(_write_md(tmp_path, "d.md", text))
        assert [(h.level, h.text, h.line) for h in document.headings] == [
            (1, "One", 0),
            (2, "Two", 2),
            (3, "Three", 4),
            (4, "Four", 6),
        ]

    def test_h5_and_h6_excluded(self, tmp_path):
        text = "##### five\n###### six\n# one\n"
        document = load_document(_write_md(tmp_path, "d.md", text))
        assert [h.text for h in document.headings] == ["one"]

    def test_heading_inside_fenced_code_block_ignored(self, tmp_path):
        text = "# real\n```\n# fake\n```\n~~~\n# also fake\n~~~\n## real too\n"
        document = load_document(_write_md(tmp_path, "d.md", text))
        assert [h.text for h in document.headings] == ["real", "real too"]

    def test_mismatched_fence_marker_does_not_close_block(self, tmp_path):
        text = "```\n~~~\n# still fenced\n```\n# real\n"
        document = load_document(_write_md(tmp_path, "d.md", text))
        assert [h.text for h in document.headings] == ["real"]

    def test_hash_without_space_is_not_a_heading(self, tmp_path):
        document = load_document(_write_md(tmp_path, "d.md", "#nope\n# yes\n"))
        assert [h.text for h in document.headings] == ["yes"]

    def test_trailing_closing_hashes_stripped(self, tmp_path):
        document = load_document(_write_md(tmp_path, "d.md", "## Usage ##\n"))
        assert document.headings[0].text == "Usage"

    def test_slug_is_github_style(self, tmp_path):
        document = load_document(_write_md(tmp_path, "d.md", "# Hello, World!\n"))
        assert document.headings[0].slug == "hello-world"

    def test_slug_strips_symbols_keeps_underscore_and_dash(self, tmp_path):
        document = load_document(_write_md(tmp_path, "d.md", "# a_b-c +d\n"))
        assert document.headings[0].slug == "a_b-c-d"

    def test_duplicate_slugs_get_numeric_suffixes(self, tmp_path):
        text = "# Setup\n## Setup\n### Setup\n"
        document = load_document(_write_md(tmp_path, "d.md", text))
        assert [h.slug for h in document.headings] == ["setup", "setup-1", "setup-2"]

    def test_heading_dataclass_is_frozen(self):
        heading = Heading(level=1, text="x", slug="x", line=0)
        with pytest.raises(AttributeError):
            heading.text = "y"  # type: ignore[misc]


class TestResolveLink:
    def test_bare_anchor_targets_same_file(self, tmp_path):
        base = tmp_path / "doc.md"
        target = resolve_link(base, "#install")
        assert target == InternalLink(path=base.resolve(), anchor="install")

    def test_empty_anchor_has_none_anchor(self, tmp_path):
        base = tmp_path / "doc.md"
        assert resolve_link(base, "#") == InternalLink(path=base.resolve(), anchor=None)

    def test_relative_path_resolves_against_base_parent(self, tmp_path):
        base = tmp_path / "docs" / "usage.md"
        target = resolve_link(base, "../README.md")
        assert target == InternalLink(
            path=(tmp_path / "README.md").resolve(), anchor=None
        )

    def test_relative_path_with_anchor_splits_fragment(self, tmp_path):
        base = tmp_path / "a.md"
        target = resolve_link(base, "b.md#usage")
        assert target == InternalLink(
            path=(tmp_path / "b.md").resolve(), anchor="usage"
        )

    def test_https_url_is_external(self, tmp_path):
        target = resolve_link(tmp_path / "a.md", "https://example.com/x")
        assert target == ExternalLink(url="https://example.com/x")

    def test_http_url_is_external(self, tmp_path):
        target = resolve_link(tmp_path / "a.md", "http://example.com")
        assert target == ExternalLink(url="http://example.com")

    def test_mailto_is_unsupported(self, tmp_path):
        target = resolve_link(tmp_path / "a.md", "mailto:x@example.com")
        assert target == UnsupportedLink(href="mailto:x@example.com")

    def test_ftp_is_unsupported(self, tmp_path):
        target = resolve_link(tmp_path / "a.md", "ftp://host/file")
        assert target == UnsupportedLink(href="ftp://host/file")

    def test_percent_encoded_path_is_decoded(self, tmp_path):
        base = tmp_path / "docs" / "a.md"
        target = resolve_link(base, "my%20file.md")
        assert target == InternalLink(
            path=(tmp_path / "docs" / "my file.md").resolve(), anchor=None
        )

    def test_percent_encoded_fragment_is_decoded(self, tmp_path):
        base = tmp_path / "a.md"
        target = resolve_link(base, "#caf%C3%A9")
        assert target == InternalLink(path=base.resolve(), anchor="café")

    def test_traversal_never_escapes_filesystem_root(self, tmp_path):
        base = tmp_path / "a.md"
        href = "../" * 100 + "etc/passwd"
        target = resolve_link(base, href)
        assert isinstance(target, InternalLink)
        assert ".." not in target.path.parts
        assert target.path.is_absolute()

    def test_document_types_are_value_objects(self, tmp_path):
        base = (tmp_path / "a.md").resolve()
        assert Document(
            path=base, text="", kind=FileKind.TEXT, headings=()
        ) == Document(path=base, text="", kind=FileKind.TEXT, headings=())
