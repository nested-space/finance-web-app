"""Budget repository contract.

The service depends on this Protocol, never on a concrete implementation. It is
``@runtime_checkable`` so contract tests can assert a concrete repository
satisfies it via ``isinstance`` (``docs/ARCHITECTURE.md`` -> "Repository protocol
shape").
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from finance_web_app.domain.records import BudgetRecord


@runtime_checkable
class BudgetRepository(Protocol):
    def list_all(self) -> list[BudgetRecord]: ...

    def list_effective(self, year: int, month: int) -> list[BudgetRecord]: ...

    def get(self, budget_id: int) -> BudgetRecord:
        """Return one budget. Raises ``NotFoundError`` if absent."""
        ...

    def create(self, record: BudgetRecord) -> BudgetRecord:
        """Persist a new budget, returning it with ``id`` set."""
        ...

    def delete(self, budget_id: int) -> None:
        """Delete a budget. Raises ``NotFoundError`` if absent."""
        ...
