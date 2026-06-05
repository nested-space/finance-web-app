"""Budget item use cases.

A budget item is a named label under a category that carries no amount. Creation
validates that the chosen category exists (a clean ``ValidationError`` rather than
letting the foreign key fail at the persistence boundary).
"""

from __future__ import annotations

from finance_web_app.core.contracts.budget_item_repository import BudgetItemRepository
from finance_web_app.core.contracts.category_repository import CategoryRepository
from finance_web_app.core.contracts.errors import NotFoundError, ValidationError
from finance_web_app.domain.records import BudgetItem


class BudgetItemService:
    def __init__(self, items: BudgetItemRepository, categories: CategoryRepository) -> None:
        self._items = items
        self._categories = categories

    def list_all(self) -> list[BudgetItem]:
        return self._items.list_all()

    def list_by_category(self, category_id: int) -> list[BudgetItem]:
        return self._items.list_by_category(category_id)

    def create(self, *, name: str, category_id: int) -> BudgetItem:
        cleaned = name.strip()
        if not cleaned:
            raise ValidationError("name", "is required")
        self._require_category(category_id)
        return self._items.create(BudgetItem(name=cleaned, category_id=category_id))

    def delete(self, budget_item_id: int) -> None:
        self._items.delete(budget_item_id)

    def _require_category(self, category_id: int) -> None:
        try:
            self._categories.get(category_id)
        except NotFoundError:
            raise ValidationError("category", "does not exist") from None
