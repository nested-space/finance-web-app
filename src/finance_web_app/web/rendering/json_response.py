"""Dashboard JSON shaping — the single home for the chart/insights payload.

This payload is the public contract embedded in the page and returned by
``/finance/api/model`` (changing its shape is a MAJOR SemVer bump). ``Money`` and
``Decimal`` are converted to JSON ``float`` pounds at this presentation boundary;
all aggregation has already happened in services.
"""

from __future__ import annotations

from decimal import Decimal

from finance_web_app.application.services.insights_service import MonthlyInsights
from finance_web_app.domain.money import Money
from finance_web_app.domain.monthly_model import MonthlyModel
from finance_web_app.domain.records import Category
from finance_web_app.web.rendering.template_context import CATEGORY_LABELS


def _pounds(value: Money | Decimal) -> float:
    amount = value.amount if isinstance(value, Money) else value
    return float(amount)


def finance_dashboard_payload(
    year: int,
    month: int,
    model: MonthlyModel,
    insights: MonthlyInsights,
    budget_totals: dict[Category, Money],
    commitment_totals: dict[Category, Money],
) -> dict[str, object]:
    outgoings = [
        _pounds(commitment.amount + expense.amount)
        for commitment, expense in zip(
            model.commitments_per_day, model.expenses_per_day, strict=True
        )
    ]
    return {
        "year": year,
        "month": month,
        "labels": [d.day for d in model.dates],
        "finance_model": {"balance": [_pounds(b) for b in model.cumulative_balance()]},
        "income_outgoings": {
            "income": [_pounds(m) for m in model.income_per_day],
            "outgoings": outgoings,
        },
        "budget_breakdown": _category_series(budget_totals),
        "commitments_by_category": _category_series(commitment_totals),
        "insights": _insights_payload(insights),
    }


def _category_series(totals: dict[Category, Money]) -> dict[str, object]:
    present = [category for category in Category if category in totals]
    return {
        "labels": [CATEGORY_LABELS[category] for category in present],
        "values": [_pounds(totals[category]) for category in present],
    }


def budgets_charts_payload(
    spend_by_category: dict[Category, Money],
    cap_by_category: dict[Category, Money],
    history: tuple[list[str], list[Money], list[Money]],
) -> dict[str, object]:
    zero = Money.from_pence(0)
    categories = [c for c in Category if c in cap_by_category or c in spend_by_category]
    labels, budget_cumulative, spend_cumulative = history
    return {
        "spend_vs_budget": {
            "labels": [CATEGORY_LABELS[c] for c in categories],
            "spend": [_pounds(spend_by_category.get(c, zero)) for c in categories],
            "budget": [_pounds(cap_by_category.get(c, zero)) for c in categories],
        },
        "breakdown": _category_series(cap_by_category),
        "history": {
            "labels": labels,
            "budget_cumulative": [_pounds(m) for m in budget_cumulative],
            "spend_cumulative": [_pounds(m) for m in spend_cumulative],
        },
    }


def _insights_payload(insights: MonthlyInsights) -> dict[str, object]:
    largest = insights.largest_expense
    return {
        "total_income": _pounds(insights.total_income),
        "total_outgoings": _pounds(insights.total_outgoings),
        "net": _pounds(insights.net),
        "closing_balance": _pounds(insights.closing_balance),
        "largest_expense": (
            {"name": largest[0], "amount": _pounds(largest[1])} if largest is not None else None
        ),
        "over_budget": [CATEGORY_LABELS[category] for category in insights.over_budget],
    }
