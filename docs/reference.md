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
| `e` | toggle FILES pane (focus moves into the tree) |
| `t` | toggle TOC pane |
| `Tab` | cycle focus tree ↔ content |
| `Enter` (tree) | open file / expand directory |
| `o` (tree) | open file in a new tab |
| `h` / `l` (tree) | collapse / expand directory |
| `.` (tree) | toggle non-Markdown files (hidden by default) |
| `Enter` (TOC) | jump to heading |
| `Esc` (tree) | return focus to content |

### Tabs & history

| Key | Action |
|-----|--------|
| `gt` / `gT` | next / previous tab |
| `1gt` … `9gt` | jump to tab N |
| `x` | close current tab |
| `Ctrl+o` / `Ctrl+i` | history back / forward (per tab) |

### Search

| Key | Action |
|-----|--------|
| `/` | open the search input |
| `Enter` | confirm query, jump to the first match |
| `n` / `N` | next / previous match (wraps with a flash) |
| `Esc` | cancel input / clear highlights |

Queries use smart case: all-lowercase matches case-insensitively; any
uppercase letter makes the search case-sensitive.

### Meta

| Key | Action |
|-----|--------|
| `?` | help modal (also closes it; `Esc` too) |
| `Ctrl+g` | toggle the footer key guide |
| `q` | quit |
