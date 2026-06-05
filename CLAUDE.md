# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

All four resources (budgets, expenses, commitments, income) are implemented end-to-end on a **SQLModel +
Alembic** stack, plus the **`/finance` dashboard** and the **per-page charts** on the budgets and expenses
pages. This completes the documented v1.0.0 page/chart scope; a `1.0.0` tag is a release decision, not yet
cut (open items D-001/D-003/D-011 — see `docs/ROADMAP.md`). The app is the Flask + SQLite rebuild of a
prior Node/Express/EJS/MongoDB app (that old code is a *capability reference only*, not in this repo).

The docs are authoritative and have a precedence order:

- **`docs/ARCHITECTURE.md`** — wins for any structural/layering/boundary/contract question.
- **`docs/DEVELOPMENT.md`** — the engineering process: quality gates, testing, commits, SemVer.
- **`docs/OPERATIONS.md`** — running, env vars, Alembic migrations, the SQLite storage conventions.
- **`docs/ROADMAP.md`** — what is in/out of v1.0.0 scope, plus the decisions register.

Read `docs/ARCHITECTURE.md` before writing any code. Most "where does this go?" questions are
already answered there (layer map, repository Protocol shape, extension seams).

## Quality gates (the merge gate — all four must exit zero)

```bash
source ~/.venvs/finance/bin/activate   # or your venv; install with: pip install -e .[dev]

ruff format src/ tests/ --check
ruff check src/ tests/
PYTHONPATH=src pytest -q
MYPYPATH=src mypy src/ tests/
```

- Run the app: `flask --app finance_web_app.web run` (serves 127.0.0.1:5000; `FLASK_DEBUG=1` for reloader).
- Run one test: `PYTHONPATH=src pytest tests/unit/domain/test_recurrence.py::test_name -q`.
- Markers: `pytest -m unit` (no I/O/DB) / `pytest -m integration` (touches SQLite or the Flask client).
- No bypassing or `# noqa`-suppressing a gate failure — fix the root cause. mypy runs in `strict` mode.
- A gate-config change (e.g. ruff settings) is its own `chore:` commit, never bundled with feature work.

## Architecture in one screen

Layers under `src/finance_web_app/`, with a **strict one-directional dependency rule** (full table in
`docs/ARCHITECTURE.md`). A request walks each layer once:

```
web/blueprints  →  web/forms  →  application/services  →  core/contracts (Protocols)  →  infrastructure/persistence (SQLModel)
                                          ↓
                                   web/rendering   (shapes template context + JSON; presentation only)
```

Persistence is **SQLModel + Alembic**: models in `domain/records.py` are the schema source of truth;
repositories extend a generic `SqlModelRepository[T]` base (CRUD written once) and keep their Protocols;
the app holds a per-request `Session`; `app_factory` runs `alembic upgrade head` on startup.

Hard boundary rules that span files (a PR violating these fails review):

- A **service never imports `infrastructure.persistence`**. It takes a Protocol-typed repo in its constructor.
- A **blueprint never calls a repository directly** — always through a service.
- **`core/runtime/container.py` is the only seam** allowed to import both a `core/contracts` Protocol and a
  concrete `infrastructure/persistence` class. It owns the request-scoped `Session`. Plain factory wiring, not a DI framework.
- **`domain/` performs no I/O.** Record models are SQLModel classes (may import sqlmodel/sqlalchemy/pydantic) but never open a session or query; `Money`/`EffectivePeriod` stay pure value objects.
- Output shaping (template context, JSON) lives **only** in `web/rendering`.
- There is deliberately **no command/orchestrator layer**. Don't add one unless one request genuinely
  spans multiple services — and document why.

## Invariants that are easy to get wrong (encoded once, on purpose)

- **Money is integer pence.** `Money` wraps a `Decimal`; the `MoneyPence` SQLAlchemy `TypeDecorator`
  (in `domain/money.py`) stores it as an `INTEGER` column — never a float.
- **Months are 1-indexed (1–12) end to end** — URLs, Python, JSON. No `month - 1` anywhere except inside
  `EffectivePeriod` itself.
- **One date-effective predicate:** `EffectivePeriod.covers_month(year, month)`, called as `record.period.covers_month(...)`.
  `EffectivePeriod` is *derived* from the model's `effective_from`/`effective_stop` columns (the `.period`
  property), not stored. Used identically for budgets, commitments, and income — no per-resource copy.
  "Starts mid-month" counts as effective for the whole month. (Expenses use a separate stricter `date.year/month ==` helper.)
