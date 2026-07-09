# Contributing

Thanks for your interest in hydro-tools. It aims to be a small, auditable set of
public-domain hydrology/hydraulics primitives, so contributions should keep the
functions dependency-free, unit-consistent (US customary), and testable.

## Development setup

```bash
git clone https://github.com/mf4633/hydro-tools
cd hydro-tools
pip install -e ".[dev]"
python -m pytest tests
```

## Guidelines

- **Add a test with every change.** New primitives should pin an expected value
  computed from an independent reference (Chow, HEC-22, NRCS NEH), not from the
  implementation itself.
- **Validate inputs.** Raise `ValueError` for out-of-domain arguments rather
  than returning a silently wrong or `NaN` result.
- **Document units** in the docstring (feet, cfs, in/hr, ft/ft) and cite the
  reference formula.
- Keep runtime dependencies at zero.

CI runs the test suite on Python 3.9–3.12 and smoke-tests the built wheel; both
must pass before a change is merged.

## Building and releasing

```bash
pip install build twine
python -m build            # produces dist/*.whl and dist/*.tar.gz
twine check dist/*
twine upload dist/*        # requires a PyPI token
```

The version is single-sourced from `hydro_tools.__version__` (in `__init__.py`);
bump it there and add a `CHANGELOG.md` entry when cutting a release.
