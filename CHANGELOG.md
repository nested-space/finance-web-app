# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial documentation suite for the Flask + SQLite rebuild: `README.md`, `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md`, `docs/DEVELOPMENT.md`, `docs/ROADMAP.md`.
- `pyproject.toml` with the canonical dependency declaration (`flask` runtime; `ruff`, `pytest`, `mypy` dev) and tool configuration for the mandatory quality gates.
- Project package scaffolding under `src/finance_web_app/` and the `tests/` tree; `schema.sql` relocated to its canonical home at `src/finance_web_app/infrastructure/persistence/schema.sql`.
- Budgets resource implemented end-to-end: domain value objects (`Money`, `EffectivePeriod`, `BudgetRecord`, `Category`), the `BudgetRepository` Protocol, a SQLite repository, `BudgetService`, the budget form, blueprint, rendering, and templates — create/list/delete with POST-redirect-GET.
- Application runtime: app factory with a per-request SQLite connection, schema bootstrap and a forward-only migration runner, and request logging that records outcomes (method, path, status, duration) but never payloads; landing page and 404 handler.
- Test pyramid covering the domain value objects, form validation, service use cases, the repository contract, the SQLite repository, the migration runner, and the web routes.

### Changed

- **Re-platformed persistence onto SQLModel (SQLAlchemy + Pydantic) with Alembic** (decisions D-008/D-009). SQLModel `table=True` models are now the schema source of truth; repositories extend a generic `SqlModelRepository` base so CRUD lives once. `Money` and `EffectivePeriod` are retained — `Money` persists as `INTEGER` pence via a `MoneyPence` SQLAlchemy `TypeDecorator`, and `EffectivePeriod` is derived from the `effective_from`/`effective_stop` columns. Connection pragmas now apply via an engine `connect` hook; the app holds a per-request SQLModel `Session`.
- **Replaced the hand-written `schema.sql` and custom migration runner with Alembic.** `alembic upgrade head` runs on startup (forward-only, aborts loudly on failure); `alembic_version` supersedes the `schema_version` table. Added `sqlmodel` and `alembic` as approved runtime dependencies.

### Notes

- Implementation proceeds in vertical-slice cycles; this is Cycle 1 (Budgets walking skeleton). Expenses, commitments, income, the finance model, and charts are not yet built — see `docs/ROADMAP.md` -> "Build phasing".
- Cycle 1 ships a small custom stylesheet (`web/static/css/app.css`); vendoring the approved frontend libraries (Bootstrap 4, jQuery, Font Awesome) and Chart.js is scheduled with the charts cycle.
- This is pre-release work; the version remains `0.0.1` and no tag is cut (SemVer impact: none).
- The design contract reflects a pre-build review: money is stored as integer pence (not `REAL`), date columns are ISO dates (not datetimes), recurrence firing derives from `effective_from` (no `day_of_*` columns), budgets carry a `category`, the command layer and the duplicate effective-period helper are removed, and chart data is embedded server-side rather than fetched as raw records.
- The behaviour of a prior Node/Express/EJS/MongoDB implementation informs the feature set; that code is a capability reference and is not part of this repository.

[Unreleased]: https://github.com/nested-space/finance-web-app/compare/HEAD...HEAD
