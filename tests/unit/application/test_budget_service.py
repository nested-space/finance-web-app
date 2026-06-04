"""Unit tests for BudgetService against a fake repository."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.application.services.budget_service import BudgetService
from finance_web_app.core.contracts.errors import NotFoundError, ValidationError
from finance_web_app.domain.effective_period import EffectivePeriod
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Budget, Category

pytestmark = pytest.mark.unit


def _create(
    service: BudgetService,
    *,
    name: str = "Groceries",
    from_date: date = date(2026, 6, 1),
) -> Budget:
    return service.create(
        name=name,
        quantity=Money.from_pence(20000),
        category=Category.GROCERIES,
        period=EffectivePeriod(from_date=from_date),
    )


def test_create_assigns_id(budget_service: BudgetService) -> None:
    assert _create(budget_service).id == 1


def test_list_all_returns_created_records(budget_service: BudgetService) -> None:
    _create(budget_service, name="A")
    _create(budget_service, name="B")
    assert [b.name for b in budget_service.list_all()] == ["A", "B"]


def test_list_effective_filters_by_month(budget_service: BudgetService) -> None:
    _create(budget_service, name="June", from_date=date(2026, 6, 1))
    _create(budget_service, name="July", from_date=date(2026, 7, 1))
    assert [b.name for b in budget_service.list_effective(2026, 6)] == ["June"]


def test_delete_removes_record(budget_service: BudgetService) -> None:
    created = _create(budget_service)
    assert created.id is not None
    budget_service.delete(created.id)
    assert budget_service.list_all() == []


def test_delete_missing_raises_not_found(budget_service: BudgetService) -> None:
    with pytest.raises(NotFoundError):
        budget_service.delete(999)


def test_create_empty_name_raises_validation_error(budget_service: BudgetService) -> None:
    with pytest.raises(ValidationError):
        _create(budget_service, name="")


def test_totals_by_category_sums_per_category(budget_service: BudgetService) -> None:
    _create(budget_service, name="A")  # GROCERIES, £200
    _create(budget_service, name="B")  # GROCERIES, £200
    totals = budget_service.totals_by_category(2026, 6)
    assert totals == {Category.GROCERIES: Money.from_pence(40000)}


def test_total_sums_caps(budget_service: BudgetService) -> None:
    _create(budget_service, name="A")  # £200
    _create(budget_service, name="B")  # £200
    assert budget_service.total(2026, 6) == Money.from_pence(40000)
