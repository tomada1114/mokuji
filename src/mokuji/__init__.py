"""Public package interface for mokuji."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .core import add

try:
    __version__ = version("mokuji")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = ["__version__", "add"]
