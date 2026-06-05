# finance_web_app

A single-user personal-finance tracker. Records budgets, expenses, recurring commitments, and recurring income streams; renders a monthly dashboard showing balance projection and category breakdowns.

Built with Flask and Jinja templates, backed by SQLite, server-rendered for everything except the canvas charts.

## Quick start

Requires Python 3.11 or newer and `git`.

```bash
git clone https://github.com/nested-space/finance-web-app.git
cd finance-web-app

python3 -m venv ~/.venvs/finance
source ~/.venvs/finance/bin/activate

pip install --upgrade pip
pip install -e .

flask --app finance_web_app.web run
```

The app serves on http://127.0.0.1:5000. On first run, an empty SQLite database is created at `~/.databases/finance/finance.db` (under your home directory, outside the working tree). Override with `FINANCE_DB_PATH` if you want it elsewhere; see [`docs/OPERATIONS.md`](docs/OPERATIONS.md) for the full env-var list.

For contributor setup (tests, linting, type checking) see [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

## Pages

| URL | What it does |
| --- | --- |
| `/` | Landing page. Click "Finance" to enter the app. |
| `/finance` | Monthly dashboard. Insights card plus four charts: finance model line, income-vs-outgoings bar, budget breakdown pie, commitments-by-category pie. |
| `/finance/budgets` | Add a budget, view current budgets, see spend-vs-budget charts and a 6-month history. |
| `/finance/expenses` | Add an expense, view this month's expenses split by category, filter the spend-vs-budget chart by category. |
| `/finance/commitments` | Add a recurring commitment (e.g. a subscription), view commitments grouped by recurrence. |
| `/finance/income` | Add a recurring income stream, view current income streams. |
| anything else | 404 page. |

## Forms reference

Every form below is a standard HTML POST. Submitting a valid form redirects back to the same page (POST-redirect-GET); the new row appears in the table.

### Budget — `POST /finance/budgets`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | text | yes | Free-form, non-empty. |
| `quantity` | number, step 0.01 | yes | Non-negative. Stored as integer pence. |
| `category` | select | yes | The expense category this budget caps. One of: `Occasional`, `Groceries`, `Clothing`, `Entertainment`, `Petrol`, `Kids`, `Christmas`. |
| `effective_from` | date | no | Defaults to today. |
| `effective_stop` | date | no | Must be on or after `effective_from`. |

### Expense — `POST /finance/expenses`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | text | yes | |
| `quantity` | number, step 0.01 | yes | Non-negative. |
| `date` | date | yes | The date the expense was incurred. |
| `category` | select | yes | One of: `Occasional`, `Groceries`, `Clothing`, `Entertainment`, `Petrol`, `Kids`, `Christmas`. |
| `description` | textarea | no | Free-form notes. |

### Commitment — `POST /finance/commitments`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | text | yes | |
| `quantity` | number, step 0.01 | yes | Non-negative. Stored as integer pence. |
| `category` | select | yes | One of: `Occasional`, `Groceries`, `Kids`, `Entertainment`, `Clothing`. |
| `recurrence` | select | yes | One of: `Once Only`, `Daily`, `Weekly`, `Monthly`, `Annual`. |
| `effective_from` | date | yes | Start of the commitment, and the anchor for *when* it fires: a `Weekly` commitment fires on this weekday, `Monthly` on this day-of-month, `Annual` on this month-and-day. There is no separate "day of week/month" field. |
| `length` | number | conditional | Required unless `recurrence` is `Once Only`. Combined with `length_unit` to compute `effective_stop`. |
| `length_unit` | select | conditional | One of: `Days`, `Weeks`, `Months`, `Years`. |

### Income — `POST /finance/income`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | text | yes | |
| `quantity` | number, step 0.01 | yes | Non-negative. Stored as integer pence. |
| `recurrence` | select | yes | One of: `Once Only`, `Daily`, `Weekly`, `Monthly`, `Quarterly`, `Annual`. |
| `effective_from` | date | yes | Start of the income stream, and the anchor for when it fires (same rule as commitments: `Weekly`→weekday, `Monthly`/`Quarterly`→day-of-month, `Annual`→month-and-day). |
| `effective_stop` | date | no | End of the income stream. Defaults to none (open-ended). Must be on or after `effective_from`. |

### Delete actions — `POST /finance/<resource>/<id>/delete`

Triggered by the trash icon on any row. Returns a redirect to the resource page; the row is gone.

## URL reference

### HTML routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Landing |
| `GET` | `/finance` | Dashboard |
| `GET` | `/finance/budgets` | Budgets page |
| `POST` | `/finance/budgets` | Create budget |
| `POST` | `/finance/budgets/<id>/delete` | Delete budget |
| `GET` | `/finance/expenses` | Expenses page |
| `POST` | `/finance/expenses` | Create expense |
| `POST` | `/finance/expenses/<id>/delete` | Delete expense |
| `GET` | `/finance/commitments` | Commitments page |
| `POST` | `/finance/commitments` | Create commitment |
| `POST` | `/finance/commitments/<id>/delete` | Delete commitment |
| `GET` | `/finance/income` | Income page |
| `POST` | `/finance/income` | Create income |
| `POST` | `/finance/income/<id>/delete` | Delete income |

### JSON routes (used by Chart.js)

Chart data for the *initial* render of each page is computed server-side and embedded in the page as a `<script type="application/json">` block — no AJAX round-trip, no aggregation in the browser. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) → "Frontend data delivery". The endpoints below exist only for interactions that change the data *after* first paint (month navigation, the expenses category filter). Each returns data already shaped by a service method; months are 1-indexed.

| Method | Path | Returns |
| --- | --- | --- |
| `GET` | `/finance/api/model/<year>/<month>` | The full `MonthlyModel` for the month: per-day income/commitments/expenses/budget series and the cumulative & subtractive balance series. Feeds the dashboard finance-model line chart on month navigation. |
| `GET` | `/finance/api/expenses/<year>/<month>` | Per-day cumulative expense spend and the straight-line budget allocation for the month, optionally filtered to one or more categories via repeated `category` query params (none = all). Feeds the expenses page's spend-vs-budget curve when the category filter changes. Returns `{labels, spend_cumulative, budget_cumulative}`. |

Response shapes match the service contracts in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). These shapes are part of the public contract — changing one is a MAJOR SemVer bump (see [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)).

## Documentation

| Document | Audience |
| --- | --- |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Contributors changing structural code |
| [`docs/DESIGN.md`](docs/DESIGN.md) | Anyone touching templates or CSS — the mandatory brand design system |
| [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) | Contributors writing or reviewing code |
| [`docs/OPERATIONS.md`](docs/OPERATIONS.md) | Anyone running, deploying, or backing up an instance |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Stakeholders and contributors deciding what to pick up |
| [`CHANGELOG.md`](CHANGELOG.md) | Anyone tracking what changed between versions |

## Versioning

The project follows Semantic Versioning. See [`CHANGELOG.md`](CHANGELOG.md) for release notes.
