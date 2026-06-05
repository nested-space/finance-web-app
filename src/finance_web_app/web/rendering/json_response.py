"""Dashboard JSON shaping — the single home for the chart/insights payload.

This payload is the public contract embedded in the page and returned by
``/finance/api/model`` (changing its shape is a MAJOR SemVer bump). Per-category
series are keyed by ``category_id`` in the services; this boundary resolves ids to
names via the request's category list and emits JSON ``float`` pounds. All
aggregation has already happened in services.
"""

from __future__ import annotations

from decimal import Decimal

from finance_web_app.application.services.insights_service import MonthlyInsights
from finance_web_app.domain.money import Money
from finance_web_app.domain.monthly_model import MonthlyModel
from finance_web_app.domain.records import Category


def _pounds(value: Money | Decimal) -> float:
    amount = value.amount if isinstance(value, Money) else value
    return float(amount)


def finance_dashboard_payload(
    year: int,
    month: int,
    model: MonthlyModel,
    insights: MonthlyInsights,
    budget_totals: dict[int, Money],
    commitment_totals: dict[int, Money],
    categories: list[Category],
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
        "budget_breakdown": _category_series(budget_totals, categories),
        "commitments_by_category": _category_series(commitment_totals, categories),
        "insights": _insights_payload(insights),
    }


def _category_series(totals: dict[int, Money], categories: list[Category]) -> dict[str, object]:
    rows = [
        (c.name, totals[cid]) for c in categories if (cid := c.id) is not None and cid in totals
    ]
    return {
        "labels": [name for name, _ in rows],
        "values": [_pounds(value) for _, value in rows],
    }


def expenses_curve_payload(
    spend_cumulative: list[Money], budget_cumulative: list[Money]
) -> dict[str, object]:
    """The two-line spend curve (shared by the embedded default and the api)."""
    return {
        "labels": list(range(1, len(spend_cumulative) + 1)),
        "spend_cumulative": [_pounds(m) for m in spend_cumulative],
        "budget_cumulative": [_pounds(m) for m in budget_cumulative],
    }


def expenses_charts_payload(
    year: int,
    month: int,
    curve: dict[str, object],
    breakdown_totals: dict[int, Money],
    history: tuple[list[str], list[Money]],
    categories: list[Category],
) -> dict[str, object]:
    labels, spend_cumulative = history
    return {
        "year": year,
        "month": month,
        "current_month": curve,
        "breakdown": _category_series(breakdown_totals, categories),
        "history": {"labels": labels, "spend_cumulative": [_pounds(m) for m in spend_cumulative]},
    }


def budgets_charts_payload(
    spend_by_category: dict[int, Money],
    cap_by_category: dict[int, Money],
    history: tuple[list[str], list[Money], list[Money]],
    categories: list[Category],
) -> dict[str, object]:
    zero = Money.from_pence(0)
    rows = [
        (c.name, cid)
        for c in categories
        if (cid := c.id) is not None and (cid in cap_by_category or cid in spend_by_category)
    ]
    labels, budget_cumulative, spend_cumulative = history
    return {
        "spend_vs_budget": {
            "labels": [name for name, _ in rows],
            "spend": [_pounds(spend_by_category.get(cid, zero)) for _, cid in rows],
            "budget": [_pounds(cap_by_category.get(cid, zero)) for _, cid in rows],
        },
        "breakdown": _category_series(cap_by_category, categories),
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
        "over_budget": list(insights.over_budget),
    }
