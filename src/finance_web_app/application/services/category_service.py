"""Category use cases.

Manages the user-managed category list. Creation rejects blank or duplicate
names; deletion is **blocked while the category is in use** by any budget, budget
item, or expense (``count_references``) -- the service raises a ``ValidationError``
the web layer maps to HTTP 400, so a referenced category is never silently
removed. Depends only on the repository Protocol and domain types.
"""

from __future__ import annotations

from finance_web_app.core.contracts.category_repository import CategoryRepository
from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.records import Category


class CategoryService:
    def __init__(self, categories: CategoryRepository) -> None:
        self._categories = categories

    def list_all(self) -> list[Category]:
        return self._categories.list_all()

    def get(self, category_id: int) -> Category:
        return self._categories.get(category_id)

    def create(self, *, name: str) -> Category:
        cleaned = name.strip()
        if not cleaned:
            raise ValidationError("name", "is required")
        if any(existing.name.casefold() == cleaned.casefold() for existing in self.list_all()):
            raise ValidationError("name", f"{cleaned!r} already exists")
        return self._categories.create(Category(name=cleaned))

    def delete(self, category_id: int) -> None:
        if self._categories.count_references(category_id) > 0:
            raise ValidationError(
                "category", "is in use; remove its budgets, items, and expenses first"
            )
        self._categories.delete(category_id)
