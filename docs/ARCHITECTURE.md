# Architecture

This document is the source of truth for the layering, contracts, and boundaries of `finance_web_app`. If guidance elsewhere conflicts with this file, this file wins for structural questions.

## Purpose

`finance_web_app` is a single-process Flask application that lets one user track:

- **Budgets** — recurring monthly spending caps with an effective date range.
- **Expenses** — one-off spends categorised at point of entry.
- **Commitments** — recurring outgoings (e.g. subscriptions) with a recurrence pattern and optional stop date.
- **Income streams** — recurring income with the same recurrence pattern shape as commitments, plus one-off `exceptions` that override the regular amount on a specific date.

The dashboard renders a per-day balance projection for the current month combining all four resources.

## Layer map

The codebase is organised under `src/finance_web_app/`. Each layer has a single responsibility and a strict dependency rule.

| Layer | Path | Responsibility | Allowed Dependencies | Forbidden Dependencies |
| --- | --- | --- | --- | --- |
| Web blueprint layer | `web/blueprints` | Flask routes, request parsing, calling a service, redirect/render decisions | `application/services`, `web/forms`, `web/rendering` | `infrastructure/*`, `domain` instantiation logic |
| Web form layer | `web/forms` | Request-body validation, type coercion from form input to domain VOs | `domain`, `core/contracts/errors` | `application/*`, `infrastructure/*` |
| Service layer | `application/services` | Use-case logic, date-effective filtering, finance modelling, insights computation. Invoked directly by blueprints. | `core/contracts`, `domain` | `web/*`, `infrastructure/persistence` concretes |
| Contracts layer | `core/contracts` | Repository Protocols, typed error classes, boundary types | `domain` only when needed for signatures | `infrastructure/*`, `web/*`, `application/services` |
| Runtime layer | `core/runtime` | App factory, DI wiring, container — the *only* place where concrete repositories are bound to service constructors | `core/contracts`, `application/services`, `infrastructure/persistence` concretes | Business rules |
| Domain layer | `domain` | Value objects, records, enums, invariants | Python stdlib only | `application/*`, `infrastructure/*`, `web/*` |
| Persistence infrastructure | `infrastructure/persistence` | SQLite repositories, connection helper, schema bootstrap, migration runner | `core/contracts`, `domain` | `web/*`, `application/*` |
| Rendering layer | `web/rendering` | Jinja rendering helpers, JSON response shapers, presentation-only mapping | `core/contracts`, `domain` | Business logic |

There is deliberately **no command layer.** For four CRUD resources with no cross-service transaction, a "thin orchestrator" between blueprint and service is a pass-through hop that earns nothing; the blueprint calls the service directly and `web/rendering` shapes the output. Reintroduce an orchestration layer only when a single request genuinely spans multiple services, and document why.

Boundary rules:

- A service must never `import` from `infrastructure.persistence`. It accepts a Protocol-typed dependency in its constructor.
- A blueprint must never call a repository directly. It goes through a service.
- Output shaping (template context, JSON) lives only in `web/rendering` — there is a single presentation home, not two.
- `core/contracts` may not import from `infrastructure/*` — Protocols are abstract by definition.
- `domain` is leaf. If a value object needs to "save itself" or "query for siblings", you have the wrong layer.
- `core/runtime` is the only layer permitted to import both a Protocol from `core/contracts` *and* a concrete class from `infrastructure/persistence`. It is the seam. The "container" is plain factory wiring, not a DI framework.

## Repository layout

```
src/finance_web_app/
  __init__.py
  web/
    __init__.py
    blueprints/
      __init__.py
      home.py
      summary.py
      budgets.py
      expenses.py
      commitments.py
      income.py
      api.py
      errors.py
    forms/
      __init__.py
      budget_form.py
      expense_form.py
      commitment_form.py
      income_form.py
    rendering/            # presentation shaping (was io/components)
      __init__.py
      json_response.py
      template_context.py
    templates/            # Jinja
    static/               # vendored Bootstrap, Chart.js, jQuery, Font Awesome, custom CSS/JS
  application/
    __init__.py
    services/
      __init__.py
      budget_service.py
      expense_service.py
      commitment_service.py
      income_service.py
      finance_model_service.py
      insights_service.py
  core/
    __init__.py
    contracts/
      __init__.py
      budget_repository.py
      expense_repository.py
      commitment_repository.py
      income_repository.py
      errors.py
    runtime/
      __init__.py
      app_factory.py
      container.py
  domain/
    __init__.py
    money.py
    recurrence.py
    effective_period.py
    records.py
  infrastructure/
    __init__.py
    persistence/
      __init__.py
      connection.py
      schema.sql
      migrations/
      budget_repository_sqlite.py
      expense_repository_sqlite.py
      commitment_repository_sqlite.py
      income_repository_sqlite.py
```

