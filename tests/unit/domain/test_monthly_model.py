"""Unit tests for MonthlyModel per-day series and balance helpers."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from finance_web_app.domain.money import Money
from finance_web_app.domain.monthly_model import MonthlyModel

pytestmark = pytest.mark.unit


def _model(
    *,
    income: list[int],
    commitments: list[int],
    expenses: list[int],
    budgets: list[int] | None = None,
) -> MonthlyModel:
    n = len(income)
    dates = [date(2026, 6, day) for day in range(1, n + 1)]
    return MonthlyModel(
        dates=dates,
        income_per_day=[Money.from_pence(p) for p in income],
        commitments_per_day=[Money.from_pence(p) for p in commitments],
        expenses_per_day=[Money.from_pence(p) for p in expenses],
        budget_allocated_per_day=[Money.from_pence(p) for p in (budgets or [0] * n)],
    )


def test_net_per_day() -> None:
    model = _model(income=[1000, 0], commitments=[200, 0], expenses=[100, 50])
    assert model.net_per_day() == [Decimal("7.00"), Decimal("-0.50")]


def test_cumulative_balance_runs_and_can_go_negative() -> None:
    model = _model(income=[0, 0, 0], commitments=[100, 100, 100], expenses=[0, 0, 0])
    assert model.cumulative_balance() == [Decimal("-1.00"), Decimal("-2.00"), Decimal("-3.00")]


def test_subtractive_balance_starts_from_opening() -> None:
    model = _model(income=[0, 0], commitments=[100, 100], expenses=[0, 0])
    assert model.subtractive_balance(Money.from_pence(500)) == [Decimal("4.00"), Decimal("3.00")]


def test_subtractive_from_zero_equals_cumulative() -> None:
    model = _model(income=[300, 0], commitments=[0, 100], expenses=[0, 0])
    assert model.subtractive_balance(Money.from_pence(0)) == model.cumulative_balance()


def test_mismatched_series_length_is_rejected() -> None:
    with pytest.raises(ValueError):
        MonthlyModel(
            dates=[date(2026, 6, 1)],
            income_per_day=[Money.from_pence(0), Money.from_pence(0)],
            commitments_per_day=[Money.from_pence(0)],
            expenses_per_day=[Money.from_pence(0)],
            budget_allocated_per_day=[Money.from_pence(0)],
        )
