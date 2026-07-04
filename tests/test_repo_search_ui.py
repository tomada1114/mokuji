"""Pilot tests for the repo-wide search modal (the capital ``S`` key)."""

from __future__ import annotations

from mokuji._ui.app import MokujiApp
from mokuji._ui.footer import KeyGuide
from mokuji._ui.repo_search import RepoSearchScreen
from mokuji._ui.sidebar import FilesTree
from mokuji._ui.viewer import ViewerPane


def make_app(tmp_path):
    (tmp_path / "README.md").write_text(
        "# Title\n\nnothing special\n", encoding="utf-8"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text(
        "# Guide\n\nasync def do_work():\n    pass\n", encoding="utf-8"
    )
    return MokujiApp(root=tmp_path, initial_file=tmp_path / "README.md")


async def type_query(pilot, query):
    """Type *query* one keystroke at a time.

    Lets each search worker finish before the next keystroke so
    exclusive=True never has to cancel one (avoids WorkerCancelled
    from an in-flight stale scan).
    """
    for char in query:
        await pilot.press(char)
        await pilot.pause()


class TestOpeningTheModal:
    async def test_capital_s_opens_modal_from_viewer(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            assert isinstance(app.focused, ViewerPane)
            await pilot.press("S")
            await pilot.pause()
            assert isinstance(app.screen, RepoSearchScreen)

    async def test_capital_s_opens_modal_from_tree(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            app.query_one(FilesTree).focus()
            await pilot.pause()
            await pilot.press("S")
            await pilot.pause()
            assert isinstance(app.screen, RepoSearchScreen)


class TestSearchingAndOpening:
    async def test_short_query_shows_placeholder(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("S")
            await pilot.pause()
            await pilot.press("a")
            await pilot.pause()
            body = app.screen.query_one("#repo-search-body")
            assert "keep typing" in str(body.render())

    async def test_typing_two_chars_lists_hits_grouped_by_file(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("S")
            await pilot.pause()
            await type_query(pilot, "async")
            body = app.screen.query_one("#repo-search-body")
            text = str(body.render())
            assert "1 matches" in text
            assert "1 files" in text
            assert "guide.md" in text
            assert "async" in text

    async def test_no_matches_message(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("S")
            await pilot.pause()
            await type_query(pilot, "zzzqqq")
            body = app.screen.query_one("#repo-search-body")
            assert "no matches" in str(body.render())

    async def test_down_moves_the_selection_marker(self, tmp_path):
        app = make_app(tmp_path)
        (tmp_path / "other.md").write_text(
            "# Other\n\nneedle over here too\n", encoding="utf-8"
        )
        (tmp_path / "docs" / "guide.md").write_text(
            "# Guide\n\nneedle in the guide\n", encoding="utf-8"
        )
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("S")
            await pilot.pause()
            await type_query(pilot, "needle")
            body = app.screen.query_one("#repo-search-body")
            initial = str(body.render())
            assert "2 matches" in initial

            await pilot.press("down")
            await pilot.pause()
            assert str(body.render()) != initial

            await pilot.press("up")
            await pilot.pause()
            assert str(body.render()) == initial

    async def test_up_from_the_first_hit_wraps_to_the_last(self, tmp_path):
        app = make_app(tmp_path)
        (tmp_path / "other.md").write_text(
            "# Other\n\nneedle over here too\n", encoding="utf-8"
        )
        (tmp_path / "docs" / "guide.md").write_text(
            "# Guide\n\nneedle in the guide\n", encoding="utf-8"
        )
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("S")
            await pilot.pause()
            await type_query(pilot, "needle")
            body = app.screen.query_one("#repo-search-body")

            await pilot.press("down")
            await pilot.pause()
            after_down = str(body.render())

            await pilot.press("up")
            await pilot.press("up")
            await pilot.pause()
            assert str(body.render()) == after_down

    async def test_enter_opens_file_at_hit_line_and_seeds_search(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("S")
            await pilot.pause()
            await type_query(pilot, "async")
            await pilot.press("enter")
            await pilot.pause()
            await pilot.pause()

            assert not isinstance(app.screen, RepoSearchScreen)
            viewer = app.query_one(ViewerPane)
            assert viewer.document is not None
            assert viewer.document.path.name == "guide.md"
            footer = app.query_one(KeyGuide)
            assert "match 1/1" in str(footer.render())
            assert isinstance(app.focused, ViewerPane)

    async def test_escape_leaves_app_unchanged(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            document_before = viewer.document
            tab_count_before = app.tab_count
            await pilot.press("S")
            await pilot.pause()
            await type_query(pilot, "async")
            await pilot.press("escape")
            await pilot.pause()

            assert not isinstance(app.screen, RepoSearchScreen)
            assert app.tab_count == tab_count_before
            assert viewer.document is document_before
