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
- Mandatory brand design system in `docs/DESIGN.md` (decision D-010): Slate Navy palette, sharp edges / 1px borders, panel + 20-section grid, white space, accessible colour combinations, and the secondary palette reserved for charts only. The frontend (`web/static/css/app.css` + templates) implements it — Slate Navy nav and tint waterfall — with the **Inter** typeface self-hosted under `web/static/fonts/` (no CDN).
- **C2 — Expenses, Commitments, and Income resources** (tables only), each a vertical slice off the generic `SqlModelRepository` base with its own Alembic migration:
  - Expenses: explicit date, optional description, the 7-category set, and a stricter `in_month` date predicate (not `covers_month`).
  - Commitments: the 5-category / 5-recurrence subsets (single-sourced so the form choices and table CHECK constraints can't drift), `effective_stop` computed from `length` + `length_unit` (clamped month/year math), listing grouped by recurrence, and a first-party JS toggle that hides the length fields for "Once Only".
  - Income: all six recurrences (incl. Quarterly), optional open-ended `effective_stop`, and the `income_exception` child table (FK `ON DELETE CASCADE`, `add_exception`/`list_exceptions` repo methods — persistence only, no UI; see D-011).
  - The `Recurrence` value object and `Recurrence.fires_on` firing predicate (`domain/recurrence.py`) with `domain/calendar_math.py` (day-clamped month/year arithmetic), fully unit-tested ahead of the C3 finance model.
- **C3a — the monthly dashboard.** `MonthlyModel` + `FinanceModelService` build the per-day model (recurrence firing within effective range, income-exception overrides, budgets prorated to exact pence via `Money.split_evenly`); balance series are signed `Decimal`. `InsightsService` computes the dashboard card (totals, net, closing balance, largest expense, over-budget categories), and `totals_by_category` on the budget/commitment services feeds the pies. The `/finance` dashboard (and `/finance/<year>/<month>`) renders the insights card + four Chart.js charts, embedding the server-shaped payload as JSON; `/finance/api/model/<year>/<month>` returns the same payload for in-place month navigation. Chart.js is self-hosted and chart colours come from the secondary palette. (Balance helpers corrected to return `Decimal`, not `Money`, since a running balance can go negative.)
- **C3b — the budgets and expenses page charts.** New server-side aggregates (`ExpenseService.total`/`totals_by_category`/`cumulative_spend`, `BudgetService.total`/`cumulative_allocation`) and a `HistoryService` for 6-month cumulative series. The **budgets page** gains a per-category spend-vs-budget bar, a budget breakdown pie, and a 6-month cumulative budget-vs-spend line. The **expenses page** gains a cumulative spend-vs-budget curve (actual cumulative spend vs the straight-line budget allocation) that refilters via `GET /finance/api/expenses/<year>/<month>?category=…`, a spend breakdown pie, and a 6-month cumulative spend line. This completes the documented v1.0.0 page/chart scope.

### Changed

- The "add" forms on the budgets, expenses, commitments, and income pages now open in a native `<dialog>` modal (triggered from a button in the page header) instead of an always-visible panel, so they no longer consume vertical space. A failed submit reopens the modal with the error inside it. Wired by `web/static/js/modal.js`; no new dependency.
- Reshaped `/finance/api/expenses` from "spend aggregated by category" to per-day cumulative spend + straight-line budget for a category filter (`{labels, spend_cumulative, budget_cumulative}`) — the shape the expenses spend curve needs. The endpoint was not previously built, so nothing breaks.

- **Re-platformed persistence onto SQLModel (SQLAlchemy + Pydantic) with Alembic** (decisions D-008/D-009). SQLModel `table=True` models are now the schema source of truth; repositories extend a generic `SqlModelRepository` base so CRUD lives once. `Money` and `EffectivePeriod` are retained — `Money` persists as `INTEGER` pence via a `MoneyPence` SQLAlchemy `TypeDecorator`, and `EffectivePeriod` is derived from the `effective_from`/`effective_stop` columns. Connection pragmas now apply via an engine `connect` hook; the app holds a per-request SQLModel `Session`.
- **Replaced the hand-written `schema.sql` and custom migration runner with Alembic.** `alembic upgrade head` runs on startup (forward-only, aborts loudly on failure); `alembic_version` supersedes the `schema_version` table. Added `sqlmodel` and `alembic` as approved runtime dependencies.

### Notes

- Implementation proceeds in vertical-slice cycles; this is Cycle 1 (Budgets walking skeleton). Expenses, commitments, income, the finance model, and charts are not yet built — see `docs/ROADMAP.md` -> "Build phasing".
- Cycle 1 ships a small custom stylesheet (`web/static/css/app.css`); vendoring the approved frontend libraries (Bootstrap 4, jQuery, Font Awesome) and Chart.js is scheduled with the charts cycle.
- This is pre-release work; the version remains `0.0.1` and no tag is cut (SemVer impact: none).
- The design contract reflects a pre-build review: money is stored as integer pence (not `REAL`), date columns are ISO dates (not datetimes), recurrence firing derives from `effective_from` (no `day_of_*` columns), budgets carry a `category`, the command layer and the duplicate effective-period helper are removed, and chart data is embedded server-side rather than fetched as raw records.
- The behaviour of a prior Node/Express/EJS/MongoDB implementation informs the feature set; that code is a capability reference and is not part of this repository.

[Unreleased]: https://github.com/nested-space/finance-web-app/compare/HEAD...HEAD
