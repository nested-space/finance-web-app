"""SQLModel income repository, including the exception child table."""

from __future__ import annotations

from typing import ClassVar

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import col, select

from finance_web_app.core.contracts.errors import RepositoryError
from finance_web_app.domain.records import Income, IncomeException
from finance_web_app.infrastructure.persistence.base_repository import SqlModelRepository


class SqlIncomeRepository(SqlModelRepository[Income]):
    model = Income
    resource_name: ClassVar[str] = "income"

    def list_effective(self, year: int, month: int) -> list[Income]:
        return [i for i in self.list_all() if i.period.covers_month(year, month)]

    def add_exception(self, income_id: int, exception: IncomeException) -> None:
        exception.income_id = income_id
        try:
            self._session.add(exception)
            self._session.commit()
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise RepositoryError("add income exception", exc) from exc

    def list_exceptions(self, income_id: int) -> list[IncomeException]:
        try:
            statement = select(IncomeException).where(col(IncomeException.income_id) == income_id)
            return list(self._session.exec(statement).all())
        except SQLAlchemyError as exc:
            raise RepositoryError("list income exceptions", exc) from exc
