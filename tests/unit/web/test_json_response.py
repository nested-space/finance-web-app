"""Unit test for the dashboard JSON payload shaper."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from finance_web_app.application.services.insights_service import MonthlyInsights
from finance_web_app.domain.money import Money
from finance_web_app.domain.monthly_model import MonthlyModel
from finance_web_app.domain.records import Category
from finance_web_app.web.rendering.json_response import (
    budgets_charts_payload,
    expenses_charts_payload,
    expenses_curve_payload,
    finance_dashboard_payload,
)

pytestmark = pytest.mark.unit


def test_expenses_curve_and_charts_payload() -> None:
    curve = expenses_curve_payload(
        [Money.from_pence(0), Money.from_pence(1000)],
        [Money.from_pence(500), Money.from_pence(1000)],
    )
    assert curve == {
        "labels": [1, 2],
        "spend_cumulative": [0.0, 10.0],
        "budget_cumulative": [5.0, 10.0],
    }
    payload = expenses_charts_payload(
        2026,
        6,
        curve,
        {Category.GROCERIES: Money.from_pence(1000)},
        (["May 2026", "Jun 2026"], [Money.from_pence(500), Money.from_pence(1500)]),
    )
    data: Any = json.loads(json.dumps(payload))
    assert data["year"] == 2026 and data["month"] == 6
    assert data["current_month"]["spend_cumulative"] == [0.0, 10.0]
    assert data["breakdown"] == {"labels": ["Groceries"], "values": [10.0]}
    assert data["history"]["spend_cumulative"] == [5.0, 15.0]


def test_budgets_charts_payload_shapes_and_serialises() -> None:
    payload = budgets_charts_payload(
        {Category.GROCERIES: Money.from_pence(20000)},
        {Category.GROCERIES: Money.from_pence(10000)},
        (
            ["May 2026", "Jun 2026"],
            [Money.from_pence(10000), Money.from_pence(20000)],
            [Money.from_pence(5000), Money.from_pence(25000)],
        ),
    )
    data: Any = json.loads(json.dumps(payload))
    assert data["spend_vs_budget"] == {"labels": ["Groceries"], "spend": [200.0], "budget": [100.0]}
    assert data["breakdown"] == {"labels": ["Groceries"], "values": [100.0]}
    assert data["history"]["budget_cumulative"] == [100.0, 200.0]
    assert data["history"]["spend_cumulative"] == [50.0, 250.0]


def test_payload_shapes_money_as_float_pounds_and_is_json_serialisable() -> None:
    model = MonthlyModel(
        dates=[date(2026, 6, 1)],
        income_per_day=[Money.from_pence(250000)],
        commitments_per_day=[Money.from_pence(0)],
        expenses_per_day=[Money.from_pence(5000)],
        budget_allocated_per_day=[Money.from_pence(0)],
    )
    insights = MonthlyInsights(
        total_income=Money.from_pence(250000),
        total_outgoings=Money.from_pence(5000),
        net=Decimal("2450.00"),
        closing_balance=Decimal("2450.00"),
        largest_expense=("Shoes", Money.from_pence(5000)),
        over_budget=[Category.GROCERIES],
    )
    payload = finance_dashboard_payload(
        2026,
        6,
        model,
        insights,
        {Category.GROCERIES: Money.from_pence(20000)},
        {Category.ENTERTAINMENT: Money.from_pence(999)},
    )

    # Round-trips through JSON (proves serialisability and float conversion).
    data: Any = json.loads(json.dumps(payload))
    assert data["labels"] == [1]
    assert data["income_outgoings"]["income"] == [2500.0]
    assert data["income_outgoings"]["outgoings"] == [50.0]
    assert data["budget_breakdown"] == {"labels": ["Groceries"], "values": [200.0]}
    assert data["commitments_by_category"] == {"labels": ["Entertainment"], "values": [9.99]}
    assert data["insights"]["largest_expense"] == {"name": "Shoes", "amount": 50.0}
    assert data["insights"]["over_budget"] == ["Groceries"]
    assert isinstance(data["insights"]["net"], float)
