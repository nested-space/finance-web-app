# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial documentation suite for the Flask + SQLite rebuild: `README.md`, `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md`, `docs/DEVELOPMENT.md`, `docs/ROADMAP.md`.
- `pyproject.toml` with the canonical dependency declaration (`flask` runtime; `ruff`, `pytest`, `mypy` dev) and tool configuration for the mandatory quality gates.

### Notes

- No application code exists yet. The documentation suite above is the design contract that subsequent commits implement.
- The design contract reflects a pre-build review: money is stored as integer pence (not `REAL`), date columns are ISO dates (not datetimes), recurrence firing derives from `effective_from` (no `day_of_*` columns), budgets carry a `category`, the command layer and the duplicate effective-period helper are removed, and chart data is embedded server-side rather than fetched as raw records.
- The behaviour of a prior Node/Express/EJS/MongoDB implementation informs the feature set; that code is a capability reference and is not part of this repository.

[Unreleased]: https://github.com/nested-space/finance-web-app/compare/HEAD...HEAD
