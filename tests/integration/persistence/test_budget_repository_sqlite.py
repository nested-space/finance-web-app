"""Integration tests for the SQLite budget repository against a temp-file DB."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from finance_web_app.core.contracts.errors import NotFoundError
from finance_web_app.domain.effective_period import EffectivePeriod
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import BudgetRecord, Category
from finance_web_app.infrastructure.persistence.budget_repository_sqlite import (
    SqliteBudgetRepository,
)
from finance_web_app.infrastructure.persistence.connection import connect

pytestmark = pytest.mark.integration


@pytest.fixture
def conn(tmp_sqlite_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_sqlite_path)
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def repo(conn: sqlite3.Connection) -> SqliteBudgetRepository:
    return SqliteBudgetRepository(conn)


def _record(
    *,
    name: str = "Groceries",
    pence: int = 1299,
    from_date: date = date(2026, 6, 1),
    stop_date: date | None = None,
) -> BudgetRecord:
    return BudgetRecord(
        name=name,
        quantity=Money.from_pence(pence),
        category=Category.GROCERIES,
        period=EffectivePeriod(from_date=from_date, stop_date=stop_date),
    )


def test_create_assigns_id_and_get_round_trips(repo: SqliteBudgetRepository) -> None:
    created = repo.create(_record(stop_date=date(2026, 12, 31)))
    assert created.id is not None

    fetched = repo.get(created.id)
    assert fetched.name == "Groceries"
    assert fetched.quantity.pence() == 1299
    assert fetched.category is Category.GROCERIES
    assert fetched.period.from_date == date(2026, 6, 1)
    assert fetched.period.stop_date == date(2026, 12, 31)


def test_get_missing_raises_not_found(repo: SqliteBudgetRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.get(404)


def test_list_all_orders_by_id(repo: SqliteBudgetRepository) -> None:
    repo.create(_record(name="A"))
    repo.create(_record(name="B"))
    assert [b.name for b in repo.list_all()] == ["A", "B"]


def test_list_effective_uses_covers_month(repo: SqliteBudgetRepository) -> None:
    repo.create(_record(name="June", from_date=date(2026, 6, 15)))
    repo.create(_record(name="Later", from_date=date(2026, 7, 1)))
    assert [b.name for b in repo.list_effective(2026, 6)] == ["June"]


def test_delete_removes_row(repo: SqliteBudgetRepository) -> None:
    created = repo.create(_record())
    assert created.id is not None
    repo.delete(created.id)
    assert repo.list_all() == []


def test_delete_missing_raises_not_found(repo: SqliteBudgetRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.delete(404)


def test_money_is_stored_as_integer_pence(
    repo: SqliteBudgetRepository, conn: sqlite3.Connection
) -> None:
    repo.create(_record(pence=1299))
    stored = conn.execute("SELECT quantity FROM budget").fetchone()[0]
    assert stored == 1299
    assert isinstance(stored, int)


def test_dates_are_stored_as_iso_strings(
    repo: SqliteBudgetRepository, conn: sqlite3.Connection
) -> None:
    repo.create(_record(from_date=date(2026, 6, 1)))
    row = conn.execute("SELECT effective_from, effective_stop FROM budget").fetchone()
    assert row["effective_from"] == "2026-06-01"
    assert row["effective_stop"] is None
