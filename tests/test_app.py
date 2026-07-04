"""Pilot tests for the mokuji application shell."""

from __future__ import annotations

from textual.widgets import Markdown

from mokuji._ui.app import MokujiApp
from mokuji._ui.sidebar import FilesTree
from mokuji._ui.viewer import ViewerPane

LONG_DOCUMENT = "# Title\n\n" + "\n\n".join(f"paragraph {i}" for i in range(120)) + "\n"


def make_app(tmp_path, text=LONG_DOCUMENT, name="README.md"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return MokujiApp(root=tmp_path, initial_file=path)


class TestLaunch:
    async def test_initial_file_renders_markdown_widget(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            assert app.query_one(Markdown) is not None

    async def test_sumi_theme_is_active(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            assert app.theme == "sumi"

    async def test_viewer_records_open_document(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            assert viewer.document is not None
            assert viewer.document.path.name == "README.md"

    async def test_viewer_has_focus_on_launch(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            assert isinstance(app.focused, ViewerPane)

    async def test_files_tree_focused_with_cursor_when_launched_without_file(
        self, tmp_path
    ):
        (tmp_path / "README.md").write_text(LONG_DOCUMENT, encoding="utf-8")
        app = MokujiApp(root=tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            tree = app.query_one(FilesTree)
            assert app.focused is tree
            assert tree.cursor_line == 0


class TestScrolling:
    async def test_j_scrolls_down_and_k_scrolls_back_up(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            assert viewer.scroll_y == 0
            await pilot.press("j", "j", "j")
            assert viewer.scroll_y == 3
            await pilot.press("k")
            assert viewer.scroll_y == 2

    async def test_shift_g_jumps_to_bottom_and_gg_returns_to_top(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await pilot.press("G")
            assert viewer.scroll_y == viewer.max_scroll_y
            assert viewer.scroll_y > 0
            await pilot.press("g", "g")
            assert viewer.scroll_y == 0

    async def test_d_scrolls_half_page_and_u_scrolls_back(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await pilot.press("d")
            half = viewer.scroll_y
            assert 0 < half <= viewer.container_size.height
            await pilot.press("u")
            assert viewer.scroll_y == 0

    async def test_f_space_and_b_scroll_full_pages(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await pilot.press("f")
            one_page = viewer.scroll_y
            assert one_page > 0
            await pilot.press("space")
            assert viewer.scroll_y > one_page
            await pilot.press("b", "b")
            assert viewer.scroll_y == 0

    async def test_ctrl_d_and_ctrl_u_alias_half_page_scroll(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await pilot.press("ctrl+d")
            half = viewer.scroll_y
            assert 0 < half <= viewer.container_size.height
            await pilot.press("ctrl+u")
            assert viewer.scroll_y == 0

    async def test_ctrl_f_and_ctrl_b_alias_full_page_scroll(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await pilot.press("ctrl+f")
            one_page = viewer.scroll_y
            assert one_page > 0
            await pilot.press("ctrl+b")
            assert viewer.scroll_y == 0


class TestKeySequenceMachine:
    async def test_lone_g_then_j_still_scrolls(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await pilot.press("g", "j")
            assert viewer.scroll_y == 1

    async def test_escape_clears_pending_g(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await pilot.press("G")
            assert viewer.scroll_y > 0
            await pilot.press("g", "escape", "g")
            assert viewer.scroll_y > 0
            await pilot.press("g")
            assert viewer.scroll_y == 0


class TestTreeFocusRouting:
    def _make_tree_app(self, tmp_path):
        (tmp_path / "a.md").write_text(LONG_DOCUMENT, encoding="utf-8")
        (tmp_path / "b.md").write_text("# B\n", encoding="utf-8")
        (tmp_path / "c.md").write_text("# C\n", encoding="utf-8")
        return MokujiApp(root=tmp_path, initial_file=tmp_path / "a.md")

    async def test_gg_in_focused_tree_moves_cursor_not_viewer(self, tmp_path):
        app = self._make_tree_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await pilot.press("j", "j", "j")
            scroll_before = viewer.scroll_y
            assert scroll_before > 0
            tree = app.query_one(FilesTree)
            tree.focus()
            await pilot.pause()
            tree.cursor_line = 2
            await pilot.press("g", "g")
            await pilot.pause()
            assert tree.cursor_line == 0
            assert viewer.scroll_y == scroll_before

    async def test_shift_g_in_focused_tree_moves_cursor_to_last_node(self, tmp_path):
        app = self._make_tree_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            tree = app.query_one(FilesTree)
            tree.focus()
            await pilot.pause()
            await pilot.press("G")
            await pilot.pause()
            assert tree.cursor_line == tree.last_line


class TestQuit:
    async def test_q_exits_with_code_zero(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.press("q")
        assert app.return_code == 0
