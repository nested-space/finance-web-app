"""Budget repository contract.

The service depends on this Protocol, never on a concrete implementation. It is
``@runtime_checkable`` so contract tests can assert a concrete repository
satisfies it via ``isinstance`` (``docs/ARCHITECTURE.md`` -> "Repository protocol
shape").
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from finance_web_app.domain.records import Budget


@runtime_checkable
class BudgetRepository(Protocol):
    def list_all(self) -> list[Budget]: ...

    def list_effective(self, year: int, month: int) -> list[Budget]: ...

    def get(self, budget_id: int) -> Budget:
        """Return one budget. Raises ``NotFoundError`` if absent."""
        ...

    def create(self, record: Budget) -> Budget:
        """Persist a new budget, returning it with ``id`` set."""
        ...

    def delete(self, budget_id: int) -> None:
        """Delete a budget. Raises ``NotFoundError`` if absent."""
        ...
