"""Unit tests for ExpenseService against fake repositories."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.application.services.expense_service import ExpenseService
from finance_web_app.core.contracts.budget_item_repository import BudgetItemRepository
from finance_web_app.core.contracts.errors import NotFoundError, ValidationError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import BudgetItem, Expense

pytestmark = pytest.mark.unit

GROCERIES = 2  # seeded category id (see conftest SEED_CATEGORY_IDS)
CLOTHING = 3


def _create(
    service: ExpenseService,
    *,
    name: str = "Lunch",
    category_id: int = GROCERIES,
    budget_item_id: int | None = None,
    when: date = date(2026, 6, 15),
) -> Expense:
    return service.create(
        name=name,
        quantity=Money.from_pence(550),
        category_id=category_id,
        budget_item_id=budget_item_id,
        date=when,
        description=None,
    )


def test_create_assigns_id(expense_service: ExpenseService) -> None:
    assert _create(expense_service).id == 1


def test_list_effective_filters_by_month(expense_service: ExpenseService) -> None:
    _create(expense_service, name="June", when=date(2026, 6, 1))
    _create(expense_service, name="July", when=date(2026, 7, 1))
    assert [e.name for e in expense_service.list_effective(2026, 6)] == ["June"]


def test_delete_removes_record(expense_service: ExpenseService) -> None:
    created = _create(expense_service)
    assert created.id is not None
    expense_service.delete(created.id)
    assert expense_service.list_all() == []


def test_delete_missing_raises_not_found(expense_service: ExpenseService) -> None:
    with pytest.raises(NotFoundError):
        expense_service.delete(999)


def test_create_empty_name_raises_validation_error(expense_service: ExpenseService) -> None:
    with pytest.raises(ValidationError):
        _create(expense_service, name="")


def test_create_unknown_category_raises_validation_error(expense_service: ExpenseService) -> None:
    with pytest.raises(ValidationError):
        _create(expense_service, category_id=999)


def test_create_accepts_a_budget_item_in_the_same_category(
    expense_service: ExpenseService, fake_budget_item_repository: BudgetItemRepository
) -> None:
    item = fake_budget_item_repository.create(BudgetItem(name="Tesco", category_id=GROCERIES))
    assert item.id is not None
    created = _create(expense_service, category_id=GROCERIES, budget_item_id=item.id)
    assert created.budget_item_id == item.id


def test_create_rejects_a_budget_item_from_another_category(
    expense_service: ExpenseService, fake_budget_item_repository: BudgetItemRepository
) -> None:
    item = fake_budget_item_repository.create(BudgetItem(name="Tesco", category_id=GROCERIES))
    assert item.id is not None
    with pytest.raises(ValidationError) as exc:
        _create(expense_service, category_id=CLOTHING, budget_item_id=item.id)
    assert exc.value.field == "budget_item"


def test_create_rejects_unknown_budget_item(expense_service: ExpenseService) -> None:
    with pytest.raises(ValidationError) as exc:
        _create(expense_service, budget_item_id=999)
    assert exc.value.field == "budget_item"


def test_total_and_totals_by_category(expense_service: ExpenseService) -> None:
    _create(expense_service, name="A")  # GROCERIES £5.50
    _create(expense_service, name="B")
    assert expense_service.total(2026, 6) == Money.from_pence(1100)
    assert expense_service.totals_by_category(2026, 6) == {GROCERIES: Money.from_pence(1100)}


def test_cumulative_spend_runs_and_filters_by_category(expense_service: ExpenseService) -> None:
    expense_service.create(
        name="Food",
        quantity=Money.from_pence(1000),
        category_id=GROCERIES,
        budget_item_id=None,
        date=date(2026, 6, 2),
        description=None,
    )
    expense_service.create(
        name="Shoes",
        quantity=Money.from_pence(5000),
        category_id=CLOTHING,
        budget_item_id=None,
        date=date(2026, 6, 5),
        description=None,
    )
    cumulative = expense_service.cumulative_spend(2026, 6)
    assert len(cumulative) == 30
    assert cumulative[0] == Money.from_pence(0)
    assert cumulative[1] == Money.from_pence(1000)
    assert cumulative[4] == Money.from_pence(6000)
    assert cumulative[-1] == Money.from_pence(6000)

    groceries = expense_service.cumulative_spend(2026, 6, {GROCERIES})
    assert groceries[-1] == Money.from_pence(1000)


def test_totals_by_category_filters_by_category(expense_service: ExpenseService) -> None:
    expense_service.create(
        name="Food",
        quantity=Money.from_pence(1000),
        category_id=GROCERIES,
        budget_item_id=None,
        date=date(2026, 6, 1),
        description=None,
    )
    expense_service.create(
        name="Shoes",
        quantity=Money.from_pence(5000),
        category_id=CLOTHING,
        budget_item_id=None,
        date=date(2026, 6, 5),
        description=None,
    )
    filtered = expense_service.totals_by_category(2026, 6, {GROCERIES})
    assert filtered == {GROCERIES: Money.from_pence(1000)}
    assert CLOTHING not in filtered
