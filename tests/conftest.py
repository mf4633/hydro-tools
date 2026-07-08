"""
Make the package importable as ``hydro_tools`` during tests even when it has
not been ``pip install``-ed.

pyproject.toml maps the ``hydro_tools`` import name to the repository root
(package-dir = {"hydro_tools" = "."}). When the package is installed (editable
or otherwise) ``import hydro_tools`` just works. As a fallback for a bare
checkout, register the repo root as the ``hydro_tools`` package here.
"""
import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

if "hydro_tools" not in sys.modules:
    try:
        import hydro_tools  # noqa: F401  (installed normally)
    except ModuleNotFoundError:
        pkg = types.ModuleType("hydro_tools")
        pkg.__path__ = [str(REPO_ROOT)]
        sys.modules["hydro_tools"] = pkg
