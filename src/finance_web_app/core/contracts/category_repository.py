"""Category repository contract.

The service depends on this Protocol, never on a concrete implementation. It is
``@runtime_checkable`` so contract tests can assert a concrete repository
satisfies it via ``isinstance`` (``docs/ARCHITECTURE.md`` -> "Repository protocol
shape"). ``count_references`` backs the in-use guard that blocks deletion of a
category still referenced by a budget, budget item, or expense.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from finance_web_app.domain.records import Category


@runtime_checkable
class CategoryRepository(Protocol):
    def list_all(self) -> list[Category]: ...

    def get(self, category_id: int) -> Category:
        """Return one category. Raises ``NotFoundError`` if absent."""
        ...

    def create(self, record: Category) -> Category:
        """Persist a new category, returning it with ``id`` set."""
        ...

    def delete(self, category_id: int) -> None:
        """Delete a category. Raises ``NotFoundError`` if absent."""
        ...

    def count_references(self, category_id: int) -> int:
        """Number of budgets, budget items, and expenses using this category."""
        ...
