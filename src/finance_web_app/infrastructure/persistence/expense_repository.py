"""SQLModel expense repository.

Inherits CRUD from the generic base; ``list_effective`` uses the stricter
expense date predicate (``Expense.in_month``), not ``covers_month``.
"""

from __future__ import annotations

from typing import ClassVar

from finance_web_app.domain.records import Expense
from finance_web_app.infrastructure.persistence.base_repository import SqlModelRepository


class SqlExpenseRepository(SqlModelRepository[Expense]):
    model = Expense
    resource_name: ClassVar[str] = "expense"

    def list_effective(self, year: int, month: int) -> list[Expense]:
        return [e for e in self.list_all() if e.in_month(year, month)]
