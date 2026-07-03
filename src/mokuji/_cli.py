"""Command-line entry point: argument parsing and app launch."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _package_version() -> str:
    try:
        return version("mokuji")
    except PackageNotFoundError:
        return "0.0.0+unknown"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mokuji",
        description="A readability-first terminal Markdown reader.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="directory to browse, or a file to open (default: current directory)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_package_version()}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the mokuji TUI.

    The Textual app is imported lazily so that ``--version`` and argument
    errors stay fast and TUI-free.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code (0 on normal quit, 1 for an invalid path).
    """
    args = _build_parser().parse_args(argv)
    target = Path(args.path)
    if not target.exists():
        sys.stderr.write(f"mokuji: path not found: {target}\n")
        return 1
    target = target.resolve()
    if target.is_dir():
        root, initial_file = target, None
    else:
        root, initial_file = target.parent, target

    # Lazy import: keeps --version and argument errors fast and TUI-free.
    from ._ui import app as app_module  # noqa: PLC0415

    tui = app_module.MokujiApp(root=root, initial_file=initial_file)
    tui.run()
    return tui.return_code or 0
