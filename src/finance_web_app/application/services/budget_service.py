"""Budget use cases.

Invoked directly by the budgets blueprint. A budget is a per-category monthly
cap over an effective date range; the category carries the amount (budgets no
longer have a name). Per-category aggregates are keyed by ``category_id``; the
rendering layer resolves ids to names. Depends only on the repository Protocols
and domain types -- never on a concrete repository or on ``web``.
"""

from __future__ import annotations

from calendar import monthrange

from finance_web_app.core.contracts.budget_repository import BudgetRepository
from finance_web_app.core.contracts.category_repository import CategoryRepository
from finance_web_app.core.contracts.errors import NotFoundError, ValidationError
from finance_web_app.domain.effective_period import EffectivePeriod
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Budget


class BudgetService:
    def __init__(self, budgets: BudgetRepository, categories: CategoryRepository) -> None:
        self._budgets = budgets
        self._categories = categories

    def list_all(self) -> list[Budget]:
        return self._budgets.list_all()

    def get(self, budget_id: int) -> Budget:
        return self._budgets.get(budget_id)

    def list_effective(self, year: int, month: int) -> list[Budget]:
        return self._budgets.list_effective(year, month)

    def total(self, year: int, month: int) -> Money:
        """Total budget cap effective in the month."""
        return Money.from_pence(
            sum(b.quantity.pence() for b in self._budgets.list_effective(year, month))
        )

    def totals_by_category(self, year: int, month: int) -> dict[int, Money]:
        """Sum the month's budget caps per category id (for the breakdown pie)."""
        totals: dict[int, int] = {}
        for budget in self._budgets.list_effective(year, month):
            totals[budget.category_id] = totals.get(budget.category_id, 0) + budget.quantity.pence()
        return {category_id: Money.from_pence(pence) for category_id, pence in totals.items()}

    def cumulative_allocation(
        self, year: int, month: int, categories: set[int] | None = None
    ) -> list[Money]:
        """Straight-line per-day cumulative budget for the selected category ids.

        The total cap is prorated evenly across the month (exact pence) and
        accumulated -- the budget reference line on the expenses spend curve.
        """
        days_in_month = monthrange(year, month)[1]
        caps = self.totals_by_category(year, month)
        total_pence = sum(
            money.pence()
            for category_id, money in caps.items()
            if categories is None or category_id in categories
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
        quantity: Money,
        category_id: int,
        period: EffectivePeriod,
    ) -> Budget:
        try:
            self._categories.get(category_id)
        except NotFoundError:
            raise ValidationError("category", "does not exist") from None
        record = Budget(
            quantity=quantity,
            category_id=category_id,
            effective_from=period.from_date,
            effective_stop=period.stop_date,
        )
        return self._budgets.create(record)

    def delete(self, budget_id: int) -> None:
        self._budgets.delete(budget_id)
