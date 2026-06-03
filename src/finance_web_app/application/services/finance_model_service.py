"""Builds the per-day :class:`MonthlyModel` from the four resources.

A recurring record contributes on a day when it is active (within its effective
range) and its recurrence fires that day. Income exceptions override a stream's
amount on their date; budgets are prorated evenly across the month. See
``docs/ARCHITECTURE.md`` -> "FinanceModelService contract".
"""

from __future__ import annotations

from calendar import monthrange
from collections.abc import Iterable
from datetime import date

from finance_web_app.core.contracts.budget_repository import BudgetRepository
from finance_web_app.core.contracts.commitment_repository import CommitmentRepository
from finance_web_app.core.contracts.expense_repository import ExpenseRepository
from finance_web_app.core.contracts.income_repository import IncomeRepository
from finance_web_app.domain.money import Money
from finance_web_app.domain.monthly_model import MonthlyModel
from finance_web_app.domain.records import Commitment, Income


def _sum_money(items: Iterable[Money]) -> Money:
    return Money.from_pence(sum(item.pence() for item in items))


def _active_on(when: date, record: Commitment | Income) -> bool:
    stop = record.effective_stop
    return (stop is None or when <= stop) and record.recurrence.fires_on(
        when, record.effective_from
    )


class FinanceModelService:
    def __init__(
        self,
        incomes: IncomeRepository,
        commitments: CommitmentRepository,
        expenses: ExpenseRepository,
        budgets: BudgetRepository,
    ) -> None:
        self._incomes = incomes
        self._commitments = commitments
        self._expenses = expenses
        self._budgets = budgets

    def model_for_month(self, year: int, month: int) -> MonthlyModel:
        days_in_month = monthrange(year, month)[1]
        days = [date(year, month, day) for day in range(1, days_in_month + 1)]

        incomes = self._incomes.list_effective(year, month)
        commitments = self._commitments.list_effective(year, month)
        expenses = self._expenses.list_effective(year, month)
        budgets = self._budgets.list_effective(year, month)

        exceptions: dict[int, dict[date, Money]] = {}
        for income in incomes:
            if income.id is None:
                continue
            exceptions[income.id] = {
                exc.date: exc.quantity for exc in self._incomes.list_exceptions(income.id)
            }

        # Prorate each budget across the month, then sum per day (integer pence).
        budget_pence = [0] * days_in_month
        for budget in budgets:
            for index, part in enumerate(budget.quantity.split_evenly(days_in_month)):
                budget_pence[index] += part.pence()

        return MonthlyModel(
            dates=days,
            income_per_day=[self._income_on(day, incomes, exceptions) for day in days],
            commitments_per_day=[
                _sum_money(c.quantity for c in commitments if _active_on(day, c)) for day in days
            ],
            expenses_per_day=[
                _sum_money(e.quantity for e in expenses if e.date == day) for day in days
            ],
            budget_allocated_per_day=[Money.from_pence(p) for p in budget_pence],
        )

    @staticmethod
    def _income_on(
        when: date, incomes: list[Income], exceptions: dict[int, dict[date, Money]]
    ) -> Money:
        pence = 0
        for income in incomes:
            if income.id is None:
                continue
            override = exceptions.get(income.id, {})
            if when in override:
                pence += override[when].pence()
            elif _active_on(when, income):
                pence += income.quantity.pence()
        return Money.from_pence(pence)
