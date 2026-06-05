"""Integration test: Alembic builds the schema and stores Money as INTEGER."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from finance_web_app.infrastructure.persistence.migrate import upgrade_to_head

pytestmark = pytest.mark.integration


def test_upgrade_head_creates_tables_and_integer_money(tmp_path: Path) -> None:
    db_path = tmp_path / "finance.db"
    upgrade_to_head(str(db_path))

    conn = sqlite3.connect(db_path)
    try:
        tables = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"category", "budget", "budget_item", "user", "alembic_version"} <= tables

        columns = {row[1]: row[2] for row in conn.execute("PRAGMA table_info(budget)")}
        assert columns["quantity"] == "INTEGER"

        version = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        assert version is not None and version[0]
    finally:
        conn.close()
