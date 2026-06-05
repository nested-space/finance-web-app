"""Integration tests for the SQLModel commitment repository."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.errors import NotFoundError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Category, Commitment
from finance_web_app.domain.recurrence import Recurrence
from finance_web_app.infrastructure.persistence.commitment_repository import (
    SqlCommitmentRepository,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(session: Session) -> SqlCommitmentRepository:
    return SqlCommitmentRepository(session)


@pytest.fixture
def category_id(session: Session) -> int:
    category = Category(name="Entertainment")
    session.add(category)
    session.commit()
    session.refresh(category)
    assert category.id is not None
    return category.id


def _commitment(
    *,
    category_id: int,
    name: str = "Netflix",
    start: date = date(2026, 1, 1),
    stop: date = date(2026, 12, 31),
) -> Commitment:
    return Commitment(
        name=name,
        quantity=Money(Decimal("9.99")),
        category_id=category_id,
        recurrence=Recurrence.MONTHLY,
        effective_from=start,
        effective_stop=stop,
    )


def test_create_and_get_round_trips(repo: SqlCommitmentRepository, category_id: int) -> None:
    created = repo.create(_commitment(category_id=category_id))
    assert created.id is not None
    fetched = repo.get(created.id)
    assert fetched.name == "Netflix"
    assert fetched.category_id == category_id
    assert fetched.recurrence is Recurrence.MONTHLY
    assert fetched.period.covers_month(2026, 6) is True


def test_get_missing_raises(repo: SqlCommitmentRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.get(404)


def test_list_effective_uses_covers_month(repo: SqlCommitmentRepository, category_id: int) -> None:
    repo.create(
        _commitment(
            category_id=category_id, name="H1", start=date(2026, 1, 1), stop=date(2026, 6, 30)
        )
    )
    repo.create(
        _commitment(
            category_id=category_id, name="H2", start=date(2026, 7, 1), stop=date(2026, 12, 31)
        )
    )
    assert [c.name for c in repo.list_effective(2026, 3)] == ["H1"]


def test_delete_removes(repo: SqlCommitmentRepository, category_id: int) -> None:
    created = repo.create(_commitment(category_id=category_id))
    assert created.id is not None
    repo.delete(created.id)
    assert repo.list_all() == []


def test_recurrence_stored_as_code(
    repo: SqlCommitmentRepository, session: Session, category_id: int
) -> None:
    repo.create(_commitment(category_id=category_id))
    stored = session.connection().exec_driver_sql("SELECT recurrence FROM commitment").scalar_one()
    assert stored == "MONTHLY"
