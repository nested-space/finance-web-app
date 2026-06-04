# Roadmap

This document describes the product direction for `finance_web_app`. Audience: stakeholders deciding what to fund, contributors deciding what to pick up, reviewers deciding what is in or out of scope. For *how the layers fit together*, see `ARCHITECTURE.md`. For *the engineering process*, see `DEVELOPMENT.md`.

This file does not contain coding rules or operational instructions. If you find a normative "you must do X" statement here, it is misplaced — move it to the document whose contract owns that concern.

## Current state

Under construction. The documentation suite — `README.md`, `ARCHITECTURE.md`, `OPERATIONS.md`, `DEVELOPMENT.md`, this file, and `CHANGELOG.md` — remains the design contract; implementation proceeds in vertical-slice cycles (see "Build phasing" below).

**Cycle 1 — Budgets walking skeleton (landed).** The Budgets resource is implemented end-to-end through every layer in `ARCHITECTURE.md` — domain value objects, the repository Protocol, a SQLite repository, schema bootstrap plus a forward-only migration runner, the service, form, blueprint, rendering, and templates — alongside the landing page, a 404 handler, the app factory + container, and the full test pyramid. The app runs (`flask --app finance_web_app.web run`) and persists budgets. The other three resources, the dashboard finance model, and the charts are not built yet.

The reference behavior comes from a prior Node/Express/EJS/MongoDB implementation (not included in this repository). It serves as **a capability reference, not a runtime dependency** — the Python build documents the corrected behaviour directly (see `ARCHITECTURE.md` → "Bug-fix decisions") rather than relying on the old source being present.

### Build phasing

Implementation lands as vertical slices rather than all of v1.0.0 at once: the most complex piece (the finance model and the embedded-JSON chart contract) is built only after the layer stack has been proven against running code. This is sequencing, not a timeline; each cycle leaves `main` green against all four quality gates.

- **C1 — Budgets walking skeleton (done).** One resource through every layer, plus app/DB/test scaffolding, so later resources are pattern-repetition. Tables only. **Subsequently re-platformed onto SQLModel + Alembic** (D-008/D-009): models are canonical, repositories extend a generic SQLModel base, and Alembic owns the schema. The frontend now implements the **brand design system** (D-010, `docs/DESIGN.md`): Slate Navy palette, panels, sharp edges, self-hosted Inter.
- **C2 — Remaining resources (done).** Expenses, commitments, and income shipped, each a ~budgets-sized slice off the generic base repository (one Alembic migration per resource). Adds `Recurrence` + `Recurrence.fires_on` (`domain/recurrence.py`, `calendar_math.py`) and the `income_exception` child table (FK cascade, repo methods) — both fully tested, no UI yet (the exceptions-creation UI is open: D-011). Commitments compute `effective_stop` from length + unit; income supports Quarterly + open-ended streams. Still tables only.
- **C3a — Finance model, insights, and dashboard (done).** `FinanceModelService` + `MonthlyModel`, `InsightsService`, and the `/finance` dashboard with the four documented charts and month navigation. Introduces the embedded-JSON delivery contract (`web/rendering/json_response.py`) + `/finance/api/model`, and vendors **Chart.js** (chart colours from the secondary palette per `docs/DESIGN.md`). Balance series are signed `Decimal`; `subtractive_balance` exists but there is no opening-balance UI (a future item).
- **C3b — Per-page charts (done).** Budgets page (per-category spend-vs-budget bar, budget breakdown pie, 6-month cumulative budget-vs-spend line) and expenses page (cumulative spend-vs-budget curve filterable via `/finance/api/expenses`, spend breakdown pie, 6-month cumulative spend line). **This completes the documented v1.0.0 page/chart scope.**

A `1.0.0` tag is **not** cut automatically — it's a release decision. Remaining before a confident 1.0.0: resolve the production runner (D-001) and decide on the open items (seed data D-003, income-exceptions UI D-011). The opening-balance feature (`subtractive_balance` exists, no UI) is post-1.0.0.

## Capability scope for v1.0.0

