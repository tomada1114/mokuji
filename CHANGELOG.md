# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- FILES pane now hides non-Markdown files by default; press `.` in the
  tree to toggle between Markdown-only and all files (the footer flashes
  the new state, and the key guide/help list the key)

### Added

- Expanding a directory with nothing to show now displays a dim
  placeholder row: `(no markdown files)` when entries are filtered out,
  `(empty)` when the directory is truly empty

## [0.1.0] - 2026-07-02

### Added

- **mokuji**, a readability-first terminal Markdown reader built with
  Textual:
    - Markdown reading view with a centered 96-cell content column and
      the `sumi` dark theme (Tokyo Night derived)
    - FILES pane: repository tree with `.git` hidden, non-Markdown
      entries dimmed, plain-text/binary/oversized-file handling
    - TOC pane built from H1–H4 headings with jump-to-heading
    - Tabs with Vim semantics (`o`, `gt`/`gT`/`<N>gt`, `x`), duplicate
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
