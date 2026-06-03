"""SQLModel commitment repository."""

from __future__ import annotations

from typing import ClassVar

from finance_web_app.domain.records import Commitment
from finance_web_app.infrastructure.persistence.base_repository import SqlModelRepository


class SqlCommitmentRepository(SqlModelRepository[Commitment]):
    model = Commitment
    resource_name: ClassVar[str] = "commitment"

    def list_effective(self, year: int, month: int) -> list[Commitment]:
        return [c for c in self.list_all() if c.period.covers_month(year, month)]