## Runtime flow

A single request walks every layer exactly once. The canonical example is `POST /finance/budgets` (creating a budget).

```
HTTP POST /finance/budgets
        |
        v
  web/blueprints/budgets.py            (1) parse request, route to handler
        |
        v
  web/forms/budget_form.py             (2) validate fields, coerce to domain VOs
        |
        v
  application/services/budget_service.py
                                       (3) apply use-case rules, build BudgetRecord
        |
        v
  core/contracts/budget_repository.py  (4) Protocol contract — what the service sees
        |
        v
  infrastructure/persistence/budget_repository_sqlite.py
                                       (5) concrete impl, parameterised SQL
        |
        v
  SQLite file (FINANCE_DB_PATH)        (6) INSERT (Money -> int pence at the boundary)
        |
        v
  BudgetRecord returned up the stack
        |
        v
  web/blueprints/budgets.py            (7) PRG: redirect to GET /finance/budgets
```

Read flow for `GET /finance` (the dashboard) is the same shape, with the service returning a list of `BudgetRecord`/`ExpenseRecord`/`CommitmentRecord`/`IncomeRecord`. `FinanceModelService` then synthesises the per-day balance series, and `web/rendering/template_context.py` shapes those into the dict the Jinja template expects — including the chart data, embedded in the page as JSON rather than refetched over AJAX (see "Frontend data delivery" below).

## Repository protocol shape

Every resource follows the same Protocol shape. `BudgetRepository` is the canonical example.

Each Protocol is decorated `@runtime_checkable` so the contract tests in `tests/unit/core/contracts/` can assert `isinstance(impl, BudgetRepository)` (a bare `Protocol` does not support `isinstance`).

```python
# core/contracts/budget_repository.py
from typing import Protocol, runtime_checkable
from finance_web_app.domain.records import BudgetRecord


@runtime_checkable
class BudgetRepository(Protocol):
    def list_all(self) -> list[BudgetRecord]: ...
    def list_effective(self, year: int, month: int) -> list[BudgetRecord]: ...
    def get(self, budget_id: int) -> BudgetRecord: ...           # raises NotFoundError
    def create(self, record: BudgetRecord) -> BudgetRecord: ...  # returns record with id set
    def delete(self, budget_id: int) -> None: ...                # raises NotFoundError
```

Error types live in `core/contracts/errors.py`:

- `NotFoundError(resource: str, identifier: int)` — raised by `get` and `delete` when the row is absent.
- `ValidationError(field: str, reason: str)` — raised by services when a form-validated VO still fails a use-case rule.
- `RepositoryError(operation: str, cause: Exception)` — wraps unexpected SQL failures so services never catch `sqlite3.Error`.

Income has one extra method to cover its child table:

```python
class IncomeRepository(Protocol):
    # ... same five methods as BudgetRepository, plus:
    def add_exception(self, income_id: int, exception: IncomeException) -> None: ...
    def list_exceptions(self, income_id: int) -> list[IncomeException]: ...
```

## Domain value objects

`domain/` contains pure data types. They have invariants but no I/O.

