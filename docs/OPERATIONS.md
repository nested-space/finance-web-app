# Operations

This document covers running, deploying, backing up, and troubleshooting a `finance_web_app` instance. Audience: operators (often the same person as the user). For *how the layers fit together*, see `ARCHITECTURE.md`. For *how to contribute code*, see `DEVELOPMENT.md`.

## Process model

`finance_web_app` is a single-process Flask application. There is no separate API server, no background worker, and no client-side build step.

| Environment | Command | Notes |
| --- | --- | --- |
| Local development | `flask --app finance_web_app.web run` | Auto-reloader on; serves on 127.0.0.1:5000. |
| Production | *Decision pending — see `ROADMAP.md`* | A WSGI runner (gunicorn or waitress) will front the app. The choice is open until first deploy. |

The Flask debug server is **not** acceptable for production use.

## Environment variables

All operational configuration is via environment variables. There is no config file.

| Variable | Default | Required | Purpose |
| --- | --- | --- | --- |
| `FINANCE_DB_PATH` | `./data/finance.db` | No | Filesystem path to the SQLite database. Parent directory is created on first run if absent. |
| `FINANCE_SECRET_KEY` | *unset* | Only when sessions are added | Flask session-signing key. v1.0.0 has no auth, so this is unused. Set before any session-bearing feature ships. |
| `FINANCE_LOG_LEVEL` | `INFO` | No | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`. Applied to the root logger at startup. |
| `FLASK_DEBUG` | `0` | No | `1` enables debug pages and the reloader. Never set this in production. |

Variables not listed above are not read. Spurious env vars do not affect behavior.

## Data layout

One SQLite file holds everything. There is no separate cache, no Redis, no message queue.

```
$FINANCE_DB_PATH         # default ./data/finance.db
$FINANCE_DB_PATH-wal     # write-ahead log (managed by SQLite, do not touch)
$FINANCE_DB_PATH-shm     # shared memory file (managed by SQLite, do not touch)
```

Connection settings applied per connection in `infrastructure/persistence/connection.py`:

- `PRAGMA foreign_keys = ON` — enforces the `income_exception.income_id` cascade and any future FKs.
- `PRAGMA journal_mode = WAL` — readers don't block writers; safer crash recovery.
- `PRAGMA synchronous = NORMAL` — durable enough for a single-user app, faster than `FULL`.

Column conventions an operator should know when inspecting the DB by hand:

- **Money is stored as `INTEGER` pence**, never a float. A row showing `quantity = 1299` is £12.99. Do not expect a decimal point in the DB. This avoids floating-point rounding error in the per-day balance maths.
- **Date columns hold ISO-8601 date strings (`YYYY-MM-DD`)**; only `created` holds a datetime (`YYYY-MM-DD HH:MM:SS`, UTC). Comparisons in queries rely on this lexical ordering, so do not write a datetime into a date column.
- **The schema ships with no secondary indexes.** At single-user scale (tens-to-hundreds of rows) a full table scan is faster than maintaining an index. If a future query genuinely needs one, add it in a forward migration with measured evidence — do not add indexes speculatively.

## Schema and migrations

The canonical schema lives at `src/finance_web_app/infrastructure/persistence/schema.sql`. It is the *current state* — not history.

Forward-only migrations live at `src/finance_web_app/infrastructure/persistence/migrations/NNN_short_name.sql`, numbered from `001` and applied in lexical order.

A `schema_version` table records the highest migration number that has been applied:

```sql
CREATE TABLE schema_version (
    version     INTEGER NOT NULL PRIMARY KEY,
    applied_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

On startup, `core/runtime/app_factory.py`:

1. Opens a connection to `FINANCE_DB_PATH`.
2. If the file does not exist, runs `schema.sql`. That script stamps its own baseline `schema_version` row (the highest migration number folded into the current-state schema — `0` at v1.0.0). The runner does **not** insert a version separately, so a fresh DB is never re-migrated through changes it already contains.
3. Whether the file was just created or already existed, the runner reads `MAX(version)` from `schema_version` and applies any migration scripts numbered higher, in lexical order, each in its own transaction; each script inserts its own `schema_version` row.
4. If a migration script fails, the transaction rolls back and startup **aborts loudly** — the operator must intervene. The app does not start in a half-migrated state.

The invariant tying these together: `schema.sql` always represents the current state and therefore stamps the same version that the last migration folded into it would have. When you add a migration, you do *not* also edit the baseline number in `schema.sql` unless you are simultaneously folding that migration into the baseline.

There is no rollback path. To "undo" a migration in production, restore from backup.

## Backup and restore

SQLite gives you a one-file backup, which is the whole point.

**Backup (online — app may be running):**

```bash
sqlite3 "$FINANCE_DB_PATH" ".backup ./backup-$(date -Iseconds).db"
```

This uses the SQLite online-backup API and is safe with concurrent writers.

**Backup (cold — app stopped):** Just copy the file.

```bash
cp "$FINANCE_DB_PATH" ./backup.db
```

**Restore:**

1. Stop the app.
2. `cp ./backup.db "$FINANCE_DB_PATH"`. Also remove any stale `-wal` and `-shm` files in the same directory.
3. Start the app. Startup will run any pending migrations against the restored data.

## Operational safety

SQLite's transactional guarantees cover atomicity and durability for single-row writes. The application's responsibilities on top of that:

- **No string-built SQL.** Every `execute()` call uses parameter binding. The ruff configuration includes `S` (bandit) rules to catch `f`-string SQL.
- **Input validation at the boundary.** Form classes in `web/forms/` reject malformed input before it reaches a service. Services trust their domain VO inputs and do not re-validate types.
- **Resource limits.** Flask is single-threaded by default in dev. In production, the WSGI runner will be configured for a single user — workers `>= 2` is overkill but harmless.

## Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `sqlite3.OperationalError: unable to open database file` at startup | Parent directory of `FINANCE_DB_PATH` does not exist or is not writable | Create the directory; check permissions. |
| `sqlite3.OperationalError: database is locked` under load | Another process is writing | Confirm no second app instance is running; WAL mode should make this rare. |
| Startup aborts with "schema version ahead of code" | An older binary is opening a DB that has been migrated by a newer one | Roll the binary forward, or restore an older backup. |
| Foreign-key violation when deleting an income with exceptions | `income_exception` rows referencing the income | Should not happen — cascade is defined in schema. If it does, file a bug; do not manually `PRAGMA foreign_keys = OFF`. |
| 500 on `/finance` with "static file not found" | Vendored library missing from `web/static/` after a partial deploy | Re-deploy; the static assets are part of the application package. |
| 404 on every page | Blueprint not registered, or `--app` argument wrong | Verify `flask --app finance_web_app.web run` and that `web/__init__.py` registers all blueprints. |
| Charts render empty | API endpoint returned 4xx/5xx | Open browser devtools; check `/finance/api/...` response; check server log for traceback. |

## Observability

Logging is via Python's stdlib `logging`. Output goes to stdout.

- Log level controlled by `FINANCE_LOG_LEVEL`.
- Each request logs one line at `INFO`: method, path, status, duration_ms.
- Exceptions log at `ERROR` with traceback.
- **What is never logged:** form-field values (could contain personally meaningful amounts or names), full DB file paths, SQL query bodies. Generic descriptions only (e.g. "create budget failed", not "create budget {'name': ..., 'quantity': ...} failed").

There is no metrics or tracing integration in v1.0.0. If needed, the seam is `core/runtime/app_factory.py` where Flask's `before_request` / `after_request` hooks are registered.
