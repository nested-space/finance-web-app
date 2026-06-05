"""SQLModel category repository.

Inherits CRUD from the generic base, orders by name for stable display, and adds
the reference count that backs the in-use deletion guard.
"""

from __future__ import annotations

from typing import ClassVar

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from finance_web_app.core.contracts.errors import RepositoryError
from finance_web_app.domain.records import Budget, BudgetItem, Category, Commitment, Expense
from finance_web_app.infrastructure.persistence.base_repository import SqlModelRepository


class SqlCategoryRepository(SqlModelRepository[Category]):
    model = Category
    resource_name: ClassVar[str] = "category"

    def list_all(self) -> list[Category]:
        try:
            return list(self._session.exec(select(Category).order_by(Category.name)).all())
        except SQLAlchemyError as exc:
            raise RepositoryError(f"list {self.resource_name}", exc) from exc

    def count_references(self, category_id: int) -> int:
        try:
            total = 0
            for model in (Budget, BudgetItem, Expense, Commitment):
                statement = select(func.count()).where(model.category_id == category_id)
                total += self._session.exec(statement).one()
            return total
        except SQLAlchemyError as exc:
            raise RepositoryError("count category references", exc) from exc
