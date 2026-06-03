# Development

This document defines the engineering process for changing `finance_web_app`. Audience: anyone writing code in this repository. For *structural* questions, see `ARCHITECTURE.md`. For *running and deploying* an instance, see `OPERATIONS.md`.

## Local setup

Prerequisites: Python 3.11 or newer, `git`, `sqlite3` CLI (for inspecting the DB locally).

```bash
git clone https://github.com/nested-space/finance-web-app.git
cd finance-web-app

python3 -m venv ~/.venvs/finance
source ~/.venvs/finance/bin/activate

pip install --upgrade pip
pip install -e .[dev]
```

The repository uses the `src/` layout; `pip install -e .` exposes the package on `PYTHONPATH` and `pytest` is preconfigured with `pythonpath = ["src"]`. Activate the venv for every session.

Run the app locally (see `OPERATIONS.md` for environment variables):

```bash
flask --app finance_web_app.web run
```

Seed data: there is no bundled seed script (decision pending in `ROADMAP.md`). For exploratory work, create budgets/expenses/commitments/income through the UI; the SQLite file is small enough to delete and recreate at will.

## Mandatory quality gates

The following four commands are the merge gate. All four must exit zero on every change.

```bash
source ~/.venvs/finance/bin/activate

ruff format src/ tests/ --check
ruff check src/ tests/
PYTHONPATH=src pytest -q
MYPYPATH=src mypy src/ tests/
```

Gate policy:

- **No merge if any gate fails.** This is non-negotiable.
- **No bypass** of formatting, linting, type, or test failures. Fix the root cause.
- **No suppressing** warnings without explicit, documented justification in a comment alongside the suppression.
- A gate-only fix (e.g. ruff config change) is its own commit, not bundled with feature work.

The configuration for each tool is in `pyproject.toml`. Changing the configuration is itself a `chore:` commit that must pass the gates with the new config.

## Testing requirements

Every behavior change ships with tests.

### Change-to-test mapping

| Change type | Required test location | Style |
| --- | --- | --- |
| Blueprint route or response shape | `tests/integration/web/` | Flask test client |
| Form validation rule | `tests/unit/web/forms/` | Direct form instantiation |
| Service use case | `tests/unit/application/` | In-memory fake repository implementing the Protocol |
| Domain VO invariant | `tests/unit/domain/` | Direct construction; assert on `ValueError` for invalid inputs |
| Money pence conversion | `tests/unit/domain/` | Round-trip `Money` → pence → `Money`; assert exact equality |
| Recurrence math | `tests/unit/domain/test_recurrence.py` | Parametrise over recurrence × date examples, anchored on `effective_from` |
| SQLite repository | `tests/integration/persistence/` | Temp file-backed DB; full schema bootstrap |
| Contract/Protocol shape | `tests/unit/core/contracts/` | `assert isinstance(impl, BudgetRepository)` — requires the Protocol be `@runtime_checkable` |
| Bug fix | A test that *fails before the fix and passes after* — regardless of layer | Same location as the layer that owned the bug |

### Test layout

```
tests/
  unit/
    domain/
    application/
    web/forms/
    core/contracts/
  integration/
    web/
    persistence/
  conftest.py            # shared fixtures
```

### Fixtures

- `engine` — an in-memory SQLModel `Engine` with `metadata.create_all` applied. `session` — a `Session` bound to it. Used by integration repository tests.
- `flask_client` — yields a Flask test client wired to a temp-file DB; the app factory runs `alembic upgrade head` on creation. Used by integration web tests.
- `fake_budget_repository` (and siblings) — in-memory `dict`-backed implementations of each Protocol, returning model instances. Used in service tests so they never touch SQL. `budget_service` wraps one for convenience.
- `seeded_repositories` — fake repositories pre-populated with sample rows.

### Coverage expectations

There is no minimum coverage percentage. The expectation is qualitative: failure modes and edge cases are tested, not only happy paths. Reviews enforce this.

## Conventional Commits

Every commit subject begins with a type:

- `feat:` — new behavior visible to users.
- `fix:` — bug fix.
- `refactor:` — internal change with no behavior delta.
- `test:` — adding or restructuring tests with no production change.
- `docs:` — documentation only.
- `chore:` — build, tooling, config, deps.
- `perf:` — performance change with measurable evidence.

Examples:

```
feat: add monthly insight for largest single expense
fix: include records starting on the first of the month as effective
refactor: lift effective-period predicate into domain value object
docs: clarify migration safety in OPERATIONS.md
chore: bump ruff to 0.7 and re-run formatter
```

