"""Unit tests for IncomeService against a fake repository."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.application.services.income_service import IncomeService
from finance_web_app.core.contracts.errors import NotFoundError, ValidationError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Income
from finance_web_app.domain.recurrence import Recurrence

pytestmark = pytest.mark.unit


def _create(
    service: IncomeService,
    *,
    name: str = "Salary",
    start: date = date(2026, 1, 1),
    stop: date | None = None,
) -> Income:
    return service.create(
        name=name,
        quantity=Money.from_pence(250000),
        recurrence=Recurrence.MONTHLY,
        effective_from=start,
        effective_stop=stop,
    )


def test_create_assigns_id(income_service: IncomeService) -> None:
    assert _create(income_service).id == 1


def test_open_ended_income_is_effective_far_in_future(income_service: IncomeService) -> None:
    _create(income_service, start=date(2026, 1, 1), stop=None)
    assert len(income_service.list_effective(2030, 12)) == 1


def test_delete_removes(income_service: IncomeService) -> None:
    created = _create(income_service)
    assert created.id is not None
    income_service.delete(created.id)
    assert income_service.list_all() == []


def test_delete_missing_raises(income_service: IncomeService) -> None:
    with pytest.raises(NotFoundError):
        income_service.delete(999)


def test_empty_name_raises_validation(income_service: IncomeService) -> None:
    with pytest.raises(ValidationError):
        _create(income_service, name="")
