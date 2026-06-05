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


@pytest.fixture
def category_id(session: Session) -> int:
    category = Category(name="Groceries")
    session.add(category)
    session.commit()
    session.refresh(category)
    assert category.id is not None
    return category.id


def _budget(
    *,
    category_id: int,
    pounds: str = "12.99",
    from_date: date = date(2026, 6, 1),
    stop_date: date | None = None,
) -> Budget:
    return Budget(
        quantity=Money(Decimal(pounds)),
        category_id=category_id,
        effective_from=from_date,
        effective_stop=stop_date,
    )


def test_create_assigns_id_and_get_round_trips(repo: SqlBudgetRepository, category_id: int) -> None:
    created = repo.create(_budget(category_id=category_id, stop_date=date(2026, 12, 31)))
    assert created.id is not None

    fetched = repo.get(created.id)
    assert fetched.quantity == Money(Decimal("12.99"))
    assert fetched.category_id == category_id
    assert fetched.period.from_date == date(2026, 6, 1)
    assert fetched.period.stop_date == date(2026, 12, 31)


def test_get_missing_raises_not_found(repo: SqlBudgetRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.get(404)


def test_list_all_orders_by_id(repo: SqlBudgetRepository, category_id: int) -> None:
    first = repo.create(_budget(category_id=category_id, from_date=date(2026, 6, 1)))
    second = repo.create(_budget(category_id=category_id, from_date=date(2026, 7, 1)))
    assert [b.id for b in repo.list_all()] == [first.id, second.id]


def test_list_effective_uses_covers_month(repo: SqlBudgetRepository, category_id: int) -> None:
    repo.create(_budget(category_id=category_id, from_date=date(2026, 6, 15)))
    repo.create(_budget(category_id=category_id, from_date=date(2026, 7, 1)))
    effective = repo.list_effective(2026, 6)
    assert [b.period.from_date for b in effective] == [date(2026, 6, 15)]


def test_delete_removes_row(repo: SqlBudgetRepository, category_id: int) -> None:
    created = repo.create(_budget(category_id=category_id))
    assert created.id is not None
    repo.delete(created.id)
    assert repo.list_all() == []


def test_delete_missing_raises_not_found(repo: SqlBudgetRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.delete(404)


def test_money_is_stored_as_integer_pence(
    repo: SqlBudgetRepository, session: Session, category_id: int
) -> None:
    repo.create(_budget(category_id=category_id, pounds="12.99"))
    stored = session.connection().exec_driver_sql("SELECT quantity FROM budget").scalar_one()
    assert stored == 1299
    assert isinstance(stored, int)


def test_dates_are_stored_as_iso_strings(
    repo: SqlBudgetRepository, session: Session, category_id: int
) -> None:
    repo.create(_budget(category_id=category_id, from_date=date(2026, 6, 1)))
    row = (
        session.connection()
        .exec_driver_sql("SELECT effective_from, effective_stop FROM budget")
        .one()
    )
    assert row[0] == "2026-06-01"
    assert row[1] is None
