"""Pilot tests for the FILES/TOC sidebar."""

from __future__ import annotations

from textual.widgets import Markdown

from mokuji._ui.app import MokujiApp
from mokuji._ui.footer import KeyGuide
from mokuji._ui.sidebar import FilesTree, Sidebar, SidebarMode, TocTree
from mokuji._ui.viewer import ViewerPane

DOCUMENT = (
    "# Alpha\n\n" + "\n\n".join(f"line {i}" for i in range(80)) + "\n\n## Omega\n"
)


def make_workspace(tmp_path):
    (tmp_path / "README.md").write_text(DOCUMENT, encoding="utf-8")
    (tmp_path / "script.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01\x02")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x\n", encoding="utf-8")
    return tmp_path


def make_app(tmp_path):
    make_workspace(tmp_path)
    return MokujiApp(root=tmp_path, initial_file=tmp_path / "README.md")


async def open_from_tree(pilot, app, name):
    """Focus the FILES tree and select the entry called *name*."""
    tree = app.query_one(FilesTree)
    tree.focus()
    await pilot.pause()
    for node in tree.root.children:
        if node.data is not None and node.data.path.name == name:
            tree.cursor_line = node.line
            await pilot.press("enter")
            await pilot.pause()
            return
    message = f"no tree entry called {name}"
    raise AssertionError(message)


class TestPaneToggle:
    async def test_sidebar_opens_in_files_mode_by_default(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            sidebar = app.query_one(Sidebar)
            assert sidebar.display
            assert sidebar.mode is SidebarMode.FILES

    async def test_e_closes_then_reopens_with_tree_focused(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            sidebar = app.query_one(Sidebar)
            await pilot.press("e")
            assert not sidebar.display
            await pilot.press("e")
            assert sidebar.display
            assert isinstance(app.focused, FilesTree)

    async def test_t_switches_pane_to_toc_mode(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            sidebar = app.query_one(Sidebar)
            await pilot.press("t")
            assert sidebar.display
            assert sidebar.mode is SidebarMode.TOC
            await pilot.press("t")
            assert not sidebar.display

    async def test_escape_in_tree_returns_focus_to_viewer(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("e", "e")
            assert isinstance(app.focused, FilesTree)
            await pilot.press("escape")
            assert isinstance(app.focused, ViewerPane)

    async def test_tab_cycles_focus_between_tree_and_viewer(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            assert isinstance(app.focused, ViewerPane)
            await pilot.press("tab")
            assert isinstance(app.focused, FilesTree)
            await pilot.press("tab")
            assert isinstance(app.focused, ViewerPane)


class TestOpeningFiles:
    async def test_markdown_file_renders_markdown(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await open_from_tree(pilot, app, "README.md")
            assert app.query_one(Markdown) is not None

    async def test_python_file_opens_as_plain_text(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await open_from_tree(pilot, app, "script.py")
            viewer = app.query_one(ViewerPane)
            assert viewer.document is not None
            assert viewer.document.path.name == "script.py"
            assert not app.query(Markdown)
            plain = app.query_one(".plain-text")
            assert "print" in str(plain.render())

    async def test_binary_file_shows_notice(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await open_from_tree(pilot, app, "blob.bin")
            notice = app.query_one(".notice")
            assert "binary file" in str(notice.render())

    async def test_git_directory_is_hidden_from_tree(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            tree = app.query_one(FilesTree)
            names = [
                node.data.path.name
                for node in tree.root.children
                if node.data is not None
            ]
            assert ".git" not in names
            assert "README.md" in names

    async def test_large_file_requires_enter_confirmation(self, tmp_path):
        make_workspace(tmp_path)
        big = tmp_path / "big.md"
        big.write_text("# Big\n" + "x" * (2 * 1024 * 1024), encoding="utf-8")
        app = MokujiApp(root=tmp_path, initial_file=tmp_path / "README.md")
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await open_from_tree(pilot, app, "big.md")
            notice = app.query_one(".notice")
            assert "press Enter to load" in str(notice.render())
            app.query_one(ViewerPane).focus()
            await pilot.press("enter")
            await pilot.pause()
            assert app.query_one(Markdown) is not None

    async def test_unreadable_file_flashes_permission_denied(self, tmp_path):
        make_workspace(tmp_path)
        secret = tmp_path / "secret.md"
        secret.write_text("# hidden\n", encoding="utf-8")
        secret.chmod(0)
        app = MokujiApp(root=tmp_path, initial_file=tmp_path / "README.md")
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await open_from_tree(pilot, app, "secret.md")
            footer = app.query_one(KeyGuide)
            assert "permission denied" in str(footer.render())
        secret.chmod(0o644)


class TestToc:
    async def test_toc_lists_headings_of_open_document(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("t")
            await pilot.pause()
            toc = app.query_one(TocTree)
            labels = [str(node.label).strip() for node in toc.root.children]
            assert labels == ["Alpha", "Omega"]

    async def test_toc_enter_jumps_to_heading_and_focuses_viewer(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            assert viewer.scroll_y == 0
            await pilot.press("t")
            await pilot.pause()
            toc = app.query_one(TocTree)
            toc.cursor_line = toc.root.children[-1].line
            await pilot.press("enter")
            await pilot.pause()
            assert viewer.scroll_y > 0
            assert isinstance(app.focused, ViewerPane)

    async def test_toc_for_plain_text_file_shows_placeholder(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await open_from_tree(pilot, app, "script.py")
            await pilot.press("t")
            await pilot.pause()
            toc = app.query_one(TocTree)
            labels = [str(node.label) for node in toc.root.children]
            assert labels == ["(not a Markdown file)"]

    async def test_toc_without_headings_shows_placeholder(self, tmp_path):
        make_workspace(tmp_path)
        bare = tmp_path / "bare.md"
        bare.write_text("just text, no headings\n", encoding="utf-8")
        app = MokujiApp(root=tmp_path, initial_file=bare)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("t")
            await pilot.pause()
            toc = app.query_one(TocTree)
            labels = [str(node.label) for node in toc.root.children]
            assert labels == ["(no headings)"]


class TestNarrowTerminal:
    async def test_sidebar_auto_collapses_below_80_columns(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(70, 20)) as pilot:
            await pilot.pause()
            assert not app.query_one(Sidebar).display

    async def test_e_opens_sidebar_as_overlay_when_narrow(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(70, 20)) as pilot:
            await pilot.pause()
            await pilot.press("e")
            sidebar = app.query_one(Sidebar)
            assert sidebar.display
            assert sidebar.has_class("-overlay")
