"""SQLite connection helper.

Centralises the per-connection pragmas so every connection -- request-scoped or
test -- gets the same durability and integrity settings
(``docs/OPERATIONS.md`` -> "Data layout").
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with the project's standard pragmas applied."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn
