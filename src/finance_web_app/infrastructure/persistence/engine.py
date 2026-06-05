"""Engine and session construction.

Centralises the SQLAlchemy engine and the per-connection pragmas (applied via a
``connect`` event so they cover every pooled connection), and the URL derivation
shared by the app and Alembic (``docs/OPERATIONS.md`` -> "Data layout").
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, event
from sqlmodel import Session, create_engine

# Default location of the production SQLite database. Lives under the user's home
# (``~/.databases/finance/finance.db``) so it is outside the working tree and
# never confused with a test or scratch DB. Override with ``FINANCE_DB_PATH``.
DEFAULT_DB_PATH = str(Path.home() / ".databases" / "finance" / "finance.db")


def database_url(db_path: str) -> str:
    """Build a SQLite URL from a filesystem path (or ``:memory:``)."""
    if db_path == ":memory:":
        return "sqlite://"
    return f"sqlite:///{db_path}"


def make_engine(db_path: str) -> Engine:
    engine = create_engine(database_url(db_path))

    @event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_connection: Any, _record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.close()

    return engine


def make_session(engine: Engine) -> Session:
    # expire_on_commit=False keeps committed instances usable after the request
    # scope closes (templates read them), avoiding DetachedInstanceError.
    return Session(engine, expire_on_commit=False)
