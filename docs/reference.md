# Reference

mokuji is an application, not a library: its public Python surface is the
`mokuji` command. This page documents the CLI and every keybinding.

## Command line

| Invocation | Behavior |
|------------|----------|
| `mokuji` | Browse the current working directory |
| `mokuji <dir>` | Browse `<dir>` |
| `mokuji <file.md>` | Browse the file's directory with the file open in a tab |
| `mokuji --version` | Print version and exit |
| `mokuji --help` | Print usage and exit |

`python -m mokuji` behaves identically.

On launch the FILES tree has focus, ready to pick a file with `j`/`k`
and `Enter`; when a file is given, the content pane has focus instead.

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Normal quit |
| `1` | Invalid path (`mokuji: path not found: <path>` on stderr) |

## Keybindings

### Reading

| Key | Action |
|-----|--------|
| `j` / `k` | scroll one line |
| `d` / `u` | half page down / up |
| `f` / `Space` / `b` | full page down / down / up |
| `gg` / `G` | top / bottom |
| `r` | reload file, keeping scroll position |

### Navigation

| Key | Action |
|-----|--------|
| `e` | focus the FILES pane, opening it if hidden; press again to hide |
| `t` | focus the TOC pane, opening it if hidden; press again to hide |
| `Tab` | cycle focus tree ↔ content |
| `Enter` (tree) | open file in a new tab (focus moves to content) / expand directory |
| `h` / `l` (tree) | collapse / expand directory |
| `.` (tree) | toggle non-Markdown files (hidden by default) |
| `/` (tree) | filter the tree by name (substring, smart case) |
| `Enter` (TOC) | jump to heading |
| `Esc` (tree) | return focus to content |

`e`/`t` are focus-or-toggle: a visible-but-unfocused pane gets focused
first, and only hides on a second press while it already has focus.

### Tabs & history

| Key | Action |
|-----|--------|
| `gt` / `gT` | next / previous tab |
| `1gt` … `9gt` | jump to tab N |
| `x` | close current tab |
| `Ctrl+o` / `Ctrl+i` | history back / forward (per tab) |

Tab labels are prefixed with their 1-based index (`1 README.md`),
matching the digit typed for `<N>gt`; duplicate names still get a
parent-directory suffix.

### Search

| Key | Action |
|-----|--------|
| `/` | open the search input |
| `Enter` | confirm query, jump to the first match |
| `n` / `N` | next / previous match (wraps with a flash) |
| `Esc` | cancel input / clear highlights |
| `S` | search every Markdown file in the project |

Queries use smart case: all-lowercase matches case-insensitively; any
uppercase letter makes the search case-sensitive.

Markdown has no public API for inline highlights, so an in-file match
shows as a footer status (`match N/M · line L · <excerpt>`) with the
matched line's text and the query span accented, instead of an inline
highlight. Plain-text files still get full inline highlighting.

`S` opens a modal listing every match across the project, grouped by
file, capped at 200 hits (20 per file). `Up`/`Down` move the
selection, `Enter` opens the selected hit at its line and seeds the
in-file search with the same query, and `Esc` closes the modal with
no change. It scans every Markdown file under the project root except
`.git` — unlike the FILES tree, it ignores the tree's own display
filter (dotfiles, build-noise directories).

### Meta

| Key | Action |
|-----|--------|
| `?` | help modal (also closes it; `Esc` too) |
| `Ctrl+g` | toggle the footer key guide |
| `q` | quit |

## Welcome tour

On the very first launch mokuji opens a five-page welcome tour. It is
shown once: a marker file under `$XDG_STATE_HOME/mokuji/` (default
`~/.local/state/mokuji/`) records that it has been seen. To replay it at
any time, press `?` and then `w`.

| Key (in the tour) | Action |
|-------------------|--------|
| `l` / `→` | next page |
| `h` / `←` | previous page |
| `Enter` | next page; on the last page, open the hands-on tutorial |
| `Esc` / `q` | close the tour |

The last page offers to open a bundled tutorial document — a short
Markdown file designed so every key it teaches can be practised on the
document itself.
