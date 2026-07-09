"""
Make the package importable as ``hydro_tools`` during tests even when it has
not been ``pip install``-ed.

pyproject.toml maps the ``hydro_tools`` import name to the repository root
(package-dir = {"hydro_tools" = "."}). When the package is installed (editable
or otherwise) ``import hydro_tools`` just works. As a fallback for a bare
checkout, register the repo root as the ``hydro_tools`` package here.
"""
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

if "hydro_tools" not in sys.modules:
    try:
        import hydro_tools  # noqa: F401  (installed normally)
    except ModuleNotFoundError:
        # Load and execute the real __init__.py as the ``hydro_tools`` package so
        # its re-exports and __version__ are available, with the repo root as the
        # submodule search path so ``from .rational import ...`` resolves.
        spec = importlib.util.spec_from_file_location(
            "hydro_tools",
            REPO_ROOT / "__init__.py",
            submodule_search_locations=[str(REPO_ROOT)],
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["hydro_tools"] = module
        spec.loader.exec_module(module)
