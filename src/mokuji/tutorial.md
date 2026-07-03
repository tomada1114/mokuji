<!--
  Bundled hands-on tutorial, opened from the last page of the welcome tour.
  Every key mentioned in backticks below is checked by the drift-guard test
  in tests/test_tour.py against the canonical key list in _ui/help.py —
  when a keybinding changes there, update this document too.
-->

# Hands-on tutorial

Welcome! This document *is* the exercise: every trick below can be
practised right here, on the text you are reading.

## Reading

Press `j` and `k` to scroll one line at a time. For bigger jumps, `d`
and `u` move half a page, and `f` and `b` move a full page.

Try `G` to jump to the very bottom of this document, then `gg` to come
straight back to the top.

## The table of contents

Press `t` to open the TOC pane — you will see the headings of this
tutorial as a tree. Move with `j` / `k`, then press `Enter` on any
heading to jump to it. Press `Esc` to return to the text, or `t` again
to close the pane.

## Browsing files

Press `e` to open the FILES pane and browse the directory you launched
mokuji in. `h` and `l` collapse and expand folders, and `Enter` opens
the file under the cursor in its own tab — this document stays open in
its tab. Press `.` to toggle non-Markdown files in and out of the
listing.

`Tab` switches between the tree and the content pane at any time.

## Tabs and history

Opened a second file from the tree? Cycle tabs with `gt` and `gT`, or
jump straight to a tab with a count like *2gt*. Close the current tab
with `x`.

Every jump — headings, links, files — is recorded per tab. Walk back
with `Ctrl+o` and forward with `Ctrl+i`, just like in Vim.

## Search

Press `/`, type the word **lantern**, and hit `Enter`. The match is
highlighted right in this paragraph: a paper lantern reads best in a
quiet, dark room — which is exactly the mood mokuji is going for.
Press `n` and `N` to hop between matches, and `Esc` to clear them.

## Links

Markdown links work too. This one jumps back to the
[Reading](#reading) section at the top — follow it, then press
`Ctrl+o` to return here.

## Where to go next

- `?` opens the full key reference; from there, `w` replays the
  welcome tour whenever you want a refresher.
- `Ctrl+g` hides or shows the key guide at the bottom of the screen.
- `r` reloads the current file after it changes on disk.
- `q` quits. That is all there is to it — enjoy the reading.
