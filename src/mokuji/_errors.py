"""Exception hierarchy for mokuji."""

from __future__ import annotations


class MokujiError(Exception):
    """Base for all mokuji errors."""


class DocumentLoadError(MokujiError):
    """A document could not be read from disk."""
