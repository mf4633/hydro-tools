# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project aims to follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- **Critical:** `critical_depth_circular` and `normal_depth_circular` computed
  the partially-full pipe area as `(D²/4)(α − sin α)` — exactly twice the true
  circular-segment area `(D²/8)(α − sin α)` — and therefore returned wrong
  depths for every input. Corrected to `D²/8`.
- `read_dbf` now raises a clear `ValueError` on empty/truncated/malformed files
  instead of an opaque `IndexError`, and stops cleanly at a truncated final
  record.

### Added
- Input validation: `scs_runoff_depth` rejects curve numbers outside `(0, 100]`;
  `normal_depth_circular` raises when the discharge exceeds the pipe's capacity;
  `normal_depth_trapezoidal` raises when the depth exceeds its search bound.
- `LICENSE` file (MIT); PEP 639 license metadata; wheel build + smoke-test in CI.
- Test suite (pytest) and GitHub Actions CI on Python 3.9–3.12.

### Changed
- Packaging: version single-sourced from `hydro_tools.__version__`.
- Documentation rewritten with an accurate API/CLI reference.

## [0.2.0]
- Added Manning open-channel/pipe primitives: full-flow circular capacity,
  trapezoidal normal flow, friction head loss, energy-grade-line step, circular
  critical and normal depth, trapezoidal normal depth, steady network HGL
  profile, Manning velocity, and simple linear-reservoir routing.
- Packaged for PyPI (`pyproject.toml`, console entry point).

## [0.1.0]
- Initial extraction: Rational Method peak flow, SCS runoff depth, a
  pure-Python `.dbf` reader, path helpers, and the CLI skeleton.
