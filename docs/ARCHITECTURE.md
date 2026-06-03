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
| Domain layer | `domain` | Value objects, SQLModel record models, enums, invariants | Python stdlib, `sqlmodel`/`sqlalchemy`/`pydantic` (type & model definitions only — no I/O) | `application/*`, `infrastructure/*`, `web/*` |
| Persistence infrastructure | `infrastructure/persistence` | SQLModel repositories (generic base + per-resource), engine/session helpers, Alembic runner | `core/contracts`, `domain` | `web/*`, `application/*` |
| Rendering layer | `web/rendering` | Jinja rendering helpers, JSON response shapers, presentation-only mapping | `core/contracts`, `domain` | Business logic |

There is deliberately **no command layer.** For four CRUD resources with no cross-service transaction, a "thin orchestrator" between blueprint and service is a pass-through hop that earns nothing; the blueprint calls the service directly and `web/rendering` shapes the output. Reintroduce an orchestration layer only when a single request genuinely spans multiple services, and document why.

Boundary rules:

- A service must never `import` from `infrastructure.persistence`. It accepts a Protocol-typed dependency in its constructor.
- A blueprint must never call a repository directly. It goes through a service.
- Output shaping (template context, JSON) lives only in `web/rendering` — there is a single presentation home, not two.
- `core/contracts` may not import from `infrastructure/*` — Protocols are abstract by definition.
- `domain` defines types and models but performs no I/O. The record models are SQLModel `table=True` classes (the schema source of truth) and may import `sqlmodel`/`sqlalchemy`/`pydantic`, but a model never opens a session, runs a query, or "saves itself" — that is the repository's job. `Money` and `EffectivePeriod` remain pure value objects.
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
    money.py              # Money VO + MoneyPence (SQLAlchemy TypeDecorator)
    recurrence.py         # (C2)
    effective_period.py   # EffectivePeriod VO (derived from model columns)
    records.py            # SQLModel table models (Budget, User, ... ) + Category
  infrastructure/
    __init__.py
    persistence/
      __init__.py
      engine.py           # engine + connect-time pragmas; session factory
      base_repository.py   # SqlModelRepository[T] — generic CRUD
      budget_repository.py # SqlBudgetRepository(SqlModelRepository[Budget])
      migrate.py           # programmatic `alembic upgrade head`
  migrations/             # Alembic environment (ships with the package)
    env.py
    script.py.mako
    versions/
```

(`alembic.ini` lives at the repo root for the dev CLI; at runtime the app builds
the Alembic config programmatically in `migrate.py`, so it does not depend on cwd.)

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
  infrastructure/persistence/budget_repository.py
                                       (5) SqlBudgetRepository: session.add + commit
        |
        v
  SQLite file (FINANCE_DB_PATH)        (6) INSERT (MoneyPence type -> int pence)
        |
        v
  Budget model returned up the stack
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
from finance_web_app.domain.records import Budget   # a SQLModel table model


@runtime_checkable
class BudgetRepository(Protocol):
    def list_all(self) -> list[Budget]: ...
    def list_effective(self, year: int, month: int) -> list[Budget]: ...
    def get(self, budget_id: int) -> Budget: ...        # raises NotFoundError
    def create(self, record: Budget) -> Budget: ...     # returns record with id set
    def delete(self, budget_id: int) -> None: ...       # raises NotFoundError
```

The Protocol is unchanged in *shape* by the ORM switch — the service still depends
only on it. The concrete implementation extends a generic base so CRUD is written
once:

```python
# infrastructure/persistence/base_repository.py  (shared CRUD)
class SqlModelRepository(Generic[TModel]):
    model: type[TModel]
    resource_name: ClassVar[str]
    def __init__(self, session: Session) -> None: ...
    # list_all / get / create / delete implemented here once

# infrastructure/persistence/budget_repository.py
class SqlBudgetRepository(SqlModelRepository[Budget]):
    model = Budget
    resource_name = "budget"
    def list_effective(self, year: int, month: int) -> list[Budget]:
        return [b for b in self.list_all() if b.period.covers_month(year, month)]
```

Error types live in `core/contracts/errors.py`:

- `NotFoundError(resource: str, identifier: int)` — raised by `get` and `delete` when the row is absent.
- `ValidationError(field: str, reason: str)` — raised by services when a form-validated VO still fails a use-case rule.
- `RepositoryError(operation: str, cause: Exception)` — wraps an unexpected `SQLAlchemyError` so services never catch a driver exception.

Income has one extra method to cover its child table:

```python
class IncomeRepository(Protocol):
    # ... same five methods as BudgetRepository, plus:
    def add_exception(self, income_id: int, exception: IncomeException) -> None: ...
    def list_exceptions(self, income_id: int) -> list[IncomeException]: ...
```

## Domain models and value objects

