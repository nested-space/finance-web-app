-- finance_web_app — canonical SQLite schema (proposed for v1.0.0)
--
-- This file represents the *current state* of the schema. It is run once on
-- first startup against an empty database. Subsequent schema changes ship as
-- numbered forward-only scripts under migrations/.
--
-- Design choices (see docs/ARCHITECTURE.md and docs/OPERATIONS.md for rationale):
--
--   * INTEGER PRIMARY KEY for surrogate ids (SQLite ROWID alias — fastest).
--   * MONEY IS STORED AS INTEGER MINOR UNITS (pence), never REAL. Floating
--     point reintroduces exactly the rounding error the domain Money(Decimal)
--     value object exists to prevent, and per-day sums in FinanceModelService
--     would accumulate it. Repositories convert Money <-> int pence at the
--     persistence boundary.
--   * DATE columns use ISO-8601 date strings ('YYYY-MM-DD') and default to
--     date('now'). Only `created` is a true timestamp and uses datetime('now').
--     Mixing date-only form input with datetime defaults in one column breaks
--     the string comparisons that drive EffectivePeriod.covers_month.
--   * recurrence/category columns store STABLE CODES (e.g. 'ONCE_ONLY',
--     'GROCERIES'), not display text. Display strings live in web/rendering.
--     Re-wording a label must never require a data migration. The codes mirror
--     the domain enums, which are the single source of truth (docs/ARCHITECTURE.md).
--   * Recurrence day-of-* fields are NOT stored. A recurring record fires
--     relative to its own effective_from (Monthly -> that day-of-month, Weekly
--     -> that weekday, Annual -> that month+day, Once Only -> that date). See
--     docs/ARCHITECTURE.md -> "FinanceModelService contract". This removes a
--     whole class of "field doesn't apply to this recurrence" invariants.
--   * Categories are CHECK-constrained to the fixed v1.0.0 set. Per
--     docs/ROADMAP.md, user-defined categories are out of scope for v1.0.0;
--     when that lands, the CHECK is replaced by a foreign key to a category
--     table in a forward migration.
--   * No secondary indexes. The tables hold tens-to-hundreds of rows for a
--     single user; a full scan beats an index at this scale and avoids write
--     overhead. Add indexes in a forward migration if a real query ever needs
--     one (and bring evidence — see docs/OPERATIONS.md).
--   * Connection-level pragmas (foreign_keys=ON, journal_mode=WAL,
--     synchronous=NORMAL) are applied in
--     infrastructure/persistence/connection.py per docs/OPERATIONS.md, not
--     here, so they apply to every connection rather than only schema
--     bootstrap.

BEGIN;