- **`Money`** — `dataclass(frozen=True)` wrapping a `Decimal`. Constructed via `Money.from_form_string(str)` which rejects negative input on creation. Two-decimal display via `__str__`. **Persisted as `INTEGER` minor units (pence):** repositories convert `Money` to/from `int` at the persistence boundary via `Money.pence()` / `Money.from_pence(int)`. The DB never stores a float — see `schema.sql` and `OPERATIONS.md`.
- **`Recurrence`** — `Enum` with members `DAILY`, `WEEKLY`, `MONTHLY`, `QUARTERLY`, `ANNUAL`, `ONCE_ONLY`. Income may use all six; commitments may use all except `QUARTERLY`. The enum member **name** (`ONCE_ONLY`, etc.) is the value stored in the DB and the schema `CHECK` set; human display text is mapped in `web/rendering`, never persisted. Recurrence carries no extra day fields — a record's firing days are derived from its own `effective_from` (see "`FinanceModelService` contract"), so there are no `day_of_*` columns to keep consistent.
- **`EffectivePeriod`** — `dataclass(frozen=True)` with `from_date: date` and `stop_date: date | None`. Invariant: `stop_date is None or stop_date >= from_date`. Exposes `covers_month(year: int, month: int) -> bool` — the *single* date-effective predicate used everywhere, defined here and nowhere else. Services call this method; there is no second copy of the predicate in `application/services`. (See "Bug-fix decisions" below.)
- **`BudgetRecord`**, **`ExpenseRecord`**, **`CommitmentRecord`**, **`IncomeRecord`** — `dataclass(frozen=True)` with `id: int | None`, `name: str`, `quantity: Money`, plus resource-specific fields (`BudgetRecord` and the categorised resources carry a `category`). `id` is `None` before persistence. The DB `created` column is an audit timestamp and is **not** carried on these records; surface it on a record only if a feature needs it.
- **`IncomeException`** — child record of `IncomeRecord`: `date`, `quantity: Money`, `reason: str | None`.

## Bug-fix decisions (carried over from the prior Node implementation)

The prior Node implementation contained several latent bugs in date-effective filtering. Those bugs are *not* replicated. The corrected semantics are encoded in exactly one place — `EffectivePeriod.covers_month`:

- A period covers month `(year, month)` if `from_date <= last_day_of_month` AND (`stop_date is None` OR `stop_date >= first_day_of_month`).
- "Starts this month" is **inclusive** — a record that begins on the 15th still counts as effective for the whole month.
- The same predicate is used for budgets, commitments, and income — no per-resource variation.
- Months in URLs and Python code are **1-indexed (1–12)** end to end. There is no `month - 1` conversion anywhere outside `EffectivePeriod` itself.

Expenses use a stricter predicate: `expense.date.year == year and expense.date.month == month`. This is its own helper, not a special case of `covers_month`.

## `FinanceModelService` contract

`FinanceModelService` replaces the JavaScript `getFinanceModel` / `cumulativeModel` / `subtractiveModel` / `constraintsFulfilled` cluster from the reference implementation.

```python
class FinanceModelService:
    def model_for_month(self, year: int, month: int) -> MonthlyModel: ...
```

`MonthlyModel` is a domain object exposing per-day fields:

- `dates: list[date]` — every day in the month.
- `income_per_day: list[Money]` — sum of all income that "fires" on each day (after applying exceptions).
- `commitments_per_day: list[Money]`
- `expenses_per_day: list[Money]`
- `budget_allocated_per_day: list[Money]` — budgets prorated linearly across the days they cover.

Plus derived helpers:

- `cumulative_balance() -> list[Money]` — running total of income minus outgoings.
- `subtractive_balance(starting: Money) -> list[Money]` — running balance starting from a given amount.

A recurring record "fires" on a date when `Recurrence.fires_on(when, effective_from)` returns `True`. Implementation lives in `domain/recurrence.py` so the predicate is testable without touching the service. Firing is derived from the record's own `effective_from` — there are no separate `day_of_*` inputs to store or validate. The Recurrence enum encapsulates the rules:

- `DAILY`: every day.
- `WEEKLY`: on the weekday of `effective_from`.
- `MONTHLY`: on the day-of-month of `effective_from`; if the month is shorter, the last day is used.
- `QUARTERLY`: only valid for income; fires on the day-of-month of `effective_from` every third month from `effective_from`.
- `ANNUAL`: same month and day as `effective_from`.
- `ONCE_ONLY`: exactly on `effective_from`.

Income exceptions: if an `IncomeException` exists for date `D`, the exception's `quantity` *replaces* the recurring amount for that day (not adds to it).

## Extension seams

Adding a fifth resource (hypothetical "savings goals"):

1. Add `SavingsGoalRecord` in `domain/records.py`.
2. Add `SavingsGoalRepository` Protocol in `core/contracts/`.
3. Add `SqliteSavingsGoalRepository` in `infrastructure/persistence/`, plus a migration script in `infrastructure/persistence/migrations/`.
4. Add `SavingsGoalService` in `application/services/`.
5. Add `SavingsGoalForm` and a blueprint in `web/`.
6. Wire the concrete repository to the service in `core/runtime/container.py`.

