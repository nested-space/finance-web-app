"""Unit tests for FinanceModelService against the fake repositories."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from finance_web_app.application.services.finance_model_service import FinanceModelService
from finance_web_app.core.contracts.budget_repository import BudgetRepository
from finance_web_app.core.contracts.commitment_repository import CommitmentRepository
from finance_web_app.core.contracts.expense_repository import ExpenseRepository
from finance_web_app.core.contracts.income_repository import IncomeRepository
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import (
    Budget,
    Category,
    Commitment,
    Expense,
    Income,
    IncomeException,
)
from finance_web_app.domain.recurrence import Recurrence

pytestmark = pytest.mark.unit


def test_model_for_june_combines_all_resources(
    finance_model_service: FinanceModelService,
    fake_income_repository: IncomeRepository,
    fake_commitment_repository: CommitmentRepository,
    fake_expense_repository: ExpenseRepository,
    fake_budget_repository: BudgetRepository,
) -> None:
    income = fake_income_repository.create(
        Income(
            name="Salary",
            quantity=Money.from_pence(250000),
            recurrence=Recurrence.MONTHLY,
            effective_from=date(2026, 6, 15),
        )
    )
    assert income.id is not None
    fake_income_repository.add_exception(
        income.id, IncomeException(date=date(2026, 6, 20), quantity=Money.from_pence(300000))
    )
    fake_commitment_repository.create(
        Commitment(
            name="Gym",
            quantity=Money.from_pence(1000),
            category=Category.ENTERTAINMENT,
            recurrence=Recurrence.DAILY,
            effective_from=date(2026, 6, 1),
            effective_stop=date(2026, 6, 3),
        )
    )
    fake_expense_repository.create(
        Expense(
            name="Shoes",
            quantity=Money.from_pence(5000),
            category=Category.CLOTHING,
            date=date(2026, 6, 10),
        )
    )
    fake_budget_repository.create(
        Budget(
            name="Food",
            quantity=Money.from_pence(30000),
            category=Category.GROCERIES,
            effective_from=date(2026, 6, 1),
        )
    )

    model = finance_model_service.model_for_month(2026, 6)

    assert len(model.dates) == 30
    # Monthly income fires on the 15th; the exception overrides the 20th.
    assert model.income_per_day[14] == Money.from_pence(250000)
    assert model.income_per_day[19] == Money.from_pence(300000)
    assert model.income_per_day[0] == Money.from_pence(0)
    # Daily commitment, active days 1-3 only.
    assert [m.pence() for m in model.commitments_per_day[:4]] == [1000, 1000, 1000, 0]
    # Expense on the 10th.
    assert model.expenses_per_day[9] == Money.from_pence(5000)
    # Budget £300 prorated exactly over 30 days -> £10/day.
    assert all(m.pence() == 1000 for m in model.budget_allocated_per_day)
    # Closing balance = income - commitments - expenses.
    assert model.cumulative_balance()[-1] == Decimal("5420.00")


def test_record_starting_mid_month_does_not_contribute_earlier(
    finance_model_service: FinanceModelService,
    fake_commitment_repository: CommitmentRepository,
) -> None:
    fake_commitment_repository.create(
        Commitment(
            name="Late",
            quantity=Money.from_pence(500),
            category=Category.KIDS,
            recurrence=Recurrence.DAILY,
            effective_from=date(2026, 6, 20),
            effective_stop=date(2026, 6, 30),
        )
    )
    model = finance_model_service.model_for_month(2026, 6)
    assert model.commitments_per_day[18] == Money.from_pence(0)  # the 19th
    assert model.commitments_per_day[19] == Money.from_pence(500)  # the 20th


def test_empty_month_is_all_zero(finance_model_service: FinanceModelService) -> None:
    model = finance_model_service.model_for_month(2026, 2)
    assert len(model.dates) == 28
    assert model.cumulative_balance()[-1] == Decimal("0.00")