-- ---------------------------------------------------------------------------
-- schema_version
--   Records the highest migration number embodied by the database. This file
--   IS the baseline (version 0); it stamps its own version. The startup
--   migration runner then applies any migration scripts numbered higher than
--   MAX(version) and each inserts its own row. Because schema.sql already
--   reflects the current state, the baseline it stamps must equal the latest
--   migration folded into it — currently none, so 0. See docs/OPERATIONS.md.
-- ---------------------------------------------------------------------------
CREATE TABLE schema_version (
    version    INTEGER NOT NULL PRIMARY KEY,
    applied_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO schema_version (version) VALUES (0);

-- ---------------------------------------------------------------------------
-- budget
--   A monthly spending cap for a category, effective over the date range
--   [effective_from, effective_stop]. effective_stop NULL means "no end date".
--   `category` ties the budget to the expense category it caps, so the
--   "spend vs budget" and "budget breakdown" views are a real join rather than
--   an implicit match on name.
-- ---------------------------------------------------------------------------
CREATE TABLE budget (
    id             INTEGER NOT NULL PRIMARY KEY,
    name           TEXT    NOT NULL,
    quantity       INTEGER NOT NULL,                       -- pence
    category       TEXT    NOT NULL,
    created        TEXT    NOT NULL DEFAULT (datetime('now')),
    effective_from TEXT    NOT NULL DEFAULT (date('now')),
    effective_stop TEXT,

    CHECK (length(name) > 0),
    CHECK (quantity >= 0),
    CHECK (category IN (
        'OCCASIONAL', 'GROCERIES', 'CLOTHING', 'ENTERTAINMENT',
        'PETROL',     'KIDS',      'CHRISTMAS'
    )),
    CHECK (effective_stop IS NULL OR effective_stop >= effective_from)
);

-- ---------------------------------------------------------------------------
-- expense
--   A one-off spend with an explicit date and a fixed-set category.
-- ---------------------------------------------------------------------------
CREATE TABLE expense (
    id          INTEGER NOT NULL PRIMARY KEY,
    name        TEXT    NOT NULL,
    quantity    INTEGER NOT NULL,                          -- pence
    description TEXT,
    category    TEXT    NOT NULL,
    date        TEXT    NOT NULL DEFAULT (date('now')),
    created     TEXT    NOT NULL DEFAULT (datetime('now')),

    CHECK (length(name) > 0),
    CHECK (quantity >= 0),
    CHECK (category IN (
        'OCCASIONAL', 'GROCERIES', 'CLOTHING', 'ENTERTAINMENT',
        'PETROL',     'KIDS',      'CHRISTMAS'
    ))
);

-- ---------------------------------------------------------------------------
-- commitment
--   A recurring outgoing (e.g. subscription). When it fires is derived from
--   effective_from by domain.recurrence.Recurrence.fires_on — see
--   docs/ARCHITECTURE.md -> "FinanceModelService contract":
--     DAILY      — every day.
--     WEEKLY     — on the weekday of effective_from.
--     MONTHLY    — on the day-of-month of effective_from (clamped to month end).
--     ANNUAL     — on the month+day of effective_from.
--     ONCE_ONLY  — exactly on effective_from.
--   Commitments do not support QUARTERLY (income does).
-- ---------------------------------------------------------------------------
CREATE TABLE commitment (
    id             INTEGER NOT NULL PRIMARY KEY,
    name           TEXT    NOT NULL,
    quantity       INTEGER NOT NULL,                       -- pence
    category       TEXT    NOT NULL,
    recurrence     TEXT    NOT NULL,
    effective_from TEXT    NOT NULL DEFAULT (date('now')),
    effective_stop TEXT,
    created        TEXT    NOT NULL DEFAULT (datetime('now')),

    CHECK (length(name) > 0),
    CHECK (quantity >= 0),
    CHECK (category IN (
        'OCCASIONAL', 'GROCERIES', 'KIDS', 'ENTERTAINMENT', 'CLOTHING'
    )),
    CHECK (recurrence IN ('DAILY', 'WEEKLY', 'MONTHLY', 'ANNUAL', 'ONCE_ONLY')),
    CHECK (effective_stop IS NULL OR effective_stop >= effective_from)
);

-- ---------------------------------------------------------------------------
-- income
--   A recurring income stream. Same recurrence shape as commitment, plus
--   QUARTERLY (which commitments do not support — see docs/ROADMAP.md).
--   When it fires is derived from effective_from exactly as for commitment;
--   QUARTERLY fires on the day-of-month of effective_from every third month.
--   One-off overrides for specific dates live in income_exception.
-- ---------------------------------------------------------------------------
CREATE TABLE income (
    id             INTEGER NOT NULL PRIMARY KEY,
    name           TEXT    NOT NULL,
    quantity       INTEGER NOT NULL,                       -- pence
    recurrence     TEXT    NOT NULL,
    effective_from TEXT    NOT NULL DEFAULT (date('now')),
    effective_stop TEXT,
    created        TEXT    NOT NULL DEFAULT (datetime('now')),

    CHECK (length(name) > 0),
    CHECK (quantity >= 0),
    CHECK (recurrence IN ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'ANNUAL', 'ONCE_ONLY')),
    CHECK (effective_stop IS NULL OR effective_stop >= effective_from)
);

-- ---------------------------------------------------------------------------
-- income_exception
--   A one-off override for a recurring income stream on a specific date.
--   Per docs/ARCHITECTURE.md -> "FinanceModelService contract", on a date with
--   a matching exception, the exception's quantity REPLACES the recurring
--   amount (it does not add to it).
--
--   ON DELETE CASCADE: removing an income deletes its exceptions.
-- ---------------------------------------------------------------------------
CREATE TABLE income_exception (
    id        INTEGER NOT NULL PRIMARY KEY,
    income_id INTEGER NOT NULL REFERENCES income(id) ON DELETE CASCADE,
    date      TEXT    NOT NULL,
    quantity  INTEGER NOT NULL,                            -- pence
    reason    TEXT,

    CHECK (quantity >= 0),
    UNIQUE (income_id, date)
);

-- ---------------------------------------------------------------------------
-- user
--   SCAFFOLD ONLY for v1.0.0 — see docs/ROADMAP.md -> "Scaffold-only seams".
--   No route reads from or writes to this table in v1.0.0. The column shape
--   is fixed in advance so that adding auth in a future release does not
--   require a destructive migration. password_hash is intentionally generic
--   (no algorithm encoded) — the hashing library choice is open (D-006).
-- ---------------------------------------------------------------------------
CREATE TABLE user (
    id            INTEGER NOT NULL PRIMARY KEY,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created       TEXT    NOT NULL DEFAULT (datetime('now')),

    CHECK (length(username) > 0),
    CHECK (length(password_hash) > 0)
);

COMMIT;