You do *not* touch existing services or repositories.

Adding a new recurrence pattern (e.g. "Biweekly"):

1. Add `BIWEEKLY` to `Recurrence` enum.
2. Extend `Recurrence.fires_on` to handle it.
3. Add unit tests in `tests/unit/domain/test_recurrence.py`.
4. Update the relevant form dropdowns in `web/forms/`.
5. Add the new value to the SQL `CHECK` constraint via a forward migration.

You do *not* touch the services that consume `Recurrence.fires_on` — they call the enum's method, never `match` on it themselves.

Adding a new chart on an existing page:

1. Add a `<canvas>` element to the relevant Jinja template.
2. Add the chart's data to the page's template context in `web/rendering/template_context.py`, fully shaped (aggregated/summed) by a service method, and emit it as an embedded `<script type="application/json">` block (see "Frontend data delivery").
3. Add a small JS module under `web/static/js/` that reads that embedded JSON and feeds Chart.js. The JS does **no** aggregation or business logic.
4. Only if a chart must refetch *after* first paint (e.g. the category-filtered spend chart) add a JSON endpoint in `web/blueprints/api.py`, returning data already shaped by a service method.

Adding a new validation rule on an existing form:

1. Extend the form class in `web/forms/`.
2. Add a unit test for the form.
3. If the rule is also a domain invariant (e.g. "amount must be non-negative"), encode it in the domain VO instead and let the form catch the resulting `ValueError`.

## Frontend data delivery

The app is server-rendered and single-user, so chart data is **computed server-side and embedded in the page**, not fetched over a second round-trip. `web/rendering/template_context.py` calls the relevant service (e.g. `FinanceModelService.model_for_month`) and serialises the result — including per-category aggregates and the per-day balance series — into an embedded `<script type="application/json" id="...">` block. The page's JS reads that block and hands it to Chart.js.

Consequences, and why this shape is fixed *before* the first build (changing a JSON response shape is a MAJOR SemVer bump — see `DEVELOPMENT.md`):

- The dashboard renders from **one** request, not one render plus four AJAX calls.
- A "6-month history" chart is served by a single range query in its service method, not six month-scoped requests.
- **Aggregation never happens in JavaScript.** Sum-by-category for the breakdown pies, spend-vs-budget joins, and the cumulative/subtractive balance series are all produced by services. This is what makes `FinanceModelService` the real owner of the finance model rather than a vestige.

`web/blueprints/api.py` exists only for genuine post-paint refetches (the category filter on the expenses page). Any endpoint it exposes returns data already shaped by a service method — no business logic in the endpoint. If such an endpoint serves the dashboard's per-day model, it is a single `/finance/api/model/<year>/<month>` returning the whole `MonthlyModel`, not four raw-record endpoints.

## Frontend asset boundary

The application ships with four vendored UI libraries under `web/static/`:

- Bootstrap 4 (CSS framework)
- Chart.js (canvas charting)
- jQuery (DOM, AJAX)
- Font Awesome (icons)

**Adding any other JavaScript or CSS library — vendored, CDN, or npm — requires explicit user approval.** This is a hard rule, not guidance. A PR that introduces a new frontend dependency without approval fails the boundary check in code review.

The same rule applies to new Python dependencies: anything beyond `flask` (runtime) and `ruff`/`pytest`/`mypy` (dev) needs approval. The decision register in `ROADMAP.md` tracks pending requests.

## Out of scope (pointers into `ROADMAP.md`)

The following are deliberately *not* part of v1.0.0:

- **Authentication and per-user data isolation.** A `User` model is scaffolded in the SQL schema but no route requires login. See `ROADMAP.md` → "Scaffold-only seams".
- **Time zone localisation.** Date columns are stored as ISO-8601 date strings (`YYYY-MM-DD`) and the `created` audit column as a UTC datetime; both are rendered as-is. See `ROADMAP.md` → "Future priorities".
- **Multi-currency.** `Money` wraps a single `Decimal` with no currency tag. See `ROADMAP.md` → "Non-goals".
- **Mobile-native client.** The web UI is responsive (Bootstrap), but no native app. See `ROADMAP.md` → "Non-goals".
