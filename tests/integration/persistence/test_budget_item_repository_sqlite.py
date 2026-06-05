"""Integration tests for the SQLModel budget item repository against a real session."""

from __future__ import annotations

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.errors import NotFoundError
from finance_web_app.domain.records import BudgetItem, Category
from finance_web_app.infrastructure.persistence.budget_item_repository import (
    SqlBudgetItemRepository,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(session: Session) -> SqlBudgetItemRepository:
    return SqlBudgetItemRepository(session)


@pytest.fixture
def categories(session: Session) -> tuple[int, int]:
    groceries = Category(name="Groceries")
    clothing = Category(name="Clothing")
    session.add(groceries)
    session.add(clothing)
    session.commit()
    session.refresh(groceries)
    session.refresh(clothing)
    assert groceries.id is not None and clothing.id is not None
    return groceries.id, clothing.id


def test_create_and_get_round_trips(
    repo: SqlBudgetItemRepository, categories: tuple[int, int]
) -> None:
    groceries, _ = categories
    created = repo.create(BudgetItem(name="Tesco", category_id=groceries))
    assert created.id is not None
    fetched = repo.get(created.id)
    assert fetched.name == "Tesco"
    assert fetched.category_id == groceries


def test_list_by_category_filters(
    repo: SqlBudgetItemRepository, categories: tuple[int, int]
) -> None:
    groceries, clothing = categories
    repo.create(BudgetItem(name="Tesco", category_id=groceries))
    repo.create(BudgetItem(name="Aldi", category_id=groceries))
    repo.create(BudgetItem(name="Shoes", category_id=clothing))
    assert {item.name for item in repo.list_by_category(groceries)} == {"Tesco", "Aldi"}


def test_get_missing_raises(repo: SqlBudgetItemRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.get(404)


def test_delete_removes(repo: SqlBudgetItemRepository, categories: tuple[int, int]) -> None:
    groceries, _ = categories
    created = repo.create(BudgetItem(name="Tesco", category_id=groceries))
    assert created.id is not None
    repo.delete(created.id)
    assert repo.list_all() == []
