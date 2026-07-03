"""Pilot tests for the help modal, context footer, reload, and edge states."""

from __future__ import annotations

from mokuji._ui.app import MokujiApp
from mokuji._ui.footer import KeyGuide
from mokuji._ui.help import HelpScreen
from mokuji._ui.viewer import ViewerPane

LONG_DOCUMENT = "# Title\n\n" + "\n\n".join(f"paragraph {i}" for i in range(120)) + "\n"


def make_app(tmp_path, text=LONG_DOCUMENT):
    path = tmp_path / "README.md"
    path.write_text(text, encoding="utf-8")
    return MokujiApp(root=tmp_path, initial_file=path)


class TestHelpModal:
    async def test_question_mark_opens_help(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("question_mark")
            await pilot.pause()
            assert isinstance(app.screen, HelpScreen)

    async def test_escape_closes_help(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("question_mark")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert not isinstance(app.screen, HelpScreen)

    async def test_question_mark_closes_help_again(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("question_mark")
            await pilot.pause()
            await pilot.press("question_mark")
            await pilot.pause()
            assert not isinstance(app.screen, HelpScreen)

    async def test_help_notes_hidden_footer(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("ctrl+g")
            await pilot.press("question_mark")
            await pilot.pause()
            content = app.screen.query_one("#help-body")
            assert "footer hidden" in str(content.render())


class TestContextFooter:
    async def test_footer_hints_differ_between_tree_and_content(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            footer = app.query_one(KeyGuide)
            content_hints = str(footer.render())
            assert "j/k scroll" in content_hints
            await pilot.press("e", "e")
            await pilot.pause()
            tree_hints = str(footer.render())
            assert tree_hints != content_hints
            assert "Enter open" in tree_hints
            await pilot.press("escape")
            await pilot.pause()
            assert "j/k scroll" in str(footer.render())

    async def test_ctrl_g_toggles_footer_visibility(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            footer = app.query_one(KeyGuide)
            assert footer.display
            await pilot.press("ctrl+g")
            assert not footer.display
            await pilot.press("ctrl+g")
            assert footer.display


class TestReload:
    async def test_r_rereads_file_and_keeps_scroll(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await pilot.press("G")
            scrolled = viewer.scroll_y
            assert scrolled > 0
            (tmp_path / "README.md").write_text(
                LONG_DOCUMENT + "\n\nfresh paragraph\n", encoding="utf-8"
            )
            await pilot.press("r")
            await pilot.pause()
            await pilot.pause()
            assert viewer.document is not None
            assert "fresh paragraph" in viewer.document.text
            assert viewer.scroll_y == scrolled
            assert "reloaded" in str(app.query_one(KeyGuide).render())

    async def test_r_on_deleted_file_keeps_content_and_flashes(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            (tmp_path / "README.md").unlink()
            await pilot.press("r")
            await pilot.pause()
            assert viewer.document is not None
            assert "# Title" in viewer.document.text
            assert "file no longer exists" in str(app.query_one(KeyGuide).render())


class TestTinyTerminal:
    async def test_tiny_terminal_shows_placeholder(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(30, 8)) as pilot:
            await pilot.pause()
            placeholder = app.query_one("#too-small")
            assert placeholder.display
            assert "terminal too small" in str(placeholder.render())

    async def test_normal_terminal_hides_placeholder(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            assert not app.query_one("#too-small").display
