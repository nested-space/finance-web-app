"""Income repository contract.

Beyond the standard five methods, income owns a child table of one-off
exceptions (``docs/ARCHITECTURE.md`` -> "Repository protocol shape").
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from finance_web_app.domain.records import Income, IncomeException


@runtime_checkable
class IncomeRepository(Protocol):
    def list_all(self) -> list[Income]: ...

    def list_effective(self, year: int, month: int) -> list[Income]: ...

    def get(self, income_id: int) -> Income:
        """Return one income stream. Raises ``NotFoundError`` if absent."""
        ...

    def create(self, record: Income) -> Income:
        """Persist a new income stream, returning it with ``id`` set."""
        ...

    def delete(self, income_id: int) -> None:
        """Delete an income stream (and its exceptions). Raises ``NotFoundError`` if absent."""
        ...

    def add_exception(self, income_id: int, exception: IncomeException) -> None:
        """Attach a one-off exception to an income stream."""
        ...

    def list_exceptions(self, income_id: int) -> list[IncomeException]:
        """List the exceptions of an income stream."""
        ...
