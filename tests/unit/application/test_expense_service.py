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
