"""The per-day finance model for a single month.

A pure value object: per-day amount series are non-negative ``Money``; the
balance helpers return signed ``Decimal`` because a running balance can go
negative (``Money`` cannot). See ``docs/ARCHITECTURE.md`` -> "FinanceModelService
contract".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from finance_web_app.domain.money import Money


@dataclass(frozen=True)
class MonthlyModel:
    dates: list[date]
    income_per_day: list[Money]
    commitments_per_day: list[Money]
    expenses_per_day: list[Money]
    budget_allocated_per_day: list[Money]

    def __post_init__(self) -> None:
        n = len(self.dates)
        for series in (
            self.income_per_day,
            self.commitments_per_day,
            self.expenses_per_day,
            self.budget_allocated_per_day,
        ):
            if len(series) != n:
                raise ValueError("every per-day series must match the number of dates")

    def net_per_day(self) -> list[Decimal]:
        """Cash flow per day: income minus commitments and expenses (not budgets)."""
        return [
            income.amount - commitment.amount - expense.amount
            for income, commitment, expense in zip(
                self.income_per_day,
                self.commitments_per_day,
                self.expenses_per_day,
                strict=True,
            )
        ]

    def cumulative_balance(self) -> list[Decimal]:
        """Running balance from zero (the dashboard's finance-model line)."""
        return self._running(Decimal("0.00"))

    def subtractive_balance(self, starting: Money) -> list[Decimal]:
        """Running balance from a given opening amount (no UI in v1.0.0)."""
        return self._running(starting.amount)

    def _running(self, start: Decimal) -> list[Decimal]:
        balances: list[Decimal] = []
        total = start
        for net in self.net_per_day():
            total += net
            balances.append(total)
        return balances
