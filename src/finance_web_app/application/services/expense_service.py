"""Expense use cases."""

from __future__ import annotations

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
