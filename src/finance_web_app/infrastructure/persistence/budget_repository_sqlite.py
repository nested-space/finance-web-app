"""SQLite implementation of the budget repository contract.

All SQL is parameterised. ``Money`` is converted to and from integer pence at
this boundary; date values are stored as ISO-8601 strings. Unexpected
``sqlite3.Error`` is wrapped in ``RepositoryError`` so callers never see a raw
driver exception (``docs/ARCHITECTURE.md``, ``docs/DEVELOPMENT.md`` -> "Security
baseline").
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import date

from finance_web_app.core.contracts.errors import NotFoundError, RepositoryError
from finance_web_app.domain.effective_period import EffectivePeriod
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import BudgetRecord, Category

# Plain string literals (no interpolation): all dynamic values are bound as
# parameters, so there is no string-built SQL for ruff's S rules to flag.
_SELECT_ALL = (
    "SELECT id, name, quantity, category, effective_from, effective_stop FROM budget ORDER BY id"
)
_SELECT_ONE = (
    "SELECT id, name, quantity, category, effective_from, effective_stop FROM budget WHERE id = ?"
)


class SqliteBudgetRepository:
    """Budget persistence backed by a single SQLite connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_all(self) -> list[BudgetRecord]:
        try:
            rows = self._conn.execute(_SELECT_ALL).fetchall()
        except sqlite3.Error as exc:
            raise RepositoryError("list budgets", exc) from exc
        return [self._to_record(row) for row in rows]

    def list_effective(self, year: int, month: int) -> list[BudgetRecord]:
        # The single date-effective predicate lives on EffectivePeriod; filtering
        # in Python keeps it the only copy. Fine at single-user row counts.
        return [b for b in self.list_all() if b.period.covers_month(year, month)]

    def get(self, budget_id: int) -> BudgetRecord:
        try:
            row = self._conn.execute(_SELECT_ONE, (budget_id,)).fetchone()
        except sqlite3.Error as exc:
            raise RepositoryError("get budget", exc) from exc
        if row is None:
            raise NotFoundError("budget", budget_id)
        return self._to_record(row)

    def create(self, record: BudgetRecord) -> BudgetRecord:
        stop = record.period.stop_date
        try:
            cursor = self._conn.execute(
                "INSERT INTO budget (name, quantity, category, effective_from, effective_stop) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    record.name,
                    record.quantity.pence(),
                    record.category.name,
                    record.period.from_date.isoformat(),
                    stop.isoformat() if stop is not None else None,
                ),
            )
            self._conn.commit()
        except sqlite3.Error as exc:
            raise RepositoryError("create budget", exc) from exc
        return replace(record, id=cursor.lastrowid)

    def delete(self, budget_id: int) -> None:
        try:
            cursor = self._conn.execute("DELETE FROM budget WHERE id = ?", (budget_id,))
            self._conn.commit()
        except sqlite3.Error as exc:
            raise RepositoryError("delete budget", exc) from exc
        if cursor.rowcount == 0:
            raise NotFoundError("budget", budget_id)

    def _to_record(self, row: sqlite3.Row) -> BudgetRecord:
        raw_stop = row["effective_stop"]
        period = EffectivePeriod(
            from_date=date.fromisoformat(row["effective_from"]),
            stop_date=date.fromisoformat(raw_stop) if raw_stop is not None else None,
        )
        return BudgetRecord(
            id=row["id"],
            name=row["name"],
            quantity=Money.from_pence(row["quantity"]),
            category=Category.from_code(row["category"]),
            period=period,
        )
