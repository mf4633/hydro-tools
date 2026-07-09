"""Tests for the path helpers in ``hydro_tools.paths``."""
from pathlib import Path

from hydro_tools import paths


def test_get_project_root_finds_a_marker():
    root = paths.get_project_root()
    assert isinstance(root, Path)
    # the resolved root should contain a recognizable marker
    assert (root / ".git").exists() or (root / "pyproject.toml").exists()


def test_resolve_absolute_path_passthrough(tmp_path):
    abs_path = tmp_path / "model.inp"
    assert paths.resolve_model_path(str(abs_path)) == abs_path


def test_resolve_relative_hits_project_root():
    # a path that exists under the project root resolves there
    resolved = paths.resolve_model_path("pyproject.toml")
    assert resolved == paths.get_project_root() / "pyproject.toml"
    assert resolved.exists()


def test_resolve_env_override(monkeypatch, tmp_path):
    # a non-existent relative path falls through to $HYDRO_PROJECT_BASE
    monkeypatch.setenv("HYDRO_PROJECT_BASE", str(tmp_path))
    resolved = paths.resolve_model_path("no/such/file_xyz.inp")
    assert resolved == tmp_path / "no/such/file_xyz.inp"


def test_resolve_cwd_fallback(monkeypatch, tmp_path):
    # with no env override and no project hit, fall back to cwd
    monkeypatch.delenv("HYDRO_PROJECT_BASE", raising=False)
    monkeypatch.chdir(tmp_path)
    resolved = paths.resolve_model_path("no/such/file_xyz.inp")
    assert resolved == Path.cwd() / "no/such/file_xyz.inp"
