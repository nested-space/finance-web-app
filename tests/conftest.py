"""Shared test fixtures.

Per ``docs/DEVELOPMENT.md`` -> "Fixtures": an in-memory schema connection and a
temp-file path for repository tests, a Flask test client for web tests, and
dict-backed fake repositories for service tests so they never touch SQL.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from flask.testing import FlaskClient

from finance_web_app.application.services.budget_service import BudgetService
from finance_web_app.core.contracts.errors import NotFoundError
from finance_web_app.core.runtime.app_factory import create_app
from finance_web_app.domain.effective_period import EffectivePeriod
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import BudgetRecord, Category
from finance_web_app.infrastructure.persistence.bootstrap import ensure_schema
from finance_web_app.infrastructure.persistence.connection import connect


@pytest.fixture
def in_memory_sqlite() -> Iterator[sqlite3.Connection]:
    conn = connect(":memory:")
    ensure_schema(conn)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def tmp_sqlite_path(tmp_path: Path) -> Path:
    db_path = tmp_path / "finance.db"
    conn = connect(db_path)
    try:
        ensure_schema(conn)
    finally:
        conn.close()
    return db_path


@pytest.fixture
def flask_client(tmp_path: Path) -> FlaskClient:
    app = create_app(db_path=str(tmp_path / "finance.db"))
    app.config.update(TESTING=True)
    return app.test_client()


class FakeBudgetRepository:
    """In-memory ``BudgetRepository`` for service tests."""

    def __init__(self) -> None:
        self._rows: dict[int, BudgetRecord] = {}
        self._next_id = 1

    def list_all(self) -> list[BudgetRecord]:
        return [self._rows[key] for key in sorted(self._rows)]

    def list_effective(self, year: int, month: int) -> list[BudgetRecord]:
        return [b for b in self.list_all() if b.period.covers_month(year, month)]

    def get(self, budget_id: int) -> BudgetRecord:
        try:
            return self._rows[budget_id]
        except KeyError:
            raise NotFoundError("budget", budget_id) from None

    def create(self, record: BudgetRecord) -> BudgetRecord:
        stored = replace(record, id=self._next_id)
        self._rows[self._next_id] = stored
        self._next_id += 1
        return stored

    def delete(self, budget_id: int) -> None:
        if budget_id not in self._rows:
            raise NotFoundError("budget", budget_id)
        del self._rows[budget_id]


@pytest.fixture
def fake_budget_repository() -> FakeBudgetRepository:
    return FakeBudgetRepository()


@pytest.fixture
def budget_service(fake_budget_repository: FakeBudgetRepository) -> BudgetService:
    return BudgetService(fake_budget_repository)


@pytest.fixture
def seeded_repositories(
    fake_budget_repository: FakeBudgetRepository,
) -> dict[str, FakeBudgetRepository]:
    fake_budget_repository.create(
        BudgetRecord(
            name="Groceries",
            quantity=Money.from_pence(20000),
            category=Category.GROCERIES,
            period=EffectivePeriod(from_date=date(2026, 1, 1)),
        )
    )
    return {"budgets": fake_budget_repository}
