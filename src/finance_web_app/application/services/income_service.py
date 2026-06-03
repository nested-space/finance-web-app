"""Income use cases."""

from __future__ import annotations

from datetime import date

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.core.contracts.income_repository import IncomeRepository
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Income
from finance_web_app.domain.recurrence import Recurrence


class IncomeService:
    def __init__(self, incomes: IncomeRepository) -> None:
        self._incomes = incomes

    def list_all(self) -> list[Income]:
        return self._incomes.list_all()

    def list_effective(self, year: int, month: int) -> list[Income]:
        return self._incomes.list_effective(year, month)

    def create(
        self,
        *,
        name: str,
        quantity: Money,
        recurrence: Recurrence,
        effective_from: date,
        effective_stop: date | None,
    ) -> Income:
        if not name:
            raise ValidationError("name", "must be non-empty")
        record = Income(
            name=name,
            quantity=quantity,
            recurrence=recurrence,
            effective_from=effective_from,
            effective_stop=effective_stop,
        )
        return self._incomes.create(record)

    def delete(self, income_id: int) -> None:
        self._incomes.delete(income_id)
