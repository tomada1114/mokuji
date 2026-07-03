# mokuji

[![CI](https://github.com/tomada1114/mokuji/actions/workflows/ci.yml/badge.svg)](https://github.com/tomada1114/mokuji/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/tomada1114/mokuji/branch/main/graph/badge.svg)](https://codecov.io/gh/tomada1114/mokuji)
[![PyPI](https://img.shields.io/pypi/v/mokuji)](https://pypi.org/project/mokuji/)
[![Python](https://img.shields.io/pypi/pyversions/mokuji)](https://pypi.org/project/mokuji/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

The most readable way to browse Markdown in your terminal.

**mokuji** (目次, "table of contents") is a terminal Markdown reader built
with [Textual](https://textual.textualize.io/). It is not an editor — it
does one thing: make reading a repository's documentation a first-class,
beautiful experience.

```bash
uvx mokuji            # browse the current repository
```

## Features

- **Repository as a book** — a file tree, tabs, internal-link following,
  per-tab jump history, and a table of contents turn a repo's Markdown
  into a navigable document set.
- **Always-visible key guide** — a context-aware footer shows the keys
  that work right now; `?` opens the full reference. Zero learning curve
  despite Vim keys.
- **Readability-first rendering** — a centered content column capped at
  96 cells, and one meticulously designed dark theme (`sumi`, derived
  from Tokyo Night).
- **In-file search** — `/` with smart case, `n`/`N` navigation, and match
  highlighting.
- Non-Markdown files are hidden from the tree by default (`.` shows
  them); they open read-only as plain text, and binary and oversized
  files are handled gracefully.

## Install

```bash
uv tool install mokuji    # or: pipx install mokuji / pip install mokuji
```

Or run it without installing:

```bash
uvx mokuji
```

## Usage

| Invocation | Behavior |
|------------|----------|
| `mokuji` | Browse the current working directory |
| `mokuji <dir>` | Browse `<dir>` |
| `mokuji <file.md>` | Browse the file's directory with the file open |
| `mokuji --version` | Print version and exit |
| `mokuji --help` | Print usage and exit |

## Keys

| Key | Context | Action |
|-----|---------|--------|
| `j` / `k` | content | scroll one line |
| `d` / `u` | content | half page down / up |
| `f` / `Space` / `b` | content | full page down / down / up |
| `gg` / `G` | content | top / bottom |
| `e` | global | toggle FILES pane |
| `t` | global | toggle TOC pane |
| `Tab` | global | cycle focus tree ↔ content |
| `Enter` | tree | open file / expand directory |
| `o` | tree | open file in a new tab |
| `.` | tree | toggle non-Markdown files (hidden by default) |
| `Enter` | TOC | jump to heading |
| `gt` / `gT` / `<N>gt` | global | next / previous / Nth tab |
| `x` | global | close tab |
| `Ctrl+o` / `Ctrl+i` | content | history back / forward |
| `/` | content | search in file |
| `n` / `N` | content | next / previous match (wraps) |
| `r` | content | reload file, keeping scroll position |
| `?` | global | help (also closes it; `Esc` too) |
| `Ctrl+g` | global | toggle the footer key guide |
| `q` | global | quit |

## Known Limitations

- **Search highlighting in Markdown**: rendered Markdown has no public
  API for inline highlights, so mokuji jumps to matches and shows a
  `match N/M · line L` counter in the footer instead. Plain-text files
  get full inline highlighting.
- **Link following is mouse-driven**: Textual's Markdown widget has no
  per-link keyboard focus, so links are followed by clicking them.
  Keyboard navigation covers everything else.
- **`Ctrl+i` aliases `Tab`** in terminals without an extended keyboard
  protocol; history-forward needs a terminal that distinguishes them
  (e.g. Kitty protocol support).
- Platforms: macOS and Linux; Windows Terminal is untested.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for full setup instructions.

```bash
just install   # dependencies + git hooks
just check     # format, lint, type check, tests
just smoke     # build the wheel and verify it in a temp venv
```

## Documentation

- [Getting Started](https://tomada1114.github.io/mokuji/getting-started/)
- [Reference](https://tomada1114.github.io/mokuji/reference/)

## License

[MIT](LICENSE)
