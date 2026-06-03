"""Contract test: implementations satisfy the runtime-checkable Protocol."""

from __future__ import annotations

import sqlite3

import pytest

from finance_web_app.core.contracts.budget_repository import BudgetRepository
from finance_web_app.infrastructure.persistence.budget_repository_sqlite import (
    SqliteBudgetRepository,
)

pytestmark = pytest.mark.unit


def test_sqlite_repository_satisfies_protocol() -> None:
    conn = sqlite3.connect(":memory:")
    try:
        assert isinstance(SqliteBudgetRepository(conn), BudgetRepository)
    finally:
        conn.close()


def test_fake_repository_satisfies_protocol(fake_budget_repository: object) -> None:
    assert isinstance(fake_budget_repository, BudgetRepository)
