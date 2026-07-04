"""Pilot tests for in-file search (req 2.6)."""

from __future__ import annotations

from mokuji._ui.app import MokujiApp
from mokuji._ui.footer import KeyGuide
from mokuji._ui.viewer import ViewerPane

DOCUMENT = (
    "# Title\n\n"
    "needle here\n\n"
    + "\n\n".join(f"filler {i}" for i in range(100))
    + "\n\nneedle again\n\nNeedle capital\n"
)


def make_app(tmp_path, name="README.md", text=DOCUMENT):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return MokujiApp(root=tmp_path, initial_file=path)


async def search_for(pilot, query):
    await pilot.press("slash")
    await pilot.pause()
    for char in query:
        await pilot.press(char)
    await pilot.press("enter")
    await pilot.pause()


class TestSearchInput:
    async def test_slash_opens_focused_search_input(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("slash")
            await pilot.pause()
            assert app.query_one("#search-input").has_focus

    async def test_escape_cancels_input_and_restores_footer(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("slash")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert not app.query_one("#search-input").display
            footer = app.query_one(KeyGuide)
            assert footer.display
            assert "? help" in str(footer.render())
            assert isinstance(app.focused, ViewerPane)

    async def test_empty_query_enter_closes_input_without_action(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await search_for(pilot, "")
            assert not app.query_one("#search-input").display
            assert viewer.scroll_y == 0
            assert "? help" in str(app.query_one(KeyGuide).render())


class TestSearchJumping:
    async def test_match_jump_scrolls_and_shows_counter(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await pilot.press("G")
            await pilot.press("g", "g")
            assert viewer.scroll_y == 0
            await search_for(pilot, "again")
            assert viewer.scroll_y > 0
            footer = app.query_one(KeyGuide)
            assert "match 1/1" in str(footer.render())

    async def test_no_match_flashes_and_does_not_move(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            viewer = app.query_one(ViewerPane)
            await search_for(pilot, "zzzq")
            assert viewer.scroll_y == 0
            assert "no match: zzzq" in str(app.query_one(KeyGuide).render())

    async def test_n_wraps_around_with_flash(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await search_for(pilot, "again")
            await pilot.press("n")
            await pilot.pause()
            footer = app.query_one(KeyGuide)
            assert "search wrapped" in str(footer.render())

    async def test_n_and_shift_n_move_between_matches(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await search_for(pilot, "needle")
            footer = app.query_one(KeyGuide)
            assert "match 1/3" in str(footer.render())
            await pilot.press("n")
            await pilot.pause()
            assert "match 2/3" in str(footer.render())
            await pilot.press("N")
            await pilot.pause()
            assert "match 1/3" in str(footer.render())

    async def test_status_line_hints_the_search_keys(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await search_for(pilot, "needle")
            status = str(app.query_one(KeyGuide).render())
            assert "n/N next/prev" in status
            assert "Esc clear" in status


class TestSmartCase:
    async def test_lowercase_query_is_case_insensitive(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await search_for(pilot, "needle")
            assert "match 1/3" in str(app.query_one(KeyGuide).render())

    async def test_uppercase_query_is_case_sensitive(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await pilot.press("slash")
            await pilot.pause()
            search_input = app.query_one("#search-input")
            search_input.value = "Needle"
            await pilot.press("enter")
            await pilot.pause()
            assert "match 1/1" in str(app.query_one(KeyGuide).render())


class TestPlainTextHighlight:
    async def test_matches_highlighted_inline(self, tmp_path):
        text = "alpha one\nalpha two\nalpha three\n"
        app = make_app(tmp_path, name="notes.txt", text=text)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await search_for(pilot, "alpha")
            plain = app.query_one(".plain-text")
            rendered = plain.render()
            assert len(rendered.spans) >= 3

    async def test_escape_in_content_clears_highlights(self, tmp_path):
        text = "alpha one\nalpha two\n"
        app = make_app(tmp_path, name="notes.txt", text=text)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await search_for(pilot, "alpha")
            assert len(app.query_one(".plain-text").render().spans) >= 2
            await pilot.press("escape")
            await pilot.pause()
            assert len(app.query_one(".plain-text").render().spans) == 0


class TestPerTabSearchState:
    async def test_search_state_restored_after_switching_tabs(self, tmp_path):
        app = make_app(tmp_path)
        (tmp_path / "b.md").write_text(
            "# B\n\nnothing to find here\n", encoding="utf-8"
        )
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            await search_for(pilot, "needle")
            footer = app.query_one(KeyGuide)
            assert "match 1/3" in str(footer.render())

            await app.open_in_new_tab(tmp_path / "b.md")
            await pilot.pause()
            assert app.tab_count == 2
            assert "match" not in str(footer.render())

            await pilot.press("g", "T")
            await pilot.pause()
            assert "match 1/3" in str(footer.render())

            await pilot.press("n")
            await pilot.pause()
            assert "match 2/3" in str(footer.render())
