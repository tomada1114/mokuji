"""Tests for the key guide footer: hint wrapping and the flash channel."""

from __future__ import annotations

from mokuji._ui.app import MokujiApp
from mokuji._ui.footer import MAX_GUIDE_LINES, KeyGuide, wrap_hints

DOCUMENT = "# Title\n\n" + "\n\n".join(f"paragraph {i}" for i in range(30)) + "\n"


def make_app(tmp_path):
    path = tmp_path / "README.md"
    path.write_text(DOCUMENT, encoding="utf-8")
    return MokujiApp(root=tmp_path, initial_file=path)


def footer_text(app: MokujiApp) -> str:
    return str(app.query_one(KeyGuide).render())


class TestWrapHints:
    # cells per pair: "a one" = 5, "bb two" = 6, "c three" = 7; separator = 3
    HINTS = (
        ("a", "one", 0),
        ("bb", "two", 1),
        ("c", "three", 2),
    )

    def test_wide_width_fits_every_hint_on_one_line(self):
        assert wrap_hints(self.HINTS, 100) == (
            (("a", "one"), ("bb", "two"), ("c", "three")),
        )

    def test_narrow_width_wraps_instead_of_dropping(self):
        # 5 + 3 + 6 = 14 fills line one; "c three" wraps to line two.
        assert wrap_hints(self.HINTS, 14) == (
            (("a", "one"), ("bb", "two")),
            (("c", "three"),),
        )

    def test_very_narrow_width_gives_one_hint_per_line(self):
        assert wrap_hints(self.HINTS, 7) == (
            (("a", "one"),),
            (("bb", "two"),),
            (("c", "three"),),
        )

    def test_exceeding_max_lines_drops_the_highest_tier(self):
        assert wrap_hints(self.HINTS, 7, max_lines=2) == (
            (("a", "one"),),
            (("bb", "two"),),
        )

    def test_tier_zero_is_the_floor_even_beyond_max_lines(self):
        hints = (("a", "one", 0), ("b", "two", 0))
        assert wrap_hints(hints, 5, max_lines=1) == (
            (("a", "one"),),
            (("b", "two"),),
        )

    def test_default_cap_is_three_lines(self):
        assert MAX_GUIDE_LINES == 3


class TestGuideWrapping:
    async def test_narrow_terminal_still_shows_every_hint(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(60, 24)) as pilot:
            await pilot.pause()
            text = footer_text(app)
            for fragment in (
                "j/k scroll",
                "d/u page",
                "gg/G top/bottom",
                "x close tab",
                "C-o/C-i history",
                "r reload",
                "q quit",
            ):
                assert fragment in text
            lines = text.split("\n")
            assert 2 <= len(lines) <= MAX_GUIDE_LINES
            assert all(len(line) <= 60 for line in lines)

    async def test_wide_terminal_uses_a_single_line(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(160, 24)) as pilot:
            await pilot.pause()
            text = footer_text(app)
            assert "\n" not in text
            assert "C-o/C-i history" in text

    async def test_resize_rewraps_the_hints(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(160, 24)) as pilot:
            await pilot.pause()
            assert "\n" not in footer_text(app)
            await pilot.resize_terminal(60, 24)
            await pilot.pause()
            text = footer_text(app)
            assert "\n" in text
            assert "C-o/C-i history" in text

    async def test_tree_hints_wrap_and_show_everything(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            await pilot.press("e")
            await pilot.pause()
            text = footer_text(app)
            for fragment in (
                "j/k move",
                "h/l collapse/expand",
                "Tab switch focus",
                ". all files",
            ):
                assert fragment in text


class TestFlash:
    async def test_flash_keeps_the_footer_height(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(60, 24)) as pilot:
            await pilot.pause()
            default_lines = footer_text(app).count("\n")
            assert default_lines > 0
            app.flash("reloaded")
            await pilot.pause()
            text = footer_text(app)
            assert text.startswith("reloaded")
            assert text.count("\n") == default_lines

    async def test_flash_treats_brackets_as_plain_text(self, tmp_path):
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 24)) as pilot:
            await pilot.pause()
            app.flash("not found: [weird].md")
            await pilot.pause()
            assert "not found: [weird].md" in footer_text(app)
