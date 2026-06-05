"""Integration tests for the SQLModel expense repository."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.errors import NotFoundError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import BudgetItem, Category, Expense
from finance_web_app.infrastructure.persistence.expense_repository import SqlExpenseRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(session: Session) -> SqlExpenseRepository:
    return SqlExpenseRepository(session)


@pytest.fixture
def category_id(session: Session) -> int:
    category = Category(name="Groceries")
    session.add(category)
    session.commit()
    session.refresh(category)
    assert category.id is not None
    return category.id


def _expense(
    *,
    category_id: int,
    budget_item_id: int | None = None,
    name: str = "Lunch",
    when: date = date(2026, 6, 15),
) -> Expense:
    return Expense(
        name=name,
        quantity=Money(Decimal("5.50")),
        category_id=category_id,
        budget_item_id=budget_item_id,
        date=when,
        description=None,
    )


def test_create_and_get_round_trips(repo: SqlExpenseRepository, category_id: int) -> None:
    created = repo.create(_expense(category_id=category_id))
    assert created.id is not None
    fetched = repo.get(created.id)
    assert fetched.name == "Lunch"
    assert fetched.quantity == Money(Decimal("5.50"))
    assert fetched.category_id == category_id
    assert fetched.budget_item_id is None
    assert fetched.date == date(2026, 6, 15)


def test_create_with_budget_item_round_trips(
    repo: SqlExpenseRepository, session: Session, category_id: int
) -> None:
    item = BudgetItem(name="Tesco", category_id=category_id)
    session.add(item)
    session.commit()
    session.refresh(item)
    created = repo.create(_expense(category_id=category_id, budget_item_id=item.id))
    assert created.id is not None
    assert repo.get(created.id).budget_item_id == item.id


def test_get_missing_raises_not_found(repo: SqlExpenseRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.get(404)


def test_list_effective_uses_in_month(repo: SqlExpenseRepository, category_id: int) -> None:
    repo.create(_expense(category_id=category_id, name="June", when=date(2026, 6, 30)))
    repo.create(_expense(category_id=category_id, name="July", when=date(2026, 7, 1)))
    assert [e.name for e in repo.list_effective(2026, 6)] == ["June"]


def test_delete_removes_row(repo: SqlExpenseRepository, category_id: int) -> None:
    created = repo.create(_expense(category_id=category_id))
    assert created.id is not None
    repo.delete(created.id)
    assert repo.list_all() == []


def test_money_is_stored_as_integer_pence(
    repo: SqlExpenseRepository, session: Session, category_id: int
) -> None:
    repo.create(_expense(category_id=category_id))
    stored = session.connection().exec_driver_sql("SELECT quantity FROM expense").scalar_one()
    assert stored == 550
    assert isinstance(stored, int)