`domain/` defines the record **models** (the schema source of truth) and the
**value objects** they compose. Neither performs I/O.

- **`Money`** — `dataclass(frozen=True)` wrapping a `Decimal`. Constructed via `Money.from_form_string(str)` which rejects negative input on creation. Two-decimal display via `__str__`. **Persisted as `INTEGER` minor units (pence)** by the `MoneyPence` SQLAlchemy `TypeDecorator` (also in `domain/money.py`), which converts via `Money.pence()` / `Money.from_pence(int)`. The DB never stores a float — see `OPERATIONS.md`.
- **`Recurrence`** — `Enum` with members `DAILY`, `WEEKLY`, `MONTHLY`, `QUARTERLY`, `ANNUAL`, `ONCE_ONLY` (C2). Income may use all six; commitments may use all except `QUARTERLY`. The enum member **name** is the value stored in the DB; human display text is mapped in `web/rendering`, never persisted. Firing days derive from `effective_from` (see "`FinanceModelService` contract"), so there are no `day_of_*` columns.
- **`EffectivePeriod`** — `dataclass(frozen=True)` with `from_date: date` and `stop_date: date | None`. Invariant: `stop_date is None or stop_date >= from_date`. Exposes `covers_month(year, month) -> bool` — the *single* date-effective predicate, defined here and nowhere else. It is **derived, not stored**: models persist `effective_from` / `effective_stop` columns and expose `.period` returning an `EffectivePeriod`. Services call `record.period.covers_month(...)`; there is no second copy of the predicate.
- **`Budget`** (and C2's `Expense`, `Commitment`, `Income`, `IncomeException`) — **SQLModel `table=True` models**, the schema source of truth. `id: int | None` is `None` before persistence. `quantity: Money` maps through `MoneyPence`; `category: Category` is stored as its member name. Integrity from the old `schema.sql` is preserved as `CheckConstraint`s in `__table_args__` (non-empty name, `quantity >= 0`, valid category set, `effective_stop >= effective_from`). A `created` audit timestamp column is carried on the model (defaulted server-/Python-side) but is not surfaced in templates unless a feature needs it. Models set `model_config = {"arbitrary_types_allowed": True}` so Pydantic accepts the `Money` field type.
- **`Category`** — `Enum`; member name is the persisted code, display text lives in `web/rendering`.

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

1. Add a `SavingsGoal` SQLModel `table=True` model in `domain/records.py` (with its CHECK constraints).
2. Add `SavingsGoalRepository` Protocol in `core/contracts/`.
3. Add `SqlSavingsGoalRepository(SqlModelRepository[SavingsGoal])` in `infrastructure/persistence/` — set `model`/`resource_name`, add only resource-specific queries (CRUD is inherited).
4. Generate the migration: `alembic revision --autogenerate -m "add savings_goal"`, then review the script (autogenerate misses some constraints — check the diff).
5. Add `SavingsGoalService` in `application/services/`.
6. Add `SavingsGoalForm` and a blueprint in `web/`.
7. Wire the concrete repository to the service in `core/runtime/container.py`.

You do *not* touch existing services or repositories, nor the generic base.

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

Visual design is governed by **`docs/DESIGN.md`** (the mandatory brand contract) and implemented as **custom CSS** in `web/static/css/app.css` — there is no CSS framework. The vendored frontend assets under `web/static/` are:

- **Inter** — the self-hosted typeface (`web/static/fonts/*.woff2`, no CDN). The approved font.
- **Chart.js** — canvas charting, to be vendored with the C3 charts cycle (the only place the secondary palette appears — see `DESIGN.md`).

**Adding any other JavaScript/CSS library or font — vendored, CDN, or npm — requires explicit user approval.** This is a hard rule, not guidance. A PR that introduces a new frontend dependency without approval fails the boundary check in code review.

The same rule applies to new Python dependencies: anything beyond `flask`, `sqlmodel`, and `alembic` (runtime) and `ruff`/`pytest`/`mypy` (dev) needs approval. The decision register in `ROADMAP.md` tracks requests.

## Out of scope (pointers into `ROADMAP.md`)

The following are deliberately *not* part of v1.0.0:

- **Authentication and per-user data isolation.** A `User` model is scaffolded in the SQL schema but no route requires login. See `ROADMAP.md` → "Scaffold-only seams".
- **Time zone localisation.** Date columns are stored as ISO-8601 date strings (`YYYY-MM-DD`) and the `created` audit column as a UTC datetime; both are rendered as-is. See `ROADMAP.md` → "Future priorities".
- **Multi-currency.** `Money` wraps a single `Decimal` with no currency tag. See `ROADMAP.md` → "Non-goals".
- **Mobile-native client.** The web UI is responsive (Bootstrap), but no native app. See `ROADMAP.md` → "Non-goals".
