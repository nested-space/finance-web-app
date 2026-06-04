"""Budget use cases.

Invoked directly by the budgets blueprint. Depends only on the repository
Protocol and domain types -- never on a concrete repository or on ``web``
(``docs/ARCHITECTURE.md`` -> "Layer map").
"""

from __future__ import annotations

from calendar import monthrange

from finance_web_app.core.contracts.budget_repository import BudgetRepository
from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.effective_period import EffectivePeriod
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Budget, Category


class BudgetService:
    def __init__(self, budgets: BudgetRepository) -> None:
        self._budgets = budgets

    def list_all(self) -> list[Budget]:
        return self._budgets.list_all()

    def list_effective(self, year: int, month: int) -> list[Budget]:
        return self._budgets.list_effective(year, month)

    def total(self, year: int, month: int) -> Money:
        """Total budget cap effective in the month."""
        return Money.from_pence(
            sum(b.quantity.pence() for b in self._budgets.list_effective(year, month))
        )

    def totals_by_category(self, year: int, month: int) -> dict[Category, Money]:
        """Sum the month's budget caps per category (for the breakdown pie)."""
        totals: dict[Category, int] = {}
        for budget in self._budgets.list_effective(year, month):
            totals[budget.category] = totals.get(budget.category, 0) + budget.quantity.pence()
        return {category: Money.from_pence(pence) for category, pence in totals.items()}

    def cumulative_allocation(
        self, year: int, month: int, categories: set[Category] | None = None
    ) -> list[Money]:
        """Straight-line per-day cumulative budget for the selected categories.

        The total cap is prorated evenly across the month (exact pence) and
        accumulated -- the budget reference line on the expenses spend curve.
        """
        days_in_month = monthrange(year, month)[1]
        caps = self.totals_by_category(year, month)
        total_pence = sum(
            money.pence()
            for category, money in caps.items()
            if categories is None or category in categories
        )
        running = 0
        cumulative: list[Money] = []
        for part in Money.from_pence(total_pence).split_evenly(days_in_month):
            running += part.pence()
            cumulative.append(Money.from_pence(running))
        return cumulative

    def create(
        self,
        *,
        name: str,
        quantity: Money,
        category: Category,
        period: EffectivePeriod,
    ) -> Budget:
        if not name:
            raise ValidationError("name", "must be non-empty")
        record = Budget(
            name=name,
            quantity=quantity,
            category=category,
            effective_from=period.from_date,
            effective_stop=period.stop_date,
        )
        return self._budgets.create(record)

    def delete(self, budget_id: int) -> None:
        self._budgets.delete(budget_id)
