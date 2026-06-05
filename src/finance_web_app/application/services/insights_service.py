"""Monthly insights for the dashboard card.

A small, well-defined set of figures computed entirely server-side from the
finance model and the underlying records (never in JavaScript).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from finance_web_app.application.services.finance_model_service import FinanceModelService
from finance_web_app.core.contracts.budget_repository import BudgetRepository
from finance_web_app.core.contracts.category_repository import CategoryRepository
from finance_web_app.core.contracts.expense_repository import ExpenseRepository
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Expense


@dataclass(frozen=True)
class MonthlyInsights:
    total_income: Money
    total_outgoings: Money
    net: Decimal
    closing_balance: Decimal
    largest_expense: tuple[str, Money] | None
    over_budget: list[str]


def _sum_pence(items: list[Money]) -> Money:
    return Money.from_pence(sum(item.pence() for item in items))


class InsightsService:
    def __init__(
        self,
        finance_model: FinanceModelService,
        expenses: ExpenseRepository,
        budgets: BudgetRepository,
        categories: CategoryRepository,
    ) -> None:
        self._finance_model = finance_model
        self._expenses = expenses
        self._budgets = budgets
        self._categories = categories

    def insights_for_month(self, year: int, month: int) -> MonthlyInsights:
        model = self._finance_model.model_for_month(year, month)
        total_income = _sum_pence(model.income_per_day)
        total_outgoings = Money.from_pence(
            sum(m.pence() for m in model.commitments_per_day)
            + sum(m.pence() for m in model.expenses_per_day)
        )
        balances = model.cumulative_balance()
        closing_balance = balances[-1] if balances else Decimal("0.00")

        expenses = self._expenses.list_effective(year, month)
        largest = max(expenses, key=lambda e: e.quantity.pence(), default=None)

        return MonthlyInsights(
            total_income=total_income,
            total_outgoings=total_outgoings,
            net=total_income.amount - total_outgoings.amount,
            closing_balance=closing_balance,
            largest_expense=(largest.name, largest.quantity) if largest is not None else None,
            over_budget=self._over_budget(year, month, expenses),
        )

    def _over_budget(self, year: int, month: int, expenses: list[Expense]) -> list[str]:
        caps: dict[int, int] = {}
        for budget in self._budgets.list_effective(year, month):
            caps[budget.category_id] = caps.get(budget.category_id, 0) + budget.quantity.pence()
        spend: dict[int, int] = {}
        for expense in expenses:
            spend[expense.category_id] = (
                spend.get(expense.category_id, 0) + expense.quantity.pence()
            )
        over = {category_id for category_id, cap in caps.items() if spend.get(category_id, 0) > cap}
        return [category.name for category in self._categories.list_all() if category.id in over]
