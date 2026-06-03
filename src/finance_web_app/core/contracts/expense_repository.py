"""Expense repository contract."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from finance_web_app.domain.records import Expense


@runtime_checkable
class ExpenseRepository(Protocol):
    def list_all(self) -> list[Expense]: ...

    def list_effective(self, year: int, month: int) -> list[Expense]: ...

    def get(self, expense_id: int) -> Expense:
        """Return one expense. Raises ``NotFoundError`` if absent."""
        ...

    def create(self, record: Expense) -> Expense:
        """Persist a new expense, returning it with ``id`` set."""
        ...

    def delete(self, expense_id: int) -> None:
        """Delete an expense. Raises ``NotFoundError`` if absent."""
        ...
