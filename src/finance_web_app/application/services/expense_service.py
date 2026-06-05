"""Expense use cases.

An expense is tagged with a category and, optionally, a budget item (a named
label under that category). Per-category aggregates are keyed by ``category_id``;
category filters are sets of category ids.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date

from finance_web_app.core.contracts.budget_item_repository import BudgetItemRepository
from finance_web_app.core.contracts.category_repository import CategoryRepository
from finance_web_app.core.contracts.errors import NotFoundError, ValidationError
from finance_web_app.core.contracts.expense_repository import ExpenseRepository
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Expense


class ExpenseService:
    def __init__(
        self,
        expenses: ExpenseRepository,
        categories: CategoryRepository,
        items: BudgetItemRepository,
    ) -> None:
        self._expenses = expenses
        self._categories = categories
        self._items = items

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
        self, year: int, month: int, categories: set[int] | None = None
    ) -> dict[int, Money]:
        """Sum the month's expense spend per category id (for the breakdown pie)."""
        totals: dict[int, int] = {}
        for expense in self._expenses.list_effective(year, month):
            if categories is None or expense.category_id in categories:
                totals[expense.category_id] = (
                    totals.get(expense.category_id, 0) + expense.quantity.pence()
                )
        return {category_id: Money.from_pence(pence) for category_id, pence in totals.items()}

    def cumulative_spend(
        self, year: int, month: int, categories: set[int] | None = None
    ) -> list[Money]:
        """Per-day running spend through the month, optionally filtered to category ids."""
        days_in_month = monthrange(year, month)[1]
        daily = [0] * days_in_month
        for expense in self._expenses.list_effective(year, month):
            if categories is None or expense.category_id in categories:
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
        category_id: int,
        budget_item_id: int | None,
        date: date,
        description: str | None,
    ) -> Expense:
        if not name:
            raise ValidationError("name", "must be non-empty")
        try:
            self._categories.get(category_id)
        except NotFoundError:
            raise ValidationError("category", "does not exist") from None
        if budget_item_id is not None:
            try:
                item = self._items.get(budget_item_id)
            except NotFoundError:
                raise ValidationError("budget_item", "does not exist") from None
            if item.category_id != category_id:
                raise ValidationError("budget_item", "does not belong to the selected category")
        record = Expense(
            name=name,
            quantity=quantity,
            category_id=category_id,
            budget_item_id=budget_item_id,
            date=date,
            description=description,
        )
        return self._expenses.create(record)

    def delete(self, expense_id: int) -> None:
        self._expenses.delete(expense_id)
