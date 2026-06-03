"""Schema bootstrap and forward-only migration runner.

Implements the startup sequence in ``docs/OPERATIONS.md`` -> "Schema and
migrations":

1. If the database has no schema yet, apply ``schema.sql`` (the baseline, which
   stamps its own ``schema_version`` row).
2. Apply every migration script numbered higher than the current
   ``MAX(version)``, in lexical order. Each script is its own transaction and
   stamps its own ``schema_version`` row.
3. If a migration fails, roll back and abort loudly -- the app does not start in
   a half-migrated state.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_PERSISTENCE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = _PERSISTENCE_DIR / "schema.sql"
MIGRATIONS_DIR = _PERSISTENCE_DIR / "migrations"


def ensure_schema(
    conn: sqlite3.Connection,
    *,
    schema_path: Path = SCHEMA_PATH,
    migrations_dir: Path = MIGRATIONS_DIR,
) -> None:
    """Bring ``conn`` up to the current schema, applying baseline and migrations."""
    if not _schema_present(conn):
        conn.executescript(schema_path.read_text(encoding="utf-8"))
    _apply_pending_migrations(conn, migrations_dir)


def _schema_present(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_version'"
    ).fetchone()
    return row is not None


def _current_version(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return int(row[0]) if row[0] is not None else 0


def _apply_pending_migrations(conn: sqlite3.Connection, migrations_dir: Path) -> None:
    current = _current_version(conn)
    for path in sorted(migrations_dir.glob("[0-9]*.sql")):
        version = _version_of(path)
        if version <= current:
            continue
        try:
            conn.executescript(path.read_text(encoding="utf-8"))
        except sqlite3.Error as exc:
            conn.rollback()
            raise RuntimeError(f"migration {path.name} failed; database left unmigrated") from exc


def _version_of(path: Path) -> int:
    stem = path.name.split("_", 1)[0]
    try:
        return int(stem)
    except ValueError as exc:
        raise RuntimeError(f"migration filename must start with a number: {path.name}") from exc
