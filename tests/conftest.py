"""Shared test fixtures.

An in-memory engine/session with the schema applied for repository tests, a Flask
test client (wired to a temp-file DB, migrated by the app factory) for web tests,
and dict-backed fake repositories for service tests so they never touch SQL
(``docs/DEVELOPMENT.md`` -> "Fixtures").
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from flask.testing import FlaskClient
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel

from finance_web_app.application.services.budget_service import BudgetService
from finance_web_app.application.services.expense_service import ExpenseService
from finance_web_app.core.contracts.errors import NotFoundError
from finance_web_app.core.runtime.app_factory import create_app
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Budget, Category, Expense
from finance_web_app.infrastructure.persistence.engine import make_engine, make_session


@pytest.fixture
def engine() -> Iterator[Engine]:
    eng = make_engine(":memory:")
    SQLModel.metadata.create_all(eng)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with make_session(engine) as db_session:
        yield db_session


@pytest.fixture
def flask_client(tmp_path: Path) -> FlaskClient:
    app = create_app(db_path=str(tmp_path / "finance.db"))
    app.config.update(TESTING=True)
    return app.test_client()


class FakeBudgetRepository:
    """In-memory ``BudgetRepository`` for service tests."""

    def __init__(self) -> None:
        self._rows: dict[int, Budget] = {}
        self._next_id = 1

    def list_all(self) -> list[Budget]:
        return [self._rows[key] for key in sorted(self._rows)]

    def list_effective(self, year: int, month: int) -> list[Budget]:
        return [b for b in self.list_all() if b.period.covers_month(year, month)]

    def get(self, budget_id: int) -> Budget:
        try:
            return self._rows[budget_id]
        except KeyError:
            raise NotFoundError("budget", budget_id) from None

    def create(self, record: Budget) -> Budget:
        record.id = self._next_id
        self._rows[self._next_id] = record
        self._next_id += 1
        return record

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


class FakeExpenseRepository:
    """In-memory ``ExpenseRepository`` for service tests."""

    def __init__(self) -> None:
        self._rows: dict[int, Expense] = {}
        self._next_id = 1

    def list_all(self) -> list[Expense]:
        return [self._rows[key] for key in sorted(self._rows)]

    def list_effective(self, year: int, month: int) -> list[Expense]:
        return [e for e in self.list_all() if e.in_month(year, month)]

    def get(self, expense_id: int) -> Expense:
        try:
            return self._rows[expense_id]
        except KeyError:
            raise NotFoundError("expense", expense_id) from None

    def create(self, record: Expense) -> Expense:
        record.id = self._next_id
        self._rows[self._next_id] = record
        self._next_id += 1
        return record

    def delete(self, expense_id: int) -> None:
        if expense_id not in self._rows:
            raise NotFoundError("expense", expense_id)
        del self._rows[expense_id]


@pytest.fixture
def fake_expense_repository() -> FakeExpenseRepository:
    return FakeExpenseRepository()


@pytest.fixture
def expense_service(fake_expense_repository: FakeExpenseRepository) -> ExpenseService:
    return ExpenseService(fake_expense_repository)


@pytest.fixture
def seeded_repositories(
    fake_budget_repository: FakeBudgetRepository,
) -> dict[str, FakeBudgetRepository]:
    fake_budget_repository.create(
        Budget(
            name="Groceries",
            quantity=Money(Decimal("200.00")),
            category=Category.GROCERIES,
            effective_from=date(2026, 1, 1),
        )
    )
    return {"budgets": fake_budget_repository}
