"""Budget item repository contract."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from finance_web_app.domain.records import BudgetItem


@runtime_checkable
class BudgetItemRepository(Protocol):
    def list_all(self) -> list[BudgetItem]: ...

    def list_by_category(self, category_id: int) -> list[BudgetItem]: ...

    def get(self, budget_item_id: int) -> BudgetItem:
        """Return one budget item. Raises ``NotFoundError`` if absent."""
        ...

    def create(self, record: BudgetItem) -> BudgetItem:
        """Persist a new budget item, returning it with ``id`` set."""
        ...

    def delete(self, budget_item_id: int) -> None:
        """Delete a budget item. Raises ``NotFoundError`` if absent."""
        ...
