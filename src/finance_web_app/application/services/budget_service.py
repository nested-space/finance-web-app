"""Budget use cases.

Invoked directly by the budgets blueprint. Depends only on the repository
Protocol and domain types -- never on a concrete repository or on ``web``
(``docs/ARCHITECTURE.md`` -> "Layer map").
"""

from __future__ import annotations

from finance_web_app.core.contracts.budget_repository import BudgetRepository
from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.effective_period import EffectivePeriod
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import BudgetRecord, Category


class BudgetService:
    def __init__(self, budgets: BudgetRepository) -> None:
        self._budgets = budgets

    def list_all(self) -> list[BudgetRecord]:
        return self._budgets.list_all()

    def list_effective(self, year: int, month: int) -> list[BudgetRecord]:
        return self._budgets.list_effective(year, month)

    def create(
        self,
        *,
        name: str,
        quantity: Money,
        category: Category,
        period: EffectivePeriod,
    ) -> BudgetRecord:
        try:
            record = BudgetRecord(name=name, quantity=quantity, category=category, period=period)
        except ValueError as exc:
            raise ValidationError("name", str(exc)) from exc
        return self._budgets.create(record)

    def delete(self, budget_id: int) -> None:
        self._budgets.delete(budget_id)
