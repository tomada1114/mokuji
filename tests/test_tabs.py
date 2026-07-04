"""Tests for tab state helpers and the tab bar lifecycle."""

from __future__ import annotations

from pathlib import Path

from textual.widgets import Tab, Tabs

from mokuji._ui.app import MokujiApp
from mokuji._ui.sidebar import FilesTree, Sidebar
from mokuji._ui.tabs import next_tab_index, prev_tab_index, tab_labels
from mokuji._ui.viewer import ViewerPane

LONG_DOCUMENT = "# Title\n\n" + "\n\n".join(f"paragraph {i}" for i in range(120)) + "\n"


def make_app(tmp_path):
    (tmp_path / "README.md").write_text(LONG_DOCUMENT, encoding="utf-8")
    (tmp_path / "script.py").write_text("print('hi')\n", encoding="utf-8")
    return MokujiApp(root=tmp_path, initial_file=tmp_path / "README.md")


async def open_from_tree(pilot, app, name):
    tree = app.query_one(FilesTree)
    tree.focus()
    await pilot.pause()
    if not tree.show_all:
        await pilot.press("full_stop")
        await pilot.pause()
    for node in tree.root.children:
        if node.data is not None and node.data.path.name == name:
            tree.cursor_line = node.line
            await pilot.press("enter")
            await pilot.pause()
            return
    message = f"no tree entry called {name}"
    raise AssertionError(message)


class TestTabHelpers:
    def test_unique_names_use_bare_file_names(self):
        labels = tab_labels([Path("/a/README.md"), Path("/a/usage.md")])
        assert labels == ["README.md", "usage.md"]

    def test_duplicate_names_get_parent_directory_suffix(self):
        labels = tab_labels([Path("/a/docs/usage.md"), Path("/a/other/usage.md")])
        assert labels == ["usage.md (docs)", "usage.md (other)"]

    def test_next_tab_wraps_around(self):
        assert next_tab_index(1, None, 2) == 0

    def test_next_tab_with_count_is_one_based(self):
        assert next_tab_index(0, 2, 3) == 1

    def test_next_tab_with_out_of_range_count_keeps_active(self):
        assert next_tab_index(0, 9, 2) == 0

    def test_prev_tab_wraps_around(self):
        assert prev_tab_index(0, 3) == 2


class TestTabLifecycle:
    async def test_tab_bar_hidden_with_single_tab(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            assert app.tab_count == 1
            assert not app.query_one(Tabs).display

    async def test_enter_in_tree_opens_second_tab_and_shows_bar(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await open_from_tree(pilot, app, "script.py")
            assert app.tab_count == 2

    async def test_tab_bar_stays_out_of_the_focus_cycle(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await open_from_tree(pilot, app, "script.py")
            assert app.query_one(Tabs).display
            app.query_one(ViewerPane).focus()
            await pilot.press("tab")
            assert isinstance(app.focused, FilesTree)
            await pilot.press("tab")
            assert isinstance(app.focused, ViewerPane)
            assert app.active_tab_index == 1
            viewer = app.query_one(ViewerPane)
            assert viewer.document is not None
            assert viewer.document.path.name == "script.py"
            assert app.query_one(Tabs).display

    async def test_gt_cycles_forward_and_shift_gt_backwards(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await open_from_tree(pilot, app, "script.py")
            app.query_one(ViewerPane).focus()
            await pilot.press("g", "t")
            await pilot.pause()
            assert app.active_tab_index == 0
            await pilot.press("g", "T")
            await pilot.pause()
            assert app.active_tab_index == 1

    async def test_numbered_gt_jumps_to_nth_tab(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await open_from_tree(pilot, app, "script.py")
            app.query_one(ViewerPane).focus()
            await pilot.press("1", "g", "t")
            await pilot.pause()
            assert app.active_tab_index == 0
            await pilot.press("2", "g", "t")
            await pilot.pause()
            assert app.active_tab_index == 1

    async def test_x_closes_current_tab_and_hides_bar(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await open_from_tree(pilot, app, "script.py")
            app.query_one(ViewerPane).focus()
            await pilot.press("x")
            await pilot.pause()
            assert app.tab_count == 1
            viewer = app.query_one(ViewerPane)
            assert viewer.document is not None
            assert viewer.document.path.name == "README.md"
            assert not app.query_one(Tabs).display

    async def test_closing_last_tab_shows_empty_state(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            app.query_one(ViewerPane).focus()
            await pilot.press("x")
            await pilot.pause()
            assert app.tab_count == 0
            viewer = app.query_one(ViewerPane)
            assert viewer.document is None
            notice = app.query_one(".empty-state")
            assert "e browse files" in str(notice.render())
            assert app.is_running

    async def test_closing_last_tab_focuses_files_tree(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            app.query_one(ViewerPane).focus()
            await pilot.press("x")
            await pilot.pause()
            assert app.query_one(Sidebar).display
            assert isinstance(app.focused, FilesTree)

    async def test_closing_last_tab_shows_sidebar_when_hidden(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("e", "e")  # focus the (visible) tree, then hide it
            await pilot.pause()
            assert not app.query_one(Sidebar).display
            app.query_one(ViewerPane).focus()
            await pilot.press("x")
            await pilot.pause()
            assert app.query_one(Sidebar).display
            assert isinstance(app.focused, FilesTree)

    async def test_reopening_open_file_focuses_existing_tab(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await open_from_tree(pilot, app, "script.py")
            assert app.active_tab_index == 1
            await open_from_tree(pilot, app, "README.md")
            assert app.tab_count == 2
            assert app.active_tab_index == 0

    async def test_scroll_position_preserved_per_tab(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await pilot.press("G")
            bottom = viewer.scroll_y
            assert bottom > 0
            await open_from_tree(pilot, app, "script.py")
            assert viewer.scroll_y == 0
            app.query_one(ViewerPane).focus()
            await pilot.press("g", "t")
            await pilot.pause()
            assert app.active_tab_index == 0
            assert viewer.scroll_y == bottom

    async def test_duplicate_tab_names_show_parent_directory(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "usage.md").write_text("# a\n", encoding="utf-8")
        (tmp_path / "other").mkdir()
        (tmp_path / "other" / "usage.md").write_text("# b\n", encoding="utf-8")
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await app.open_in_new_tab(tmp_path / "docs" / "usage.md")
            await app.open_in_new_tab(tmp_path / "other" / "usage.md")
            await pilot.pause()
            labels = [str(tab.label) for tab in app.query(Tab)]
            assert "usage.md (docs)" in labels
            assert "usage.md (other)" in labels
