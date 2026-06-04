"""Six-month cumulative history for the budgets and expenses pages.

Composes the budget and expense services to produce a running total across the
last six months (each month adds that month's total). All aggregation is here,
not in JavaScript.
"""

from __future__ import annotations

from calendar import month_abbr

from finance_web_app.application.services.budget_service import BudgetService
from finance_web_app.application.services.expense_service import ExpenseService
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Category


def _label(year: int, month: int) -> str:
    return f"{month_abbr[month]} {year}"


class HistoryService:
    def __init__(self, budgets: BudgetService, expenses: ExpenseService) -> None:
        self._budgets = budgets
        self._expenses = expenses

    @staticmethod
    def last_six_months(year: int, month: int) -> list[tuple[int, int]]:
        """The six months ending at (year, month), oldest first."""
        base = year * 12 + (month - 1)
        return [((base - offset) // 12, (base - offset) % 12 + 1) for offset in range(5, -1, -1)]

    def budget_history(self, year: int, month: int) -> tuple[list[str], list[Money], list[Money]]:
        labels: list[str] = []
        budget_cumulative: list[Money] = []
        spend_cumulative: list[Money] = []
        budget_total = 0
        spend_total = 0
        for y, m in self.last_six_months(year, month):
            labels.append(_label(y, m))
            budget_total += self._budgets.total(y, m).pence()
            spend_total += self._expenses.total(y, m).pence()
            budget_cumulative.append(Money.from_pence(budget_total))
            spend_cumulative.append(Money.from_pence(spend_total))
        return labels, budget_cumulative, spend_cumulative

    def expense_history(
        self, year: int, month: int, categories: set[Category] | None = None
    ) -> tuple[list[str], list[Money]]:
        labels: list[str] = []
        spend_cumulative: list[Money] = []
        spend_total = 0
        for y, m in self.last_six_months(year, month):
            labels.append(_label(y, m))
            spend_total += sum(
                v.pence() for v in self._expenses.totals_by_category(y, m, categories).values()
            )
            spend_cumulative.append(Money.from_pence(spend_total))
        return labels, spend_cumulative
