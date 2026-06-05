"""JSON API for post-paint refetches.

Returns data already shaped by services — no business logic here. The expenses
spend curve (category filter) (``docs/ARCHITECTURE.md`` -> "Frontend data
delivery").
"""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request
from flask.typing import ResponseReturnValue

from finance_web_app.core.runtime.container import (
    get_budget_service,
    get_category_service,
    get_expense_service,
    get_history_service,
)
from finance_web_app.web.rendering.json_response import (
    expenses_charts_payload,
    expenses_curve_payload,
)

bp = Blueprint("api", __name__, url_prefix="/finance/api")


@bp.get("/expenses/<int:year>/<int:month>")
def expenses(year: int, month: int) -> ResponseReturnValue:
    if not 1 <= month <= 12:
        abort(404)
    categories = _parse_categories(request.args.getlist("category"))
    expense_svc = get_expense_service()
    spend = expense_svc.cumulative_spend(year, month, categories)
    budget = get_budget_service().cumulative_allocation(year, month, categories)
    curve = expenses_curve_payload(spend, budget)
    breakdown = expense_svc.totals_by_category(year, month, categories)
    history = get_history_service().expense_history(year, month, categories)
    all_categories = get_category_service().list_all()
    return jsonify(expenses_charts_payload(year, month, curve, breakdown, history, all_categories))


def _parse_categories(codes: list[str]) -> set[int] | None:
    if not codes:
        return None
    try:
        return {int(code) for code in codes}
    except ValueError:
        abort(400)
