"""Tests for mokuji._errors."""

from __future__ import annotations

import pytest

from mokuji._errors import DocumentLoadError, MokujiError


class TestErrorHierarchy:
    def test_mokuji_error_is_exception_subclass(self):
        assert issubclass(MokujiError, Exception)

    def test_document_load_error_is_mokuji_error_subclass(self):
        assert issubclass(DocumentLoadError, MokujiError)

    def test_document_load_error_raised_with_message_matches(self):
        message = "could not load: broken.md"
        with pytest.raises(DocumentLoadError, match=r"could not load: broken\.md"):
            raise DocumentLoadError(message)

    def test_document_load_error_caught_as_mokuji_error(self):
        message = "boom"
        with pytest.raises(MokujiError):
            raise DocumentLoadError(message)
