"""Unit tests for InsightsService."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from finance_web_app.application.services.insights_service import InsightsService
from finance_web_app.core.contracts.budget_repository import BudgetRepository
from finance_web_app.core.contracts.commitment_repository import CommitmentRepository
from finance_web_app.core.contracts.expense_repository import ExpenseRepository
from finance_web_app.core.contracts.income_repository import IncomeRepository
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Budget, Commitment, Expense, Income
from finance_web_app.domain.recurrence import Recurrence

pytestmark = pytest.mark.unit

GROCERIES = 2  # seeded category id (see conftest SEED_CATEGORY_IDS)
CLOTHING = 3
ENTERTAINMENT = 4


def test_insights_for_a_seeded_month(
    insights_service: InsightsService,
    fake_income_repository: IncomeRepository,
    fake_commitment_repository: CommitmentRepository,
    fake_expense_repository: ExpenseRepository,
    fake_budget_repository: BudgetRepository,
) -> None:
    fake_income_repository.create(
        Income(
            name="Salary",
            quantity=Money.from_pence(250000),
            recurrence=Recurrence.MONTHLY,
            effective_from=date(2026, 6, 15),
        )
    )
    fake_commitment_repository.create(
        Commitment(
            name="Gym",
            quantity=Money.from_pence(1000),
            category_id=ENTERTAINMENT,
            recurrence=Recurrence.DAILY,
            effective_from=date(2026, 6, 1),
            effective_stop=date(2026, 6, 3),
        )
    )
    fake_expense_repository.create(
        Expense(
            name="Shoes",
            quantity=Money.from_pence(5000),
            category_id=CLOTHING,
            date=date(2026, 6, 10),
        )
    )
    fake_expense_repository.create(
        Expense(
            name="Food",
            quantity=Money.from_pence(20000),
            category_id=GROCERIES,
            date=date(2026, 6, 5),
        )
    )
    fake_budget_repository.create(
        Budget(
            quantity=Money.from_pence(10000),
            category_id=GROCERIES,
            effective_from=date(2026, 6, 1),
        )
    )

    insights = insights_service.insights_for_month(2026, 6)

    assert insights.total_income == Money.from_pence(250000)
    assert insights.total_outgoings == Money.from_pence(28000)  # 3000 + 5000 + 20000
    assert insights.net == Decimal("2220.00")
    assert insights.closing_balance == Decimal("2220.00")
    assert insights.largest_expense == ("Food", Money.from_pence(20000))
    assert insights.over_budget == ["Groceries"]


def test_empty_month_has_no_largest_expense_and_zero_net(
    insights_service: InsightsService,
) -> None:
    insights = insights_service.insights_for_month(2026, 2)
    assert insights.largest_expense is None
    assert insights.net == Decimal("0.00")
    assert insights.over_budget == []
