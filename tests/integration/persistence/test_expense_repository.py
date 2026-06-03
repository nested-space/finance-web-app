"""Integration tests for the SQLModel expense repository."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.errors import NotFoundError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Category, Expense
from finance_web_app.infrastructure.persistence.expense_repository import SqlExpenseRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(session: Session) -> SqlExpenseRepository:
    return SqlExpenseRepository(session)


def _expense(*, name: str = "Lunch", when: date = date(2026, 6, 15)) -> Expense:
    return Expense(
        name=name,
        quantity=Money(Decimal("5.50")),
        category=Category.GROCERIES,
        date=when,
        description=None,
    )


def test_create_and_get_round_trips(repo: SqlExpenseRepository) -> None:
    created = repo.create(_expense())
    assert created.id is not None
    fetched = repo.get(created.id)
    assert fetched.name == "Lunch"
    assert fetched.quantity == Money(Decimal("5.50"))
    assert fetched.date == date(2026, 6, 15)


def test_get_missing_raises_not_found(repo: SqlExpenseRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.get(404)


def test_list_effective_uses_in_month(repo: SqlExpenseRepository) -> None:
    repo.create(_expense(name="June", when=date(2026, 6, 30)))
    repo.create(_expense(name="July", when=date(2026, 7, 1)))
    assert [e.name for e in repo.list_effective(2026, 6)] == ["June"]


def test_delete_removes_row(repo: SqlExpenseRepository) -> None:
    created = repo.create(_expense())
    assert created.id is not None
    repo.delete(created.id)
    assert repo.list_all() == []


def test_money_is_stored_as_integer_pence(repo: SqlExpenseRepository, session: Session) -> None:
    repo.create(_expense())
    stored = session.connection().exec_driver_sql("SELECT quantity FROM expense").scalar_one()
    assert stored == 550
    assert isinstance(stored, int)
