"""SQLModel budget item repository.

Inherits CRUD from the generic base and adds the per-category listing used to
populate the budget-item selects.
"""

from __future__ import annotations

from typing import ClassVar

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from finance_web_app.core.contracts.errors import RepositoryError
from finance_web_app.domain.records import BudgetItem
from finance_web_app.infrastructure.persistence.base_repository import SqlModelRepository


class SqlBudgetItemRepository(SqlModelRepository[BudgetItem]):
    model = BudgetItem
    resource_name: ClassVar[str] = "budget_item"

    def list_by_category(self, category_id: int) -> list[BudgetItem]:
        try:
            statement = select(BudgetItem).where(BudgetItem.category_id == category_id)
            return list(self._session.exec(statement).all())
        except SQLAlchemyError as exc:
            raise RepositoryError(f"list {self.resource_name} by category", exc) from exc
