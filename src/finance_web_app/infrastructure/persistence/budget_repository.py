"""SQLModel budget repository.

Inherits CRUD from the generic base and adds only the date-effective query, which
reuses the single ``EffectivePeriod.covers_month`` predicate.
"""

from __future__ import annotations

from typing import ClassVar

from finance_web_app.domain.records import Budget
from finance_web_app.infrastructure.persistence.base_repository import SqlModelRepository


class SqlBudgetRepository(SqlModelRepository[Budget]):
    model = Budget
    resource_name: ClassVar[str] = "budget"

    def list_effective(self, year: int, month: int) -> list[Budget]:
        return [b for b in self.list_all() if b.period.covers_month(year, month)]
