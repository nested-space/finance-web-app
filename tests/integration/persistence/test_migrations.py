"""Integration tests for the schema bootstrap and migration runner."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from finance_web_app.infrastructure.persistence.bootstrap import ensure_schema
from finance_web_app.infrastructure.persistence.connection import connect

pytestmark = pytest.mark.integration


def _max_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0])


def test_baseline_stamps_version_zero(in_memory_sqlite: sqlite3.Connection) -> None:
    assert _max_version(in_memory_sqlite) == 0


def test_migration_above_baseline_is_applied(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_add_marker.sql").write_text(
        "BEGIN;\n"
        "CREATE TABLE marker (note TEXT);\n"
        "INSERT INTO schema_version (version) VALUES (1);\n"
        "COMMIT;\n",
        encoding="utf-8",
    )
    conn = connect(":memory:")
    try:
        ensure_schema(conn, migrations_dir=migrations)
        assert _max_version(conn) == 1
        marker = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='marker'"
        ).fetchone()
        assert marker is not None
    finally:
        conn.close()


def test_failing_migration_aborts_loudly(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_broken.sql").write_text(
        "BEGIN;\nINSERT INTO does_not_exist (x) VALUES (1);\nCOMMIT;\n",
        encoding="utf-8",
    )
    conn = connect(":memory:")
    try:
        with pytest.raises(RuntimeError):
            ensure_schema(conn, migrations_dir=migrations)
    finally:
        conn.close()
