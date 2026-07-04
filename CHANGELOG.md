# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Expanding a directory with nothing to show now displays a dim
  placeholder row: `(no markdown files)` when entries are filtered out,
  `(empty)` when the directory is truly empty
- A five-page welcome tour on first launch, ending in a bundled
  hands-on tutorial document; replay it any time with `?` then `w`
- Repo-wide search (`S`): a modal that searches every Markdown file in
  the project, groups hits by file, and on `Enter` opens the selected
  hit at its line, seeding the in-file search with the same query
- Type-to-filter (`/`) in the FILES/TOC trees: narrows the tree to
  substring matches (smart case), keeping matched files' ancestor
  directories visible; `Esc` restores the full tree
- `Ctrl+d`/`Ctrl+u`/`Ctrl+f`/`Ctrl+b` as scroll aliases for `d`/`u`/`f`/`b`

### Changed

- FILES pane now hides non-Markdown files by default; press `.` in the
  tree to toggle between Markdown-only and all files (the footer flashes
  the new state, and the key guide/help list the key)
- FILES pane also hides dotfiles and common build/tooling directories
  by default (`node_modules`, `__pycache__`, `dist`, `build`, `target`,
  `.tox`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache`); `.` still
  reveals everything except `.git`
- Key guide and help modal redesigned for discoverability: a
  context-aware footer shows the keys that work right now, wraps
  sensibly on narrow terminals, and `?` opens a fuller reference
  covering the whole app
- Launch focus and the FILES tree cursor now land where expected, and
  tree files always open in a new tab rather than replacing the
  current one
- `e`/`t` are now focus-or-toggle instead of a plain toggle: a
  visible-but-unfocused pane is focused first, and only a second press
  hides it; `Esc` in a narrow-terminal overlay also dismisses it
- Tab labels are now prefixed with their 1-based index (e.g.
  `1 README.md`), matching the digit typed for `<N>gt`
- Following a Markdown link now always navigates within the current
  tab, even when the target is already open in another tab, so
  `Ctrl+o` returns to where you were reading instead of another tab's
  history
- In-file search state is now per-tab: switching tabs no longer
  silently clears an active search, and returning to a tab restores it
- The in-file search footer status now shows the matched line's text
  with the query span accented, instead of just a bare match counter
- `gg`/`G` now route to the focused FILES/TOC tree (cursor to first/
  last node) instead of always scrolling the (possibly hidden) viewer
- Closing the last tab now moves focus to the FILES tree, showing it
  if it was hidden

### Fixed

- Links with percent-escaped characters (e.g. `my%20file.md`) now
  resolve correctly, and percent-encoded heading anchors match too
- Heading slugs are now Unicode-aware, matching GitHub's anchor
  generation for non-ASCII headings (previously non-ASCII headings
  collapsed to an empty or colliding slug)
- Internal links are now confined to the project root; a link that
  resolves outside it is rejected with a flash instead of opening
  arbitrary files on disk
- Opening a file classified as too-large no longer crashes if the
  underlying path disappears before it renders; it shows a placeholder
  instead
- The TOC pane shows a dedicated placeholder when no file is open,
  instead of leaving the pane in an inconsistent state

## [0.1.0] - 2026-07-02

### Added

- **mokuji**, a readability-first terminal Markdown reader built with
  Textual:
    - Markdown reading view with a centered 96-cell content column and
      the `sumi` dark theme (Tokyo Night derived)
    - FILES pane: repository tree with `.git` hidden, non-Markdown
      entries dimmed, plain-text/binary/oversized-file handling
    - TOC pane built from H1–H4 headings with jump-to-heading
    - Tabs with Vim semantics (`Enter`, `gt`/`gT`/`<N>gt`, `x`), duplicate
      detection, and per-tab scroll positions
    - Internal/external link following with per-tab jump history
      (`Ctrl+o`/`Ctrl+i`)
    - In-file smart-case search (`/`, `n`/`N`) with inline highlights for
      plain text and a match counter for Markdown
    - Context-aware footer key guide (`Ctrl+g` toggles), footer flash
      feedback, help modal (`?`), manual reload (`r`), and
      narrow/tiny-terminal handling
    - `mokuji` CLI: directory or file argument, `--version`, exit code 1
      with a stderr message for invalid paths
- Initial project structure
- `scripts/bootstrap.py` deterministic template initializer: renames the
  package and replaces every placeholder (`mokuji`, `mokuji`,
  `tomada1114`, `tomada`, `tmasuyama1114@gmail.com`) across tracked files
- Python 3.14 support in the CI test matrix and trove classifiers
- `zizmor` security lint for GitHub Actions workflows, wired into both CI
  and pre-commit
- `actions/dependency-review-action` on pull requests
- Weekly `pip-audit` dependency vulnerability scan
- Weekly OpenSSF Scorecard analysis
- PR auto-labeling by Conventional Commit type, so the release changelog
  categories actually populate
- `.devcontainer/devcontainer.json` for a ready-to-use dev environment
- `.github/ISSUE_TEMPLATE/config.yml` disabling blank issues and linking
  security reports to GitHub Security Advisories
- Dependabot cooldown and `tool.uv.exclude-newer` supply-chain cutoff,
  documented in `.claude/rules/pyproject.md`

### Changed

- Moved coverage enforcement (`--cov-fail-under=80`) out of pytest
  `addopts` and into `just test` / CI, so a single test can be run in
  isolation without failing the coverage gate
- Restructured the release pipeline: a dedicated `build` job now builds
  and attests provenance once; `publish` and the GitHub Release both
  consume that artifact instead of rebuilding
- Scoped all workflow permissions to job level, added `timeout-minutes`
  to every job, added `--locked` to every `uv sync` in CI, and disabled
  checkout credential persistence outside the docs deploy job
- Simplified `src/mokuji/__init__.py`'s version resolution to the
  standard `importlib.metadata.version()` pattern, dropping the ~50-line
  local-pyproject-walking fallback chain
- Replaced the bespoke `no-commit-to-main` pre-commit hook with the
  pre-commit-hooks builtin `no-commit-to-branch`
- Unified mypy targets (`src scripts tests`) across justfile, CI,
  release, and pre-commit
- Expanded ruff rule set (`D`, `PT`, `N`, `TRY`, `EM`, `DTZ`, `RSE`,
  `PGH`) to match `.claude/rules/python.md`; renamed `TCH` -> `TC`

### Fixed

- Switched to PEP 639 license metadata (`license-files`, dropped the
  redundant OSI trove classifier)

[Unreleased]: https://github.com/tomada1114/mokuji/compare/v0.1.0...main
[0.1.0]: https://github.com/tomada1114/mokuji/commits/main
