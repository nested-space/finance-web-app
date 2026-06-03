"""Dependency wiring -- the one seam that binds concrete repositories to services.

This is the only module permitted to import both a contract Protocol's concrete
implementation and the service that consumes it. It also owns the request-scoped
SQLite connection stored on Flask's ``g`` (``docs/ARCHITECTURE.md`` -> "Layer
map", "Runtime flow"). Plain factory wiring -- not a DI framework.
"""

from __future__ import annotations

import sqlite3

from flask import current_app, g

from finance_web_app.application.services.budget_service import BudgetService
from finance_web_app.infrastructure.persistence.budget_repository_sqlite import (
    SqliteBudgetRepository,
)
from finance_web_app.infrastructure.persistence.connection import connect


def get_connection() -> sqlite3.Connection:
    """Return the request-scoped connection, opening it on first use."""
    if "db" not in g:
        g.db = connect(current_app.config["DB_PATH"])
    connection: sqlite3.Connection = g.db
    return connection


def close_connection(_exception: BaseException | None = None) -> None:
    """Teardown hook: close the request-scoped connection if one was opened."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def get_budget_service() -> BudgetService:
    return BudgetService(SqliteBudgetRepository(get_connection()))
