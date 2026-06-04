"""Unit tests for the 6-month cumulative HistoryService."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.application.services.history_service import HistoryService
from finance_web_app.core.contracts.budget_repository import BudgetRepository
from finance_web_app.core.contracts.expense_repository import ExpenseRepository
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Budget, Category, Expense

pytestmark = pytest.mark.unit


def test_last_six_months_rolls_over_the_year() -> None:
    assert HistoryService.last_six_months(2026, 2) == [
        (2025, 9),
        (2025, 10),
        (2025, 11),
        (2025, 12),
        (2026, 1),
        (2026, 2),
    ]


def test_expense_history_is_cumulative(
    history_service: HistoryService, fake_expense_repository: ExpenseRepository
) -> None:
    fake_expense_repository.create(
        Expense(
            name="May",
            quantity=Money.from_pence(1000),
            category=Category.GROCERIES,
            date=date(2026, 5, 10),
        )
    )
    fake_expense_repository.create(
        Expense(
            name="Jun",
            quantity=Money.from_pence(2000),
            category=Category.GROCERIES,
            date=date(2026, 6, 10),
        )
    )
    labels, spend_cumulative = history_service.expense_history(2026, 6)
    assert len(labels) == 6
    assert labels[-1] == "Jun 2026"
    assert spend_cumulative[-2] == Money.from_pence(1000)  # through May
    assert spend_cumulative[-1] == Money.from_pence(3000)  # May + June


def test_budget_history_has_two_cumulative_series(
    history_service: HistoryService,
    fake_budget_repository: BudgetRepository,
    fake_expense_repository: ExpenseRepository,
) -> None:
    fake_budget_repository.create(
        Budget(
            name="cap",
            quantity=Money.from_pence(5000),
            category=Category.GROCERIES,
            effective_from=date(2026, 1, 1),
        )
    )
    fake_expense_repository.create(
        Expense(
            name="spend",
            quantity=Money.from_pence(2000),
            category=Category.GROCERIES,
            date=date(2026, 6, 3),
        )
    )
    labels, budget_cumulative, spend_cumulative = history_service.budget_history(2026, 6)
    assert len(labels) == 6
    # £50 cap effective every month of the Jan-Jun window -> cumulative £300.
    assert budget_cumulative[-1] == Money.from_pence(30000)
    assert spend_cumulative[-1] == Money.from_pence(2000)
