"""Unit tests for BudgetItemService against fake repositories."""

from __future__ import annotations

import pytest

from finance_web_app.application.services.budget_item_service import BudgetItemService
from finance_web_app.core.contracts.errors import NotFoundError, ValidationError

pytestmark = pytest.mark.unit

GROCERIES = 2  # seeded category id (see conftest SEED_CATEGORY_IDS)
CLOTHING = 3


def test_create_adds_an_item(budget_item_service: BudgetItemService) -> None:
    created = budget_item_service.create(name="Tesco", category_id=GROCERIES)
    assert created.id is not None
    assert created.category_id == GROCERIES


def test_create_blank_name_raises(budget_item_service: BudgetItemService) -> None:
    with pytest.raises(ValidationError) as exc:
        budget_item_service.create(name="  ", category_id=GROCERIES)
    assert exc.value.field == "name"


def test_create_unknown_category_raises(budget_item_service: BudgetItemService) -> None:
    with pytest.raises(ValidationError) as exc:
        budget_item_service.create(name="Tesco", category_id=999)
    assert exc.value.field == "category"


def test_list_by_category_filters(budget_item_service: BudgetItemService) -> None:
    budget_item_service.create(name="Tesco", category_id=GROCERIES)
    budget_item_service.create(name="Aldi", category_id=GROCERIES)
    budget_item_service.create(name="Shoes", category_id=CLOTHING)
    groceries = budget_item_service.list_by_category(GROCERIES)
    assert {item.name for item in groceries} == {"Tesco", "Aldi"}


def test_delete_removes_item(budget_item_service: BudgetItemService) -> None:
    created = budget_item_service.create(name="Tesco", category_id=GROCERIES)
    assert created.id is not None
    budget_item_service.delete(created.id)
    assert budget_item_service.list_all() == []


def test_delete_missing_raises(budget_item_service: BudgetItemService) -> None:
    with pytest.raises(NotFoundError):
        budget_item_service.delete(999)
