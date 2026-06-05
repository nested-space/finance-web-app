"""Unit tests for CommitmentService against fake repositories."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.application.services.commitment_service import CommitmentService
from finance_web_app.core.contracts.errors import NotFoundError, ValidationError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Commitment
from finance_web_app.domain.recurrence import Recurrence

pytestmark = pytest.mark.unit

ENTERTAINMENT = 4  # seeded category id (see conftest SEED_CATEGORY_IDS)


def _create(
    service: CommitmentService,
    *,
    name: str = "Netflix",
    category_id: int = ENTERTAINMENT,
    start: date = date(2026, 1, 1),
    stop: date = date(2026, 12, 31),
) -> Commitment:
    return service.create(
        name=name,
        quantity=Money.from_pence(999),
        category_id=category_id,
        recurrence=Recurrence.MONTHLY,
        effective_from=start,
        effective_stop=stop,
    )


def test_create_assigns_id(commitment_service: CommitmentService) -> None:
    assert _create(commitment_service).id == 1


def test_list_effective_filters_by_month(commitment_service: CommitmentService) -> None:
    _create(commitment_service, name="H1", start=date(2026, 1, 1), stop=date(2026, 6, 30))
    _create(commitment_service, name="H2", start=date(2026, 7, 1), stop=date(2026, 12, 31))
    assert [c.name for c in commitment_service.list_effective(2026, 3)] == ["H1"]


def test_delete_removes(commitment_service: CommitmentService) -> None:
    created = _create(commitment_service)
    assert created.id is not None
    commitment_service.delete(created.id)
    assert commitment_service.list_all() == []


def test_delete_missing_raises(commitment_service: CommitmentService) -> None:
    with pytest.raises(NotFoundError):
        commitment_service.delete(999)


def test_empty_name_raises_validation(commitment_service: CommitmentService) -> None:
    with pytest.raises(ValidationError):
        _create(commitment_service, name="")


def test_unknown_category_raises_validation(commitment_service: CommitmentService) -> None:
    with pytest.raises(ValidationError):
        _create(commitment_service, category_id=999)


def test_totals_by_category_sums_per_category(commitment_service: CommitmentService) -> None:
    _create(commitment_service, name="A")  # ENTERTAINMENT, £9.99
    _create(commitment_service, name="B")  # ENTERTAINMENT, £9.99
    totals = commitment_service.totals_by_category(2026, 6)
    assert totals == {ENTERTAINMENT: Money.from_pence(1998)}