Version 1.0.0 ships when all of the below are true and the quality gates pass.

### Pages

| URL | What it does |
| --- | --- |
| `/` | Landing page with a single working button: "Finance". |
| `/finance` | Monthly dashboard for the current month: insights card, finance-model line chart, income-vs-outgoings bar chart, budget breakdown pie, commitments-by-category pie. |
| `/finance/budgets` | Create-budget form, three charts (spend-vs-budget bar, breakdown pie, 6-month history line), table of current budgets. |
| `/finance/expenses` | Create-expense form, category-filterable spend-vs-budget line chart, breakdown pie, 6-month history line, table of current-month expenses. |
| `/finance/commitments` | Create-commitment form (with conditional length fields hidden when "Once Only"), table grouped by recurrence. |
| `/finance/income` | Create-income form, table of current income streams. |
| `*` | 404 page. |

### Resources

Four CRUD resources, all unscoped (single-user). Schema documented in `ARCHITECTURE.md` and `OPERATIONS.md`.

- Budgets — `name`, `quantity`, `category`, `effective_from`, `effective_stop`. The `category` ties a budget to the expense category it caps, so spend-vs-budget is a real comparison.
- Expenses — `name`, `quantity`, `date`, `category`, optional `description`.
- Commitments — `name`, `quantity`, `category`, `recurrence`, `effective_from`, optional `effective_stop`. When the commitment fires is derived from `effective_from` (no separate day-of-week/month fields).
- Income — same as commitments (minus `category`, plus `Quarterly`) with a one-to-many `income_exception` child table.

Categories for expenses and commitments are a fixed dropdown set, matching the reference implementation:

- Expenses: `Occasional`, `Groceries`, `Clothing`, `Entertainment`, `Petrol`, `Kids`, `Christmas`.
- Commitments: `Occasional`, `Groceries`, `Kids`, `Entertainment`, `Clothing`.

### Persistence

Single SQLite file. Forward-only migrations. WAL journal mode. No external database service.

### Frontend

Server-rendered Jinja templates for all tables, summaries, and form responses. Custom CSS implementing the mandatory brand design system in `docs/DESIGN.md` (Slate Navy palette, sharp edges, panels, self-hosted Inter); no CSS framework. Chart.js (vendored with the charts cycle) for canvas visualisations on the dashboard, budgets, and expenses pages — the only place the secondary palette appears. POST-redirect-GET for create and delete actions.

### Out of v1.0.0

- Authentication.
- Multi-user data isolation.
- Time zone localisation.
- Multi-currency support.
- CSV export, alerts, integrations.
- Any frontend or Python dependency not already named.

## Scaffold-only seams

These exist in the codebase to keep the eventual addition cheap, but are not wired into any user-facing flow in v1.0.0. They have **no functional behavior** until separately scoped work happens.

- **User account table.** A `user` table appears in the SQLite schema with `id`, `username`, `password_hash`, `created`. No route reads from or writes to it. No password hashing helper is implemented in v1.0.0 — when auth is scoped, the implementer chooses a hashing library, subject to dependency approval (see decision register below).

No other "ghost" features are permitted. A capability is either *in* v1.0.0 or *out* — partial implementations do not earn their place in `main`.

## Future priorities

The list below is not a commitment to a timeline. It describes the kind of work that would plausibly land after v1.0.0, in rough priority order. Pulling any item forward requires its own scope discussion.

1. **Authentication and session management.** Wire the existing `user` table into a login flow. Add `user_id` foreign keys to all resource tables in a forward migration. Per-user data isolation in every repository query.
2. **CSRF protection.** Required as soon as authenticated sessions exist. Approach (hand-rolled token vs. a library) is in the decision register.
3. **CSV export.** A per-resource "Download as CSV" link. Server-rendered, no JS.
4. **Net-worth page.** Aggregates budgets, expenses, commitments, and income across multiple months. Requires extending `FinanceModelService` to span a date range, not a single month.
5. **Budget alerts.** Notify when a category exceeds X% of its budget partway through the month. Requires a notification surface (initially: a banner on the dashboard).
6. **Localisation.** Time zones, currency, and number formatting. Likely the largest single piece of post-v1.0.0 work.
7. **Theming.** Replace the current Bootstrap 4 palette overrides with a small CSS variable set. No new dependencies.
8. **Mobile-friendly forms.** The Bootstrap grid handles layout, but date pickers and number inputs deserve a second look on touch devices.

