"""Integration tests for the SQLModel budget repository against a real session."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.errors import NotFoundError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Budget, Category
from finance_web_app.infrastructure.persistence.budget_repository import SqlBudgetRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(session: Session) -> SqlBudgetRepository:
    return SqlBudgetRepository(session)


def _budget(
    *,
    name: str = "Groceries",
    pounds: str = "12.99",
    from_date: date = date(2026, 6, 1),
    stop_date: date | None = None,
) -> Budget:
    return Budget(
        name=name,
        quantity=Money(Decimal(pounds)),
        category=Category.GROCERIES,
        effective_from=from_date,
        effective_stop=stop_date,
    )


def test_create_assigns_id_and_get_round_trips(repo: SqlBudgetRepository) -> None:
    created = repo.create(_budget(stop_date=date(2026, 12, 31)))
    assert created.id is not None

    fetched = repo.get(created.id)
    assert fetched.name == "Groceries"
    assert fetched.quantity == Money(Decimal("12.99"))
    assert fetched.category is Category.GROCERIES
    assert fetched.period.from_date == date(2026, 6, 1)
    assert fetched.period.stop_date == date(2026, 12, 31)


def test_get_missing_raises_not_found(repo: SqlBudgetRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.get(404)


def test_list_all_orders_by_id(repo: SqlBudgetRepository) -> None:
    repo.create(_budget(name="A"))
    repo.create(_budget(name="B"))
    assert [b.name for b in repo.list_all()] == ["A", "B"]


def test_list_effective_uses_covers_month(repo: SqlBudgetRepository) -> None:
    repo.create(_budget(name="June", from_date=date(2026, 6, 15)))
    repo.create(_budget(name="Later", from_date=date(2026, 7, 1)))
    assert [b.name for b in repo.list_effective(2026, 6)] == ["June"]


def test_delete_removes_row(repo: SqlBudgetRepository) -> None:
    created = repo.create(_budget())
    assert created.id is not None
    repo.delete(created.id)
    assert repo.list_all() == []


def test_delete_missing_raises_not_found(repo: SqlBudgetRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.delete(404)


def test_money_is_stored_as_integer_pence(repo: SqlBudgetRepository, session: Session) -> None:
    repo.create(_budget(pounds="12.99"))
    stored = session.connection().exec_driver_sql("SELECT quantity FROM budget").scalar_one()
    assert stored == 1299
    assert isinstance(stored, int)


def test_dates_are_stored_as_iso_strings(repo: SqlBudgetRepository, session: Session) -> None:
    repo.create(_budget(from_date=date(2026, 6, 1)))
    row = (
        session.connection()
        .exec_driver_sql("SELECT effective_from, effective_stop FROM budget")
        .one()
    )
    assert row[0] == "2026-06-01"
    assert row[1] is None
