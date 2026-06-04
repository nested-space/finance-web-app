"""Expense use cases."""

from __future__ import annotations

from calendar import monthrange
from datetime import date

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.core.contracts.expense_repository import ExpenseRepository
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Category, Expense


class ExpenseService:
    def __init__(self, expenses: ExpenseRepository) -> None:
        self._expenses = expenses

    def list_all(self) -> list[Expense]:
        return self._expenses.list_all()

    def list_effective(self, year: int, month: int) -> list[Expense]:
        return self._expenses.list_effective(year, month)

    def total(self, year: int, month: int) -> Money:
        """Total expense spend for the month."""
        return Money.from_pence(
            sum(e.quantity.pence() for e in self._expenses.list_effective(year, month))
        )

    def totals_by_category(
        self, year: int, month: int, categories: set[Category] | None = None
    ) -> dict[Category, Money]:
        """Sum the month's expense spend per category (for the breakdown pie)."""
        totals: dict[Category, int] = {}
        for expense in self._expenses.list_effective(year, month):
            if categories is None or expense.category in categories:
                totals[expense.category] = (
                    totals.get(expense.category, 0) + expense.quantity.pence()
                )
        return {category: Money.from_pence(pence) for category, pence in totals.items()}

    def cumulative_spend(
        self, year: int, month: int, categories: set[Category] | None = None
    ) -> list[Money]:
        """Per-day running spend through the month, optionally filtered to categories."""
        days_in_month = monthrange(year, month)[1]
        daily = [0] * days_in_month
        for expense in self._expenses.list_effective(year, month):
            if categories is None or expense.category in categories:
                daily[expense.date.day - 1] += expense.quantity.pence()
        running = 0
        cumulative: list[Money] = []
        for pence in daily:
            running += pence
            cumulative.append(Money.from_pence(running))
        return cumulative

    def create(
        self,
        *,
        name: str,
        quantity: Money,
        category: Category,
        date: date,
        description: str | None,
    ) -> Expense:
        if not name:
            raise ValidationError("name", "must be non-empty")
        record = Expense(
            name=name,
            quantity=quantity,
            category=category,
            date=date,
            description=description,
        )
        return self._expenses.create(record)

    def delete(self, expense_id: int) -> None:
        self._expenses.delete(expense_id)
