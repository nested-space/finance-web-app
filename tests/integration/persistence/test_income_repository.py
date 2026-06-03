"""Integration tests for the SQLModel income repository, including exceptions."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.errors import NotFoundError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Income, IncomeException
from finance_web_app.domain.recurrence import Recurrence
from finance_web_app.infrastructure.persistence.income_repository import SqlIncomeRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(session: Session) -> SqlIncomeRepository:
    return SqlIncomeRepository(session)


def _income(*, name: str = "Salary", stop: date | None = None) -> Income:
    return Income(
        name=name,
        quantity=Money(Decimal("2500")),
        recurrence=Recurrence.MONTHLY,
        effective_from=date(2026, 1, 1),
        effective_stop=stop,
    )


def test_create_and_get_round_trips(repo: SqlIncomeRepository) -> None:
    created = repo.create(_income())
    assert created.id is not None
    fetched = repo.get(created.id)
    assert fetched.name == "Salary"
    assert fetched.recurrence is Recurrence.MONTHLY
    assert fetched.period.stop_date is None


def test_get_missing_raises(repo: SqlIncomeRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.get(404)


def test_add_and_list_exceptions(repo: SqlIncomeRepository) -> None:
    income = repo.create(_income())
    assert income.id is not None
    repo.add_exception(
        income.id,
        IncomeException(date=date(2026, 6, 1), quantity=Money(Decimal("3000")), reason="bonus"),
    )
    exceptions = repo.list_exceptions(income.id)
    assert len(exceptions) == 1
    assert exceptions[0].quantity == Money(Decimal("3000"))


def test_deleting_income_cascades_to_exceptions(
    repo: SqlIncomeRepository, session: Session
) -> None:
    income = repo.create(_income())
    assert income.id is not None
    repo.add_exception(
        income.id, IncomeException(date=date(2026, 6, 1), quantity=Money(Decimal("3000")))
    )

    repo.delete(income.id)

    remaining = (
        session.connection().exec_driver_sql("SELECT count(*) FROM income_exception").scalar_one()
    )
    assert remaining == 0


def test_delete_missing_raises(repo: SqlIncomeRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.delete(404)