Breaking changes go in the body as `BREAKING CHANGE:` and trigger a MAJOR bump (see "SemVer workflow" below).

## PR checklist

Every PR description includes:

- **What changed and why** — one paragraph.
- **Tests** — what tests were added/updated, with the relevant test file(s).
- **Docs** — which docs were updated (`ARCHITECTURE.md`, `OPERATIONS.md`, etc.) and why, or "no docs change needed because ...".
- **SemVer impact** — `patch` / `minor` / `major` / `none (pre-release)`.
- **Boundary-impact statement** — which layers were touched. Use the layer names from `ARCHITECTURE.md`'s layer map.

A PR that crosses a layer boundary without justification is not approved.

## SemVer workflow

The project follows Semantic Versioning. `pyproject.toml`'s `version` is the canonical source.

SemVer impact assessment is mandatory before commit. Every user-visible change ships with a `CHANGELOG.md` entry and, if the version bumps, a matching tag.

| Bump | Triggers |
| --- | --- |
| MAJOR | Removing a route, changing a URL path, changing a JSON response shape, changing form-field semantics, dropping support for a Python version, schema migration that loses data. |
| MINOR | Adding a route, adding an optional form field, adding a chart, new opt-in env var. |
| PATCH | Bug fix, performance fix, doc update, internal refactor with no behavior delta. |

### The mandatory workflow for a SemVer bump

Complete in order, in one commit:

1. Update `version = "MAJOR.MINOR.PATCH"` in `pyproject.toml`.
2. Add a dated section to `CHANGELOG.md` describing all changes since the last release.
3. Run and pass all four quality gates.
4. Commit with a Conventional Commit subject describing the headline change.
5. Create an annotated git tag: `git tag -a vMAJOR.MINOR.PATCH -m "vMAJOR.MINOR.PATCH"`.
6. Push the commit and the tag.

Hard rules:

- Do not tag before all four gates pass.
- Do not ship a SemVer bump without a matching `CHANGELOG.md` entry and tag.
- Do not include unrelated changes in a SemVer bump commit. The bump commit contains only the version, the changelog, and any final fixes needed to make it green.

## Definition of Done

A change is done only when every statement below is true:

- All four quality gates pass.
- Layer boundaries are respected; no forbidden imports per `ARCHITECTURE.md`'s layer map.
- Tests exist for new behavior, and for any bug being fixed.
- Docs are updated at the correct boundary (route changes → `README.md`; layer changes → `ARCHITECTURE.md`; gate/workflow changes → this file; env/runtime changes → `OPERATIONS.md`; scope/decision changes → `ROADMAP.md`).
- `CHANGELOG.md` reflects user-facing impact.
- Version bump and tag are in place if SemVer impact is non-zero.
- No unresolved blockers remain (a failing gate, a pending decision, or an unanswered review comment all count as blockers).

## Security baseline

Security rules are non-optional and enforced by review.

- **No string-built SQL.** Queries go through the SQLModel/SQLAlchemy expression API, which binds parameters. Any raw SQL (e.g. a hand-written migration or a `exec_driver_sql` in a test) uses bound parameters, never f-string interpolation. Ruff's `S` rules catch `f`-string SQL and may not be disabled.
- **Validate at the boundary.** Forms reject malformed input. Services trust their domain VO inputs.
- **Fail securely.** Errors raised from `core/contracts/errors.py` are typed. The blueprint layer maps them to HTTP status codes; nothing surfaces a stack trace to the user.
- **Do not log payload.** Form values, query parameters, and DB row contents do not appear in logs. Log identifiers and outcomes, not data. See `OPERATIONS.md` → "Observability".
- **Static analysis as a backstop.** The ruff `S` rules and mypy's `strict` mode are part of the gate. A finding may not be silently `# noqa`'d.

## Adding dependencies

`pyproject.toml` is the canonical dependency declaration. The approved runtime set is `flask`, `sqlmodel` (→ SQLAlchemy + Pydantic), and `alembic`; dev tools are `ruff`, `pytest`, `mypy`.

- A new runtime dependency requires explicit user approval. This applies whether the dependency is Python, JavaScript, or CSS. See `ARCHITECTURE.md` → "Frontend asset boundary" for the rule.
- A new dev dependency (a tool used only by the gates or in tests) requires the same approval.
- The PR proposing the dependency includes the rationale, the alternative considered, and an entry in `ROADMAP.md`'s decision register.

Approval lives in the PR. There is no "approved deps" file.
