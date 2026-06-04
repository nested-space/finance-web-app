"""JSON API for post-paint refetches.

Returns data already shaped by services — no business logic here. The dashboard
per-month payload (month navigation) and the expenses spend curve (category
filter) (``docs/ARCHITECTURE.md`` -> "Frontend data delivery").
"""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request
from flask.typing import ResponseReturnValue

from finance_web_app.core.runtime.container import get_budget_service, get_expense_service
from finance_web_app.domain.records import Category
from finance_web_app.web.blueprints.summary import build_dashboard_payload
from finance_web_app.web.rendering.json_response import expenses_curve_payload

bp = Blueprint("api", __name__, url_prefix="/finance/api")


@bp.get("/model/<int:year>/<int:month>")
def model(year: int, month: int) -> ResponseReturnValue:
    if not 1 <= month <= 12:
        abort(404)
    return jsonify(build_dashboard_payload(year, month))


@bp.get("/expenses/<int:year>/<int:month>")
def expenses(year: int, month: int) -> ResponseReturnValue:
    if not 1 <= month <= 12:
        abort(404)
    categories = _parse_categories(request.args.getlist("category"))
    spend = get_expense_service().cumulative_spend(year, month, categories)
    budget = get_budget_service().cumulative_allocation(year, month, categories)
    return jsonify(expenses_curve_payload(spend, budget))


def _parse_categories(codes: list[str]) -> set[Category] | None:
    if not codes:
        return None
    try:
        return {Category.from_code(code) for code in codes}
    except ValueError:
        abort(400)
