"""Tests for the mokuji command-line interface."""

from __future__ import annotations

import importlib
from typing import ClassVar

import pytest

from mokuji import __version__
from mokuji._cli import main
from mokuji._ui import app as ui_app


class FakeApp:
    """Records constructor arguments instead of running a real TUI."""

    instances: ClassVar[list[FakeApp]] = []

    def __init__(self, root, initial_file=None):
        self.root = root
        self.initial_file = initial_file
        self.return_code = 0
        FakeApp.instances.append(self)

    def run(self):
        return None


@pytest.fixture
def fake_app(monkeypatch):
    FakeApp.instances = []
    monkeypatch.setattr(ui_app, "MokujiApp", FakeApp)
    return FakeApp


class TestVersionAndErrors:
    def test_version_flag_prints_version_and_exits_zero(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            main(["--version"])
        assert excinfo.value.code == 0
        assert __version__ in capsys.readouterr().out

    def test_missing_path_prints_error_and_returns_one(self, tmp_path, capsys):
        missing = tmp_path / "nope"
        assert main([str(missing)]) == 1
        stderr = capsys.readouterr().err
        assert f"mokuji: path not found: {missing}" in stderr


class TestPathResolution:
    def test_directory_argument_roots_app_there(self, tmp_path, fake_app):
        assert main([str(tmp_path)]) == 0
        (app,) = fake_app.instances
        assert app.root == tmp_path
        assert app.initial_file is None

    def test_file_argument_roots_at_parent_and_opens_file(self, tmp_path, fake_app):
        docs = tmp_path / "docs"
        docs.mkdir()
        target = docs / "usage.md"
        target.write_text("# usage\n", encoding="utf-8")
        assert main([str(target)]) == 0
        (app,) = fake_app.instances
        assert app.root == docs
        assert app.initial_file == target

    def test_no_argument_defaults_to_cwd(self, tmp_path, fake_app, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert main([]) == 0
        (app,) = fake_app.instances
        assert app.root == tmp_path
        assert app.initial_file is None

    def test_nonzero_app_return_code_propagates(self, tmp_path, fake_app, monkeypatch):
        monkeypatch.setattr(
            FakeApp, "run", lambda self: setattr(self, "return_code", 2)
        )
        assert main([str(tmp_path)]) == 2
        (app,) = fake_app.instances
        assert app.return_code == 2


class TestDunderMain:
    def test_module_is_importable_and_wired_to_main(self):
        module = importlib.import_module("mokuji.__main__")
        assert module.main is main
