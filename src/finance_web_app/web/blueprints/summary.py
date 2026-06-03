"""Dashboard blueprint.

Renders the monthly dashboard at ``/finance`` (current month) and
``/finance/<year>/<month>`` (deep-link / navigation target). Composes the
finance model, insights, and category aggregates into the embedded JSON payload.
"""

from __future__ import annotations

import calendar
from datetime import date

from flask import Blueprint, abort, render_template

from finance_web_app.core.runtime.container import (
    get_budget_service,
    get_commitment_service,
    get_finance_model_service,
    get_insights_service,
)
from finance_web_app.web.rendering.json_response import finance_dashboard_payload

bp = Blueprint("summary", __name__, url_prefix="/finance")


def build_dashboard_payload(year: int, month: int) -> dict[str, object]:
    """Compose the dashboard payload (also used by the api blueprint)."""
    model = get_finance_model_service().model_for_month(year, month)
    insights = get_insights_service().insights_for_month(year, month)
    budget_totals = get_budget_service().totals_by_category(year, month)
    commitment_totals = get_commitment_service().totals_by_category(year, month)
    return finance_dashboard_payload(year, month, model, insights, budget_totals, commitment_totals)


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


@bp.get("")
def dashboard() -> str:
    today = date.today()
    return _render(today.year, today.month)


@bp.get("/<int:year>/<int:month>")
def dashboard_for_month(year: int, month: int) -> str:
    if not 1 <= month <= 12:
        abort(404)
    return _render(year, month)


def _render(year: int, month: int) -> str:
    payload = build_dashboard_payload(year, month)
    prev_year, prev_month = _shift_month(year, month, -1)
    next_year, next_month = _shift_month(year, month, 1)
    return render_template(
        "summary.html",
        payload=payload,
        month_label=f"{calendar.month_name[month]} {year}",
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
    )
