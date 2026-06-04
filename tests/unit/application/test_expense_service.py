"""Unit tests for ExpenseService against a fake repository."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.application.services.expense_service import ExpenseService
from finance_web_app.core.contracts.errors import NotFoundError, ValidationError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Category, Expense

pytestmark = pytest.mark.unit


def _create(
    service: ExpenseService,
    *,
    name: str = "Lunch",
    when: date = date(2026, 6, 15),
) -> Expense:
    return service.create(
        name=name,
        quantity=Money.from_pence(550),
        category=Category.GROCERIES,
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


def test_total_and_totals_by_category(expense_service: ExpenseService) -> None:
    _create(expense_service, name="A")  # GROCERIES £5.50
    _create(expense_service, name="B")
    assert expense_service.total(2026, 6) == Money.from_pence(1100)
    assert expense_service.totals_by_category(2026, 6) == {
        Category.GROCERIES: Money.from_pence(1100)
    }


def test_cumulative_spend_runs_and_filters_by_category(expense_service: ExpenseService) -> None:
    expense_service.create(
        name="Food",
        quantity=Money.from_pence(1000),
        category=Category.GROCERIES,
        date=date(2026, 6, 2),
        description=None,
    )
    expense_service.create(
        name="Shoes",
        quantity=Money.from_pence(5000),
        category=Category.CLOTHING,
        date=date(2026, 6, 5),
        description=None,
    )
    cumulative = expense_service.cumulative_spend(2026, 6)
    assert len(cumulative) == 30
    assert cumulative[0] == Money.from_pence(0)
    assert cumulative[1] == Money.from_pence(1000)
    assert cumulative[4] == Money.from_pence(6000)
    assert cumulative[-1] == Money.from_pence(6000)

    groceries = expense_service.cumulative_spend(2026, 6, {Category.GROCERIES})
    assert groceries[-1] == Money.from_pence(1000)
