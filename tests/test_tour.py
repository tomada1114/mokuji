"""Pilot tests for the welcome tour and its drift guards."""

from __future__ import annotations

import re

import pytest

from mokuji._ui.app import MokujiApp
from mokuji._ui.help import FILES_AND_TOC, READING, SEARCH, TABS_AND_HISTORY, HelpScreen
from mokuji._ui.tour import FINISH_SECTION, PAGES, TourScreen, page_dots, tutorial_path
from mokuji._ui.viewer import ViewerPane

DOCUMENT = "# Title\n\nbody text\n"

ALL_SECTIONS = (READING, TABS_AND_HISTORY, FILES_AND_TOC, SEARCH, FINISH_SECTION)

# Keys that are real bindings but never appear in the help sections
# (``q`` quits from the app-level bindings).
EXTRA_KEYS = {"q"}


def make_app(tmp_path):
    path = tmp_path / "README.md"
    path.write_text(DOCUMENT, encoding="utf-8")
    return MokujiApp(root=tmp_path, initial_file=path)


def canonical_key_tokens() -> set[str]:
    """All key tokens named by the help sections (e.g. ``gt``, ``C-o``)."""
    tokens: set[str] = set()
    for _, rows in ALL_SECTIONS:
        for key, _ in rows:
            for part in key.split(" / "):
                tokens.update(part.split())
    return tokens | EXTRA_KEYS


class TestFirstRun:
    async def test_first_launch_shows_tour_and_writes_marker(self, tmp_path, first_run):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            assert isinstance(app.screen, TourScreen)
            assert first_run.exists()

    async def test_second_launch_does_not_show_tour(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            assert not isinstance(app.screen, TourScreen)


class TestNavigation:
    @pytest.mark.usefixtures("first_run")
    async def test_l_and_h_move_between_pages_with_clamping(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, TourScreen)
            assert screen.page_index == 0
            await pilot.press("h")
            assert screen.page_index == 0
            await pilot.press("l")
            assert screen.page_index == 1
            await pilot.press("right")
            assert screen.page_index == 2
            await pilot.press("left")
            assert screen.page_index == 1

    @pytest.mark.usefixtures("first_run")
    async def test_l_on_last_page_stays_open(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, TourScreen)
            for _ in range(len(PAGES) + 2):
                await pilot.press("l")
            assert screen.page_index == len(PAGES) - 1
            assert isinstance(app.screen, TourScreen)

    @pytest.mark.usefixtures("first_run")
    async def test_escape_skips_without_opening_tutorial(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert not isinstance(app.screen, TourScreen)
            viewer = app.query_one(ViewerPane)
            assert viewer.document is not None
            assert viewer.document.path.name == "README.md"

    @pytest.mark.usefixtures("first_run")
    async def test_enter_through_all_pages_opens_tutorial(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            for _ in range(len(PAGES)):
                await pilot.press("enter")
            await pilot.pause()
            assert not isinstance(app.screen, TourScreen)
            viewer = app.query_one(ViewerPane)
            assert viewer.document is not None
            assert viewer.document.path == tutorial_path().resolve()


class TestReopen:
    async def test_w_from_help_reopens_tour(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("question_mark")
            assert isinstance(app.screen, HelpScreen)
            await pilot.press("w")
            await pilot.pause()
            assert isinstance(app.screen, TourScreen)

    async def test_help_plain_close_does_not_open_tour(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("question_mark")
            await pilot.press("escape")
            await pilot.pause()
            assert not isinstance(app.screen, TourScreen | HelpScreen)


class TestPageDots:
    def test_page_dots_show_position_and_counter(self):
        rendered = page_dots(1, 5)
        assert rendered.count("●") == 1
        assert rendered.count("○") == 4
        assert "2/5" in rendered


class TestDriftGuard:
    """A renamed keybinding must fail here, not rot the guide silently."""

    def test_tour_pages_reuse_canonical_sections(self):
        assert {id(page.section) for page in PAGES} <= {id(s) for s in ALL_SECTIONS}

    def test_tutorial_key_mentions_exist_in_help_sections(self):
        text = tutorial_path().read_text(encoding="utf-8")
        canonical = canonical_key_tokens()
        mentions = re.findall(r"`([^`\n]+)`", text)
        assert mentions, "tutorial.md should teach at least one key"
        unknown = {
            mention
            for mention in mentions
            if mention.replace("Ctrl+", "C-") not in canonical
        }
        assert not unknown, f"tutorial.md mentions unknown keys: {sorted(unknown)}"