## Non-goals

The following are deliberately *not* on the roadmap. Adding them would change the shape of the product enough that we would treat the result as a different project.

- **Banking-API integration** (Open Banking, Plaid, etc.). The app is a manual tracker by design.
- **Multi-tenant SaaS hosting.** A single Python process backed by a single SQLite file is the deployment model.
- **Native mobile clients** (iOS, Android, React Native, etc.). Responsive web only.
- **Real-time collaboration.** Single-user app.
- **Forecasting models beyond the linear projections in `FinanceModelService`.** Statistical or ML-based forecasts are out of scope.

## Decision register

Decisions that are *open* and require the user's explicit input before they can be resolved.

| ID | Decision | Status | Notes |
| --- | --- | --- | --- |
| D-001 | Production WSGI runner (gunicorn vs. waitress vs. defer) | Open | Not needed for local dev. Resolve before first remote deploy. Adding a runner is a new runtime dependency and needs approval. |
| D-002 | CSRF approach (Flask-WTF vs. hand-rolled token) | Open — gated on D-004 | Only relevant once authenticated sessions exist. |
| D-003 | Bundle a seed-data SQL script for first-run? | Open | Convenience for local dev. No security implication. |
| D-004 | Add Flask-WTF (or any form-handling library) at all? | Open | A new runtime dependency. **Requires user approval before introducing.** Until resolved, forms are hand-rolled. |
| D-005 | Logging library — stdlib `logging` vs. `structlog` | Resolved (interim) | Default is stdlib for v1.0.0. Reopen if structured logs become necessary in production. |
| D-006 | Password hashing library when auth is scoped | Open — gated on auth work | Candidates include `werkzeug.security` (already transitively available via Flask) and `bcrypt`. **Requires user approval before introducing a new dependency.** |
| D-007 | Provide a seed-data fixture for tests? | Resolved | Yes — `tests/conftest.py` exposes a `seeded_repositories` fixture. No production seed yet (see D-003). |
| D-008 | Adopt SQLModel (SQLAlchemy + Pydantic) as the ORM, with models as the schema source of truth? | Resolved — approved | **Reverses the original raw-`sqlite3` pre-build decision.** Approved to remove CRUD duplication ahead of C2. Repositories keep their Protocols and extend a generic SQLModel base. `Money`/`EffectivePeriod` are retained as value objects. |
| D-009 | Migration tool now that models are canonical (Alembic vs. `create_all`)? | Resolved — approved | Alembic. Retires `schema.sql`, the custom runner, and `schema_version`. `upgrade head` runs on startup; preserves the forward-only / abort-loudly model in `OPERATIONS.md`. |
| D-010 | Brand design system + self-hosted Inter typeface | Resolved — approved | Mandatory visual contract in `docs/DESIGN.md` (Slate Navy palette, sharp edges, panels/grid, white space, accessible combinations). Implemented as custom CSS; **Inter** is self-hosted under `web/static/fonts/` (approved font, no CDN). Supersedes the earlier Bootstrap-default styling assumption. |
| D-011 | How are income exceptions *created* — UI, import, or admin-only? | Open | C2 built the `income_exception` table + repo methods (read/write) so the C3 finance model can apply exceptions, but no create-exception UI exists; nothing in the spec describes one. Resolve before exceptions can be entered by a user. |

Every entry above maps to a rule, not a preference. The relevant rule is: **adding any frontend or Python dependency beyond those named in `ARCHITECTURE.md` requires explicit user approval, recorded as a decision in this register.** A PR that introduces an undeclared dependency does not pass review. The approved runtime set is now `flask`, `sqlmodel`, and `alembic`.

Closed decisions move out of the table once they have been recorded in `CHANGELOG.md`.
