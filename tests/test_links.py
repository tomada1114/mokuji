"""Tests for Markdown link following and per-tab jump history."""

from __future__ import annotations

import webbrowser

from textual.widgets import Markdown

from mokuji._ui.app import MokujiApp
from mokuji._ui.footer import KeyGuide
from mokuji._ui.viewer import ViewerPane

README = (
    "# Title\n\n"
    "[usage](docs/usage.md)\n\n"
    "[missing](docs/missing.md)\n\n"
    "[ext](https://example.com/x)\n\n"
    "[mail](mailto:x@example.com)\n\n"
    "[anchor](#omega)\n\n"
    "[nowhere](#nope)\n\n"
    + "\n\n".join(f"filler {i}" for i in range(120))
    + "\n\n## Omega\n\nend\n"
)


def make_app(tmp_path):
    (tmp_path / "README.md").write_text(README, encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "usage.md").write_text("# Usage\n\nsome text\n", encoding="utf-8")
    return MokujiApp(root=tmp_path, initial_file=tmp_path / "README.md")


async def click_link(pilot, app, href):
    markdown = app.query_one(Markdown)
    markdown.post_message(Markdown.LinkClicked(markdown, href))
    await pilot.pause()
    await pilot.pause()


class TestInternalLinks:
    async def test_relative_link_opens_in_current_tab(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await click_link(pilot, app, "docs/usage.md")
            viewer = app.query_one(ViewerPane)
            assert viewer.document is not None
            assert viewer.document.path.name == "usage.md"
            assert app.tab_count == 1

    async def test_ctrl_o_goes_back_and_ctrl_i_forward(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await click_link(pilot, app, "docs/usage.md")
            viewer = app.query_one(ViewerPane)
            await pilot.press("ctrl+o")
            await pilot.pause()
            assert viewer.document.path.name == "README.md"
            await pilot.press("ctrl+i")
            await pilot.pause()
            assert viewer.document.path.name == "usage.md"

    async def test_back_at_history_start_is_a_no_op(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await pilot.press("ctrl+o")
            await pilot.pause()
            assert viewer.document.path.name == "README.md"

    async def test_broken_link_flashes_not_found_and_stays(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await click_link(pilot, app, "docs/missing.md")
            footer = app.query_one(KeyGuide)
            assert "not found" in str(footer.render())
            viewer = app.query_one(ViewerPane)
            assert viewer.document.path.name == "README.md"

    async def test_relative_link_outside_root_is_rejected(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        (project / "README.md").write_text(
            "# Title\n\n[outside](../outside.md)\n", encoding="utf-8"
        )
        (tmp_path / "outside.md").write_text("# Outside\n", encoding="utf-8")
        app = MokujiApp(root=project, initial_file=project / "README.md")
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await click_link(pilot, app, "../outside.md")
            footer = app.query_one(KeyGuide)
            assert "outside project" in str(footer.render())
            viewer = app.query_one(ViewerPane)
            assert viewer.document is not None
            assert viewer.document.path.name == "README.md"

    async def test_absolute_link_outside_root_is_rejected(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        (project / "README.md").write_text("# Title\n", encoding="utf-8")
        outside = tmp_path / "outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        app = MokujiApp(root=project, initial_file=project / "README.md")
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await click_link(pilot, app, str(outside))
            footer = app.query_one(KeyGuide)
            assert "outside project" in str(footer.render())
            viewer = app.query_one(ViewerPane)
            assert viewer.document is not None
            assert viewer.document.path.name == "README.md"


class TestAnchors:
    async def test_anchor_link_scrolls_within_document(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            assert viewer.scroll_y == 0
            await click_link(pilot, app, "#omega")
            await pilot.pause()
            assert viewer.scroll_y > 0

    async def test_unknown_anchor_flashes_anchor_not_found(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await click_link(pilot, app, "#nope")
            footer = app.query_one(KeyGuide)
            assert "anchor not found" in str(footer.render())


class TestExternalLinks:
    async def test_https_link_opens_browser_and_flashes(self, tmp_path, monkeypatch):
        opened = []

        def fake_open(url):
            opened.append(url)
            return True

        monkeypatch.setattr(webbrowser, "open", fake_open)
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await click_link(pilot, app, "https://example.com/x")
            assert opened == ["https://example.com/x"]
            footer = app.query_one(KeyGuide)
            assert "opened in browser" in str(footer.render())

    async def test_browser_failure_flashes_url(self, tmp_path, monkeypatch):
        def fail(url):
            raise OSError(1, "no browser")

        monkeypatch.setattr(webbrowser, "open", fail)
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await click_link(pilot, app, "https://example.com/x")
            footer = app.query_one(KeyGuide)
            assert "could not open browser" in str(footer.render())
            assert "example.com" in str(footer.render())

    async def test_mailto_link_flashes_unsupported(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await click_link(pilot, app, "mailto:x@example.com")
            footer = app.query_one(KeyGuide)
            assert "unsupported link" in str(footer.render())