- **Recurrence firing derives from the record's own `effective_from`** via `Recurrence.fires_on(when, effective_from)`
  in `domain/recurrence.py`. There are **no `day_of_week`/`day_of_month` columns**. Services call the enum
  method; they never `match` on the enum themselves.
- **`Recurrence` enum member *names* (`ONCE_ONLY`, …) are what's stored** in the DB and the schema `CHECK`
  set. Human display text is mapped in `web/rendering`, never persisted.
- **Categories are a user-managed table, not an enum** (decision D-012). Budgets, budget items, expenses,
  and commitments reference `category.id` by foreign key (`category_id`) — there is no `category IN (...)`
  CHECK, and no per-resource category column. The budget amount lives at the **category** level (a `Budget`
  has no name); a `BudgetItem` is a named label under a category with no amount; an `Expense` carries an
  optional `budget_item_id`. Per-category aggregates in services are keyed by `category_id`; only
  `web/rendering` resolves ids to display names. Deleting a category is blocked while it is in use.
- **Chart data is computed server-side and embedded** in the page as `<script type="application/json">`,
  not fetched via AJAX. Aggregation happens in services, never in JavaScript. `web/blueprints/api.py`
  exists only for genuine post-paint refetches (the expenses category filter), and returns data already
  shaped by a service. **JSON response shapes are public contract — changing one is a MAJOR SemVer bump.**

## Frontend design system (MANDATORY)

`docs/DESIGN.md` is the binding visual contract; it overrides any framework default.
Non-negotiables when touching templates or CSS:

- **Slate Navy (`--brand #2D3F5C`) is the most prominent colour** and anchors every page (at minimum the nav bar). The landing/cover uses a full Slate Navy header panel; inner pages step down the **tint waterfall** (`--brand-tint` → `--surface` → `--wash`) rather than repeating full Slate Navy.
- **Secondary palette (`--s1`…`--s5`) and all tints/shades are chart-only** — never backgrounds, never text. Tints step in 20% increments, 20–80%.
- **Sharp edges (`border-radius: 0`) and 1px borders.** Professional/corporate feel.
- **Inter only** (self-hosted in `web/static/fonts/`, no CDN): H1 ExtraLight/Light, sub-heads Light, intro Bold, body Regular. **Sentence case** headings; **text always left-aligned**; tight tracking (`-0.01em`).
- **White space is required** — don't fill the page; panels breathe.
- **At most four panels** per page. The 20-section grid is vertical rhythm — horizontal bands stacked down the page (the panel stack), **not** vertical columns; subdivide *within* a band flexibly (`.split`) but keep it balanced.
- Accessible contrast (WCAG AA) is mandatory; only approved colour combinations.
- Tokens + components live in `web/static/css/app.css`. New frontend libraries/fonts still need approval per the asset boundary.

## Process rules with teeth

- **MANDATORY: commits carry no authoring notes.** Commit messages and PR bodies must contain **no**
  `Co-Authored-By` trailers, no "Generated with Claude Code" lines, no tool/agent attribution of any kind.
  The message is the change and its rationale — nothing else. This overrides any default attribution
  behavior. No exceptions.
- **No new dependency without explicit user approval** — Python *or* frontend (CDN/npm/vendored), runtime
  *or* dev. Approved runtime set is `flask`, `sqlmodel`, `alembic`; dev tools `ruff`/`pytest`/`mypy`. Vendored
  frontend is fixed at Bootstrap 4, Chart.js, jQuery, Font Awesome (not yet vendored — see ROADMAP). New
  requests get logged in `docs/ROADMAP.md`'s decision register (D-008/D-009 record the SQLModel + Alembic adoption).
- **Every behavior change ships with tests.** See the change-to-test mapping table in `docs/DEVELOPMENT.md`
  (e.g. service tests use in-memory fake repos implementing the Protocol; bug fixes need a test that fails
  before and passes after).
- **No string-built SQL** — use the SQLModel/SQLAlchemy query API; any raw SQL binds parameters. ruff `S` rules catch f-string SQL.
- **Schema changes go through Alembic** — edit the models in `domain/records.py`, then `alembic revision --autogenerate`, and **review the script** (autogenerate misses CHECK constraints and custom-type imports).
- **Conventional Commits** (`feat:`/`fix:`/`refactor:`/`test:`/`docs:`/`chore:`/`perf:`). Assess SemVer
  impact before committing; user-facing changes need a `CHANGELOG.md` entry, and a version bump in
  `pyproject.toml` + annotated tag follows the mandatory ordered workflow in `docs/DEVELOPMENT.md`.
- **Out of scope for v1.0.0:** auth, multi-user isolation, multi-currency, timezones, CSV export. A `user`
  table is scaffold-only — no route touches it. Don't build "ghost" features.
