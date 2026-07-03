# Getting Started

## Installation

```bash
uv tool install mokuji
```

Or with pipx / pip:

```bash
pipx install mokuji
pip install mokuji
```

To try it once without installing:

```bash
uvx mokuji
```

## Basic Usage

Run mokuji in a repository:

```bash
cd your-project
mokuji
```

The FILES pane on the left lists the Markdown files under the current
directory (press `.` to show everything else too). Move with `j`/`k`,
open a document with `Enter`, or open it in a new tab with `o`. Markdown
files render with headings, code blocks, and tables; any other text file
opens read-only as plain text.

A few keys to get productive:

- `t` shows the table of contents of the open document; `Enter` jumps to
  a heading.
- `/` searches within the file (smart case); `n`/`N` step through
  matches.
- `gt`/`gT` switch tabs, `x` closes one.
- Click a relative Markdown link to follow it; `Ctrl+o` goes back.
- `?` opens the complete key reference at any time.

!!! tip
    The footer always shows the keys that work in the focused pane,
    wrapping onto up to three lines when the terminal is narrow. If you
    hide it with `Ctrl+g`, the help modal reminds you how to bring it
    back.

## What's Next?

See the [Reference](reference.md) for the CLI options and the full
keybinding table.
