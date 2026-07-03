# Project Guide

## Overview

**mokuji** is a terminal (TUI) Markdown reader built with
[Textual](https://textual.textualize.io/), packaged with
[uv](https://docs.astral.sh/uv/) and [hatchling](https://hatch.pypa.io/).
It uses a strict `src/` layout with comprehensive type checking and
linting.

## Quick Reference

```bash
just install   # Install dependencies and git hooks when .git/ is present
just fmt       # Format code (ruff format + ruff check --fix)
just lint      # Lint (ruff check) + type check (mypy)
just test      # Run tests with coverage
just smoke     # Build and verify the wheel in a temp virtual environment
just check     # Run all checks: fmt → lint → test
just docs      # Serve docs locally
just build     # Build distribution packages
```

Without Just: replace `just <cmd>` with the corresponding `uv run` commands
in the `justfile`.

## Architecture

```
src/mokuji/
├── __init__.py    # Public API: __version__ + main only
├── __main__.py    # `python -m mokuji`
├── py.typed       # PEP 561 marker for typed package
├── _cli.py        # argparse; resolves root/initial file; runs MokujiApp
├── _errors.py     # MokujiError base + DocumentLoadError
├── _files.py      # pure: file classification (markdown/text/binary/too-large)
├── _document.py   # pure: Document model, heading extraction, link resolution
├── _search.py     # pure: smart-case substring search
├── _state.py      # pure: first-run marker under $XDG_STATE_HOME
├── _theme.py      # sumi color tokens + Textual Theme
├── tutorial.md    # bundled hands-on tutorial (opened from the tour)
└── _ui/
    ├── app.py        # MokujiApp: layout, bindings, event wiring
    ├── navigator.py  # tab states, per-tab history, Tabs widget sync
    ├── keys.py       # Vim multi-key sequence machine (gg/gt/gT/Ngt)
    ├── search.py     # search input, match state, n/N navigation
    ├── viewer.py     # ViewerPane: renders one document
    ├── sidebar.py    # FILES DirectoryTree + TOC Tree
    ├── footer.py     # KeyGuide: context hints + flash messages
    ├── help.py       # HelpScreen modal; canonical key list (single source)
    ├── tour.py       # TourScreen: first-run welcome carousel (help `w`)
    ├── style.py      # app-wide Textual CSS
    └── tabs.py       # TabState + pure tab arithmetic/label helpers
```

- Dependency rule: `_files`/`_document`/`_search`/`_errors`/`_state`
  import nothing from `_ui` and nothing from Textual; `_theme` may import
  `textual.theme.Theme` only; `_ui/*` may import everything; `_cli`
  imports `_ui.app` lazily inside `main()` (keeps `--version` fast)
- Keep the public API surface small — export via `__init__.py.__all__`
  (mokuji is an application: only `__version__` and `main` are public)
- Separate concerns: one module per logical unit, under 300 lines each
- Update `docs/reference.md` and README examples whenever you change the
  CLI or keybindings; the key sections in `_ui/help.py` are the single
  source the welcome tour reuses, but `_ui/tour.py` mock art and
  `tutorial.md` mention keys in prose — re-check both (the drift-guard
  test in `tests/test_tour.py` fails on stale key names)

## Review Checklist

Before submitting a PR:

1. `just check` passes (format, lint, type check, tests)
2. New public APIs have type annotations and docstrings
3. Tests cover the new functionality
4. No unnecessary dependencies added

## Important Reminders

- All code, docs, commits, and PRs must be written in English
- Do what has been asked; nothing more, nothing less
- NEVER create files unless absolutely necessary
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files unless explicitly requested
- Dependencies should always be added to the appropriate group in pyproject.toml
