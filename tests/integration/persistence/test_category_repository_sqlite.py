"""Integration tests for the SQLModel category repository against a real session."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.errors import NotFoundError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Budget, BudgetItem, Category, Expense
from finance_web_app.infrastructure.persistence.category_repository import SqlCategoryRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(session: Session) -> SqlCategoryRepository:
    return SqlCategoryRepository(session)


def test_create_and_get_round_trips(repo: SqlCategoryRepository) -> None:
    created = repo.create(Category(name="Groceries"))
    assert created.id is not None
    assert repo.get(created.id).name == "Groceries"


def test_list_all_orders_by_name(repo: SqlCategoryRepository) -> None:
    repo.create(Category(name="Petrol"))
    repo.create(Category(name="Clothing"))
    repo.create(Category(name="Groceries"))
    assert [c.name for c in repo.list_all()] == ["Clothing", "Groceries", "Petrol"]


def test_get_missing_raises_not_found(repo: SqlCategoryRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.get(404)


def test_count_references_counts_budgets_items_and_expenses(
    repo: SqlCategoryRepository, session: Session
) -> None:
    category = repo.create(Category(name="Groceries"))
    assert category.id is not None
    assert repo.count_references(category.id) == 0

    session.add(
        Budget(
            quantity=Money(Decimal("10.00")),
            category_id=category.id,
            effective_from=date(2026, 6, 1),
        )
    )
    session.add(BudgetItem(name="Tesco", category_id=category.id))
    session.add(
        Expense(
            name="Lunch",
            quantity=Money(Decimal("5.00")),
            category_id=category.id,
            date=date(2026, 6, 2),
        )
    )
    session.commit()
    assert repo.count_references(category.id) == 3


def test_delete_removes_row(repo: SqlCategoryRepository) -> None:
    created = repo.create(Category(name="Holidays"))
    assert created.id is not None
    repo.delete(created.id)
    assert repo.list_all() == []
